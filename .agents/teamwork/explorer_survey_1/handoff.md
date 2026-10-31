# Comprehensive Front-End UI & Template Audit Report

**Working Directory**: `c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\`  
**Investigator**: Frontend UI Explorer (`explorer_survey_1`)  
**Mission**: Technical investigation of `bwe/templates/`, `bwe/templates/partials/`, static assets, and backend bindings against Requirements R1–R4.  
**Date**: 2026-10-31  

---

## Executive Summary

A comprehensive static and runtime inspection was conducted on all templates in `bwe/templates/` (`site.html`, `portal.html`, `ide.html`, `analytics.html`), `bwe/templates/partials/` (`nav.html`, `analytics_dashboard.html`, `footnote_drawer.html`, `telemetry_table.html`, `audit_results.html`), static assets in `bwe/static/`, and route handlers in `bwe/main.py`.

The audit identified five critical structural and design gaps:
1. **Missing Foundational Architecture**: There is no shared `base.html` template. Each view independently duplicates boilerplate `<!DOCTYPE html>`, `<head>`, metadata, and CDN script tags (`htmx`, `alpinejs`, `tailwindcss`, `katex`). Furthermore, `reader.html` does not exist; the backend currently renders `portal.html`.
2. **Visual Design Inconsistency (`site.html`)**: `site.html` contains over 1,000 lines of legacy inline CSS (lines 17–1074) using custom variables (`--bg: #0c0a09;`, `--gold: #f59e0b;`) and system sans-serif fonts, conflicting with the R2 design system tokens (`stone-950` background, `stone-900`/`stone-800` surfaces, `amber-400`/`amber-500` accents, `font-serif`/`font-mono`).
3. **Missing Core Interactive Components**:
   - `/site`: Missing an interactive Public Evidence Brief drawer (currently links out to an external PDF).
   - `/ide`: Missing the required file explorer and split Markdown editor (currently only contains an FTS5 search list, an audit script runner form, and a TTS log stream).
   - `/read`: Missing the 3-lens toggle (Science / Interpretation / Art), styled takeaway cards, and inline footnote tooltips.
4. **Touch Target Size Violations (< 44px)**: Interactive controls systematically drop below 44px on desktop and mobile: `nav.html` tab targets are 36–40px, IDE selects/inputs are 36–38px, KDP box copy buttons are 20px, and footnote dismiss buttons are 36px.
5. **Test Coverage Deficit**: Automated tests in `tests/test_analytics.py` pass (8/8), but verify *only* `/analytics`. There are zero automated tests verifying HTTP 200 or element rendering for `/site`, `/ide`, or `/read/{series}/{chapter}`.

---

## 1. Observation

### 1.1 Template Architecture & Missing Files

1. **Absence of `base.html`**:
   - A search via `find_by_name` across `bwe/templates/` reveals only four top-level templates: `analytics.html`, `ide.html`, `portal.html`, `site.html`.
   - `bwe/templates/base.html` **does not exist**.
   - As a direct consequence, each template duplicates `<head>`, meta tags, and CDN assets:
     - `site.html:11-16`: KaTeX CSS, KaTeX JS, auto-render JS, HTMX 2.0.4, Alpine.js 3.14.8, Tailwind CSS CDN script.
     - `portal.html:11-16`: HTMX 2.0.4, Alpine.js 3.14.8, Tailwind CSS CDN script, KaTeX CSS, KaTeX JS, auto-render JS.
     - `ide.html:11-14`: HTMX 2.0.4, htmx-ext-sse 2.2.2, Alpine.js 3.14.8, Tailwind CSS CDN script.
     - `analytics.html:9-11`: HTMX 2.0.4, Alpine.js 3.14.8, Tailwind CSS CDN script.
2. **Absence of `reader.html`**:
   - `bwe/templates/reader.html` **does not exist**.
   - In `bwe/main.py` lines 183–227, the chapter reader endpoint is bound to `portal.html`:
     ```python
     # bwe/main.py:215-217
     return templates.TemplateResponse(
         "portal.html",
         { ... }
     )
     ```
3. **Static Directory State**:
   - `bwe/static/` contains only `.gitkeep` (0 bytes). No localized CSS, compiled Tailwind output, or frontend modules exist. Everything relies on runtime CDN script execution (`https://cdn.tailwindcss.com`).

---

### 1.2 View 1: `/site` (`site.html`) — Design System & Component Audit

1. **Legacy Inline Styling Conflict (R2 Violation)**:
   - Lines 17–1074 of `bwe/templates/site.html` consist of an inline `<style>` block (1,057 lines).
   - It defines a custom color palette rather than Tailwind's `stone` tokens:
     ```css
     /* site.html:18-35 */
     :root {
       --bg: #0c0a09;
       --card-bg: #1c1917;
       --card-hover: #292524;
       --border: #292524;
       --border-light: #44403c;
       --gold: #f59e0b;
       --gold-light: #fbbf24;
       --gold-dim: rgba(245, 158, 11, 0.12);
       --gold-glow: rgba(245, 158, 11, 0.25);
       --text: #f5f5f4;
       --text-muted: #a8a29e;
       --accent: #38bdf8;
       --success: #34d399;
       --sidebar-w: 320px;
       --dock-h: 104px;
       --safe-bottom: env(safe-area-inset-bottom, 0px);
     }
     ```
   - Body font rule:
     ```css
     /* site.html:42-47 */
     body {
       font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       background: var(--bg);
       color: var(--text);
     ```
   - Literary headings (`.hero-title`, `.hero-subtitle`, `.book-nav-title`) do not apply `font-serif`.
   - At line 1079, `{% include "partials/nav.html" %}` is injected, resulting in two conflicting layout styles (pure Tailwind in `nav.html` vs custom CSS classes `.navbar`, `.brand`, `.brand-mark`, `.main-layout`, `.catalog-sidebar`).
2. **Missing Public Evidence Brief Drawer**:
   - Requirement R1 stipulates: `"/site (site.html): Imprint home, multi-series showcase, audiobook player, and public evidence brief drawer."`
   - In `site.html:1158-1180`, the "Tier 1: Public Evidence Briefs" section only contains a static external download anchor:
     ```html
     <!-- site.html:1162-1164 -->
     <div class="tier-links">
       <a href="https://github.com/ralfcam/realized-press/releases/download/v1.0-rc1/parenthood-atlas-evidence-briefs-compendium.pdf" target="_blank">Download Compendium PDF →</a>
     </div>
     ```
   - Ten standalone HTML evidence briefs exist in `series/parenthood-atlas/publishing/evidence-briefs/` (`deferred-imitation.html`, `infant-contingency-learning.html`, etc.), but `site.html` has no drawer, modal, or HTMX loader to view them inline.

---

### 1.3 View 2: `/ide` (`ide.html`) — 3-Pane Architecture & Component Audit

1. **Structural Mismatch with Requirement R1**:
   - Requirement R1: `"/ide (ide.html): 3-Pane Epistemic IDE including file explorer, split Markdown editor, and OKF v0.2 Evidence Card live drawer."`
   - Actual structure in `bwe/templates/ide.html:84-265`:
     - **Pane 1 (Column 1, lines 86–138)**: SQLite FTS5 search on `evidence_cards_fts`. Allows search and copying `[^card_slug]`.
     - **Pane 2 (Column 2, lines 140–192)**: Subprocess Audit Gate runner (`five_rule_check.py`, `audit_manuscript.py`, `audit_epub.py`).
     - **Pane 3 (Column 3, lines 194–264)**: SSE TTS synthesis log streamer (`/ide/tts-stream/{series}/{chapter}`).
   - **Gaps**:
     - No file explorer (directory tree of chapters, cards, notes, outlines).
     - No split Markdown editor (editor textarea + preview renderer).
     - The OKF cards are in a fixed search column rather than an integrated slide-out live drawer.

---

### 1.4 View 3: `/read/{series}/{chapter}` (`portal.html`) — Typography, Lenses, Takeaways, Footnotes

1. **Missing 3-Lens Toggle**:
   - `portal.html` renders `{{ prose_html | safe }}` (line 105) inside a `<main>` container.
   - There are **no UI controls or toggles** to filter or highlight content according to the 3-lens framework (`Science`, `Interpretation`, `Art` for *Parenthood: The Atlas*; `Technical`, `Organizational`, `Philosophical` for *Architectures of Memory*).
2. **Missing Takeaway Card Styling**:
   - Chapters contain `<aside class="chapter-takeaway">` blocks (e.g. `01-before-the-child-is-born.md:88-94` containing "What the Evidence Shows", "What You Can Let Go Of", "The Core Rule").
   - `portal.html` has zero CSS rules for `.chapter-takeaway`. It renders as unformatted default HTML paragraphs inside Tailwind's `prose-invert`.
3. **Footnote Interaction vs Inline Tooltips**:
   - In `portal.html:326-344`, clicking a footnote ref executes an HTMX request to `/hx/footnote/{series}/{chapter}/{fnId}` and updates `#footnote-drawer-content`.
   - On line 341, it executes:
     ```javascript
     drawer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
     ```
     On mobile viewports, where the drawer is stacked below the main text, this scrolls the viewport away from the reader's paragraph.
   - There are **no inline hover/focus tooltips** on footnote references.

---

### 1.5 View 4: `/analytics` (`analytics.html` & `partials/analytics_dashboard.html`)

1. **Dashboard Completeness**:
   - Features the Demand Quadrant SVG scatter plot (`analytics_dashboard.html:98`), Chapter Volume & CPC bars (`analytics_dashboard.html:120`), KDP 7-box 50-byte utilization gauges (`analytics_dashboard.html:158-185`), and filterable signal table with 12-month sparklines (`analytics_dashboard.html:189-298`).
2. **Color Token Non-Compliance**:
   - `analytics_dashboard.html:164`: `text-red-400` instead of `text-rose-400`.
   - `analytics_dashboard.html:169`: `bg-red-500` instead of `bg-rose-500`.
   - `analytics.html:14`: `.deck-container { background-color: #ffffff; ... }` (light background in dark mode context).

---

### 1.6 Navigation & Layout: `partials/nav.html`

1. **Layout & Semantics**:
   - Brand badge: Lines 5–13 ("R" amber gradient mark + "REALIZED PRESS").
   - LAN Port Indicator: Lines 66–69 (`LAN 8080` with pulsating emerald dot).
   - Navigation links:
     - Uses `role="tablist"` with `<a role="tab">` (lines 22–62).
     - Because these perform full page navigations (`href="/site"`, `href="/ide"`, etc.) rather than controlling on-page tabpanels, they lack `aria-controls` attributes and standard keyboard tab navigation.
     - The "Reader" tab hardcodes `href="/read/parenthood-atlas/01-before-the-child-is-born"` (line 43).

---

### 1.7 Accessibility (R3) & Touch Target Size Audit (>=44px)

Static code inspection reveals widespread violations of the 44px minimum touch target size (WCAG 2.5.5 / 2.5.8):

| File | Line Number | Element / Selector | Current Target Size | Compliant (>=44px)? | Required Fix |
|---|---|---|---|---|---|
| `bwe/templates/partials/nav.html` | 26, 36, 46, 56 | Central nav tab anchors (`Audio`, `IDE`, `Reader`, `Analytics`) | `min-h-[40px] sm:min-h-[36px]` | **NO** (36px–40px) | Change to `min-h-[44px] min-w-[44px]` |
| `bwe/templates/partials/nav.html` | 76 | Linear ARC external link | `min-h-[36px]` | **NO** (36px) | Change to `min-h-[44px]` |
| `bwe/templates/site.html` | 123, 1366 | `.nav-link-btn` (Reader button in playlist) | `padding: 5px 9px; font-size: 0.72rem;` | **NO** (~26px) | Set `min-h-[44px] min-w-[44px]` |
| `bwe/templates/site.html` | 156 | `.series-chip` (Mobile book selector) | `padding: 6px 14px; font-size: 0.8rem;` | **NO** (~32px) | Set `min-h-[44px]` |
| `bwe/templates/site.html` | 332 | `.source-btn` (Cloud vs Local audio) | `min-height: 34px;` | **NO** (34px) | Set `min-height: 44px;` |
| `bwe/templates/site.html` | 950 | `.dock-speed` (Playback speed dropdown) | `min-height: 38px;` | **NO** (38px) | Set `min-height: 44px;` |
| `bwe/templates/site.html` | 1730 | Footnote drawer close button (`✕`) | `px-2 py-0.5 rounded` | **NO** (~24px) | Set `min-h-[44px] min-w-[44px]` |
| `bwe/templates/portal.html` | 95 | Scrubber area (`#reader-scrubber`) | `h-3 flex items-center` (container) | **NO** (12px height) | Add vertical padding `py-3` to reach 44px |
| `bwe/templates/portal.html` | 134 | `#feedback-category` select | `min-h-[44px] sm:min-h-[38px]` | **NO** (38px on `sm:`) | Retain `min-h-[44px]` on all viewports |
| `bwe/templates/partials/footnote_drawer.html` | 12 | Footnote dismiss button (`✕`) | `min-h-[36px] min-w-[36px]` | **NO** (36px) | Change to `min-h-[44px] min-w-[44px]` |
| `bwe/templates/ide.html` | 109 | FTS5 search `<input type="search">` | `min-h-[44px] sm:min-h-[38px]` | **NO** (38px on `sm:`) | Retain `min-h-[44px]` on all viewports |
| `bwe/templates/ide.html` | 125 | Footnote tag copy `<button>` | `min-h-[38px]` | **NO** (38px) | Change to `min-h-[44px]` |
| `bwe/templates/ide.html` | 161, 169 | `#gate-script`, `#target-path` selects | `min-h-[44px] sm:min-h-[36px]` | **NO** (36px on `sm:`) | Retain `min-h-[44px]` on all viewports |
| `bwe/templates/ide.html` | 219, 224 | `#tts-series-select`, `#tts-chapter-select` | `min-h-[44px] sm:min-h-[36px]` | **NO** (36px on `sm:`) | Retain `min-h-[44px]` on all viewports |
| `bwe/templates/analytics.html` | 53, 56 | Top action links (IDE, Linear) | `px-3 py-2 text-xs` | **NO** (~32px) | Change to `min-h-[44px]` |
| `bwe/templates/analytics.html` | 67, 75, 83 | Series switcher buttons | `px-4 py-2.5 text-xs` | **NO** (~36px) | Set `min-h-[44px]` |
| `bwe/templates/partials/analytics_dashboard.html` | 93, 94, 115, 116 | Chart PNG/SVG download links | `px-2 py-1 text-[10px]` | **NO** (~24px) | Change to `min-h-[44px] px-3` or icon buttons |
| `bwe/templates/partials/analytics_dashboard.html` | 141, 147 | Action buttons (Export Ads, Write YAML) | `px-3 py-1.5 text-xs` | **NO** (~30px) | Change to `min-h-[44px]` |
| `bwe/templates/partials/analytics_dashboard.html` | 179 | KDP box copy button | `px-2 py-0.5 text-[10px]` | **NO** (~20px) | Change to `min-h-[44px] min-w-[44px]` |
| `bwe/templates/partials/analytics_dashboard.html` | 207, 213, 221 | Table search input & filter selects | `px-2.5 py-1.5 text-xs` | **NO** (~32px) | Change to `min-h-[44px]` |

---

### 1.8 WCAG 2.1 AA Color Contrast Audit

WCAG 2.1 AA requires a minimum contrast ratio of **4.5:1** for normal text and **3.0:1** for large text (>= 18pt or >= 14pt bold):
1. **Failing Text Pairings**:
   - `text-stone-500` (`#78716c`) on `bg-stone-950` (`#0c0a09`): Contrast ratio is **4.13:1** (Fails 4.5:1 requirement).
     - Found in:
       - `analytics_dashboard.html:13,24,33,42,52,62,72`: Microcopy subtitles under KPI numbers.
       - `analytics_dashboard.html:176`: "UTF-8 Collocations" label.
       - `analytics.html:98`: Footer copy.
       - `ide.html:134,259`: Empty state / ready notes.
     - **Fix**: Elevate to `text-stone-400` (`#a8a29e`), which achieves an **8.12:1** contrast ratio against `stone-950`.
2. **Passing Text Pairings**:
   - `amber-400` (`#fbbf24`) on `stone-950`: **10.5:1** (Passes).
   - `amber-300` (`#fcd34d`) on `stone-900`: **11.2:1** (Passes).
   - `stone-100` (`#f5f5f4`) on `stone-950`: **17.8:1** (Passes).
   - `stone-300` (`#d6d3d1`) on `stone-900`: **11.4:1** (Passes).
   - `emerald-400` (`#34d399`) on `stone-950`: **9.4:1** (Passes).
   - `rose-400` (`#fb7185`) on `stone-950`: **7.8:1** (Passes).

---

### 1.9 HTMX Integration, Dynamic Swaps & Layout Shift Risks

1. **Analytics Series Switch CLS (Cumulative Layout Shift)**:
   - When clicking series switcher tabs in `analytics.html:64,72,80`, HTMX targets `#analytics-content` with `hx-get="/hx/analytics/dashboard?series=..."`.
   - In `bwe/main.py:425`, if the static SVG charts do not exist on disk, `export_static_charts` executes synchronously (taking 1–3s).
   - `#analytics-content` has no CSS min-height or placeholder skeleton, causing the layout to collapse to 0px and re-expand on receipt.
2. **Reader Feedback OuterHTML Swap**:
   - In `portal.html:126-144`, the feedback form uses `hx-swap="outerHTML"`:
     ```html
     <form hx-post="/hx/feedback" hx-swap="outerHTML" ...>
     ```
   - In `bwe/main.py:295`, the server returns a confirmation banner:
     ```python
     return HTMLResponse(
         '<div class="p-3 text-sm bg-emerald-950 text-emerald-200 rounded border border-emerald-700">'
         '&check; Feedback logged for ARC-53 triage. Thank you.</div>'
     )
     ```
   - This permanently obliterates the form from the DOM, preventing readers from logging multiple notes during a chapter without a full page reload.

---

### 1.10 Backend Route Context & Test Suite Audit

1. **Existing Test Suite Baseline**:
   - Running `python -m pytest tests/test_analytics.py` succeeded (8 passed in 27.24s).
   - The tests cover:
     - `test_gini_coefficient_edge_cases`
     - `test_herfindahl_index_edge_cases`
     - `test_extract_series_bib_years`
     - `test_svg_generators`
     - `test_build_series_analytics_payload_parenthood_atlas`
     - `test_build_series_analytics_payload_architectures_of_memory`
     - `test_export_static_charts`
     - `test_analytics_web_dashboard`
2. **Missing Test Coverage**:
   - There are **no tests** in `tests/` for:
     - `/site/` (verifying HTTP 200, catalog payload rendering, player dock, series chips).
     - `/ide` (verifying HTTP 200, FTS5 cards rendering, form elements).
     - `/read/{series}/{chapter}` (verifying HTTP 200, prose rendering, audio elements, footnote drawer target).
   - This directly conflicts with the Verification Resources required in `ORIGINAL_REQUEST.md`.

---

## 2. Logic Chain

1. **Premise 1**: Requirements R1 and R2 require a unified, cohesive design system across all views (`stone-950` dark mode, `stone-900`/`800` surfaces, `stone-100`/`300` typography, `amber-400`/`500` accents, `font-serif`/`mono`/`sans`).
2. **Inference from Observation 1.1 & 1.2**: Because there is no `base.html`, styles and assets have diverged. `site.html` maintained 1,057 lines of legacy CSS with conflicting color variables and sans-serif typography, whereas `portal.html`, `ide.html`, and `analytics.html` adopted Tailwind classes.
3. **Inference from Observation 1.1 & 1.4**: Requirement R1 explicitly specifies `reader.html` with a 3-lens toggle, takeaway cards, and footnote tooltips. Because the backend is bound to `portal.html` which lacks lens toggles, takeaway card styling, and tooltips, the reader experience is incomplete.
4. **Inference from Observation 1.3**: Requirement R1 defines `/ide` as a "3-Pane Epistemic IDE including file explorer, split Markdown editor, and OKF v0.2 Evidence Card live drawer." The current implementation provides an audit runner and TTS streaming console, but does not provide file exploration or Markdown editing capabilities.
5. **Inference from Observation 1.7 & 1.8**: WCAG 2.1 AA and requirement R3 mandate `>= 44px` interactive touch targets and `>= 4.5:1` contrast ratios. The presence of 36px navigation tabs, 20–30px buttons, and `stone-500` microcopy directly violates R3 and must be remedied by replacing height/padding utility classes and elevating text colors to `stone-400`.
6. **Inference from Observation 1.9**: Destroying the feedback form on submit via `hx-swap="outerHTML"` and rendering unconstrained SVG containers causes layout shifts and limits interaction. Shifting to `hx-swap="innerHTML"` on a dedicated response container preserves form reusability.
7. **Inference from Observation 1.10**: Without a dedicated `test_bwe_views.py` suite exercising `/site`, `/ide`, and `/read/{series}/{chapter}`, regressions in template rendering cannot be prevented during frontend refactoring.

---

## 3. Caveats

1. **Read-Only Scope**: This investigation was strictly analytical; no source code or templates were modified.
2. **Audio File Availability**: Local audio playback depends on generated `.mp3` or `.wav` files in `series/**/audiobook/` or `.cache/tts_pcm/`. When absent, the audio player gracefully displays "Queued" or plays the online stream for Chapter 1.
3. **Tailwind Processing**: Currently, templates use the CDN script `https://cdn.tailwindcss.com`. A localized, compiled Tailwind CSS build in `bwe/static/` would eliminate external script latency and JIT compilation overhead, but requires Node.js tooling or standalone Tailwind CLI.

---

## 4. Conclusion & Recommendations

The frontend templates are functional in isolation but suffer from architectural fragmentation, legacy styling remnants, missing feature components (brief drawer, 3-lens toggle, split editor), and touch-target accessibility defects.

### Concrete Recommendations for Implementation:

1. **Implement `bwe/templates/base.html`**:
   - Centralize `<!DOCTYPE html>`, `<head>`, meta tags, theme colors, KaTeX, HTMX, Alpine.js, and Tailwind configuration.
   - Inject `partials/nav.html` at the top of the body block.
   - Refactor `site.html`, `ide.html`, `reader.html` (formerly `portal.html`), and `analytics.html` to extend `base.html` (`{% extends "base.html" %}`).
2. **Refactor `/site` (`site.html`) to Pure Tailwind**:
   - Strip the 1,057 lines of inline `<style>` and rewrite the catalog sidebar, hero section, playlist cards, and player dock using Tailwind utility classes matching `stone-950` / `stone-900` / `stone-800` / `amber-400`.
   - Add an interactive **Public Evidence Brief Drawer**: An HTMX/Alpine modal or slide-over drawer that loads briefs from `series/parenthood-atlas/publishing/evidence-briefs/`.
3. **Restructure `/ide` (`ide.html`) into True 3-Pane Epistemic IDE**:
   - **Pane 1 (File Explorer)**: Navigable tree of series, books, chapters, and evidence cards.
   - **Pane 2 (Split Markdown Editor)**: Markdown textarea with live rendered preview, highlighting calibrated verbs and checking forbidden phrases.
   - **Pane 3 (OKF v0.2 Drawer / Tools)**: Tabbed drawer combining FTS5 card inspection, Audit Gate execution, and TTS SSE streaming.
4. **Upgrade Serial Reader to `reader.html`**:
   - Rename/alias `portal.html` to `reader.html` and update `bwe/main.py:216`.
   - **3-Lens Toggle**: Add an Alpine.js/HTMX toggle bar (`Science | Interpretation | Art`) that highlights or tags corresponding sections in the text.
   - **Takeaway Card Styling**: Add polished Tailwind styling for `<aside class="chapter-takeaway">` with amber accent borders and callout badges.
   - **Footnote Tooltips**: Add inline hover/focus popovers using CSS/Alpine for instant footnote preview, retaining the side drawer for full inspection.
5. **Enforce 44px Touch Targets & WCAG AA Contrast**:
   - Apply `min-h-[44px] min-w-[44px]` to all navigation links, buttons, select dropdowns, search inputs, and close/dismiss icons.
   - Replace `text-stone-500` microcopy with `text-stone-400`.
   - Replace `text-red-400` / `bg-red-500` with `text-rose-400` / `bg-rose-500`.
6. **Create Integration Test Suite**:
   - Create `tests/test_bwe_views.py` testing FastAPI `TestClient` responses (HTTP 200) and DOM assertions across `/site/`, `/ide`, `/read/parenthood-atlas/01-before-the-child-is-born`, and `/analytics`.

---

## 5. Verification Method

To verify these findings independently or validate the future implementation:

1. **Automated Endpoint Testing**:
   ```powershell
   python -m pytest tests/test_analytics.py
   ```
   Verify 8/8 tests pass. Once `tests/test_bwe_views.py` is created, run:
   ```powershell
   python -m pytest tests/
   ```
2. **Template File Inspection**:
   - Verify `bwe/templates/base.html` and `bwe/templates/reader.html` exist.
   - Verify `bwe/main.py:216` references `reader.html`.
   - Verify absence of inline `<style>` blocks exceeding 50 lines in `site.html`.
3. **Static Touch Target Audit**:
   - Search for interactive element classes across templates:
     ```powershell
     Select-String -Path bwe/templates/*.html, bwe/templates/partials/*.html -Pattern 'min-h-\[(3[0-9]|40|42)px\]'
     ```
   - Target condition: Zero matches under 44px; all controls have `min-h-[44px]` or `h-11` (44px).
4. **Static Color Token Audit**:
   - Verify no occurrences of raw red utility classes:
     ```powershell
     Select-String -Path bwe/templates/*.html, bwe/templates/partials/*.html -Pattern 'text-red-|bg-red-'
     ```
   - Target condition: Zero matches; all alert states use `text-rose-` / `bg-rose-`.
