---
okf_version: "0.3"
card_id: "[slug-identifier]"
series: "architectures-of-memory"
primary_lens: "[technical | organizational | philosophical]"
causal_design: "[formal_proof_and_numerical_simulation | ablation_benchmark | longitudinal_cohort | conceptual_analysis]"
certainty_grade: "High" # High | Moderate | Low | Very Low
attenuation_tier: "formal_proof" # formal_proof | robust_<20% | partially_confounded_20_50% | largely_confounded_>50%
attenuation_class: "not_applicable" # formal_proof / robust / partially_confounded / largely_confounded / not_applicable
identification_design: "[Description of mathematical proof, ablation design, or organizational cohort]"
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

> Domain: backprop / rnn / gating / attention / rag / privacy / unlearning / org-memory / philosophy-of-mind
> Last updated: [YYYY-MM-DD]
> Status: Draft (source-audited first pass unless noted)

## What We Know

[Narrowest supported conclusion, 1-2 sentences.]

## How Confident We Are

**Grade**: [High / Moderate / Low / Very Low]

[Concise justification matching the YAML `certainty_grade` and `confidence` tokens.]

## Evidence and Causal Assessment

[Key studies/syntheses, mathematical theorems, ablation benchmarks, or historical empirical records, replication status, causal or external-validity limitations.]

## Effect Size and Persistence

[Absolute/standardized effect sizes, spectral/scaling bounds, asymptotic complexities, practical magnitude, time or sequence horizon — does the effect persist, fade, or is persistence untested?]

## Bias, Heterogeneity, and Confounding

[Main alternative explanations; subgroup or architecture variation; benchmark leakage or systemic attenuation in controlled settings.]

## What Remains Uncertain

[Most decision-relevant unresolved questions.]

## What This Does Not Mean

[Explicitly prohibited overreach, anthropomorphic metaphor, deterministic interpretation, or unsupported prescriptions (>40 characters).]

## What Action Is Reasonably Justified

[Proportionate guidance for engineering architectures, organizations, or policy — or a statement that no action follows.]

## Sources

- [Citation 1]
- [Citation 2]
