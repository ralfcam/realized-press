# Repository Digest — Realized Press (`ralfcam/realized-press`)

Cold-start orientation map for human collaborators and AI agents working in the **Realized Press** multi-series editorial monorepo and **Book Writing Environment (BWE)** (`https://github.com/ralfcam/realized-press`).

---

## 1. Monorepo & BWE Architecture

This repository unites nonfiction book series under a single **Book Writing Environment (BWE v1.3.1)** governed by **Open Knowledge Format (OKF v0.3)**, **5-Step MCP Tool Routing**, **Sentence/Paragraph Micro-QA (`--micro-strict`) & SotA Phrasal Poetics (`--poetics`)**, and **Multi-Channel Publishing (Amazon KDP 6"×9" Print PDF + Hybrid Gemini 2K/4K Full-Wrap Cover PDF + Kindle EPUB 3, Patreon Reader Edition PDF+HTML, and Gemini TTS Audiobook)**:

| Series | Root Path & Manifest | Linear Project (Team `ARC`) | Epistemic Three-Lens Method | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **Series 1: *Architectures of Memory*** | [`series/architectures-of-memory/`](series/architectures-of-memory/) ([`series.yaml`](series/architectures-of-memory/series.yaml)) | `Architectures of Memory — Series` (`3cae0985-8124-4f85-a959-6216cb041c81`) | **Technical $\to$ Organizational $\to$ Philosophical** | **Books 1–5 Gold-Master (`ARC-106`)**: 87 chapters (`87/87 PASS` under `--bestseller-strict --graph-strict --micro-strict --poetics`, FK Grade `6.5–9.4`, `0` dense paragraphs, `0` outlier sentences, `Poetics Score 91.0–100.0`), 65 OKF v0.3 evidence cards ($\ge 12$ cards/volume floor satisfied), 100% typed semantic edges (`EXTENDS:`, `BOUNDS:`, etc.), verified `quantitative_anchors` and `attenuation_tier`, 116 locked BibTeX sources across volumes, cross-volume escalation tracking (`CROSS_BOOK_ESCALATES`), Amazon KDP 6"×9" Print Interiors (`51–57` pages/volume, `100%` same-page bottom footnotes), Kindle EPUB 3 eBooks, Reader Edition PDFs/HTML, and full-wrap print covers ready. |
| **Series 2: *Parenthood: The Atlas*** | [`series/parenthood-atlas/`](series/parenthood-atlas/) ([`series.yaml`](series/parenthood-atlas/series.yaml)) | `Parenthood: The Atlas — Series` (`d480b512-ba3d-45dd-9a5a-3933265cdaae`) | **Science $\to$ Interpretation $\to$ Art** | **`v1.0` Gold-Master Commercial & Public Release (`ARC-100` – `ARC-105`, `ARC-108`)**: 15 curated chapters (`56,633` words, FK Grade `8.2–9.4`, Avg Sent `16.4w–18.4w`, `0` dense paragraphs, `Poetics Score 98.4–99.7`), 78 OKF v0.3 `evidence-cards/*.md` (`78/78` `status: stable`, 100% typed semantic edges, structured `quantitative_anchors`, valid `attenuation_tier`), 141 verified sources in `SOURCES.md` + `sources.bib`, 1,081/1,081 (`100.0%`) covered search clusters, Public Evidence Briefs (78 individual PDFs/HTML + Compendium), Amazon KDP 6"×9" Print Interior PDF (`154` pages, `141/141` co-located bottom footnotes), Kindle EPUB 3, Reader Edition PDF/HTML (`103` pages), Spanish Gold-Master edition (`i18n/es/`, `62,053` words, Szigriszt `55.6–70.9`, Avg Sent `16.7w–19.7w`, `0` dense paragraphs, `Poetics Score 97.6–99.2`, `165` KDP pages, `148/148` co-located bottom footnotes, `138/138` covered clusters), and French Gold-Master edition (`i18n/fr/`, *L'Atlas de la parentalité*, `59,810` words, Kandel-Moles `67.4–74.6`, Avg Sent `18.0w–20.1w`, `0` dense paragraphs, `Poetics Score 97.7–99.7`, `166` KDP pages, `147/147` co-located bottom footnotes, `7` French regional footnotes, Reader Edition PDF/HTML, full-wrap covers, and EPUB 3 ready). |

---

## 2. Canonical Root Harness Map

- [`VISION.md`](VISION.md) — Three-pillar project strategy: (1) Amazon KDP + Patreon monetization, (2) Book Writing Environment (BWE) software architecture, and (3) multi-series extensibility.
- [`AGENTS.md`](AGENTS.md) — Master agent instructions, Linear IDs, and Definitive 5-Step Tool Routing Protocol.
- [`SPEC.md`](SPEC.md) — Universal Open Knowledge Format (OKF v0.3) specification for `evidence-cards/` and `SOURCES.md` / `sources.bib`.
- [`COMPOSITION.md`](COMPOSITION.md) — Three-Lens crosswalk, Anomaly-driven chapter grammar, and Grade-to-Verb prose calibration.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Evidence grading rules, confounding attenuation standards, and Five-Rule + Rule 7f-7g Promotion Gate.
- [`templates/evidence-card-template.md`](templates/evidence-card-template.md) — Canonical 9-section OKF v0.3 Evidence Card template.
- [`style/`](style/) — Shared `forbidden-phrases.md`, `voice-checklist.md`, and `anomaly-bank.md`.
- [`scripts/`](scripts/) — Unified BWE CLI and CI tools:
  - [`scripts/mcp_academic_bib.py`](scripts/mcp_academic_bib.py) — `academic-bib` MCP server & CLI (`crossref_lookup`, `arxiv_search`, `openalex_work`, `add_bibtex_entry`).
  - [`scripts/five_rule_check.py`](scripts/five_rule_check.py) — Mechanical 5-rule checker for OKF v0.3 `evidence-cards/*.md` with `--online-retraction-check` via Crossref/OpenAlex.
  - [`scripts/audit_manuscript.py`](scripts/audit_manuscript.py) — Cross-chapter continuity, metaphor collision, footnote integrity, forbidden-phrase, Rule 7a-7g graph coherence (`--graph-strict`), and grade-verb auditor.
  - [`scripts/merge_book_chapters.py`](scripts/merge_book_chapters.py) — Merges book chapters into full print Markdown and TTS-stripped audiobook transcripts.
  - [`scripts/render_publishing_pdfs.py`](scripts/render_publishing_pdfs.py) — Compiles deterministic **Reader Edition (A4 PDF + HTML)**, **Amazon KDP 6"×9" Print Interior PDF** (`--format kdp-6x9`), and **Kindle EPUB 3** (`--epub`).
  - [`scripts/generate_cover_art.py`](scripts/generate_cover_art.py) & [`scripts/render_kdp_cover.py`](scripts/render_kdp_cover.py) — Synthesizes 300+ DPI Gemini 2K/4K cover illustrations (`gemini-3-pro-image` -> `gemini-3.1-flash-image` -> `gemini-3.1-flash-lite-image`) with Multi-Part Resolution Guard, composites full-wrap KDP covers with deterministic `MIN_SPINE_TEXT_PAGES = 79` threshold guard, cream/white stock variants, and 1600×2400 eBook covers (`bwe cover-art`).
  - [`scripts/render_audiobook_player.py`](scripts/render_audiobook_player.py) — Compiles centralized multi-series audiobook player & imprint showcase (`docs/index.html` and `dist/site/index.html`) with cover artwork thumbnails across all 7 volumes (`bwe export-site`).
  - [`scripts/render_evidence_briefs.py`](scripts/render_evidence_briefs.py) — Compiles deterministic **Public Evidence Briefs** (standalone 2-page PDFs + responsive HTML + Compendium PDF) for all `stable` OKF v0.3 cards (`make briefs`).
  - [`scripts/generate_audiobook_tts.py`](scripts/generate_audiobook_tts.py) — Synthesizes chapter audio via Gemini 2.5 Flash TTS.
  - [`scripts/init_series.py`](scripts/init_series.py) — Scaffolds new series (`series/<slug>/series.yaml`) and book volumes in one command.
  - [`scripts/marketing_intelligence.py`](scripts/marketing_intelligence.py) — Marketing Intelligence, Demand Telemetry & KDP 7-Box Knapsack Optimizer (`make market-intel`, `make market-intel-kdp`).
  - [`scripts/gads_client.py`](scripts/gads_client.py) — Google Ads API (`KeywordPlanIdeaService`) client & native Keyword Planner UI CSV export parser.
  - [`tests/`](tests/) — Pytest automated test suite (`tests/test_gads_client.py`, `tests/test_keyword_pipeline.py`) (`make test`).

---

## 3. Common `make` Commands

```bash
# Audit manuscript continuity, footnotes, metaphors & forbidden phrases
make audit BOOK=series/architectures-of-memory/book-01-vanishing-signal
make audit BOOK=series/parenthood-atlas

# Run OKF v0.3 Five-Rule Evidence Card check
make five-rule BOOK=series/parenthood-atlas
make five-rule BOOK=series/architectures-of-memory/book-01-vanishing-signal

# Compile merged Markdown + TTS transcript
make merge BOOK=series/architectures-of-memory/book-01-vanishing-signal
make merge BOOK=series/parenthood-atlas

# Render deterministic Reader Edition (A4 PDF + HTML) for Patreon / review
make pdf BOOK=series/architectures-of-memory/book-01-vanishing-signal
make pdf BOOK=series/parenthood-atlas

# Render Amazon KDP Print Interior (6"x9" PDF) + Kindle EPUB 3 eBook
make kdp BOOK=series/architectures-of-memory/book-01-vanishing-signal
make kdp BOOK=series/parenthood-atlas

# Render Public Evidence Briefs (2-Page PDFs + HTML + Compendium)
make briefs BOOK=series/parenthood-atlas

# Estimate duration / dry-run Gemini TTS Audiobook
make audiobook-dry-run BOOK=series/architectures-of-memory/book-01-vanishing-signal
make audiobook-dry-run BOOK=series/parenthood-atlas

# Initialize a new book series in the BWE
make new-series SERIES=systems-of-trust TITLE="Systems of Trust" LENSES="Mechanism,Institution,Ethics" NEW_BOOK=book-01-the-verification-gap
```
