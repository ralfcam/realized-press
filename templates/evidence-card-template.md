---
okf_version: "0.3"
card_id: "[slug-identifier]"
series: "[series-slug]"
primary_lens: "[technical | organizational | philosophical]" # or [science | interpretation | art]
causal_design: "[rct | natural_experiment | twin_offspring | longitudinal_cohort | formal_proof_and_numerical_simulation]"
certainty_grade: "High" # High | Moderate | Low | Very Low
attenuation_tier: "robust_<20%" # formal_proof | robust_<20% | partially_confounded_20_50% | largely_confounded_>50%
attenuation_class: "robust" # robust | partially_confounded | largely_confounded | not_applicable
identification_design: "[Description of causal identification design, e.g. sibling-comparison, RCT, or formal Jacobian derivation]"
quantitative_anchors:
  - "[Verified quantitative figure or empirical constant 1]"
  - "[Verified quantitative figure or empirical constant 2]"
allowed_verbs: ["demonstrates", "establishes", "proves", "shows"]
forbidden_verbs: ["proves_universally", "solves_all_problems"]
canonical_metaphors:
  body_prose: "[Metaphor calibrated for body prose avoiding clinical jargon]"
  spoken_tts: "[Phonetically clear audio TTS form]"
relates_to_cards:
  - "EXTENDS:[card_slug]" # EXTENDS | BOUNDS | CONTRASTS | MITIGATES | BRIDGES_LENS
  - "BOUNDS:[card_slug]"
type: Evidence Card
title: "[Topic Name]"
description: "[One-sentence narrowest claim.]"
tags: [domain-tag-1, domain-tag-2]
status: draft # draft | stable
confidence: high # high | moderate | low | very-low
generated: { by: agent:antigravity, at: 2026-11-04T00:00:00Z }
stale_after: 2027-11-04T00:00:00Z
sources:
  - id: ExampleKey2024
    resource: https://doi.org/10.xxxx/example
    title: "Author (year), Short title"
---

# [Topic Name]

> Domain: [Series 1: backprop / rnn / gating / attention / rag / privacy / unlearning / org-memory | Series 2: preconception / pregnancy / birth / responsive caregiving / attachment / sleep / feeding / language / play / stress / childcare / screens / executive function / self-regulation / early learning / social development]
> Last updated: [YYYY-MM-DD]
> Status: Draft (source-audited first pass unless noted)

## What We Know

[Narrowest supported conclusion, 1-2 sentences.]

## How Confident We Are

**Grade**: [High / Moderate / Low / Very Low]

[Concise justification matching the YAML `certainty_grade` and `confidence` tokens.]

## Evidence and Causal Assessment

[Key studies/syntheses, mathematical theorems, ablation benchmarks, or developmental designs (RCT, natural experiment, MR, adoption/IVF/sibling/twin-offspring, longitudinal cohort, cross-sectional, mechanistic), replication status, causal or external-validity limitations.]

## Effect Size and Persistence

[Absolute/standardized effect sizes, spectral/scaling bounds, CIs where available, practical magnitude, time or sequence horizon — does the effect persist, fade, or is persistence untested?]

## Bias, Heterogeneity, and Confounding

[Main alternative explanations; subgroup or architecture variation; benchmark leakage or attenuation in genetically informed / controlled designs, classified as largely confounded (>50%), partially confounded (20-50%), robust (<20%), or n/a (formal theorem).]

## What Remains Uncertain

[Most decision-relevant unresolved questions.]

## What This Does Not Mean

[Explicitly prohibited overreach, anthropomorphic metaphor, deterministic interpretation, or unsupported prescriptions (>40 characters).]

## What Action Is Reasonably Justified

[Proportionate guidance for engineering architectures, organizations, families, or policy — or a statement that no action follows.]

## Sources

- [Citation 1]
- [Citation 2]
