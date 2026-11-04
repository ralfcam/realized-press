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
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "MRC Vitamin Study (1991) randomized controlled trial (N = 1,817 women at high risk of neural tube defect recurrence)"
  - "72% relative risk reduction for neural tube defects with 4mg/day periconceptional folic acid"
  - "population-wide grain fortification reduced spina bifida and anencephaly incidence by 28-35% across the United States"
relates_to_cards:
  - "EXTENDS:prenatal-neural-construction"
  - "BOUNDS:preconception-nutrition-beyond-folate"
---


# Periconceptional Folic Acid and Neural-Tube Defects

> Domain: pregnancy / feeding
> Last updated: 2026-09-16
> Status: Stable for the *narrow* NTD-prevention claim (`stable-candidates--replication-note.md`). Other-anomaly and cognition claims remain Low.

## What We Know

Daily periconceptional folic acid (alone or with other vitamins) reduces neural-tube-defect-affected pregnancy relative to no folate. The Cochrane synthesis of five trials reports RR 0.31 (95% CI 0.17–0.58; 6,708 births; high-quality evidence). This is a structural embryonic outcome, not a general intelligence or “optimal development” claim.

## How Confident We Are

**Grade**: High for NTD prevention with periconceptional folic acid. **Low** for other congenital anomalies (Cochrane: clefts and cardiac defects, low-quality, CIs crossing 1) and for later cognition.

## Evidence and Causal Assessment

- Landmark RCT: MRC Vitamin Study (1991) established prevention of NTD *recurrence* with periconceptional folic acid.
- Independent first-occurrence RCT: Czeizel & Dudás (1992), *NEJM*, Hungarian periconceptional multivitamin trial; no NTD in the folic-acid arm versus six in the control arm among women without a prior NTD pregnancy.
- De-Regil et al. (2015) Cochrane review: five RCTs, 6,708 births, RR 0.31 (0.17–0.58) for NTDs; recurrence RR 0.34 (0.18–0.64). Dose subgroup (0.4 mg vs higher) did not change the conclusion. Cochrane `new_version` on this record is a successor review, not a retraction.
- WHO antenatal-care guidance recommends daily iron and folic acid as a public-health measure; that guideline is adjacent framework, not this card’s identification.

## Effect Size and Persistence

Large relative-risk reduction for NTD. Persistence is binary at the structural level (defect present or not). There is no license to carry this effect size into IQ, school achievement, or all birth defects.

## Bias, Heterogeneity, and Confounding

GI attenuation: **n/a** for NTD. Baseline fortification and population folate status change the absolute benefit. Trials are older and often recurrence-focused; first-occurrence evidence is now represented by Czeizel & Dudás as well as the Cochrane pool. Adherence, timing (must cover neural-tube closure), and access are implementation issues, not reasons to doubt the core RCT result.

## What Remains Uncertain

Optimal dose in already-fortified populations; effects of isolated versus combined micronutrients on later neurodevelopment; consequences of over-supplementation.

## What This Does Not Mean

Does not mean perfect supplementation guarantees typical development, that an NTD implies parental nutritional failure in every case, or that folic acid is a general brain-optimization tool.

## What Action Is Reasonably Justified

Population fortification and periconceptional folic acid as recommended antenatal care are justified on NTD-prevention grounds. Supplement maximalism and cognitive-enhancement framing are not.

## Sources

- De-Regil et al. (2015), Cochrane Database of Systematic Reviews
- MRC Vitamin Study Research Group (1991), *Lancet*
- Czeizel & Dudás (1992), *New England Journal of Medicine*
