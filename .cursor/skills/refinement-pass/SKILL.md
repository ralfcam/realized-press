---
name: refinement-pass
description: Runs an iterative book refinement and BWE harness-hardening pass across chapters, OKF v0.2 evidence cards, marketing intelligence, and KDP/Reader Edition outputs. Use during Stage 1 (Parenthood: The Atlas) and Stage 2 (Architectures of Memory) refinement loops.
---

# Iterative Refinement & Harness-Hardening Pass (`refinement-pass`)

Executes one complete **Book Development Lifecycle (BDLC)** refinement and harness-hardening iteration in accordance with the **Master 4-Stage Execution Sequence**:
- **Stage 1 (Immediate Goal):** `series/parenthood-atlas` ([`P-ARC-17`](https://linear.app/realized/project/parenthood-the-atlas-series-e3ae54ac870d/overview))
- **Stage 2:** `series/architectures-of-memory/book-01..05-*` ([`P-ARC-8`](https://linear.app/realized/project/architectures-of-memory-series-e798843bf9fb/overview))

## 5-Step Refinement Loop

1. **Step 1 — Mechanical Diagnostics & Baseline Snapshot:**
   - Run the OKF v0.2 Five-Rule Gate, Manuscript Auditor, and Marketing Intelligence Scorecard on the target book/series:
     ```bash
     python scripts/five_rule_check.py <book-dir> --online-retraction-check
     python scripts/audit_manuscript.py <book-dir> --strict
     python scripts/marketing_intelligence.py --series <series-slug>
     ```
2. **Step 2 — Epistemic & Confounding Refinement (`evidence-cards/*.md` & `sources.bib`):**
   - Follow the **5-Step Definitive Tool Routing Protocol** (`perplexity_research` / `perplexity_reason` $\to$ `context7` $\to$ `academic-bib` `crossref_lookup`/`openalex_work`/`add_bibtex_entry` $\to$ `scripts/sync_okf_sources.py`).
   - Verify genetically-informed (GI) cohort attenuation (`largely confounded (>50%)`, `partially confounded (20–50%)`, `robust (<20%)`, `untested-in-GI`), narrowest exact claim wording, and `## What This Does Not Mean` scope boundaries.
3. **Step 3 — Three-Lens Prose & Grade-to-Verb Calibration (`chapters/*.md`):**
   - Ensure each chapter opens with a concrete **Anomaly / Lived Tension**, transitions cleanly across the series' **Three Lenses** (`Science -> Interpretation -> Art` or `Technical -> Organizational -> Philosophical`), and calibrates verbs to OKF certainty grades (*High* $\to$ **shows**; *Moderate* $\to$ **suggests**; *Low* $\to$ **is associated with**).
   - Eliminate any phrase in [`style/forbidden-phrases.md`](../../../style/forbidden-phrases.md).
4. **Step 4 — Commercial & Serial Compilation Verification:**
   - Re-compile both the **Patreon-Blueprint Reader Edition (A4 PDF + HTML)** and the **Amazon KDP Release Package (6"×9" Mirrored-Margin Print PDF + Kindle EPUB 3)**:
     ```bash
     python scripts/render_publishing_pdfs.py <book-dir> --format a4
     python scripts/render_publishing_pdfs.py <book-dir> --format kdp-6x9 --epub
     ```
   - Verify 100% non-blank page extraction in `publishing/*-extraction-report.txt`.
5. **Step 5 — Harness Reflection & Hardening (Mandatory in Stage 1):**
   - If the pass exposed any false positive, missed pattern, typography edge case, or schema gap in `scripts/*.py`, `.agents/hooks/post_edit_guard.py`, or `style/*.md`, **upgrade the harness script/rule immediately in the same commit** so Stage 2 (*Architectures of Memory*) and Stage 3 (`P-ARC-18`) inherit the hardened capability.
