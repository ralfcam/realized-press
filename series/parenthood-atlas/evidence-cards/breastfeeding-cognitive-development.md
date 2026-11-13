---
type: Evidence Card
title: "Breastfeeding and Cognitive Development"
description: "PROBIT RCT and sibling-comparison evidence indicate a small, verbal-concentrated, fading causal effect of breastfeeding on IQ."
tags: [feeding, cognition, rct]
status: draft
confidence: moderate
generated: { by: human:jose-campos, at: 2026-09-14T16:11:00Z }
stale_after: 2027-03-14T00:00:00Z
atlas_domains: [feeding, cognition]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: probit-16yr-2018
    resource: https://pmc.ncbi.nlm.nih.gov/articles/PMC5909901/
    title: "16-year follow-up of the PROBIT cluster-randomized trial, PLOS Medicine (2018)"
  - id: sibling-comparison-2006
    resource: https://pmc.ncbi.nlm.nih.gov/articles/PMC1361236/
    title: "Evenhouse & Reilly (2005), sibling comparisons of breastfeeding benefits"
  - id: kramer-2008-probit
    resource: https://pubmed.ncbi.nlm.nih.gov/18458209/
    title: "Kramer et al. (2008), PROBIT IQ outcomes at 6.5 years"
  - id: der-2006-bmj
    resource: https://pmc.ncbi.nlm.nih.gov/articles/PMC1634122/
    title: "Der, Batty & Deary (2006), BMJ, breastfeeding and intelligence"
  - id: colen-ramey-2014
    resource: https://pmc.ncbi.nlm.nih.gov/articles/PMC4077166/
    title: "Colen & Ramey (2014), sibling comparisons of breastfeeding"
attenuation_tier: "largely_confounded_>50%"
quantitative_anchors:
  - "+7.5 WASI verbal IQ at age 6.5 (95% CI +0.8 to +14.3; Kramer et al. 2008) fading in PROBIT at age 16 (N = 17,046 randomized; 13,557 assessed = 79.5%)"
  - "Yang et al. (2018, PLOS Medicine): age-16 verbal function +1.4 baseline-adjusted ITT (95% CI 0.3 to 2.5), +1.5 cluster-adjusted ITT (95% CI -0.04 to 3.0), and +3.5 IV complier effect (95% CI 0.9 to 6.1), with +0.8 global neurocognitive score (95% CI -0.6 to 2.3)"
  - "sibling-comparison designs (Der 2006; Colen & Ramey 2014) attenuate observational IQ differences to null (>50% attenuation under maternal education and SES controls)"
relates_to_cards:
  - "BOUNDS:responsive-feeding-as-regulation"
  - "CONTRASTS:early-allergen-introduction-blw"
---


# Breastfeeding and Cognitive Development

> Domain: feeding
> Last updated: 2026-11-13
> Status: Draft (PROBIT 6.5-year WASI vs 16-year computerized neurocognitive figures and sibling attenuation aligned to primary papers).

## What We Know

Observational studies consistently show a 3-4 IQ-point advantage for breastfed children, but the strongest causal designs (PROBIT cluster-randomized trial follow-up, sibling comparisons) indicate the long-term causal effect for full-term infants is small, concentrated in verbal ability, and largely fades by adolescence.

## How Confident We Are

**Grade**: Moderate. One of the few developmental questions with an actual large randomized trial, increasing confidence relative to most nutrition/parenting topics, but effect sizes shrank markedly over time and domains.

## Evidence and Causal Assessment

- PROBIT (Belarus, N=17,046 randomized at the hospital/cluster level) found infants in the breastfeeding-promotion arm scored +5.9 points higher full-scale WASI IQ (95% CI -1.0 to +12.8, not significant) and +7.5 points higher verbal IQ (95% CI +0.8 to +14.3, significant) at age 6.5 (**Kramer et al., 2008**).
- 16-year PROBIT follow-up (**Yang et al., 2018**, *PLOS Medicine*; 79.5% retention, N=13,557 on a computerized neurocognitive battery rather than WASI IQ) found no statistically significant difference in global neurocognitive score (+0.8 points, 95% CI -0.6 to 2.3) or executive functioning (-0.03 points, 95% CI -1.3 to 1.2). Only **verbal function** retained a modest signal: **+1.4 points** baseline-adjusted intention-to-treat (95% CI 0.3 to 2.5), **+1.5 points** cluster-adjusted ITT (95% CI -0.04 to 3.0), corresponding to a **+3.5 point** instrumental-variable complier estimate (95% CI 0.9 to 6.1) for >=3 months of exclusive breastfeeding.
- Sibling-comparison studies (Der 2006; Colen & Ramey 2014) using within-family designs to remove shared confounders found no significant cognitive differences between breastfed and non-breastfed siblings.

## Effect Size and Persistence

Randomized estimate at age 6.5 (WASI): +5.9 full-scale IQ (ns), +7.5 verbal IQ (significant). At age 16 (computerized battery): global neurocognitive effect +0.8 (ns); verbal function fades to +1.4 baseline-adjusted (+1.5 cluster-adjusted ITT; +3.5 IV). Sibling designs: null. Best summary estimate for full-term, adequately nourished infants: 0-2 points on average, concentrated in the verbal domain, with substantial fade-out by adolescence.

## Bias, Heterogeneity, and Confounding

GI attenuation: **largely confounded (>50%)** (observational IQ gains attenuate substantially in sibling-comparison designs and PROBIT adolescent follow-up).

**Partially-to-largely confounded** relative to observational estimates: PROBIT's cluster-randomized design removes maternal-choice confounding, yet the effect remaining at age 16 is modest in the verbal domain only (+1.4/+1.5 ITT; +3.5 IV), global cognition is null, and sibling comparisons eliminate family-level confounding. Findings may not generalize to preterm or malnourished populations.

## What Remains Uncertain

Whether effects differ meaningfully for preterm infants, low-birthweight infants, or in resource-limited settings where formula-water safety and nutritional adequacy are less assured.

## What This Does Not Mean

Does not support claims that breastfeeding produces large or lifelong IQ gains, nor that formula-feeding meaningfully harms cognitive development in full-term, well-nourished populations.

## What Action Is Reasonably Justified

Breastfeeding promotion is justifiable on other well-established grounds (infection reduction, maternal health, cost), not primarily on cognitive-enhancement grounds for full-term infants in high-resource settings.

## Sources

- Kramer et al. (2008), *Arch Gen Psychiatry*, PROBIT IQ at 6.5 years
- Yang et al. (2018), *PLOS Medicine*, 16-year PROBIT follow-up
- Der, Batty & Deary (2006), *BMJ*, sibling pairs and meta-analysis
- Colen & Ramey (2014), *Soc Sci Med*, sibling comparisons
- Evenhouse & Reilly (2005), sibling comparisons (catalog ID `sibling-comparison-2006`)
