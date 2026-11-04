---
name: evidence-card-pass
description: Creates, audits, and promotes Open Knowledge Format (OKF v0.3) Evidence Cards across Architectures of Memory and Parenthood: The Atlas using academic-bib MCP, five_rule_check.py, and Rule 7f/7g graph parity. Use when the user asks to create an evidence card, audit evidence cards, run the five-rule check, or promote cards from draft to stable.
---

# OKF v0.3 Evidence Card Workflow (`evidence-card-pass`)

Use this skill when creating, auditing, or promoting atomic `evidence-cards/*.md` in `series/architectures-of-memory/book-*/evidence-cards/` or `series/parenthood-atlas/evidence-cards/`.

## 1. Authoring or Updating an OKF v0.3 Evidence Card
1. Copy [`templates/evidence-card-template.md`](../../../templates/evidence-card-template.md) (or volume `_TEMPLATE.md`) into `evidence-cards/<slug>.md`.
2. Configure OKF v0.3 front-matter:
   - `okf_version: "0.3"`
   - `attenuation_tier: "formal_proof" | "robust_<20%" | "partially_confounded_20_50%" | "largely_confounded_>50%"`
   - `quantitative_anchors:` $\ge 2$ verified numerical figures or empirical constants.
   - `relates_to_cards:` 100% typed semantic prefixes (`EXTENDS:`, `BOUNDS:`, `CONTRASTS:`, `MITIGATES:`, `BRIDGES_LENS:`). Zero untyped card slugs allowed.
3. Verify all primary sources through **`academic-bib` MCP** (`crossref_lookup`, `arxiv_search`, `openalex_work`) and persist them via `add_bibtex_entry` to `sources.bib`.
4. Synchronize `SOURCES.md` and `sources.bib` across the monorepo:
   ```bash
   python scripts/sync_okf_sources.py
   ```
5. Complete all 9 required H2 sections (`What We Know`, `How Confident We Are`, `Evidence and Causal Assessment`, `Effect Size and Persistence`, `Bias, Heterogeneity, and Confounding`, `What Remains Uncertain`, `What This Does Not Mean`, `What Action Is Reasonably Justified`, `Sources`).
6. Ensure the tokens in `**Grade**:` match YAML `certainty_grade` / `confidence:` and that `## What This Does Not Mean` is substantive (>40 chars).

## 2. Running Mechanical Verification & Graph Parity Gates
Run [`scripts/five_rule_check.py`](../../../scripts/five_rule_check.py) with `--online-retraction-check`:
```bash
python scripts/five_rule_check.py <card-or-book-dir> --online-retraction-check
python scripts/audit_manuscript.py <book-dir> --strict --graph-strict
```
- Confirm Rules 1–5 pass before proposing `status: stable`.
- Confirm Rule 7f (quantitative anchors $\ge 2$, valid attenuation tier, typed edges) and Rule 7g (zero orphaned cards, 100% EN/ES citation parity) pass with 0 errors.
