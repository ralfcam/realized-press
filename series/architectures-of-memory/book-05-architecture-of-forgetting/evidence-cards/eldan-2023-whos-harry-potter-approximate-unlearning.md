---
okf_version: '0.3'
card_id: eldan-2023-whos-harry-potter-approximate-unlearning
series: architectures-of-memory
primary_lens: technical
causal_role: mechanism
plain_english_metaphor: the targeted conceptual erasure
attenuation_class: robust_under_20pct
type: Evidence Card
title: Approximate Selective Unlearning in Pre-Trained Language Models (Eldan & Russinovich
  2023)
description: Fine-tuning target models on synthetic counterfactual completions paired
  with reinforced generic text unlearns targeted copyrighted or sensitive domain knowledge
  without catastrophic general language degradation.
tags:
- machine-unlearning
- llm-unlearning
- selective-forgetting
- copyright
status: stable
confidence: high
generated:
  by: agent:antigravity
  at: 2026-10-21 21:32:00+00:00
stale_after: '2028-01-01T00:00:00Z'
series_domains:
- technical
chapter_hooks:
- anomaly
- mechanism
- boundary
locked_bib_keys:
- eldan2023arxiv
sources:
  - id: eldan2023arxiv
    resource: https://arxiv.org/abs/2310.02238
    title: "Eldan & Russinovich (2023), Who's Harry Potter? Approximate Unlearning in LLMs"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "approximate unlearning of copyrighted fiction from Llama-7B via negative target reinforcement"
  - "prompt completion accuracy reduction from 80%+ to baseline zero on Harry Potter trivia"
  - "preservation of general benchmark performance on MMLU and ARC"
relates_to_cards:
  - "CONTRASTS:bourtoule-2021-sisa-machine-unlearning"
  - "BOUNDS:carlini-2021-extracting-training-data-from-large-language-models"
---


# Approximate Selective Unlearning in Pre-Trained Language Models

> Domain: privacy / machine-unlearning
> Last updated: 2026-10-21
> Status: Stable (replicated benchmark framework)

## What We Know

Targeted knowledge (e.g., characters, plots, and verbatim quotes from the Harry Potter corpus) can be selectively erased from a pre-trained language model (Llama-2-7b) by steering predictions away from unlearning targets using reinforced synthetic baseline comparisons, reducing completion accuracy to near-zero while preserving general benchmark performance (MMLU, ARC).

## How Confident We Are

**Grade**: High

Demonstrated by Eldan and Russinovich (2023) across factual completion probes, prompt-leakage tests, and standard academic benchmarks, with the unlearned model scoring comparable to un-adapted baselines on general reasoning tasks while scoring 0% on Harry Potter trivia prompts.

## Evidence and Causal Assessment

Controlled fine-tuning experiments demonstrate that replacing target-specific token logits with generic counterfactual completions (rather than naive gradient ascent) successfully prevents catastrophic language degradation (model lobotomy) while achieving effective domain erasure.

## Effect Size and Persistence

The technique erased knowledge across 300+ prompt probes with only 1 hour of fine-tuning on a single A100 GPU (compared to 184,000 GPU-hours for initial pre-training). General performance on MT-Bench and MMLU shifted by less than 1%.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Although direct trivia prompts fail, sophisticated adversarial jailbreaks, multi-hop indirect relational queries, and white-box latent representation probes can sometimes recover residual unlearned knowledge fragments.

## What Remains Uncertain

Whether approximate representation-steering unlearning provides verifiable cryptographic guarantees equivalent to exact retraining from scratch (e.g., SISA).

## What This Does Not Mean

Approximate unlearning is not a cryptographic deletion certificate; erasing generation does not guarantee that underlying associative weights in deep MLP layers have been completely expunged.

## What Action Is Reasonably Justified

Use approximate unlearning techniques for cost-effective remediation of targeted copyright violations and toxic data exposure in production models where retraining from scratch is computationally infeasible.

## Sources

- Eldan, R., & Russinovich, M. (2023). Who's Harry Potter? Approximate Unlearning in LLMs. *arXiv preprint arXiv:2310.02238*. https://arxiv.org/abs/2310.02238
