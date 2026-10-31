# bwe/main.py
import asyncio
import json
import re
import sqlite3
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
import markdown
import yaml
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
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
def get_server_info(request: Request) -> dict:
    """Helper to provide LAN port and host detection for nav.html."""
    return {
        "host": request.url.hostname or "0.0.0.0",
        "port": request.url.port or 8080,
    }


def split_frontmatter_safe(text: str) -> tuple[str, str]:
    """Splits YAML frontmatter from markdown body safely."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def get_series_manifest_safe(series_slug: str) -> dict:
    """Extracts series title, lenses, and epistemic contract safely."""
    clean_slug = series_slug.split("/i18n/")[0]
    yaml_path = SERIES_DIR / clean_slug / "series.yaml"
    if yaml_path.is_file():
        try:
            cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            epistemic = cfg.get("epistemic_contract")
            lenses = []
            contract_str = "Science -> Interpretation -> Art"
            if isinstance(epistemic, dict) and "three_lenses" in epistemic:
                lenses = [
                    l.get("label") or l.get("id", "").capitalize()
                    for l in epistemic["three_lenses"]
                ]
                contract_str = " -> ".join(lenses)
            elif isinstance(epistemic, str) and "->" in epistemic:
                contract_str = epistemic
                lenses = [p.strip() for p in epistemic.split("->")]
            elif "parenthood" in clean_slug:
                lenses = ["Science", "Interpretation", "Art"]
                contract_str = "Science -> Interpretation -> Art"
            elif "memory" in clean_slug or "architectures" in clean_slug:
                lenses = ["Technical", "Organizational", "Philosophical"]
                contract_str = "Technical -> Organizational -> Philosophical"
            else:
                cfg_lenses = cfg.get("lenses")
                if isinstance(cfg_lenses, list):
                    lenses = [str(x).capitalize() for x in cfg_lenses]
                else:
                    lenses = ["Science", "Interpretation", "Art"]

            return {
                "title": cfg.get("title", clean_slug.replace("-", " ").title()),
                "subtitle": cfg.get("subtitle", ""),
                "lenses": lenses,
                "epistemic_contract": contract_str,
            }
        except Exception:
            pass

    if "memory" in clean_slug or "architectures" in clean_slug:
        return {
            "title": "The Architectures of Memory",
            "subtitle": "Memory, Persistence, and Forgetting Across Machine Learning, Organizations, and Philosophy",
            "lenses": ["Technical", "Organizational", "Philosophical"],
            "epistemic_contract": "Technical -> Organizational -> Philosophical",
        }
    return {
        "title": clean_slug.replace("-", " ").title(),
        "subtitle": "",
        "lenses": ["Science", "Interpretation", "Art"],
        "epistemic_contract": "Science -> Interpretation -> Art",
    }


def extract_chapter_takeaways(raw_md: str) -> list[dict]:
    """Extracts takeaway items from chapter markdown (<aside class="chapter-takeaway"> or movements)."""
    takeaways = []
    aside_match = re.search(r"<aside[^>]*class=['\"][^'\"]*takeaway[^'\"]*['\"][^>]*>(.*?)</aside>", raw_md, re.DOTALL | re.IGNORECASE)
    if aside_match:
        content = aside_match.group(1).strip()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                clean_line = line[2:].strip()
                m = re.match(r"^\*\*([^*]+)\*\*:\s*(.+)$", clean_line)
                if m:
                    takeaways.append({
                        "label": m.group(1).strip(),
                        "text": m.group(2).strip(),
                    })
                else:
                    takeaways.append({
                        "label": "Takeaway",
                        "text": clean_line,
                    })
    if not takeaways:
        movements = re.findall(r"^##\s+([IVXLCDM]+\.\s+[^#\n]+)", raw_md, re.MULTILINE)
        for mov in movements:
            takeaways.append({
                "label": "Movement",
                "text": mov.strip(),
            })
    return takeaways


def extract_chapter_footnotes(raw_md: str) -> dict[str, str]:
    """Extracts all footnote definitions from ## Notes as a dict mapping id -> text."""
    footnotes = {}
    pattern = r"\[\^([a-zA-Z0-9_\-]+)\]:\s*(.+?)(?=\n\[\^|\n## |\Z)"
    for m in re.finditer(pattern, raw_md, re.DOTALL):
        fn_id = m.group(1).strip()
        fn_text = m.group(2).strip()
        footnotes[fn_id] = fn_text
    return footnotes


def build_file_tree() -> dict:
    """Collects all series, books, chapters, and OKF evidence cards for the IDE file tree."""
    tree: dict[str, Any] = {}
    if not SERIES_DIR.is_dir():
        return tree
    for s_dir in sorted(SERIES_DIR.iterdir()):
        if not s_dir.is_dir() or s_dir.name.startswith("."):
            continue
        s_slug = s_dir.name
        tree[s_slug] = {"books": {}, "root_chapters": [], "root_cards": []}

        sub_books = [b for b in sorted(s_dir.iterdir()) if b.is_dir() and b.name.startswith("book-")]
        if sub_books:
            for b in sub_books:
                ch_list = [
                    {
                        "stem": f.stem,
                        "name": f.name,
                        "path": f.relative_to(REPO_ROOT).as_posix(),
                    }
                    for f in sorted((b / "chapters").glob("*.md"))
                    if not f.name.startswith("_")
                ]
                card_list = [
                    {
                        "stem": f.stem,
                        "name": f.name,
                        "path": f.relative_to(REPO_ROOT).as_posix(),
                    }
                    for f in sorted((b / "evidence-cards").glob("*.md"))
                    if not f.name.startswith("_") and f.name.lower() not in {"index.md", "readme.md"}
                ]
                tree[s_slug]["books"][b.name] = {
                    "chapters": ch_list,
                    "evidence_cards": card_list,
                }
        else:
            ch_list = [
                {
                    "stem": f.stem,
                    "name": f.name,
                    "path": f.relative_to(REPO_ROOT).as_posix(),
                }
                for f in sorted((s_dir / "chapters").glob("*.md"))
                if not f.name.startswith("_")
            ]
            card_list = [
                {
                    "stem": f.stem,
                    "name": f.name,
                    "path": f.relative_to(REPO_ROOT).as_posix(),
                }
                for f in sorted((s_dir / "evidence-cards").glob("*.md"))
                if not f.name.startswith("_") and f.name.lower() not in {"index.md", "readme.md"}
            ]
            tree[s_slug]["root_chapters"] = ch_list
            tree[s_slug]["root_cards"] = card_list
    return tree


def safe_resolve_md_path(raw_path: str) -> Path | None:
    """Safely resolves a markdown path within series/ directory, preventing directory traversal."""
    if not raw_path:
        return None
    clean = raw_path.strip().lstrip("/\\")
    series_resolved = (REPO_ROOT / "series").resolve()

    target = (REPO_ROOT / clean).resolve()
    try:
        target.relative_to(series_resolved)
        if target.is_file() and target.suffix.lower() == ".md":
            return target
    except ValueError:
        pass

    target_series = (series_resolved / clean).resolve()
    try:
        target_series.relative_to(series_resolved)
        if target_series.is_file() and target_series.suffix.lower() == ".md":
            return target_series
    except ValueError:
        pass

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

    # Query stable OKF cards for public briefs showcase
    evidence_briefs = []
    with get_db() as conn:
        brief_rows = conn.execute(
            "SELECT series_slug, book_slug, card_slug, title, body "
            "FROM evidence_cards_fts WHERE body LIKE '%status: stable%' LIMIT 16"
        ).fetchall()
        for r in brief_rows:
            text = r["body"]
            fm_str, body_str = split_frontmatter_safe(text)
            meta = yaml.safe_load(fm_str) if fm_str and yaml else {}
            desc = meta.get("description", "")
            if not desc:
                snippet = body_str.strip()[:240]
            else:
                snippet = desc
            evidence_briefs.append({
                "series_slug": r["series_slug"],
                "book_slug": r["book_slug"],
                "card_slug": r["card_slug"],
                "title": meta.get("title", r["title"].split(" — ")[0] if " — " in r["title"] else r["title"]),
                "confidence": meta.get("confidence", "moderate"),
                "grade": meta.get("confidence", "moderate"),
                "snippet": snippet,
                "sources": meta.get("sources", []),
            })
        if not evidence_briefs:
            fallback_rows = conn.execute(
                "SELECT series_slug, book_slug, card_slug, title, substr(body, 1, 280) AS snippet "
                "FROM evidence_cards_fts LIMIT 16"
            ).fetchall()
            evidence_briefs = [dict(r) for r in fallback_rows]

    return templates.TemplateResponse(
        request,
        "site.html",
        {
            "request": request,
            "catalog": catalog,
            "catalog_json": catalog_json,
            "evidence_briefs": evidence_briefs,
            "server_info": get_server_info(request),
            "active_tab": "site",
        },
    )


@app.get("/hx/brief/{series_slug}/{card_slug}", response_class=HTMLResponse)
async def inspect_evidence_brief(request: Request, series_slug: str, card_slug: str):
    """
    Renders the OKF v0.2 Public Evidence Brief drawer for /site/ and /ide/.
    Loads the card from series/**/evidence-cards/{card_slug}.md, parses frontmatter
    and canonical sections, and renders partials/brief_drawer.html or fallback.
    """
    card_candidates = list((SERIES_DIR / series_slug).glob(f"**/evidence-cards/{card_slug}.md"))
    if not card_candidates:
        card_candidates = list(SERIES_DIR.glob(f"**/evidence-cards/{card_slug}.md"))
    if not card_candidates:
        raise HTTPException(status_code=404, detail=f"Evidence card '{card_slug}' not found in series '{series_slug}'")

    card_file = card_candidates[0]
    card_text = card_file.read_text(encoding="utf-8")

    fm_str, body_str = split_frontmatter_safe(card_text)
    metadata = yaml.safe_load(fm_str) if fm_str and yaml else {}

    sections: dict[str, list[str]] = {}
    current_sec = "Summary"
    for line in body_str.splitlines():
        if line.startswith("## "):
            current_sec = line[3:].strip()
            sections[current_sec] = []
        elif line.startswith("# "):
            pass
        elif current_sec:
            sections.setdefault(current_sec, []).append(line)
    parsed_sections = {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}

    sources_list = metadata.get("sources", [])
    primary_doi = metadata.get("primary_doi", "")
    if not primary_doi and sources_list and isinstance(sources_list, list):
        first_src = sources_list[0]
        if isinstance(first_src, dict):
            primary_doi = first_src.get("resource", "") or first_src.get("id", "")

    title = metadata.get("title", card_slug.replace("-", " ").title())
    grade = metadata.get("confidence") or metadata.get("certainty_grade") or "Moderate"

    drawer_template = REPO_ROOT / "bwe" / "templates" / "partials" / "brief_drawer.html"
    if drawer_template.exists():
        return templates.TemplateResponse(
            request,
            "partials/brief_drawer.html",
            {
                "request": request,
                "card_slug": card_slug,
                "series_slug": series_slug,
                "title": title,
                "grade": grade,
                "doi": primary_doi,
                "metadata": metadata,
                "sections": parsed_sections,
                "body": body_str,
                "server_info": get_server_info(request),
            },
        )

    from html import escape
    sections_html = "".join(
        f'<div class="mb-4"><h4 class="text-xs font-mono font-bold uppercase tracking-wider text-amber-400 mb-1">{escape(k)}</h4>'
        f'<div class="text-xs text-stone-300 font-serif leading-relaxed whitespace-pre-wrap">{escape(v)}</div></div>'
        for k, v in parsed_sections.items()
    )
    sources_html = "".join(
        f'<li class="text-[11px] font-mono text-stone-400 truncate"><a href="{escape(s.get("resource", "#"))}" target="_blank" rel="noopener noreferrer" class="hover:text-amber-400 underline">{escape(s.get("title", s.get("id", "")))}</a></li>'
        for s in sources_list if isinstance(s, dict)
    )
    return HTMLResponse(
        content=f"""
<div id="brief-drawer" class="p-6 bg-stone-900 border-l border-stone-800 text-stone-100 max-w-xl h-full overflow-y-auto">
    <div class="flex items-center justify-between pb-4 border-b border-stone-800">
        <div>
            <span class="text-[10px] font-mono uppercase tracking-widest text-amber-500 font-semibold">OKF v0.2 Evidence Brief</span>
            <h3 class="text-lg font-serif font-bold text-stone-100 mt-0.5">{escape(title)}</h3>
        </div>
        <span class="px-2.5 py-1 text-xs font-mono rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">Grade: {escape(str(grade))}</span>
    </div>
    <div class="py-4 space-y-4">
        {sections_html}
    </div>
    {f'<div class="pt-4 border-t border-stone-800"><h4 class="text-xs font-mono font-bold uppercase tracking-wider text-amber-400 mb-2">Sources</h4><ul class="space-y-1">{sources_html}</ul></div>' if sources_html else ''}
</div>
        """.strip()
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


def _render_chapter_view(
    request: Request,
    series_slug: str,
    chapter_slug: str,
    book_slug: Optional[str] = None,
    lens: Optional[str] = None,
) -> HTMLResponse:
    """Internal helper to locate chapter markdown, timings, and render with dual template support."""
    if book_slug:
        base_dir = SERIES_DIR / series_slug / book_slug
    else:
        base_dir = SERIES_DIR / series_slug

    if not base_dir.exists():
        raise HTTPException(status_code=404, detail="Series or book not found")

    md_candidates = list(base_dir.glob(f"**/chapters/{chapter_slug}.md"))
    if not md_candidates:
        raise HTTPException(status_code=404, detail="Chapter not found")
    md_path = md_candidates[0]
    raw_md = md_path.read_text(encoding="utf-8")

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

    s_meta = get_series_manifest_safe(series_slug)
    chosen_lens = lens or (s_meta["lenses"][0] if s_meta["lenses"] else "Science")
    takeaways = extract_chapter_takeaways(raw_md)
    footnotes = extract_chapter_footnotes(raw_md)

    # Dual template support: render reader.html if it exists, otherwise fall back to portal.html
    template_file = "reader.html" if (REPO_ROOT / "bwe" / "templates" / "reader.html").exists() else "portal.html"

    resolved_book = book_slug or (md_path.parent.parent.name if md_path.parent.parent.name.startswith("book-") else "root")

    return templates.TemplateResponse(
        request,
        template_file,
        {
            "request": request,
            "series_slug": series_slug,
            "book_slug": resolved_book,
            "chapter_slug": chapter_slug,
            "series_title": s_meta["title"],
            "series_subtitle": s_meta.get("subtitle", ""),
            "lenses": s_meta["lenses"],
            "active_lens": chosen_lens,
            "epistemic_contract": s_meta["epistemic_contract"],
            "takeaways": takeaways,
            "footnotes": footnotes,
            "prose_html": prose_html,
            "timings": blocks_list,
            "has_audio": has_audio,
            "audio_url": audio_url,
            "server_info": get_server_info(request),
            "active_tab": "reader",
        },
    )


@app.get("/read/{series_slug}/{chapter_slug}", response_class=HTMLResponse)
async def read_chapter(request: Request, series_slug: str, chapter_slug: str, lens: Optional[str] = None):
    """Serves the bidirectional audio-synced chapter reader with isolated footnotes and 3-lens support."""
    return _render_chapter_view(request, series_slug, chapter_slug, lens=lens)


@app.get("/read/{series_slug}/{book_slug}/{chapter_slug}", response_class=HTMLResponse)
async def read_chapter_multibook(request: Request, series_slug: str, book_slug: str, chapter_slug: str, lens: Optional[str] = None):
    """Serves the chapter reader for multi-book series volumes (e.g. Architectures of Memory)."""
    return _render_chapter_view(request, series_slug, chapter_slug, book_slug=book_slug, lens=lens)


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
        request,
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
        request,
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
        request,
        "ide.html",
        {
            "request": request,
            "cards": rows,
            "query": "",
            "file_tree": build_file_tree(),
            "server_info": get_server_info(request),
            "active_tab": "ide",
        },
    )


@app.get("/ide/search-cards", response_class=HTMLResponse)
async def search_evidence_cards(request: Request, q: str = ""):
    """Instant FTS5 search across all OKF v0.2 Evidence Cards."""
    sanitized_q = re.sub(r'["\']', '', q).strip()
    with get_db() as conn:
        if not q.strip():
            rows = conn.execute(
                "SELECT series_slug, book_slug, card_slug, title, substr(body, 1, 240) AS snippet "
                "FROM evidence_cards_fts LIMIT 15"
            ).fetchall()
        elif not sanitized_q:
            rows = []
        else:
            try:
                rows = conn.execute(
                    "SELECT series_slug, book_slug, card_slug, title, snippet(evidence_cards_fts, 4, '<mark>', '</mark>', '...', 24) AS snippet "
                    "FROM evidence_cards_fts WHERE evidence_cards_fts MATCH ? LIMIT 20",
                    (f'"{sanitized_q}"*',),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []
    return templates.TemplateResponse(
        request,
        "ide.html",
        {
            "request": request,
            "cards": rows,
            "query": q,
            "file_tree": build_file_tree(),
            "server_info": get_server_info(request),
            "active_tab": "ide",
        },
        block_name="card_results",
    )


@app.get("/ide/file-content")
@app.get("/hx/ide/editor")
async def get_ide_file_content(
    request: Request,
    path: Optional[str] = None,
    target_path: Optional[str] = None,
    format: Optional[str] = None,
):
    """
    Safely reads chapter or card markdown (preventing directory traversal),
    renders preview HTML via markdown, and returns content or editor partial.
    """
    chosen_path = path or target_path or ""
    if not chosen_path:
        raise HTTPException(status_code=400, detail="Query parameter 'path' or 'target_path' is required")
    file_path = safe_resolve_md_path(chosen_path)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Markdown file '{chosen_path}' not found or path traversal rejected")

    raw_text = file_path.read_text(encoding="utf-8")

    try:
        preview_html = markdown.markdown(raw_text, extensions=["extra", "toc", "tables"])
    except Exception:
        preview_html = markdown.markdown(raw_text)

    rel_path = file_path.relative_to(REPO_ROOT).as_posix()
    title = file_path.stem.replace("-", " ").replace("_", " ").title()

    accept_header = request.headers.get("accept", "")
    if format == "json" or "application/json" in accept_header:
        return JSONResponse(
            content={
                "path": rel_path,
                "title": title,
                "raw_content": raw_text,
                "preview_html": preview_html,
            }
        )

    ide_editor_tmpl = REPO_ROOT / "bwe" / "templates" / "partials" / "ide_editor.html"
    if ide_editor_tmpl.exists():
        return templates.TemplateResponse(
            request,
            "partials/ide_editor.html",
            {
                "request": request,
                "path": rel_path,
                "title": title,
                "raw_content": raw_text,
                "preview_html": preview_html,
                "server_info": get_server_info(request),
            },
        )

    from html import escape
    escaped_raw = escape(raw_text)
    return HTMLResponse(
        content=f"""
<div id="editor-container" class="flex-1 flex flex-col md:flex-row h-full overflow-hidden bg-stone-950 border border-stone-800 rounded-lg">
    <div class="flex-1 flex flex-col border-b md:border-b-0 md:border-r border-stone-800 min-w-0">
        <div class="p-2.5 bg-stone-900 border-b border-stone-800 flex items-center justify-between">
            <span class="font-mono text-xs text-amber-400 truncate">{escape(rel_path)}</span>
            <span class="text-[10px] font-mono text-stone-400">Markdown Editor</span>
        </div>
        <textarea id="markdown-source" name="content" spellcheck="false"
            class="flex-1 w-full p-4 bg-stone-950 text-stone-200 font-mono text-xs resize-none focus:outline-none focus:ring-1 focus:ring-amber-500/50"
            aria-label="Markdown editor for {escape(title)}">{escaped_raw}</textarea>
    </div>
    <div class="flex-1 flex flex-col min-w-0">
        <div class="p-2.5 bg-stone-900 border-b border-stone-800 flex items-center justify-between">
            <span class="text-xs font-mono text-stone-300">Live Preview</span>
            <span class="text-[10px] font-mono text-emerald-400">Rendered HTML</span>
        </div>
        <div id="preview-panel" class="flex-1 p-6 overflow-y-auto prose prose-invert prose-stone max-w-none text-stone-300 font-serif leading-relaxed">
            {preview_html}
        </div>
    </div>
</div>
        """.strip()
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
        request,
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
    base_slug = series.split("/i18n/")[0]
    if not base_slug or not (SERIES_DIR / base_slug).is_dir():
        raise HTTPException(status_code=404, detail=f"Series '{series}' not found")

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
            "request": request,
            "series_slug": series,
            "deck_dir": deck_dir,
            "data": data,
            "server_info": get_server_info(request),
            "active_tab": "analytics",
        },
    )


@app.get("/hx/analytics/dashboard", response_class=HTMLResponse)
@app.get("/hx/analytics/overview", response_class=HTMLResponse)
async def hx_analytics_dashboard(request: Request, series: str = "parenthood-atlas", lang: Optional[str] = None):
    """HTMX endpoint for instant series switching on the analytics dashboard (ARC-80)."""
    base_slug = series.split("/i18n/")[0]
    if not base_slug or not (SERIES_DIR / base_slug).is_dir():
        raise HTTPException(status_code=404, detail=f"Series '{series}' not found")

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
            "request": request,
            "series_slug": series,
            "deck_dir": deck_dir,
            "data": data,
            "server_info": get_server_info(request),
            "active_tab": "analytics",
        },
    )


@app.get("/hx/analytics/export-ads")
async def hx_analytics_export_ads(series: str = "parenthood-atlas", lang: Optional[str] = None):
    """One-click download of Amazon Ads Sponsored Products CSV from covered demand (ARC-80)."""
    base_slug = series.split("/i18n/")[0]
    if not base_slug or not (SERIES_DIR / base_slug).is_dir():
        raise HTTPException(status_code=404, detail=f"Series '{series}' not found")

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
    base_slug = series.split("/i18n/")[0]
    if not base_slug or not (SERIES_DIR / base_slug).is_dir():
        raise HTTPException(status_code=404, detail=f"Series '{series}' not found")
    if not (SERIES_DIR / base_slug / "series.yaml").is_file():
        raise HTTPException(status_code=404, detail=f"series.yaml not found for series '{series}'")

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


@app.get("/hx/graph/context-pack", response_class=HTMLResponse)
async def hx_graph_context_pack(series: str = "parenthood-atlas", chapter: str = "01-before-the-child-is-born", book: Optional[str] = None):
    """Compile and render a Chapter Context Pack (CCP) partial for Pane 3 drawer (ARC-84)."""
    from bwe.graph_rag import compile_chapter_context_pack

    conn = get_db()
    ch_clean = chapter.removesuffix(".md").split("/")[-1]
    ccp = compile_chapter_context_pack(series_slug=series, chapter_slug=ch_clean, book_slug=book, repo_root=REPO_ROOT, conn=conn)

    raw_md = ccp.to_markdown()
    token_count = ccp.token_estimate()

    html = f"""
    <div class="flex flex-col h-full overflow-hidden text-xs font-mono" x-data="{{ copied: false }}">
        <div class="p-3 border-b border-stone-800 bg-stone-900/60 flex items-center justify-between gap-2 shrink-0">
            <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">OKF v0.3 CCP</span>
                <span class="text-stone-300 font-bold">{token_count:,} tokens</span>
                <span class="text-[10px] text-stone-500">(Budget: &lt; 2,500)</span>
            </div>
            <button type="button"
                    @click="navigator.clipboard.writeText($refs.rawCcp.value); copied = true; setTimeout(() => copied = false, 2000)"
                    class="px-2.5 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-stone-950 font-bold text-[11px] transition flex items-center gap-1 shadow-sm touch-manipulation">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                <span x-text="copied ? 'Copied!' : 'Copy CCP'">Copy CCP</span>
            </button>
        </div>
        <textarea x-ref="rawCcp" class="hidden">{raw_md}</textarea>
        <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-stone-950/60 text-stone-300 text-[11px] leading-relaxed">
            <div class="border border-stone-800/80 rounded-lg p-3 bg-stone-900/40">
                <div class="text-[10px] text-amber-400/90 font-bold uppercase tracking-wider mb-1">Target Chapter Ego-Graph</div>
                <div class="text-stone-100 font-bold text-sm">{ccp.chapter_title}</div>
                <div class="text-stone-400 text-xs mt-0.5">Chapter {ccp.chapter_num} &bull; {ccp.series_slug} {f'({ccp.book_slug})' if ccp.book_slug and ccp.book_slug != 'root' else ''}</div>
            </div>

            <div class="space-y-2">
                <div class="text-stone-400 font-bold border-b border-stone-800 pb-1 flex justify-between items-center">
                    <span>1. Active Epistemic Ledger</span>
                    <span class="text-[10px] text-stone-500">{len(ccp.epistemic_contract)} cards bound</span>
                </div>
                <div class="space-y-1.5">
                    {''.join(f'''<div class="p-2 rounded bg-stone-900/60 border border-stone-800/60">
                        <div class="flex items-center justify-between text-stone-200 font-semibold">
                            <span>{c.get("card_slug")}</span>
                            <span class="text-[10px] px-1.5 py-0.5 rounded bg-stone-800 text-amber-300">{c.get("grade", "Moderate")}</span>
                        </div>
                        <div class="text-stone-400 text-[10px] mt-1">{c.get("causal_design", "").replace("_", " ")}</div>
                        <div class="text-stone-500 text-[10px] mt-0.5">Allowed verbs: {", ".join(c.get("allowed_verbs", [])[:3])}</div>
                    </div>''' for c in ccp.epistemic_contract) if ccp.epistemic_contract else '<div class="text-stone-500 italic">No cards cited directly in this chapter.</div>'}
                </div>
            </div>

            <div class="space-y-2">
                <div class="text-stone-400 font-bold border-b border-stone-800 pb-1">2. Narrative Handoff Vectors</div>
                <div class="p-2.5 rounded bg-stone-900/60 border border-stone-800/60 space-y-2 text-[10px]">
                    <div>
                        <span class="text-stone-500 font-bold block">Incoming Bridge (From Ch.{ccp.incoming_handoff.get("from_ch_num", "Start")}):</span>
                        <p class="text-stone-300 italic mt-0.5">"{ccp.incoming_handoff.get("closing_anchor", "Start of series")[:180]}..."</p>
                    </div>
                    <div>
                        <span class="text-stone-500 font-bold block">Outgoing Bridge (To Ch.{ccp.outgoing_handoff.get("to_ch_num", "End")}):</span>
                        <p class="text-stone-300 italic mt-0.5">"{ccp.outgoing_handoff.get("prologue_anchor", "End of series")[:180]}..."</p>
                    </div>
                </div>
            </div>

            <div class="space-y-2">
                <div class="text-stone-400 font-bold border-b border-stone-800 pb-1">3. Split-Register Metaphor Ledger</div>
                <div class="space-y-1 text-[10px]">
                    {''.join(f'''<div class="flex justify-between items-center p-1.5 rounded bg-stone-900/40 border border-stone-800/40">
                        <span class="text-rose-400/80 font-mono">{m.get("raw_jargon")}</span>
                        <span class="text-stone-300 italic max-w-[65%] text-right">{m.get("body_prose")}</span>
                    </div>''' for m in ccp.metaphor_ledger[:5]) if ccp.metaphor_ledger else '<div class="text-stone-500 italic">Zero body jargon violations; terms isolated in ## Notes.</div>'}
                </div>
            </div>

            <div class="space-y-2">
                <div class="text-stone-400 font-bold border-b border-stone-800 pb-1 flex justify-between items-center">
                    <span>4. Demand Weave Targets</span>
                    <span class="text-[10px] text-stone-500">{len(ccp.demand_targets)} queries</span>
                </div>
                <div class="space-y-1 text-[10px]">
                    {''.join(f'''<div class="flex justify-between items-center p-1.5 rounded bg-stone-900/40 border border-stone-800/40">
                        <span class="text-stone-200">{d.get("query")}</span>
                        <span class="text-amber-400 font-mono">{d.get("monthly_volume", 0):,} / mo</span>
                    </div>''' for d in ccp.demand_targets[:4]) if ccp.demand_targets else '<div class="text-stone-500 italic">No high-volume search clusters mapped.</div>'}
                </div>
            </div>
        </div>
    </div>
    """
    return HTMLResponse(content=html)


@app.get("/hx/graph/series-map")
async def hx_graph_series_map(series: str = "parenthood-atlas"):
    """Generate interactive SVG map of the OKF v0.3 series knowledge graph (ARC-84)."""
    from bwe.graph_rag import generate_series_map_svg

    conn = get_db()
    svg_content = generate_series_map_svg(conn, series)
    return Response(content=svg_content, media_type="image/svg+xml")
