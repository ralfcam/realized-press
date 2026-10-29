---
type: Evidence Card
title: "In-Context Few-Shot Learning via Foundation Scale (Brown et al. 2020)"
description: "Scaling autoregressive language models to 175B parameters enables in-context learning without gradient updates, highlighting the fundamental divide of in-context learning vs parametric memory where models execute novel tasks conditioned purely on context window demonstrations."
tags: [in-context-learning, few-shot, gpt-3, emergent-capabilities, parametric-memory, in-context-learning-vs-parametric-memory]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T15:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [anomaly, mechanism, boundary]
sources:
  - id: brown2020arxiv
    resource: https://arxiv.org/abs/2005.14165
    title: "Brown et al. (2020), Language Models are Few-Shot Learners"
---

# In-Context Few-Shot Learning via Foundation Scale

> Domain: in-context-learning / scaling
> Last updated: 2026-10-23
> Status: Stable (landmark foundational discovery)

## What We Know

Scaling Transformer language models to hundreds of billions of parameters allows them to perform diverse natural language and reasoning tasks conditioned purely on prompt demonstrations provided inside the context window, without any parameter fine-tuning or gradient adjustments. In the architectural paradigm of in-context learning vs parametric memory, the context window functions as a fast, dynamic inference workspace, contrasting sharply with static knowledge encoded in frozen neural network weights.

## How Confident We Are

**Grade**: High

Evaluated across dozens of benchmark datasets (SuperGLUE, TriviaQA, arithmetic, translation) by Brown et al. (2020) with GPT-3 (175B parameters) and replicated across all subsequent frontier models (PaLM, Llama, Claude, Gemini).

## Evidence and Causal Assessment

Model performance scales monotonically with parameter count on few-shot tasks, while zero-shot and one-shot performance show widening gaps relative to smaller architectures, showing that the context window functions as a dynamic runtime memory environment.

## Effect Size and Persistence

On SuperGLUE, GPT-3 few-shot performance improved from 41.5% at 125M parameters to 71.8% at 175B parameters without gradient modifications; on TriviaQA few-shot accuracy reached 64.3%, competitive with fine-tuned state-of-the-art systems.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Prompt formatting, demonstration ordering, and token distribution introduce high sensitivity into few-shot outputs; nevertheless, the fundamental capability to execute task induction in-context is thoroughly verified.

## What Remains Uncertain

Whether in-context learning executes implicit Bayesian inference, meta-gradient descent in activation space, or complex associative retrieval across parametric weights.

## What This Does Not Mean

In-context learning does not permanently update the model's parametric knowledge; once the context window is cleared, all few-shot demonstrations and ephemeral session facts are instantly forgotten.

## What Action Is Reasonably Justified

Treat the context window as ephemeral working memory rather than durable knowledge storage; persist organizational facts in verified external knowledge bases for retrieval.

## Sources

- Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., Hesse, C., Chen, M., Sigler, E., Litwin, M., Gray, S., Chess, B., Clark, J., Berner, C., McCandlish, S., Radford, A., Sutskever, I., & Amodei, D. (2020). Language Models are Few-Shot Learners. *arXiv preprint arXiv:2005.14165*. https://arxiv.org/abs/2005.14165
