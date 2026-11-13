---
type: Evidence Card
title: "The Placenta Mediates Fetal Dose"
description: "Maternal exposure is not equivalent to fetal dose; the placenta transports, metabolizes, restricts, or facilitates substances, including via an incomplete glucocorticoid buffer."
tags: [pregnancy, placenta, mechanism]
status: draft
confidence: high-enzymatic-mechanism; moderate-stress-downregulation; low-child-forecast
generated: { by: agent:cursor, at: 2026-09-15T18:00:00Z }
stale_after: 2027-03-15T00:00:00Z
atlas_domains: [pregnancy]
chapter_hooks: [mechanism, puzzle]
sources:
  - id: burton-2015-placenta
    resource: https://pmc.ncbi.nlm.nih.gov/articles/PMC4305167/
    title: "Burton & Fowden (2015), the placenta as a multifaceted transient organ"
  - id: seckl-holmes-2007
    resource: https://doi.org/10.1038/ncpendmet0515
    title: "Seckl & Holmes (2007), placental glucocorticoid metabolism and fetal programming"
  - id: odonnell-2012-placenta
    resource: https://doi.org/10.1016/j.psyneuen.2011.09.014
    title: "O'Donnell et al. (2012), Psychoneuroendocrinology, maternal prenatal anxiety and downregulation of placental 11beta-HSD2"
  - id: chapman-2013-physrev
    resource: https://doi.org/10.1152/physrev.00020.2012
    title: "Chapman, Holmes & Seckl (2013), Physiological Reviews, 11beta-hydroxysteroid dehydrogenases as tissue glucocorticoid gatekeepers"
  - id: benediktsson-1997-cortisol
    resource: https://doi.org/10.1046/j.1365-2265.1997.1230939.x
    title: "Benediktsson et al. (1997), Clinical Endocrinology, placental 11beta-hydroxysteroid dehydrogenase regulation of fetal cortisol"
attenuation_tier: "formal_proof"
quantitative_anchors:
  - "placental 11beta-HSD2 oxidizes ~80-90% of maternal cortisol into inactive cortisone in perfused placenta studies (Benediktsson et al. 1997; Seckl & Holmes 2007)"
  - "O'Donnell et al. (2012, Psychoneuroendocrinology; N = 56 term pregnancies): maternal trait anxiety negatively correlated with placental 11beta-HSD2 mRNA expression (r = -0.40, p < 0.01; state anxiety r = -0.27, p = 0.05)"
  - "Chapman, Holmes & Seckl (2013, Phys Rev): review of intracellular 11beta-HSD glucocorticoid gatekeeping and down-regulation under inflammation, preeclampsia, or severe hypoxia"
relates_to_cards:
  - "EXTENDS:fetal-autonomic-maturation"
  - "BOUNDS:prenatal-maternal-stress-anxiety"
---


# The Placenta Mediates Fetal Dose

> Domain: pregnancy
> Last updated: 2026-11-13
> Status: Audited mechanistic card (`High` for 11β-HSD2 enzymatic cortisol oxidation; `Moderate` for human stress-threshold and preeclampsia down-regulation; `Low` for long-term child cognitive/personality forecasting).

## What We Know

The placenta is a transient organ of exchange, metabolism, and endocrine signaling. Maternal blood levels are not identical to fetal dose: placental **11β-HSD2** oxidizes **~80–90%** of maternal cortisol into inactive cortisone (`Benediktsson et al., 1997`; `Seckl & Holmes, 2007`), functioning as a high-capacity enzymatic buffer rather than an impermeable 100% seal. Crucially, this enzymatic gate can itself be down-regulated by severe chronic anxiety, pro-inflammatory signaling, or preeclampsia (**O'Donnell et al., 2012**; **Chapman, Holmes & Seckl, 2013**).

## How Confident We Are

**Grade**: **High** for the enzymatic `11β-HSD2` cortisol-to-cortisone conversion mechanism and selective placental transport anatomy; **Moderate** for human prenatal anxiety and preeclampsia down-regulating placental `11β-HSD2` expression; **Low** that placental variation within typical pregnancies forecasts long-term childhood cognition or personality.

## Evidence and Causal Assessment

- **Burton & Fowden (2015):** Reviews nutrient transport, uterine-artery remodeling, endocrine modulation of maternal metabolism, and selective barrier physiology.
- **Benediktsson et al. (1997), Seckl & Holmes (2007) & Chapman, Holmes & Seckl (2013):** Perfused human placenta, animal knockout/inhibition models, and rare human *HSD11B2* mutations establish **~80–90%** enzymatic conversion of maternal cortisol into inactive cortisone, while inflammation, preeclampsia, and hypoxia reduce enzymatic gatekeeping capacity.
- **O'Donnell et al. (2012, *Psychoneuroendocrinology*, N = 56 term elective-cesarean pregnancies):** Found maternal prenatal trait anxiety negatively correlated with placental `11β-HSD2` mRNA expression (`r = -0.40, p < 0.01`; state anxiety `r = -0.27, p = 0.05`), demonstrating that chronic distress can attenuate — though not abolish — the enzymatic buffer in humans.

## Effect Size and Persistence

A placental enzyme level or placental weight reflects contemporaneous intrauterine physiology and fetal growth regulation, not a permanent behavioral sentence. Typical transient cortisol spikes barely register past intact `11β-HSD2`, whereas chronic illness, severe depression, or preeclampsia require clinical attention to placental function.

## Bias, Heterogeneity, and Confounding

GI attenuation: **n/a** (biological placental transport and enzymatic physiology, not an observational population phenotype association).

Term-delivery placental sampling captures late-gestation expression rather than first- or second-trimester kinetics; observational anxiety–expression correlations remain vulnerable to residual confounding by sleep, nutrition, and vascular status.

## What Remains Uncertain

Exact stress-duration thresholds at which modest placental `11β-HSD2` down-regulation produces clinically durable postnatal shifts in typical community pregnancies versus genetically confounded vulnerability (see `prenatal-maternal-stress-anxiety`).

## What This Does Not Mean

Does not mean the placenta is a 100% hermetically sealed barrier that makes maternal health irrelevant, nor that ordinary daily worry floods the fetus with maternal stress hormones or writes a lifelong behavioral destiny.

## What Action Is Reasonably Justified

Clinical attention to placental insufficiency, preeclampsia, maternal hypertension/diabetes, chronic clinical anxiety/depression, and known teratogens is justified. Individual fear or guilt over ordinary day-to-day mood fluctuations is not licensed by this mechanism.

## Sources

- Burton & Fowden (2015), *Phil. Trans. R. Soc. B* (PMC: [PMC4305167](https://pmc.ncbi.nlm.nih.gov/articles/PMC4305167/))
- Seckl & Holmes (2007), *Nat. Clin. Pract. Endocrinol. Metab.* (DOI: [10.1038/ncpendmet0515](https://doi.org/10.1038/ncpendmet0515))
- Benediktsson et al. (1997), *Clinical Endocrinology* (DOI: [10.1046/j.1365-2265.1997.1230939.x](https://doi.org/10.1046/j.1365-2265.1997.1230939.x))
- O'Donnell et al. (2012), *Psychoneuroendocrinology* (DOI: [10.1016/j.psyneuen.2011.09.014](https://doi.org/10.1016/j.psyneuen.2011.09.014))
- Chapman, Holmes & Seckl (2013), *Physiological Reviews* (DOI: [10.1152/physrev.00020.2012](https://doi.org/10.1152/physrev.00020.2012))
