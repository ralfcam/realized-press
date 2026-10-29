# Realized Press (`ralfcam/realized-press`) — Book Writing Environment & Multi-Series Imprint

**Realized Press** (`https://github.com/ralfcam/realized-press`) is a dual-engine publishing studio and **Book Writing Environment (BWE)** built on the principles of the **Software Development Lifecycle (SDLC)** and modern **IDEs**:

1. **Book Monetization & Owned Marketing Engine:** Compiles verified manuscripts directly into **Amazon KDP** assets (**6"×9" Print-on-Demand PDF** with mirrored gutter margins, **Kindle EPUB 3**, and **Gemini TTS Audiobook** — serving as the initial release channel and blueprint for multi-retailer expansion) alongside an **internally developed Marketing & Serial-Membership Web Site** modeled on Patreon (**Public Evidence Briefs**, **Interactive OKF Explorer**, **Chapter Preprints**, and **Reader Edition 0.1 PDF+HTML**).
2. **The Book Writing Environment (BWE):** An agentic authoring, verification, and publishing software harness governed by **Open Knowledge Format (OKF v0.2)** (an epistemic type system and unit-test suite for prose), a **5-step MCP Tool Routing Protocol**, real-time style/continuity linting, and CI release gates.
3. **Plug-and-Play Multi-Series Extensibility:** Declarative `series/<series-slug>/series.yaml` manifests and automated scaffolding (`scripts/init_series.py`) allow new book series and volumes to be added in seconds without changing the core harness.
4. **Marketing Intelligence & Data-Driven Topic Selection:** Upstream and closed-loop telemetry (`scripts/marketing_intelligence.py`) driving series/book topic selection, competitive review-gap mining, OpenAlex/Crossref citation velocity, Amazon KDP 7-slot backend keywords, and owned-marketing-site lead-magnet ranking.

See **[VISION.md](VISION.md)** for the full product, monetization, and BWE software architecture roadmap, and **[REPO_DIGEST.md](REPO_DIGEST.md)** for the cold-start inventory.

---

## 1. Imprint Catalog (`series/`)

| Series | Directory & Manifest | Three-Lens Method | Description & Current Release Slice |
| :--- | :--- | :--- | :--- |
| **Series 1: *Architectures of Memory*** | [`series/architectures-of-memory/`](series/architectures-of-memory/) ([`series.yaml`](series/architectures-of-memory/series.yaml)) | **Technical $\to$ Organizational $\to$ Philosophical** | Landmark five-book series exploring memory, persistence, and forgetting across artificial neural networks, institutional governance, and philosophy of mind. **Books 1–5 Complete**: Book 1 (*The Vanishing Signal*), Book 2 (*The Forget Gate*), Book 3 (*The Weight of Attention*), Book 4 (*The Context Window*), and Book 5 (*The Architecture of Forgetting*) — 85 chapters (~220k words), 76 OKF v0.2 cards, 127 locked BibTeX sources, KDP 6"×9" Print and Reader Edition ready. |
| **Series 2: *Parenthood: The Atlas*** | [`series/parenthood-atlas/`](series/parenthood-atlas/) ([`series.yaml`](series/parenthood-atlas/series.yaml)) | **Science $\to$ Interpretation $\to$ Art** | Developmental science field guide from conception through age 3. **`v1.0-rc3` Bestseller Release Slice**: 15 curated chapters + Quick-Finder front matter (54,406 words), 76 OKF v0.2 `evidence-cards/`, 134 verified BibTeX DOIs, zero retractions. Calibrated to Flesch-Kincaid Grade 8.0–10.0 with 100% clinical jargon isolated to chapter-local `## Notes` and HTMX side-drawer. KDP 6"×9" Print PDF (145p) & Reader Edition A4 PDF (96p) + EPUB 3 ready. |

---

## 2. The Book Writing Environment (BWE) Harness (`BWE v0.6.1`)

| SDLC / IDE Equivalent | Realized Press BWE Component | Purpose |
| :--- | :--- | :--- |
| **Product & Monetization Vision** | **[VISION.md](VISION.md)** | 4-pillar strategy: KDP initial launch channel + owned Patreon-style marketing site, BWE software architecture, multi-series extensibility, and marketing intelligence. |
| **Demand Engine & Live Telemetry** | **[scripts/marketing_intelligence.py](scripts/marketing_intelligence.py)** & **[scripts/gads_client.py](scripts/gads_client.py)** | Two-stage demand funnel: Stage 1 autocomplete phrasing discovery + Stage 2 Google Ads API (`KeywordPlanIdeaService`) historical volume/trend/CPC enrichment, negative token domain filtering, and Amazon Ads campaign export (`make market-intel`, `make market-intel-ads`). |
| **Turnkey API OAuth2 Bootstrap** | **[scripts/gads_auth_setup.py](scripts/gads_auth_setup.py)** | Interactive desktop OAuth2 token generation and `google-ads.yaml` configuration with MCC customer ID routing. |
| **Type System & Unit Tests** | **[SPEC.md](SPEC.md) & [CONTRIBUTING.md](CONTRIBUTING.md)** | Universal **OKF v0.2** specification for atomic `evidence-cards/*.md` (9 required sections, compound certainty grading, confounding attenuation, and `## What This Does Not Mean`). |
| **Language Grammar & Readability** | **[COMPOSITION.md](COMPOSITION.md) & [style/](style/)** | Three-Lens crosswalk, anomaly chapter grammar, grade-calibrated verbs (*shows* / *suggests* / *is associated with*), split-register jargon isolation (`style/jargon-to-notes.yml`), and [`style/forbidden-phrases.md`](style/forbidden-phrases.md). |
| **Dependency Lockfile & CVE Scanner** | **[scripts/mcp_academic_bib.py](scripts/mcp_academic_bib.py) & [scripts/five_rule_check.py](scripts/five_rule_check.py)** | Verifies DOIs/arXiv IDs against Crossref and OpenAlex (`is_retracted`), locks `sources.bib` $\leftrightarrow$ `SOURCES.md`, and enforces the 5-rule promotion gate. |
| **Static Analyzer & Continuity Linter** | **[scripts/audit_manuscript.py](scripts/audit_manuscript.py) & `.agents/hooks/post_edit_guard.py`** | Real-time `PostToolUse` guard checking continuity, footnote integrity, Flesch-Kincaid grade, forbidden phrases, harness anti-leakage, and KDP 7-box 50-byte limits. |
| **Multi-Target Release Compiler** | **[scripts/render_publishing_pdfs.py](scripts/render_publishing_pdfs.py) & [scripts/generate_audiobook_tts.py](scripts/generate_audiobook_tts.py)** | Compiles deterministic **Reader Edition (A4 PDF + HTML)**, **Amazon KDP 6"×9" Print Interior PDF** (`--format kdp-6x9`), **Kindle EPUB 3** (`--epub`), and **Gemini 2.5 Flash TTS Audiobooks**. |
| **Epistemic IDE & Reader Portal** | **[bwe/server.py](bwe/server.py) & `bwe.cli`** | 3-pane Epistemic IDE and reader portal with real-time HTMX side-drawer, audio sync, and interactive card inspection (`make serve`). |
| **Project Generator (`create-app`)** | **[scripts/init_series.py](scripts/init_series.py)** | Scaffolds new book series (`series/<slug>/series.yaml`) and book volumes with OKF v0.2 directories and seed files. |

---

## 3. Quick Commands (`Makefile`)

```bash
# Run deterministic test suite (14+ unit tests across schema, knapsack, and telemetry)
make test

# Audit flagship manuscripts for style, continuity, footnotes, and Flesch-Kincaid grade
make audit BOOK=series/parenthood-atlas
make audit-all

# Run layout budget and page overflow auditor
make audit-layout BOOK=series/parenthood-atlas

# Run OKF v0.2 Five-Rule check across evidence cards (with live retraction sentinel)
make five-rule BOOK=series/parenthood-atlas
make five-rule-online BOOK=series/parenthood-atlas
make five-rule-all

# Render Reader Edition (A4 PDF + standalone HTML) for Patreon / review
make pdf BOOK=series/architectures-of-memory/book-01-vanishing-signal
make pdf BOOK=series/parenthood-atlas

# Compile Amazon KDP Release Package (6"x9" Mirrored-Margin Print PDF + Kindle EPUB 3)
make kdp BOOK=series/architectures-of-memory/book-01-vanishing-signal
make kdp BOOK=series/parenthood-atlas

# Run Demand & Editorial Telemetry Radar (Stage 1 + Stage 2 demand scoring)
make market-intel SERIES=parenthood-atlas
make market-intel SERIES=architectures-of-memory

# Pack high-intent demand words into 7 KDP backend keyword boxes (<= 49 UTF-8 bytes each)
make market-intel-kdp SERIES=parenthood-atlas

# Export Amazon Ads Sponsored Products bulk upload CSV from covered demand
make market-intel-ads SERIES=parenthood-atlas

# Merge chapters into full Markdown and TTS-ready audiobook transcript
make merge BOOK=series/parenthood-atlas
make merge-audiobook BOOK=series/parenthood-atlas

# Estimate Gemini TTS audiobook duration or synthesize speech
make audiobook-dry-run BOOK=series/parenthood-atlas
make audiobook-tts BOOK=series/parenthood-atlas

# Launch 3-Pane Epistemic IDE & Serial Reader Portal locally on port 8080
make serve

# Validate series manifests against JSON Schema
make bwe-schema

# Scaffold a brand-new series or book volume in the BWE
make new-series SERIES=systems-of-trust TITLE="Systems of Trust" LENSES="Mechanism,Institution,Ethics" NEW_BOOK=book-01-the-verification-gap
```
