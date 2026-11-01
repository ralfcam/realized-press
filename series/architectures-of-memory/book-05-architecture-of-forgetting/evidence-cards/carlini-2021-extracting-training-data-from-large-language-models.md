---
okf_version: '0.3'
card_id: carlini-2021-extracting-training-data-from-large-language-models
series: architectures-of-memory
primary_lens: technical
causal_role: boundary
plain_english_metaphor: the verbatim memory leak
attenuation_class: robust_under_20pct
type: Evidence Card
title: Verbatim Training Data Extraction Attacks on Autoregressive Language Models
  (Carlini et al. 2021)
description: Black-box sampling and membership inference metrics allow adversaries
  to extract verbatim training sequences—including personally identifiable information—directly
  from pre-trained language model parameters.
tags:
- data-extraction
- memorization
- privacy-attack
- language-models
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
- carlini2020arxiv
sources:
  - id: carlini2020arxiv
    resource: https://arxiv.org/abs/2012.07805
    title: Carlini et al. (2020), Extracting Training Data from Large Language Models---

# Verbatim Training Data Extraction Attacks on Autoregressive Language Models

> Domain: privacy / extraction-attacks
> Last updated: 2026-10-21
> Status: Stable (replicated empirical attack)

## What We Know

Adversaries can extract verbatim text sequences—including names, email addresses, phone numbers, source code snippets, and copyrighted text—from autoregressive language models by generating high-volume samples and ranking them via differential perplexity heuristics.

## How Confident We Are

**Grade**: High

Empirically demonstrated by Carlini et al. (2020/2021) on GPT-2, extracting hundreds of verbatim multi-sentence sequences from training data with zero white-box parameter access, and replicated across larger modern model families (GPT-Neo, LLaMA, Pythia).

## Evidence and Causal Assessment

Controlled extraction experiments comparing perplexity under the target model to perplexity under a smaller reference model or zlib compression ratios isolate memorization as a causal function of repetition in the training corpus and model parameter capacity.

## Effect Size and Persistence

Sequences repeated even a modest number of times (e.g., 10–50 occurrences) in multi-billion-token corpora are memorized near-verbatim. Larger models memorize a substantially higher fraction of their training sets than smaller models trained on the same data.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Extraction success is heterogeneous across token frequencies: highly repeated boilerplate or web headers are trivially extracted, whereas single-occurrence sequences are harder to retrieve without targeted prefix prompting.

## What Remains Uncertain

Whether post-training alignment (RLHF, DPO) genuinely eliminates memorized data traces from underlying weights or merely suppresses generation during benign conversational prompting.

## What This Does Not Mean

A model failing to output private data under standard prompting does not imply that the data was unlearned; adversarial suffix prompting and representation probing can frequently resurrect suppressed training spans.

## What Action Is Reasonably Justified

Aggressively deduplicate and scrub sensitive PII from pre-training web corpora prior to training, and implement differential privacy (DP) or verifiable unlearning protocols where privacy guarantees are legally mandated.

## Sources

- Carlini, N., Tramer, F., Wallace, E., Jagielski, M., Herbert-Voss, A., Lee, K., ... & Raffel, C. (2021). Extracting Training Data from Large Language Models. *USENIX Security Symposium 2021*. https://arxiv.org/abs/2012.07805
