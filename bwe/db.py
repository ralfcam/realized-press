# bwe/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(".cache/bwe_state.db")


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db(repo_root: Path) -> None:
    with get_db() as conn:
        # 1. FTS5 Virtual Table for OKF v0.2 Evidence Cards
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS evidence_cards_fts USING fts5(
                series_slug, book_slug, card_slug, title, body
            );
        """)
        # 1b. ARC-72: FTS5 Virtual Table for Chapter Prose & Search Subtitles
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chapters_fts USING fts5(
                series_slug, book_slug, chapter_slug, title, body
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
        # 4. ARC-72: Google Keyword Planner & Trends Demand Signals
        conn.execute("""
            CREATE TABLE IF NOT EXISTS keyword_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_slug TEXT NOT NULL,
                query TEXT NOT NULL,
                monthly_volume INTEGER NOT NULL,
                yoy_trend_pct REAL NOT NULL,
                competition_index REAL NOT NULL,
                target_chapter TEXT,
                paa_question_hook TEXT,
                matched_chapter TEXT,
                matched_card TEXT,
                opportunity_score REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
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
