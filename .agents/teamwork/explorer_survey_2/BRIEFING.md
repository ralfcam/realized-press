# BRIEFING — 2026-10-31T11:19:00Z

## Mission
Investigate bwe/ backend routes, server entry points, and data models for Realized Press BWE UI states and enhancements.

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend Route Explorer, Investigator, Synthesizer
- Working directory: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_2
- Original parent: f4876ee9-0d9f-4458-901c-f2a09823d438
- Milestone: BWE Backend Routes & Data Models Survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Inspect bwe/ backend routes, server entry points, and data models
- Deliverable in handoff.md, progress updates in progress.md

## Current Parent
- Conversation ID: f4876ee9-0d9f-4458-901c-f2a09823d438
- Updated: 2026-10-31T11:13:00Z

## Investigation State
- **Explored paths**: `ORIGINAL_REQUEST.md`, `bwe/main.py`, `bwe/analytics.py`, `bwe/schema.py`, `bwe/db.py`, `bwe/cli.py`, `bwe/templates/` (`site.html`, `ide.html`, `portal.html`, `analytics.html`, `partials/*`), `scripts/render_audiobook_player.py`, `scripts/render_evidence_briefs.py`, `tests/`.
- **Key findings**:
  1. `/site/` serves `site.html` with `catalog` and `catalog_json` covering 6 books across 2 series; needs explicit `evidence_briefs` data and `/hx/brief/{series}/{card}` endpoint for public evidence brief drawer.
  2. `/ide` serves `ide.html` with FTS5 cards, audit runner, and SSE TTS streaming; lacks dynamic file tree and split editor content.
  3. `/read/{series}/{chapter}` renders `portal.html` (named `reader.html` in request); lacks dynamic 3-lens toggle context (`lenses`, `epistemic_contract`), takeaway cards, and inline tooltip data.
  4. `/analytics` already computes Demand Quadrant scatter, Chapter Volume & CPC bars, KDP 7-box 50-byte utilization gauges, 12-month sparklines, and Amazon Ads CSV export via `bwe/analytics.py`.
  5. `partials/nav.html` has hardcoded "LAN 8080" and "Science → Interpretation → Art"; needs dynamic server port/host and series lens context.
  6. All 36 pytest tests pass; all 4 main views return HTTP 200 with `TestClient`.
- **Unexplored areas**: None (investigation complete).

## Key Decisions Made
- Formulated exact context dictionary mappings and backwards-compatible backend enhancements for all 5 requested UI areas.

## Artifact Index
- DISPATCH.md — Initial dispatch message
- BRIEFING.md — Persistent working memory
- progress.md — Liveness heartbeat and progress tracking
- handoff.md — Comprehensive 5-component handoff report
