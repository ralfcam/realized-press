---
okf_version: '0.3'
card_id: abadi-2016-deep-learning-with-differential-privacy
series: architectures-of-memory
primary_lens: technical
causal_role: mechanism
plain_english_metaphor: the privacy noise blanket
attenuation_class: robust_under_20pct
type: Evidence Card
title: Differentially Private Stochastic Gradient Descent (Abadi et al. 2016)
description: Clipping per-sample gradient norms and injecting calibrated Gaussian
  noise during stochastic gradient descent (DP-SGD) provides provable (epsilon, delta)-differential
  privacy for deep neural networks.
tags:
- dp-sgd
- differential-privacy
- gradient-clipping
- moments-accountant
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
- abadi2016arxiv
sources:
  - id: abadi2016arxiv
    resource: https://arxiv.org/abs/1607.00133
    title: Abadi et al. (2016), Deep Learning with Differential Privacy
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "differentially private stochastic gradient descent (DP-SGD) with per-sample gradient clipping"
  - "moments accountant technique tracking privacy loss across training epochs"
  - "certified (epsilon = 1.25, delta = 10^-5) privacy on MNIST and CIFAR-10"
relates_to_cards:
  - "EXTENDS:dwork-2006-differential-privacy-noise-calibration"
  - "BOUNDS:mcmahan-2017-federated-learning-communication-efficient"
---


# Differentially Private Stochastic Gradient Descent

> Domain: privacy / dp-sgd
> Last updated: 2026-10-21
> Status: Stable (replicated benchmark framework)

## What We Know

Bounding the influence of individual training examples via per-sample gradient clipping to maximum $L_2$ norm $C$ and adding calibrated Gaussian noise $\mathcal{N}(0, \sigma^2 C^2 I)$ to mini-batch gradients guarantees $(\epsilon, \delta)$-differential privacy for deep neural network training under the Moments Accountant framework.

## How Confident We Are

**Grade**: High

Demonstrated by Abadi et al. (2016) on MNIST (97% accuracy at $\epsilon = 1.25$) and CIFAR-10 (73% accuracy at $\epsilon = 8$), universally replicated in standard libraries (Opacus, TensorFlow Privacy) as the foundational algorithm for private deep learning.

## Evidence and Causal Assessment

Mathematical tracking of higher-order moments of privacy loss random variables (the Moments Accountant) establishes tight composition bounds over thousands of training steps, directly enabling non-convex deep learning with rigorous privacy bounds.

## Effect Size and Persistence

DP-SGD maintains neural network accuracy within modest degradations (e.g., 5–10% accuracy gap on complex vision/language tasks) while providing mathematical protection against membership inference and model inversion attacks for the entire operational life of the weights.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Gradient clipping disproportionately attenuates gradients from under-represented minority classes or rare examples, causing DP-SGD to exhibit disparate impact on model utility across class distributions.

## What Remains Uncertain

Scaling DP-SGD efficiently to billion-parameter autoregressive models without severe throughput slowdowns caused by per-sample gradient computation and communication overhead.

## What This Does Not Mean

Training with DP-SGD does not eliminate utility degradation; strict privacy guarantees ($\epsilon < 2$) require substantial compute overhead and typically incur notable accuracy reductions relative to unconstrained SGD.

## What Action Is Reasonably Justified

Use DP-SGD and the Moments Accountant when training deep neural networks on sensitive user records, medical images, or confidential institutional communications.

## Sources

- Abadi, M., Chu, A., Goodfellow, I., McMahan, H. B., Mironov, I., Talwar, K., & Zhang, L. (2016). Deep Learning with Differential Privacy. *Proceedings of the 2016 ACM SIGSAC Conference on Computer and Communications Security*, 308-318. https://doi.org/10.1145/2976749.2978318
