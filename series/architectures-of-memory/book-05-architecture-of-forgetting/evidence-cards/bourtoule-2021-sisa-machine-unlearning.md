---
okf_version: '0.3'
card_id: bourtoule-2021-sisa-machine-unlearning
series: architectures-of-memory
primary_lens: technical
causal_role: mechanism
plain_english_metaphor: the sharded compartmentalized vault
attenuation_class: robust_under_20pct
type: Evidence Card
title: Sharded, Isolated, Sliced, and Aggregated (SISA) Exact Machine Unlearning (Bourtoule
  et al. 2021)
description: Exact removal of a training point's influence from a deep neural network
  without full retraining requires architectural partitioning (SISA), trading ensemble
  accuracy and storage overhead for bounded retraining cost.
tags:
- unlearning
- privacy
- forgetting
status: stable
confidence: high
generated:
  by: agent:antigravity
  at: 2026-10-20 23:05:00+00:00
stale_after: '2028-01-01T00:00:00Z'
series_domains:
- technical
chapter_hooks:
- anomaly
- mechanism
- boundary
locked_bib_keys:
- Bourtoule_2021
sources:
  - id: Bourtoule_2021
    resource: https://doi.org/10.1109/sp40001.2021.00019
    title: Bourtoule et al. (2021), Machine Unlearning (IEEE S&P)
  - id: Dwork_2006
    resource: https://doi.org/10.1007/11681878_14
    title: "Dwork, McSherry, Nissim, and Smith (2006), Calibrating Noise to Sensitivity in Private Data Analysis"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "Sharded, Isolated, Sliced, Aggregated (SISA) training framework for machine unlearning"
  - "up to 4.4x speedup in unlearning requests compared to retraining from scratch"
  - "exact unlearning guarantees via certified data partitioning"
relates_to_cards:
  - "EXTENDS:abadi-2016-deep-learning-with-differential-privacy"
  - "BOUNDS:eldan-2023-whos-harry-potter-approximate-unlearning"
---


# Sharded, Isolated, Sliced, and Aggregated (SISA) Exact Machine Unlearning

> Domain: unlearning / privacy
> Last updated: 2026-10-20
> Status: Stable (formal guarantee and systems benchmark)

## What We Know

In standard stochastic gradient descent, every training example updates shared parameters across all subsequent batches, making exact post-hoc removal of a single data point equivalent to retraining from scratch unless the training pipeline partitions data into isolated shards and checkpointed slices (SISA).

## How Confident We Are

**Grade**: High

Demonstrated formally and empirically by Bourtoule et al. (2021) at IEEE Symposium on Security and Privacy, complementary to differential privacy bounds established by Dwork et al. (2006).

## Evidence and Causal Assessment

Bourtoule et al. (2021) prove that partitioning a dataset into $S$ disjoint shards and $R$ sequential slices per shard bounds the retraining work of a single deletion request to one shard from the slice where the point first appeared, yielding exact distributional equivalence to a model trained without that point.

## Effect Size and Persistence

On Purchase, SVHN, and ImageNet benchmarks, SISA reduces retraining time per unlearning request by $2.45\times$ to $4.63\times$ over naive retraining, but degrades ensemble accuracy when shard count $S$ becomes large or when deletion requests arrive non-uniformly across shards.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)` for exact unlearning under bounded request rates. However, adaptive or adversarial deletion streams that hit every shard collapse SISA's speedup back toward full retraining.

## What Remains Uncertain

For frontier foundation models trained at $10^{25}$ FLOPs where SISA sharding is prohibitively degradative, approximate parameter-space unlearning methods still lack tight certified guarantees against extraction attacks.

## What This Does Not Mean

Approximate gradient-ascent or representation-editing "unlearning" heuristics on monolithic LLMs do not provide the certified deletion guarantee of SISA or $(\varepsilon, \delta)$-differential privacy; suppressed facts can often be recovered via rephrasing or few-shot fine-tuning.

## What Action Is Reasonably Justified

Regulated AI systems subject to statutory deletion mandates (GDPR Art. 17) should separate immutable base representations from partitioned, revocable retrieval indexes or sharded adapters rather than relying on unverified weight-editing heuristics.

## Sources

- Bourtoule, L., Chandrasekaran, V., Choquette-Choo, C. A., Jia, H., Travers, A., Zhang, B., Lie, D., & Papernot, N. (2021). Machine Unlearning. *2021 IEEE Symposium on Security and Privacy (SP)*, 141–159. https://doi.org/10.1109/sp40001.2021.00019
- Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006). Calibrating Noise to Sensitivity in Private Data Analysis. *Theory of Cryptography (TCC 2006)*, LNCS 3876, 265–284. https://doi.org/10.1007/11681878_14
