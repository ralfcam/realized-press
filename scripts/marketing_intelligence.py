#!/usr/bin/env python3
"""Realized Press BWE — Demand & Editorial Telemetry Pipeline (`BWE v0.6.0`, `ARC-73`).

Turns a curated keyword seed into an evidence-tiered, cache-backed demand model and ranks editorial
and commercial actions from it.

Data tiers (``keyword_signals.source_tier``), best evidence first:
  gads_api               Google Ads API (``KeywordPlanIdeaService``) with a 30-day SQLite TTL cache
  gkp_csv_export         Keyword Planner web-UI export (``--import-gkp-export``; no Developer Token)
  seed                   Curated estimates in ``data/gkp_*_seed.csv`` (offline, deterministic)
  autocomplete_heuristic Google/Amazon autocomplete phrasing only: NO volume; never scored

Workflows:
  A. Keyword Gap Radar (``--keywords``): volume x trend x commercial intent (CPC) discounted by
     continuous FTS5 BM25 coverage of chapters and OKF evidence cards.
  B. Title, Subtitle & KDP 7-Box Optimizer (scorecard) and ``--optimize-kdp-boxes`` (50-byte packer).
  C. Upstream Frontier Topic Radar (``--discover <query>``): OpenAlex citation-velocity works.
  D. ``--fetch-live``: autocomplete discovery -> Google Ads enrichment; ``--expand-ideas`` for
     ``GenerateKeywordIdeas``; ``--import-gkp-export`` for UI exports.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from bwe import db as bwedb  # noqa: E402
from bwe.db import (  # noqa: E402
    TIER_AUTOCOMPLETE, TIER_GADS_API, TIER_GKP_EXPORT, TIER_SEED, VERIFIED_TIERS, CoverageResult,
    normalize_query,
)
from gads_client import (  # noqa: E402
    EnrichedKeywordMetric, GoogleAdsKeywordClient, cluster_to_seed_phrases, parse_native_gkp_csv_export,
)

STOPWORDS = {
    "when", "to", "what", "how", "why", "is", "are", "does", "do", "can", "my",
    "the", "a", "an", "in", "on", "of", "for", "vs", "or", "and", "with", "from",
    "by", "at", "baby", "babies", "toddler", "toddlers", "child", "kids", "old",
    "doesnt", "dont", "isnt", "myth", "debunked", "really", "actually", "study", "versus",
}

# Opportunity = vol x trend x intent / (1 + ALPHA*chapter_cov + BETA*card_cov).
# ALPHA + BETA = 3 reproduces the legacy 0.25 floor for a topic that is fully covered.
OPP_ALPHA_CHAPTER = 2.0
OPP_BETA_CARD = 1.0
OPP_CPC_WEIGHT = 0.15
# A query counts as covered (routed to KDP / Amazon Ads rather than the gap list) above both thresholds.
COVERED_CHAPTER_MIN = 0.60
COVERED_CARD_MIN = 0.40

SEED_CSV_BY_SERIES = {
    "parenthood-atlas": "gkp_parenting_0_3_seed.csv",
    "architectures-of-memory": "gkp_architectures_of_memory_seed.csv",
}
CSV_FIELDS = [
    "query", "monthly_volume", "yoy_trend_pct", "competition_index", "target_chapter",
    "paa_question_hook", "cpc_low_usd", "cpc_high_usd", "volume_range_high", "source_tier", "fetched_at",
]
TIER_SHORT = {TIER_GADS_API: "API", TIER_GKP_EXPORT: "CSV-UI", TIER_SEED: "SEED", TIER_AUTOCOMPLETE: "AUTO"}

KDP_BOX_COUNT = 7
KDP_BOX_BYTES = 50        # hard KDP limit, enforced by bwe.schema
KDP_PACK_BYTES = 49       # packer target: one byte of headroom under the limit
KDP_MIN_COVERAGE = 0.25
BOX_STOPWORDS = {
    "a", "an", "the", "of", "and", "or", "for", "to", "in", "on", "at", "by", "from", "with", "vs",
    "versus", "how", "what", "when", "why", "which", "who", "is", "are", "was", "be", "do", "does",
    "did", "can", "my", "your", "you", "it", "its", "as", "not", "no", "about", "this", "that",
    "doesnt", "dont", "isnt", "your", "i", "we",
}


@dataclass
class KeywordSignal:
    query: str
    monthly_volume: int
    yoy_trend_pct: float
    competition_index: float
    target_chapter: str
    paa_hook: str
    source_tier: str = TIER_SEED
    cpc_low_usd: float = 0.0
    cpc_high_usd: float = 0.0
    volume_range_high: Optional[int] = None
    fetched_at: str = ""
    chapter_score: float = 0.0
    card_score: float = 0.0
    matched_chapter: Optional[str] = None
    matched_card: Optional[str] = None
    opportunity_score: float = 0.0

    @property
    def coverage(self) -> float:
        return min(1.0, 0.65 * self.chapter_score + 0.35 * self.card_score)

    @property
    def covered(self) -> bool:
        return self.chapter_score >= COVERED_CHAPTER_MIN and self.card_score >= COVERED_CARD_MIN

    @property
    def verified(self) -> bool:
        return self.source_tier in VERIFIED_TIERS


def compute_opportunity_score(
    vol: int, yoy: float, cpc_high: float = 0.0, chapter_cov: float = 0.0, card_cov: float = 0.0
) -> float:
    """Volume x trend x commercial intent, discounted by how much the book already answers the query.

    trend    = max(1, 1 + YoY/100)              (declines are not penalised below 1)
    intent   = 1 + 0.15 * ln(1 + CPC_high_usd)  (advertisers paying more signal buying intent)
    discount = 1 / (1 + 2*chapter_cov + 1*card_cov), coverages in [0, 1] from FTS5 BM25
    """
    trend = max(1.0, 1.0 + yoy / 100.0)
    intent = 1.0 + OPP_CPC_WEIGHT * math.log1p(max(cpc_high, 0.0))
    discount = 1.0 / (1.0 + OPP_ALPHA_CHAPTER * chapter_cov + OPP_BETA_CARD * card_cov)
    return round(vol * trend * intent * discount, 1)


def repo_root() -> Path:
    return ROOT


def _extract_core_tokens(query: str) -> list[str]:
    cleaned = re.sub(r"'s\b", "", query.lower()).replace("'", "")
    tokens = [t for t in re.findall(r"[a-z0-9]+", cleaned) if len(t) >= 3]
    core = [t for t in tokens if t not in STOPWORDS]
    return core or tokens[:2]


def chapter_label(matched: Optional[str]) -> str:
    """'04-regulatory-relationship' -> '04'; 'book-04-x/05-rag' -> 'B04.05'; None -> ''."""
    if not matched:
        return ""
    m = re.match(r"^(?:book-(\d+)-[^/]+/)?(\d+)-", matched)
    if not m:
        return ""
    return f"B{m.group(1)}.{m.group(2)}" if m.group(1) else m.group(2)


def _fmt_chapter(label: str) -> str:
    return f"Ch {label}" if label.isdigit() else (label or "?")


# ---------------------------------------------------------------------------
# Seed CSV (Tier 3) read / write
# ---------------------------------------------------------------------------

def seed_csv_path(series_slug: str, root: Path = ROOT) -> Path:
    name = SEED_CSV_BY_SERIES.get(series_slug, f"gkp_{series_slug.replace('-', '_')}_seed.csv")
    return root / "data" / name


def _num(value: object, cast: Callable, default):
    try:
        return cast(str(value).strip())
    except (TypeError, ValueError):
        return default


def read_seed_csv(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Return (leading '#' comment lines, rows). Tolerates rows whose free-text hook has unquoted commas."""
    text = csv_path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    comments = [ln for ln in lines if ln.lstrip().startswith("#")]
    body = "\n".join(ln for ln in lines if not ln.lstrip().startswith("#"))
    reader = csv.DictReader(io.StringIO(body))
    if not reader.fieldnames or "query" not in [f.strip() for f in reader.fieldnames]:
        raise ValueError(
            f"{csv_path.name}: no 'query' column. If this is a Keyword Planner web-UI export, use "
            "--import-gkp-export instead."
        )
    rows: list[dict[str, str]] = []
    for row in reader:
        extras = row.pop(None, None)  # type: ignore[call-overload]
        if extras:
            print(f"[WARN] {csv_path.name}: row for '{row.get('query')}' has {len(extras)} unquoted extra field(s); merged into the hook.", file=sys.stderr)
            row["paa_question_hook"] = ",".join([row.get("paa_question_hook") or "", *extras])
        if (row.get("query") or "").strip():
            rows.append({k: (v or "") for k, v in row.items()})
    return comments, rows


def write_seed_csv(csv_path: Path, comments: list[str], rows: list[dict[str, str]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        for c in comments:
            f.write(c.rstrip() + "\n")
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def _signal_from_csv_row(row: dict[str, str]) -> KeywordSignal:
    return KeywordSignal(
        query=normalize_query(row["query"]),
        monthly_volume=_num(row.get("monthly_volume"), lambda s: int(float(s)), 0),
        yoy_trend_pct=_num(row.get("yoy_trend_pct"), float, 0.0),
        competition_index=_num(row.get("competition_index"), float, 0.0),
        target_chapter=(row.get("target_chapter") or "").strip(),
        paa_hook=(row.get("paa_question_hook") or "").strip(),
        source_tier=(row.get("source_tier") or "").strip() or TIER_SEED,
        cpc_low_usd=_num(row.get("cpc_low_usd"), float, 0.0),
        cpc_high_usd=_num(row.get("cpc_high_usd"), float, 0.0),
        volume_range_high=_num(row.get("volume_range_high"), lambda s: int(float(s)), None),
        fetched_at=(row.get("fetched_at") or "").strip(),
    )


def _signal_from_db_row(row) -> KeywordSignal:
    return KeywordSignal(
        query=row["query"],
        monthly_volume=int(row["monthly_volume"]),
        yoy_trend_pct=float(row["yoy_trend_pct"]),
        competition_index=float(row["competition_index"]),
        target_chapter=row["target_chapter"] or "",
        paa_hook=row["paa_hook"] or "",
        source_tier=row["source_tier"],
        cpc_low_usd=float(row["cpc_low_usd"]),
        cpc_high_usd=float(row["cpc_high_usd"]),
        volume_range_high=row["volume_range_high"],
        fetched_at=row["fetched_at"] or "",
    )


# ---------------------------------------------------------------------------
# Tier resolution + scoring
# ---------------------------------------------------------------------------

def _prefer_db(csv_sig: KeywordSignal, db_sig: KeywordSignal) -> bool:
    """Verified evidence beats seed estimates; two verified rows -> newer wins (CSV on ties);
    two unverified rows -> the curated CSV wins."""
    if db_sig.verified != csv_sig.verified:
        return db_sig.verified
    if db_sig.verified:
        db_ts, csv_ts = bwedb.parse_ts(db_sig.fetched_at), bwedb.parse_ts(csv_sig.fetched_at)
        return bool(db_ts and (csv_ts is None or db_ts > csv_ts))
    return False


def _persist_metrics(conn, series_slug: str, sig: KeywordSignal, hist_json: str = "[]") -> None:
    """Write a CSV-sourced signal's metrics to the cache. fetched_at (the TTL clock) is only written
    when the CSV carries one, so re-reading a seed never refreshes a cache entry."""
    fields = dict(
        monthly_volume=sig.monthly_volume, volume_range_high=sig.volume_range_high,
        yoy_trend_pct=sig.yoy_trend_pct, competition_index=sig.competition_index,
        cpc_low_usd=sig.cpc_low_usd, cpc_high_usd=sig.cpc_high_usd, source_tier=sig.source_tier,
        target_chapter=sig.target_chapter, paa_hook=sig.paa_hook, monthly_histogram_json=hist_json,
    )
    if sig.fetched_at:
        fields["fetched_at"] = sig.fetched_at
    bwedb.upsert_keyword_signal(conn, series_slug, sig.query, **fields)


def score_signal(conn, series_slug: str, sig: KeywordSignal) -> CoverageResult:
    cov = bwedb.bm25_coverage(conn, series_slug, _extract_core_tokens(sig.query)[:8])
    sig.chapter_score, sig.card_score = cov.chapter_score, cov.card_score
    sig.matched_chapter, sig.matched_card = cov.chapter, cov.card
    sig.opportunity_score = compute_opportunity_score(
        sig.monthly_volume, sig.yoy_trend_pct, sig.cpc_high_usd, sig.chapter_score, sig.card_score
    )
    bwedb.upsert_keyword_signal(
        conn, series_slug, sig.query,
        bm25_chapter_score=cov.chapter_score, bm25_card_score=cov.card_score,
        bm25_coverage_score=round(sig.coverage, 4), matched_chapter=cov.chapter, matched_card=cov.card,
        opportunity_score=sig.opportunity_score, scored_at=bwedb.now_iso(),
    )
    return cov


def load_and_score_signals(
    conn, series_slug: str, seed_rows: list[dict[str, str]]
) -> tuple[list[KeywordSignal], list[KeywordSignal]]:
    """Merge seed CSV rows with cached DB rows by tier, then BM25-score everything.

    Returns (scored signals, unverified autocomplete candidates). Autocomplete rows carry no volume
    and are never scored.
    """
    merged: dict[str, KeywordSignal] = {}
    for row in seed_rows:
        merged[normalize_query(row["query"])] = _signal_from_csv_row(row)
    from_csv = set(merged)
    histograms: dict[str, str] = {}

    candidates: list[KeywordSignal] = []
    for db_row in conn.execute(
        "SELECT * FROM keyword_signals WHERE series_slug = ? ORDER BY query;", (series_slug,)
    ).fetchall():
        db_sig = _signal_from_db_row(db_row)
        histograms[db_sig.query] = db_row["monthly_histogram_json"]
        if db_sig.source_tier == TIER_AUTOCOMPLETE:
            candidates.append(db_sig)
            continue
        csv_sig = merged.get(db_sig.query)
        if csv_sig is None:
            # Google Ads discoveries not (yet) in the seed; a verified zero-volume answer stays cached only.
            if db_sig.verified and db_sig.monthly_volume > 0:
                merged[db_sig.query] = db_sig
        elif _prefer_db(csv_sig, db_sig):
            db_sig.target_chapter = csv_sig.target_chapter or db_sig.target_chapter
            db_sig.paa_hook = csv_sig.paa_hook or db_sig.paa_hook
            merged[db_sig.query] = db_sig
            from_csv.discard(db_sig.query)

    for q in from_csv:
        _persist_metrics(conn, series_slug, merged[q], histograms.get(q, "[]"))

    signals = list(merged.values())
    for sig in signals:
        score_signal(conn, series_slug, sig)
    return signals, candidates


# ---------------------------------------------------------------------------
# Stage 1 (autocomplete) and Stage 2 (Google Ads) enrichment
# ---------------------------------------------------------------------------

def _http_json(url: str, timeout: float = 6.0):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_autocomplete_candidates(
    seed_rows: list[dict[str, str]],
    existing: set[str],
    per_seed: int = 2,
    spacing_s: float = 0.25,
    fetch: Callable[[str], object] = _http_json,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, str]]:
    """Stage 1: surface how readers phrase questions via Google Suggest and Amazon stripbooks.

    Returns candidates with their originating seed's chapter and PAA hook. No volume is implied.
    A candidate must keep >=60% of its origin query's core tokens to limit topical drift.
    """
    seen = set(existing)
    found: list[dict[str, str]] = []
    for row in seed_rows:
        origin = row["query"]
        prefix = " ".join(origin.split()[:4])
        origin_core = set(_extract_core_tokens(origin))
        fetched: list[str] = []
        try:
            data = fetch(f"https://suggestqueries.google.com/complete/search?client=firefox&q={urllib.parse.quote_plus(prefix)}")
            if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
                fetched += [s for s in data[1] if isinstance(s, str)]
        except Exception:  # noqa: BLE001 - network is best-effort
            pass
        try:
            data = fetch(f"https://completion.amazon.com/api/2017/suggestions?prefix={urllib.parse.quote_plus(prefix)}&mid=ATVPDKIKX0DER&alias=stripbooks")
            if isinstance(data, dict):
                fetched += [s.get("value", "") for s in data.get("suggestions", []) if isinstance(s, dict)]
        except Exception:  # noqa: BLE001
            pass

        taken = 0
        for cand in fetched:
            q = normalize_query(cand)
            if taken >= per_seed or len(q) < 8 or q in seen:
                continue
            if origin_core and len(origin_core & set(_extract_core_tokens(q))) / len(origin_core) < 0.6:
                continue
            seen.add(q)
            taken += 1
            found.append({
                "query": q,
                "target_chapter": (row.get("target_chapter") or "").strip(),
                "paa_hook": (row.get("paa_question_hook") or "").strip(),
            })
        sleep(spacing_s)
    return found


def enrich_with_gads(
    conn, series_slug: str, queries: Iterable[str], client: GoogleAdsKeywordClient,
    ttl_days: int = bwedb.DEFAULT_CACHE_TTL_DAYS, refresh: bool = False, now: Optional[datetime] = None,
) -> dict[str, int]:
    """Stage 2: GenerateKeywordHistoricalMetrics for every query not cached within the TTL."""
    stats = {"cached": 0, "fetched": 0, "unavailable": 0}
    wanted = list(dict.fromkeys(normalize_query(q) for q in queries if q.strip()))
    todo: list[str] = []
    for q in wanted:
        if not refresh and bwedb.is_cache_fresh(bwedb.get_keyword_signal(conn, series_slug, q), ttl_days, now):
            stats["cached"] += 1
        else:
            todo.append(q)
    if not todo:
        return stats
    metrics = client.fetch_historical_metrics(todo)
    stamp = bwedb.now_iso(now)
    for q in todo:
        m = metrics.get(q)
        if m is None:
            stats["unavailable"] += 1
            continue
        _store_gads_metric(conn, series_slug, m, stamp)
        stats["fetched"] += 1
    return stats


def _store_gads_metric(conn, series_slug: str, m: EnrichedKeywordMetric, stamp: str, **extra) -> None:
    bwedb.upsert_keyword_signal(
        conn, series_slug, m.query,
        monthly_volume=m.monthly_volume, volume_range_high=m.volume_range_high,
        yoy_trend_pct=m.yoy_trend_pct, competition_index=m.competition_index,
        cpc_low_usd=m.cpc_low_usd, cpc_high_usd=m.cpc_high_usd,
        monthly_histogram_json=json.dumps(m.monthly_histogram), source_tier=m.source_tier,
        fetched_at=stamp, **extra,
    )


def series_seed_phrases(series_dir: Path, limit: int = 40) -> list[str]:
    """Short keyword seeds from series.yaml topic clusters and chapter subtitles."""
    data = yaml.safe_load((series_dir / "series.yaml").read_text(encoding="utf-8")) or {}
    texts = list((data.get("marketing_intelligence") or {}).get("high_intent_topic_clusters") or [])
    for book in data.get("books") or []:
        texts += [ch.get("subtitle") for ch in book.get("chapters") or [] if ch.get("subtitle")]
    phrases: list[str] = []
    for t in texts:
        phrases += cluster_to_seed_phrases(t)
    return list(dict.fromkeys(phrases))[:limit]


def expand_ideas(
    conn, series_slug: str, client: GoogleAdsKeywordClient, seeds: list[str],
    min_volume: int = 1000, limit: int = 50, min_relevance: float = 0.25,
) -> int:
    """GenerateKeywordIdeas from topic seeds; keep adjacent queries the series could plausibly answer.

    Ideas whose best BM25 coverage is below ``min_relevance`` are dropped (e.g. 'baby names').
    New ideas are stored as verified rows (tier gads_api) but are not written to the seed CSV
    unless --persist-discoveries is given.
    """
    stamp = bwedb.now_iso()
    added = 0
    for m in client.generate_keyword_ideas(seeds, max_results=limit * 3, min_volume=min_volume):
        if bwedb.get_keyword_signal(conn, series_slug, m.query) is not None:
            continue
        cov = bwedb.bm25_coverage(conn, series_slug, _extract_core_tokens(m.query)[:8])
        if cov.combined < min_relevance:
            continue
        _store_gads_metric(conn, series_slug, m, stamp, target_chapter=chapter_label(cov.chapter), paa_hook="")
        added += 1
        if added >= limit:
            break
    return added


def sync_seed_csv(conn, series_slug: str, csv_path: Path, persist_discoveries: bool = False) -> int:
    """Mirror verified DB metrics back into the committed seed so offline/CI runs stay deterministic."""
    comments, rows = read_seed_csv(csv_path)
    by_query = {normalize_query(r["query"]): r for r in rows}
    changed = 0
    for db_row in conn.execute(
        "SELECT * FROM keyword_signals WHERE series_slug = ? AND source_tier IN (?, ?) ORDER BY query;",
        (series_slug, TIER_GADS_API, TIER_GKP_EXPORT),
    ):
        target = by_query.get(db_row["query"])
        if target is None:
            if not persist_discoveries:
                continue
            target = {"query": db_row["query"], "target_chapter": db_row["target_chapter"] or "",
                      "paa_question_hook": db_row["paa_hook"] or ""}
            rows.append(target)
            by_query[db_row["query"]] = target
        new = {
            "monthly_volume": str(db_row["monthly_volume"]),
            "yoy_trend_pct": f"{db_row['yoy_trend_pct']:g}",
            "competition_index": f"{db_row['competition_index']:g}",
            "cpc_low_usd": f"{db_row['cpc_low_usd']:g}",
            "cpc_high_usd": f"{db_row['cpc_high_usd']:g}",
            "volume_range_high": "" if db_row["volume_range_high"] is None else str(db_row["volume_range_high"]),
            "source_tier": db_row["source_tier"],
            "fetched_at": db_row["fetched_at"],
        }
        if any(target.get(k, "") != v for k, v in new.items()):
            target.update(new)
            changed += 1
    if changed:
        write_seed_csv(csv_path, comments, rows)
    return changed


def import_gkp_export(
    export_path: Path, series_slug: str, csv_path: Path, dry_run: bool = False
) -> str:
    """Tier 2: ingest a Keyword Planner web-UI export into the DB and the series seed CSV."""
    export = parse_native_gkp_csv_export(export_path)
    bwedb.init_db(ROOT)
    stamp = bwedb.now_iso()
    updated = added = 0
    comments, rows = read_seed_csv(csv_path) if csv_path.is_file() else ([], [])
    by_query = {normalize_query(r["query"]): r for r in rows}
    with bwedb.get_db() as conn:
        for m in export.metrics:
            q = normalize_query(m.query)
            cov = bwedb.bm25_coverage(conn, series_slug, _extract_core_tokens(q)[:8])
            row = by_query.get(q)
            if row is None:
                row = {"query": q, "target_chapter": chapter_label(cov.chapter), "paa_question_hook": ""}
                rows.append(row)
                by_query[q] = row
                added += 1
            else:
                updated += 1
            row.update({
                "monthly_volume": str(m.monthly_volume), "yoy_trend_pct": f"{m.yoy_trend_pct:g}",
                "competition_index": f"{m.competition_index:g}", "cpc_low_usd": f"{m.cpc_low_usd:g}",
                "cpc_high_usd": f"{m.cpc_high_usd:g}",
                "volume_range_high": "" if m.volume_range_high is None else str(m.volume_range_high),
                "source_tier": TIER_GKP_EXPORT, "fetched_at": stamp,
            })
            if not dry_run:
                _store_gads_metric(
                    conn, series_slug, m, stamp,
                    target_chapter=row.get("target_chapter") or "", paa_hook=row.get("paa_question_hook") or "",
                )
    if not dry_run:
        write_seed_csv(csv_path, comments, rows)
    lines = [
        f"[marketing-intel:import] {export_path.name}: {len(export.metrics)} keyword row(s) parsed "
        f"({updated} updated, {added} new), {export.skipped_rows} skipped (no volume) -> "
        f"{csv_path.name if not dry_run else '(dry run: nothing written)'} [tier={TIER_GKP_EXPORT}]",
    ]
    lines += [f"[WARN] {w}" for w in export.warnings]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def collect_signals(
    csv_path: Optional[Path], series_slug: str
) -> tuple[list[KeywordSignal], list[KeywordSignal]]:
    """Load seed + cache for a series and BM25-score it (returns signals, autocomplete candidates)."""
    bwedb.init_db(ROOT)
    seed_rows: list[dict[str, str]] = []
    if csv_path is not None and csv_path.is_file():
        _, seed_rows = read_seed_csv(csv_path)
    with bwedb.get_db() as conn:
        return load_and_score_signals(conn, series_slug, seed_rows)


def run_keyword_gap_radar(
    csv_path: Optional[Path], series_slug: str = "parenthood-atlas", extra_notes: Optional[list[str]] = None
) -> str:
    """Workflows A & B: score every cached/seed query and render the Demand & Editorial report."""
    signals, candidates = collect_signals(csv_path, series_slug)
    return render_radar_report(signals, candidates, csv_path, series_slug, extra_notes)


def render_radar_report(
    signals: list[KeywordSignal], candidates: list[KeywordSignal], csv_path: Optional[Path],
    series_slug: str, extra_notes: Optional[list[str]] = None,
) -> str:
    if not signals:
        hint = f"`{csv_path.relative_to(ROOT).as_posix()}`" if csv_path and csv_path.is_relative_to(ROOT) else "a seed CSV"
        return f"# BWE v0.6.0 Keyword Demand Report (`{series_slug}`)\n- No keyword signals found. Add rows to {hint} or run `--import-gkp-export` / `--fetch-live`.\n"

    signals.sort(key=lambda s: (-s.opportunity_score, s.query))
    gaps = [s for s in signals if not s.covered]
    covered = sorted((s for s in signals if s.covered), key=lambda s: -(s.monthly_volume * s.coverage))
    tiers = Counter(s.source_tier for s in signals)
    verified_vol = sum(s.monthly_volume for s in signals if s.verified)
    total_vol = sum(s.monthly_volume for s in signals)
    src = csv_path.relative_to(ROOT).as_posix() if csv_path and csv_path.is_relative_to(ROOT) else (str(csv_path) if csv_path else "db cache")

    lines = [
        f"# BWE v0.6.0 Keyword Demand & Editorial Telemetry Report (`{series_slug}`)",
        f"- **Seed Dataset:** `{src}`",
        f"- **Search Clusters Analyzed:** {len(signals)} ({total_vol:,}/mo combined)",
        "- **Evidence Tiers:** " + ", ".join(f"{TIER_SHORT.get(t, t)}={n}" for t, n in sorted(tiers.items())),
        f"- **Verified Volume Share:** {(verified_vol / total_vol * 100 if total_vol else 0):.0f}% of combined volume is from Google Ads / Keyword Planner exports",
        f"- **Covered (chapter >= {COVERED_CHAPTER_MIN:.2f} and card >= {COVERED_CARD_MIN:.2f} BM25 coverage):** {len(covered)}/{len(signals)}",
        f"- **Priority 1 Content Gaps:** {len(gaps)}",
    ]
    if not verified_vol:
        lines.append("- **NOTE:** every volume here is a curated seed estimate (tier SEED). Enrich with `--fetch-live` (Google Ads credentials) or `--import-gkp-export <file>`.")
    lines += [f"- {n}" for n in (extra_notes or [])]

    lines += [
        "",
        "## 1. Priority 1 Content Gaps (Volume x Trend x CPC Intent, Discounted by BM25 Coverage)",
        "| Search Query | Vol | Trend | Comp | CPC high | Target | Best Chapter (cov) | Best Card (cov) | Opportunity | Tier |",
        "| :--- | ---: | ---: | ---: | ---: | :---: | :--- | :--- | ---: | :---: |",
    ]
    for s in gaps:
        vol = f"{s.monthly_volume:,}" + (f"-{s.volume_range_high:,}" if s.volume_range_high else "")
        lines.append(
            f"| `{s.query}` | {vol} | {s.yoy_trend_pct:+.1f}% | {s.competition_index:.2f} | ${s.cpc_high_usd:.2f} | "
            f"{_fmt_chapter(s.target_chapter)} | `{s.matched_chapter or '-'}` ({s.chapter_score:.2f}) | "
            f"`{s.matched_card or '-'}` ({s.card_score:.2f}) | **{s.opportunity_score:,.1f}** | {TIER_SHORT.get(s.source_tier, s.source_tier)} |"
        )
    if not gaps:
        lines.append("| *(none: every tracked query is covered)* | | | | | | | | | |")

    lines += [
        "",
        "## 2. Covered Demand -> KDP 7-Box & Amazon Ads Bid Candidates (the book already answers these)",
        "| Search Query | Vol | CPC high | Coverage | Best Chapter | Tier |",
        "| :--- | ---: | ---: | ---: | :--- | :---: |",
    ]
    for s in covered[:12]:
        lines.append(
            f"| `{s.query}` | {s.monthly_volume:,} | ${s.cpc_high_usd:.2f} | {s.coverage:.2f} | `{s.matched_chapter}` | {TIER_SHORT.get(s.source_tier, s.source_tier)} |"
        )
    if not covered:
        lines.append("| *(none yet)* | | | | | |")

    lines += [
        "",
        "## 3. 'People Also Ask' (PAA) Question Hooks",
        "| Target | Search Query | Monthly Vol | Best OKF Card | 'People Also Ask' Natural Opening Hook |",
        "| :---: | :--- | ---: | :--- | :--- |",
    ]
    for s in sorted(signals, key=lambda x: (x.target_chapter, -x.monthly_volume)):
        card = f"`{s.matched_card}` ({s.card_score:.2f})" if s.card_score >= COVERED_CARD_MIN else "**GAP (needs card/section)**"
        lines.append(f"| **{_fmt_chapter(s.target_chapter)}** | `{s.query}` | {s.monthly_volume:,} | {card} | *{s.paa_hook}* |")

    if candidates:
        lines += [
            "",
            "## 4. Unverified Autocomplete Candidates (phrasing only: no volume, not scored)",
            "Enrich with `--fetch-live` once Google Ads credentials exist, or paste into a Keyword Planner project and `--import-gkp-export`. Review relevance before promoting.",
        ]
        lines += [f"- `{c.query}` -> {_fmt_chapter(c.target_chapter)}" for c in candidates[:25]]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# KDP 7-box 50-byte packer
# ---------------------------------------------------------------------------

def _stem_key(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def _box_tokens(text: str) -> list[str]:
    cleaned = re.sub(r"'s\b", "", text.lower()).replace("'", "")
    return [t for t in re.findall(r"[a-z0-9]+", cleaned) if len(t) > 1 and not t.isdigit()]


def pack_kdp_boxes(
    signals: Iterable[KeywordSignal], excluded_text: str,
    boxes: int = KDP_BOX_COUNT, max_bytes: int = KDP_PACK_BYTES,
) -> tuple[list[str], float, float]:
    """Greedy knapsack of search words into KDP backend boxes.

    Each word is weighted by sum(volume x coverage) over the queries containing it, so the book only
    spends box space on demand it genuinely answers (coverage < 0.25 is ignored). Words already in
    the title/subtitle, stop words, and singular/plural duplicates (across all boxes) are skipped.
    Phrase fragments from one query are kept together where they fit. Returns
    (boxes, weight_captured, weight_total).
    """
    used = {_stem_key(t) for t in _box_tokens(excluded_text)}
    phrases: dict[tuple[str, ...], float] = {}
    weight: Counter = Counter()
    for sig in signals:
        w = sig.monthly_volume * sig.coverage if sig.coverage >= KDP_MIN_COVERAGE else 0.0
        if w <= 0:
            continue
        toks = [t for t in dict.fromkeys(_box_tokens(sig.query)) if t not in BOX_STOPWORDS and _stem_key(t) not in used]
        if not toks:
            continue
        phrases[tuple(toks)] = phrases.get(tuple(toks), 0.0) + w
        for t in toks:
            weight[_stem_key(t)] += w
    total = float(sum(weight.values()))

    packed: list[str] = []
    for _ in range(boxes):
        chosen: list[str] = []
        size = 0
        while True:
            best: Optional[tuple[float, float, str, list[str], int]] = None
            for phrase in phrases:
                fresh = [t for t in phrase if _stem_key(t) not in used and t not in chosen]
                take: list[str] = []
                s = size
                for t in fresh:
                    cost = len(t.encode("utf-8")) + (1 if (chosen or take) else 0)
                    if s + cost <= max_bytes:
                        take.append(t)
                        s += cost
                if not take:
                    continue
                gain = sum(weight[_stem_key(t)] for t in take)
                cand = (gain / (s - size), gain, " ".join(phrase), take, s)
                if best is None or cand[:3] > best[:3]:
                    best = cand
            if best is None:
                break
            chosen += best[3]
            size = best[4]
            used |= {_stem_key(t) for t in best[3]}
        if chosen:
            packed.append(" ".join(chosen))
    captured = float(sum(weight[k] for k in {_stem_key(t) for box in packed for t in box.split()}))
    return packed, captured, total


def optimize_kdp_boxes_report(series_slug: str, signals: list[KeywordSignal]) -> str:
    from pydantic import ValidationError
    from bwe.schema import KdpMarketingMetadata

    series_dir = ROOT / "series" / series_slug
    data = yaml.safe_load((series_dir / "series.yaml").read_text(encoding="utf-8")) or {}
    title, subtitle = data.get("title", ""), data.get("subtitle", "") or ""
    current = (((data.get("monetization") or {}).get("kdp")) or {}).get("backend_keywords") or []
    excluded = f"{title} {subtitle}"
    ex_stems = {_stem_key(t) for t in _box_tokens(excluded)}

    proposed, captured, total = pack_kdp_boxes(signals, excluded)
    lines = [
        f"# KDP 7-Box Backend Keyword Optimizer: *{title}* (`{series_slug}`)",
        f"- **Excluded (already indexed from title/subtitle):** {', '.join(sorted(dict.fromkeys(_box_tokens(excluded)))) or 'none'}",
        f"- **Method:** greedy knapsack over sum(volume x BM25 coverage) per word; <= {KDP_PACK_BYTES} UTF-8 bytes per box (KDP limit {KDP_BOX_BYTES}); no repeated words across boxes.",
        f"- **Demand weight captured by proposed boxes:** {(captured / total * 100 if total else 0):.0f}% of covered-demand weight",
    ]
    if not any(s.verified for s in signals):
        lines.append("- **NOTE:** weights come from SEED estimates; re-run after Google Ads / UI-export enrichment before changing the live boxes.")

    lines += ["", "## Current boxes (`series.yaml`)", "| # | Box | Bytes | Issues |", "| ---: | :--- | ---: | :--- |"]
    seen: dict[str, int] = {}
    for i, box in enumerate(current, 1):
        toks = _box_tokens(box)
        issues = []
        wasted = [t for t in toks if _stem_key(t) in ex_stems]
        if wasted:
            issues.append("repeats title/subtitle: " + ", ".join(wasted))
        dup = [t for t in toks if _stem_key(t) in seen]
        if dup:
            issues.append("repeats earlier box: " + ", ".join(dup))
        n = len(box.encode("utf-8"))
        if n > KDP_BOX_BYTES:
            issues.append(f"over {KDP_BOX_BYTES} bytes")
        for t in toks:
            seen.setdefault(_stem_key(t), i)
        lines.append(f"| {i} | `{box}` | {n} | {'; '.join(issues) or 'ok'} |")
    if len(current) != KDP_BOX_COUNT:
        lines.append(f"| | *{len(current)} of {KDP_BOX_COUNT} boxes defined* | | |")

    lines += ["", "## Proposed boxes", "| # | Box | Bytes |", "| ---: | :--- | ---: |"]
    for i, box in enumerate(proposed, 1):
        lines.append(f"| {i} | `{box}` | {len(box.encode('utf-8'))} |")

    try:
        KdpMarketingMetadata(primary_subtitle=subtitle, backend_keywords=proposed)
        lines.append(f"\n- **Schema validation (`KdpMarketingMetadata.backend_keywords`):** PASS ({len(proposed)} boxes)")
    except ValidationError as exc:
        lines.append(f"\n- **Schema validation:** FAIL: {exc.errors()[0]['msg']}")
    if len(proposed) < KDP_BOX_COUNT:
        lines.append(f"- **Note:** only {len(proposed)} of {KDP_BOX_COUNT} boxes could be filled from covered demand; keep curated phrases for the remainder.")
    lines += ["", "```yaml", "backend_keywords:"] + [f'  - "{b}"' for b in proposed] + ["```",
              "", "*Proposal only: `series.yaml` is not modified (PyYAML would drop its comments). Paste after review.*"]
    return "\n".join(lines) + "\n"


def extract_bib_years(series_dir: Path) -> list[int]:
    years: list[int] = []
    for bib in sorted(series_dir.rglob("sources.bib")):
        if "preliminary" in bib.parts:
            continue
        text = bib.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\byear\s*=\s*[\"{]?(\d{4})[\"}]?", text, re.IGNORECASE):
            years.append(int(m.group(1)))
    return years


def extract_lead_magnet_cards(series_dir: Path, limit: int = 5) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for card_path in sorted(series_dir.rglob("evidence-cards/*.md")):
        if card_path.name.startswith("_") or card_path.name.lower() in {"index.md", "readme.md"}:
            continue
        if "preliminary" in card_path.parts:
            continue
        text = card_path.read_text(encoding="utf-8", errors="replace")
        title_m = re.search(r'^title:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        status_m = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
        conf_m = re.search(r"^confidence:\s*(\S+)", text, re.MULTILINE)
        not_mean_m = re.search(
            r"^##\s+What This Does Not Mean\s*\n+(.+?)(?=\n##\s+|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        hook = ""
        if not_mean_m:
            first_line = not_mean_m.group(1).strip().splitlines()[0].strip()
            hook = re.sub(r"^[-*]\s+", "", first_line)
            if len(hook) > 140:
                hook = hook[:137] + "..."
        status = status_m.group(1) if status_m else "draft"
        conf = conf_m.group(1) if conf_m else "unknown"
        score = (2 if status == "stable" else 1) + (2 if "high" in conf else 1)
        candidates.append(
            {
                "id": card_path.stem,
                "title": title_m.group(1) if title_m else card_path.stem,
                "status": status,
                "confidence": conf,
                "hook": hook,
                "score": str(score),
            }
        )
    candidates.sort(key=lambda c: (-int(c["score"]), c["id"]))
    return candidates[:limit]


def analyze_series(series_dir: Path) -> str:
    manifest_path = series_dir / "series.yaml"
    if not manifest_path.is_file():
        return f"## `{series_dir.name}` — Missing `series.yaml`\n"

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    title = data.get("title", series_dir.name)
    subtitle = data.get("subtitle", "")
    mi = data.get("marketing_intelligence", {})
    mon = data.get("monetization", {})
    kdp = mon.get("kdp", {})
    site = mon.get("owned_marketing_site", {})
    books = data.get("books", [])

    personas = mi.get("target_personas", [])
    clusters = mi.get("high_intent_topic_clusters", [])
    comps = mi.get("comp_title_gaps", [])
    kdp_keywords = kdp.get("backend_keywords", [])
    bisac = kdp.get("bisac_categories", [])

    # Check search-intent subtitles across chapters
    all_chapters = [ch for b in books for ch in (b.get("chapters") or [])]
    subtitled_chapters = [ch for ch in all_chapters if ch.get("subtitle")]

    years = extract_bib_years(series_dir)
    recent_2015_plus = sum(1 for y in years if y >= 2015)
    recent_2020_plus = sum(1 for y in years if y >= 2020)
    decade_counts = Counter((y // 10) * 10 for y in years)

    lead_cards = extract_lead_magnet_cards(series_dir, limit=5)

    checks = [
        ("Target personas defined (>=2)", len(personas) >= 2),
        ("High-intent search/topic clusters defined (>=3)", len(clusters) >= 3),
        ("Competitive review-gap thesis defined (>=2 comps)", len(comps) >= 2),
        ("Amazon KDP 7 backend keyword phrases populated (<=50 bytes each)", len(kdp_keywords) == 7 and all(len(k.encode('utf-8')) <= 50 for k in kdp_keywords)),
        ("BISAC category codes assigned (>=2)", len(bisac) >= 2),
        ("Owned marketing site tiers configured", len(site.get("tiers", [])) >= 2),
        (
            f"Bestseller search-intent chapter subtitles configured ({len(subtitled_chapters)}/{len(all_chapters)})",
            len(all_chapters) > 0 and len(subtitled_chapters) == len(all_chapters),
        ),
    ]
    passed = sum(1 for _, ok in checks if ok)

    lines = [
        f"# Marketing Intelligence & Topic Scorecard — *{title}*",
        f"- **Manifest:** `{manifest_path.relative_to(repo_root()).as_posix()}`",
        f"- **Subtitle / Positioning Hook:** *{subtitle}*",
        f"- **Market Readiness Score:** **{passed}/{len(checks)} checks passed**",
        "",
        "## 1. Demand Signals, Personas & Competitive Gap Thesis",
        "### Target Personas",
    ]
    for p in personas:
        lines.append(f"- {p}")
    lines.append("\n### High-Intent Topic & Search Clusters (Driving Chapter/Book Selection)")
    for c in clusters:
        lines.append(f"- {c}")
    lines.append("\n### Competitive Market & Review-Gap Analysis")
    for comp in comps:
        lines.append(f"- {comp}")

    lines.extend(
        [
            "",
            "## 2. Amazon KDP & Search-Intent TOC Optimizer (Workflow B)",
            f"- **BISAC Categories ({len(bisac)}):** {', '.join(f'`{b}`' for b in bisac)}",
            f"- **KDP Backend Keywords ({len(kdp_keywords)}/7 slots):**",
        ]
    )
    for idx, kw in enumerate(kdp_keywords, 1):
        lines.append(f"  {idx}. `{kw}` ({len(kw.encode('utf-8'))}/50 bytes)")

    if subtitled_chapters:
        lines.extend(
            [
                "",
                "### High-Intent Search Subtitles Mapped to TOC",
                "| Slug | Literary Title | Search-Intent Subtitle |",
                "| :--- | :--- | :--- |",
            ]
        )
        for ch in subtitled_chapters:
            lines.append(f"| `{ch['slug']}` | *{ch['title']}* | **{ch['subtitle']}** |")

    lines.extend(
        [
            "",
            "## 3. Bibliographic Recency & Citation Velocity (`sources.bib`)",
            f"- **Total verified citations:** {len(years)}",
            f"- **Post-2015 literature:** {recent_2015_plus} ({(recent_2015_plus / len(years) * 100) if years else 0:.1f}%)",
            f"- **Post-2020 frontier literature:** {recent_2020_plus} ({(recent_2020_plus / len(years) * 100) if years else 0:.1f}%)",
            f"- **Decade distribution:** " + ", ".join(f"{d}s: {cnt}" for d, cnt in sorted(decade_counts.items())),
            "",
            "## 4. Top Owned-Marketing-Site Lead Magnets (OKF v0.2 Evidence Cards)",
            "| Card ID | Status | Grade | Counter-Intuitive / Myth-Busting Hook (`What This Does Not Mean`) |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )
    for c in lead_cards:
        lines.append(f"| `{c['id']}` | `{c['status']}` | `{c['confidence']}` | {c['hook']} |")

    lines.append("\n## 5. Readiness Gate Checklist")
    for label, ok in checks:
        mark = "PASS" if ok else "FAIL"
        lines.append(f"- [{mark}] {label}")
    lines.append("")
    return "\n".join(lines)


def discover_frontier_topics(query: str, limit: int = 5, min_year: int = 2022) -> str:
    current_year = 2026
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://api.openalex.org/works?search={encoded_q}&filter=publication_year:{min_year}-{current_year},is_retracted:false&sort=cited_by_count:desc&per-page=25"
    headers = {"User-Agent": "RealizedPressBWE/1.0 (mailto:admin@realizedpress.com)"}

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return f"# Upstream Frontier Topic Radar — Error querying OpenAlex: {e}\n"

    results = data.get("results") or []
    total_found = data.get("meta", {}).get("count", 0)

    candidates = []
    topic_counter = Counter()
    keyword_counter = Counter()

    for w in results:
        title = w.get("title") or "Untitled"
        year = w.get("publication_year") or current_year
        citations = w.get("cited_by_count") or 0
        doi = w.get("doi") or ""
        age = max(1, current_year - year)
        velocity = citations / age

        pt = w.get("primary_topic") or {}
        if pt.get("display_name"):
            topic_counter[pt["display_name"]] += 1

        for kw in w.get("keywords") or []:
            if kw.get("display_name"):
                keyword_counter[kw["display_name"].lower()] += 1

        candidates.append(
            {
                "title": title,
                "year": year,
                "citations": citations,
                "velocity": velocity,
                "doi": doi,
                "topic": pt.get("display_name", "General"),
                "field": (pt.get("field") or {}).get("display_name", "Interdisciplinary"),
            }
        )

    candidates.sort(key=lambda x: -x["velocity"])
    top_candidates = candidates[:limit]

    lines = [
        f"# Upstream Frontier Topic Radar — Query: *\"{query}\"*",
        f"- **Literature Scope:** OpenAlex indexed works ({min_year}–{current_year})",
        f"- **Total Relevant Works Identified:** {total_found:,}",
        "",
        "## 1. High-Velocity Frontier Citation Clusters (Candidate Topics)",
    ]
    for topic, count in topic_counter.most_common(5):
        lines.append(f"- **{topic}** ({count} flagship high-velocity papers)")

    lines.extend(
        [
            "",
            "## 2. Emerging Keyword Signals",
            "- " + ", ".join(f"`{k}` ({cnt})" for k, cnt in keyword_counter.most_common(8)),
            "",
            "## 3. Top Candidate Seed Works for OKF v0.2 Evidence Cards",
            "| Title | Year | Citations | Velocity (cites/yr) | Primary Topic / Field | DOI |",
            "| :--- | :---: | :---: | :---: | :--- | :--- |",
        ]
    )
    for c in top_candidates:
        doi_link = f"[{c['doi'].replace('https://doi.org/', '')}]({c['doi']})" if c['doi'] else "N/A"
        lines.append(f"| {c['title']} | {c['year']} | {c['citations']} | {c['velocity']:.1f}/yr | {c['topic']} ({c['field']}) | {doi_link} |")

    lines.extend(
        [
            "",
            "## 4. Next Actions for Series / Book Scaffolding",
            f"- Initialize new series manifest: `python scripts/init_series.py --series <slug> --title \"<Title>\"`",
            "- Author seed OKF v0.2 evidence cards using the verified DOIs above.",
            "- Verify with `python scripts/five_rule_check.py series/<slug>/book-01-<book-slug> --online-retraction-check`.",
        ]
    )
    return "\n".join(lines)


def _resolve_series(arg: Optional[str], need_seed: bool = True) -> list[str]:
    if arg:
        slug = Path(arg).name
        if not (ROOT / "series" / slug / "series.yaml").is_file():
            raise SystemExit(f"error: unknown series '{arg}' (no series/{slug}/series.yaml)")
        return [slug]
    slugs = sorted(p.parent.name for p in (ROOT / "series").glob("*/series.yaml"))
    return [s for s in slugs if seed_csv_path(s).is_file()] if need_seed else slugs


def run_live_stages(slug: str, csv_path: Path, args: argparse.Namespace, writeback: bool) -> list[str]:
    """Stage 1 (autocomplete) and Stage 2 (Google Ads) for one series; returns report notes."""
    notes: list[str] = []
    bwedb.init_db(ROOT)
    _, rows = read_seed_csv(csv_path)
    with bwedb.get_db() as conn:
        existing = {normalize_query(r["query"]) for r in rows}
        existing |= {r["query"] for r in conn.execute("SELECT query FROM keyword_signals WHERE series_slug = ?;", (slug,))}
        if args.fetch_live:
            cands = fetch_autocomplete_candidates(rows, existing)
            for c in cands:
                bwedb.upsert_keyword_signal(
                    conn, slug, c["query"], source_tier=TIER_AUTOCOMPLETE, monthly_volume=0,
                    target_chapter=c["target_chapter"], paa_hook=c["paa_hook"], fetched_at=bwedb.now_iso(),
                )
            notes.append(f"Stage 1 (autocomplete): {len(cands)} new candidate phrasing(s); no volume implied.")

        client = GoogleAdsKeywordClient(customer_id=args.gads_customer_id)
        if not client.is_available:
            notes.append(
                "Stage 2 (Google Ads) skipped: no credentials (needs the `google-ads` SDK, google-ads.yaml or "
                "GOOGLE_ADS_*, and GOOGLE_ADS_CUSTOMER_ID). Using cached / seed tiers."
            )
            return notes

        queries = [normalize_query(r["query"]) for r in rows]
        queries += [r["query"] for r in conn.execute(
            "SELECT query FROM keyword_signals WHERE series_slug = ? AND source_tier = ?;", (slug, TIER_AUTOCOMPLETE))]
        stats = enrich_with_gads(conn, slug, queries, client, ttl_days=args.cache_ttl_days, refresh=args.refresh)
        notes.append(
            f"Stage 2 (Google Ads): {stats['fetched']} fetched, {stats['cached']} served from the {args.cache_ttl_days}-day cache, "
            f"{stats['unavailable']} not returned."
        )
        if args.expand_ideas:
            seeds = series_seed_phrases(ROOT / "series" / slug)
            added = expand_ideas(conn, slug, client, seeds, min_volume=args.ideas_min_volume, limit=args.ideas_limit)
            notes.append(f"GenerateKeywordIdeas: {added} relevant new idea(s) from {len(seeds)} seed phrase(s).")
        if writeback and not args.dry_run:
            changed = sync_seed_csv(conn, slug, csv_path, persist_discoveries=args.persist_discoveries)
            notes.append(f"Seed CSV `{csv_path.name}`: {changed} row(s) updated with verified metrics.")
    return notes


def run_keyword_mode(args: argparse.Namespace) -> int:
    if args.import_gkp_export and not args.series:
        raise SystemExit("error: --import-gkp-export requires --series (an export must not be guessed onto a series)")
    if args.seed_csv and not args.series:
        raise SystemExit("error: --seed-csv requires --series")
    slugs = _resolve_series(args.series)
    if not slugs:
        raise SystemExit("error: no series with a seed CSV in data/ (create data/gkp_<series>_seed.csv)")

    for n, slug in enumerate(slugs):
        if n:
            print("\n---\n")
        seed_path = Path(args.seed_csv).resolve() if args.seed_csv else seed_csv_path(slug)
        read_path, writeback = seed_path, True
        if args.keywords and args.keywords.lower() != "seed":
            read_path, writeback = Path(args.keywords).resolve(), False   # explicit input CSV is read-only
        notes: list[str] = []

        if args.import_gkp_export:
            print(import_gkp_export(Path(args.import_gkp_export).resolve(), slug, seed_path, dry_run=args.dry_run))
        if args.fetch_live or args.expand_ideas:
            if not read_path.is_file():
                raise SystemExit(f"error: seed CSV not found: {read_path}")
            notes += run_live_stages(slug, read_path, args, writeback)

        csv_arg = read_path if read_path.is_file() else None
        signals, candidates = collect_signals(csv_arg, slug)
        print(render_radar_report(signals, candidates, csv_arg, slug, notes))
        if args.optimize_kdp_boxes:
            print(optimize_kdp_boxes_report(slug, signals))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BWE Marketing Intelligence: demand telemetry, keyword gap radar & KDP optimizer.")
    parser.add_argument("--series", default=None, help="Series slug or directory (omit to cover every series that has a seed CSV)")
    parser.add_argument("--keywords", default=None,
                        help="'seed' (data/gkp_*_seed.csv for the series) or a path to a normalised keyword CSV (read-only)")
    parser.add_argument("--seed-csv", default=None, help="Override the series seed CSV path (read + write-back; needs --series)")
    parser.add_argument("--fetch-live", action="store_true",
                        help="Stage 1 autocomplete discovery (Google Suggest + Amazon stripbooks), then Stage 2 Google Ads enrichment when credentials exist")
    parser.add_argument("--expand-ideas", action="store_true", help="Also run Google Ads GenerateKeywordIdeas from series.yaml topic seeds")
    parser.add_argument("--ideas-min-volume", type=int, default=1000, help="Minimum monthly searches for an expanded idea (default 1000)")
    parser.add_argument("--ideas-limit", type=int, default=50, help="Maximum new ideas per run (default 50)")
    parser.add_argument("--persist-discoveries", action="store_true", help="Append Ads-verified discoveries to the seed CSV (default: DB cache only)")
    parser.add_argument("--import-gkp-export", default=None, metavar="CSV", help="Import a Keyword Planner web-UI export (UTF-16 CSV; no Developer Token needed); requires --series")
    parser.add_argument("--optimize-kdp-boxes", action="store_true", help="Propose 7 backend keyword boxes (<=49 UTF-8 bytes each) from covered demand")
    parser.add_argument("--refresh", action="store_true", help="Ignore the Google Ads cache TTL and refetch")
    parser.add_argument("--cache-ttl-days", type=int, default=bwedb.DEFAULT_CACHE_TTL_DAYS, help="Google Ads cache TTL in days (default 30)")
    parser.add_argument("--gads-customer-id", default=None, help="Google Ads customer id (default: GOOGLE_ADS_CUSTOMER_ID)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write the seed CSV (import / Ads write-back)")
    parser.add_argument("--discover", default=None, help="Upstream search query to discover frontier citation-velocity topics via OpenAlex")
    parser.add_argument("--limit", type=int, default=5, help="Max candidate seed cards to return for topic discovery")
    args = parser.parse_args()

    if args.discover:
        print(discover_frontier_topics(args.discover, limit=args.limit))
        return 0

    if any([args.keywords, args.fetch_live, args.expand_ideas, args.import_gkp_export, args.optimize_kdp_boxes]):
        return run_keyword_mode(args)

    root = repo_root()
    if args.series:
        target = Path(args.series)
        if not target.is_dir():
            target = root / "series" / args.series
        series_dirs = [target.resolve()]
    else:
        series_dirs = sorted(p.parent for p in (root / "series").glob("*/series.yaml"))

    reports = [analyze_series(d) for d in series_dirs]
    print("\n---\n\n".join(reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
