## 2026-10-31T11:48:43Z

# Task Assignment: Milestone 4C — Serial Reader with 3-Lens Toggle & Takeaways

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4c_reader\`

## Mission
Author `bwe/templates/reader.html` and polish `bwe/templates/portal.html` to establish the refined serial reading experience:
1. `bwe/templates/reader.html`:
   - Extend `base.html` (`{% extends "base.html" %}`).
   - Refined Typography (R2):
     - Article container `#reader-content` with `font-serif leading-relaxed text-stone-100 max-w-3xl mx-auto`.
     - Movement subheadings (`## I. ...` etc.) with amber numbering and literary styling.
     - KaTeX inline math equations cleanly rendered.
   - 3-Lens Toggle:
     - Prominent epistemic control bar (`#lens-toggle` or `data-lens-toggle`) presenting the series lenses (`{{ lenses }}`: Science / Interpretation / Art, or Technical / Organizational / Philosophical).
     - Buttons with `min-h-[44px] px-4 py-2 rounded-lg font-mono text-xs font-semibold` allowing instant lens switching or visual emphasis.
   - Styled Takeaway Cards:
     - Styling for `<aside class="chapter-takeaway">` blocks: callout cards with `bg-stone-900/90 border border-amber-500/30 rounded-xl p-6 my-8`, epistemic badges (`bg-amber-500/10 text-amber-400 font-mono text-xs`), and structured 3-tier causal resolution bullets.
   - Footnote Tooltips & Slide Drawer:
     - Footnote references (`a.footnote-ref`): inline hover/focus preview popover using Alpine.js or CSS tooltips for instantaneous reading without losing position.
     - Persistent `#footnote-drawer` for deep citation inspection, telemetry logging (`/hx/footnote/...`), and citation detail view.
     - Close button with strict `min-h-[44px] min-w-[44px]` touch target and `aria-label="Close footnote drawer"`.
   - Chapter Audio Mini-Player:
     - Scrubber, play/pause, time display, and speed control with ALL controls meeting >= 44px (`min-h-[44px] min-w-[44px]`).
   - Paragraph Feedback Form:
     - Form submitting via HTMX `hx-post="/hx/feedback"` into a response container (`hx-target="#feedback-status" hx-swap="innerHTML"`) without destroying the form inputs.
     - Dropdowns and inputs with `min-h-[44px]`.
   - Strict Standards:
     - ZERO elements under 44px (`min-h-[44px] min-w-[44px]`).
     - ZERO `text-stone-500` or `text-stone-600` tokens.
     - ZERO `red-` tokens.
2. Synchronize `portal.html` with `reader.html` to guarantee identical functionality if loaded as fallback.
3. Update `bwe/templates/partials/footnote_drawer.html` to ensure close button has `min-h-[44px] min-w-[44px]` and valid contrast.
4. Verification:
   - Run `python -m pytest tests/test_bwe_views.py -k test_reader_view` and `python -m pytest tests/test_ui_compliance.py`.
   - Confirm 0 violations for `reader.html`, `portal.html`, and `partials/footnote_drawer.html`.

## File Ownership
You own exclusively:
- `bwe/templates/reader.html`
- `bwe/templates/portal.html`
- `bwe/templates/partials/footnote_drawer.html`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Write your report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4c_reader\handoff.md`
Report back when finished.
