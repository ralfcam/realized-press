# Realized Press Book Writing Environment (BWE) Plugin

`realized-bwe` is the integrated software harness and agentic authoring environment for **Realized Press** (`ralfcam/realized-press`). It provides epistemic rigor, bibliographic locking, continuous audit gates, and multi-format commercial publishing automation across all series.

## Features

- **Open Knowledge Format (OKF v0.2):** Canonical 9-section evidence cards with certainty grading, bounding disclaimers (`## What This Does Not Mean`), and automated five-rule verification (`scripts/five_rule_check.py`).
- **Definitive 5-Step Routing Protocol:** Integrated tool orchestration spanning Perplexity, Context7, and Academic-Bib MCPs.
- **Narrative & Literary Rigor Directives:** Concentric movement architecture, 3-tier causal resolution, "then vs. now" set-pieces, progressive lens escalation, and dual-representation syntax.
- **Continuous Audit Gates:** Automated checks on metaphor collisions, forbidden phrases, footnote syntax, and DOI locks via `scripts/audit_manuscript.py`.
- **Multi-Format Publishing Pipeline:** Compiles Markdown sources to KDP 6"×9" Print interior PDF, Kindle EPUB 3, Reader Edition PDF+HTML, and Gemini TTS audiobooks with zero-drift paragraph timing sidecars.
- **Epistemic IDE Workbench:** Web-based 3-column workspace (`bwe/cli.py serve`) with real-time HTMX audit triggers and citation telemetry.

## Available Skills

- `audiobook-tts`: Synthesizes Gemini TTS audio with zero-drift `.timings.json` paragraph synchronization.
- `chapter-draft`: Drafts chapters using series voice, three-lens structure, and narrative rigor directives.
- `evidence-card-pass`: Authors, audits, and promotes OKF v0.2 evidence cards.
- `fact-check-pass`: Verifies assertions against primary academic sources and locks DOIs.
- `manuscript-audit`: Lints manuscripts for voice compliance, continuity, and footnote integrity.
- `refinement-pass`: Runs iterative refinement loops across drafts, cards, and release builds.
- `research-loop`: Orchestrates deep literature synthesis across Perplexity and Crossref/OpenAlex.

## CLI Usage

```bash
# Launch the 3-column Epistemic IDE & Reader site
python -m bwe.cli serve --host 0.0.0.0 --port 8080

# Run static audit across a book
python scripts/audit_manuscript.py series/parenthood-atlas --strict

# Run OKF v0.2 Five-Rule check with live retraction scans
python scripts/five_rule_check.py series/parenthood-atlas --online-retraction-check

# Compile multi-format publishing outputs
python scripts/render_publishing_pdfs.py series/parenthood-atlas --format kdp-6x9 --epub
```
