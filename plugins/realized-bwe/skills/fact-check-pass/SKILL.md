---
name: fact-check-pass
description: >-
  Sweeps a chapter or evidence card for assertive claims, cross-references research notes
  and academic bibliographic databases, updates fact-check tables and OKF cards, and opens
  Linear fact-check issues for gaps. Use when the user asks to fact-check, verify citations,
  audit sources, or close citation debt.
---

# Fact-Check Pass (Definitive Tool Routing Protocol & OKF v0.2)

## Inputs

- Path to chapter or card in `series/architectures-of-memory/book-*` or `series/parenthood-atlas`

## Steps

1. **Extract** numbered assertive claims (dates, "first", "proved", quotes, causal claims, effect sizes, statistics).
2. **Route Verification by Claim Type:**
   - **Academic papers / preprints:** Run **`academic-bib`** (`crossref_lookup`, `arxiv_search`, `openalex_work`) to verify exact DOI, volume, issue, pagination, and retraction status (`is_retracted`).
   - **Methodological / confounding / vendor statistics / disputed attributions:** Run **`perplexity_reason`**.
   - **Targeted factual / biographical lookups:** Run **`perplexity_ask`** (`search_context_size: "high"`).
   - **Live library / SDK claims:** Run **`context7`** (`resolve-library-id` → `query-docs`).
3. **Update** `research/fact-checks/chNN.md` or `evidence-cards/*.md`.
4. **BibTeX & OKF Source Lock** — Persist every verified paper into `sources.bib` via **`academic-bib`** (`add_bibtex_entry`) and run `python scripts/sync_okf_sources.py`.
5. **Linear** — For each `no` or `partial`, open a `fact-check` issue on Team **ARC** (`Architectures of Memory — Series` or `Parenthood: The Atlas — Series`).
6. **Audit** — Run `python scripts/five_rule_check.py <book-dir> --online-retraction-check` and `python scripts/audit_manuscript.py <book-dir> --strict`.
