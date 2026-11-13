---
type: Evidence Card
title: "Paternal Age and De Novo Mutation Rate"
description: "De novo single-nucleotide mutations in offspring increase linearly with paternal age at conception; this establishes a biological germline mutation rate, not an individual psychiatric or cognitive forecast for a child."
tags: [preconception, genetics, paternal]
status: draft
confidence: high-mutation-rate; moderate-sibling-hr; low-forecast
generated: { by: agent:antigravity, at: 2026-10-21T01:10:00Z }
stale_after: 2027-03-15T00:00:00Z
atlas_domains: [preconception, pregnancy, genetics]
chapter_hooks: [anomaly, boundary]
sources:
  - id: kong-2012-nature
    resource: https://doi.org/10.1038/nature11396
    title: "Kong et al. (2012), Nature, rate of de novo mutations and father's age"
  - id: jonsson-2017-mutations
    resource: https://doi.org/10.1038/nature24018
    title: "Jónsson et al. (2017), Nature, parental influence on de novo mutations in 1,548 trios"
  - id: donofrio-2014-paternal-age
    resource: https://doi.org/10.1001/jamapsychiatry.2013.4525
    title: "D'Onofrio et al. (2014), JAMA Psychiatry, paternal age at childbearing and offspring psychiatric and academic morbidity"
  - id: gratten-2016-ng
    resource: https://doi.org/10.1038/ng.3577
    title: "Gratten et al. (2016), Nature Genetics, risk of psychiatric illness from advanced paternal age is not predominantly from de novo mutations"
  - id: janecka-2017-tp
    resource: https://doi.org/10.1038/tp.2016.294
    title: "Janecka et al. (2017), Translational Psychiatry, advanced paternal age effects in neurodevelopmental disorders"
  - id: petersen-2011-ajp
    resource: https://doi.org/10.1176/appi.ajp.2010.10020252
    title: "Petersen, Mortensen & Pedersen (2011), Am J Psychiatry, paternal age at birth of first child and risk of schizophrenia"
  - id: hassold-hunt-2001
    resource: https://doi.org/10.1038/35066065
    title: "Hassold & Hunt (2001), Nature Reviews Genetics, the genesis of human aneuploidy"
  - id: goisis-2017-ije
    resource: https://doi.org/10.1093/ije/dyw354
    title: "Goisis, Schneider & Myrskyla (2017), Int J Epidemiol, reversing association between advanced maternal age and child cognitive ability"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "Kong et al. (2012) and Jónsson et al. (2017): 1.51 to ~2.0 de novo single-nucleotide mutations added per year of paternal age (paternal ~20-year-old ~25 mutations vs ~65 at age 45)"
  - "D'Onofrio et al. (2014, N = 2,615,081 Swedish births): within-family sibling hazard ratios for fathers >=45 vs 20-24 remained elevated (autism HR 3.45 [95% CI 1.62-7.33], ADHD HR 13.13, psychosis HR 2.07), while Gratten et al. (2016) estimated de novo coding mutations explain ~10% (unlikely >10-20%) of psychiatric risk"
  - "Hassold & Hunt (2001): maternal oocyte meiotic aneuploidy increases clinically recognized pregnancy trisomy from ~2% under age 25 to ~35% over age 40"
relates_to_cards:
  - "BOUNDS:preterm-cognition-group-risk"
  - "BRIDGES_LENS:fetal-growth-not-destiny"
---


# Paternal Age and De Novo Mutation Rate

> Domain: preconception / genetics
> Last updated: 2026-11-13
> Status: Draft. De novo single-nucleotide mutations scale reliably with father's age at conception, and sibling fixed-effects models in D'Onofrio et al. (2014) did not attenuate paternal-age associations; however, de novo mutations explain ~10–20% of population risk alongside inherited liability for delayed reproduction, and absolute psychiatric risk remains low (>95% unaffected).

## What We Know

Male spermatogenesis involves continuous germline cell divisions throughout post-pubertal life (approximately 23 divisions per year), whereas female oocytes arrest in meiosis I prior to birth and exhibit sharply increasing meiotic non-disjunction with maternal age (**Hassold & Hunt, 2001**: clinically recognized pregnancy trisomy rising from **~2%** under age 25 to **~35%** over age 40). In whole-genome sequencing of parent-offspring trios, offspring *de novo* single-nucleotide mutations increase linearly with father's age at conception, adding **1.51 to ~2.0** mutations per year. Most *de novo* point mutations occur in non-coding regions without clinical phenotype.

## How Confident We Are

**Grade**: High for the linear biological relationship between paternal age at conception and transmitted *de novo* point mutations (and for maternal age-linked meiotic non-disjunction). **Moderate** that paternal age over 45 predicts higher *relative* neurodevelopmental hazards within families (**D'Onofrio et al., 2014**), paired with **Low-to-Moderate** mechanistic certainty because quantitative modeling (**Gratten et al., 2016**) estimates *de novo* coding mutations explain only ~10% (unlikely >10–20%) of the population association, and **Low** that parental age acts as an individual deterministic forecast.

## Evidence and Causal Assessment

- **Germline Sequencing — Kong et al. (2012, *Nature*, 78 Icelandic trios) & Jónsson et al. (2017, *Nature*, 1,548 trios, 108,778 mutations):** Established a paternal increase of ~2.0 (**Kong 2012**) and a high-precision **1.51** mutations per year of father's age (95% CI [1.45, 1.57]; **Jónsson 2017**), alongside **0.37** per year from maternal age.
- **Within-Family Sibling Models — D'Onofrio et al. (2014, *JAMA Psychiatry*, N = 2,615,081 Swedish births):** Within-family sibling fixed-effects analyses did **not** attenuate associations for fathers aged $\ge 45$ vs 20–24: autism (population HR = 1.76 [1.36–2.28], sibling **HR = 3.45 [1.62–7.33]**), ADHD (sibling **HR = 13.13 [6.85–25.16]**), and psychotic disorders (sibling **HR = 2.07 [1.35–3.20]**) persisted or widened within families sharing the same father and mother.
- **Population-Genetic & Confounding Reconciliation — Gratten et al. (2016, *Nature Genetics*), Janecka et al. (2017, *Translational Psychiatry*), & Petersen et al. (2011, *Am J Psychiatry*):** Quantitative genetic modeling demonstrates that age-related *de novo* point mutations account for only **~10%** (unlikely exceeding **10–20%**) of excess psychiatric risk in older fathers, while epidemiological adjustment for father's age at *first* birth (**Petersen et al., 2011**: IRR 1.22 per 10-year increment) points to inherited polygenic liability correlated with delayed first fatherhood interacting with paternal age mechanisms (selective germline clonal expansion, epigenetics, or sibling-design measurement artifacts).
- **Socioeconomic Demographic Offsetting — Goisis, Schneider & Myrskylä (2017, *Int J Epidemiol*):** Across three UK birth cohorts (1958 *n* = 10,969; 1970 *n* = 9,362; 2000–2002 *n* = 11,600), children of older mothers (35–39) reversed from slight cognitive disadvantages (`-0.06` to `-0.12 SD`) to `+0.16 SD` advantage by the 2000s, largely accounted for by older parents' educational and socioeconomic resources offsetting biological age gradients.

## Effect Size and Persistence

Across 25 years of paternal age (20 vs 45), offspring inherit roughly **40–50** additional *de novo* point mutations (~25 to ~65 mutations) out of 3.2 billion base pairs. Even when relative hazards double or triple for fathers $\ge 45$ in registry cohorts, **absolute risk stays low** because baseline neurodevelopmental incidence (~1–1.5% for autism) shifts modestly (~2–3.5%), meaning **well over 95% (roughly 96–98%)** of children born to fathers over 45 do not receive those diagnoses.

## Bias, Heterogeneity, and Confounding

GI attenuation: **n/a** for the biological germline mutation count (directly sequenced in trios).

For offspring psychiatric phenotypes, sibling designs hold constant shared fixed parental genotype and baseline household environment — yet still do not attenuate the paternal-age association in D'Onofrio et al. (2014). At the same time, sibling comparisons can amplify birth-order, paternal career-stage, or age-at-first-birth confounding, and **Gratten et al. (2016)** shows *de novo* mutations cannot alone carry the observed hazard ratios. Both biological age-linked mechanisms and inherited selection/environmental covariance remain active explanations.

## What Remains Uncertain

How much within-family sibling excess risk reflects rare *de novo* non-coding/structural mutations, paternal germline mosaicism/clonal selection ("selfish spermatogonial selection"), epigenetic alterations, or birth-order and shared parental traits correlated with age at first child.

## What This Does Not Mean

Does not mean men or women in their late 30s or 40s should avoid parenthood or expect severe child outcomes, nor that relative hazard ratios equal high absolute probability of illness.

## What Action Is Reasonably Justified

Present **absolute probabilities** (typically >95% unaffected for psychiatric conditions; age-specific first-trimester aneuploidy screening options for maternal age) rather than bare relative hazard ratios, alongside structural support for timing and fertility access.

## Sources

- Kong et al. (2012), *Nature* (DOI: [10.1038/nature11396](https://doi.org/10.1038/nature11396))
- Jónsson et al. (2017), *Nature* (DOI: [10.1038/nature24018](https://doi.org/10.1038/nature24018))
- D'Onofrio et al. (2014), *JAMA Psychiatry* (DOI: [10.1001/jamapsychiatry.2013.4525](https://doi.org/10.1001/jamapsychiatry.2013.4525))
- Gratten et al. (2016), *Nature Genetics* (DOI: [10.1038/ng.3577](https://doi.org/10.1038/ng.3577))
- Janecka et al. (2017), *Translational Psychiatry* (DOI: [10.1038/tp.2016.294](https://doi.org/10.1038/tp.2016.294))
- Petersen, Mortensen & Pedersen (2011), *American Journal of Psychiatry* (DOI: [10.1176/appi.ajp.2010.10020252](https://doi.org/10.1176/appi.ajp.2010.10020252))
- Hassold & Hunt (2001), *Nature Reviews Genetics* (DOI: [10.1038/35066065](https://doi.org/10.1038/35066065))
- Goisis, Schneider & Myrskylä (2017), *International Journal of Epidemiology* (DOI: [10.1093/ije/dyw354](https://doi.org/10.1093/ije/dyw354))
