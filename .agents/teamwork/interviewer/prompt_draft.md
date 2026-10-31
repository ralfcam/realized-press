Execute a comprehensive UX/UI design pass on the templates in `bwe/templates` for the Book Writing Environment and Multi-Series Nonfiction Publishing Imprint (realized-press).

Integrity mode: development

## Requirements

### R1. Core Views and Navigation Polish
Execute a comprehensive UX/UI design pass across the templates in `bwe/templates/` and `bwe/templates/partials/`:
- `/site` (`site.html`): Imprint home, multi-series showcase, audiobook player, and public evidence brief drawer.
- `/ide` (`ide.html`): 3-Pane Epistemic IDE including file explorer, split Markdown editor, and OKF v0.2 Evidence Card live drawer.
- `/read/{series}/{chapter}` (`reader.html`): Serial reader featuring refined typography, 3-lens toggle, takeaway cards, and footnote tooltips.
- `/analytics` (`analytics.html` and `partials/analytics_dashboard.html`): Demand Quadrant scatter, Chapter Volume & CPC ceiling bars, KDP 7-box 50-byte utilization gauges, filterable signal table with 12-month sparklines, and Amazon Ads CSV export.
- Layout and Navigation (`partials/nav.html`): Unified mobile-first header with 44px touch targets, ARIA tabs, LAN port indicator, and brand badge.

### R2. Design Language and Aesthetic Consistency
Anchor the interface in the specified dark mode design system:
- Background: `stone-950`
- Surfaces and borders: `stone-900` / `stone-800`
- Typography: `stone-100` / `stone-300`
- Accents: `amber-400`/`amber-500` (primary epistemic brand), `emerald-400` (live status / verified tiers), `rose-400` (confounding alerts / noise flags).
- Font stacks: `font-serif` for manuscript prose and literary titles, `font-mono` for evidence metrics, KDP byte counters, DOIs, and search volume, and `font-sans` for UI controls.

### R3. Accessibility, Interaction, and Responsiveness
Ensure responsive presentation across mobile, tablet, and desktop viewports with seamless HTMX transitions free of layout shift. Ensure interactive elements meet or exceed 44px touch target sizes and maintain WCAG 2.1 AA color contrast compliance.

### R4. Scope of Backend Adjustments
Modifications to templates and front-end assets in `bwe/templates/` may be accompanied by updates to backend FastAPI route handlers or template context in `bwe/` if necessary to support enhanced UI states or data bindings.

## Verification Resources
- Automated test suite using FastAPI `TestClient` (running `pytest`) verifying HTTP 200 responses and rendered elements across `/site`, `/ide`, `/read/{series}/{chapter}`, and `/analytics`.
- Static code inspection checking template markup and Tailwind utility classes for 44px touch targets (`min-h-[44px]`, `min-w-[44px]`) and WCAG 2.1 AA color contrast pairings.

## Acceptance Criteria

### Visual Design and Layout Consistency
- [ ] All four core views (`/site`, `/ide`, `/read/{series}/{chapter}`, `/analytics`) and `partials/nav.html` adhere to the `stone-950` dark mode palette and typography system (`font-serif`, `font-mono`, `font-sans`).
- [ ] Interactive components (drawers, 3-lens toggle, audiobook player, scatter plot, sparklines, gauges, tabs) render without visual distortion or unexpected layout shift during HTMX transitions.

### Accessibility and Usability
- [ ] Static code audit of template markup and Tailwind utility classes confirms interactive touch targets on navigation and control elements meet or exceed 44px.
- [ ] Static code audit confirms text and foreground UI elements achieve WCAG 2.1 AA color contrast ratios against their respective backgrounds.
- [ ] All views render responsively and cleanly across mobile, tablet, and desktop viewport dimensions.

### Integration and Verification
- [ ] Automated tests run via `pytest` using FastAPI `TestClient` pass and confirm endpoints (`/site`, `/ide`, `/read/{series}/{chapter}`, `/analytics`) return valid HTTP 200 responses with the updated templates and styling rendered.
- [ ] If backend routes or context in `bwe/` are modified, existing server functionality and data bindings remain intact and operational.
