# Agent Guide — Realized Press (`ralfcam/realized-press`: Book Writing Environment & Multi-Series Imprint)

This repository (**Realized Press**, `https://github.com/ralfcam/realized-press`) is both a **multi-series nonfiction publishing imprint** (launching initially via **Amazon KDP** as an expansion blueprint and marketed/serialized via an **internally developed Patreon-style marketing & membership site**) and a **Book Writing Environment (BWE)** software harness governed by **Open Knowledge Format (OKF v0.2)**, a **5-step Definitive Tool Routing Protocol**, **Linear (`ARC`)** project tracking, and a **Multi-Format Publishing Pipeline (Markdown, Reader Edition PDF+HTML, KDP 6"×9" Print PDF, Kindle EPUB 3, and Gemini TTS Audiobook)**. See [VISION.md](VISION.md), [README.md](README.md), and [REPO_DIGEST.md](REPO_DIGEST.md).

## 1. Symmetric Multi-Series File Map

- **Root BWE Harness:**
  - [VISION.md](VISION.md) — Three-pillar vision: Amazon KDP + Patreon monetization, Book Writing Environment (SDLC/IDE for books), and multi-series extensibility.
  - [SPEC.md](SPEC.md) — Universal Open Knowledge Format (OKF v0.2) specification.
  - [COMPOSITION.md](COMPOSITION.md) — Three-Lens crosswalk, Anomaly-driven chapter grammar, and Grade-to-Verb prose calibration.
  - [CONTRIBUTING.md](CONTRIBUTING.md) — Evidence-Card format, confounding attenuation standards, and Five-Rule Promotion Gate.
  - [REPO_DIGEST.md](REPO_DIGEST.md) — Cold-start orientation map and inventory across all series.
  - [templates/evidence-card-template.md](templates/evidence-card-template.md) — Canonical 9-section OKF v0.2 Evidence Card template.
  - [style/](style/) — Shared [forbidden-phrases.md](style/forbidden-phrases.md), [voice-checklist.md](style/voice-checklist.md), and [anomaly-bank.md](style/anomaly-bank.md).
  - [scripts/](scripts/) — Shared CLI & MCP automation (`mcp_academic_bib.py`, `five_rule_check.py`, `audit_manuscript.py`, `merge_book_chapters.py`, `render_publishing_pdfs.py`, `generate_audiobook_tts.py`, `sync_okf_sources.py`, `init_series.py`).
- **Series 1 — *Architectures of Memory* (`series/architectures-of-memory/`):**
  - Series manifest & context: [series.yaml](series/architectures-of-memory/series.yaml), [series-bible.md](series/architectures-of-memory/series-bible.md), [characters.md](series/architectures-of-memory/characters.md), [baseline outlines.md](series/architectures-of-memory/baseline%20outlines.md).
  - Five books (`book-01-vanishing-signal` … `book-05-architecture-of-forgetting`), each with `outline.md`, `evidence-cards/`, `chapters/`, `drafts/`, `research/notes/`, `research/fact-checks/`, `research/sources.bib`, and `research/SOURCES.md`.
- **Series 2 — *Parenthood: The Atlas* (`series/parenthood-atlas/`):**
  - Series manifest & context: [series.yaml](series/parenthood-atlas/series.yaml), [README.md](series/parenthood-atlas/README.md), [COMPOSITION.md](series/parenthood-atlas/COMPOSITION.md), [REPO_DIGEST.md](series/parenthood-atlas/REPO_DIGEST.md), [CHANGELOG.md](series/parenthood-atlas/CHANGELOG.md).
  - Canonical layers: `evidence-cards/` (68 OKF v0.2 cards), `chapters/` (`01-*.md` … `15-*.md` + `_OUTLINE.md`), `SOURCES.md`, `sources.bib`, `style/`, and `preliminary/` (staging drafts, extraction, triage, publishing).
- **Adding New Series (`series/<series-slug>/`):**
  - Scaffold any new series or book volume via `python scripts/init_series.py --series <slug> --title "<Title>" --lenses "<L1,L2,L3>" --book <book-slug>` (`make new-series`).

## 2. Before You Write

- Read [COMPOSITION.md](COMPOSITION.md) and [style/forbidden-phrases.md](style/forbidden-phrases.md) before drafting or editing any chapter.
- **For Series 1 (*Architectures of Memory*):** Read [series/architectures-of-memory/series-bible.md](series/architectures-of-memory/series-bible.md) and [series/architectures-of-memory/characters.md](series/architectures-of-memory/characters.md); apply the **Technical $\to$ Organizational $\to$ Philosophical** three-lens method.
- **For Series 2 (*Parenthood: The Atlas*):** Read [series/parenthood-atlas/COMPOSITION.md](series/parenthood-atlas/COMPOSITION.md) and [series/parenthood-atlas/CONTRIBUTING.md](series/parenthood-atlas/CONTRIBUTING.md); apply the **Science $\to$ Interpretation $\to$ Art** three-lens method.
- **For Any New Series:** Read `series/<slug>/series.yaml` and `series/<slug>/series-bible.md` to identify its configured three-lens grammar and voice rules.
- Calibrate claim verbs to the underlying OKF v0.2 Evidence Card certainty grade (*High* $\to$ **shows**; *Moderate* $\to$ **suggests**; *Low* $\to$ **is associated with**).

## 3. Linear (Team `ARC`) & Master 4-Stage Execution Sequence

- **Team:** `ARC` — id `b507edbe-bdaa-4c47-8bdd-63af48774ebf` (`https://linear.app/realized/team/ARC/projects/all`)
- **Master Execution Order Across Projects:**
  1. **Stage 1 (Immediate Goal — Priority 1):** Loop on refinement passes until publish for **Parenthood: The Atlas — Series (`P-ARC-17`)** (`https://linear.app/realized/project/parenthood-the-atlas-series-e3ae54ac870d/overview`) — *reflect upon and harden the BWE harness along this phase.*
  2. **Stage 2 (Priority 2):** Repeat the hardened loop across all five volumes of **Architectures of Memory — Series (`P-ARC-8`)** (`https://linear.app/realized/project/architectures-of-memory-series-e798843bf9fb/overview`).
  3. **Stage 3 (Priority 3):** Continue in pillar order of **Realized Press — Canonical Vision & Book Writing Environment (`P-ARC-18`)** (`https://linear.app/realized/project/realized-press-canonical-vision-and-book-writing-environment-bwe-130eae5e23b7/overview`).
  4. **Stage 4 (Expansion):** Select new series/books via **Marketing Intelligence** (`scripts/marketing_intelligence.py`) and publish the **internally developed marketing & serial-membership site**.
- **Antigravity Native Automation Primitives Map:**
  - **Lifecycle Hooks ([`.agents/hooks.json`](.agents/hooks.json) $\to$ [`.agents/hooks/post_edit_guard.py`](.agents/hooks/post_edit_guard.py)):** Real-time `PostToolUse` & `PostInvocation` enforcement of OKF v0.2 Five-Rule checks, DOI bibliographic locks, forbidden phrases, footnote integrity, and `series.yaml` KDP 7-keyword-slot gates across Stages 1–4.
  - **Workspace Skills ([`.agents/skills/`](.agents/skills/)):** `refinement-pass`, `research-loop`, `evidence-card-pass`, `chapter-draft`, `fact-check-pass`, `manuscript-audit`, and `audiobook-tts`.
  - **Slash Commands & Subagent Orchestration:** `/goal` (autonomous Stage 1/2 refinement loops), `/teamwork-preview` / `invoke_subagent` (parallel GI-confounding card audits & multi-lens research), `/schedule` (nightly retraction sentinel & weekly marketing intelligence sidecars), and `/plugin` (Stage 3 `realized-bwe` packaging).
- **Imprint & BWE Vision Project:** `Realized Press — Canonical Vision & Book Writing Environment (BWE)` (`P-ARC-18`) — id `fe68af35-3169-4d26-868e-0000a8d07672` (`https://linear.app/realized/project/realized-press-canonical-vision-and-book-writing-environment-bwe-130eae5e23b7`)
  - **Canonical Vision Document:** `916947a3-864e-45c2-bc26-2a8b2b1a465f` (`https://linear.app/realized/document/canonical-vision-monetization-book-writing-environment-bwe-and-multi-aecc83c9240e`)
  - **Milestones:**
    - `Pillar 1 — KDP Launch Channel & Owned Marketing/Serial Site` — id `11633e7c-51be-4b14-bfbd-5574f5af65c2`
    - `Pillar 2 — Book Writing Environment (BWE) Software & Agentic Harness` — id `f87ccfa9-55a1-4124-ace0-6f514e001ead`
    - `Pillar 3 — Plug-and-Play Multi-Series Extensibility (series/<slug>/)` — id `beac3251-0a47-4546-9603-a30c9037a64e`
    - `Pillar 4 — Marketing Intelligence & Data-Driven Topic Selection` — id `4ac18540-c439-42d0-a29d-fbd13d4d17dc`
- **Series 1 Project:** `Architectures of Memory — Series` (`P-ARC-8`) — id `3cae0985-8124-4f85-a959-6216cb041c81`
  - **Book 1 milestone:** `Book 1 — The Vanishing Signal` — id `3b9c4dbb-ed86-42f1-9370-d02730fb1d7e`
- **Series 2 Project:** `Parenthood: The Atlas — Series` (`P-ARC-17`) — id `d480b512-ba3d-45dd-9a5a-3933265cdaae`
  - **Milestones:**
    - `v0.3 — Curated 15-Chapter Baseline & Reader Edition 0.1` — id `b711f5c4-c873-4f9f-9bcc-642a6f2067f6`
    - `v0.4 — Evidence Card Expansion & GI Classification` — id `682e6eda-ace2-4366-b601-e64c1a42d917`
    - `v1.0 — Public Evidence Briefs, Print & Audiobook Release` — id `011981ab-eaea-443b-b189-d54d68290b74`

Use labels `research`, `draft`, `edit`, `fact-check`, `structure`, and `book-01` … `book-05` as appropriate.

## 4. Citations, OKF v0.2 & Definitive Tool Routing Protocol

**Do not invent dates, quotes, or attributions.** If a claim is not yet sourced, mark it `[citation needed]` and capture the gap in `research/fact-checks/` or a Linear `fact-check` issue.

All research, evidence-card authoring, verification, and drafting tasks MUST follow the **5-step Definitive Tool Routing Protocol**:

1. **Phase 1 — Broad Historical & Archival Synthesis:** Start with **`perplexity_research`** (`perplexity` MCP) for multi-paper timelines, unpublished technical report numbers, and conference/cohort histories; use **`perplexity_ask`** for targeted 2–3 paper lookups.
2. **Phase 2 — Methodological, Confounding & Vendor-Statistic Audits:** Run **`perplexity_reason`** (`perplexity` MCP) whenever evaluating secondary vendor statistics, genetically-informed (GI) cohort confounding, sample populations, or contested attributions. For pre-DOI print/literary loci, pair **`perplexity_search`** with **Gemini `search_web`**.
3. **Phase 3 — Live Technical Frameworks, Vector Stores & Privacy SDKs:** Always run **`context7` MCP** (`resolve-library-id` $\to$ `query-docs`) for technical chapters (RAG, vector databases, differential privacy, unlearning libraries).
4. **Phase 4 — Mandatory Bibliographic Lock & OKF v0.2 Evidence Cards:**
   - Pass every cited academic paper or preprint through **`academic-bib` MCP** (`crossref_lookup`, `arxiv_search`, `openalex_work`) to verify exact DOIs, volume/issue/page numbers, and retraction flags (`is_retracted`), then persist to `sources.bib` via **`add_bibtex_entry`** and sync `SOURCES.md` via `python scripts/sync_okf_sources.py`.
   - Capture empirical/benchmark claims in `evidence-cards/*.md` (9 required sections including `## What This Does Not Mean`) and verify via `python scripts/five_rule_check.py <book-dir> --online-retraction-check`.
   - Never paste raw `vertexaisearch.cloud.google.com/grounding-api-redirect/` URLs into notes, cards, or chapters.
5. **Phase 5 — Pre-PR Manuscript & OKF Gate:** Run `make five-rule BOOK=<dir>` and `make audit BOOK=<dir>` before opening any PR.

## 5. Project Automation (`Makefile` & `scripts/`)

- **OKF v0.2 Five-Rule Gate:** `python scripts/five_rule_check.py <book-dir> [--online-retraction-check]` (`make five-rule BOOK=...`).
- **Manuscript, Continuity & Style Auditor:** `python scripts/audit_manuscript.py <book-dir> [--strict]` (`make audit BOOK=...`).
- **Source Catalog Sync (`SOURCES.md` $\leftrightarrow$ `sources.bib`):** `python scripts/sync_okf_sources.py` (`make sync-sources`).
- **Merged Manuscripts (Print MD + TTS Transcript):** `python scripts/merge_book_chapters.py <book-dir> [--audiobook]` (`make merge BOOK=...`).
- **Reader Edition PDF + HTML Renderer (Patreon / Review):** `python scripts/render_publishing_pdfs.py <book-dir>` (`make pdf BOOK=...`).
- **Amazon KDP Print Interior (6"×9") + Kindle EPUB 3 Compiler:** `python scripts/render_publishing_pdfs.py <book-dir> --format kdp-6x9 --epub` (`make kdp BOOK=...`).
- **Audiobook TTS Generator:** `python scripts/generate_audiobook_tts.py <book-dir> --dry-run` (`make audiobook-dry-run BOOK=...` / `make audiobook-tts BOOK=...`).
- **New Series / Volume Scaffolder:** `python scripts/init_series.py --series <slug> --title "<Title>" [--book <book-slug>]` (`make new-series SERIES=... TITLE="..."`).
- **Marketing Intelligence & KDP Demand Telemetry:** `python scripts/marketing_intelligence.py [--keywords seed] [--optimize-kdp-boxes] [--fetch-live] [--import-gkp-export <file>]` (`make market-intel` / `make market-intel-kdp`).
- **Deterministic Test Suite:** `pytest tests/` (`make test`).
