---
name: evidence-card-pass
description: Creates, audits, and promotes Open Knowledge Format (OKF v0.2) Evidence Cards across Architectures of Memory and Parenthood: The Atlas using academic-bib MCP and five_rule_check.py. Use when the user asks to create an evidence card, audit evidence cards, run the five-rule check, or promote cards from draft to stable.
---

# OKF v0.2 Evidence Card Workflow (`evidence-card-pass`)

Use this skill when creating, auditing, or promoting atomic `evidence-cards/*.md` in `series/architectures-of-memory/book-*/evidence-cards/` or `series/parenthood-atlas/evidence-cards/`.

## 1. Authoring or Updating an Evidence Card
1. Copy [`templates/evidence-card-template.md`](../../../templates/evidence-card-template.md) into the target `evidence-cards/<slug>.md`.
2. Verify all primary sources through **`academic-bib` MCP** (`crossref_lookup`, `arxiv_search`, `openalex_work`) and persist them via `add_bibtex_entry` to `sources.bib`.
3. Synchronize `SOURCES.md` and `sources.bib` across the monorepo:
   ```bash
   python scripts/sync_okf_sources.py
   ```
4. Complete all 9 required H2 sections (`What We Know`, `How Confident We Are`, `Evidence and Causal Assessment`, `Effect Size and Persistence`, `Bias, Heterogeneity, and Confounding`, `What Remains Uncertain`, `What This Does Not Mean`, `What Action Is Reasonably Justified`, `Sources`).
5. Ensure the tokens in `**Grade**:` match YAML `confidence:` and that `## What This Does Not Mean` is substantive (>40 chars).

## 2. Running the Mechanical Five-Rule Gate (with Live Retraction Audit)
Run [`scripts/five_rule_check.py`](../../../scripts/five_rule_check.py) with `--online-retraction-check`:
```bash
python scripts/five_rule_check.py <card-or-book-dir> --online-retraction-check
```
- Confirm Rules 1, 2 (Crossref `updates_or_errata` + OpenAlex `is_retracted`), 3, 4, and 5 pass before proposing `status: stable`.
