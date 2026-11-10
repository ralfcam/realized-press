# bwe/db.py
"""BWE SQLite state: FTS5 manuscript indexes, reader telemetry, and the keyword demand cache (BWE v0.6.0)."""
from __future__ import annotations

import math
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

DB_PATH = Path(".cache/bwe_state.db")

# Bump when a derived table (FTS5) or the keyword cache changes shape; init_db migrates in place.
# v2: FTS5 porter tokenization & (series_slug, query) primary key.
# v3 (ARC-78): FTS5 'porter unicode61 remove_diacritics 2', cluster_variants_json & i18n partitioning.
# v4 (ARC-84): OKF v0.3 Property Graph (okf_nodes, okf_edges) & Graph RAG Context Engine.
SCHEMA_VERSION = 4

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
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
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
        cluster_variants_json TEXT NOT NULL DEFAULT '[]',
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
        "cpc_high_usd", "monthly_histogram_json", "cluster_variants_json", "source_tier", "target_chapter",
        "paa_hook", "matched_chapter", "matched_card", "bm25_chapter_score", "bm25_card_score",
        "bm25_coverage_score", "opportunity_score", "fetched_at", "scored_at",
    }
)


_OKF_GRAPH_DDL = """
    CREATE TABLE IF NOT EXISTS okf_nodes (
        node_id TEXT PRIMARY KEY,
        series_slug TEXT NOT NULL,
        book_slug TEXT,
        node_type TEXT NOT NULL,
        label TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS okf_edges (
        edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
        series_slug TEXT NOT NULL,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        edge_type TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    );

    CREATE INDEX IF NOT EXISTS idx_okf_nodes_series_type ON okf_nodes(series_slug, node_type);
    CREATE INDEX IF NOT EXISTS idx_okf_edges_source_type ON okf_edges(source_id, edge_type);
    CREATE INDEX IF NOT EXISTS idx_okf_edges_target_type ON okf_edges(target_id, edge_type);
    CREATE INDEX IF NOT EXISTS idx_okf_edges_series_type ON okf_edges(series_slug, edge_type);
    CREATE INDEX IF NOT EXISTS idx_okf_edges_src ON okf_edges(series_slug, source_id, edge_type);
    CREATE INDEX IF NOT EXISTS idx_okf_edges_dst ON okf_edges(series_slug, target_id, edge_type);

    CREATE TABLE IF NOT EXISTS graph_sync_meta (
        series_slug TEXT PRIMARY KEY,
        fingerprint_sha256 TEXT NOT NULL,
        updated_at REAL NOT NULL
    );
"""


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table});")}


def _migrate(conn: sqlite3.Connection) -> bool:
    """Bring a pre-v0.7.0 database to SCHEMA_VERSION. Returns True when a migration ran.

    * FTS5 tables are derived from the Markdown tree, so they are dropped and rebuilt (adopting the
      'porter unicode61 remove_diacritics 2' tokenizer and i18n slug partitioning).
    * keyword_signals is updated to include cluster_variants_json if missing.
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
    elif legacy_cols and "cluster_variants_json" not in legacy_cols:
        conn.execute("ALTER TABLE keyword_signals ADD COLUMN cluster_variants_json TEXT NOT NULL DEFAULT '[]';")

    if version < 4:
        conn.executescript(_OKF_GRAPH_DDL)

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
    # 1. FTS5 Virtual Table for OKF v0.2 Evidence Cards (ARC-78: porter + unicode61 + remove_diacritics 2)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS evidence_cards_fts USING fts5(
            series_slug, book_slug, card_slug, title, body,
            tokenize = 'porter unicode61 remove_diacritics 2'
        );
    """)
    # 1b. ARC-72 / ARC-78: FTS5 Virtual Table for Chapter Prose & Search Subtitles
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chapters_fts USING fts5(
            series_slug, book_slug, chapter_slug, title, body,
            tokenize = 'porter unicode61 remove_diacritics 2'
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
    # 5. ARC-84: OKF v0.3 Property Graph (okf_nodes, okf_edges)
    conn.executescript(_OKF_GRAPH_DDL)
    if (repo_root / "series").is_dir():
        reindex_evidence_cards(conn, repo_root)
        reindex_chapters(conn, repo_root)
        try:
            ensure_series_graph(conn, repo_root)
        except Exception:
            pass
    conn.commit()


def compute_series_fingerprint(repo_root: Path, series_slug: str) -> str:
    """Compute fast SHA-256 manifest fingerprint over file paths + (mtime_ns, size) in a series."""
    import hashlib
    series_dir = repo_root / "series"
    if "/i18n/" in series_slug:
        parent_name, lang = series_slug.split("/i18n/")
        base_paths = [series_dir / parent_name / "i18n" / lang, series_dir / parent_name]
    else:
        base_paths = [series_dir / series_slug]

    file_entries: list[tuple[str, int, int]] = []
    seen_paths: set[Path] = set()
    for bp in base_paths:
        if not bp.is_dir():
            continue
        for pattern in (
            "**/chapters/*.md",
            "**/evidence-cards/*.md",
            "**/sources.bib",
            "characters.md",
            "series.yaml",
            "style/jargon-to-notes.yml",
            "style/lexicon.yaml",
        ):
            for p in bp.glob(pattern):
                if p.is_file() and p not in seen_paths and "preliminary" not in p.parts and not p.name.startswith("_"):
                    seen_paths.add(p)
                    st = p.stat()
                    file_entries.append((p.relative_to(repo_root).as_posix(), st.st_mtime_ns, st.st_size))

    file_entries.sort()
    hasher = hashlib.sha256()
    for path_str, mtime, size in file_entries:
        hasher.update(f"{path_str}:{mtime}:{size}\n".encode("utf-8"))
    return hasher.hexdigest()


def ensure_series_graph(
    conn: sqlite3.Connection,
    repo_root: Path,
    series_slug: Optional[str] = None,
    force: bool = False,
) -> bool:
    """Ensure OKF property graph is synchronized with disk state.

    Returns False in < 1 ms if series fingerprint matches graph_sync_meta and nodes exist.
    Rebuilds via build_series_knowledge_graph if fingerprint diverges or nodes are missing.
    """
    from bwe.graph_rag import build_series_knowledge_graph
    import time

    conn.executescript(_OKF_GRAPH_DDL)

    series_dir = repo_root / "series"
    if not series_dir.is_dir():
        return False

    if series_slug:
        slugs = [series_slug]
    else:
        discovered: set[str] = set()
        for ch in series_dir.glob("**/chapters/*.md"):
            if ch.name.startswith("_") or "preliminary" in ch.parts:
                continue
            rel = ch.relative_to(series_dir).parts
            s_slug, _ = resolve_series_and_book_slug(rel)
            discovered.add(s_slug)
        slugs = sorted(discovered)

    rebuilt_any = False
    for s_slug in slugs:
        current_fp = compute_series_fingerprint(repo_root, s_slug)
        if not force:
            row = conn.execute(
                "SELECT fingerprint_sha256 FROM graph_sync_meta WHERE series_slug = ?",
                (s_slug,),
            ).fetchone()
            if row and row[0] == current_fp:
                node_cnt = conn.execute(
                    "SELECT COUNT(*) FROM okf_nodes WHERE series_slug = ?",
                    (s_slug,),
                ).fetchone()[0]
                if node_cnt > 0:
                    continue

        build_series_knowledge_graph(conn, repo_root, series_slug=s_slug)
        conn.execute(
            "INSERT OR REPLACE INTO graph_sync_meta (series_slug, fingerprint_sha256, updated_at) VALUES (?, ?, ?)",
            (s_slug, current_fp, time.time()),
        )
        conn.commit()
        rebuilt_any = True

    return rebuilt_any


def _extract_card_title(text: str, default: str) -> str:
    parts: list[str] = []
    fm_title = re.search(r'^title:\s*"?([^"\n]+)"?', text, re.MULTILINE)
    if fm_title:
        parts.append(fm_title.group(1).strip())
    fm_tags = re.search(r"^tags:\s*\[([^\]]+)\]", text, re.MULTILINE)
    if fm_tags:
        parts.append(fm_tags.group(1).replace(",", " ").replace("-", " ").strip())
    h1 = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")), "")
    if h1 and h1 not in parts:
        parts.append(h1)
    if not parts:
        fallback = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), default)
        parts.append(fallback)
    return " — ".join(parts)


def _extract_chapter_title(text: str, default: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parts: list[str] = []
    for ln in lines[:4]:
        if ln.startswith("#"):
            parts.append(ln.lstrip("# ").strip())
        elif ln.startswith("*") and ln.endswith("*") and len(ln) > 2:
            parts.append(ln.strip("* ").strip())
    return " — ".join(parts) if parts else default


def resolve_series_and_book_slug(rel_parts: tuple[str, ...]) -> tuple[str, str]:
    """Derive (series_slug, book_slug) from paths relative to series_dir.

    Root single-book:
        ('parenthood-atlas', 'chapters', '01.md') -> ('parenthood-atlas', 'root')
    Multi-book series:
        ('architectures-of-memory', 'book-01-vanishing-signal', 'chapters', '01.md')
        -> ('architectures-of-memory', 'book-01-vanishing-signal')
    Nested i18n series:
        ('parenthood-atlas', 'i18n', 'es', 'chapters', '01.md') -> ('parenthood-atlas/i18n/es', 'root')
        ('architectures-of-memory', 'i18n', 'es', 'book-01', 'chapters', '01.md')
        -> ('architectures-of-memory/i18n/es', 'book-01')
    """
    if "i18n" in rel_parts:
        idx = rel_parts.index("i18n")
        parent_slug = "/".join(rel_parts[:idx])
        lang = rel_parts[idx + 1]
        series_slug = f"{parent_slug}/i18n/{lang}"
        tail = rel_parts[idx + 2:]
        if len(tail) > 2 and tail[0].startswith("book-"):
            book_slug = tail[0]
        else:
            book_slug = "root"
        return series_slug, book_slug

    series_slug = rel_parts[0]
    book_slug = rel_parts[1] if len(rel_parts) > 3 and rel_parts[1].startswith("book-") else "root"
    return series_slug, book_slug


def normalize_series_and_lang(series_slug: str, lang: str | None = None) -> tuple[str, str]:
    """Normalize series_slug (e.g. 'parenthood-atlas-es' or 'parenthood-atlas/i18n/es')
    into (canonical_series_slug, effective_lang).
    """
    raw = series_slug.strip("/\\")
    slug_lang = "en"
    if "/i18n/" in raw:
        parts = raw.split("/i18n/")
        clean_series = parts[0].strip("/\\")
        slug_lang = parts[1].split("/")[0].strip() or "en"
    elif raw.endswith("-es"):
        clean_series = raw[:-3]
        slug_lang = "es"
    elif raw.endswith("-fr"):
        clean_series = raw[:-3]
        slug_lang = "fr"
    else:
        clean_series = raw

    effective_lang = lang if lang is not None else slug_lang
    return clean_series, effective_lang


def resolve_edition_dir(series_slug: str, lang: str | None = None, repo_root: Path | None = None) -> Path:
    """Resolve the filesystem directory for a series edition and language.

    - If lang == 'en' (or series_slug already ends with /i18n/{lang}):
      resolve to series_dir / clean_slug (stripping /i18n/* and -es/-fr suffixes).
    - If lang in ('es', 'fr') (or inferred from series_slug when lang is None):
      resolve to series_dir / clean_slug / 'i18n' / lang when it exists.
    """
    root = repo_root or Path(__file__).resolve().parent.parent
    series_dir = root / "series"
    clean_series, effective_lang = normalize_series_and_lang(series_slug, lang)

    if effective_lang in ("es", "fr"):
        candidate = series_dir / clean_series / "i18n" / effective_lang
        if candidate.is_dir():
            return candidate

    if "i18n" in series_slug and effective_lang != "en":
        target = series_dir / series_slug.strip("/\\")
        if target.is_dir():
            return target

    return series_dir / clean_series


def reindex_evidence_cards(conn: sqlite3.Connection, repo_root: Path) -> None:
    conn.execute("DELETE FROM evidence_cards_fts;")
    series_dir = repo_root / "series"
    for card_path in series_dir.glob("**/evidence-cards/*.md"):
        if card_path.name.startswith("_") or card_path.name.lower() in {"index.md", "readme.md"}:
            continue
        if "preliminary" in card_path.parts:
            continue
        rel_parts = card_path.relative_to(series_dir).parts
        series_slug, book_slug = resolve_series_and_book_slug(rel_parts)
        text = card_path.read_text(encoding="utf-8", errors="replace")
        title = _extract_card_title(text, card_path.stem)
        conn.execute(
            "INSERT INTO evidence_cards_fts (series_slug, book_slug, card_slug, title, body) VALUES (?, ?, ?, ?, ?)",
            (series_slug, book_slug, card_path.stem, title, text),
        )
    conn.commit()


def reindex_chapters(conn: sqlite3.Connection, repo_root: Path) -> None:
    conn.execute("DELETE FROM chapters_fts;")
    series_dir = repo_root / "series"
    for ch_path in series_dir.glob("**/chapters/*.md"):
        if ch_path.name.startswith("_") or ch_path.name.lower() in {"index.md", "readme.md"}:
            continue
        if "preliminary" in ch_path.parts:
            continue
        rel_parts = ch_path.relative_to(series_dir).parts
        series_slug, book_slug = resolve_series_and_book_slug(rel_parts)
        text = ch_path.read_text(encoding="utf-8", errors="replace")
        title = _extract_chapter_title(text, ch_path.stem)
        conn.execute(
            "INSERT INTO chapters_fts (series_slug, book_slug, chapter_slug, title, body) VALUES (?, ?, ?, ?, ?)",
            (series_slug, book_slug, ch_path.stem, title, text),
        )
    conn.commit()


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

_LEXICON_CACHE: dict[Path, dict[str, list[str]]] = {}


def _load_lexicon_term_mapping(lexicon_path: Path) -> dict[str, list[str]]:
    """Map localized words from style/lexicon.yaml terms to English words."""
    if lexicon_path in _LEXICON_CACHE:
        return _LEXICON_CACHE[lexicon_path]
    mapping: dict[str, list[str]] = {}
    if not lexicon_path.is_file():
        _LEXICON_CACHE[lexicon_path] = mapping
        return mapping
    try:
        import yaml
        data = yaml.safe_load(lexicon_path.read_text(encoding="utf-8")) or {}
        terms = data.get("terms") or {}
        for _term_key, term_val in terms.items():
            if isinstance(term_val, dict):
                en_phrase = term_val.get("en", "")
                en_words = [w.lower() for w in re.findall(r"[a-z0-9]+", en_phrase) if len(w) > 2]
                for lang_key, loc_phrase in term_val.items():
                    if lang_key == "en" or not isinstance(loc_phrase, str):
                        continue
                    norm = unicodedata.normalize("NFD", loc_phrase.lower())
                    loc_clean = "".join(c for c in norm if unicodedata.category(c) != "Mn")
                    for w in re.findall(r"[a-z0-9]+", loc_clean):
                        if len(w) > 2:
                            mapping.setdefault(w, []).extend(en_words)
    except Exception:
        pass
    for k in mapping:
        mapping[k] = list(dict.fromkeys(mapping[k]))
    _LEXICON_CACHE[lexicon_path] = mapping
    return mapping


@dataclass(frozen=True)
class CoverageResult:
    chapter_score: float          # 0..1, saturating transform of the best chapter BM25
    card_score: float             # 0..1, same for OKF evidence cards
    chapter: Optional[str]        # "book-01-.../03-slug" or "03-slug"; None when nothing matched
    card: Optional[str]
    raw_chapter_bm25: float       # positive magnitude of -bm25()
    raw_card_bm25: float
    is_i18n_without_cards: bool = False

    @property
    def combined(self) -> float:
        """Single 0..1 relevance weight: chapter prose dominates, the card corroborates."""
        if self.is_i18n_without_cards and self.card_score == 0.0:
            return self.chapter_score
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


STOPWORDS: set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "should", "could", "can",
    "may", "might", "must", "vs", "versus", "about", "what", "when", "why", "how",
    "de", "la", "el", "los", "las", "en", "y", "o", "un", "una", "unos", "unas",
    "del", "al", "con", "por", "para", "como", "que", "es", "son",
}


def _best_document(
    conn: sqlite3.Connection,
    table: str,
    label_sql: str,
    series_slug: str,
    match: str,
    terms: list[str],
    saturation: float,
    co_cited_cards: Optional[set[str]] = None,
) -> tuple[Optional[sqlite3.Row], float, float]:
    """Return (best row, raw BM25 magnitude, normalised coverage 0..1) for one FTS5 table."""
    rows = conn.execute(
        f"""
        SELECT rowid AS rid, {label_sql}, bm25({table}, {_BM25_WEIGHTS}) AS s
        FROM {table} WHERE series_slug = ? AND {table} MATCH ? ORDER BY s;
        """,
        (series_slug, match),
    ).fetchall()
    if not rows:
        return None, 0.0, 0.0

    non_stopwords = [t for t in terms if t.lower() not in STOPWORDS]
    best: Optional[tuple[float, int, int, float, sqlite3.Row]] = None

    for row in rows:
        rid = int(row["rid"])
        hits = 0
        title_hits = 0
        matched_terms: list[str] = []
        for term in terms:
            if conn.execute(
                f"SELECT 1 FROM {table} WHERE rowid = ? AND {table} MATCH ?;",
                (rid, f'{{title body}} : "{term}"'),
            ).fetchone():
                hits += 1
                matched_terms.append(term)
            if conn.execute(
                f"SELECT 1 FROM {table} WHERE rowid = ? AND {table} MATCH ?;",
                (rid, f'{{title}} : "{term}"'),
            ).fetchone():
                title_hits += 1

        fraction = hits / len(terms) if terms else 0.0

        # Term-fraction gating for Evidence Cards (ARC-93)
        if table == "evidence_cards_fts" and len(non_stopwords) >= 2:
            matched_non_stopwords = {t for t in matched_terms if t.lower() not in STOPWORDS}
            if len(matched_non_stopwords) < 2 and fraction < 0.50:
                continue

        # SQLite FTS5 clamps IDF to 1e-6 when a term appears in >=50% of the table across series
        # (e.g. "training", "memory", "model"); adding a per-hit floor preserves multi-term and
        # title/subtitle relevance before scaling by sqrt(term fraction).
        raw = max(0.0, -float(row["s"])) + 1.5 * hits + 2.0 * title_hits
        score = _normalize_bm25(raw, saturation) * math.sqrt(fraction)

        # Co-citation boost for candidate cards directly cited by the winning chapter (ARC-93)
        if table == "evidence_cards_fts" and co_cited_cards:
            card_slug = row["card_slug"] if "card_slug" in row.keys() else None
            if card_slug and card_slug in co_cited_cards:
                score = min(1.0, score * 1.25)
                raw = raw * 1.25

        cand = (score, hits, title_hits, raw, row)
        if best is None or cand[:4] > best[:4]:
            best = cand

    if best is None:
        return None, 0.0, 0.0

    score, _hits, _title_hits, raw, winner = best
    return winner, raw, score


def bm25_coverage(
    conn: sqlite3.Connection,
    series_slug: str,
    tokens: Iterable[str],
    saturation: float = BM25_SATURATION,
    repo_root: Optional[Path] = None,
) -> CoverageResult:
    """Score how well a series' chapters and OKF cards answer a query, continuously.

    The tokens are OR-ed (partial matches still count; BM25's IDF weights rare terms such as
    "peanut" above common ones), restricted to title/body, with titles weighted 3x. The best
    chapter and best card per series are kept, and each score is scaled by the share of query
    terms the winning document really contains.

    For nested i18n series (e.g. 'parenthood-atlas/i18n/es') that share the parent's evidence
    cards, localized query tokens are translated to English via style/lexicon.yaml before
    querying the parent's evidence_cards_fts index.
    """
    terms = [t for t in dict.fromkeys(tokens) if re.fullmatch(r"[a-z0-9]+", t)]
    match = _fts_or_query(terms)
    if not match:
        return CoverageResult(0.0, 0.0, None, None, 0.0, 0.0)

    ch, raw_ch, score_ch = _best_document(
        conn, "chapters_fts", "book_slug, chapter_slug", series_slug, match, terms, saturation
    )

    # ARC-93 / ARC-94: Extract co-cited cards from the winning chapter in okf_edges
    co_cited_cards: set[str] = set()
    if ch:
        best_ch_slug = ch["chapter_slug"]
        clean_ch_slug = best_ch_slug.split("/")[-1]
        parent_slug = series_slug.partition("/i18n/")[0] if "/i18n/" in series_slug else series_slug
        try:
            cited_rows = conn.execute(
                """
                SELECT target_id FROM okf_edges
                WHERE (series_slug = ? OR series_slug = ? OR series_slug LIKE ?)
                  AND source_id LIKE ?
                  AND edge_type = 'CITES_CARD';
                """,
                (series_slug, parent_slug, f"{parent_slug}%", f"%:{clean_ch_slug}"),
            ).fetchall()
            for cr in cited_rows:
                co_cited_cards.add(cr[0].split(":")[-1])
        except Exception:
            pass

    is_i18n_without_cards = False
    if "/i18n/" in series_slug:
        has_local_cards = conn.execute(
            "SELECT 1 FROM evidence_cards_fts WHERE series_slug = ? LIMIT 1;",
            (series_slug,),
        ).fetchone()
        if not has_local_cards:
            is_i18n_without_cards = True
            parent_slug, _, lang = series_slug.partition("/i18n/")
            root = repo_root or Path(__file__).resolve().parent.parent
            lexicon_path = root / "series" / parent_slug / "i18n" / lang / "style" / "lexicon.yaml"
            mapping = _load_lexicon_term_mapping(lexicon_path)
            en_mapped: list[str] = []
            unmapped: list[str] = []
            for t in terms:
                norm_t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
                en_w = mapping.get(t, []) or mapping.get(norm_t, [])
                if en_w:
                    en_mapped.extend(en_w)
                elif t.lower() not in STOPWORDS:
                    unmapped.append(t)
            # ARC-94: Evaluate term-fraction gate on mapped English terms + loanwords/cognates
            card_terms = [t for t in dict.fromkeys(en_mapped + unmapped or terms) if re.fullmatch(r"[a-z0-9]+", t)]
            all_search_terms = [t for t in dict.fromkeys(en_mapped + terms) if re.fullmatch(r"[a-z0-9]+", t)]
            card_match = _fts_or_query(all_search_terms)
            card, raw_card, score_card = _best_document(
                conn, "evidence_cards_fts", "card_slug", parent_slug, card_match, card_terms, saturation,
                co_cited_cards=co_cited_cards,
            )
        else:
            card, raw_card, score_card = _best_document(
                conn, "evidence_cards_fts", "card_slug", series_slug, match, terms, saturation,
                co_cited_cards=co_cited_cards,
            )
    else:
        card, raw_card, score_card = _best_document(
            conn, "evidence_cards_fts", "card_slug", series_slug, match, terms, saturation,
            co_cited_cards=co_cited_cards,
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
        is_i18n_without_cards=is_i18n_without_cards,
    )


compute_coverage_score = bm25_coverage
