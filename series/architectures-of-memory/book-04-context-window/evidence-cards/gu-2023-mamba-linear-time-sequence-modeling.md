---
type: Evidence Card
title: "Selective State Space Models for Linear-Time Sequence Modeling (Gu & Dao 2023)"
description: "Mamba introduces input-dependent selection mechanisms into structured state space models, achieving linear O(N) sequence scaling, fast inference, and performance matching Transformers on million-length sequences."
tags: [mamba, state-space-models, linear-time, selective-memory]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T15:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: gu2023arxiv
    resource: https://arxiv.org/abs/2312.00752
    title: "Gu & Dao (2023), Mamba: Linear-Time Sequence Modeling with Selective State Spaces"
---

# Selective State Space Models for Linear-Time Sequence Modeling

> Domain: architectures / state-space-models
> Last updated: 2026-10-23
> Status: Stable (major architectural breakthrough)

## What We Know

While standard Transformers incur quadratic $O(N^2)$ computational complexity in sequence length $N$ due to full pairwise attention, Mamba introduces input-dependent selection parameters ($B, C, \Delta$) into structured state space models (SSMs). This allows the model to selectively propagate or discard information along sequence trajectories in linear $O(N)$ time with constant $O(1)$ memory state per step during autoregressive generation.

## How Confident We Are

**Grade**: High

Demonstrated by Gu & Dao (2023) across language modeling, genomics, and audio processing, matching or exceeding Transformer performance at equivalent parameter scales (up to 2.8B parameters) and processing sequences up to 1 million tokens.

## Evidence and Causal Assessment

Traditional linear-time recurrent models failed on language because their time-invariant transition matrices could not filter out irrelevant tokens; Mamba's hardware-aware selective scan dynamically adjusts state transitions based on incoming tokens, restoring content-based associative recall.

## Effect Size and Persistence

Mamba achieves 5× higher inference throughput than Transformers of comparable parameter size and scales linearly with context length, eliminating the quadratic KV cache memory footprint that bounds Transformer deployments.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Pure SSMs can struggle with exact copy-pasting of long random sequences relative to full quadratic attention; hybrid architectures (Mamba-Transformer hybrids) frequently resolve this boundary condition.

## What Remains Uncertain

Scaling Mamba architectures to 70B+ parameter frontiers and evaluating long-term cross-modal pretraining stability.

## What This Does Not Mean

Mamba does not retain infinite sequence memory in lossless form; information is compressed into a fixed-dimensional continuous state vector, meaning historical details undergo lossy decay unless selectively prioritized.

## What Action Is Reasonably Justified

Evaluate selective state space models (Mamba / SSM hybrids) for production domains requiring long-context stream processing and high-throughput real-time inference without massive KV cache infrastructure.

## Sources

- Gu, A., & Dao, T. (2023). Mamba: Linear-Time Sequence Modeling with Selective State Spaces. *arXiv preprint arXiv:2312.00752*. https://arxiv.org/abs/2312.00752
