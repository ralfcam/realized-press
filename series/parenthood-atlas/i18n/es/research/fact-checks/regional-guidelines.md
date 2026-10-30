# Regional health-guideline footnotes — Spanish edition (verification record)

Purpose: the body prose of the Spanish edition stays **universal** (it follows the canonical English chapters and the shared
OKF v0.2 evidence cards). Regional institutional guidance is annotated **only** in chapter-local `## Notes` footnotes whose keys
match `ch\d\d-es-<slug>` (see `style/lexicon.yaml → chapter_apparatus.regional_footnote_key_pattern`).

Verified on 2026-10-30 with `perplexity_ask` (Phase 1/2 routing). Institutional documents have no DOI, so they are cited by issuer,
exact title and year; **no year is stated unless the issuer's page or a retrieved copy confirmed it.** All URLs below are canonical issuer URLs (no search-grounding redirect links).

## Verification table

| Claim used in a footnote | Issuer / document (year) | URL | Status |
| :--- | :--- | :--- | :--- |
| Folic acid 400 µg/day from ≥1–2 months before conception through 12 weeks; 4 mg/day after a previous neural-tube-defect pregnancy | Ministerio de Sanidad, *Guía para la Prevención de Defectos Congénitos* (2006); Ministerio de Sanidad/GuíaSalud, *Guía de práctica clínica de atención en el embarazo y puerperio* (2014); SEGO, *Recomendaciones ácido fólico y yodo, preconcepcional, embarazo y lactancia* (2013) | https://portal.guiasalud.es/egpc/embarazo-recomendaciones/ · https://www.sanidad.gob.es/profesionales/prestacionesSanitarias/publicaciones/DefectosCongenitos.htm | verified (3 sources agree) |
| Iodine is **not** uniform: 2014 guideline = 200 µg/day potassium iodide only if diet is insufficient (3 dairy servings + 2 g iodized salt as benchmark); PrevInfad/AEPap = no routine supplementation; SEGO = recommends 200 µg/day | same GuíaSalud guideline; AEPap/PrevInfad, *Suplementos de yodo en la gestación y la lactancia* (2014; PDF posted 2017); SEGO (2013) | https://previnfad.aepap.org/sites/default/files/2017-04/previnfad_yodoemb.pdf | verified; **contradicts the brief's assumption of a single AEP iodine rule** |
| Uninterrupted skin-to-skin after birth for healthy newborns and early breastfeeding start (preferably within the first hour) | Ministerio de Sanidad, *Guía de Práctica Clínica sobre la Atención al Parto Normal* (2010) | https://www.sanidad.gob.es/areas/calidadAsistencial/estrategias/atencionPartoNormal/docs/guiaPracParMujer.pdf | verified |
| Exclusive breastfeeding for about 6 months; early skin-to-skin for all newborns | AEP Comité de Lactancia Materna, *Recomendaciones sobre lactancia materna* (2012) | https://www.aeped.es/publicaciones/protocolos/recomendaciones-sobre-lactancia-materna | verified |
| AEP safe-sleep core: supine, own cot, in parents' room, near the bed, under 6 months; sidecar cot as a separate surface | AEP Comité de Lactancia Materna y Grupo de Trabajo de Muerte Súbita, *Colecho, síndrome de muerte súbita del lactante y lactancia materna. Recomendaciones actuales de consenso* (2014) | https://www.aeped.es/publicaciones/protocolos/colecho-sindrome-muerte-subita-lactante-y | verified |
| AEP advises **against** bed-sharing: <3 months; prematurity/low birth weight; smoking, alcohol, drugs or sedatives; extreme tiredness; soft surface, waterbed, sofa/armchair; other people or children in the bed | same AEP 2014 consensus | same | verified. **The AEP does not declare bed-sharing categorically safe for breastfed infants >3 months** (it lists circumstances where it should not be recommended) |
| IHAN-España issued a specific statement on co-sleeping and breastfeeding | IHAN-España, *Comunicado de IHAN-España sobre la práctica del colecho y el amamantamiento* (2013) | https://www.ihan.es/recursos/recomendaciones/ | title/year verified; **content not verified** → cited by title only |
| PrevInfad: evidence on bed-sharing in breastfed infants without other risk factors is uncertain | AEPap/PrevInfad, monograph on sudden infant death | https://previnfad.aepap.org/monografia/muerte-subita-lactante | verified (summary level) |
| Complementary feeding around 6 months when ready, not before 4 months and not beyond ~26 weeks; do not delay allergenic foods to prevent allergy; gluten between 4 and 11 months; BLW choking caution | AEP (Comités de Lactancia Materna y de Nutrición), *Recomendaciones de la Asociación Española de Pediatría sobre la alimentación complementaria* (2018) | https://www.aeped.es/publicaciones/protocolos/recomendaciones-aep-sobre-alimentacion | verified |

### Deliberately NOT claimed (could not be verified)
- That the AEP/IHAN endorses "risk-minimized co-sleeping in breastfed infants over 3 months" as safe.
- A single AEP/Ministerio iodine rule applicable to every pregnancy.
- A vitamin K recommendation in Ch 03 (the English Ch 03 body does not discuss vitamin K, so no footnote is added).
- Any peanut-specific AEP recommendation matching the LEAP 4–11 month window (the AEP text covers egg, fish and gluten, and says allergenic foods should not be delayed).

## Exact footnote definitions (copy verbatim into the chapter `## Notes`)

Use the inline anchor `[^<key>]` at the sentence named in each entry. Keep the literal English structural key `Evidence Card:`.

### Chapter 1 — key `ch01-es-folato-yodo` (anchor: end of the sentence in Movement III that gives the 400 µg/day folic-acid recommendation)

```
[^ch01-es-folato-yodo]: Contexto regional (España): las guías españolas coinciden en recomendar 400 µg diarios de ácido fólico desde al menos uno o dos meses antes de la concepción y hasta la semana 12 del embarazo, y 4 mg diarios cuando hubo un embarazo previo con defecto del tubo neural (Ministerio de Sanidad, *Guía para la Prevención de Defectos Congénitos*, 2006; Ministerio de Sanidad y GuíaSalud, *Guía de práctica clínica de atención en el embarazo y puerperio*, 2014; SEGO, *Recomendaciones ácido fólico y yodo, preconcepcional, embarazo y lactancia*, 2013). Sobre el yodo no existe una postura única: la guía clínica de 2014 propone 200 µg diarios de yoduro potásico solo cuando la dieta no alcanza, PrevInfad (AEPap, 2014) no recomienda la suplementación sistemática y la SEGO (2013) sí la recomienda; conviene decidirlo con el profesional que lleva el embarazo. Evidence Card: `evidence-cards/prenatal-folate-ntd.md`.
```

### Chapter 3 — key `ch03-es-piel-lactancia` (anchor: end of the paragraph in Movement IV that summarizes what skin-to-skin contact does)

```
[^ch03-es-piel-lactancia]: Contexto regional (España): el contacto piel con piel ininterrumpido tras el parto en recién nacidos sanos y el inicio de la lactancia, preferiblemente durante la primera hora, figuran en la *Guía de Práctica Clínica sobre la Atención al Parto Normal* (Ministerio de Sanidad, 2010). El Comité de Lactancia Materna de la AEP (*Recomendaciones sobre lactancia materna*, 2012) aconseja además la lactancia materna exclusiva durante unos seis meses. Estas indicaciones describen buenas prácticas de atención; no convierten el piel con piel en una condición para el apego (véase el texto). Evidence Card: `evidence-cards/skin-to-skin-immediate-physiology.md`.
```

### Chapter 4 — key `ch04-es-colecho` (anchor: end of the sentence/paragraph on room-sharing and safe sleep in Movement II)

```
[^ch04-es-colecho]: Contexto regional (España): el consenso de la AEP (*Colecho, síndrome de muerte súbita del lactante y lactancia materna. Recomendaciones actuales de consenso*, Comité de Lactancia Materna y Grupo de Trabajo de Muerte Súbita, 2014) sitúa el sueño más seguro del lactante menor de seis meses boca arriba, en su propia cuna, en la habitación de los padres y cerca de la cama; para las familias que desean cercanía nocturna propone la cuna de colecho (cuna adosada), una superficie independiente acoplada a la cama. Reconoce que compartir cama puede favorecer la lactancia, pero no lo recomienda cuando el bebé tiene menos de tres meses, nació prematuro o con bajo peso, algún progenitor fuma o ha consumido alcohol, drogas o fármacos sedantes, hay cansancio extremo, la superficie es blanda o es un sofá o sillón, o comparten la cama otras personas o niños. La AEP no declara el colecho seguro por sí mismo en lactantes amamantados mayores de tres meses: enumera las circunstancias en que no debe recomendarse. IHAN-España publicó un comunicado específico sobre colecho y amamantamiento (2013) y PrevInfad (AEPap) señala que la evidencia sobre colecho en lactantes amamantados sin otros factores de riesgo es incierta. Evidence Card: `evidence-cards/safe-sleep-supine-room-sharing.md`.
```

### Chapter 4 — key `ch04-es-alimentacion-complementaria` (anchor: end of the sentence in Movement II about introducing peanut foods at 4–11 months / allergen timing)

```
[^ch04-es-alimentacion-complementaria]: Contexto regional (España): la AEP (Comités de Lactancia Materna y de Nutrición, *Recomendaciones de la Asociación Española de Pediatría sobre la alimentación complementaria*, 2018) aconseja empezar hacia los seis meses, cuando el bebé muestra señales de estar listo, nunca antes de los cuatro meses ni más tarde de las 26 semanas, y no retrasar los alimentos potencialmente alergénicos con el fin de prevenir alergias; el gluten se recomienda entre los 4 y los 11 meses, preferiblemente hacia los 6 y en pequeñas cantidades al principio. Para la alimentación complementaria dirigida por el bebé advierte del riesgo de atragantamiento con alimentos duros y pequeños (frutos secos enteros, aceitunas, zanahoria o manzana crudas) y de la supervisión constante durante la comida. El ensayo LEAP del texto estudió el cacahuate en lactantes de alto riesgo entre los 4 y los 11 meses; la recomendación española citada no se refiere al cacahuate en particular. Evidence Card: `evidence-cards/early-allergen-introduction-blw.md`.
```
