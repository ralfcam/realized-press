---
name: chapter-draft
description: >-
  Drafts or curates a chapter from research notes and OKF v0.2 evidence cards using series
  voice and three-lens structure. Use when the user asks to draft, write, compose, or
  expand a chapter in Architectures of Memory or Parenthood: The Atlas.
---

# Chapter Draft (Multi-Series Three-Lens & OKF v0.2)

## Prerequisites

- Matching OKF v0.2 `evidence-cards/*.md` and `research/notes/chNN-*.md` (or `preliminary/triage/chNN-*.md`) exist for the chapter.
- Linear **`draft`** issue under Team **ARC** (`Architectures of Memory — Series` `P-ARC-8` or `Parenthood: The Atlas — Series` `P-ARC-17`).

## Steps

1. Read [`COMPOSITION.md`](../../../COMPOSITION.md), [`style/forbidden-phrases.md`](../../../style/forbidden-phrases.md), [`style/voice-checklist.md`](../../../style/voice-checklist.md), and the series-specific bible:
   - **Series 1:** [`series/architectures-of-memory/series-bible.md`](../../../series/architectures-of-memory/series-bible.md), [`series/architectures-of-memory/characters.md`](../../../series/architectures-of-memory/characters.md), and `outline.md`.
   - **Series 2:** [`series/parenthood-atlas/COMPOSITION.md`](../../../series/parenthood-atlas/COMPOSITION.md), [`series/parenthood-atlas/chapters/_OUTLINE.md`](../../../series/parenthood-atlas/chapters/_OUTLINE.md), and [`series/parenthood-atlas/style/anomaly-bank.md`](../../../series/parenthood-atlas/style/anomaly-bank.md).
2. Create or update `<book-dir>/chapters/NN-slug.md` (two-digit `NN`, kebab-case `slug`).
3. **Three-Lens Structure:**
   - **Series 1 (*Architectures of Memory*):** **Technical** $\to$ **Organizational** $\to$ **Philosophical**.
   - **Series 2 (*Parenthood: The Atlas*):** **Science** $\to$ **Interpretation** $\to$ **Art**.
4. **Grade-Calibrated Verbs & Citations:**
   - Calibrate claim verbs to the underlying OKF v0.2 Evidence Card grade (*High* $\to$ **shows**; *Moderate* $\to$ **suggests**; *Low* $\to$ **is associated with**).
   - Trace every claim to `sources.bib` / `SOURCES.md` and `evidence-cards/*.md`.
5. **Audit:** Run `python scripts/audit_manuscript.py <book-dir> --strict` and `python scripts/five_rule_check.py <book-dir>` before opening a PR.
