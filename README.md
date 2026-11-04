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
| **Series 1: *Architectures of Memory*** | [`series/architectures-of-memory/`](series/architectures-of-memory/) ([`series.yaml`](series/architectures-of-memory/series.yaml)) | **Technical $\to$ Organizational $\to$ Philosophical** | Landmark five-book series exploring memory, persistence, and forgetting across artificial neural networks, institutional governance, and philosophy of mind. **Books 1–5 Complete**: Book 1 (*The Vanishing Signal*), Book 2 (*The Forget Gate*), Book 3 (*The Weight of Attention*), Book 4 (*The Context Window*), and Book 5 (*The Architecture of Forgetting*) — 87 chapters (~72k words), 65 OKF v0.3 cards ($\ge 12$ cards/volume floor satisfied across all 5 volumes), 116 locked BibTeX sources, KDP 6"×9" Print Interior, Kindle EPUB 3, and Reader Edition ready. |
| **Series 2: *Parenthood: The Atlas*** | [`series/parenthood-atlas/`](series/parenthood-atlas/) ([`series.yaml`](series/parenthood-atlas/series.yaml)) | **Science $\to$ Interpretation $\to$ Art** | Developmental science field guide from conception through age 3. **`v1.0` Gold-Master Release Slice**: 15 curated chapters + Quick-Finder front matter (56,548 words), 78 OKF v0.3 `evidence-cards/`, 141 verified BibTeX DOIs, zero retractions, 1,081/1,081 (`100.0%`) covered search clusters. Calibrated to Flesch-Kincaid Grade 8.0–9.6 with 100% clinical jargon isolated to chapter-local `## Notes` and HTMX side-drawer. KDP 6"×9" Print PDF & Reader Edition A4 PDF + EPUB 3 ready. Complete Spanish edition in `series/parenthood-atlas/i18n/es/` (61,981 words, Szigriszt $\ge 50.0$). |

---

## 2. The Book Writing Environment (BWE) Harness (`BWE v1.0.6`)

| SDLC / IDE Equivalent | Realized Press BWE Component | Purpose |
| :--- | :--- | :--- |
| **Product & Monetization Vision** | **[VISION.md](VISION.md)** | 4-pillar strategy: KDP initial launch channel + owned Patreon-style marketing site, BWE software architecture, multi-series extensibility, and marketing intelligence. |
| **Demand Engine & Live Telemetry** | **[scripts/marketing_intelligence.py](scripts/marketing_intelligence.py)** & **[scripts/gads_client.py](scripts/gads_client.py)** | Two-stage demand funnel: Stage 1 autocomplete phrasing discovery + Stage 2 Google Ads API (`KeywordPlanIdeaService`) historical volume/trend/CPC enrichment, negative token domain filtering, Amazon Ads campaign export (`make market-intel`, `make market-intel-ads`), `ANSWERS_DEMAND` graph edges linking search telemetry to OKF cards, and `bwe.cli graph --gaps` ranking highest-volume uncovered intent. |
| **Turnkey API OAuth2 Bootstrap** | **[scripts/gads_auth_setup.py](scripts/gads_auth_setup.py)** | Interactive desktop OAuth2 token generation and `google-ads.yaml` configuration with MCC customer ID routing. |
| **Type System & Unit Tests** | **[SPEC.md](SPEC.md) & [CONTRIBUTING.md](CONTRIBUTING.md)** | Universal **OKF v0.3** specification: 143 evidence cards with 100% typed semantic edges (`EXTENDS:`, `BOUNDS:`, `CONTRASTS:`, `MITIGATES:`, `BRIDGES_LENS:`), structured `quantitative_anchors` ($\ge 2$ empirical constants), formal `attenuation_tier` classifications (`Rule 7f`), zero orphaned cards with complete cross-edition citation parity (`Rule 7g`), and a 167+ deterministic `pytest` regression suite. |
| **Language Grammar & Readability** | **[COMPOSITION.md](COMPOSITION.md) & [style/](style/)** | Three-Lens crosswalk, anomaly chapter grammar, grade-calibrated verbs (*shows* / *suggests* / *is associated with*), split-register jargon isolation (`style/jargon-to-notes.yml`), and [`style/forbidden-phrases.md`](style/forbidden-phrases.md). |
| **Dependency Lockfile & CVE Scanner** | **[scripts/mcp_academic_bib.py](scripts/mcp_academic_bib.py) & [scripts/five_rule_check.py](scripts/five_rule_check.py)** | Verifies DOIs/arXiv IDs against Crossref and OpenAlex (`is_retracted`), locks `sources.bib` $\leftrightarrow$ `SOURCES.md`, and enforces the 5-rule + Rule 7f promotion gate. |
| **Static Analyzer & Continuity Linter** | **[scripts/audit_manuscript.py](scripts/audit_manuscript.py) & `.agents/hooks/post_edit_guard.py`** | Real-time `PostToolUse` guard checking continuity, footnote integrity, Flesch-Kincaid grade, forbidden phrases, harness anti-leakage, Rule 7a-7g graph coherence (`--graph-strict`), and KDP 7-box 50-byte limits. |
| **Multi-Target Release Compiler** | **[scripts/render_publishing_pdfs.py](scripts/render_publishing_pdfs.py), [scripts/render_evidence_briefs.py](scripts/render_evidence_briefs.py) & [scripts/generate_audiobook_tts.py](scripts/generate_audiobook_tts.py)** | Compiles deterministic **Reader Edition (A4 PDF + HTML)**, **Amazon KDP 6"×9" Print Interior PDF** (`--format kdp-6x9`), **Kindle EPUB 3** (`--epub`), **OKF v0.3 Public Evidence Briefs** (`make briefs`), and **Gemini 2.5 Flash TTS Audiobooks**. |
| **Epistemic IDE & Graph RAG Engine** | **[bwe/server.py](bwe/server.py), [bwe/graph_rag.py](bwe/graph_rag.py) & `bwe.cli`** | 3-pane Epistemic IDE with interactive SVG knowledge graph inspector, OKF v0.3 Public Evidence Brief drawer with interactive semantic neighbor navigation, sub-millisecond SQLite Recursive CTE shortest-path epistemic lineage (`find_epistemic_lineage`), $k$-hop subgraph traversal (`query_k_hop_subgraph`), 3-tier hybrid Context Pack compiler, sub-15ms incremental fingerprint caching (`graph_sync_meta`), and interactive Lineage Explorer UI in `/analytics`. |
| **Project Generator (`create-app`)** | **[scripts/init_series.py](scripts/init_series.py)** | Scaffolds new book series (`series/<slug>/series.yaml`) and book volumes with OKF v0.3 directories and seed files. |

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
