---
type: Evidence Card
title: "Empirical Scaling Laws for Neural Language Models (Kaplan et al. 2020)"
description: "Language model cross-entropy loss scales as a power-law with compute, dataset size, and parameter count across more than seven orders of magnitude, with architectural hyperparameters having minimal effect."
tags: [scaling-laws, power-law, compute-optimal, transformer-scaling]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T15:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: kaplan2020arxiv
    resource: https://arxiv.org/abs/2001.08361
    title: "Kaplan et al. (2020), Scaling Laws for Neural Language Models"
---

# Empirical Scaling Laws for Neural Language Models

> Domain: scaling / power-laws
> Last updated: 2026-10-23
> Status: Stable (foundational empirical scaling law)

## What We Know

Cross-entropy loss in autoregressive Transformer language models follows predictable power-law relationships with three fundamental variables: parameter count $N$, dataset size $D$, and compute budget $C$. Architectural details such as network depth, width, and number of attention heads have remarkably little impact within wide bounds, establishing that scale dominates structural tuning.

## How Confident We Are

**Grade**: High

Empirically confirmed across seven orders of magnitude by Kaplan et al. (2020), subsequently refined by Hoffmann et al. (2022 / Chinchilla) regarding data-compute proportionality, and universally validated across modern frontier foundation models.

## Evidence and Causal Assessment

Systematic ablation across model sizes from $10^3$ to $10^9$ parameters and compute budgets demonstrated smooth, continuous power-law decay of test loss without plateauing, indicating that language modeling difficulty scales predictably with information-theoretic information density.

## Effect Size and Persistence

Performance improves smoothly as $L(N) \approx (N_c/N)^{\alpha_N}$, with power-law exponents $\alpha_N \approx 0.076$, $\alpha_C \approx 0.050$, and $\alpha_D \approx 0.095$. Models can be scaled reliably by predicting loss before committing massive training clusters.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Downstream task evaluation can exhibit sharp non-linear emergent phase changes even when the underlying pretraining token cross-entropy loss decreases smoothly and continuously.

## What Remains Uncertain

The exact boundaries where pretraining data depletion or data quality saturation bends the power-law curves into sub-logarithmic returns.

## What This Does Not Mean

Power-law reduction in next-token cross-entropy loss does not guarantee semantic comprehension, factual reliability, or causal reasoning ability in downstream inference.

## What Action Is Reasonably Justified

Use scaling law equations to determine optimal compute and data allocations prior to large-scale training runs rather than heuristic trial-and-error parameter tuning.

## Sources

- Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., Gray, S., Radford, A., Wu, J., & Amodei, D. (2020). Scaling Laws for Neural Language Models. *arXiv preprint arXiv:2001.08361*. https://arxiv.org/abs/2001.08361
