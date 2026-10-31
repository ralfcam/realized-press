---
okf_version: "0.3"
card_id: "elman-1990-simple-recurrent-networks"
series: "architectures-of-memory"
primary_lens: "technical"
causal_design: "empirical_network_simulation_and_grammar_prediction"
certainty_grade: "High"
attenuation_class: "not_applicable"
allowed_verbs: ["shows", "demonstrates", "establishes", "models", "extracts"]
forbidden_verbs: ["proves_unbounded_retention", "solves_long_dependencies"]
locked_bib_keys: ["Elman_1990", "Bengio_1994"]
contradicts_or_bounds: ["rumelhart-1986-backpropagation"]
canonical_metaphors:
  body_prose: "a dynamic echo chamber where hidden activations linger for a few ticks before dissolving into background noise"
  spoken_tts: "a dynamic echo chamber where hidden activations linger for a few ticks before dissolving into background noise"
jargon_mappings:
  - term: "context units"
    notes_definition: "Recurrent feedback buffer copying hidden state activations h_{t-1} as secondary inputs at step t"
escalation_plan:
  1: "Demonstrate how copying hidden states across a single tick captures temporal structure without symbolic rules."
  2: "Examine institutional working memory and temporary post-it notes as organizational context units."
  3: "Reflect on lived present (Bergson's durée) vs. the mechanical buffer of context units."
type: Evidence Card
title: "Simple Recurrent Networks and Context Unit Dynamics (Elman 1990)"
description: "Context units copying previous hidden states allow recurrent networks to process temporal structure and miniature grammars; memory capacity is fundamentally bounded by un-gated recurrent Jacobian decay across sequence length."
tags: [rnn, sequence-learning, context-units, temporal-memory]
status: stable
confidence: high-finite-grammar; low-unbounded-horizon
generated: { by: agent:antigravity, at: 2026-10-21T11:45:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational, philosophical]
chapter_hooks: [mechanism, anomaly, boundary]
sources:
  - id: Elman_1990
    resource: https://doi.org/10.1207/s15516709cog1402_1
    title: "Elman (1990), Cognitive Science, Finding Structure in Time"
  - id: Bengio_1994
    resource: https://doi.org/10.1109/72.279181
    title: "Bengio, Simard, and Frasconi (1994), Learning long-term dependencies with gradient descent is difficult"
---

# Simple Recurrent Networks and Context Unit Dynamics

> Domain: rnn / sequence-learning
> Last updated: 2026-10-21
> Status: Stable (replicated laboratory architecture for local temporal sequences; bounded horizon)

## What We Know

By copying the hidden activation vector $h_{t-1}$ to dedicated context units with fixed unit weights ($w=1.0$) and feeding both current inputs $x_t$ and context activations into the hidden layer at tick $t$, a simple recurrent network (SRN) maintains an internal dynamic state. This architecture enables the network to predict upcoming tokens in sequence streams and implicitly cluster grammatical categories (nouns, verbs) without explicit symbolic look-up tables. However, because backpropagation through time across the un-gated recurrent loop multiplies unconstrained Jacobian matrices, credit assignment across temporal horizons beyond roughly $10$ to $15$ time steps rapidly decays.

## How Confident We Are

**Grade**: High that context feedback enables representation of short temporal dependencies and statistical regularities in finite artificial grammars. **Low** that un-gated simple recurrent networks can reliably learn or maintain unbounded, multi-timescale temporal dependencies under standard gradient descent.

## Evidence and Causal Assessment

Elman (1990) demonstrated across synthetic sentence prediction tasks and letter-sequence streams that SRNs learn internal representations where hierarchical cluster analyses of hidden unit activation vectors reproduce syntactic word categories and agreement rules. Replications confirmed the effectiveness of the SRN for small-to-moderate sequence lengths, while subsequent formal analyses by Bengio, Simard, and Frasconi (1994) and Hochreiter (1991) proved that un-gated recurrent transitions suffer exponential gradient vanishing or explosion whenever learning requires information latching over extended sequences.

## Effect Size and Persistence

In short-range lexical and grammatical prediction tasks ($T < 10$), SRNs reduce prediction perplexity substantially compared to zero-memory feedforward baselines. However, empirical and mathematical sequence persistence exhibits sharp degradation: as dependency span $T$ exceeds $10$–$15$ steps, the probability of successful credit assignment drops toward zero.

## Bias, Heterogeneity, and Confounding

Classified as `n/a` (formal network architecture and empirical benchmark analysis). Performance is confounded by sequence vocabulary size, transition entropy, and the correlation between short-term surface statistics and deep grammatical hierarchy.

## What Remains Uncertain

The optimal trade-off between continuous attractor dynamics and discrete state representations in modern recurrent state-space models (e.g., Mamba, S4) operating on natural language streams.

## What This Does Not Mean

This finding does not mean that connectionist systems lack representations of time, nor does it imply that human working memory is a simple unrolled feedforward buffer; the simple recurrent network is a minimal computational model of temporal context, not an exhaustive account of human cognitive architecture.

## What Action Is Reasonably Justified

Applications requiring sequential processing over short, local context windows can utilize simple recurrent transitions, but tasks requiring long-range credit assignment, cross-sentence context, or memory persistence across extended temporal intervals must incorporate explicit constant-error carousels (LSTM/GRU), structured state-space models, or attention mechanisms.

## Sources

- Elman, J. L. (1990). Finding Structure in Time. *Cognitive Science*, 14(2), 179–211. https://doi.org/10.1207/s15516709cog1402_1
- Bengio, Y., Simard, P., & Frasconi, P. (1994). Learning long-term dependencies with gradient descent is difficult. *IEEE Transactions on Neural Networks*, 5(2), 157–166. https://doi.org/10.1109/72.279181
