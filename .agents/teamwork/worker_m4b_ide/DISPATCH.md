# Task Assignment: Milestone 4B — 3-Pane Epistemic IDE

## Working Directory
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4b_ide\`

## Mission
Refactor `bwe/templates/ide.html` into a true 3-Pane Epistemic IDE:
1. `bwe/templates/ide.html`:
   - Extend `base.html` (`{% extends "base.html" %}`).
   - Implement the 3-Pane layout:
     - **Pane 1: File Explorer (`#file-explorer`)**:
       - Displays navigable tree from `file_tree` context: Series (Parenthood, Architectures of Memory) -> Books -> Chapters & Evidence Cards.
       - File tree links trigger `hx-get="/ide/file-content?path=..." hx-target="#editor-container"` with 44px touch targets (`min-h-[44px]`).
     - **Pane 2: Split Markdown Editor (`#editor-container`)**:
       - Left: Markdown editor pane (`<textarea id="markdown-editor">`) with line numbers and calibrated verb guidelines.
       - Right: Live preview pane (`<div id="markdown-preview" class="prose prose-invert max-w-none">`).
       - Header bar with file path indicator, word count counter, and copy/action buttons meeting 44px touch targets.
     - **Pane 3: OKF v0.2 Live Drawer & Tool Bench**:
       - Tabbed interface (or collapsible accordion) combining:
         1. FTS5 Evidence Card Search: search input (`input[name="q"]`) with `min-h-[44px]`, card result cards with `min-h-[44px]` copy buttons (`[^card_slug]`), certainty grade badges, snippet text in `text-stone-300`/`text-stone-400`.
         2. Epistemic Audit Gate Runner: form (`form[hx-post="/ide/audit"]`), selects (`#gate-script`, `#target-path`) with `min-h-[44px]`, submit button with `min-h-[44px]`, results container (`#audit-output`).
         3. TTS Stream Synthesis: series/chapter selects with `min-h-[44px]`, stream button with `min-h-[44px]`, live terminal output (`#tts-terminal`).
   - Touch Target & Contrast Standards:
     - STRICT 44px touch targets on ALL inputs, selects, buttons, and links (`min-h-[44px] min-w-[44px]`).
     - ZERO `text-stone-500` or `text-stone-600` tokens (use `text-stone-400` or `text-stone-300`).
     - ZERO `red-` tokens (use `rose-400` / `rose-500`).
2. Verification:
   - Run `python -m pytest tests/test_bwe_views.py -k test_ide_view` and `python -m pytest tests/test_ui_compliance.py`.
   - Confirm 0 violations for `ide.html`.

## File Ownership
You own exclusively:
- `bwe/templates/ide.html`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverable
Write your report to:
`c:\Users\joser\PycharmProjects\realized-press\.agents\teamwork\worker_m4b_ide\handoff.md`
Report back when finished.
