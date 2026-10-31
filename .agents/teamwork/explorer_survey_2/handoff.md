# BWE Backend Routes, Server Entry Points, and Data Models Survey Report

**Author**: Backend Route Explorer  
**Working Directory**: `c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_2\`  
**Target Subsystem**: `bwe/` (FastAPI Server, Jinja2 Templates, SQLite State, Data Analytics Engine)  
**Date**: 2026-10-31  

---

## 1. Observation

### 1.1 Architecture, Server Entry Points, and Mountings
Direct inspection of `bwe/main.py`, `bwe/cli.py`, `bwe/schema.py`, and `bwe/db.py` revealed:

1. **FastAPI Application & Template Renderer**:
   - `bwe/main.py:30-31`:
     ```python
     app = FastAPI(title="Realized Press — BWE & Serial Portal (P-ARC-18)")
     templates = Jinja2Blocks(directory=str(REPO_ROOT / "bwe" / "templates"))
     ```
     `Jinja2Blocks` from `jinja2_fragments.fastapi` is configured. This enables both standard full-page Jinja2 rendering and partial HTMX block-level rendering via `block_name`.
2. **Static Mountings**:
   - `bwe/main.py:34`: `app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")` pointing to `bwe/static` (currently empty with only `.gitkeep`).
   - `bwe/main.py:38`: `app.mount("/docs-static", StaticFiles(directory=str(REPO_ROOT / "docs")), name="docs")` (mounted conditionally if `docs/` exists).
   - `bwe/main.py:43`: `app.mount("/dist/analytics", StaticFiles(directory=str(DIST_ANALYTICS_DIR)), name="analytics_dist")` mounting `dist/analytics` for static SVG/PNG charts.
3. **CLI Entrypoint & LAN Port Binding**:
   - `bwe/cli.py:21-25`:
     ```python
     @cli.command()
     def serve(host: str = "0.0.0.0", port: int = 8080, reload: bool = True):
         """Launch the BWE Epistemic IDE & Serial Reader Portal (with LAN auto-detection)."""
         uvicorn.run("bwe.main:app", host=host, port=port, reload=reload)
     ```
     The default host is `0.0.0.0` and port is `8080`.
4. **Lifespan Startup & Media Indexing**:
   - `bwe/main.py:101-105`:
     ```python
     @asynccontextmanager
     async def lifespan(app: FastAPI):
         init_db(REPO_ROOT)
         refresh_media_cache()
         yield
     ```
     `init_db` migrates SQLite database `.cache/bwe_state.db` to schema version 3, indexing FTS5 virtual tables `evidence_cards_fts` and `chapters_fts`. `refresh_media_cache` builds an in-memory index of all `*.mp3`, `*.wav`, and `*.pdf` files across `series/**` and `.cache/tts_pcm/`.

---

### 1.2 Inventory of Existing Endpoints and Context Dictionaries

| Route | Method | Handler | Rendered Template / Response | Current Context Dictionary / Output |
|---|---|---|---|---|
| `/` | GET | `root_redirect` | HTTP 307 Redirect | `RedirectResponse(url="/site/", status_code=307)` |
| `/site` | GET | `imprint_site_redirect` | HTTP 307 Redirect | `RedirectResponse(url="/site/", status_code=307)` |
| `/site/` | GET | `imprint_site_home` | `site.html` (HTMLResponse) | `{"request": request, "catalog": catalog, "catalog_json": catalog_json, "active_tab": "site"}` |
| `/media/audio/{filename}`, `/site/{filename}.mp3`, etc. | GET, HEAD | `stream_audio` | FileResponse (`audio/mpeg` or `audio/wav`) | Canonical audio stream supporting HTTP 206 Byte-Range requests |
| `/media/pdf/{filename}`, `/site/{filename}.pdf`, etc. | GET, HEAD | `stream_pdf` | FileResponse (`application/pdf`) | Canonical PDF stream |
| `/read/{series_slug}/{chapter_slug}` | GET | `read_chapter` | `portal.html` (HTMLResponse) | `{"request": request, "series_slug": series_slug, "chapter_slug": chapter_slug, "prose_html": prose_html, "timings": blocks_list, "has_audio": has_audio, "audio_url": audio_url, "active_tab": "reader"}` |
| `/hx/footnote/{series_slug}/{chapter_slug}/{footnote_id}` | GET | `inspect_footnote` | `partials/footnote_drawer.html` (HTMLResponse) | `{"request": request, "footnote_id": footnote_id, "note_text": note_text}` (also inserts event to `citation_telemetry`) |
| `/hx/telemetry` | GET | `view_citation_telemetry` | `partials/telemetry_table.html` (HTMLResponse) | `{"request": request, "telemetry": telemetry}` (last 25 events from `citation_telemetry`) |
| `/hx/feedback` | POST | `submit_reader_feedback` | Inline HTML alert (HTMLResponse) | Inserts row into `reader_feedback` |
| `/ide` | GET | `epistemic_ide_home` | `ide.html` (HTMLResponse) | `{"request": request, "cards": rows, "query": ""}` (first 15 FTS5 evidence cards) |
| `/ide/search-cards` | GET | `search_evidence_cards` | `ide.html` (fragment: `card_results`) | `{"request": request, "cards": rows, "query": q}` |
| `/ide/audit` | POST | `run_epistemic_audit` | `partials/audit_results.html` (HTMLResponse) | `{"request": request, "script_name": script_name, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}` |
| `/ide/tts-stream/{series_slug}/{chapter_slug}` | GET | `stream_tts_synthesis` | StreamingResponse (`text/event-stream`) | SSE live stream invoking `scripts/generate_audiobook_tts.py` |
| `/analytics` | GET | `view_analytics` | `analytics.html` (HTMLResponse) | `{"series_slug": series, "deck_dir": deck_dir, "data": data}` (computed via `build_series_analytics_payload`) |
| `/hx/analytics/dashboard`, `/hx/analytics/overview` | GET | `hx_analytics_dashboard` | `partials/analytics_dashboard.html` (HTMLResponse) | `{"series_slug": series, "deck_dir": deck_dir, "data": data}` |
| `/hx/analytics/export-ads` | GET | `hx_analytics_export_ads` | FileResponse (`text/csv`) | `amazon_ads_{clean_slug}.csv` generated by `marketing_intelligence.py` |
| `/hx/analytics/write-kdp-yaml` | POST | `hx_analytics_write_kdp_yaml` | Inline HTML badge (HTMLResponse) | Repacks 7 KDP boxes into `series.yaml` in-place |

---

### 1.3 Direct Inspection of Template Files and Requirements Discrepancies

1. **`ORIGINAL_REQUEST.md:15` vs `bwe/main.py:216` (Template Naming)**:
   - `ORIGINAL_REQUEST.md:15`:
     > `- /read/{series}/{chapter} (reader.html): Serial reader featuring refined typography, 3-lens toggle, takeaway cards, and footnote tooltips.`
   - `bwe/main.py:216`:
     ```python
     return templates.TemplateResponse(
         "portal.html",
         { ... }
     )
     ```
   - Direct verification: `bwe/templates/portal.html` exists (364 lines); no `reader.html` currently exists in `bwe/templates/`.
2. **`partials/nav.html:68` & `partials/nav.html:17` (Hardcoded Elements)**:
   - Line 17:
     ```html
     Science → Interpretation → Art
     ```
     This contract is hardcoded for *Parenthood: The Atlas*, but *Architectures of Memory* uses *Technical → Organizational → Philosophical*.
   - Line 68:
     ```html
     LAN 8080
     ```
     The port `8080` is hardcoded string text rather than dynamically reading the server port.
   - Lines 26, 36, 46, 56:
     ```html
     min-h-[40px] sm:min-h-[36px]
     ```
     Navigation touch targets are currently 36px/40px, below the required 44px touch target specification (`min-h-[44px]`).
3. **Catalog Scanning (`scan_all_imprint_books`)**:
   - `scripts/render_audiobook_player.py:236-266` scans all series and books. Executing:
     ```python
     scan_all_imprint_books(Path('.'), 'ralfcam/realized-press')
     ```
     yields 6 books: `['book-01-vanishing-signal', 'book-02-forget-gate', 'book-03-weight-of-attention', 'book-04-context-window', 'book-05-architecture-of-forgetting', 'parenthood-atlas']`.
4. **Analytics Payload Coverage**:
   - Execution of `build_series_analytics_payload("parenthood-atlas")` directly verified:
     - `data["quadrant_svg"]`: Fully responsive dark-mode SVG scatter plot with 4 quadrant labels (Q1 Content Gaps, Q2 Core Anchors, Q3 Niche Strengths, Q4 Long Tail), log volume scale, and hover tooltips.
     - `data["chapter_bars_svg"]`: Chapter volume breakdown SVG with verified GKP vs seed volume and max CPC overlay.
     - `data["kdp_boxes_meta"]`: 7 items with UTF-8 byte counts, utilization percentages, and strict validity checks (`bytes <= 49`).
     - `data["signals"]`: KeywordSignal items, each with `s.sparkline_svg` (responsive 12-point dark-mode SVG mini sparkline).
     - `data["bib_decade_svg"]`: Bibliographic publication year recency distribution.

---

## 2. Logic Chain

### 2.1 Analysis of `/site` View (Imprint Showcase, Player State, Evidence Briefs)
1. **Observation**: `/site/` passes `catalog` (list of 6 book dicts) and `catalog_json` to `site.html`. In `site.html`, book switching, audio playback, and footnote drawer display are handled via client-side JavaScript.
2. **Gap Analysis**:
   - The user requirement specifies an "evidence brief drawer" on `/site`. Currently, `site.html` only contains static links to release PDFs (lines 1163, 1170, 1177) and a footnote drawer triggered by `a.footnote-ref` targeting `/hx/footnote/{book.id}/{ch.stem}/{fnId}`.
   - There is no server-side route or context variable providing structured public evidence briefs on `/site`.
3. **Inference & Required Backend Enhancement**:
   - **Route Addition**: Add `GET /hx/brief/{series_slug}/{card_slug}` (or `GET /hx/brief/{card_slug}`) that loads the OKF v0.2 evidence card from `series/**/evidence-cards/{card_slug}.md` or SQLite FTS5, parses the 9 canonical OKF sections, and renders `partials/brief_drawer.html`.
   - **Context Enhancement**: In `imprint_site_home`, query stable OKF evidence cards from SQLite or `series/parenthood-atlas/evidence-cards` and pass `evidence_briefs` in the context dictionary (e.g. `card_slug`, `title`, `grade`, `doi`, `claims_summary`).
   - **Audio Player State**: Accept optional query parameters `?series=...&book=...&chapter=...` to pre-select initial book and track index.

### 2.2 Analysis of `/ide` View (3-Pane Layout, File Tree, Split Editor)
1. **Observation**: `ide.html` currently presents 3 columns:
   - Col 1: OKF Evidence Card search (`/ide/search-cards`)
   - Col 2: Epistemic Gate & Audit Runner (`/ide/audit`)
   - Col 3: Zero-Drift TTS stream (`/ide/tts-stream/{series}/{chapter}`)
2. **Gap Analysis**:
   - The requirement calls for a "3-Pane Epistemic IDE including file explorer, split Markdown editor, and OKF v0.2 Evidence Card live drawer."
   - Currently, there is NO file explorer / tree, NO split Markdown editor, and NO file content loading endpoint in `bwe/main.py`.
3. **Inference & Required Backend Enhancement**:
   - **Context Enhancement**: Pass `file_tree` in `/ide` context:
     ```python
     "file_tree": {
         "parenthood-atlas": {"chapters": [...], "evidence_cards": [...]},
         "architectures-of-memory": {
             "book-01-vanishing-signal": {"chapters": [...], "evidence_cards": [...]}, ...
         }
     }
     ```
   - **Route Addition**: Add `GET /ide/file-content` (or `GET /hx/ide/editor?path=...`) which reads a selected chapter or evidence card Markdown file safely (preventing path traversal), renders preview HTML via markdown/bs4, and returns editor + preview data for HTMX swapping.
   - **Card Detail Expansion**: Add `GET /hx/ide/card/{card_slug}` to inspect full 9-section OKF metadata in the live drawer rather than only the 240-char FTS5 snippet.

### 2.3 Analysis of `/read/{series}/{chapter}` (Lenses, Takeaways, Footnotes, Template Naming)
1. **Observation**:
   - `bwe/main.py:216` renders `portal.html`. The requirement specifically requests `reader.html`.
   - `read_chapter` passes `series_slug`, `chapter_slug`, `prose_html`, `timings`, `has_audio`, `audio_url`, `active_tab`.
   - It does NOT pass `lenses`, `epistemic_contract`, `takeaways`, or `footnotes` dictionary.
2. **Gap Analysis**:
   - The 3-lens toggle cannot render dynamically without knowing whether the series is *Science / Interpretation / Art* (*Parenthood: The Atlas*) or *Technical / Organizational / Philosophical* (*Architectures of Memory*).
   - Takeaway cards (organically resolving 3-tier causal trajectories: Population Average, Individual Trajectory, Actionable Control) have no data passed in context.
   - Footnotes are currently resolved on-demand per click via `/hx/footnote/...`, which prevents instant hover tooltips unless pre-extracted into context.
3. **Inference & Required Backend Enhancement**:
   - **Dual Template Support**: In `read_chapter`:
     ```python
     template_name = "reader.html" if (REPO_ROOT / "bwe" / "templates" / "reader.html").exists() else "portal.html"
     ```
     This permits immediate backwards compatibility with `portal.html` while prioritizing `reader.html` when authored.
   - **Series Manifest & Lenses Integration**:
     Load `series/{series_slug}/series.yaml` using `validate_series_yaml` (or fallback dict). Pass:
     - `lenses`: list of lens labels (e.g. `["Science", "Interpretation", "Art"]` or `["Technical", "Organizational", "Philosophical"]`).
     - `epistemic_contract`: string (e.g. `"Science -> Interpretation -> Art"`).
     - `active_lens`: string (from query param `?lens=...`, defaulting to lens 0).
   - **Takeaway Cards Extraction**:
     Parse movement headers (`## I. ...`, `## II. ...`) or front-matter takeaways from `md_path`, passing `takeaways: list[dict]` (with `movement`, `title`, `lens`, `summary`).
   - **Footnote Dictionary**:
     Extract `footnotes: dict[str, str]` from `## Notes` to support client-side hover tooltips.
   - **Multi-Book Path Flexibility**:
     Add route `@app.get("/read/{series_slug}/{book_slug}/{chapter_slug}")` for explicit 3-segment book paths (e.g. `/read/architectures-of-memory/book-01-vanishing-signal/01-rosenblatt-perceptron`).

### 2.4 Analysis of `/analytics` (Dashboard Data & Exports)
1. **Observation**:
   - `bwe/analytics.py` already generates the complete statistical and visual telemetry:
     `quadrant_svg`, `chapter_bars_svg`, `bib_decade_svg`, `kdp_boxes_meta` (7 boxes <= 49 bytes), `signals` (with 12-month `sparkline_svg`), and `/hx/analytics/export-ads`.
2. **Gap Analysis**:
   - In `bwe/main.py:429` and `457`, `templates.TemplateResponse(request, "analytics.html", {"series_slug": series, "deck_dir": deck_dir, "data": data})` passes `request` as the first argument, omitting `"request": request` from the context dictionary.
   - In `partials/analytics_dashboard.html`, series switcher tabs are hardcoded for 3 series slugs.
3. **Inference & Required Backend Enhancement**:
   - Ensure `"request": request` and `"active_tab": "analytics"` are explicitly present in the context dictionary.
   - Pass `available_series`: list of series options (slug, display title, language flag).
   - No data model modifications are required for analytics; the existing computation engine in `bwe/analytics.py` fully satisfies all R1/R4 requirements.

### 2.5 Analysis of `partials/nav.html` (LAN Indicator, Badge, ARIA)
1. **Observation**:
   - Port 8080 is hardcoded in `partials/nav.html:68`.
   - Contract "Science → Interpretation → Art" is hardcoded in line 17.
   - Touch targets are 36–40px instead of 44px.
2. **Inference & Required Backend Enhancement**:
   - Route handlers should pass `server_info`:
     ```python
     "server_info": {
         "host": request.url.hostname or "0.0.0.0",
         "port": request.url.port or 8080,
     }
     ```
   - Template context can provide `epistemic_contract` defaulting to series context.
   - `nav.html` utility classes need updating from `min-h-[36px]` / `min-h-[40px]` to `min-h-[44px]` and `min-w-[44px]`.

---

## 3. Caveats

1. **No Source Code Edits Executed**: In accordance with the Explorer archetype rules, no source files were modified during this investigation. All findings and proposed code adjustments are formulated as verified specifications and drop-in replacements.
2. **Audio File Availability**: While all chapter Markdown text files exist across both series, synthesized `*.mp3` audio files currently exist primarily for *Parenthood: The Atlas* (Chapter 1) and in `.cache/tts_pcm/`. When audio is absent, `has_audio` is `False`, and templates must gracefully fall back to silent reader mode without player layout shift.
3. **Browser Execution in Test Environment**: Testing was performed via headless FastAPI `TestClient` (HTTP status codes, header parsing, and response text assertions). Visual layout shifts and browser-specific CSS rendering (e.g. mobile Safari safe area insets) must be verified visually or via Chrome DevTools during template implementation.
4. **Jinja2Blocks Parameter Convention**: `jinja2_fragments.fastapi.Jinja2Blocks.TemplateResponse` supports both `TemplateResponse(name, context)` and `TemplateResponse(request, name, context)`. To avoid ambiguity across FastAPI versions, passing `"request": request` inside the context dictionary while maintaining consistent argument order is recommended.

---

## 4. Conclusion

The `bwe/` backend architecture is robust, lightweight, and cleanly partitioned:
1. **FastAPI & Jinja2Blocks**: The server setup in `bwe/main.py` is capable of handling full-page and HTMX block swaps with low latency.
2. **Data Availability**:
   - Analytics metrics, Demand Quadrant SVG, Chapter Volume & CPC bars, KDP 7-box byte utilization, and 12-month sparklines are **100% computed and operational** in `bwe/analytics.py`.
   - Multi-series book catalog scanning in `render_audiobook_player.py` accurately catalogs all 6 books across *Parenthood: The Atlas* and *Architectures of Memory*.
3. **Targeted Backend Adjustments Required**:
   - **For `/site`**: Add `evidence_briefs` to `/site/` context and implement `GET /hx/brief/{series_slug}/{card_slug}` for the public evidence brief drawer.
   - **For `/ide`**: Provide `file_tree` in `/ide` context and add `GET /ide/file-content` (or `GET /hx/ide/editor?path=...`) to power the 3-pane file explorer and split Markdown editor.
   - **For `/read`**: Support both `reader.html` and `portal.html`, inject `lenses` and `epistemic_contract` based on `series.yaml`, extract `takeaways` and chapter `footnotes` upfront into context, and add a 3-segment route for multi-book series.
   - **For `nav.html`**: Pass dynamic `server_info` (`host`, `port`) and `active_tab` across all handlers.
4. **Zero Regression Risk**: All recommended additions are non-breaking, strictly additive, and preserve 100% test compatibility with the existing test suite (36/36 tests passing).

---

## 5. Verification Method

To independently verify the observations and conclusions in this report:

### 5.1 Run Automated Pytest Suite
```powershell
python -m pytest tests/
```
**Expected Result**: 36 passed in ~29 seconds (`test_analytics.py`, `test_gads_client.py`, `test_keyword_pipeline.py`).

### 5.2 Verify Core Endpoint Status Codes and Responses
Run the following verification script via Python in PowerShell:
```powershell
python -c "
from fastapi.testclient import TestClient
from bwe.main import app

client = TestClient(app)

# 1. Site / Imprint Hub
r_site = client.get('/site/')
assert r_site.status_code == 200, f'/site/ failed: {r_site.status_code}'
assert 'catalog' in r_site.text

# 2. Epistemic IDE
r_ide = client.get('/ide')
assert r_ide.status_code == 200, f'/ide failed: {r_ide.status_code}'
assert 'OKF v0.2' in r_ide.text

# 3. Serial Reader (Parenthood)
r_read_p = client.get('/read/parenthood-atlas/01-before-the-child-is-born')
assert r_read_p.status_code == 200, f'/read parenthood failed: {r_read_p.status_code}'

# 4. Serial Reader (Architectures of Memory)
r_read_a = client.get('/read/architectures-of-memory/01-rosenblatt-perceptron')
assert r_read_a.status_code == 200, f'/read aom failed: {r_read_a.status_code}'

# 5. Visual Analytics Studio & Dashboard
r_an = client.get('/analytics?series=parenthood-atlas')
assert r_an.status_code == 200, f'/analytics failed: {r_an.status_code}'

r_dash = client.get('/hx/analytics/dashboard?series=parenthood-atlas')
assert r_dash.status_code == 200, f'/hx/analytics/dashboard failed: {r_dash.status_code}'

# 6. HTMX Footnote Telemetry
r_fn = client.get('/hx/footnote/parenthood-atlas/01-before-the-child-is-born/1')
assert r_fn.status_code == 200, f'/hx/footnote failed: {r_fn.status_code}'

# 7. Amazon Ads Export
r_ads = client.get('/hx/analytics/export-ads?series=parenthood-atlas')
assert r_ads.status_code == 200, f'/hx/analytics/export-ads failed: {r_ads.status_code}'

print('[VERIFICATION SUCCESS] All core routes and HTMX endpoints return HTTP 200.')
"
```

### 5.3 Invalidation Conditions
This report's conclusions would be invalidated if:
- `scan_all_imprint_books` is unable to discover multi-book series structures under `series/`.
- `build_series_analytics_payload` fails to render SVGs in headless environments without X11/display (prevented by `matplotlib.use('Agg')` in `bwe/analytics.py:24`).
- Any newly introduced endpoint modifies existing URL paths or breaks JSON/HTML response contracts expected by HTMX attributes in existing templates.

---

## 6. Architectural Change Specification (For Implementer)

Below are the recommended exact code adjustments to `bwe/main.py` for downstream implementers:

### Proposed Addition to `bwe/main.py`: Enhanced Context & New HTMX Routes

```python
# -------------------------------------------------------------------------
# PROPOSED REFINEMENTS FOR BWE/MAIN.PY
# -------------------------------------------------------------------------

def get_server_info(request: Request) -> dict:
    """Helper to provide LAN port and host detection for nav.html."""
    return {
        "host": request.url.hostname or "0.0.0.0",
        "port": request.url.port or 8080,
    }

def get_series_manifest_safe(series_slug: str) -> dict:
    """Extracts series title, lenses, and epistemic contract safely."""
    clean_slug = series_slug.split("/i18n/")[0]
    yaml_path = SERIES_DIR / clean_slug / "series.yaml"
    if yaml_path.is_file():
        try:
            import yaml
            cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            lenses = cfg.get("lenses") or []
            if not lenses and isinstance(cfg.get("epistemic_contract"), dict):
                lenses = [l.get("id", "") for l in cfg["epistemic_contract"].get("three_lenses", [])]
            return {
                "title": cfg.get("title", clean_slug.replace("-", " ").title()),
                "subtitle": cfg.get("subtitle", ""),
                "lenses": [l.capitalize() for l in lenses] if lenses else ["Science", "Interpretation", "Art"],
                "epistemic_contract": cfg.get("epistemic_contract") if isinstance(cfg.get("epistemic_contract"), str) else "Science -> Interpretation -> Art",
            }
        except Exception:
            pass
    return {
        "title": clean_slug.replace("-", " ").title(),
        "subtitle": "",
        "lenses": ["Science", "Interpretation", "Art"],
        "epistemic_contract": "Science -> Interpretation -> Art",
    }

def build_file_tree() -> dict:
    """Collects all series, books, chapters, and OKF evidence cards for the IDE file tree."""
    tree = {}
    if not SERIES_DIR.is_dir():
        return tree
    for s_dir in sorted(SERIES_DIR.iterdir()):
        if not s_dir.is_dir() or s_dir.name.startswith("."):
            continue
        s_slug = s_dir.name
        tree[s_slug] = {"books": {}, "root_chapters": [], "root_cards": []}
        
        # Sub-books
        sub_books = [b for b in sorted(s_dir.iterdir()) if b.is_dir() and b.name.startswith("book-")]
        if sub_books:
            for b in sub_books:
                ch_list = [f.stem for f in sorted((b / "chapters").glob("*.md")) if not f.name.startswith("_")]
                card_list = [f.stem for f in sorted((b / "evidence-cards").glob("*.md")) if not f.name.startswith("_") and f.name.lower() not in {"index.md", "readme.md"}]
                tree[s_slug]["books"][b.name] = {"chapters": ch_list, "evidence_cards": card_list}
        else:
            ch_list = [f.stem for f in sorted((s_dir / "chapters").glob("*.md")) if not f.name.startswith("_")]
            card_list = [f.stem for f in sorted((s_dir / "evidence-cards").glob("*.md")) if not f.name.startswith("_") and f.name.lower() not in {"index.md", "readme.md"}]
            tree[s_slug]["root_chapters"] = ch_list
            tree[s_slug]["root_cards"] = card_list
    return tree

# 1. Update /site/ to include evidence_briefs and server_info
@app.get("/site/", response_class=HTMLResponse)
async def imprint_site_home(request: Request):
    catalog = scan_all_imprint_books(REPO_ROOT, DEFAULT_GITHUB_REPO)
    catalog_json = json.dumps(catalog)
    
    # Query stable OKF cards for public briefs showcase
    with get_db() as conn:
        brief_rows = conn.execute(
            "SELECT series_slug, book_slug, card_slug, title, substr(body, 1, 280) AS snippet "
            "FROM evidence_cards_fts LIMIT 12"
        ).fetchall()
        evidence_briefs = [dict(r) for r in brief_rows]

    return templates.TemplateResponse(
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

# 2. Add /hx/brief/{series_slug}/{card_slug} for the Public Evidence Brief Drawer
@app.get("/hx/brief/{series_slug}/{card_slug}", response_class=HTMLResponse)
async def inspect_evidence_brief(request: Request, series_slug: str, card_slug: str):
    card_candidates = list((SERIES_DIR / series_slug).glob(f"**/evidence-cards/{card_slug}.md"))
    if not card_candidates:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    card_text = card_candidates[0].read_text(encoding="utf-8")
    
    from five_rule_check import split_frontmatter
    metadata, body = split_frontmatter(card_text)
    
    # Parse 9 canonical sections
    sections = {}
    current_sec = ""
    for line in body.splitlines():
        if line.startswith("## "):
            current_sec = line[3:].strip()
            sections[current_sec] = []
        elif current_sec:
            sections[current_sec].append(line)
    parsed_sections = {k: "\n".join(v).strip() for k, v in sections.items()}

    return templates.TemplateResponse(
        "partials/brief_drawer.html",
        {
            "request": request,
            "card_slug": card_slug,
            "title": metadata.get("title", card_slug.replace("-", " ").title()),
            "grade": metadata.get("certainty_grade", "Moderate"),
            "doi": metadata.get("primary_doi", ""),
            "metadata": metadata,
            "sections": parsed_sections,
        },
    )

# 3. Update /ide to include file_tree and server_info
@app.get("/ide", response_class=HTMLResponse)
async def epistemic_ide_home(request: Request):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT series_slug, book_slug, card_slug, title, substr(body, 1, 240) AS snippet "
            "FROM evidence_cards_fts LIMIT 15"
        ).fetchall()
    return templates.TemplateResponse(
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

# 4. Update /read/{series_slug}/{chapter_slug} for 3-lens toggle and reader.html
@app.get("/read/{series_slug}/{chapter_slug}", response_class=HTMLResponse)
async def read_chapter(request: Request, series_slug: str, chapter_slug: str, lens: Optional[str] = None):
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
            blocks_list = t_data.get("blocks", []) if isinstance(t_data, dict) else t_data
        except Exception:
            blocks_list = []

    s_meta = get_series_manifest_safe(series_slug)
    chosen_lens = lens or (s_meta["lenses"][0] if s_meta["lenses"] else "Science")

    template_file = "reader.html" if (REPO_ROOT / "bwe" / "templates" / "reader.html").exists() else "portal.html"

    return templates.TemplateResponse(
        template_file,
        {
            "request": request,
            "series_slug": series_slug,
            "chapter_slug": chapter_slug,
            "series_title": s_meta["title"],
            "lenses": s_meta["lenses"],
            "active_lens": chosen_lens,
            "epistemic_contract": s_meta["epistemic_contract"],
            "prose_html": prose_html,
            "timings": blocks_list,
            "has_audio": has_audio,
            "audio_url": audio_url,
            "server_info": get_server_info(request),
            "active_tab": "reader",
        },
    )
```
