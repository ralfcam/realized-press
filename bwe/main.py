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

from bwe.db import get_db, init_db, normalize_series_and_lang, resolve_edition_dir
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
from render_audiobook_player import DEFAULT_GITHUB_REPO, scan_all_imprint_books, UI_STRINGS

app = FastAPI(title="Realized Press — BWE & Serial Portal (P-ARC-18)")
templates = Jinja2Blocks(directory=str(REPO_ROOT / "bwe" / "templates"))

# Mount static client assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount documentation if present
if (REPO_ROOT / "docs").exists():
    app.mount("/docs-static", StaticFiles(directory=str(REPO_ROOT / "docs")), name="docs")

# Mount static site assets (cover thumbnails, etc.)
DOCS_ASSETS_DIR = REPO_ROOT / "docs" / "assets"
DOCS_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/site/assets", StaticFiles(directory=str(DOCS_ASSETS_DIR)), name="site_assets")
app.mount("/assets", StaticFiles(directory=str(DOCS_ASSETS_DIR)), name="assets")

# Mount static analytics charts (ARC-80)
DIST_ANALYTICS_DIR = REPO_ROOT / "dist" / "analytics"
DIST_ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/dist/analytics", StaticFiles(directory=str(DIST_ANALYTICS_DIR)), name="analytics_dist")

def resolve_series_edition_dir(series_slug: str, lang: Optional[str] = None) -> Path:
    """Canonical path resolver delegating to bwe.db.resolve_edition_dir."""
    return resolve_edition_dir(series_slug, lang=lang, repo_root=REPO_ROOT)


def get_available_languages(series_slug: str) -> list[str]:
    """Detect available languages for a series ('en', 'es', 'fr')."""
    clean_slug, _ = normalize_series_and_lang(series_slug, None)
    base_dir = SERIES_DIR / clean_slug
    langs = ["en"]
    i18n_dir = base_dir / "i18n"
    if i18n_dir.is_dir():
        for sub in sorted(i18n_dir.iterdir()):
            if sub.is_dir() and ((sub / "series.yaml").is_file() or (sub / "chapters").is_dir()):
                if sub.name not in langs:
                    langs.append(sub.name)
    return langs


# In-memory index of canonical media files partitioned by (lang, key)
AUDIO_CACHE: dict[tuple[str, str], Path] = {}
PDF_CACHE: dict[str, Path] = {}


def refresh_media_cache() -> None:
    """Index canonical audio and PDF files partitioned by (lang, stem)."""
    AUDIO_CACHE.clear()
    PDF_CACHE.clear()
    for ext in ("*.mp3", "*.wav"):
        for p in SERIES_DIR.glob(f"**/audiobook/{ext}"):
            if p.is_file():
                lang = "en"
                if "i18n/es" in p.as_posix() or "/es/" in p.as_posix():
                    lang = "es"
                elif "i18n/fr" in p.as_posix() or "/fr/" in p.as_posix():
                    lang = "fr"
                AUDIO_CACHE[(lang, p.stem)] = p
                AUDIO_CACHE[(lang, p.name)] = p
        for p in (REPO_ROOT / ".cache" / "tts_pcm").glob(ext):
            if p.is_file():
                AUDIO_CACHE.setdefault(("en", p.stem), p)
                AUDIO_CACHE.setdefault(("en", p.name), p)
    for p in SERIES_DIR.glob("**/*.pdf"):
        if p.is_file():
            PDF_CACHE[p.name] = p


def find_canonical_audio(filename: str, series_slug: Optional[str] = None, lang: str = "en") -> Path | None:
    """Locates canonical audio in series/**/audiobook/ without cross-language leakage."""
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower() or ".mp3"
    full_name = f"{stem}{ext}"

    if series_slug:
        edition_dir = resolve_series_edition_dir(series_slug, lang)
        for cand in (
            edition_dir / "audiobook" / full_name,
            edition_dir / "audiobook" / f"{stem}.mp3",
            edition_dir / "audiobook" / f"{stem}.wav",
        ):
            if cand.is_file():
                return cand
        # Never fall back to English if localized audio was requested
        if lang in ("es", "fr"):
            return None

    if (lang, full_name) in AUDIO_CACHE:
        return AUDIO_CACHE[(lang, full_name)]
    if (lang, stem) in AUDIO_CACHE:
        return AUDIO_CACHE[(lang, stem)]

    # Search strictly in the language scope
    if lang in ("es", "fr"):
        for candidate_ext in (".mp3", ".wav"):
            for p in SERIES_DIR.glob(f"**/i18n/{lang}/audiobook/{stem}{candidate_ext}"):
                if p.is_file():
                    AUDIO_CACHE[(lang, stem)] = p
                    AUDIO_CACHE[(lang, p.name)] = p
                    return p
        return None

    # English fallback search
    for candidate_ext in (".mp3", ".wav"):
        for p in SERIES_DIR.glob(f"**/audiobook/{stem}{candidate_ext}"):
            if "i18n" not in p.parts and p.is_file():
                AUDIO_CACHE[("en", stem)] = p
                AUDIO_CACHE[("en", p.name)] = p
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


def build_file_tree(lang: Optional[str] = None) -> dict:
    """Collects all series, books, chapters, and OKF evidence cards for the IDE file tree, including localized editions."""
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

        # Discover localized i18n sibling editions
        i18n_dir = s_dir / "i18n"
        if i18n_dir.is_dir():
            for loc in sorted(i18n_dir.iterdir()):
                if not loc.is_dir():
                    continue
                loc_chapters = [
                    {
                        "stem": f.stem,
                        "name": f.name,
                        "path": f.relative_to(REPO_ROOT).as_posix(),
                    }
                    for f in sorted((loc / "chapters").glob("*.md"))
                    if not f.name.startswith("_")
                ]
                loc_cards = [
                    {
                        "stem": f.stem,
                        "name": f.name,
                        "path": f.relative_to(REPO_ROOT).as_posix(),
                    }
                    for f in sorted((loc / "evidence-cards").glob("*.md"))
                    if not f.name.startswith("_") and f.name.lower() not in {"index.md", "readme.md"}
                ]
                tree[s_slug]["books"][f"i18n/{loc.name}"] = {
                    "chapters": loc_chapters,
                    "evidence_cards": loc_cards,
                }
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
async def imprint_site_home(request: Request, lang: str = "en"):
    """
    ARC-55: Serves the Imprint Audiobook Portal & Marketing Hub under the
    unified FastAPI + HTMX stack with aligned navigation and live catalog data.
    """
    catalog = scan_all_imprint_books(REPO_ROOT, DEFAULT_GITHUB_REPO)
    catalog_json = json.dumps(catalog, ensure_ascii=False)
    ui_strings_json = json.dumps(UI_STRINGS, ensure_ascii=False)

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
            "ui_strings_json": ui_strings_json,
            "lang": lang,
            "evidence_briefs": evidence_briefs,
            "server_info": get_server_info(request),
            "active_tab": "site",
        },
    )


@app.get("/hx/brief/{series_slug}/{card_slug}", response_class=HTMLResponse)
async def inspect_evidence_brief(request: Request, series_slug: str, card_slug: str):
    """
    Renders the OKF v0.3 Public Evidence Brief drawer for /site/ and /ide/.
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
            <span class="text-[10px] font-mono uppercase tracking-widest text-amber-500 font-semibold">OKF v0.3 Evidence Brief</span>
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
@app.get("/site/audio/{series_slug}/{lang}/{filename}")
@app.head("/site/audio/{series_slug}/{lang}/{filename}")
@app.get("/audio/{series_slug}/{lang}/{filename}")
@app.head("/audio/{series_slug}/{lang}/{filename}")
async def stream_audio_localized(series_slug: str, lang: str, filename: str):
    audio_path = find_canonical_audio(filename, series_slug=series_slug, lang=lang)
    if audio_path and audio_path.is_file():
        media_type = "audio/mpeg" if audio_path.suffix.lower() == ".mp3" else "audio/wav"
        return FileResponse(
            audio_path,
            media_type=media_type,
            headers={"Cache-Control": "public, max-age=3600", "Vary": "Accept-Language"},
        )
    raise HTTPException(
        status_code=404,
        detail=f"Audio asset '{filename}' not found for series '{series_slug}' and language '{lang}'",
    )


@app.get("/site/audio/{series_slug}/{filename}")
@app.head("/site/audio/{series_slug}/{filename}")
@app.get("/audio/{series_slug}/{filename}")
@app.head("/audio/{series_slug}/{filename}")
async def stream_audio_default_lang(series_slug: str, filename: str, lang: str = "en"):
    return await stream_audio_localized(series_slug, lang, filename)


@app.get("/timings/{series_slug}/{lang}/{chapter_slug}")
@app.get("/timings/{series_slug}/{chapter_slug}")
async def get_chapter_timings(series_slug: str, chapter_slug: str, lang: str = "en"):
    edition_dir = resolve_series_edition_dir(series_slug, lang)
    timings_path = edition_dir / "audiobook" / f"{chapter_slug}.timings.json"
    audio_mp3 = edition_dir / "audiobook" / f"{chapter_slug}.mp3"
    audio_wav = edition_dir / "audiobook" / f"{chapter_slug}.wav"

    md_path = edition_dir / "chapters" / f"{chapter_slug}.md"
    if not md_path.is_file():
        cands = list(edition_dir.glob(f"**/chapters/{chapter_slug}.md"))
        if cands:
            md_path = cands[0]

    from audio_sync_utils import (
        extract_semantic_blocks,
        pack_semantic_blocks,
        build_timings_manifest,
        verify_timings_match_markdown,
    )

    current_blocks = []
    if md_path.is_file():
        raw_md = md_path.read_text(encoding="utf-8")
        current_blocks = extract_semantic_blocks(raw_md, lang=lang)

    if (audio_mp3.is_file() or audio_wav.is_file()) and timings_path.is_file() and current_blocks:
        try:
            data = json.loads(timings_path.read_text(encoding="utf-8"))
            is_valid, _ = verify_timings_match_markdown(data, current_blocks)
            if is_valid and isinstance(data, dict):
                data["language"] = lang
                data["has_neural_audio"] = True
                return JSONResponse(data)
        except Exception:
            pass

    # Tier 2 dynamic localized scaffold fallback
    if md_path.is_file():
        chunks = pack_semantic_blocks(current_blocks, per_paragraph=True)
        scaffold = build_timings_manifest(chapter_slug, chunks, language=lang, has_neural_audio=False)
        return JSONResponse(scaffold)

    raise HTTPException(status_code=404, detail="Chapter or timings not found")


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
    lang: str = "en",
) -> HTMLResponse:
    """Internal helper to locate chapter markdown, timings, and render with localized support."""
    edition_dir = resolve_series_edition_dir(series_slug, lang)
    if book_slug and (edition_dir / book_slug).is_dir():
        base_dir = edition_dir / book_slug
    else:
        base_dir = edition_dir

    if not base_dir.exists():
        raise HTTPException(status_code=404, detail=f"Series edition '{series_slug}' ({lang}) not found")

    md_candidates = list(base_dir.glob(f"**/chapters/{chapter_slug}.md"))
    if not md_candidates:
        md_candidates = list(base_dir.glob(f"**/{chapter_slug}.md"))
    if not md_candidates:
        raise HTTPException(status_code=404, detail=f"Chapter '{chapter_slug}' not found for language '{lang}'")

    md_path = md_candidates[0]
    raw_md = md_path.read_text(encoding="utf-8")

    # Locate audio and timings strictly in edition directory
    timings_path = edition_dir / "audiobook" / f"{chapter_slug}.timings.json"
    audio_mp3 = edition_dir / "audiobook" / f"{chapter_slug}.mp3"
    audio_wav = edition_dir / "audiobook" / f"{chapter_slug}.wav"

    from audio_sync_utils import (
        extract_semantic_blocks,
        pack_semantic_blocks,
        build_timings_manifest,
        verify_timings_match_markdown,
    )
    from render_audiobook_player import extract_clean_text, UI_STRINGS

    current_blocks = extract_semantic_blocks(raw_md, lang=lang)
    has_audio = False
    is_stale_audio = False

    if (audio_mp3.is_file() or audio_wav.is_file()) and timings_path.is_file():
        try:
            t_data = json.loads(timings_path.read_text(encoding="utf-8"))
            is_valid, _ = verify_timings_match_markdown(t_data, current_blocks)
            if is_valid:
                has_audio = True
            else:
                is_stale_audio = True
        except Exception:
            is_stale_audio = True

    stale_archive = edition_dir / "audiobook" / "stale_pre_arc103" / f"{chapter_slug}.timings.json"
    if stale_archive.is_file() and not has_audio:
        is_stale_audio = True

    audio_url = (
        f"/audio/{series_slug}/{lang}/{chapter_slug}.mp3" if audio_mp3.is_file() and has_audio
        else (f"/audio/{series_slug}/{lang}/{chapter_slug}.wav" if audio_wav.is_file() and has_audio else "")
    )

    if has_audio:
        prose_html = extract_clean_text(md_path, timings_path=timings_path, lang=lang)
        blocks_list = []
        try:
            t_data = json.loads(timings_path.read_text(encoding="utf-8"))
            if isinstance(t_data, dict):
                blocks_list = t_data.get("blocks", [])
            elif isinstance(t_data, list):
                blocks_list = t_data
        except Exception:
            blocks_list = []
    else:
        # Tier 2 dynamic localized scaffold
        chunks = pack_semantic_blocks(current_blocks, per_paragraph=True)
        scaffold = build_timings_manifest(chapter_slug, chunks, language=lang, has_neural_audio=False)
        prose_html = extract_clean_text(md_path, scaffold_manifest=scaffold, lang=lang)
        blocks_list = scaffold.get("blocks", [])

    s_meta = get_series_manifest_safe(series_slug)
    # Check for localized title/subtitle if in i18n
    loc_yaml = edition_dir / "series.yaml"
    edition_title = s_meta["title"]
    edition_subtitle = s_meta.get("subtitle", "")
    if loc_yaml.is_file():
        try:
            loc_cfg = yaml.safe_load(loc_yaml.read_text(encoding="utf-8")) or {}
            edition_title = loc_cfg.get("title", edition_title)
            edition_subtitle = loc_cfg.get("subtitle", edition_subtitle)
        except Exception:
            pass

    available_languages = get_available_languages(series_slug)
    ui_strings = UI_STRINGS.get(lang, UI_STRINGS["en"])

    # Collect edition chapters for navigation
    chapters_dir = base_dir / "chapters"
    edition_chapters = []
    if chapters_dir.is_dir():
        from merge_book_chapters import iter_chapter_files
        from render_audiobook_player import extract_chapter_title
        for idx, f in enumerate(iter_chapter_files(chapters_dir), 1):
            edition_chapters.append({
                "num": idx,
                "stem": f.stem,
                "title": extract_chapter_title(f),
                "is_active": f.stem == chapter_slug,
            })

    chosen_lens = lens or (s_meta["lenses"][0] if s_meta["lenses"] else "Science")
    takeaways = extract_chapter_takeaways(raw_md)
    footnotes = extract_chapter_footnotes(raw_md)

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
            "series_title": edition_title,
            "series_subtitle": edition_subtitle,
            "lenses": s_meta["lenses"],
            "active_lens": chosen_lens,
            "epistemic_contract": s_meta["epistemic_contract"],
            "takeaways": takeaways,
            "footnotes": footnotes,
            "prose_html": prose_html,
            "timings": blocks_list,
            "has_audio": has_audio,
            "has_neural_audio": has_audio,
            "is_stale_audio": is_stale_audio,
            "audio_url": audio_url,
            "server_info": get_server_info(request),
            "active_tab": "reader",
            "lang": lang,
            "available_languages": available_languages,
            "ui_strings": ui_strings,
            "edition_chapters": edition_chapters,
        },
    )


@app.get("/reader/{series_slug}", response_class=HTMLResponse)
async def reader_landing(request: Request, series_slug: str, lang: str = "en", chapter: Optional[str] = None):
    """Landing route for synchronized reader, defaulting to chapter 1 or requested chapter."""
    edition_dir = resolve_series_edition_dir(series_slug, lang)
    if chapter:
        target_ch = chapter
    else:
        chapters_dir = edition_dir / "chapters"
        from merge_book_chapters import iter_chapter_files
        files = iter_chapter_files(chapters_dir) if chapters_dir.is_dir() else []
        target_ch = files[0].stem if files else "01-before-the-child-is-born"
    return _render_chapter_view(request, series_slug, target_ch, lang=lang)


@app.get("/read/{series_slug}/{chapter_slug}", response_class=HTMLResponse)
async def read_chapter(request: Request, series_slug: str, chapter_slug: str, lens: Optional[str] = None, lang: str = "en"):
    """Serves the bidirectional audio-synced chapter reader with isolated footnotes and 3-lens support."""
    return _render_chapter_view(request, series_slug, chapter_slug, lens=lens, lang=lang)


@app.get("/read/{series_slug}/{book_slug}/{chapter_slug}", response_class=HTMLResponse)
async def read_chapter_multibook(request: Request, series_slug: str, book_slug: str, chapter_slug: str, lens: Optional[str] = None, lang: str = "en"):
    """Serves the chapter reader for multi-book series volumes (e.g. Architectures of Memory)."""
    return _render_chapter_view(request, series_slug, chapter_slug, book_slug=book_slug, lens=lens, lang=lang)


@app.get("/hx/reader/{series_slug}/{chapter_slug}", response_class=HTMLResponse)
async def hx_read_chapter(request: Request, series_slug: str, chapter_slug: str, lens: Optional[str] = None, lang: str = "en"):
    """HTMX partial endpoint for swapping chapter manuscript and audio in reader view."""
    return _render_chapter_view(request, series_slug, chapter_slug, lens=lens, lang=lang)


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
async def epistemic_ide_home(request: Request, lang: str = "en"):
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
            "file_tree": build_file_tree(lang=lang),
            "lang": lang,
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

    # ARC-101: Annotate preview paragraphs with #p-block-XX IDs for IDE gutter jumping & diagnostics
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(preview_html, "html.parser")
        p_idx = 0
        for p_tag in soup.find_all("p"):
            if p_tag.parent and p_tag.parent.get("class") == ["footnote"]:
                continue
            if p_tag.find_parent(["aside", "blockquote"]):
                continue
            p_idx += 1
            p_tag["id"] = f"p-block-{p_idx}"
            classes = p_tag.get("class") or []
            if "transition-colors" not in classes:
                p_tag["class"] = classes + ["transition-colors", "duration-500"]
        preview_html = str(soup)
    except Exception:
        pass

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
        "five_rule_check": [sys.executable, str(SCRIPTS_DIR / "five_rule_check.py"), target_path],
        "audit_manuscript": [sys.executable, str(SCRIPTS_DIR / "audit_manuscript.py"), target_path],
        "audit_manuscript_bestseller": [sys.executable, str(SCRIPTS_DIR / "audit_manuscript.py"), target_path, "--bestseller-strict", "--graph-strict"],
        "audit_epub": [sys.executable, str(SCRIPTS_DIR / "audit_epub.py"), target_path],
    }
    if script_name not in allowed_scripts:
        raise HTTPException(status_code=400, detail="Unsupported audit script")

    proc = subprocess.run(
        allowed_scripts[script_name],
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


@app.get("/hx/micro-qa/{series_slug}/{chapter_slug}", response_class=HTMLResponse)
async def get_chapter_micro_qa(
    request: Request,
    series_slug: str,
    chapter_slug: str,
    book_slug: Optional[str] = None,
    lang: Optional[str] = None,
):
    """
    ARC-101: Returns granular paragraph-by-paragraph diagnostics (Rules 8a–8d)
    for editor gutter display and micro-QA inspection.
    """
    from audit_manuscript import (
        audit_micro_qa,
        compute_phrasal_poetics,
        split_sections,
        tokenize_sentences,
        compute_readability_metrics,
        INLINE_FN_RE,
    )
    from bwe.style_sculptor import build_sculptor_prompt

    target_lang = lang or ("fr" if ("fr" in series_slug) else ("es" if ("es" in series_slug) else "en"))
    edition_dir = resolve_series_edition_dir(series_slug, target_lang)

    if book_slug and (edition_dir / book_slug).is_dir():
        base_dir = edition_dir / book_slug
    else:
        base_dir = edition_dir

    if not base_dir.exists():
        raise HTTPException(status_code=404, detail="Series or book directory not found")

    md_candidates = list(base_dir.glob(f"**/chapters/{chapter_slug}.md"))
    if not md_candidates:
        md_candidates = list(base_dir.glob(f"**/{chapter_slug}.md"))
    if not md_candidates:
        raise HTTPException(status_code=404, detail=f"Chapter {chapter_slug} not found")

    md_path = md_candidates[0]
    raw_md = md_path.read_text(encoding="utf-8")
    body_before_notes = raw_md.split("## Notes")[0] if "## Notes" in raw_md else raw_md

    hard_errs, warns, metrics = audit_micro_qa(
        body_before_notes,
        language=target_lang,
        chapter_slug=chapter_slug,
    )
    poetics = compute_phrasal_poetics(
        body_before_notes,
        language=target_lang,
        chapter_slug=chapter_slug,
        root=REPO_ROOT,
        book_path=base_dir,
    )
    poetics_by_idx = {p["index"]: p for p in poetics.get("paragraphs", [])}

    clean_body = re.sub(r"<aside[\s\S]*?</aside>", "", body_before_notes, flags=re.IGNORECASE)
    sections = split_sections(clean_body)
    paragraphs = []
    p_global = 0

    for sec_title, sec_body in sections:
        if sec_title.lower().startswith(("notes", "sources", "further reading", "linked evidence cards")):
            continue
        raw_paras = [pr.strip() for pr in sec_body.split("\n\n") if pr.strip()]
        for pr in raw_paras:
            if pr.startswith(("#", ">", "|", "```", "---", "<aside", "<div", "<!--", "$$")):
                continue
            lines = [ln.strip() for ln in pr.splitlines() if ln.strip()]
            if all(ln.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")) for ln in lines):
                continue
            p_global += 1
            clean_p = INLINE_FN_RE.sub("", pr)
            clean_p = re.sub(r"<[^>]+>", " ", clean_p)
            sents = tokenize_sentences(pr, language=target_lang)
            if target_lang == "es":
                w_regex = r"[A-Za-z0-9áéíóúüñÁÉÍÓÚÜÑ']+"
            elif target_lang == "fr":
                w_regex = r"[A-Za-z0-9àâäéèêëîïôöùûüÿçœæÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇŒÆ']+"
            else:
                w_regex = r"[A-Za-z0-9']+"
            words = re.findall(w_regex, clean_p)
            rm = compute_readability_metrics(clean_p, language=target_lang) if (len(sents) >= 3 or len(words) >= 40) else {}
            if target_lang == "fr":
                readability_val = float(rm.get("kandel", 55.0))
            elif target_lang == "es":
                readability_val = float(rm.get("szigriszt", 55.0))
            else:
                readability_val = float(rm.get("fk_grade", 8.5))

            prefix = f"[p.{p_global}"
            p_errs = [e for e in hard_errs if prefix in e]
            p_warns = [w for w in warns if prefix in w] + [w for w in poetics.get("warnings", []) if prefix in w]
            p_poetics = poetics_by_idx.get(p_global, {})
            sculpt_prompt = build_sculptor_prompt(
                pr,
                section_title=sec_title,
                language=target_lang,
                reasons=p_poetics.get("reasons", []),
            )

            paragraphs.append({
                "idx": p_global,
                "section": sec_title,
                "words": len(words),
                "sents": len(sents),
                "readability": readability_val,
                "poetics_score": p_poetics.get("poetics_score", 100.0),
                "copula_ratio": p_poetics.get("copula_ratio", 0.0),
                "cadence_sigma": p_poetics.get("cadence_sigma", 3.5),
                "sculpt_prompt": sculpt_prompt,
                "excerpt": clean_p[:120].strip() + ("..." if len(clean_p) > 120 else ""),
                "hard_errors": p_errs,
                "warnings": p_warns,
            })

    return templates.TemplateResponse(
        request,
        "partials/micro_qa_gutter.html",
        {
            "request": request,
            "series_slug": series_slug,
            "chapter_slug": chapter_slug,
            "language": target_lang,
            "hard_errors": hard_errs,
            "warnings": warns,
            "metrics": metrics,
            "poetics": poetics,
            "paragraphs": paragraphs,
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


@app.get("/hx/graph/lineage", response_class=HTMLResponse)
async def hx_graph_lineage(
    series: str = "architectures-of-memory",
    src: str = "rosenblatt-1958-perceptron-convergence-theorem",
    dst: str = "vaswani-2017-attention-is-all-you-need",
    max_hops: int = 8,
):
    """Trace shortest causal/epistemic path between two cards in < 2 ms (ARC-90)."""
    from bwe.graph_rag import find_epistemic_lineage
    conn = get_db()
    steps = find_epistemic_lineage(conn, series, src, dst, max_hops=max_hops)

    if not steps:
        return HTMLResponse(
            '<div class="p-4 rounded-xl bg-stone-900/80 border border-stone-800 text-stone-400 font-mono text-xs text-center">'
            f'No connecting epistemic path found between <code class="text-amber-400">{src}</code> and <code class="text-amber-400">{dst}</code> within {max_hops} hops.'
            '</div>'
        )

    items_html = []
    for s in steps:
        rel_color = {
            "EXTENDS": "bg-sky-500/20 text-sky-300 border-sky-500/30",
            "BOUNDS": "bg-amber-500/20 text-amber-300 border-amber-500/30",
            "CONTRASTS": "bg-purple-500/20 text-purple-300 border-purple-500/30",
            "MITIGATES": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
            "BRIDGES_LENS": "bg-pink-500/20 text-pink-300 border-pink-500/30",
            "CONTRADICTS_OR_BOUNDS": "bg-rose-500/20 text-rose-300 border-rose-500/30",
        }.get(s["relationship"], "bg-stone-800 text-stone-300 border-stone-700")

        dir_icon = "→" if s.get("direction") == "forward" else "←"

        items_html.append(f"""
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-stone-950/70 border border-stone-800/80 hover:border-amber-500/40 transition">
            <div class="flex items-center gap-2.5">
                <span class="w-6 h-6 rounded-full bg-stone-800 flex items-center justify-center font-mono text-[10px] text-amber-400 font-bold shrink-0">{s['hop']}</span>
                <div>
                    <span class="font-mono text-xs font-semibold text-stone-200 block">{s['source_slug']}</span>
                    <span class="text-[10px] text-stone-400 font-sans">{s['source_title']}</span>
                </div>
            </div>
            <div class="flex items-center gap-2 shrink-0 self-center">
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold border {rel_color} flex items-center gap-1">
                    <span>{s['relationship']}</span>
                    <span>{dir_icon}</span>
                </span>
            </div>
            <div class="flex items-center gap-2.5 text-right sm:text-left justify-end">
                <div>
                    <span class="font-mono text-xs font-semibold text-stone-200 block">{s['target_slug']}</span>
                    <span class="text-[10px] text-stone-400 font-sans">{s['target_title']}</span>
                </div>
            </div>
        </div>
        """)

    html = f"""
    <div class="p-4 rounded-xl bg-stone-900/90 border border-stone-800 space-y-3 font-mono text-xs">
        <div class="flex items-center justify-between border-b border-stone-800 pb-2">
            <span class="text-stone-300 font-bold">Lineage Trace: <span class="text-amber-400">{src}</span> → <span class="text-amber-400">{dst}</span></span>
            <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">{len(steps)} hops</span>
        </div>
        <div class="space-y-2">
            {''.join(items_html)}
        </div>
    </div>
    """
    return HTMLResponse(content=html)
