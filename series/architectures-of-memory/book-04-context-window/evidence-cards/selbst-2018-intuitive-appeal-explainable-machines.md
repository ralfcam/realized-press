---
type: Evidence Card
title: "The Intuitive Appeal of Explainable Machines (Selbst & Barocas 2018)"
description: "Legal and regulatory demands for algorithmic explainability conflate inscrutability (epistemic opacity) with non-intuitiveness (statistical counter-intuitiveness), creating governance gaps when applied to complex models."
tags: [explainability, algorithmic-governance, legal-scrutiny, compliance]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T15:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [organizational, philosophical]
chapter_hooks: [mechanism, boundary, action]
sources:
  - id: Selbst_2018
    resource: https://doi.org/10.2139/ssrn.3126971
    title: "Selbst & Barocas (2018), The Intuitive Appeal of Explainable Machines"
---

# The Intuitive Appeal of Explainable Machines

> Domain: regulation / explainability
> Last updated: 2026-10-23
> Status: Stable (definitive legal/epistemic analysis)

## What We Know

Regulators and legal scholars demand "explanation" for automated decisions, assuming machine explanations can serve the same function as human reasons (justification, contesting decisions, ensuring non-discrimination). Selbst & Barocas demonstrate that this demand conflates two distinct forms of opacity: *inscrutability* (inability to inspect the mathematical path from input to output) and *non-intuitiveness* (the statistical logic operates on high-dimensional correlations that defy human causal heuristics).

## How Confident We Are

**Grade**: High

Published in *Fordham Law Review* (Vol. 87), foundational to legal critiques of GDPR "right to an explanation," and central to administrative law discussions surrounding automated governance.

## Evidence and Causal Assessment

Even if a deep neural network's calculations are rendered fully transparent (complete mathematical inspectability), its statistical rules frequently remain unintelligible to human operators because the model relies on weak, non-linear correlations across millions of features that cannot be translated into traditional normative reasons.

## Effect Size and Persistence

Post-hoc explainability techniques (e.g., LIME, SHAP, feature saliency) provide local linear approximations that can be misleading or easily gamed, failing to satisfy the legal standard of substantive causal accountability.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Demands for simplified intuitive explanations frequently force organizations to discard predictive accuracy or resort to superficial explanations that conceal underlying disparate impacts.

## What Remains Uncertain

How to formulate legally enforceable standards of proof and algorithmic due process when high-dimensional foundation models generate automated determinations in underwriting, pricing, and resource allocation.

## What This Does Not Mean

The difficulty of intuitive machine explanation does not excuse organizations from compliance; rather, it indicates that regulation must focus on empirical outcome testing and system constraints rather than post-hoc verbal justifications.

## What Action Is Reasonably Justified

In regulated industries, ground compliance architectures in deterministic constraint layers, auditable retrieval databases, and statistical impact audits rather than relying on LLM-generated narrative self-explanations.

## Sources

- Selbst, A. D., & Barocas, S. (2018). The Intuitive Appeal of Explainable Machines. *Fordham Law Review*, 87(3), 1085–1139. https://doi.org/10.2139/ssrn.3126971
