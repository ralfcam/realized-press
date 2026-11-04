---
trigger: always_on
description: 5-step Definitive Tool Routing Protocol and OKF v0.3 verification policy across all series and books.
---

# MCP and Tool Routing Policy (Definitive Protocol Across All Series)

All research, OKF v0.3 evidence-card authoring, fact-checking, and drafting tasks MUST follow this 5-step routing protocol:

1. **Broad Historical & Multi-Paper Synthesis (Phase 1):**
   - Use **`perplexity_research`** (`perplexity` MCP) for chapter-level literature surveys, historical timelines, technical report numbers, and developmental cohort histories.
   - Use **`perplexity_ask`** (`perplexity` MCP) for targeted 2–3 paper comparisons.
2. **Contested Claims, Confounding & Vendor-Statistic Audits (Phase 2):**
   - Run **`perplexity_reason`** (`perplexity` MCP) to audit sample scopes, genetically-informed (GI) cohort attenuation (`largely confounded (>50%)`, `partially confounded (20–50%)`, `robust (<20%)`), and secondary-source citation decay.
   - For pre-DOI literary/newspaper print sources, pair **`perplexity_search`** with **Gemini `search_web`**.
3. **Live Frameworks, Vector Stores, RAG & Privacy SDKs (Phase 3):**
   - Always run **`context7` MCP** (`resolve-library-id` → `query-docs`) to pull authoritative repository documentation and SDK signatures for technical chapters.
4. **Mandatory Bibliographic Lock & OKF v0.3 Evidence Cards (Phase 4):**
   - Pass every academic paper or preprint through **`academic-bib` MCP** (`crossref_lookup`, `arxiv_search`, `openalex_work`) to verify exact DOIs, volume/issue/pagination, and retraction status (`is_retracted`).
   - Persist every verified citation into `sources.bib` using **`add_bibtex_entry`** and synchronize `SOURCES.md` via `python scripts/sync_okf_sources.py`.
   - Capture empirical/benchmark claims in `evidence-cards/*.md` with OKF v0.3 front-matter (`attenuation_tier`, $\ge 2$ `quantitative_anchors`, 100% typed `relates_to_cards` semantic edges) and verify via `python scripts/five_rule_check.py <book-dir> --online-retraction-check`.
   - **Never** commit raw `vertexaisearch.cloud.google.com/grounding-api-redirect/` URLs.
5. **Pre-PR Manuscript & OKF Gate (Phase 5):**
   - Run `make five-rule BOOK=<dir>` and `make audit BOOK=<dir>` (under `--strict --graph-strict`) before opening any PR.
