# Progress — explorer_mobile_survey_1

Last visited: 2026-11-05T12:02:15Z

## Status
- [x] Read dispatch message and initialized DISPATCH.md, BRIEFING.md, progress.md
- [x] Read ORIGINAL_REQUEST.md
- [x] Inspected bwe/templates/base.html and bwe/templates/partials/nav.html
- [x] Inspected bwe/templates/site.html and master audio player
- [x] Inspected bwe/templates/ide.html
- [x] Inspected bwe/templates/reader.html and portal.html
- [x] Inspected bwe/templates/analytics.html and partials/analytics_dashboard.html
- [x] Inspected bwe/templates/partials/brief_drawer.html and static assets
- [ ] Synthesize mobile overflow triggers and design concrete responsive fixes
- [ ] Write handoff.md and send_message to parent

## Identified Vulnerabilities Summary
1. `nav.html`:
   - Central tabs `<nav role="tablist">` with `overflow-x-auto justify-center` causes left overflow clipping on 320px–375px; 4 tabs with 44px min-size and px-3.5 require ~382px width.
   - Mobile nav drawer line 143: `<span>Epistemic Method:</span>` + `<span>Science → Interpretation → Art</span>` in monospace requires ~393px with padding and lacks wrapping/truncation, blowing out 320px–375px screens.
   - Header brand badge + hamburger toggle are constrained with `shrink-0` on 320px screens.
2. `site.html`:
   - Line 103 Hero Audio Source controls: `<div class="shrink-0 flex sm:flex-col ...">` defaults to `flex-row` on mobile, taking ~315px width inside `p-6` on 320px–375px screens (available width 240px–280px), causing severe horizontal blowout.
   - Line 276 Footnote drawer: `<aside id="site-footnote-drawer" class="hidden fixed bottom-28 right-6 max-w-md w-full">` lacks `left-4 right-4` or proper mobile inset constraints, hanging off-screen.
   - Persistent master player (`#master-audio-player`):
     - Scrubber time spans (`w-12 text-right shrink-0` + `w-12 text-left shrink-0`) + scrubber area.
     - Controls row (lines 318–365): 4 buttons side-by-side (`↺ 15s`, `▶`, `15s ↻`, speed select) require ~218px width in `shrink-0`. On 320px screen (available width 288px), track title/subtitle is squeezed to < 54px or clips controls.
3. `ide.html`:
   - Line 347 Verb Calibration banner: `<div class="flex items-center gap-3">` contains 4 unwrapped spans requiring ~486px width without `flex-wrap`, causing horizontal overflow across ALL mobile viewports (320px–428px).
   - Line 627 TTS fallback chain: unwrapped 82-character monospace string (`2.5-pro-preview-tts → ...`) without `break-all`/`break-words`.
   - Line 721 Context Pack node inspector: unconstrained `nodeId` string without truncation or word-break.
4. `reader.html` & `portal.html`:
   - Line 199 Sticky Mini Player: `sticky top-14` assumes a 56px desktop header; on mobile the 2-row navbar is ~108px high, so the sticky player scrolls under the navbar.
   - Line 199 Mini Player controls: `flex-1 min-w-[180px]` + `min-w-[44px]` play button + `min-w-[44px]` speed select + `p-3` requires 337px, overflowing/wrapping awkwardly on 320px screens.
   - Line 379 Footnote tooltip: fixed `const tooltipWidth = 320;` + `left = 16px` = 336px width, overflowing 320px viewport.
5. `analytics_dashboard.html`:
   - Lines 82, 104, 128: Card headers (`flex items-center justify-between`) lack `flex-col sm:flex-row` or `flex-wrap`, causing title + download buttons to collide on mobile.
   - Line 161: KDP action buttons (`Amazon Ads CSV` + `Write series.yaml`) in `shrink-0 flex items-center gap-2.5` take ~330px width without wrapping on 320px–360px screens.
   - Main content containers lack `min-w-0` to protect against wide table/graph expansion.
6. `base.html`:
   - `body` and `main` lack `min-w-0` and `overflow-x-clip`/`overflow-x-hidden`.
