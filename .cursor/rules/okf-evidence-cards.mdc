---
trigger: glob
globs: "**/evidence-cards/**/*.md,**/SOURCES.md,**/sources.bib"
description: Enforces Open Knowledge Format (OKF v0.3) Evidence Card anatomy, the Five-Rule Promotion Gate, Rule 7f/7g graph parity, and dual SOURCES.md / sources.bib synchronization across all series and books.
---

# Open Knowledge Format (OKF v0.3) & Seven-Rule Promotion Gate

All books across both series (`series/architectures-of-memory/book-*` and `series/parenthood-atlas/`) use **OKF v0.3** atomic `evidence-cards/*.md` governed by [`SPEC.md`](../../SPEC.md) and [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

## 1. Required OKF v0.3 Front-Matter & 9-Section Anatomy (`templates/evidence-card-template.md`)

Every card in `evidence-cards/` (excluding `_TEMPLATE.md` and `index.md`) must include canonical OKF v0.3 YAML frontmatter:
- `okf_version: "0.3"`
- `card_id: "<slug-identifier>"`
- `series: "<series-slug>"`
- `primary_lens: "<lens-name>"` (`technical` | `organizational` | `philosophical` for AoM; `biological` | `ecological` | `philosophical` for PA)
- `causal_design: "<design>"` (`rct` | `natural_experiment` | `twin_offspring` | `longitudinal_cohort` | `formal_proof_and_numerical_simulation`)
- `certainty_grade: "High"` (`High` | `Moderate` | `Low` | `Very Low`)
- `attenuation_tier: "robust_<20%"` (`formal_proof` | `robust_<20%` | `partially_confounded_20_50%` | `largely_confounded_>50%`)
- `quantitative_anchors: [...]` ($\ge 2$ verified empirical, statistical, or mathematical figures)
- `allowed_verbs: [...]` / `forbidden_verbs: [...]` (calibrated claim verbs)
- `canonical_metaphors: { body_prose: "...", spoken_tts: "..." }`
- `relates_to_cards: [...]` (100% typed semantic prefixes: `EXTENDS:`, `BOUNDS:`, `CONTRASTS:`, `MITIGATES:`, `BRIDGES_LENS:` — **zero untyped edges**)
- `sources: [...]` (locked bibliographic keys with DOI/resource)

And these exact 9 H2 sections:
1. `## What We Know` (1–2 sentence narrowest supported conclusion)
2. `## How Confident We Are` (starts with `**Grade**: [High / Moderate / Low / Very Low]`)
3. `## Evidence and Causal Assessment`
4. `## Effect Size and Persistence`
5. `## Bias, Heterogeneity, and Confounding` (classified as `largely confounded (>50%)`, `partially confounded (20–50%)`, `robust (<20%)`, `n/a`, or `not classified`)
6. `## What Remains Uncertain`
7. `## What This Does Not Mean` (**Mandatory > 40 chars**: explicitly prohibited overreach or deterministic extrapolation)
8. `## What Action Is Reasonably Justified`
9. `## Sources`

## 2. Seven-Rule Promotion & Graph Gate (`scripts/five_rule_check.py` & `scripts/audit_manuscript.py`)

Never flip `status: draft` $\to$ `status: stable` or open a PR without passing:
```bash
python scripts/five_rule_check.py <book-dir> --online-retraction-check
python scripts/audit_manuscript.py <book-dir> --strict --graph-strict
```
- **Rule 1:** Every `sources:` entry has a resolvable `http(s)` / DOI `resource` and is mirrored in `SOURCES.md` and `sources.bib` (run `python scripts/sync_okf_sources.py`).
- **Rule 2:** Zero retractions or unresolved Expressions of Concern on Crossref (`updates_or_errata`) and OpenAlex (`is_retracted`).
- **Rule 3:** Independent or conceptual replication (or formal mathematical theorem + empirical benchmark) documented.
- **Rule 4:** Exact token match between YAML `certainty_grade` / `confidence:` and in-body `**Grade**:`.
- **Rule 5:** Non-empty `## What This Does Not Mean` (>40 characters).
- **Rule 7f (Quantitative & Semantic Edge Parity):** Valid `attenuation_tier`, $\ge 2$ `quantitative_anchors`, and 100% typed `relates_to_cards` prefixes (zero untyped `RELATES_TO_CARD` edges).
- **Rule 7g (Zero Orphaned Cards & Cross-Edition Parity):** Every card in `evidence-cards/*.md` must have `in_degree(CITES_CARD) >= 1` in manuscript chapters, and `series/parenthood-atlas/i18n/es` must maintain 100% citation parity with the English flagship.
