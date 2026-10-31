## 2026-10-31T11:37:23Z
You are Worker M3 (Base Template & Navigation Polish) for Realized Press BWE.
Your working directory is: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m3_nav\

You MUST read the original request file before starting:
c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\ORIGINAL_REQUEST.md

Also read:
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\handoff.md
- c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\joser\PycharmProjects\realized-press\TEST_READY.md

Scope and File Ownership:
You own exclusively:
- bwe/templates/base.html
- bwe/templates/partials/nav.html

Tasks:
1. Implement `bwe/templates/base.html`:
   - Full HTML5 template structure (`<!DOCTYPE html>`, `<html lang="en" class="dark">`).
   - `<head>`: charset utf-8, viewport `width=device-width, initial-scale=1.0, maximum-scale=5.0`, meta description, theme-color `#0c0a09`.
   - Tailwind CDN script configured with the R2 design system:
     - `stone-950` (#0c0a09) background.
     - `stone-900` (#1c1917) and `stone-800` (#292524) surfaces & borders.
     - `stone-100` (#f5f5f4), `stone-300` (#d6d3d1), and `stone-400` (#a8a29e) typography.
     - `amber-400` (#fbbf24) / `amber-500` (#f59e0b) accents.
     - `emerald-400` (#34d399) live status.
     - `rose-400` (#fb7185) / `rose-500` (#f43f5e) alert/noise accents (DO NOT use red-400/500).
     - Font stacks: `font-serif`, `font-mono`, `font-sans`.
   - KaTeX CSS and auto-render JS.
   - HTMX 2.0.4 and Alpine.js 3.14.8 scripts.
   - Body with `bg-stone-950 text-stone-100 min-h-screen flex flex-col font-sans`.
   - Injects `{% include "partials/nav.html" %}`.
   - Main content block `{% block content %}{% endblock %}` with `flex-1`.
   - Scripts block `{% block scripts %}{% endblock %}`.
2. Refactor `bwe/templates/partials/nav.html`:
   - Mobile-first responsive sticky header (`sticky top-0 z-50 bg-stone-950/95 backdrop-blur border-b border-stone-800`).
   - Realized Press Brand Badge (`min-h-[44px] flex items-center gap-2.5 px-2` with `amber-500` "R" mark and `font-serif text-stone-100`).
   - Dynamic epistemic contract badge (`{{ epistemic_contract or "Science → Interpretation → Art" }}` in `text-xs font-mono text-stone-400`).
   - Central navigation tabs (`role="tablist"`):
     - Audio / Catalog (`/site/`)
     - IDE (`/ide`)
     - Reader (`/read/parenthood-atlas/01-before-the-child-is-born`)
     - Analytics (`/analytics`)
     - STRICT 44px touch targets on ALL viewports: `min-h-[44px] min-w-[44px] px-3.5 py-2 inline-flex items-center justify-center rounded-lg text-xs font-mono font-medium`.
     - Active tab highlighted in `bg-stone-800 text-amber-400 border border-amber-500/30`, inactive tabs in `text-stone-400 hover:text-stone-100 hover:bg-stone-900`.
   - System indicators:
     - LAN Port Indicator (`min-h-[44px] px-3 inline-flex items-center gap-2 rounded-lg bg-stone-900/80 border border-stone-800 text-xs font-mono text-stone-300` with pulsating `emerald-400` indicator showing `LAN {{ server_info.port if server_info and server_info.port else 8080 }}`).
     - Linear ARC link with `min-h-[44px] min-w-[44px] inline-flex items-center justify-center rounded-lg bg-stone-900 border border-stone-800 text-stone-400 hover:text-amber-400`.
   - Mobile menu / drawer toggle with `min-h-[44px] min-w-[44px]` touch target.
3. Run `python -m pytest tests/` to confirm all 46 tests pass.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliverable:
Write your report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m3_nav\handoff.md`
Report back when finished.
