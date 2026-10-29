# Repository Digest — Realized Press (`ralfcam/realized-press`)

Cold-start orientation map for human collaborators and AI agents working in the **Realized Press** multi-series editorial monorepo and **Book Writing Environment (BWE)** (`https://github.com/ralfcam/realized-press`).

---

## 1. Monorepo & BWE Architecture

This repository unites nonfiction book series under a single **Book Writing Environment (BWE)** governed by **Open Knowledge Format (OKF v0.2)**, **5-Step MCP Tool Routing**, and **Multi-Channel Publishing (Amazon KDP 6"×9" Print PDF + Kindle EPUB 3, Patreon Reader Edition PDF+HTML, and Gemini TTS Audiobook)**:

| Series | Root Path & Manifest | Linear Project (Team `ARC`) | Epistemic Three-Lens Method | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **Series 1: *Architectures of Memory*** | [`series/architectures-of-memory/`](series/architectures-of-memory/) ([`series.yaml`](series/architectures-of-memory/series.yaml)) | `Architectures of Memory — Series` (`3cae0985-8124-4f85-a959-6216cb041c81`) | **Technical $\to$ Organizational $\to$ Philosophical** | **Book 1 (`book-01-vanishing-signal`)**: Complete 16-chapter manuscript (~42,100 words), fact-checked, BibTeX-locked, KDP 6"×9" PDF / EPUB 3 / Reader Edition / TTS ready. **Books 2–5**: Outlined, `sources.bib` + `evidence-cards/` seeded. |
| **Series 2: *Parenthood: The Atlas*** | [`series/parenthood-atlas/`](series/parenthood-atlas/) ([`series.yaml`](series/parenthood-atlas/series.yaml)) | `Parenthood: The Atlas — Series` (`d480b512-ba3d-45dd-9a5a-3933265cdaae`) | **Science $\to$ Interpretation $\to$ Art** | **`v1.0` Commercial & Public Release**: 15 curated chapters (41,342 words), 72 OKF v0.2 `evidence-cards/*.md` (12 `stable`, 60 `draft`), 127 verified sources in `SOURCES.md` + `sources.bib`, Public Evidence Briefs (12 individual PDFs/HTML + Compendium), Amazon KDP 6"×9" Print Interior PDF (139 pages), Kindle EPUB 3 (116 KB), Reader Edition PDF/HTML (94 pages), and Gemini TTS Audiobook Transcript (41,118 words, 4.57 hrs). |

---

## 2. Canonical Root Harness Map

- [`VISION.md`](VISION.md) — Three-pillar project strategy: (1) Amazon KDP + Patreon monetization, (2) Book Writing Environment (BWE) software architecture, and (3) multi-series extensibility.
- [`AGENTS.md`](AGENTS.md) — Master agent instructions, Linear IDs, and Definitive 5-Step Tool Routing Protocol.
- [`SPEC.md`](SPEC.md) — Open Knowledge Format (OKF v0.2) specification for `evidence-cards/` and `SOURCES.md` / `sources.bib`.
- [`COMPOSITION.md`](COMPOSITION.md) — Three-Lens crosswalk, Anomaly-driven chapter grammar, and Grade-to-Verb prose calibration.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Evidence grading rules, confounding attenuation standards, and Five-Rule Promotion Gate.
- [`templates/evidence-card-template.md`](templates/evidence-card-template.md) — Canonical 9-section OKF v0.2 Evidence Card template.
- [`style/`](style/) — Shared `forbidden-phrases.md`, `voice-checklist.md`, and `anomaly-bank.md`.
- [`scripts/`](scripts/) — Unified BWE CLI and CI tools:
  - [`scripts/mcp_academic_bib.py`](scripts/mcp_academic_bib.py) — `academic-bib` MCP server & CLI (`crossref_lookup`, `arxiv_search`, `openalex_work`, `add_bibtex_entry`).
  - [`scripts/five_rule_check.py`](scripts/five_rule_check.py) — Mechanical 5-rule checker for OKF v0.2 `evidence-cards/*.md` with `--online-retraction-check` via Crossref/OpenAlex.
  - [`scripts/audit_manuscript.py`](scripts/audit_manuscript.py) — Cross-chapter continuity, metaphor collision, footnote integrity, forbidden-phrase, and grade-verb auditor.
  - [`scripts/merge_book_chapters.py`](scripts/merge_book_chapters.py) — Merges book chapters into full print Markdown and TTS-stripped audiobook transcripts.
  - [`scripts/render_publishing_pdfs.py`](scripts/render_publishing_pdfs.py) — Compiles deterministic **Reader Edition (A4 PDF + HTML)**, **Amazon KDP 6"×9" Print Interior PDF** (`--format kdp-6x9`), and **Kindle EPUB 3** (`--epub`).
  - [`scripts/render_evidence_briefs.py`](scripts/render_evidence_briefs.py) — Compiles deterministic **Public Evidence Briefs** (standalone 2-page PDFs + responsive HTML + Compendium PDF) for all `stable` OKF v0.2 cards (`make briefs`).
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

# Run OKF v0.2 Five-Rule Evidence Card check
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
