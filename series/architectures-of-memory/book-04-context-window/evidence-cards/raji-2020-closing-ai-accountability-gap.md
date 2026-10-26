---
type: Evidence Card
title: "Internal Algorithmic Auditing and Accountability Frameworks (Raji et al. 2020)"
description: "Closing the AI accountability gap requires end-to-end internal auditing frameworks across system lifecycles, establishing verifiable documentation, ownership, and testing prior to organizational deployment."
tags: [algorithmic-auditing, accountability, governance, compliance]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T15:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [organizational, technical]
chapter_hooks: [mechanism, boundary, action]
sources:
  - id: Raji_2020
    resource: https://doi.org/10.1145/3351095.3372873
    title: "Raji et al. (2020), Closing the AI accountability gap: defining an end-to-end framework for internal algorithmic auditing"
---

# Internal Algorithmic Auditing and Accountability Frameworks

> Domain: governance / algorithmic-auditing
> Last updated: 2026-10-23
> Status: Stable (definitive operational framework)

## What We Know

Voluntary ethical principles and post-hoc model explainability fail to ensure algorithmic accountability without structured, institutionalized internal audit trails. Raji et al. (2020) define the Internal Algorithmic Audit framework (SMACTR: Scoping, Mapping, Artifact Collection, Testing, and Reflection), translating high-level regulatory mandates into verifiable engineering artifacts across the entire development lifecycle.

## How Confident We Are

**Grade**: High

Adopted widely across enterprise governance bodies, cited across regulatory standard-setting guidelines (NIST AI RMF, EU AI Act conformity assessments), and validated across industry auditing practices.

## Evidence and Causal Assessment

Case studies in algorithmic bias and corporate failure reveal that harms occur primarily not from code bugs, but from organizational gaps: unrecorded assumptions, absent data lineage, and lack of defined institutional accountability for failure modes.

## Effect Size and Persistence

Pre-deployment auditing identifies systemic performance disparities and compliance violations that routine unit testing fails to capture, formalizing a paper trail necessary for regulated industry compliance (finance, healthcare, employment).

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Organizational incentives often treat auditing frameworks as compliance theater unless audits are backed by independent authority to halt deployments.

## What Remains Uncertain

Adapting audit frameworks to non-deterministic, continuously updated foundation models whose parametric weights are black boxes hosted by third-party API providers.

## What This Does Not Mean

Completing an internal audit does not prove that an algorithm is flawless, bias-free, or mathematically incapable of future failure in unseen production environments.

## What Action Is Reasonably Justified

Mandate end-to-end artifact collection (data sheets, model cards, audit logs) and independent sign-off gates before deploying algorithmic systems into regulated operational environments.

## Sources

- Raji, I. D., Smart, A., White, R. N., Mitchell, M., Gebru, T., Hutchinson, B., Smith-Loud, J., Theron, D., & Barnes, P. (2020). Closing the AI accountability gap: defining an end-to-end framework for internal algorithmic auditing. *Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency (FAT\* '20)*, 33–44. https://doi.org/10.1145/3351095.3372873
