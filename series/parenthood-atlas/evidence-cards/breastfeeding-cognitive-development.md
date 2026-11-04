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
  - "+7.5 verbal IQ at age 6.5 fading to +1.4 non-significant points at age 16 in PROBIT RCT (N = 17,046)"
  - "sibling-comparison designs attenuate observational IQ differences to null (d < 0.05)"
  - ">50% attenuation under maternal education and socioeconomic controls"
relates_to_cards:
  - "BOUNDS:responsive-feeding-as-regulation"
  - "CONTRASTS:early-allergen-introduction-blw"
---


# Breastfeeding and Cognitive Development

> Domain: feeding
> Last updated: 2026-09-14
> Status: Preliminary (initial literature pass; not yet deeply audited)

## What We Know

Observational studies consistently show a 3-4 IQ-point advantage for breastfed children, but the strongest causal designs (PROBIT cluster-randomized trial follow-up, sibling comparisons) indicate the long-term causal effect for full-term infants is small, concentrated in verbal ability, and may approach zero by adolescence.

## How Confident We Are

**Grade**: Moderate. One of the few developmental questions with an actual large randomized trial, increasing confidence relative to most nutrition/parenting topics, but effect sizes shrank markedly over time and domains.

## Evidence and Causal Assessment

- PROBIT (Belarus, N=17,046 randomized at the hospital/cluster level) found infants in the breastfeeding-promotion arm scored 5.9 points higher full-scale IQ (not significant) and 7.5 points higher verbal IQ (significant) at age 6.5.
- 16-year PROBIT follow-up (79.5% retention, N=13,557) found no significant difference in overall neurocognitive function; only verbal function remained significantly higher (+1.4 points).
- Sibling-comparison studies (Der 2006; Colen & Ramey 2014) using within-family designs to remove shared confounders found no significant cognitive differences between breastfed and non-breastfed siblings.

## Effect Size and Persistence

Randomized estimate at age 6.5: +5.9 full-scale IQ (ns), +7.5 verbal IQ (significant). At age 16: overall effect non-significant; verbal effect fades to +1.4 points. Sibling designs: null. Best summary estimate for full-term, adequately nourished infants: 0-2 IQ points, likely concentrated in verbal domain, with fade-out over adolescence.

## Bias, Heterogeneity, and Confounding

GI attenuation: **largely confounded (>50%)** (observational IQ gains largely attenuate in sibling-comparison designs and PROBIT trials).

**Partially-to-largely confounded** relative to observational estimates: PROBIT's cluster-randomized design removes maternal-choice confounding, yet the effect that remains after 16 years is far smaller than initial observational estimates (~3-4 points) and disappears in sibling comparisons. Findings may not generalize to preterm or malnourished populations.

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
