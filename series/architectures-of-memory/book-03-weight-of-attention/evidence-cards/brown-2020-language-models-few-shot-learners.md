---
okf_version: "0.3"
card_id: "brown-2020-language-models-few-shot-learners"
series: "architectures-of-memory"
primary_lens: "technical"
causal_design: "empirical_scaling_benchmark"
certainty_grade: "High"
attenuation_class: "robust_under_20pct"
allowed_verbs: ["demonstrates", "establishes", "shows", "exhibits", "scales"]
forbidden_verbs: ["proves_reasoning", "guarantees_factuality"]
locked_bib_keys: ["brown2020arxiv", "Brown2020"]
contradicts_or_bounds: ["devlin-2019-bert-pretraining-deep-bidirectional"]
canonical_metaphors:
  body_prose: "a massive working memory workspace where in-context examples guide generation without weight updates"
  spoken_tts: "a massive working memory workspace where in-context examples guide generation"
jargon_mappings:
  - term: "In-Context Learning (ICL)"
    notes_definition: "Conditioning model outputs on natural language prompt demonstrations within the context window without updating parametric weights"
escalation_plan:
  1: "Show how parameter scaling from 125M to 175B parameters unlocks few-shot task adaptation."
  2: "Distinguish between parametric memory (weights) and working memory (context window)."
  3: "Connect to corporate onboarding: how clear contextual guidelines allow staff to execute complex procedures without altering structural policy."
type: Evidence Card
title: "Language Models are Few-Shot Learners (Brown et al. 2020)"
description: "Scaling autoregressive Transformer language models to 175 billion parameters unlocks in-context few-shot learning capabilities across diverse tasks without task-specific gradient fine-tuning."
tags: [gpt3, few-shot-learning, in-context-learning, scaling]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-21T21:26:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [mechanism, boundary]
sources:
  - id: brown2020arxiv
    resource: https://arxiv.org/abs/2005.14165
    title: "Brown et al. (2020), Language Models are Few-Shot Learners"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "175 billion parameter GPT-3 architecture with 96 attention layers"
  - "in-context few-shot learning performance scaling with parameter count"
  - "zero-shot, one-shot, and few-shot evaluation across 24 language benchmarks"
relates_to_cards:
  - "EXTENDS:radford-2019-language-models-unsupervised-multitask"
  - "BOUNDS:kaplan-2020-scaling-laws-neural-language-models"
---


# Language Models are Few-Shot Learners

> Domain: large-language-models / few-shot-learning
> Last updated: 2026-10-21
> Status: Stable (landmark foundational scaling benchmark)

## What We Know

Scaling autoregressive Transformer models by orders of magnitude (to 175B parameters in GPT-3) enables few-shot in-context learning where models perform novel linguistic and cognitive tasks guided solely by text prompts in their context window without fine-tuning weights.

## How Confident We Are

**Grade**: High

Replicated across dozens of proprietary and open-weights model families (PaLM, LLaMA, Chinchilla, Claude) showing robust prompt-driven behavioral adaptation at scale.

## Evidence and Causal Assessment

Controlled evaluations comparing zero-shot, one-shot, and few-shot conditions across 40+ datasets isolate prompt demonstration length and parameter scale as the causal determinants of task accuracy.

## Effect Size and Persistence

On SuperGLUE, GPT-3 175B achieved 71.8 in few-shot mode, matching fine-tuned BERT models and demonstrating strong qualitative jumps on translation, arithmetic, and cloze tasks.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. In-context learning performance remains brittle to prompt formatting, token ordering, and demonstration selection, and models can retrieve confident hallucinations when context is ambiguous.

## What Remains Uncertain

The exact mathematical mechanism by which attention layers simulate implicit gradient updates or meta-learning during context processing.

## What This Does Not Mean

This does not mean that the model has acquired new permanent memories; once the context window is cleared, all few-shot demonstrations vanish, leaving the underlying weights unchanged.

## What Action Is Reasonably Justified

Use prompt engineering and few-shot in-context examples for agile task prototyping while relying on external vector retrieval (RAG) for verifiable domain knowledge.

## Sources

- Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., ... & Amodei, D. (2020). Language Models are Few-Shot Learners. *NeurIPS 2020*. DOI: 10.48550/arXiv.2005.14165
