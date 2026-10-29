# Realized Press — Book Writing Environment (BWE) & Multi-Series Makefile
# Usage:
#   make audit BOOK=series/architectures-of-memory/book-01-vanishing-signal
#   make audit BOOK=series/parenthood-atlas
#   make five-rule BOOK=series/parenthood-atlas
#   make pdf BOOK=series/architectures-of-memory/book-01-vanishing-signal
#   make kdp BOOK=series/architectures-of-memory/book-01-vanishing-signal
#   make new-series SERIES=systems-of-trust TITLE="Systems of Trust" LENSES="Mechanism,Institution,Ethics" NEW_BOOK=book-01-the-verification-gap

PYTHON ?= python
BOOK ?= series/architectures-of-memory/book-01-vanishing-signal
PREFIX ?=
VOICE ?= Kore
CHAPTER ?=
SERIES ?=
TITLE ?=
LENSES ?= Technical,Organizational,Philosophical
NEW_BOOK ?=

PrefixArg = $(if $(strip $(PREFIX)),--prefix $(strip $(PREFIX)),)
ChapterArg = $(if $(strip $(CHAPTER)),--chapter $(strip $(CHAPTER)),)
NewBookArg = $(if $(strip $(NEW_BOOK)),--book $(strip $(NEW_BOOK)),)

.PHONY: merge merge-audiobook merge-both audit audit-gemini audit-all audit-layout five-rule five-rule-online five-rule-all pdf kdp epub briefs sync-sources audiobook-dry-run audiobook-tts new-series market-intel market-intel-kdp market-intel-ads test

merge:
	$(PYTHON) scripts/merge_book_chapters.py $(BOOK) $(PrefixArg)

merge-audiobook:
	$(PYTHON) scripts/merge_book_chapters.py $(BOOK) --audiobook $(PrefixArg)

merge-both: merge merge-audiobook

audit:
	$(PYTHON) scripts/audit_manuscript.py $(BOOK)

audit-gemini:
	$(PYTHON) scripts/audit_manuscript.py $(BOOK) --gemini

audit-all:
	$(PYTHON) scripts/audit_manuscript.py series/architectures-of-memory/book-01-vanishing-signal --strict
	$(PYTHON) scripts/audit_manuscript.py series/parenthood-atlas --strict

audit-layout:
	$(PYTHON) scripts/audit_pdf_layout.py $(BOOK)

five-rule:
	$(PYTHON) scripts/five_rule_check.py $(BOOK) --summary-only

five-rule-online:
	$(PYTHON) scripts/five_rule_check.py $(BOOK) --online-retraction-check

five-rule-all:
	$(PYTHON) scripts/five_rule_check.py series/architectures-of-memory/book-01-vanishing-signal --summary-only
	$(PYTHON) scripts/five_rule_check.py series/architectures-of-memory/book-02-forget-gate --summary-only
	$(PYTHON) scripts/five_rule_check.py series/architectures-of-memory/book-03-weight-of-attention --summary-only
	$(PYTHON) scripts/five_rule_check.py series/architectures-of-memory/book-04-context-window --summary-only
	$(PYTHON) scripts/five_rule_check.py series/architectures-of-memory/book-05-architecture-of-forgetting --summary-only
	$(PYTHON) scripts/five_rule_check.py series/parenthood-atlas --summary-only

pdf:
	$(PYTHON) scripts/render_publishing_pdfs.py $(BOOK) --format a4

kdp:
	$(PYTHON) scripts/render_publishing_pdfs.py $(BOOK) --format kdp-6x9 --epub
	$(PYTHON) scripts/render_kdp_cover.py $(BOOK)

cover:
	$(PYTHON) scripts/render_kdp_cover.py $(BOOK)

epub:
	$(PYTHON) scripts/render_publishing_pdfs.py $(BOOK) --epub

epub-audit:
	$(PYTHON) scripts/audit_epub.py series/parenthood-atlas/publishing/parenthood-atlas-kdp.epub

briefs:
	$(PYTHON) scripts/render_evidence_briefs.py $(BOOK)

sync-sources:
	$(PYTHON) scripts/sync_okf_sources.py

audiobook-dry-run:
	$(PYTHON) scripts/generate_audiobook_tts.py $(BOOK) $(ChapterArg) --voice $(VOICE) --dry-run

audiobook-tts:
	$(PYTHON) scripts/generate_audiobook_tts.py $(BOOK) $(ChapterArg) --voice $(VOICE)

audiobook-player:
	$(PYTHON) scripts/render_audiobook_player.py $(BOOK)

site:
	$(PYTHON) scripts/render_audiobook_player.py --imprint --output dist/site

serve: bwe-serve

new-series:
	$(PYTHON) scripts/init_series.py --series $(SERIES) --title "$(TITLE)" --lenses "$(LENSES)" $(NewBookArg)

market-intel:
	$(PYTHON) scripts/marketing_intelligence.py $(if $(strip $(SERIES)),--series $(strip $(SERIES)),)

market-intel-kdp:
	$(PYTHON) scripts/marketing_intelligence.py --optimize-kdp-boxes $(if $(strip $(SERIES)),--series $(strip $(SERIES)),)

market-intel-ads:
	$(PYTHON) scripts/marketing_intelligence.py --export-amazon-ads dist/kdp_ads_campaign.csv $(if $(strip $(SERIES)),--series $(strip $(SERIES)),)

test:
	$(PYTHON) -m pytest tests/

# Stage 3: BWE Productization (P-ARC-18)
.PHONY: bwe-serve bwe-schema bwe-audit bwe-intelligence bwe-export-site

bwe-serve: ## Launch Epistemic IDE & Serial Reader Portal on port 8080 (ARC-55 / ARC-56)
	$(PYTHON) -m bwe.cli serve --host 0.0.0.0 --port 8080

bwe-export-site: ## Export static offline imprint site bundle to dist/site (ARC-55)
	$(PYTHON) -m bwe.cli export-site --output dist/site

bwe-schema: ## Export series.schema.json and validate series.yaml files (ARC-57)
	$(PYTHON) -m bwe.cli validate-schema --series-slug parenthood-atlas
	$(PYTHON) -m bwe.cli validate-schema --series-slug architectures-of-memory

bwe-audit: ## Run 5-Rule Check and Manuscript Audit via BWE CLI (ARC-56)
	$(PYTHON) -m bwe.cli audit $(BOOK)

bwe-intelligence: ## Run Marketing Intelligence & Citation Telemetry (ARC-58)
	$(PYTHON) -m bwe.cli intelligence

