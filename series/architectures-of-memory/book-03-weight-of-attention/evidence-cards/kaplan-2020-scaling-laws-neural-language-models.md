---
okf_version: "0.3"
card_id: "kaplan-2020-scaling-laws-neural-language-models"
series: "architectures-of-memory"
primary_lens: "technical"
causal_design: "empirical_power_law_scaling"
certainty_grade: "High"
attenuation_class: "robust_under_20pct"
allowed_verbs: ["demonstrates", "establishes", "shows", "governs", "scales"]
forbidden_verbs: ["guarantees_agi", "proves_infinite_scaling"]
locked_bib_keys: ["kaplan2020arxiv", "Kaplan2020"]
contradicts_or_bounds: ["hoffmann-2022-chinchilla"]
canonical_metaphors:
  body_prose: "a power-law gravity well that predicts downstream performance gains purely from compute, data, and parameters"
  spoken_tts: "a power-law gravity well that predicts performance gains from compute data and parameters"
jargon_mappings:
  - term: "Power-Law Scaling"
    notes_definition: "Mathematical relationship L(N) = (N_c / N)^alpha_N where cross-entropy loss decreases smoothly as a power law of parameter count, dataset size, and compute"
escalation_plan:
  1: "Establish the empirical regularity of power-law loss decay across six orders of magnitude."
  2: "Show that architecture details (depth vs. width) matter far less than overall scale."
  3: "Connect to organizational resources: why systemic infrastructure investments yield predictable compounding advantages over localized tactical tweaks."
type: Evidence Card
title: "Scaling Laws for Neural Language Models (Kaplan et al. 2020)"
description: "Cross-entropy loss in autoregressive Transformer language models follows smooth power-law relationships with parameter count, dataset size, and compute budget over multiple orders of magnitude."
tags: [scaling-laws, compute-optimal, transformers, power-laws]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-21T21:26:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [mechanism, boundary]
sources:
  - id: kaplan2020arxiv
    resource: https://arxiv.org/abs/2001.08361
    title: "Kaplan et al. (2020), Scaling Laws for Neural Language Models"
---

# Scaling Laws for Neural Language Models

> Domain: machine-learning / scaling-laws
> Last updated: 2026-10-21
> Status: Stable (landmark empirical scaling methodology)

## What We Know

Language model performance improves predictably as a power-law function of model parameters $N$, dataset size $D$, and total training compute $C$, with smooth scaling spanning more than six orders of magnitude.

## How Confident We Are

**Grade**: High

Replicated and refined across subsequent studies (Hoffmann et al., 2022; Henighan et al., 2020) confirming the broad validity of empirical power-law relationships across modalities.

## Evidence and Causal Assessment

Systematic multi-scale experiments varying $N$, $D$, and $C$ independently isolate the causal trade-offs governing cross-entropy test loss, showing that architectural hyper-parameters have minimal impact compared to scale.

## Effect Size and Persistence

Test loss scales as $L(N) \propto N^{-lpha_N}$, $L(D) \propto D^{-lpha_D}$, and $L(C) \propto C^{-lpha_C}$, allowing researchers to accurately forecast the loss of billion-parameter models from small-scale training runs.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Although Hoffmann et al. (2022) adjusted Kaplan's compute-optimal token-to-parameter ratio from $1:1$ to roughly $20:1$, the fundamental finding of smooth power-law scaling remains robust.

## What Remains Uncertain

Whether power-law reductions in cross-entropy loss smoothly translate into linear gains in complex multi-step reasoning and algorithmic verification.

## What This Does Not Mean

This does not mean that scaling parameters alone solves truthfulness, safety, or factuality; lower cross-entropy loss merely indicates more accurate token probability modeling.

## What Action Is Reasonably Justified

Use small-scale scaling law projections to optimize compute and data allocation before committing to multi-million-dollar training runs.

## Sources

- Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., ... & Amodei, D. (2020). Scaling Laws for Neural Language Models. *arXiv:2001.08361*.
- Hoffmann, J., et al. (2022). Training Compute-Optimal Large Language Models. *arXiv:2203.15556*.
