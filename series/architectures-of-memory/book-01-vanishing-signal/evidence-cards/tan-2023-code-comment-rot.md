---
okf_version: "0.3"
card_id: "tan-2023-code-comment-rot"
series: "architectures-of-memory"
primary_lens: "organizational"
causal_design: "empirical_software_repository_mining"
certainty_grade: "Moderate"
attenuation_class: "robust_under_20pct"
allowed_verbs: ["suggests", "indicates", "demonstrates_in_repositories", "finds", "tracks"]
forbidden_verbs: ["proves_universally", "causes"]
locked_bib_keys: ["Tan2023", "Holtzblatt2010", "Tan_2023"]
contradicts_or_bounds: []
canonical_metaphors:
  body_prose: "an un-gated archive of fossilized comments that actively misleads new maintainers"
  spoken_tts: "an un-gated archive of fossilized comments that actively misleads new maintainers"
jargon_mappings:
  - term: "documentation rot"
    notes_definition: "Semantic divergence between static text comments and executable implementation over commit history"
escalation_plan:
  1: "Demonstrate empirical rates of code-comment divergence across open-source repositories."
  2: "Examine corporate compliance wikis as extreme manifestations of un-gated documentation rot."
  3: "Reflect on how externalized symbols outlive the cognitive state that created them."
type: Evidence Card
title: "Code-Comment Inconsistency and Documentation Rot in Software Repositories (Tan et al. 2023)"
description: "Empirical software repository analyses show that documentation and inline comments frequently drift out of synchronization with executable code when update gating is absent."
tags: [documentation-rot, software-maintenance, org-memory]
status: stable
confidence: moderate
generated: { by: agent:antigravity, at: 2026-10-20T22:45:00Z }
stale_after: 2027-10-20T00:00:00Z
series_domains: [organizational, technical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: Tan2023
    resource: https://doi.org/10.1007/s10664-023-10397-6
    title: "Tan, Wagner, and Treude (2023), Detecting Outdated Code Element References in Software Repository Documentation"
  - id: Holtzblatt2010
    resource: https://doi.org/10.1145/1753846.1754208
    title: "Holtzblatt et al. (2010), Evaluating the uses and benefits of an enterprise wiki"
---

# Code-Comment Inconsistency and Documentation Rot in Software Repositories

> Domain: org-memory / software-maintenance
> Last updated: 2026-10-20
> Status: Stable (source-audited empirical software engineering evidence)

## What We Know

Software repository studies suggest that static documentation and wiki artifacts routinely diverge from live system behavior when code commits are not mechanically gated against documentation references.

## How Confident We Are

**Grade**: Moderate

Empirical repository mining across open-source projects (Tan, Wagner, & Treude, 2023) and enterprise field studies of corporate wikis (Holtzblatt et al., 2010) consistently document reference staleness and contributor hesitation, though exact rot rates vary across governance models and languages.

## Evidence and Causal Assessment

Tan, Wagner, and Treude (2023) analyzed over 3,000 GitHub projects to track outdated code element references in documentation, identifying lifetime patterns of stale references before eventual repair or deletion. Holtzblatt et al. (2010) conducted qualitative and survey fieldwork inside an enterprise wiki environment, documenting how organizational incentives and ownership ambiguity impede shared maintenance.

## Effect Size and Persistence

Outdated references in un-gated documentation can persist for months or years across commit histories until automated broken-reference detectors or active onboarding failures surface the discrepancy.

## Bias, Heterogeneity, and Confounding

Classified as `partially confounded (20-50%)`. Observational repository metrics are confounded by project maturity, team size, CI/CD tooling, and whether documentation is user-facing API reference vs. internal architectural notes.

## What Remains Uncertain

The long-term net productivity impact of strict CI documentation-gating (false-positive friction vs. prevented operational incidents) remains incompletely quantified in randomized organizational trials.

## What This Does Not Mean

This evidence does not mean that written documentation is useless or that organizations should abandon architectural decision records; rather, it demonstrates that un-gated write-only archives degrade without active retrieval and verification loops.

## What Action Is Reasonably Justified

Engineering teams should couple critical operational invariants to automated CI checks (linting code-element references, executable tests, and staleness horizons) rather than relying solely on manual wiki upkeep.

## Sources

- Tan, W. S., Wagner, M., & Treude, C. (2023). Detecting Outdated Code Element References in Software Repository Documentation. *Empirical Software Engineering*, 29(1). https://doi.org/10.1007/s10664-023-10397-6
- Holtzblatt, L. J., Damianos, L. E., & Weiss, D. (2010). Factors impeding Wiki use in the enterprise: a case study. *CHI '10 Extended Abstracts on Human Factors in Computing Systems*, 4661–4676. https://doi.org/10.1145/1753846.1754208
