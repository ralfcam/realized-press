# Task Assignment: Milestone 4D — Analytics Studio & Dashboard Polish

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4d_analytics\`

## Mission
Refactor `bwe/templates/analytics.html` and `bwe/templates/partials/analytics_dashboard.html` to eliminate all touch target, WCAG contrast, and layout shift defects:
1. `bwe/templates/analytics.html`:
   - Extend `base.html` (`{% extends "base.html" %}`).
   - Series switcher tabs: replace 36px/38px buttons with full 44px buttons (`min-h-[44px] px-4 py-2.5 rounded-lg text-xs font-mono font-medium`).
   - Header action links: replace ~32px links with 44px buttons/links (`min-h-[44px] px-3.5 inline-flex items-center gap-2`).
   - `#analytics-content`: set a responsive `min-h-[600px]` container to prevent cumulative layout shift (CLS) during HTMX series switches.
   - Clean up footer text: replace `text-stone-500` with `text-stone-400`.
2. `bwe/templates/partials/analytics_dashboard.html`:
   - Enforce 44px touch targets on ALL controls:
     - Chart SVG / PNG download links: change from `py-1` to `min-h-[44px] min-w-[44px] inline-flex items-center justify-center px-3 rounded-lg border border-stone-800 bg-stone-900 text-xs font-mono text-stone-300 hover:text-amber-400`.
     - Action buttons (Amazon Ads CSV export, Write KDP YAML): change from `py-1.5` to `min-h-[44px] px-4 inline-flex items-center gap-2 rounded-lg font-mono text-xs`.
     - KDP 7-box copy button: change from `px-2 py-0.5` (~20px) to `min-h-[44px] min-w-[44px] inline-flex items-center justify-center rounded-lg border border-stone-800 bg-stone-900 text-xs font-mono text-stone-300 hover:text-amber-400`.
     - Table search input & filter selects: change from `py-1.5` (~32px) to `min-h-[44px] px-3 rounded-lg`.
   - WCAG 2.1 AA Color Contrast Remediation:
     - Replace ALL occurrences of `text-stone-500` with `text-stone-400` (lines 13, 23, 33, 42, 52, 62, 72, 176, etc.).
   - Palette Tokens Remediation:
     - Replace `text-red-400` with `text-rose-400` (line 164).
     - Replace `bg-red-500` with `bg-rose-500` (line 169).
   - Ensure `partials/telemetry_table.html` also replaces any `text-stone-500` with `text-stone-400`.
3. Verification:
   - Run `python -m pytest tests/test_bwe_views.py -k test_analytics_view` and `python -m pytest tests/test_ui_compliance.py`.
   - Run with strict gate: `$env:STRICT_UI_GATE="1"; python -m pytest tests/test_ui_compliance.py` (or Python equivalent).
   - Confirm ZERO violations across all templates!

## File Ownership
You own exclusively:
- `bwe/templates/analytics.html`
- `bwe/templates/partials/analytics_dashboard.html`
- `bwe/templates/partials/telemetry_table.html`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Write your report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4d_analytics\handoff.md`
Report back when finished.


## 2026-10-31T11:48:55Z
[Message] timestamp=2026-10-31T11:48:55Z sender=f4876ee9-0d9f-4458-901c-f2a09823d438 priority=MESSAGE_PRIORITY_HIGH content=You are Worker M4D (Analytics Studio & Dashboard Polish) for Realized Press BWE.
Your working directory is: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4d_analytics\
Scope and File Ownership:
- bwe/templates/analytics.html
- bwe/templates/partials/analytics_dashboard.html
- bwe/templates/partials/telemetry_table.html
