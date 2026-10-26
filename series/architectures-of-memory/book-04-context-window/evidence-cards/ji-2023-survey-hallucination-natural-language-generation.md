---
type: Evidence Card
title: "Taxonomy and Structural Mechanisms of Hallucination in NLG (Ji et al. 2023)"
description: "Hallucination in neural language generation stems from parametric memory corruption, training data bias, and decoding divergence, categorizable into intrinsic and extrinsic factual inaccuracies."
tags: [hallucination, parametric-memory, factual-grounding, nlg-survey]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T15:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: Ji_2023
    resource: https://doi.org/10.1145/3571730
    title: "Ji et al. (2023), Survey of Hallucination in Natural Language Generation"
---

# Taxonomy and Structural Mechanisms of Hallucination in NLG

> Domain: hallucination / memory-corruption
> Last updated: 2026-10-23
> Status: Stable (definitive survey and taxonomy)

## What We Know

Hallucination in natural language generation is not an anomalous bug but a structural feature of maximum-likelihood statistical sequence predictors. Models generate fluent, grammatically flawless statements that contradict the source context (intrinsic hallucination) or introduce unverifiable assertions absent from the training distribution or grounding input (extrinsic hallucination).

## How Confident We Are

**Grade**: High

Synthesized by Ji et al. (2023) across hundreds of empirical studies and verified across summarization, machine translation, dialogue, and question answering systems.

## Evidence and Causal Assessment

Causal roots of hallucination include: (1) imperfect memorization during pretraining, where co-occurrence statistics override factual precision; (2) exposure bias during autoregressive decoding; and (3) divergence between training data distribution and prompt requirements.

## Effect Size and Persistence

Hallucination rates range from 3% to over 30% depending on domain complexity, entity rarity, and context window length, persisting even as model scale expands into hundreds of billions of parameters.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Surface plausibility correlates inversely with detectability: larger models produce hallucinations that are more syntactically polished and self-consistent, increasing the cognitive load required to audit them.

## What Remains Uncertain

Whether pure autoregressive next-token prediction can ever drive hallucination rates to absolute zero without explicit external epistemic grounding or formal theorem-proving verifiers.

## What This Does Not Mean

Hallucination does not imply malicious intent or conscious deceit; it reflects probabilistic pattern completion operating across ungrounded parametric weight matrices.

## What Action Is Reasonably Justified

Never deploy ungrounded LLMs as authoritative single points of failure in regulated or mission-critical workflows; mandate external retrieval validation (RAG) and deterministic citation checks.

## Sources

- Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., & Fung, P. (2023). Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*, 55(12), 1–38. https://doi.org/10.1145/3571730
