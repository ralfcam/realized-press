---
name: research-loop
description: >-
  Runs the Linear to Perplexity/Academic-Bib/Context7 to GitHub research loop for a book
  chapter or OKF v0.2 evidence card across Architectures of Memory and Parenthood: The Atlas.
  Use when the user asks to research, gather sources for, run Perplexity on, or complete
  a research issue.
---

# Research Loop (Definitive Tool Routing Protocol & OKF v0.2)

## Inputs to confirm

- Target series/book folder: `series/architectures-of-memory/book-0X-*` or `series/parenthood-atlas`
- Chapter number / domain slug (e.g. `ch01-six-years-thesis-to-paper` or `guided-play-efficacy`)
- Linear issue id (e.g. `ARC-50`) under Team **ARC**

## Steps

1. **Linear (`linear` MCP)** — Ensure an issue exists on team **ARC** (`b507edbe-bdaa-4c47-8bdd-63af48774ebf`), under **Architectures of Memory — Series** (`3cae0985-8124-4f85-a959-6216cb041c81`) or **Parenthood: The Atlas — Series** (`d480b512-ba3d-45dd-9a5a-3933265cdaae`), with labels **`research`**.
2. **Execute Definitive Tool Routing Protocol:**
   - **Historical / Archival Survey:** Run **`perplexity_research`** (or **`perplexity_ask`** for targeted 2–3 paper lookups).
   - **Confounding / Vendor Statistics / Contested Claims:** Run **`perplexity_reason`** to audit sample populations, genetically-informed (GI) cohort attenuation, and secondary citation decay.
   - **Pre-DOI Literary / Print Loci:** Pair **`perplexity_search`** with **Gemini `search_web`**.
   - **Live Technical SDKs / Vector Stores / Privacy Libraries:** Run **`context7`** (`resolve-library-id` → `query-docs`).
   - **Mandatory Bibliographic Lock:** Pass every cited academic paper or preprint through **`academic-bib`** (`crossref_lookup`, `arxiv_search`, `openalex_work`), persist to `sources.bib` via **`add_bibtex_entry`**, and sync `SOURCES.md` via `python scripts/sync_okf_sources.py`. Never commit `vertexaisearch.cloud.google.com/grounding-api-redirect/` URLs.
3. **Author OKF v0.2 Evidence Card & Research Note:**
   - Create/update `evidence-cards/<slug>.md` (9 required sections + `## What This Does Not Mean`) and verify via `python scripts/five_rule_check.py <card> --online-retraction-check`.
   - For Series 1 chapters, create `research/notes/chNN-slug.md` and `research/fact-checks/chNN.md`.
4. **Branch + PR** — Open PR via `gh pr create`; link PR in Linear.
