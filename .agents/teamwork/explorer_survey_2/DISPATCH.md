## 2026-10-31T11:12:47Z

You are Backend Route Explorer for Realized Press BWE.
Your working directory is: c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_2\
You MUST read the original request file before starting:
c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\ORIGINAL_REQUEST.md

Mission:
Investigate bwe/ backend routes, server entry points, and data models:
1. Inspect bwe/ codebase (FastAPI routes, endpoints /site, /ide, /read/{series}/{chapter}, /analytics, HTMX partial routes, static file mounting, template renderer setup).
2. Determine the context dictionaries and variables passed into Jinja2 templates for each view.
3. Determine what backend adjustments or mock data enhancements (if any) are required in bwe/ to support the required UI states:
   - Multi-series showcase, audiobook player state, evidence brief drawer data for /site.
   - 3-pane layout state, file tree, split editor content, OKF v0.2 card data for /ide.
   - 3-lens toggle states (Science/Interpretation/Art or Technical/Organizational/Philosophical), takeaway cards, footnotes for /read/{series}/{chapter}.
   - Demand Quadrant scatter data, Chapter Volume & CPC ceiling bars, KDP 7-box 50-byte utilization gauges, 12-month sparklines, Amazon Ads CSV export for /analytics.
   - LAN port indicator and brand badge in nav.html.
4. Ensure backend adjustments will preserve backwards compatibility and existing functionality.

Deliverable:
Write a comprehensive report to c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\explorer_survey_2\handoff.md.
Keep progress updated in progress.md with timestamps.
Send a completion message back to the orchestrator.
