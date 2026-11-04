---
okf_version: '0.3'
card_id: feldman-2020-does-learning-require-memorization
series: architectures-of-memory
primary_lens: technical
causal_role: constraint
plain_english_metaphor: the long-tail memory tax
attenuation_class: not_applicable
type: Evidence Card
title: Necessity of Memorization for Generalization in Long-Tailed Distributions (Feldman
  2020)
description: Achieving Bayes-optimal generalization on long-tailed data distributions
  mathematically necessitates memorizing training sample labels from rare sub-populations,
  creating a fundamental tension with differential privacy.
tags:
- memorization
- generalization
- long-tail
- privacy-utility-tradeoff
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
- feldman2019arxiv
sources:
  - id: feldman2019arxiv
    resource: https://arxiv.org/abs/1906.05271
    title: "Feldman (2020), Does Learning Require Memorization? A Short Tale about a Long Tail"
attenuation_tier: "formal_proof"
quantitative_anchors:
  - "mathematical proof that memorization of rare/atypical examples is necessary for near-optimal generalization"
  - "long-tailed distribution setting where subpopulation frequencies scale as O(1/k)"
  - "lower bound on excess error for classifiers that do not memorize atypical instances"
relates_to_cards:
  - "EXTENDS:carlini-2021-extracting-training-data-from-large-language-models"
  - "BOUNDS:dwork-2006-differential-privacy-noise-calibration"
---


# Necessity of Memorization for Generalization in Long-Tailed Distributions

> Domain: privacy / memorization-theory
> Last updated: 2026-10-21
> Status: Stable (theoretical foundation theorem)

## What We Know

When the underlying data-generating distribution is heavy-tailed—comprising a massive frequency tail of rare sub-populations—any learning algorithm that achieves close-to-optimal generalization error must memorize individual labels and specific features of training instances appearing only once or twice in the dataset.

## How Confident We Are

**Grade**: High

Proven theoretically by Feldman (2020 / STOC 2020) within formal statistical learning models, and empirically verified by Feldman and Zhang (2020) on ImageNet and CIFAR-100 benchmarks.

## Evidence and Causal Assessment

Mathematical proofs demonstrate that in distributions where the frequency of sub-populations decays as a power law, the cumulative probability mass of rare atypical examples dominates total test loss; learning algorithms that suppress atypical instance memorization cannot achieve Bayes-optimal generalization error.

## Effect Size and Persistence

Empirical measurements on ImageNet show that memorization of rare examples accounts for substantial accuracy gains (+3.7% accuracy on ImageNet directly attributable to memorized instances), establishing that memorization in deep learning is not merely an over-parameterization bug.

## Bias, Heterogeneity, and Confounding

Classified as `n/a (formal theorem)`. The mathematical trade-off between memorization and generalization on long-tailed distributions is fundamental, establishing an irreducible structural conflict with strict differential privacy ($\epsilon \ll 1$).

## What Remains Uncertain

Developing formal criteria to delineate necessary functional memorization (required for generalizing on rare syntactic rules) from accidental idiosyncratic memorization (e.g., social security numbers or private keys).

## What This Does Not Mean

The theorem does not imply that all memorization is useful; memorizing arbitrary label noise or random data artifacts degrades out-of-distribution performance without conferring inductive benefit.

## What Action Is Reasonably Justified

Acknowledge the fundamental structural trade-off between strict differential privacy and optimal utility on tail sub-populations; avoid naive claims that zero memorization can be achieved without sacrificing minority-group performance.

## Sources

- Feldman, V. (2020). Does Learning Require Memorization? A Short Tale about a Long Tail. *Proceedings of the 52nd Annual ACM SIGACT Symposium on Theory of Computing (STOC 2020)*, 954-959. https://arxiv.org/abs/1906.05271
