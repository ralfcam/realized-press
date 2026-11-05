# Amazon KDP Upload Manifest & Pre-Flight Specifications
## *Parenthood: The Atlas* (`series/parenthood-atlas`) & *El atlas de la crianza* (`series/parenthood-atlas/i18n/es`)
**BWE Version:** `v1.1.1` (`ARC-99`) | **Date:** 2026-11-05 | **Release Status:** Gold-Master (`EN` & `ES`)

---

## 1. Deliverables Inventory & SHA-256 Checksums

All interior and cover wrap files are pre-flight validated against Amazon KDP print specifications:
- Zero blank interior pages (`152/152` EN, `166/166` ES).
- 465.5 Effective DPI cover artwork ($\ge 300\text{ DPI}$ print gate).
- Mandatory $2.0" \times 1.2"$ ($50.8 \times 30.48\text{ mm}$) ISBN Barcode Reserve Box on lower-right back cover.
- Rotated spine text enabled ($N \ge 79\text{ pages}$, preserving $0.0625"$ hinge margin).

| Edition | Deliverable Path | File Size | Interior Pages | Format / Stock | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp-6x9.pdf` | `556,750` bytes | 152 pp. | 6"×9" Interior | `0fb9b9999542125c5677fdaa4dd83a6914c24dbabfd6ca71be002d0574d177e5` |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp-cover.pdf` | `7,378,284` bytes | 152 pp. | Full Wrap (White) | `bf8514001bb868ed5a7406bf3ed3226648cc7b776a27b69c70ab68e66d21a05f` |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp-cover-cream.pdf` | `7,378,292` bytes | 152 pp. | Full Wrap (Cream) | `944f210048a7bc3a78577c5c1a99fceb1cff2090b35286aa2de4756167d245da` |
| **EN** | `series/parenthood-atlas/publishing/parenthood-atlas-kdp.epub` | `2,806,561` bytes | 15 ch. | Kindle EPUB 3.0 | `af381e93e4f0660ac919d6a1b8e98dac590c7ee08b85f057c7e2fcac5f4a685a` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp-6x9.pdf` | `589,886` bytes | 166 pp. | 6"×9" Interior | `9b4948838b4f5829384e730c46094d96768e8d921b9f3af1e3c866d109a309a8` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp-cover.pdf` | `7,376,384` bytes | 166 pp. | Full Wrap (White) | `76f5aca16b8eda030184355b40102e9171a0bf61bca918c8aefcd37a4c123811` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp-cover-cream.pdf` | `7,376,384` bytes | 166 pp. | Full Wrap (Cream) | `35a4270653cdf4cfda2fbc9156cb44fa3a6e29c3cbb47d77f50cf74bb8d9dd44` |
| **ES** | `series/parenthood-atlas/i18n/es/publishing/parenthood-atlas-kdp.epub` | `2,819,547` bytes | 15 ch. | Kindle EPUB 3.0 | `e37f38645defe61aed985b26425585b4745e98134fe04750ecec98e17efae033` |

---

## 2. Physical Print Specifications (KDP Paperback & Hardcover)

### English Edition (`152` interior pages)
- **Trim Size:** 6.00" × 9.00" (152.4 mm × 228.6 mm)
- **Bleed:** 0.125" (3.175 mm) on top, bottom, and outside edges
- **Margins:** Inside Gutter 0.787" (20.0 mm), Outside 0.591" (15.0 mm), Top/Bottom 0.709" (18.0 mm)
- **White Paper Stock (`0.002252"` / page):**
  - **Spine Width:** $0.3423"$ ($8.69\text{ mm}$)
  - **Total Wrap Dimensions:** $12.5923" \times 9.2500"$ ($319.84 \times 234.95\text{ mm}$)
- **Cream Paper Stock (`0.002500"` / page):**
  - **Spine Width:** $0.3800"$ ($9.65\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6300" \times 9.2500"$ ($320.80 \times 234.95\text{ mm}$)
- **Spine Text Status:** **Included** ($152 \ge 79\text{ pages}$, centered rotated title, author, and publisher)

### Spanish Edition (`166` interior pages)
- **Trim Size:** 6.00" × 9.00" (152.4 mm × 228.6 mm)
- **Bleed:** 0.125" (3.175 mm) on top, bottom, and outside edges
- **Margins:** Inside Gutter 0.787" (20.0 mm), Outside 0.591" (15.0 mm), Top/Bottom 0.709" (18.0 mm)
- **White Paper Stock (`0.002252"` / page):**
  - **Spine Width:** $0.3738"$ ($9.50\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6238" \times 9.2500"$ ($320.65 \times 234.95\text{ mm}$)
- **Cream Paper Stock (`0.002500"` / page):**
  - **Spine Width:** $0.4150"$ ($10.54\text{ mm}$)
  - **Total Wrap Dimensions:** $12.6650" \times 9.2500"$ ($321.69 \times 234.95\text{ mm}$)
- **Spine Text Status:** **Included** ($166 \ge 79\text{ pages}$, centered rotated title, author, and publisher)

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
