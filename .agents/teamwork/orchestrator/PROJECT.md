# Project: Realized Press BWE UX/UI Design Pass

## Architecture
- **Framework**: FastAPI + Jinja2Blocks + HTMX + Alpine.js + Tailwind CSS.
- **Design System**: Dark mode (`stone-950` background, `stone-900`/`stone-800` surfaces/borders, `stone-100`/`stone-300` text, `amber-400`/`amber-500` epistemic brand accents, `emerald-400` live status, `rose-400` warnings/alerts).
- **Typography Stacks**: `font-serif` for literary prose/titles, `font-mono` for metrics/bytes/DOIs, `font-sans` for controls/UI.
- **Accessibility**: 44px minimum touch targets (`min-h-[44px]`, `min-w-[44px]`), WCAG 2.1 AA color contrast compliance (≥ 4.5:1 for normal text).
- **Core Views**:
  - `/site`: Imprint Home, Multi-Series Showcase, Audiobook Player, Public Evidence Brief Drawer.
  - `/ide`: 3-Pane Epistemic IDE (File Explorer, Split Markdown Editor, OKF v0.2 Evidence Card Live Drawer).
  - `/read/{series}/{chapter}`: Serial Reader with 3-Lens Toggle, Takeaway Cards, Footnote Tooltips/Drawer.
  - `/analytics`: Demand Quadrant Scatter, Chapter Volume & CPC Ceiling Bars, KDP 7-Box 50-Byte Utilization Gauges, Signal Table with Sparklines, Amazon Ads CSV Export.
  - `partials/nav.html`: Unified Mobile-First Header with 44px Touch Targets, ARIA Tabs, LAN Port Indicator, Brand Badge.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | E2E View Integration Tests | Automated FastAPI TestClient tests for `/site`, `/ide`, `/read/...`, `/analytics` verifying HTTP 200 and rendered DOM | M1 | survey (Explorer 3) |
| 2 | UI Compliance Static Test Suite | BeautifulSoup static audit testing all interactive elements for >=44px and WCAG 2.1 AA color contrast | M1 | survey (Explorer 3) |
| 3 | Reusable Test Conftest Fixture | Session-scoped database init and client fixture in `tests/conftest.py` | M1 | survey (Explorer 3) |
| 4 | Backend Route Context Extensions | Inject `server_info`, `active_tab`, `evidence_briefs`, `file_tree`, `lenses`, `epistemic_contract`, `takeaways`, `footnotes` | M2 | survey (Explorer 2) |
| 5 | Public Evidence Brief Endpoint | `GET /hx/brief/{series_slug}/{card_slug}` rendering `partials/brief_drawer.html` | M2 | survey (Explorer 2) |
| 6 | IDE File Explorer Content Endpoint | `GET /ide/file-content` reading markdown and rendering HTML preview | M2 | survey (Explorer 2) |
| 7 | Multi-Series Dual Template Reader Route | Support `reader.html` with fallback to `portal.html` and 3-lens data bindings in `bwe/main.py` | M2 | survey (Explorer 2) |
| 8 | Shared Base Template (`base.html`) | Centralized `<head>`, KaTeX, HTMX, Alpine.js, Tailwind dark mode config, and body slot | M3 | survey (Explorer 1) |
| 9 | Mobile-First Navigation Header | Polished `partials/nav.html` with 44px touch targets, ARIA tabs, LAN port indicator, and brand badge | M3 | survey (Explorer 1) |
| 10 | Imprint Showcase & Player Refactor | Refactor `site.html` to pure Tailwind `stone-950` system, 44px touch targets, and brief drawer | M4 | survey (Explorer 1) |
| 11 | 3-Pane Epistemic IDE Implementation | Implement `ide.html` 3 panes: File Explorer, Split Editor, and OKF Live Drawer | M4 | survey (Explorer 1) |
| 12 | Serial Reader (`reader.html`) | Refined typography, 3-lens toggle, styled takeaway cards, inline footnote tooltips | M4 | survey (Explorer 1) |
| 13 | Analytics Studio Accessibility & Polish | WCAG AA contrast (`text-stone-400`), `rose-400` alerts, 44px controls, CLS elimination in `analytics.html` & `partials/analytics_dashboard.html` | M4 | survey (Explorer 1) |
| 14 | Full Test Suite Execution & Acceptance Gate | 100% pass of existing 36 tests + new view tests + UI compliance tests + multi-agent gate verification | M5 | survey (All) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | E2E Test Suite & QA Infrastructure | `tests/conftest.py`, `tests/test_bwe_views.py`, `tests/test_ui_compliance.py`, `TEST_READY.md` | none | DONE |
| M2 | Backend Routes & Data Bindings | `bwe/main.py` route handlers, context enrichment, endpoints for briefs & IDE files | M1 | DONE |
| M3 | Shared Base Template & Nav Polish | `bwe/templates/base.html`, `bwe/templates/partials/nav.html` | M1 | DONE |
| M4 | Core Views & Interactive Components | `bwe/templates/site.html`, `bwe/templates/ide.html`, `bwe/templates/reader.html`, `bwe/templates/analytics.html`, `bwe/templates/partials/analytics_dashboard.html`, `bwe/templates/partials/brief_drawer.html` | M2, M3 | DONE |
| M5 | Final Verification & Hardening | Full pytest run, static audit check, Reviewer, Challenger, and Auditor gate | M4 | DONE |

## Code Layout
- `bwe/main.py`: FastAPI server routes, context generation, and HTMX endpoints.
- `bwe/templates/base.html`: Common layout, metadata, and script inclusions.
- `bwe/templates/partials/nav.html`: Top header navigation and system badges.
- `bwe/templates/site.html`: Public imprint hub, multi-series showcase, audiobook player.
- `bwe/templates/ide.html`: 3-Pane Epistemic IDE.
- `bwe/templates/reader.html`: Chapter reader with 3-lens toggle, takeaway cards, and footnote tooltips.
- `bwe/templates/analytics.html`: Analytics host page.
- `bwe/templates/partials/analytics_dashboard.html`: Analytics dashboard partial.
- `bwe/templates/partials/brief_drawer.html`: Public Evidence Brief slide-over drawer.
- `tests/conftest.py`: Shared pytest fixtures (`client`).
- `tests/test_bwe_views.py`: View integration test suite.
- `tests/test_ui_compliance.py`: Static touch target and WCAG AA contrast test suite.
