# Task Assignment: Milestone 1 — E2E Test Suite & QA Infrastructure

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m1_test\`

## Mission
Author the comprehensive automated test suite and static UI compliance inspection tests for Realized Press BWE:
1. `tests/conftest.py`:
   - Initialize session database fixture via `init_db(REPO_ROOT)` from `bwe.db`.
   - Provide standard `client` fixture using `TestClient(app)` from `bwe.main`.
2. `tests/test_bwe_views.py`:
   - `test_root_redirect`: GET `/` returns 307 -> `/site/`.
   - `test_site_view`: GET `/site/` returns 200, checks brand mark, navigation tabs, catalog/player markup, and evidence brief drawer container.
   - `test_ide_view`: GET `/ide` returns 200, checks FTS5 card search, card results, audit runner form, file explorer markup, split editor container.
   - `test_reader_view`: GET `/read/parenthood-atlas/01-before-the-child-is-born` returns 200, checks `#reader-content` article, 3-lens toggle, takeaway cards or container, and footnote integration.
   - `test_reader_view_404`: GET `/read/invalid/invalid` returns 404.
   - `test_analytics_view`: GET `/analytics?series=parenthood-atlas` returns 200, checks quadrant SVG, chapter volume bars, KDP boxes, sparklines.
   - `test_htmx_endpoints`: Test `/hx/footnote/...`, `/hx/analytics/dashboard`, `/hx/analytics/export-ads`, and `/hx/brief/...` (if present).
3. `tests/test_ui_compliance.py`:
   - `test_touch_target_sizes()`: Scan all HTML files in `bwe/templates/`. For interactive tags (`a`, `button`, `input`, `select`, `textarea`, `role="tab"`, `role="button"`), verify presence of 44px minimum touch targets (`min-h-[44px]`, `min-w-[44px]`, `h-11`, `h-12`, `min-height: 44px`).
   - `test_wcag_color_contrast()`: Ensure no low-contrast text tokens like `text-stone-500` or `text-stone-600` are used on dark backgrounds (`stone-950`/`900`/`800`), requiring `text-stone-400` or higher.
   - `test_dark_mode_palette()`: Ensure alert classes use `rose-400` rather than `red-400`/`red-500`.
4. Run `python -m pytest tests/` to confirm that existing 36 tests still pass, run view tests, and publish `TEST_READY.md`.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Write your implementation report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m1_test\handoff.md`
Report back when finished.
