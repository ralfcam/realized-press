# Task Assignment: Milestone 4A — Imprint Showcase, Audiobook Player & Brief Drawer

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4a_site\`

## Mission
Refactor `bwe/templates/site.html` and author `bwe/templates/partials/brief_drawer.html`:
1. `bwe/templates/site.html`:
   - Extend `base.html` (`{% extends "base.html" %}`).
   - Strip the 1000+ lines of legacy inline CSS and replace with Tailwind utilities adhering to R2:
     - Dark mode background `stone-950`, card surfaces `stone-900` / `stone-800`, borders `stone-800`, typography `stone-100`/`stone-300`/`stone-400`, epistemic accents `amber-400`/`amber-500`, verified status `emerald-400`.
     - Headings in `font-serif`.
   - Multi-series showcase displaying catalog books (Parenthood: The Atlas, Architectures of Memory volumes).
   - Master audiobook player dock with full controls, track duration, scrubber, chapter playlist, speed selector, and download links. Ensure ALL interactive elements meet >=44px touch targets (`min-h-[44px] min-w-[44px]`).
   - Public Evidence Briefs drawer container (`#brief-drawer`) and cards grid populated from `evidence_briefs` context variable, with buttons/links triggering `hx-get="/hx/brief/{series_slug}/{card_slug}" hx-target="#brief-drawer"`.
   - Ensure ZERO elements violate 44px touch targets (`min-h-[44px] min-w-[44px]`), ZERO low-contrast `text-stone-500` tokens, and ZERO `red-` tokens.
2. `bwe/templates/partials/brief_drawer.html`:
   - Interactive slide-over drawer modal (`fixed inset-0 z-50` or off-canvas panel) displaying the full OKF v0.2 evidence brief:
     - Card title in `font-serif text-stone-100`, certainty grade badge (`amber-400` or `emerald-400`), DOI link in `font-mono text-stone-400 hover:text-amber-400`.
     - 9 canonical OKF sections rendered cleanly in `stone-300`.
     - Dismiss / close button with strict `min-h-[44px] min-w-[44px]` touch target and `aria-label="Close brief drawer"`.
3. Verification:
   - Run `python -m pytest tests/test_bwe_views.py -k test_site_view` and `python -m pytest tests/test_ui_compliance.py`.
   - Confirm 0 violations for `site.html` and `partials/brief_drawer.html`.

## File Ownership
You own exclusively:
- `bwe/templates/site.html`
- `bwe/templates/partials/brief_drawer.html`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Write your report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4a_site\handoff.md`
Report back when finished.


## 2026-10-31T11:48:25Z
You are Worker M4A (Imprint Showcase, Audiobook Player & Brief Drawer) for Realized Press BWE.
Your working directory is: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4a_site\

You MUST read the original request file before starting:
c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\ORIGINAL_REQUEST.md

Also read:
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\handoff.md
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\joser\PycharmProjects\realized-press\TEST_READY.md
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4a_site\DISPATCH.md

Scope and File Ownership:
You own exclusively:
- bwe/templates/site.html
- bwe/templates/partials/brief_drawer.html
