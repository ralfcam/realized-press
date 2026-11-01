---
name: chapter-draft
description: >-
  Drafts or curates a chapter from OKF v0.3 Chapter Context Packs (CCPs), research notes,
  and evidence cards using series voice and three-lens structure. Use when the user asks to
  draft, write, compose, or expand a chapter in Architectures of Memory or Parenthood: The Atlas.
---

# Chapter Draft (Multi-Series Three-Lens & OKF v0.3 Graph RAG)

## Prerequisites

- Matching OKF v0.2 / v0.3 `evidence-cards/*.md` and `research/notes/chNN-*.md` (or `preliminary/triage/chNN-*.md`) exist for the chapter.
- Linear **`draft`** issue under Team **ARC** (`Architectures of Memory — Series` `P-ARC-8` or `Parenthood: The Atlas — Series` `P-ARC-17`).

## Steps

1. **Compile Chapter Context Pack (Graph RAG Engine, OKF v0.3):**
   Run the CLI command to emit the ~1,800-token Chapter Context Pack (CCP):
   ```bash
   python -m bwe.cli context --series <series-slug> [--book <book-slug>] --chapter <chapter-slug>
   ```
   Examine the generated 6-section pack:
   - **Active Epistemic Ledger:** Exact certainty grades and allowed claim verbs for cited cards.
   - **Narrative Handoff Vectors:** Previous chapter's closing scene/takeaway anchor and following chapter's opening hook.
   - **Progressive Lens Escalation Protocol:** Directives for cards appearing for the 2nd or 3rd+ time across the book.
   - **Split-Register Metaphor Ledger:** Canonical plain-English metaphors to use in body prose (keeping clinical/math jargon in `## Notes`).
   - **Character Continuity State:** Historical figures, intro status, and guidance against redundant biographical boilerplate.
   - **Demand & PAA Targets:** High-intent search queries and questions to weave organically into narrative movements.
2. Read [`COMPOSITION.md`](../../../COMPOSITION.md), [`style/forbidden-phrases.md`](../../../style/forbidden-phrases.md), [`style/voice-checklist.md`](../../../style/voice-checklist.md), and the series-specific bible:
   - **Series 1:** [`series/architectures-of-memory/series-bible.md`](../../../series/architectures-of-memory/series-bible.md), [`series/architectures-of-memory/characters.md`](../../../series/architectures-of-memory/characters.md), and `outline.md`.
   - **Series 2:** [`series/parenthood-atlas/COMPOSITION.md`](../../../series/parenthood-atlas/COMPOSITION.md), [`series/parenthood-atlas/chapters/_OUTLINE.md`](../../../series/parenthood-atlas/chapters/_OUTLINE.md), and [`series/parenthood-atlas/style/anomaly-bank.md`](../../../series/parenthood-atlas/style/anomaly-bank.md).
3. Create or update `<book-dir>/chapters/NN-slug.md` (two-digit `NN`, kebab-case `slug`).
4. **Three-Lens Structure:**
   - **Series 1 (*Architectures of Memory*):** **Technical** $\to$ **Organizational** $\to$ **Philosophical**.
   - **Series 2 (*Parenthood: The Atlas*):** **Science** $\to$ **Interpretation** $\to$ **Art**.
5. **Grade-Calibrated Verbs & Citations:**
   - Calibrate claim verbs to the underlying OKF v0.3 Evidence Card grade (*High* $\to$ **shows**; *Moderate* $\to$ **suggests**; *Low* $\to$ **is associated with**).
   - Trace every claim to `sources.bib` / `SOURCES.md` and `evidence-cards/*.md`.
6. **Audit Gate:** Run `python scripts/audit_manuscript.py <book-dir> --strict --graph-strict` and `python scripts/five_rule_check.py <book-dir>` before opening a PR.
