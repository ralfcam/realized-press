# bwe/db.py
"""BWE SQLite state: FTS5 manuscript indexes, reader telemetry, and the keyword demand cache (BWE v0.6.0)."""
from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

DB_PATH = Path(".cache/bwe_state.db")

# Bump when a derived table (FTS5) or the keyword cache changes shape; init_db migrates in place.
SCHEMA_VERSION = 2

# Source tiers for keyword_signals.source_tier, best evidence first.
TIER_GADS_API = "gads_api"
TIER_GKP_EXPORT = "gkp_csv_export"
TIER_AUTOCOMPLETE = "autocomplete_heuristic"
TIER_SEED = "seed"
VERIFIED_TIERS = (TIER_GADS_API, TIER_GKP_EXPORT)

DEFAULT_CACHE_TTL_DAYS = 30

# BM25 coverage normalisation. FTS5 bm25() is negative (more negative = better) and unbounded, so the
# raw magnitude is squashed to [0, 1) with 1 - exp(-raw / BM25_SATURATION). See bm25_coverage().
BM25_SATURATION = 6.0
# Column weights for bm25(): series_slug, book_slug, <slug>, title, body.
_BM25_WEIGHTS = "0.0, 0.0, 0.0, 3.0, 1.0"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse_ts(value: Any) -> Optional[datetime]:
    """Parse ISO-8601 or SQLite CURRENT_TIMESTAMP text; naive values are treated as UTC."""
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(str(value).strip())
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


parse_ts = _parse_ts


_KEYWORD_SIGNALS_DDL = """
    CREATE TABLE IF NOT EXISTS keyword_signals (
        series_slug TEXT NOT NULL,
        query TEXT NOT NULL,
        monthly_volume INTEGER NOT NULL DEFAULT 0,
        volume_range_high INTEGER,
        yoy_trend_pct REAL NOT NULL DEFAULT 0.0,
        competition_index REAL NOT NULL DEFAULT 0.0,
        cpc_low_usd REAL NOT NULL DEFAULT 0.0,
        cpc_high_usd REAL NOT NULL DEFAULT 0.0,
        monthly_histogram_json TEXT NOT NULL DEFAULT '[]',
        source_tier TEXT NOT NULL DEFAULT 'seed',
        target_chapter TEXT,
        paa_hook TEXT,
        matched_chapter TEXT,
        matched_card TEXT,
        bm25_chapter_score REAL NOT NULL DEFAULT 0.0,
        bm25_card_score REAL NOT NULL DEFAULT 0.0,
        bm25_coverage_score REAL NOT NULL DEFAULT 0.0,
        opportunity_score REAL NOT NULL DEFAULT 0.0,
        fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        scored_at TEXT,
        PRIMARY KEY (series_slug, query)
    );
"""

KEYWORD_COLUMNS = frozenset(
    {
        "monthly_volume", "volume_range_high", "yoy_trend_pct", "competition_index", "cpc_low_usd",
        "cpc_high_usd", "monthly_histogram_json", "source_tier", "target_chapter", "paa_hook",
        "matched_chapter", "matched_card", "bm25_chapter_score", "bm25_card_score",
        "bm25_coverage_score", "opportunity_score", "fetched_at", "scored_at",
    }
)


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table});")}


def _migrate(conn: sqlite3.Connection) -> bool:
    """Bring a pre-v0.6.0 database to SCHEMA_VERSION. Returns True when a migration ran.

    * FTS5 tables are derived from the Markdown tree, so they are dropped and rebuilt (adopting the
      porter tokenizer so "tantrums" matches "tantrum").
    * keyword_signals (autoincrement id, no uniqueness) is rebuilt keyed on (series_slug, query);
      legacy rows are carried over as source_tier='seed'.
    """
    version = conn.execute("PRAGMA user_version;").fetchone()[0]
    if version >= SCHEMA_VERSION:
        return False

    conn.execute("DROP TABLE IF EXISTS evidence_cards_fts;")
    conn.execute("DROP TABLE IF EXISTS chapters_fts;")

    legacy_cols = _table_columns(conn, "keyword_signals")
    has_legacy = bool(legacy_cols) and "source_tier" not in legacy_cols
    if has_legacy:
        conn.execute("DROP TABLE IF EXISTS keyword_signals_legacy;")
        conn.execute("ALTER TABLE keyword_signals RENAME TO keyword_signals_legacy;")

    conn.execute(_KEYWORD_SIGNALS_DDL)

    if has_legacy:
        hook_col = "paa_question_hook" if "paa_question_hook" in legacy_cols else "NULL"
        stamp_col = "updated_at" if "updated_at" in legacy_cols else "NULL"
        conn.execute(
            f"""
            INSERT OR REPLACE INTO keyword_signals (
                series_slug, query, monthly_volume, yoy_trend_pct, competition_index,
                target_chapter, paa_hook, matched_chapter, matched_card, opportunity_score,
                source_tier, fetched_at
            )
            SELECT series_slug, lower(trim(query)), monthly_volume, yoy_trend_pct, competition_index,
                   target_chapter, {hook_col}, matched_chapter, matched_card, opportunity_score,
                   'seed', COALESCE({stamp_col}, CURRENT_TIMESTAMP)
            FROM keyword_signals_legacy ORDER BY id;
            """
        )
        conn.execute("DROP TABLE keyword_signals_legacy;")

    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")
    return True


def init_db(repo_root: Optional[Path] = None, conn: Optional[sqlite3.Connection] = None) -> None:
    root = repo_root or Path(__file__).resolve().parent.parent
    if conn is not None:
        _init_db_conn(conn, root)
    else:
        with get_db() as c:
            _init_db_conn(c, root)


def _init_db_conn(conn: sqlite3.Connection, repo_root: Path) -> None:
    _migrate(conn)
    # 1. FTS5 Virtual Table for OKF v0.2 Evidence Cards
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS evidence_cards_fts USING fts5(
            series_slug, book_slug, card_slug, title, body,
            tokenize = 'porter unicode61'
        );
    """)
    # 1b. ARC-72: FTS5 Virtual Table for Chapter Prose & Search Subtitles
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chapters_fts USING fts5(
            series_slug, book_slug, chapter_slug, title, body,
            tokenize = 'porter unicode61'
        );
    """)
    # 2. ARC-53: Structured Reader Feedback (replaces manual CSV triage)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reader_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_slug TEXT NOT NULL,
            chapter_slug TEXT NOT NULL,
            block_id TEXT,
            category TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 3. ARC-58: Citation & Footnote Telemetry for Marketing Intelligence
    conn.execute("""
        CREATE TABLE IF NOT EXISTS citation_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_slug TEXT NOT NULL,
            chapter_slug TEXT NOT NULL,
            footnote_id TEXT NOT NULL,
            event_type TEXT DEFAULT 'inspect',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 4. ARC-73: Keyword demand telemetry + 30-day cache (one row per series/query)
    conn.execute(_KEYWORD_SIGNALS_DDL)
    if (repo_root / "series").is_dir():
        reindex_evidence_cards(conn, repo_root)
        reindex_chapters(conn, repo_root)


def reindex_evidence_cards(conn: sqlite3.Connection, repo_root: Path) -> None:
    conn.execute("DELETE FROM evidence_cards_fts;")
    series_dir = repo_root / "series"
    for card_path in series_dir.glob("**/evidence-cards/*.md"):
        if card_path.name.startswith("_") or card_path.name.lower() in {"index.md", "readme.md"}:
            continue
        if "preliminary" in card_path.parts:
            continue
        rel_parts = card_path.relative_to(series_dir).parts
        series_slug = rel_parts[0]
        book_slug = rel_parts[1] if len(rel_parts) > 3 else "root"
        text = card_path.read_text(encoding="utf-8", errors="replace")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), card_path.stem)
        conn.execute(
            "INSERT INTO evidence_cards_fts (series_slug, book_slug, card_slug, title, body) VALUES (?, ?, ?, ?, ?)",
            (series_slug, book_slug, card_path.stem, title, text),
        )


def reindex_chapters(conn: sqlite3.Connection, repo_root: Path) -> None:
    conn.execute("DELETE FROM chapters_fts;")
    series_dir = repo_root / "series"
    for ch_path in series_dir.glob("**/chapters/*.md"):
        if ch_path.name.startswith("_") or ch_path.name.lower() in {"index.md", "readme.md"}:
            continue
        if "preliminary" in ch_path.parts:
            continue
        rel_parts = ch_path.relative_to(series_dir).parts
        series_slug = rel_parts[0]
        book_slug = rel_parts[1] if len(rel_parts) > 3 else "root"
        text = ch_path.read_text(encoding="utf-8", errors="replace")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), ch_path.stem)
        conn.execute(
            "INSERT INTO chapters_fts (series_slug, book_slug, chapter_slug, title, body) VALUES (?, ?, ?, ?, ?)",
            (series_slug, book_slug, ch_path.stem, title, text),
        )


# ---------------------------------------------------------------------------
# Keyword cache helpers
# ---------------------------------------------------------------------------

def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def get_keyword_signal(conn: sqlite3.Connection, series_slug: str, query: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM keyword_signals WHERE series_slug = ? AND query = ?;",
        (series_slug, normalize_query(query)),
    ).fetchone()


def upsert_keyword_signal(conn: sqlite3.Connection, series_slug: str, query: str, **fields: Any) -> None:
    """Insert or update one (series_slug, query) row, touching only the supplied columns.

    Re-scoring passes only bm25_*/opportunity_*/matched_*/scored_at, so fetched_at (the TTL clock) and
    the verified metrics survive. Metric writers pass fetched_at explicitly.
    """
    unknown = set(fields) - KEYWORD_COLUMNS
    if unknown:
        raise ValueError(f"unknown keyword_signals columns: {sorted(unknown)}")
    cols = ["series_slug", "query", *fields]
    placeholders = ", ".join("?" for _ in cols)
    updates = ", ".join(f"{c} = excluded.{c}" for c in fields)
    sql = f"INSERT INTO keyword_signals ({', '.join(cols)}) VALUES ({placeholders})"
    sql += f" ON CONFLICT(series_slug, query) DO UPDATE SET {updates};" if updates else " ON CONFLICT DO NOTHING;"
    conn.execute(sql, (series_slug, normalize_query(query), *fields.values()))


def is_cache_fresh(
    row: Optional[Mapping[str, Any]],
    ttl_days: int = DEFAULT_CACHE_TTL_DAYS,
    now: Optional[datetime] = None,
    tiers: Iterable[str] = (TIER_GADS_API,),
) -> bool:
    """True when row holds a verified-tier metric newer than ttl_days (the 30-day Google Ads TTL)."""
    if row is None or row["source_tier"] not in set(tiers):
        return False
    fetched = _parse_ts(row["fetched_at"])
    if fetched is None:
        return False
    return (now or utc_now()) - fetched < timedelta(days=ttl_days)


def now_iso(now: Optional[datetime] = None) -> str:
    return _iso(now or utc_now())


# ---------------------------------------------------------------------------
# Continuous BM25 manuscript coverage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverageResult:
    chapter_score: float          # 0..1, saturating transform of the best chapter BM25
    card_score: float             # 0..1, same for OKF evidence cards
    chapter: Optional[str]        # "book-01-.../03-slug" or "03-slug"; None when nothing matched
    card: Optional[str]
    raw_chapter_bm25: float       # positive magnitude of -bm25()
    raw_card_bm25: float

    @property
    def combined(self) -> float:
        """Single 0..1 relevance weight: chapter prose dominates, the card corroborates."""
        return min(1.0, 0.65 * self.chapter_score + 0.35 * self.card_score)


def _fts_or_query(tokens: Iterable[str]) -> str:
    terms = [t for t in dict.fromkeys(tokens) if re.fullmatch(r"[a-z0-9]+", t)]
    if not terms:
        return ""
    return "{title body} : (" + " OR ".join(f'"{t}"' for t in terms) + ")"


def _normalize_bm25(raw: float, saturation: float = BM25_SATURATION) -> float:
    return 0.0 if raw <= 0 else 1.0 - math.exp(-raw / saturation)


def _term_fraction(conn: sqlite3.Connection, table: str, rowid: int, terms: list[str]) -> float:
    """Fraction of the query terms that actually occur (title/body, stemmed) in one indexed document."""
    hits = 0
    for term in terms:
        found = conn.execute(
            f"SELECT 1 FROM {table} WHERE rowid = ? AND {table} MATCH ?;",
            (rowid, f'{{title body}} : "{term}"'),
        ).fetchone()
        hits += 1 if found else 0
    return hits / len(terms)


def _best_document(
    conn: sqlite3.Connection, table: str, label_sql: str, series_slug: str, match: str, terms: list[str],
    saturation: float,
) -> tuple[Optional[sqlite3.Row], float, float]:
    """Return (best row, raw BM25 magnitude, normalised coverage 0..1) for one FTS5 table."""
    row = conn.execute(
        f"""
        SELECT rowid AS rid, {label_sql}, bm25({table}, {_BM25_WEIGHTS}) AS s
        FROM {table} WHERE series_slug = ? AND {table} MATCH ? ORDER BY s LIMIT 1;
        """,
        (series_slug, match),
    ).fetchone()
    if row is None:
        return None, 0.0, 0.0
    raw = -float(row["s"])
    # A single rare term can score high under BM25 alone; scaling by sqrt(term fraction) keeps a
    # one-of-four-terms match from reading as "covered" without punishing a 2-of-3 match too hard.
    fraction = _term_fraction(conn, table, int(row["rid"]), terms)
    return row, raw, _normalize_bm25(raw, saturation) * math.sqrt(fraction)


def bm25_coverage(
    conn: sqlite3.Connection,
    series_slug: str,
    tokens: Iterable[str],
    saturation: float = BM25_SATURATION,
) -> CoverageResult:
    """Score how well a series' chapters and OKF cards answer a query, continuously.

    The tokens are OR-ed (partial matches still count; BM25's IDF weights rare terms such as
    "peanut" above common ones), restricted to title/body, with titles weighted 3x. The best
    chapter and best card per series are kept, and each score is scaled by the share of query
    terms the winning document really contains.
    """
    terms = [t for t in dict.fromkeys(tokens) if re.fullmatch(r"[a-z0-9]+", t)]
    match = _fts_or_query(terms)
    if not match:
        return CoverageResult(0.0, 0.0, None, None, 0.0, 0.0)

    ch, raw_ch, score_ch = _best_document(
        conn, "chapters_fts", "book_slug, chapter_slug", series_slug, match, terms, saturation
    )
    card, raw_card, score_card = _best_document(
        conn, "evidence_cards_fts", "card_slug", series_slug, match, terms, saturation
    )

    chapter = None
    if ch:
        chapter = ch["chapter_slug"] if ch["book_slug"] == "root" else f"{ch['book_slug']}/{ch['chapter_slug']}"
    return CoverageResult(
        chapter_score=round(score_ch, 4),
        card_score=round(score_card, 4),
        chapter=chapter,
        card=card["card_slug"] if card else None,
        raw_chapter_bm25=round(raw_ch, 4),
        raw_card_bm25=round(raw_card, 4),
    )
