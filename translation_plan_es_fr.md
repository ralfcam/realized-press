# Realized Press Multilingual Pipeline: Two-Pass Translation & Posterior Phrasal-Sculpting Plan (`ES` / `FR`)

**Status:** Active (`i18n/es` in `ARC-105`; `i18n/fr` paused per compute guardrails until Stage 4)
**Governing Issues:** `ARC-76`, `ARC-77`, `ARC-81`, `ARC-101`, `ARC-104`, `ARC-105`

---

## 1. Core Architectural Rule: The Two-Pass Localization Standard

No book translation in Realized Press is complete after semantic and epistemic transfer alone. Because first-pass translation from English into Romance languages inevitably introduces **syntactic calques**, **copula inflation (`ser / estar / haber / tener`)**, **`de + noun` genitive chains**, **trailing gerunds (`gerundio de posterioridad`)**, and **15–20% paragraph length expansion** over the 135-word visual geometry cap, every localized edition must execute in **two distinct passes**:

### Pass 1 — Epistemic, Lexical & Regional Apparatus Transfer
1. **Citation & Epistemic Parity:** Preserve 100% of canonical inline `[^chXX-...]` footnote anchors and calibrate bold claim verbs to each OKF v0.3 card's `certainty_grade` and `attenuation_tier`.
2. **Regional Clinical & Legal Apparatus:** Inject target-market regional footnotes (`[^chXX-es-...]`) in `## Notes` (e.g., AEMPS/SEGO periconceptional folate & iodine, SNS crib safety, AEP screen time, Ministerio de Educación 0–3 *escuelas infantiles*, RDL 6/2019 16-week paid parental leave).
3. **Split-Register Jargon Isolation & Search-Intent Weaves:** Relocate all clinical terms in `i18n/<lang>/style/jargon-to-notes.yml` into `## Notes` and weave localized search-intent vocabulary from `i18n/<lang>/style/lexicon.yaml`.

### Pass 2 — Posterior Native Phrasal-Sculpting (`--micro-strict --poetics --lang <lang>`)
With the **Epistemic Skeleton frozen** (`bwe/style_sculptor.py`), run a dedicated native phrasal-sculpting pass governed by `i18n/<lang>/style/phrasal-poetics.yml` and verified by:
```powershell
python scripts/audit_manuscript.py series/parenthood-atlas/i18n/es --bestseller-strict --graph-strict --micro-strict --poetics --lang es
```

1. **Kinetic & Pronominal Verbs Over Copulas (`Copula Ratio <= 38%`):** Replace static `es / está / hay / tiene` predicates and passive calques with physical, pronominal, and kinetic verbs drawn from each card's `canonical_metaphors` (*intercepta, desactiva, blinda, sella, amortigua, encarrila, desborda, engulle*).
2. **Pruning Genitive Chains & Nominalization Clusters (`0` Clusters):** Eliminate clauses stacking $>2$ abstract suffixes (`-ción`, `-sión`, `-miento`, `-dad`, `-encia`, `-ismo`).
3. **Purging Trailing Gerunds & Negation-Pivot Clichés:** Eliminate sentence-ending gerunds (`, destacando...`, `, subrayando...`, `, facilitando...`, `, demostrando...`) and cap formulaic negation pivots (*"no es X, sino Y"*) at $\le 3$ per chapter.
4. **Native Clausal Counterpoint (`Cadence Flags = 0`, $\sigma \ge 3.0\text{w}$):** Alternate sweeping periodic setups with crisp 6-to-10-word declarative hinges.
5. **De-Walling Expanded Paragraphs (`<= 135w`, `<= 6s`, Local Readability `>= 42.0`):** Tighten prepositional bloat and split every narrative paragraph exceeding `135 words` or `6 sentences` at its natural causal hinge so Dense Paragraph advisories equal `0`.
