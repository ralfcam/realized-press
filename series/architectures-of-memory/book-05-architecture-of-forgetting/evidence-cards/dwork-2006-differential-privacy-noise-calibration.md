---
type: Evidence Card
title: "Calibrating Noise to Sensitivity for Differential Privacy (Dwork et al. 2006)"
description: "Differential privacy bounds the privacy loss of individual data participants by calibrating additive noise to the global sensitivity of query functions, providing mathematical guarantees against data reconstruction."
tags: [differential-privacy, noise-calibration, sensitivity, cryptography]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-21T21:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational]
chapter_hooks: [mechanism, boundary, action]
sources:
  - id: Dwork_2006
    resource: https://doi.org/10.1007/11681878_14
    title: "Dwork et al. (2006), Calibrating Noise to Sensitivity in Private Data Analysis"
---

# Calibrating Noise to Sensitivity for Differential Privacy

> Domain: privacy / differential-privacy
> Last updated: 2026-10-21
> Status: Stable (foundational mathematical framework)

## What We Know

Dwork et al. (2006) formalize differential privacy, providing a mathematical guarantee that the presence or absence of any single individual in a database does not significantly alter the probability distribution of any computational output. By calibrating Laplacian noise to the global $L_1$ sensitivity of the query function ($\Delta f / \epsilon$), the mechanism ensures $\epsilon$-differential privacy, mathematically precluding reconstruction and linkage attacks regardless of auxiliary background knowledge.

## How Confident We Are

**Grade**: High

Published at TCC 2006 (Theory of Cryptography Conference), winner of the Gödel Prize (2017), universally recognized as the theoretical gold standard in quantitative privacy and data protection.

## Evidence and Causal Assessment

Mathematical proof establishes that bounded noise injection bounds the privacy loss random variable by $e^{\epsilon}$, guaranteeing semantic plausible deniability for every data contributor.

## Effect Size and Persistence

Eliminates the vulnerability of heuristic anonymization (k-anonymity, data swapping) to external linkage attacks, establishing absolute bounds on information disclosure that persist under arbitrary post-processing.

## Bias, Heterogeneity, and Confounding

Classified as `n/a` (formal mathematical proof). Applying small privacy budgets ($\epsilon < 1$) requires substantial additive noise that can distort downstream statistical utility, particularly in small subgroup populations.

## What Remains Uncertain

Determining optimal domain-specific trade-offs between privacy loss parameters ($\epsilon, \delta$) and empirical analytical utility in high-dimensional deep learning architectures.

## What This Does Not Mean

Differential privacy does not guarantee absolute secrecy of population-level facts discovered from aggregate data; it guarantees that an individual's personal participation cannot be reliably inferred.

## What Action Is Reasonably Justified

Mandate differential privacy frameworks (such as DP-SGD or randomized response mechanisms) across sensitive population telemetry and machine learning training pipelines.

## Sources

- Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006). Calibrating Noise to Sensitivity in Private Data Analysis. In *Theory of Cryptography* (pp. 265–284). Springer, Berlin, Heidelberg. https://doi.org/10.1007/11681878_14
