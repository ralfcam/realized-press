---
type: Evidence Card
title: "Periconceptional Folic Acid and Neural-Tube Defects"
description: "Randomized and systematic-review evidence shows periconceptional folic acid substantially reduces neural-tube-defect risk; this does not generalize to all anomalies or to intelligence."
tags: [pregnancy, nutrition, rct]
status: stable
confidence: high-ntd; low-other-anomalies-cognition
generated: { by: agent:cursor, at: 2026-09-15T17:00:00Z }
stale_after: 2027-03-15T00:00:00Z
atlas_domains: [pregnancy, nutrition]
chapter_hooks: [evidence, boundary]
sources:
  - id: deregil-2015-cochrane
    resource: https://doi.org/10.1002/14651858.CD007950.pub3
    title: "De-Regil et al. (2015), Cochrane review of periconceptional folate"
  - id: mrc-ntd-1991
    resource: https://doi.org/10.1016/0140-6736(91)90133-A
    title: "MRC Vitamin Study Research Group (1991), Lancet, NTD prevention trial"
  - id: czeizel-dudas-1992
    resource: https://doi.org/10.1056/NEJM199212243272602
    title: "Czeizel & Dudás (1992), NEJM, first-occurrence NTD prevention trial"
  - id: berry-1999-nejm
    resource: https://doi.org/10.1056/NEJM199911113412001
    title: "Berry et al. (1999), NEJM, prevention of neural-tube defects with 400 mcg daily folic acid in China"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "Wald et al. / MRC Vitamin Study (1991, Lancet; N = 1,817 randomized, 1,195 completed pregnancies): 4 mg/day folic acid reduced NTD recurrence by 72% (RR 0.28, 95% CI 0.12-0.71; 3.5% to 1.0%, ARR 2.5 percentage points)"
  - "Berry et al. (1999, NEJM; N = 247,831 pregnancies): 400 mcg/day folic acid alone cut first-occurrence NTDs by 79% in high-baseline northern China (4.8 to 1.0 per 1,000; 85% with >80% compliance) and 41% in southern China (1.0 to 0.6 per 1,000)"
  - "Czeizel & Dudás (1992, NEJM; N = 4,156 known pregnancy outcomes): periconceptional multivitamin with 800 mcg folic acid yielded 0/2,104 vs 6/2,052 first-occurrence NTDs (P = 0.029)"
relates_to_cards:
  - "EXTENDS:prenatal-neural-construction"
  - "BOUNDS:preconception-nutrition-beyond-folate"
---


# Periconceptional Folic Acid and Neural-Tube Defects

> Domain: pregnancy / feeding
> Last updated: 2026-11-13
> Status: Stable for the *narrow* NTD-prevention claim (`stable-candidates--replication-note.md`), separating high-dose recurrence (4 mg) from general-population first-occurrence (400-800 mcg). Other-anomaly and cognition claims remain Low.

## What We Know

Daily periconceptional folic acid reduces neural-tube-defect (NTD) risk relative to no supplementation, but the clinical dose differs sharply by baseline risk. In **high-risk recurrence** (prior NTD-affected pregnancy), **4 mg/day** cut NTDs from **3.5% to 1.0%** (**72% relative reduction**; RR 0.28, 95% CI 0.12–0.71; absolute risk reduction 2.5 percentage points). For **general-population first occurrence**, prevention rests on **400–800 mcg/day**: a multivitamin with **800 mcg** folic acid eliminated NTDs in a Hungarian RCT (`0/2,104` vs `6/2,052`), and **400 mcg/day** of folic acid alone cut first-occurrence NTDs by **79%** in high-baseline northern China and **41%** in low-baseline southern China. The Cochrane synthesis reports **RR 0.31** (95% CI 0.17–0.58; Summary of Findings lists **6,708** across 5 trials). This is a structural embryonic closure outcome within the first ~28 days post-conception, not a general intelligence or "optimal development" claim.

## How Confident We Are

**Grade**: High for NTD prevention with periconceptional folic acid (400–800 mcg/day for first occurrence; 4–5 mg/day under medical supervision for defined high-risk pregnancies). **Low** for other congenital anomalies (Cochrane: clefts and cardiac defects, low-quality, CIs crossing 1) and for later cognition.

## Evidence and Causal Assessment

- **Recurrence RCT — Wald et al. / MRC Vitamin Study Research Group (1991, *Lancet*, N = 1,817 randomized; 1,195 completed pregnancies):** Established prevention of NTD *recurrence* with **4 mg/day** folic acid (**RR 0.28**, 95% CI 0.12–0.71; risk dropped from 3.5% to 1.0%, 2.5 percentage-point absolute reduction).
- **First-occurrence RCT — Czeizel & Dudás (1992, *NEJM*, N = 4,156 known outcomes of 4,753 confirmed pregnancies):** Tested a periconceptional multivitamin containing **800 mcg** folic acid versus trace elements in women without prior NTDs (`0/2,104` vs `6/2,052` NTDs, `P = 0.029`). Because the intervention combined folic acid with other micronutrients, single-nutrient isolation awaited China's community intervention.
- **First-occurrence single-nutrient cohort intervention — Berry et al. (1999, *NEJM*, China–U.S. Collaborative Project, N = 247,831 pregnancies):** Evaluated **400 mcg/day** folic acid **alone** without other vitamins. Periconceptional use lowered NTDs by **79%** in northern China (31,960 pregnancies; 4.8 to 1.0 per 1,000; **85%** among women with >80% pill compliance) and **41%** in southern China (215,871 pregnancies; 1.0 to 0.6 per 1,000; **40%** with >80% compliance).
- **Cochrane pooling — De-Regil et al. (2015, CD007950):** Summary of Findings reports **RR 0.31** (95% CI 0.17–0.58; listed as **6,708** across 5 trials), pooling four recurrence trials (`RR 0.34`, 95% CI 0.18–0.64, `n = 1,846`) with first-occurrence data from the Hungarian randomized series (`Czeizel 1994`, `n = 5,358` randomized). Cochrane `new_version` on this record is a successor review, not a retraction.

## Effect Size and Persistence

Large relative-risk reduction for NTD (`72%` recurrence reduction with 4 mg; `79%` north / `41%` south first-occurrence reduction with 400 mcg alone). Persistence is binary at the structural level (neural tube closes cleanly by week 4 post-conception or does not). Absolute risk reduction depends strongly on baseline folate status (`4.8 to 1.0 per 1,000` in folate-poor northern China vs `1.0 to 0.6 per 1,000` in folate-replete southern China).

## Bias, Heterogeneity, and Confounding

GI attenuation: **n/a** for NTD prevention (established by factorial randomization in MRC 1991, Hungarian RCTs, and prospective periconceptional registration in Berry 1999). Baseline fortification, maternal folate status, and early timing (prior to gestational day 28 post-conception) explain variation in absolute benefit. Mixing the **4 mg** MRC recurrence trial with **400 mcg** general-population dosing or confusing multivitamin vs isolated folic acid introduces translation bias.

## What Remains Uncertain

Optimal upper supplementation dose in mandatory-fortification populations; whether high-dose folic acid above clinical thresholds alters rare metabolic outcomes; effects of combined micronutrients on later neurodevelopment.

## What This Does Not Mean

Does not mean 4 mg/day is appropriate for the general low-risk population, that supplementation after a missed period prevents neural-tube opening failures already past the ~day-28 closure window, or that folic acid is a general brain-optimization tool.

## What Action Is Reasonably Justified

For the general reproductive-age population capable of pregnancy, **400–800 mcg/day** beginning at least one month before conception alongside food-fortification policy is strongly justified. Higher therapeutic dosing (**4–5 mg/day** under clinician guidance) is reserved for defined high-risk clinical indications: prior NTD-affected pregnancy, valproate or carbamazepine antiepileptic therapy, pre-gestational type 1/2 diabetes, or severe malabsorption syndromes.

## Sources

- De-Regil et al. (2015), *Cochrane Database of Systematic Reviews* (DOI: [10.1002/14651858.CD007950.pub3](https://doi.org/10.1002/14651858.CD007950.pub3))
- MRC Vitamin Study Research Group / Wald et al. (1991), *Lancet* (DOI: [10.1016/0140-6736(91)90133-A](https://doi.org/10.1016/0140-6736(91)90133-A))
- Czeizel & Dudás (1992), *New England Journal of Medicine* (DOI: [10.1056/NEJM199212243272602](https://doi.org/10.1056/NEJM199212243272602))
- Berry et al. (1999), *New England Journal of Medicine* (DOI: [10.1056/NEJM199911113412001](https://doi.org/10.1056/NEJM199911113412001))
