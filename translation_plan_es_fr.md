# Realized Press Multilingual Pipeline: Two-Pass Translation & Posterior Phrasal-Sculpting Plan (`ES` / `FR`)

**Status:** Complete (`i18n/es` Gold-Master in `ARC-105`; `i18n/fr` Gold-Master in `ARC-108` / `ARC-109`)  
**Governing Issues:** `ARC-76`, `ARC-77`, `ARC-81`, `ARC-101`, `ARC-104`, `ARC-105`, `ARC-107`, `ARC-108`, `ARC-109`

---

## 1. Core Architectural Rule: The Two-Pass Localization Standard

No book translation in Realized Press is complete after semantic and epistemic transfer alone. Because first-pass translation from English into Romance languages inevitably introduces **syntactic calques**, **copula inflation (`ser / estar / haber / tener`)**, **`de + noun` genitive chains**, **trailing gerunds (`gerundio de posterioridad`)**, and **15–20% paragraph length expansion** over the 135-word visual geometry cap, every localized edition must execute in **two distinct passes**:

### Pass 1 — Epistemic, Lexical & Regional Apparatus Transfer
1. **Citation & Epistemic Parity:** Preserve 100% of canonical inline `[^chXX-...]` footnote anchors and calibrate bold claim verbs to each OKF v0.3 card's `certainty_grade` and `attenuation_tier`.
2. **Regional Clinical & Legal Apparatus:** Inject target-market regional footnotes (`[^chXX-es-...]` / `[^chXX-fr-...]`) in `## Notes` (e.g., AEMPS/SEGO periconceptional folate & iodine, HAS periconceptional folates, SNS/HAS crib safety, AEP/HCSP screen time, statutory leave frameworks).
3. **Split-Register Jargon Isolation & Search-Intent Weaves:** Relocate all clinical terms in `i18n/<lang>/style/jargon-to-notes.yml` into `## Notes` and weave localized search-intent vocabulary from `i18n/<lang>/style/lexicon.yaml`.

### Pass 2 — Posterior Native Phrasal-Sculpting (`--micro-strict --poetics --lang <lang>`)
With the **Epistemic Skeleton frozen** (`bwe/style_sculptor.py`), run a dedicated native phrasal-sculpting pass governed by `i18n/<lang>/style/phrasal-poetics.yml` and verified by:
```powershell
python scripts/audit_manuscript.py series/parenthood-atlas/i18n/<lang> --bestseller-strict --graph-strict --micro-strict --poetics --lang <lang>
```

1. **Kinetic & Pronominal Verbs Over Copulas (`Copula Ratio <= 38%`):** Replace static copular predicates and passive calques with physical, pronominal, and kinetic verbs drawn from each card's canonical metaphors.
2. **Pruning Genitive Chains & Nominalization Clusters (`0` Clusters):** Eliminate clauses stacking $\ge 3$ abstract noun suffixes.
3. **Purging Trailing Gerunds & Negation-Pivot Clichés:** Eliminate sentence-ending participial tail-drags and cap formulaic negation pivots at $\le 3$ per chapter.
4. **Native Clausal Counterpoint (`Cadence Flags = 0`, $\sigma \ge 2.0\text{w}$):** Alternate sweeping periodic setups with crisp declarative hinges.
5. **De-Walling Expanded Paragraphs (`<= 135w`, `<= 6s`, Local Readability `>= 42.0`):** Tighten prepositional bloat and split every narrative paragraph exceeding `135 words` or `6 sentences` at its natural causal hinge so Dense Paragraph advisories equal `0`.

---

## 2. Spanish Edition (*El atlas de la crianza* — `series/parenthood-atlas/i18n/es/`) Gold-Master

* **Manuscript Scale:** 15 curated chapters + Quick-Finder front-matter (`62,053` words).
* **Readability & Sentence Cadence:** Szigriszt-Pazos `55.6–70.9` (target $\ge 50.0$), average sentence length `16.7w–19.7w`, max single sentence $\le 38\text{w}$ (`0` outlier sentences).
* **Paragraph De-Walling:** `0` dense paragraphs across all 15 chapters ($\le 135\text{w}$, $\le 6\text{s}$).
* **Phrasal Poetics:** Poetics score `97.6–99.2`, copula ratio $\le 24.5\%$, `0` nominalization clusters, `0` trailing gerunds (`gerundio de posterioridad`).
* **Epistemic Hygiene:** `78/78` OKF v0.3 cards cited (`0` orphans), `148` verified BibTeX DOIs, `0` retractions, `7` Spanish public-health footnotes (`[^ch01-es-folatos]`, `[^ch01-es-yodo]`, `[^ch03-es-piel-con-piel]`, `[^ch04-es-colecho-seguro]`, `[^ch07-es-pantallas]`, `[^ch08-es-escuelas-infantiles]`, `[^ch13-es-permiso-paternal]`).
* **Publishing Suite:**
  * Reader Edition A4 PDF (`112` pages) + Reader HTML.
  * Amazon KDP 6"×9" Trade Paperback Interior PDF (`165` pages, `148/148` co-located bottom footnotes, `0` leaks).
  * Amazon KDP Full-Wrap Cover PDF (`465.5 DPI` front art, dynamically calculated spine wrap).
  * Kindle EPUB 3.0 (`2.8 MB`).
  * Telemetry: `data/gkp_parenting_es_seed.csv` (138 search clusters, 7 optimized backend keyword boxes in `series.yaml`).

---

## 3. French Edition (*L'Atlas de la parentalité* — `series/parenthood-atlas/i18n/fr/`) Gold-Master

* **Manuscript Scale:** 15 curated chapters + Quick-Finder front-matter (`59,810` words).
* **Readability & Sentence Cadence:** Kandel-Moles `67.4–74.6` (statutory target $\ge 50.0$), average sentence length `18.0w–20.1w`, max single sentence $\le 38\text{w}$ (`0` outlier sentences).
* **Paragraph De-Walling:** `0` dense paragraphs across all 15 chapters ($\le 135\text{w}$, $\le 6\text{s}$, local Kandel-Moles $\ge 42.0$).
* **Phrasal Poetics:** Poetics score `97.7–99.7`, copula ratio $\le 22.0\%$, `0` nominalization clusters, `0` participial tail-drags, $\le 3$ formulaic negation pivots.
* **Epistemic Hygiene:** `78/78` OKF v0.3 cards cited (`0` orphans), `147` verified BibTeX DOIs, `0` retractions, `7` French public-health footnotes (`[^ch01-fr-folates]`, `[^ch03-fr-naissance]`, `[^ch04-fr-sommeil-securitaire]`, `[^ch04-fr-diversification]`, `[^ch07-fr-ecrans]`, `[^ch08-fr-modes-accueil]`, `[^ch13-fr-conges-parentaux]`).
* **Publishing Suite:**
  * Reader Edition A4 PDF (`110` pages, 456 KB) + Reader HTML.
  * Amazon KDP 6"×9" Trade Paperback Interior PDF (`166` pages, 511 KB, `147/147` co-located bottom footnotes, `0` leaks).
  * Amazon KDP Full-Wrap Cover PDF (`12.6238" x 9.2500"`, `465.5 DPI` front art, white and cream variants).
  * Kindle EPUB 3.0 (`2.8 MB`, 17 valid XHTML docs, 369 noterefs, 149 footnote asides).
  * Telemetry: `data/gkp_parenting_fr_seed.csv` (25 search clusters, 541,600 monthly volume, 7 optimized backend keyword boxes in `series.yaml`).
  * Audiobook Dry-Run: `50,074` spoken words, 755 blocks, `333.8` min (5.56 hrs) estimated narration.

---

## 4. Multilingual Publishing Matrix (All Editions Verified)

| Dimension | English Edition (*Parenthood: The Atlas*) | Spanish Edition (*El atlas de la crianza*) | French Edition (*L'Atlas de la parentalité*) |
| :--- | :--- | :--- | :--- |
| **Directory** | `series/parenthood-atlas/` | `series/parenthood-atlas/i18n/es/` | `series/parenthood-atlas/i18n/fr/` |
| **Language Code** | `en` | `es` | `fr` |
| **Total Words** | 56,633 words | 62,053 words | 59,810 words |
| **Readability Metric** | Flesch-Kincaid `8.2–9.4` | Szigriszt-Pazos `55.6–70.9` | Kandel-Moles `67.4–74.6` |
| **Dense Paragraphs** | **0** | **0** | **0** |
| **Outlier Sentences** | **0** | **0** | **0** |
| **Poetics Score** | `98.4–99.7` | `97.6–99.2` | `97.7–99.7` |
| **OKF Cards Cited** | `78/78` (0 orphans) | `78/78` (0 orphans) | `78/78` (0 orphans) |
| **Regional Footnotes**| Base UK/US DOIs | 7 Spanish Institutional | 7 French Institutional |
| **KDP 6"×9" Pages** | 154 pages | 165 pages | 166 pages |
| **Reader Edition** | 103 pages A4 | 112 pages A4 | 110 pages A4 |
| **Cover DPI** | 465.5 DPI | 465.5 DPI | 465.5 DPI |
| **EPUB 3.0** | Validated (EPUBCheck) | Validated (EPUBCheck) | Validated (EPUBCheck) |
