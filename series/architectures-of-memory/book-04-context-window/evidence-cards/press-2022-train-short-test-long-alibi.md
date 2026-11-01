---
okf_version: "0.3"
card_id: "press-2022-train-short-test-long-alibi"
series: "architectures-of-memory"
primary_lens: "technical"
causal_role: "mechanism"
plain_english_metaphor: "the fading horizon"
attenuation_class: "robust (<20%)"
type: Evidence Card
title: "Attention with Linear Biases for Input Length Extrapolation (Press et al. 2021)"
description: "Injecting non-learned, head-specific static negative linear penalties into query-key attention scores (ALiBi) enables Transformer language models to extrapolate smoothly to sequences far longer than those observed during training."
tags: [alibi, length-extrapolation, positional-encoding, context-window]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-21T21:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: press2021arxiv
    resource: https://arxiv.org/abs/2108.12409
    title: "Press et al. (2021), Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation"
---

# Attention with Linear Biases for Input Length Extrapolation

> Domain: attention / alibi
> Last updated: 2026-10-21
> Status: Stable (replicated benchmark finding)

## What We Know

Replacing learned or sinusoidal position embeddings with static, linearly decaying attention biases proportional to token distance ($\text{softmax}(q_i k_j^T - m \cdot (i - j))$) allows autoregressive language models trained on short sequences (e.g., 512 or 1024 tokens) to extrapolate stably to sequences several times longer (e.g., 2048 to 8192+ tokens) without perplexity explosion.

## How Confident We Are

**Grade**: High

Demonstrated by Press, Smith, and Lewis (2021/2022) across 1.3B parameter models evaluated on WikiText-103 and the Toronto Book Corpus, and adopted in production architectures such as BLOOM and MPT-7B for extended-context inference.

## Evidence and Causal Assessment

Controlled comparisons against sinusoidal positional encodings, learned positional embeddings, T5 relative bias, and rotary position embeddings prove that linear distance-proportional penalties prevent attention score saturation on unseen sequence lengths.

## Effect Size and Persistence

Models trained on sequences of length 512 with ALiBi maintained declining or flat validation perplexity when evaluated on sequences up to 2,048 tokens (+4× extrapolation), whereas models with sinusoidal or learned embeddings suffered catastrophic perplexity spikes within 50–100 tokens past the training horizon.

## Bias, Heterogeneity, and Confounding

Classified as: `robust (<20%)`.

Classified as `robust (<20%)`. While ALiBi guarantees stable perplexity extrapolation, its strong monotonic recency bias can impair long-range associative recall and needle-in-a-haystack retrieval tasks at extreme sequence lengths (>32K tokens).

## What Remains Uncertain

The optimal balance between monotonic recency attenuation and non-monotonic positional reasoning across multi-document synthesized contexts.

## What This Does Not Mean

Length extrapolation does not mean a model retains uniform recall over distant tokens; linear decay guarantees mathematical stability rather than lossless associative memory.

## What Action Is Reasonably Justified

Use relative positional encodings such as ALiBi or RoPE with frequency scaling when designing language models intended for context-length expansion beyond their pre-training window.

## Sources

- Press, O., Smith, N. A., & Lewis, M. (2021). Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation. *ICLR 2022*. https://arxiv.org/abs/2108.12409
