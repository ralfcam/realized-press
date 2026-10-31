# Handoff Report: Challenger 2 — Layout Stability & Interaction Empirical Verification

**Author:** Challenger 2 (Layout Stability & Interaction Challenger)  
**Date:** 2026-10-31T12:25:00Z  
**Working Directory:** `c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\challenger_2\`  
**Recommendation:** **REQUEST_CHANGES**  

---

## Challenge Summary

- **Overall Risk Assessment:** **MEDIUM-HIGH**
- **Component Markup & Layout Stability:** **APPROVE** (Exceptional CSS layout stability, zero Cumulative Layout Shift during HTMX swaps, 100% compliant >=44px touch targets, ARIA roles, and responsive markup across all 4 core views).
- **Interactive Backend Robustness:** **REQUEST_CHANGES** (Empirical testing discovered reproducible HTTP 500 crashes during live user interaction in the IDE card search input and invalid series query handling in the Analytics dashboard).

---

## 1. Observation

### 1.1 Automated Test Execution
- **Full Test Suite (`python -m pytest tests/ -v`)**:
  - Ran 46 tests across `tests/test_analytics.py`, `tests/test_bwe_views.py`, `tests/test_gads_client.py`, `tests/test_keyword_pipeline.py`, and `tests/test_ui_compliance.py`.
  - Result: `46 passed in 330.57s (0:05:30)`.
- **Strict UI Acceptance Gate (`STRICT_UI_GATE=1 python -m pytest tests/test_ui_compliance.py -v`)**:
  - `test_touch_target_sizes`: PASSED (0 touch target violations across all templates).
  - `test_wcag_color_contrast`: PASSED (0 occurrences of `text-stone-500` / `text-stone-600` on dark backgrounds).
  - `test_dark_mode_palette`: PASSED (0 occurrences of generic `red-400`/`red-500` classes; all alerts use canonical `rose-400`/`rose-500`).
- **Dedicated Empirical Layout & Interaction Suite (`python -m pytest tests/test_challenger_layout.py -v`)**:
  - 13 empirical tests verifying triggers, swap targets, DOM structure, traversal security, and stress scenarios.
  - Result: `13 passed in 32.49s`.

### 1.2 Layout Stability & Interaction Hook Audit
1. **Public Evidence Brief Drawer (`/site/` and `/hx/brief/{series}/{card}`)**:
   - `bwe/templates/site.html:176-180`: Trigger buttons define `hx-get="/hx/brief/{{ brief.series_slug }}/{{ brief.card_slug }}"`, `hx-target="#brief-drawer"`, `hx-swap="innerHTML"`.
   - `bwe/templates/site.html:273`: Target container `<div id="brief-drawer" data-brief-drawer="true" class="relative z-50"></div>` exists and matches target ID.
   - `bwe/templates/partials/brief_drawer.html:1-9`: Renders `<div class="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="brief-drawer-title">` with fixed backdrop and slide-over panel. Zero layout shift is introduced to the document flow because the drawer is rendered as a fixed overlay above the catalog and audio player.
2. **3-Pane Epistemic IDE (`/ide`)**:
   - `bwe/templates/ide.html:85`: File explorer renders `<aside id="file-explorer">` with book accordions and chapter links targeting `#editor-container`.
   - `bwe/templates/ide.html:290`: Editor renders `<section id="editor-container">` with split editor flex layout (`flex-col md:flex-row h-full overflow-hidden`).
   - `bwe/templates/ide.html:446-674`: TTS Panel renders `<button id="tab-tts" role="tab" aria-controls="panel-tts">`, `<section id="panel-tts" role="tabpanel" aria-labelledby="tab-tts">`, `#tts-terminal`, and `#tts-sse-mount`.
   - `bwe/main.py:733-750`: Directory traversal attacks (`../../etc/passwd`, `..\\..\\Windows\\win.ini`) are rejected cleanly with HTTP 404.
3. **Serial Reader (`/read/{series}/{chapter}`)**:
   - `bwe/templates/reader.html:173-193`: Three-lens toggle `<div id="lens-toggle" data-lens-toggle="true" role="group">` renders buttons with `aria-label`, `:aria-pressed`, and `>=44px` hit targets.
   - `bwe/templates/reader.html:254`: Manuscript prose renders in isolated `<article id="reader-content" class="prose prose-invert prose-stone max-w-3xl mx-auto font-serif">` inside `lg:col-span-8`.
   - `bwe/templates/reader.html:261-292`: Chapter takeaways render in `<section id="takeaways" class="chapter-takeaway bg-stone-900/90 border border-amber-500/30 rounded-xl p-6 my-8 shadow-xl">` with 3-Tier Causal Resolution badges.
   - `bwe/templates/reader.html:300-320`: Footnote apparatus renders in `<section id="footnote-drawer">` with `<div id="footnote-drawer-content">` isolated in `lg:col-span-4`. Footnote swaps do not shift manuscript prose.
   - `bwe/templates/reader.html:377`: Floating `<div id="footnote-tooltip">` with bounded coordinate calculation (`left` clamped to viewport width) prevents horizontal screen overflow.
4. **Analytics Dashboard (`/analytics` and `/hx/analytics/dashboard`)**:
   - `bwe/templates/analytics.html:97`: Host container `<div id="analytics-content" class="min-h-[600px]">` explicitly defines `min-h-[600px]`, eliminating layout collapse and Cumulative Layout Shift during HTMX series switches.
   - `bwe/templates/partials/analytics_dashboard.html`: Embeds Demand Quadrant SVG, Chapter Volume & CPC SVG, 7 KDP boxes (with 50-byte progress bars and >=44px copy buttons), and 12-month sparklines.
5. **Mobile Navigation (`bwe/templates/partials/nav.html`)**:
   - Navigation header defines `role="banner"`, `order-3 md:order-2` responsive flex order, `role="tablist"` with 4 ARIA tabs meeting `>=44px` touch targets.
   - Mobile menu toggle button specifies `aria-controls="mobile-nav-drawer"`, `:aria-expanded="mobileMenuOpen"`, `md:hidden`, and `min-h-[44px] min-w-[44px]`.
   - Mobile dropdown `#mobile-nav-drawer` has `x-show="mobileMenuOpen"` with `md:hidden` and smooth Alpine transitions.

### 1.3 Empirical Vulnerabilities Uncovered
During adversarial stress testing, three unhandled exceptions were reproduced empirically:

1. **Bug 1 — SQLite FTS5 Syntax Crash on Live IDE Card Search (`bwe/main.py:713`)**:
   ```
   Command: client.get("/ide/search-cards?q=\"\"\"'''")
   Error: sqlite3.OperationalError: fts5: syntax error near "'"
   File: bwe\main.py:713, in search_evidence_cards
         rows = conn.execute(
             "SELECT series_slug, book_slug, card_slug, title, snippet(evidence_cards_fts, 4, '<mark>', '</mark>', '...', 24) AS snippet "
             "FROM evidence_cards_fts WHERE evidence_cards_fts MATCH ? LIMIT 20",
             (f'"{q}"*',),
         ).fetchall()
   ```
   - **Root Cause**: The query parameter `q` is directly wrapped into `(f'"{q}"*',)`. When the query contains double quotes (`"`), single quotes (`'`), or unmatched FTS5 operators (`AND`, `OR`, `*`), SQLite throws an `OperationalError`. Because the input field in `ide.html:483` has `hx-trigger="keyup changed delay:200ms, search"`, author keystrokes containing quotes immediately crash the server with HTTP 500.

2. **Bug 2 — Unhandled `IndexError` on Analytics for Invalid/Uninitialized Series (`bwe/analytics.py:790` & `bwe/main.py:901, 932`)**:
   ```
   Command: client.get("/analytics?series=bogus_series_slug")
   Error: IndexError: index -1 is out of bounds for axis 0 with size 0
   File: bwe\analytics.py:790, in export_static_charts
         if cum_vols[-1] > 0:
   ```
   - **Root Cause**: `view_analytics` and `hx_analytics_dashboard` call `export_static_charts` without verifying whether the series exists or has seed data. An empty `cum_vols` array triggers `IndexError: index -1 is out of bounds` (or `FileNotFoundError` when creating chart directories for bogus paths), crashing the route with HTTP 500 instead of returning HTTP 404.

3. **Bug 3 — Unhandled `FileNotFoundError` on `write-kdp-yaml` Action (`scripts/marketing_intelligence.py:1163` & `bwe/main.py:986`)**:
   ```
   Command: client.post("/hx/analytics/write-kdp-yaml?series=bogus_series")
   Error: FileNotFoundError: [Errno 2] No such file or directory: '...\\series\\bogus_series\\series.yaml'
   File: scripts\marketing_intelligence.py:1163, in optimize_kdp_boxes_report
         data = yaml.safe_load((series_dir / "series.yaml").read_text(encoding="utf-8")) or {}
   ```
   - **Root Cause**: The action handler attempts to read `series/{series_slug}/series.yaml` without pre-checking file existence, raising `FileNotFoundError` (HTTP 500).

4. **Polish 4 — Missing Escape Keydown Dismissal on Brief Modal (`bwe/templates/partials/brief_drawer.html:1`)**:
   - `partials/brief_drawer.html` implements `role="dialog"` and `aria-modal="true"`, but lacks an `@keydown.escape.window` event listener, preventing keyboard-only users from dismissing the modal via the `Escape` key.

---

## 2. Logic Chain

1. **Premise 1**: A publishing environment template and interaction pass must provide both visual stability (zero CLS, 44px touch targets, correct ARIA hooks) and robust interactive behavior without unhandled server crashes during live operator use.
2. **Step 2 (Layout & CSS Verification)**:
   - Automated testing with `STRICT_UI_GATE=1` confirmed 0 touch target violations (<44px), 0 low-contrast text classes (`stone-500/600`), and 0 generic red tokens.
   - Inspection of `#brief-drawer` verified `fixed inset-0 z-50` overlay geometry, meaning drawer activation leaves catalog, player, and article DOM completely unperturbed.
   - Inspection of `#analytics-content` verified `min-h-[600px]`, preventing Cumulative Layout Shift during HTMX partial re-renders.
   - Inspection of `#reader-content` verified it is strictly isolated in `lg:col-span-8` while the footnote apparatus resides in `lg:col-span-4`, guaranteeing that footnote inspection never disrupts prose reading.
3. **Step 3 (Adversarial Interaction Verification)**:
   - Empirical execution of `test_ide_card_search_malformed_query_vulnerability` proved that typing quotes into the live card search box crashes the server (`sqlite3.OperationalError: fts5: syntax error`).
   - Empirical execution of `test_analytics_invalid_series_vulnerability` proved that navigating to `/analytics` with an unrecognized series slug causes an unhandled `IndexError` / `FileNotFoundError` (HTTP 500).
   - Execution of `test_public_evidence_brief_drawer_html_structure` confirmed the absence of an `Escape` key event listener on the modal dialog.
4. **Conclusion**:
   - While the visual and layout stability requirements (M3/M4) are thoroughly satisfied and adhere to all design system guidelines, the live interactive search and route handlers fail under predictable user inputs (typing quotes, navigating with arbitrary query parameters).
   - Therefore, the system requires changes before final approval.

---

## 3. Caveats

- **Network-Level CLS**: Visual stability was validated via static DOM geometry and layout container classes (`min-h-[600px]`, `fixed inset-0`, flex constraints). High-latency real-browser CLS was not measured via Lighthouse/Puppeteer, but the CSS layout constraints prevent container collapse.
- **Audio Decoding**: Live Web Audio API playback was tested via DOM structure and media routes; hardware audio output was not tested.
- **Scope Restriction**: In accordance with the Review-Only constraint, Challenger 2 authored tests reproducing the bugs but did not edit implementation files in `bwe/` or `series/`.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

### Actionable Remediation Items for Implementers:
1. **Fix FTS5 Query Sanitization (`bwe/main.py:703-718`)**:
   - Sanitize `q` by escaping quotes (e.g., `safe_q = q.replace('"', '""')` or strip non-word characters for prefix matching).
   - Wrap `conn.execute()` in `try...except sqlite3.OperationalError:` and return `rows = []` on syntax errors so the user is presented with an empty result rather than an HTTP 500 crash.
2. **Fix Series Parameter Validation in Analytics (`bwe/main.py:889-947` & `bwe/analytics.py:790`)**:
   - Check `if not (SERIES_DIR / series).exists(): raise HTTPException(status_code=404, detail=f"Series '{series}' not found")` in `view_analytics` and `hx_analytics_dashboard`.
   - In `bwe/analytics.py:790`, guard `if cum_vols.size > 0 and cum_vols[-1] > 0:` to prevent `IndexError` when dataset is empty.
3. **Fix Series Validation in KDP YAML Writer (`bwe/main.py:975-993`)**:
   - Validate that `(SERIES_DIR / series / "series.yaml").is_file()` before calling `optimize_kdp_boxes_report`, returning HTTP 404 or a structured error banner if missing.
4. **Add Escape Key Listener to Brief Drawer (`bwe/templates/partials/brief_drawer.html:1`)**:
   - Add `@keydown.escape.window="document.getElementById('brief-drawer').innerHTML = ''"` to the top-level `<div ... role="dialog">` container.

---

## 5. Verification Method

To independently reproduce all observations and verify remediation:

1. **Run Full Test Suite**:
   ```powershell
   python -m pytest tests/ -v
   ```
2. **Run Strict UI Compliance Gate (Zero Violations Confirmed)**:
   ```powershell
   python -c "import os, sys, pytest; os.environ['STRICT_UI_GATE']='1'; sys.exit(pytest.main(['tests/test_ui_compliance.py', '-v']))"
   ```
3. **Run Challenger Layout & Interaction Empirical Verification Suite**:
   ```powershell
   python -m pytest tests/test_challenger_layout.py -v
   ```
4. **Reproduce Bug 1 (FTS5 Crash on Card Search)**:
   ```powershell
   python -c "from fastapi.testclient import TestClient; from bwe.main import app; c = TestClient(app); r = c.get('/ide/search-cards?q=\"\"\"\'\'\''); print(r.status_code)"
   ```
   *Expected after fix*: HTTP 200 with empty results. *Current behavior*: `sqlite3.OperationalError` (500).
5. **Reproduce Bug 2 (IndexError on Analytics Series)**:
   ```powershell
   python -c "from fastapi.testclient import TestClient; from bwe.main import app; c = TestClient(app); r = c.get('/analytics?series=bogus_series_slug'); print(r.status_code)"
   ```
   *Expected after fix*: HTTP 404. *Current behavior*: `IndexError` (500).
