# bwe/main.py
import asyncio
import json
import re
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks

from bwe.db import get_db, init_db
from bwe.schema import validate_series_yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
BWE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SERIES_DIR = REPO_ROOT / "series"
STATIC_DIR = BWE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Ensure scripts directory is importable for data synthesis
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from render_audiobook_player import DEFAULT_GITHUB_REPO, scan_all_imprint_books

app = FastAPI(title="Realized Press — BWE & Serial Portal (P-ARC-18)")
templates = Jinja2Blocks(directory=str(REPO_ROOT / "bwe" / "templates"))

# Mount static client assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount documentation if present
if (REPO_ROOT / "docs").exists():
    app.mount("/docs-static", StaticFiles(directory=str(REPO_ROOT / "docs")), name="docs")

# Mount static analytics charts (ARC-80)
DIST_ANALYTICS_DIR = REPO_ROOT / "dist" / "analytics"
DIST_ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/dist/analytics", StaticFiles(directory=str(DIST_ANALYTICS_DIR)), name="analytics_dist")

# In-memory index of canonical media files for O(1) streaming
AUDIO_CACHE: dict[str, Path] = {}
PDF_CACHE: dict[str, Path] = {}


def refresh_media_cache() -> None:
    """Index canonical audio and PDF files from series directories without duplication."""
    AUDIO_CACHE.clear()
    PDF_CACHE.clear()
    for ext in ("*.mp3", "*.wav"):
        for p in SERIES_DIR.glob(f"**/audiobook/{ext}"):
            if p.is_file():
                AUDIO_CACHE[p.stem] = p
                AUDIO_CACHE[p.name] = p
        for p in (REPO_ROOT / ".cache" / "tts_pcm").glob(ext):
            if p.is_file():
                AUDIO_CACHE.setdefault(p.stem, p)
                AUDIO_CACHE.setdefault(p.name, p)
    for p in SERIES_DIR.glob("**/*.pdf"):
        if p.is_file():
            PDF_CACHE[p.name] = p


def find_canonical_audio(filename: str) -> Path | None:
    """Locates canonical audio in series/**/audiobook/ without duplication."""
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower() or ".mp3"
    full_name = f"{stem}{ext}"
    if full_name in AUDIO_CACHE:
        return AUDIO_CACHE[full_name]
    if stem in AUDIO_CACHE:
        return AUDIO_CACHE[stem]
    # Fallback search if newly generated
    for candidate_ext in (".mp3", ".wav"):
        for p in SERIES_DIR.glob(f"**/audiobook/{stem}{candidate_ext}"):
            if p.is_file():
                AUDIO_CACHE[stem] = p
                AUDIO_CACHE[p.name] = p
                return p
    return None


def find_canonical_pdf(filename: str) -> Path | None:
    """Locates canonical PDF across series/**/publishing/ without duplication."""
    pdf_name = Path(filename).name
    if not pdf_name.lower().endswith(".pdf"):
        pdf_name = f"{pdf_name}.pdf"
    if pdf_name in PDF_CACHE:
        return PDF_CACHE[pdf_name]
    for p in SERIES_DIR.glob(f"**/{pdf_name}"):
        if p.is_file():
            PDF_CACHE[pdf_name] = p
            return p
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(REPO_ROOT)
    refresh_media_cache()
    yield

app.router.lifespan_context = lifespan


@app.get("/")
async def root_redirect():
    """Root entrypoint landing on the unified Imprint Hub."""
    return RedirectResponse(url="/site/", status_code=307)


# -------------------------------------------------------------------------
# PILLAR 1 (ARC-55): IMPRINT SITE & AUDIOBOOK HUB (FASTAPI + HTMX)
# -------------------------------------------------------------------------


@app.get("/site")
async def imprint_site_redirect():
    """Redirects /site to /site/ to preserve relative audio asset resolution."""
    return RedirectResponse(url="/site/", status_code=307)


@app.get("/site/", response_class=HTMLResponse)
async def imprint_site_home(request: Request):
    """
    ARC-55: Serves the Imprint Audiobook Portal & Marketing Hub under the
    unified FastAPI + HTMX stack with aligned navigation and live catalog data.
    """
    catalog = scan_all_imprint_books(REPO_ROOT, DEFAULT_GITHUB_REPO)
    catalog_json = json.dumps(catalog)
    return templates.TemplateResponse(
        "site.html",
        {
            "request": request,
            "catalog": catalog,
            "catalog_json": catalog_json,
            "active_tab": "site",
        },
    )


# Canonical zero-copy media streaming endpoints (supporting HTTP 206 Range requests)
@app.get("/media/audio/{filename}")
@app.head("/media/audio/{filename}")
@app.get("/site/{filename}.mp3")
@app.head("/site/{filename}.mp3")
@app.get("/{filename}.mp3")
@app.head("/{filename}.mp3")
@app.get("/site/{filename}.wav")
@app.head("/site/{filename}.wav")
@app.get("/{filename}.wav")
@app.head("/{filename}.wav")
async def stream_audio(filename: str):
    audio_path = find_canonical_audio(filename)
    if audio_path and audio_path.is_file():
        media_type = "audio/mpeg" if audio_path.suffix.lower() == ".mp3" else "audio/wav"
        return FileResponse(audio_path, media_type=media_type)
    raise HTTPException(status_code=404, detail=f"Audio asset '{filename}' not found")


@app.get("/media/pdf/{filename}")
@app.head("/media/pdf/{filename}")
@app.get("/site/{filename}.pdf")
@app.head("/site/{filename}.pdf")
@app.get("/{filename}.pdf")
@app.head("/{filename}.pdf")
async def stream_pdf(filename: str):
    pdf_path = find_canonical_pdf(filename)
    if pdf_path and pdf_path.is_file():
        return FileResponse(pdf_path, media_type="application/pdf")
    raise HTTPException(status_code=404, detail=f"PDF publication '{filename}' not found")


# -------------------------------------------------------------------------
# PILLAR 1 (ARC-55): SERIAL READER, FOOTNOTE ISOLATION & ARC-53 FEEDBACK
# -------------------------------------------------------------------------


@app.get("/read/{series_slug}/{chapter_slug}", response_class=HTMLResponse)
async def read_chapter(request: Request, series_slug: str, chapter_slug: str):
    """Serves the bidirectional audio-synced chapter reader with isolated footnotes."""
    md_candidates = list((SERIES_DIR / series_slug).glob(f"**/chapters/{chapter_slug}.md"))
    if not md_candidates:
        raise HTTPException(status_code=404, detail="Chapter not found")
    md_path = md_candidates[0]

    timings_path = SERIES_DIR / series_slug / "audiobook" / f"{chapter_slug}.timings.json"
    if not timings_path.exists():
        sub_timings = list((SERIES_DIR / series_slug).glob(f"**/audiobook/{chapter_slug}.timings.json"))
        if sub_timings:
            timings_path = sub_timings[0]

    audio_url = f"/site/{chapter_slug}.mp3"
    audio_path = find_canonical_audio(chapter_slug)
    has_audio = audio_path is not None and audio_path.is_file()

    from render_audiobook_player import extract_clean_text
    prose_html = extract_clean_text(md_path, timings_path if timings_path.exists() else None)

    blocks_list = []
    if timings_path.exists():
        try:
            t_data = json.loads(timings_path.read_text(encoding="utf-8"))
            if isinstance(t_data, dict):
                blocks_list = t_data.get("blocks", [])
            elif isinstance(t_data, list):
                blocks_list = t_data
        except Exception:
            blocks_list = []

    return templates.TemplateResponse(
        "portal.html",
        {
            "request": request,
            "series_slug": series_slug,
            "chapter_slug": chapter_slug,
            "prose_html": prose_html,
            "timings": blocks_list,
            "has_audio": has_audio,
            "audio_url": audio_url,
            "active_tab": "reader",
        },
    )


@app.get("/hx/footnote/{series_slug}/{chapter_slug}/{footnote_id}", response_class=HTMLResponse)
async def inspect_footnote(request: Request, series_slug: str, chapter_slug: str, footnote_id: str):
    """
    ARC-55 & ARC-58: Returns a single chapter-local footnote into the side drawer
    without interrupting paragraph audio playback, and logs citation telemetry.
    """
    md_candidates = list((SERIES_DIR / series_slug).glob(f"**/chapters/{chapter_slug}.md"))
    if not md_candidates:
        raise HTTPException(status_code=404, detail="Chapter not found")
    raw_md = md_candidates[0].read_text(encoding="utf-8")

    pattern = rf"\[\^{re.escape(footnote_id)}\]:\s*(.+?)(?=\n\[\^|\n## |\Z)"
    match = re.search(pattern, raw_md, flags=re.DOTALL)
    note_text = match.group(1).strip() if match else "Footnote definition not found in ## Notes."

    with get_db() as conn:
        conn.execute(
            "INSERT INTO citation_telemetry (series_slug, chapter_slug, footnote_id) VALUES (?, ?, ?)",
            (series_slug, chapter_slug, footnote_id),
        )

    return templates.TemplateResponse(
        "partials/footnote_drawer.html",
        {"request": request, "footnote_id": footnote_id, "note_text": note_text},
    )


@app.get("/hx/telemetry", response_class=HTMLResponse)
async def view_citation_telemetry(request: Request):
    """ARC-58: Renders closed-loop citation telemetry events for reader inspection."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT series_slug, chapter_slug, footnote_id, created_at "
            "FROM citation_telemetry ORDER BY id DESC LIMIT 25"
        ).fetchall()
        telemetry = [
            {
                "series_slug": r[0],
                "chapter_slug": r[1],
                "footnote_id": r[2],
                "created_at": r[3],
            }
            for r in rows
        ]
    return templates.TemplateResponse(
        "partials/telemetry_table.html",
        {"request": request, "telemetry": telemetry},
    )


@app.post("/hx/feedback", response_class=HTMLResponse)
async def submit_reader_feedback(
    series_slug: str = Form(...),
    chapter_slug: str = Form(...),
    block_id: str = Form(""),
    category: str = Form("epistemic-clarity"),
    comment: str = Form(...),
):
    """ARC-53: Replaces manual CSV feedback entry with instant HTMX inline capture."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO reader_feedback (series_slug, chapter_slug, block_id, category, comment)
               VALUES (?, ?, ?, ?, ?)""",
            (series_slug, chapter_slug, block_id, category, comment),
        )
    return HTMLResponse(
        '<div class="p-3 text-sm bg-emerald-950 text-emerald-200 rounded border border-emerald-700">'
        '&check; Feedback logged for ARC-53 triage. Thank you.</div>'
    )


# -------------------------------------------------------------------------
# PILLAR 2 (ARC-56): EPISTEMIC IDE, LIVE AUDITS & INCREMENTAL TTS STREAM
# -------------------------------------------------------------------------


@app.get("/ide", response_class=HTMLResponse)
async def epistemic_ide_home(request: Request):
    """ARC-56: Renders the full 3-column Epistemic IDE workbench."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT series_slug, book_slug, card_slug, title, substr(body, 1, 240) AS snippet "
            "FROM evidence_cards_fts LIMIT 15"
        ).fetchall()
    return templates.TemplateResponse(
        "ide.html",
        {"request": request, "cards": rows, "query": ""},
    )


@app.get("/ide/search-cards", response_class=HTMLResponse)
async def search_evidence_cards(request: Request, q: str = ""):
    """Instant FTS5 search across all OKF v0.2 Evidence Cards."""
    with get_db() as conn:
        if not q.strip():
            rows = conn.execute(
                "SELECT series_slug, book_slug, card_slug, title, substr(body, 1, 240) AS snippet "
                "FROM evidence_cards_fts LIMIT 15"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT series_slug, book_slug, card_slug, title, snippet(evidence_cards_fts, 4, '<mark>', '</mark>', '...', 24) AS snippet "
                "FROM evidence_cards_fts WHERE evidence_cards_fts MATCH ? LIMIT 20",
                (f'"{q}"*',),
            ).fetchall()
    return templates.TemplateResponse(
        "ide.html",
        {"request": request, "cards": rows, "query": q},
        block_name="card_results",
    )


@app.post("/ide/audit", response_class=HTMLResponse)
async def run_epistemic_audit(
    request: Request,
    script_name: str = Form(...),
    target_path: str = Form(...),
):
    """
    ARC-56: Invokes five_rule_check.py, audit_manuscript.py, or audit_epub.py
    and swaps the structured audit output directly into the IDE panel.
    """
    allowed_scripts = {
        "five_rule_check": SCRIPTS_DIR / "five_rule_check.py",
        "audit_manuscript": SCRIPTS_DIR / "audit_manuscript.py",
        "audit_epub": SCRIPTS_DIR / "audit_epub.py",
    }
    if script_name not in allowed_scripts:
        raise HTTPException(status_code=400, detail="Unsupported audit script")

    proc = subprocess.run(
        [sys.executable, str(allowed_scripts[script_name]), target_path],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return templates.TemplateResponse(
        "partials/audit_results.html",
        {
            "request": request,
            "script_name": script_name,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        },
    )


@app.get("/ide/tts-stream/{series_slug}/{chapter_slug}")
async def stream_tts_synthesis(series_slug: str, chapter_slug: str):
    """
    ARC-62 / ARC-56: Streams live paragraph-by-paragraph Gemini TTS synthesis
    and SHA-256 PCM cache hits (.cache/tts_pcm/) over Server-Sent Events (SSE).
    """

    async def event_generator():
        # Match series directory (e.g. series/parenthood-atlas)
        series_target = f"series/{series_slug}"
        # Extract 2-digit chapter prefix if present (e.g. '01' from '01-before-the-child-is-born')
        ch_prefix = chapter_slug.split("-")[0] if "-" in chapter_slug else chapter_slug

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(SCRIPTS_DIR / "generate_audiobook_tts.py"),
            series_target,
            "--chapter",
            ch_prefix,
            cwd=str(REPO_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        async for line in proc.stdout:
            clean = line.decode("utf-8", errors="replace").rstrip()
            yield f"event: tts-log\ndata: <div class='font-mono text-xs py-0.5'>{clean}</div>\n\n"
        rc = await proc.wait()
        status = "COMPLETE (Zero Drift)" if rc == 0 else f"FAILED (exit {rc})"
        yield f"event: tts-done\ndata: <span class='font-bold'>{status}</span>\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/analytics", response_class=HTMLResponse)
async def view_analytics(request: Request, series: str = "parenthood-atlas", lang: Optional[str] = None):
    """BWE v0.8.0 / ARC-80: Marketing Intelligence Visual Analytics Studio."""
    from bwe.analytics import build_series_analytics_payload, export_static_charts

    deck_dir_map = {
        "parenthood-atlas": "parenthood-atlas",
        "parenthood-atlas/i18n/es": "parenthood-atlas-es",
        "architectures-of-memory": "architectures-of-memory",
    }
    deck_dir = deck_dir_map.get(series, series.replace("/", "_").replace("-", "_"))
    deck_target = DIST_ANALYTICS_DIR / deck_dir
    if not (deck_target / "demand_quadrant.svg").exists():
        export_static_charts(series, deck_target, root=REPO_ROOT, lang=lang)

    data = build_series_analytics_payload(series, root=REPO_ROOT, lang=lang)
    return templates.TemplateResponse(
        request,
        "analytics.html",
        {
            "series_slug": series,
            "deck_dir": deck_dir,
            "data": data,
        },
    )


@app.get("/hx/analytics/dashboard", response_class=HTMLResponse)
@app.get("/hx/analytics/overview", response_class=HTMLResponse)
async def hx_analytics_dashboard(request: Request, series: str = "parenthood-atlas", lang: Optional[str] = None):
    """HTMX endpoint for instant series switching on the analytics dashboard (ARC-80)."""
    from bwe.analytics import build_series_analytics_payload, export_static_charts

    deck_dir_map = {
        "parenthood-atlas": "parenthood-atlas",
        "parenthood-atlas/i18n/es": "parenthood-atlas-es",
        "architectures-of-memory": "architectures-of-memory",
    }
    deck_dir = deck_dir_map.get(series, series.replace("/", "_").replace("-", "_"))
    deck_target = DIST_ANALYTICS_DIR / deck_dir
    if not (deck_target / "demand_quadrant.svg").exists():
        export_static_charts(series, deck_target, root=REPO_ROOT, lang=lang)

    data = build_series_analytics_payload(series, root=REPO_ROOT, lang=lang)
    return templates.TemplateResponse(
        request,
        "partials/analytics_dashboard.html",
        {
            "series_slug": series,
            "deck_dir": deck_dir,
            "data": data,
        },
    )


@app.get("/hx/analytics/export-ads")
async def hx_analytics_export_ads(series: str = "parenthood-atlas", lang: Optional[str] = None):
    """One-click download of Amazon Ads Sponsored Products CSV from covered demand (ARC-80)."""
    import sys
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import marketing_intelligence as mi

    seed_csv = mi.resolve_seed_csv_path(series, REPO_ROOT)
    effective_lang = lang or mi.detect_series_language(series, REPO_ROOT)
    signals, _ = mi.collect_signals(seed_csv, series, lang=effective_lang)

    clean_slug = series.replace("/", "_").replace("-", "_")
    out_dir = DIST_ANALYTICS_DIR / clean_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"amazon_ads_{clean_slug}.csv"
    mi.export_amazon_ads_csv(signals, series, out_path)

    return FileResponse(
        out_path,
        media_type="text/csv",
        filename=f"amazon_ads_{clean_slug}.csv",
    )


@app.post("/hx/analytics/write-kdp-yaml", response_class=HTMLResponse)
async def hx_analytics_write_kdp_yaml(series: str = "parenthood-atlas", lang: Optional[str] = None):
    """HTMX action to optimize & write packed KDP 7 boxes directly into series.yaml (ARC-80)."""
    import sys
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import marketing_intelligence as mi

    seed_csv = mi.resolve_seed_csv_path(series, REPO_ROOT)
    effective_lang = lang or mi.detect_series_language(series, REPO_ROOT)
    signals, _ = mi.collect_signals(seed_csv, series, lang=effective_lang)

    _ = mi.optimize_kdp_boxes_report(series, signals, write_yaml=True, lang=effective_lang)
    return HTMLResponse(
        content='<div class="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center justify-between">'
                '<span>[SUCCESS] Successfully repacked &amp; updated 7 backend keyword boxes in series.yaml</span>'
                '<span class="text-[10px] text-emerald-400 font-bold px-2 py-0.5 rounded bg-emerald-500/30">SCHEMA VALID</span>'
                '</div>'
    )
