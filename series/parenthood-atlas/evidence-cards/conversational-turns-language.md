---
type: Evidence Card
title: "Conversational Turns Predict Later Language Better Than Raw Word Counts"
description: "In LENA recordings, adult–child conversational turns at 18–24 months predict school-age language and IQ after SES control more robustly than adult word counts; this is prediction, not proof that increasing turns causes those outcomes."
tags: [language, interaction, measurement]
status: draft
confidence: moderate-prediction; low-causation
generated: { by: agent:cursor, at: 2026-09-15T20:00:00Z }
stale_after: 2027-03-15T00:00:00Z
atlas_domains: [language]
chapter_hooks: [evidence, boundary]
sources:
  - id: gilkerson-2018-lena
    resource: https://pmc.ncbi.nlm.nih.gov/articles/PMC6192025/
    title: "Gilkerson et al. (2018), Pediatrics, language experience in the second year predicts late-childhood outcomes"
attenuation_tier: "partially_confounded_20_50%"
quantitative_anchors:
  - "LENA automated turn-taking accounting for 14-27% of language variance at age 10 in Gilkerson et al. (N = 146)"
  - "conversational turn counts predict verbal comprehension better than raw adult word counts"
  - "attenuation under parental educational attainment and genetic communicative drive"
relates_to_cards:
  - "EXTENDS:infant-babbling-as-exploration"
  - "BOUNDS:screen-time-language-development"
  - "MITIGATES:parent-implemented-language"
---


# Conversational Turns Predict Later Language Better Than Raw Word Counts

> Domain: language
> Last updated: 2026-09-15
> Status: Source-audited first pass (CH07-C07/C08)

## What We Know

Language quantity and interactional quality are distinct. Automated daylong recordings can count adult words (AWC) and adult–child conversational turns (CTC). In a longitudinal LENA sample, turns at 18–24 months accounted for 14–27% of variance in IQ, verbal comprehension, and vocabulary about a decade later after socioeconomic status was controlled; adult word counts in the same window were weakened by that control.

## How Confident We Are

**Grade**: Moderate that turns are a stronger *predictor* than raw adult word counts in this design. **Low** that increasing turns would cause those later scores (child speech is part of the turn count; families are not randomized). **Low** for the original Hart & Risley “30-million-word gap” as a causal metric.

## Evidence and Causal Assessment

Gilkerson et al. (2018), *Pediatrics*: 146 children with monthly daylong recordings; follow-up at 9–14 years (WISC-V, PPVT, EVT). Observational, automated measurement, SES covariate. Child-to-adult effects and shared family factors remain. This is stronger identification than a small transcribed SES contrast extrapolated to millions of words; it is not an RCT of “more turns.”

## Effect Size and Persistence

Reported 14–27% variance at a decade is a prediction interval in one cohort, not a portable intervention effect. Persistence is the follow-up itself; causation of persistence is not shown.

## Bias, Heterogeneity, and Confounding

GI attenuation: **untested-in-GI** (conversational turn-taking shares unmeasured genetic variance with parental verbal ability and child communicative drive; not yet tested in sibling-comparison or twin designs).

LENA classification error; who talks more may already be the more verbal child; SES residual confounding; LENA-using families are not a random population.

## What Remains Uncertain

Which ingredient of a “turn” (timing, vocabulary, joint attention, child contribution) carries the association.

## What This Does Not Mean

Does not mean families with fewer recorded words care less, or that a missed month of conversation writes a life. Hart & Risley’s figure is not this card’s claim.

## What Action Is Reasonably Justified

Support time and conditions for contingent exchange. Treating a word-count dashboard as parenting quality is not justified.

## Sources

- Gilkerson et al. (2018), *Pediatrics* (PMC6192025)
