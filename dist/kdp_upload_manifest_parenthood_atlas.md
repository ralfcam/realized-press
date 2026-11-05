# Amazon KDP Upload Manifest & Pre-Flight Specifications
## *Parenthood: The Atlas* (`series/parenthood-atlas`) & *El atlas de la crianza* (`series/parenthood-atlas/i18n/es`)
**BWE Version:** `v1.2.0` (`ARC-100`) | **Date:** 2026-11-05 | **Release Status:** Gold-Master (`EN` & `ES`)

---

## 1. Deliverables Inventory & SHA-256 Checksums

All interior and cover wrap files are pre-flight validated against Amazon KDP print specifications:
- Zero blank interior pages (`159/159` EN, `167/167` ES).
- Dynamic same-page bottom footnotes in `8.5pt` (`10.5pt` leading) apparatus register with `0.4pt` partial-width separator rule and zero `Evidence Card:` / `Grade:` leaks.
- 465.5 Effective DPI cover artwork ($\ge 300\text{ DPI}$ print gate).
- Mandatory $2.0" \times 1.2"$ ($50.8 \times 30.48\text{ mm}$) ISBN Barcode Reserve Box on lower-right back cover.
- Rotated spine text enabled ($N \ge 79\text{ pages}$, preserving $0.0625"$ hinge margin).

| Edition | Deliverable Path | File Size | Interior Pages | Format / Stock | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp-6x9.pdf` | `479,979` bytes | 159 pp. | 6"×9" Interior | `4fd9a3ef60cb48fca09fde6bb26417e76ce15876f152939ac72497cc27066ceb` |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp-cover.pdf` | `7,378,288` bytes | 159 pp. | Full Wrap (White) | `fac5c1745f5147db8e35eb98149b3d4264416fd1e9fb0a416cdeb2dff848ee1b` |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp-cover-cream.pdf` | `7,378,287` bytes | 159 pp. | Full Wrap (Cream) | `7d09731f52b7a8b9890b82659d861f524dc342309aac83e1922db95e0923234f` |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp.epub` | `2,804,863` bytes | 15 ch. | Kindle EPUB 3.0 | `c8d60dc7399baaaa9d6df858222983d8974b3002ff79f9a8db72688b3c8952bc` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp-6x9.pdf` | `504,052` bytes | 167 pp. | 6"×9" Interior | `8f88bfe27403da682b9e2597d61e3d54d8f7f2ca7e910b7fd15b1fb2be7d3d40` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp-cover.pdf` | `7,376,383` bytes | 167 pp. | Full Wrap (White) | `bba3129bd3e919c0c2bac93034d501ec27ff0b4c61296389a846de7fe436a563` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp-cover-cream.pdf` | `7,376,375` bytes | 167 pp. | Full Wrap (Cream) | `267e3f05d5bc9b34230bac33654d0dd0f44ebf2342e7c09afbd9d2ddfd23de68` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp.epub` | `2,817,638` bytes | 15 ch. | Kindle EPUB 3.0 | `fbfffeaa6e4cb32e2cec928365484bdf5a19af8fc355c4d0db0dc10f347f8265` |

---

## 2. Physical Print Specifications (KDP Paperback & Hardcover)

### English Edition (`159` interior pages)
- **Trim Size:** 6.00" × 9.00" (152.4 mm × 228.6 mm)
- **Bleed:** 0.125" (3.175 mm) on top, bottom, and outside edges
- **Margins:** Inside Gutter 0.787" (20.0 mm), Outside 0.591" (15.0 mm), Top/Bottom 0.709" (18.0 mm)
- **White Paper Stock (`0.002252"` / page):**
  - **Spine Width:** $0.3581"$ ($9.09\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6081" \times 9.2500"$ ($320.24 \times 234.95\text{ mm}$)
- **Cream Paper Stock (`0.002500"` / page):**
  - **Spine Width:** $0.3975"$ ($10.10\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6475" \times 9.2500"$ ($321.25 \times 234.95\text{ mm}$)
- **Spine Text Status:** **Included** ($159 \ge 79\text{ pages}$, centered rotated title, author, and publisher)

### Spanish Edition (`167` interior pages)
- **Trim Size:** 6.00" × 9.00" (152.4 mm × 228.6 mm)
- **Bleed:** 0.125" (3.175 mm) on top, bottom, and outside edges
- **Margins:** Inside Gutter 0.787" (20.0 mm), Outside 0.591" (15.0 mm), Top/Bottom 0.709" (18.0 mm)
- **White Paper Stock (`0.002252"` / page):**
  - **Spine Width:** $0.3761"$ ($9.55\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6261" \times 9.2500"$ ($320.70 \times 234.95\text{ mm}$)
- **Cream Paper Stock (`0.002500"` / page):**
  - **Spine Width:** $0.4175"$ ($10.60\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6675" \times 9.2500"$ ($321.75 \times 234.95\text{ mm}$)
- **Spine Text Status:** **Included** ($167 \ge 79\text{ pages}$, centered rotated title, author, and publisher)

---

## 3. Metadata & Backend Keywords (Amazon KDP Setup)

### English Edition (`EN`)
- **Book Title:** `Parenthood: The Atlas`
- **Subtitle:** `What Science Knows, What It Doesn't, and Where Art Begins from Conception to Age Three`
- **Author:** `Jose Campos`
- **Publisher / Imprint:** `Realized Press`
- **BISAC Categories:**
  1. `FAM034000` — FAMILY & RELATIONSHIPS / Parenting / General
  2. `PSY004000` — PSYCHOLOGY / Developmental / Child
  3. `SCI049000` — SCIENCE / Life Sciences / Human Anatomy & Physiology
- **Backend Search Keywords (7 slots, strictly $\le 49$ UTF-8 bytes each):**
  1. `sleep training peanut butter baby cry out non cio` (49 bytes)
  2. `sharing room sids toddler hitting biting home mom` (49 bytes)
  3. `cortisol attachment tantrums calm down tongue tie` (49 bytes)
  4. `screen speech delay montessori toys pretend safe` (48 bytes)
  5. `conversational turns play intelligence formula iq` (49 bytes)
  6. `pregnancy stress hurt object permanence hear womb` (49 bytes)
  7. `section microbiome skin neural tube window set go` (49 bytes)

### Spanish Edition (`ES`)
- **Book Title:** `El atlas de la crianza`
- **Subtitle:** `Lo que demuestra la ciencia, lo que aún ignora y dónde comienza el arte, desde la concepción hasta los tres años`
- **Author:** `Jose Campos`
- **Publisher / Imprint:** `Realized Press`
- **BISAC Categories:**
  1. `FAM034000` — FAMILY & RELATIONSHIPS / Parenting / General
  2. `PSY004000` — PSYCHOLOGY / Developmental / Child
  3. `SCI049000` — SCIENCE / Life Sciences / Human Anatomy & Physiology
- **Backend Search Keywords (7 slots, strictly $\le 49$ UTF-8 bytes each):**
  1. `dejar panal control ferber sueno llanto baby led` (48 bytes)
  2. `esfinteres senales colecho seguro muerte mi hijo` (48 bytes)
  3. `rabietas berrinches calmar subita lactante dos` (46 bytes)
  4. `pantallas retraso habla pegan muerden limites blw` (49 bytes)
  5. `turnos conversacionales juego simbolico ficcion` (47 bytes)
  6. `disciplina nalgadas introduccion cacahuate acido` (48 bytes)
  7. `juguetes montessori lactancia materna formula dia` (49 bytes)

---

## 4. Back-Cover Copy & Product Descriptions

### English Product Description
```
Parenthood: The Atlas is a longitudinal evidence atlas of developmental science from roughly one year before conception through age three. It distinguishes three non-collapsible domains: what science can observe, what interpretation suggests, and what the relational art of caregiving demands.

Rather than prescriptive parenting manuals or single-study alarmism, this work presents a systematic natural-history map across fifteen curated developmental milestones. Every claim is calibrated to verified empirical certainty grades under the Open Knowledge Format (OKF v0.3).

From the placental filtration of maternal cortisol to the emergence of communicative turns, from neonatal transition physiology to the fragile mechanics of toddler self-regulation, The Atlas offers parents and practitioners an unpadded, evidence-anchored foundation.

Key Epistemic Attributes:
- 15 curated developmental chapters from preconception through age three.
- Calibrated claim verbs strictly matching underlying evidence certainty grades.
- Systematic genetically informed (GI) confounding audits across all 78 evidence cards.
- Governed by Open Knowledge Format (OKF v0.3) and verified primary DOIs with zero retractions.
```

### Spanish Product Description
```
El atlas de la crianza es un mapa longitudinal de la evidencia sobre el desarrollo infantil, desde aproximadamente un año antes de la concepción hasta los tres años. Separa tres planos que no deben fundirse: lo que la ciencia puede observar, lo que la interpretación sugiere y lo que el arte relacional del cuidado exige.

En lugar de manuales prescriptivos o alarmas basadas en un solo estudio, esta obra traza un mapa de historia natural a lo largo de quince hitos del desarrollo. Cada afirmación está calibrada al grado de certeza empírica verificado bajo el Open Knowledge Format (OKF v0.3).

Desde el filtro placentario del cortisol materno hasta la aparición de los turnos de conversación, desde la fisiología de la transición neonatal hasta la frágil mecánica de la autorregulación del niño pequeño, El atlas ofrece a madres, padres y profesionales una base sin relleno, anclada en la evidencia.

Atributos Epistémicos Clave:
- 15 capítulos de desarrollo, desde la preconcepción hasta los tres años.
- Verbos de afirmación calibrados al grado de certeza de la evidencia.
- Auditorías de confusión genética (GI) en las 78 fichas de evidencia.
- Regido por Open Knowledge Format (OKF v0.3) y DOI verificados sin retractaciones.
```
