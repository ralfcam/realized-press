---
type: Evidence Card
title: "Infant Statistical Speech Segmentation"
description: "Eight-month-olds can use transitional probabilities in a brief artificial-speech stream to distinguish word-like units from part-words; this is laboratory segmentation, not proof that statistics alone explain natural language."
tags: [language, learning, infancy]
status: stable
confidence: high-lab; low-transfer
generated: { by: agent:cursor, at: 2026-09-15T20:00:00Z }
stale_after: 2027-03-15T00:00:00Z
atlas_domains: [language, learning]
chapter_hooks: [anomaly, mechanism]
sources:
  - id: saffran-1996-statistical
    resource: https://doi.org/10.1126/science.274.5294.1926
    title: "Saffran, Aslin & Newport (1996), Science, statistical learning by 8-month-old infants"
  - id: aslin-saffran-1998
    resource: https://doi.org/10.1111/1467-9280.00063
    title: "Aslin, Saffran & Newport (1998), Psychological Science, conditional-probability statistics in 8-month-olds"
attenuation_tier: "robust_<20%"
quantitative_anchors:
  - "Saffran, Aslin & Newport (1996) 8-month-olds exposed to continuous stream of synthetic speech with transitional probabilities"
  - "preferential looking time significantly longer for novel part-words than familiar words (p < 0.01, d ~ 0.60)"
  - "rapid statistical extraction achieved after only 2 minutes of continuous auditory exposure without prosodic or pause cues"
relates_to_cards:
  - "EXTENDS:infant-perceptual-narrowing"
  - "BOUNDS:conversational-turns-language"
---


# Infant Statistical Speech Segmentation

> Domain: language
> Last updated: 2026-09-16
> Status: Stable for the *narrow* laboratory claim (`stable-candidates--replication-note.md`). Household transfer remains Low.

## What We Know

Fluent speech does not arrive pre-segmented. In a classic laboratory demonstration, 8-month-old infants exposed to two minutes of a continuous artificial-speech stream later distinguished syllable sequences that had been “words” in that stream from sequences that straddled word boundaries. Transitional probability was the available cue.

## How Confident We Are

**Grade**: High that infants can compute this kind of distributional regularity under controlled conditions. **Low** that two minutes of nonsense speech equals how children find words in a household, or that statistical learning is a complete theory of grammar.

## Evidence and Causal Assessment

Saffran, Aslin & Newport (1996), *Science*: 8-month-olds; familiarization with a continuous stream of three-syllable nonsense words; test preference for words vs part-words. Aslin, Saffran & Newport (1998), *Psychological Science*, held syllable frequency constant and still found discrimination based on *conditional probability* — a conceptual replication of the computational claim, not a household-vocabulary study. The design manipulates the statistics of the input and measures immediate segmentation. It does not assign meaning, social reference, or later vocabulary.

## Effect Size and Persistence

The result is immediate looking/listening preference after a short exposure. Transfer to the child’s language, durability without further exposure, and contribution to real vocabulary are not established by these experiments.

## Bias, Heterogeneity, and Confounding

GI attenuation: **n/a**. Artificial language; small classic samples; laboratory attention. Adjacent Chapter 6 contingency learning is a different action–outcome claim.

## What Remains Uncertain

How statistical cues interact with prosody, social attention, and existing vocabulary; individual differences.

## What This Does Not Mean

Does not mean the infant already knows words in the adult sense, or that a parent must provide a statistically engineered stream. Detecting a regularity is not knowing a meaning.

## What Action Is Reasonably Justified

Ordinary talk in a shared world is consistent with the finding. Segmentation software for infants is not.

## Sources

- Saffran, Aslin & Newport (1996), *Science* 274:1926–1928
- Aslin, Saffran & Newport (1998), *Psychological Science* 9:321–324
