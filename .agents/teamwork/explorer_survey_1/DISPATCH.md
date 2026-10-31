# Task Assignment: Explorer Survey 1 (Templates & Front-End Structure)

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\`

## Mission
Investigate all templates in `bwe/templates/` and `bwe/templates/partials/`, static assets, Tailwind setup, and frontend interactive components.
Read `c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\ORIGINAL_REQUEST.md`.

## Deliverable
Write your comprehensive findings and recommendations to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\handoff.md`
Report back when finished.

## 2026-10-31T11:12:42Z
You are Frontend UI Explorer for Realized Press BWE.
Your working directory is: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\
You MUST read the original request file before starting:
c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\ORIGINAL_REQUEST.md

Mission:
Conduct a thorough technical investigation of the templates and frontend UI assets for bwe:
1. Inspect bwe/templates/ (base.html, site.html, ide.html, reader.html, analytics.html), bwe/templates/partials/ (nav.html, analytics_dashboard.html, etc.), and any CSS/JS assets.
2. Audit current visual design against R2: dark mode design system (stone-950 background, stone-900/stone-800 surfaces/borders, stone-100/stone-300 typography, amber-400/amber-500 epistemic brand accents, emerald-400 live status/verified tiers, rose-400 confounding alerts/noise flags, and font stacks font-serif, font-mono, font-sans).
3. Audit interactive components across views:
   - /site: Imprint home, multi-series showcase, audiobook player, public evidence brief drawer.
   - /ide: 3-Pane Epistemic IDE (file explorer, split Markdown editor, OKF v0.2 Evidence Card live drawer).
   - /read/{series}/{chapter}: Serial reader (refined typography, 3-lens toggle, takeaway cards, footnote tooltips).
   - /analytics: Demand Quadrant scatter, Chapter Volume & CPC ceiling bars, KDP 7-box 50-byte utilization gauges, filterable signal table with 12-month sparklines, Amazon Ads CSV export.
   - partials/nav.html: Unified mobile-first header with 44px touch targets, ARIA tabs, LAN port indicator, brand badge.
4. Audit accessibility (R3): interactive element touch targets (>=44px, e.g. min-h-[44px], min-w-[44px]), WCAG 2.1 AA color contrast pairings, ARIA attributes, responsive layout (mobile, tablet, desktop).
5. Identify current gaps, layout shifts, HTMX integration issues, and specific code locations that need enhancement.

Deliverable:
Write a comprehensive report to c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_1\handoff.md.
Keep progress updated in progress.md with timestamps.
Send a completion message back to the orchestrator.

