---
okf_version: "0.3"
card_id: "liu-2024-lost-in-the-middle-long-context"
series: "architectures-of-memory"
primary_lens: "technical"
causal_role: "constraint"
plain_english_metaphor: "the desk valley"
attenuation_class: "robust (<20%)"
type: Evidence Card
title: "U-Shaped Positional Retrieval Degradation in Long Context Windows (Liu et al. 2024)"
description: "Language models exhibit a pronounced U-shaped accuracy curve on multi-document question answering and key-value retrieval, performing highest when relevant information appears at the very beginning or end of the input context and degrading significantly when placed in the middle."
tags: [context-window, lost-in-the-middle, rag]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-20T23:05:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: Liu_2024
    resource: https://doi.org/10.1162/tacl_a_00638
    title: "Liu et al. (2024), Lost in the Middle: How Language Models Use Long Contexts"
  - id: lewis2020arxiv
    resource: https://arxiv.org/abs/2005.11401
    title: "Lewis et al. (2020), Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "U-shaped retrieval accuracy curve across multi-document QA benchmarks"
  - "performance degradation of over 30% when relevant facts are placed in the middle of context"
  - "robust replication across open and closed long-context models up to 32k tokens"
relates_to_cards:
  - "BOUNDS:press-2022-train-short-test-long-alibi"
  - "BOUNDS:lewis-2020-retrieval-augmented-generation"
---


# U-Shaped Positional Retrieval Degradation in Long Context Windows

> Domain: context-window / rag
> Last updated: 2026-10-20
> Status: Stable (replicated benchmark evidence)

## What We Know

Even when transformer language models accept long input contexts ($16\text{k}$–$100\text{k}+$ tokens), retrieval accuracy for facts embedded within the prompt is strongly position-dependent: models reliably extract information located at the start (primacy) or end (recency) of the context but suffer substantial accuracy drops when the target passage sits in the middle.

## How Confident We Are

**Grade**: High

Demonstrated systematically by Liu et al. (2024) in *Transactions of the Association for Computational Linguistics* across open- and closed-weight models using controlled multi-document QA and synthetic key-value retrieval tasks, and independently replicated across subsequent long-context benchmarks.

## Evidence and Causal Assessment

Liu et al. (2024) hold the exact gold document and distractor set constant while permuting the serial position of the gold passage across 10, 20, and 30 documents. Because content and total token count remain identical across permutations, the U-shaped curve directly isolates serial position inside the context window as the causal driver of retrieval failure.

## Effect Size and Persistence

Across evaluated long-context models, moving the gold document from position 1 (start) or position 20 (end) to position 10 (middle) reduces multi-document QA accuracy by $15$ to $30+$ percentage points—sometimes falling below the model's closed-book (zero-context) accuracy.

## Bias, Heterogeneity, and Confounding

Classified as: `robust (<20%)`.

Classified as `robust (<20%)` in controlled position-permutation experiments. Instruction tuning and RoPE scaling mitigate but do not eliminate mid-context entropy dilution as distractor volume grows.

## What Remains Uncertain

How architectural hybrids combining targeted top-$k$ retrieval (Lewis et al., 2020) with ring/sparse attention trade off latency against mid-context recall on multi-hop reasoning tasks remains an active engineering trade-off.

## What This Does Not Mean

This finding does not mean that long context windows are useless or that models cannot process long documents for summarization; rather, it refutes the assumption that expanding the maximum token horizon makes every token inside the window equally accessible.

## What Action Is Reasonably Justified

Production RAG and context-assembly pipelines should rank and place highest-relevance evidence near the boundaries of the prompt (or restrict retrieved chunk counts to high-precision subsets) rather than dumping puluhan/hundreds of unfiltered documents into a mega-context.

## Sources

- Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the Middle: How Language Models Use Long Contexts. *Transactions of the Association for Computational Linguistics*, 12, 157–173. https://doi.org/10.1162/tacl_a_00638
- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems*, 33. https://arxiv.org/abs/2005.11401
