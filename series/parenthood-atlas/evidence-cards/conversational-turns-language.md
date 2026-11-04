---
type: Evidence Card
title: "Conversational Turns Predict Later Language Better Than Raw Word Counts"
description: "In LENA recordings, adult–child conversational turns at 18–24 months predict school-age language and IQ after SES control more robustly than adult word counts; 18-month expressive vocabulary norms (CDI median ~50 words, range 10-170+) show vast typical variance."
tags: [language, interaction, vocabulary, milestones, measurement]
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
  - id: fenson-2007-cdi
    resource: https://doi.org/10.1037/t11538-000
    title: "Fenson et al. (2007), MacArthur-Bates Communicative Development Inventories (CDI) User's Guide and Technical Manual"
attenuation_tier: "partially_confounded_20_50%"
quantitative_anchors:
  - "LENA automated turn-taking accounting for 14-27% of language variance at age 10 in Gilkerson et al. (N = 146)"
  - "conversational turn counts predict verbal comprehension better than raw adult word counts"
  - "attenuation under parental educational attainment and genetic communicative drive"
  - "Fenson et al. (2007) MacArthur-Bates CDI normative baseline: 18-month median spoken vocabulary of ~50 words (10th percentile ~10 words, 90th percentile ~170+ words, wide typical variation)"
  - "18-month clinical screening threshold: expressive vocabulary under 10-20 words or absence of communicative gestures prompts pediatric evaluation"
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

Language quantity, normative milestone timing, and interactional quality are distinct developmental dimensions. Parents often ask how many words should an 18-month-old say: normative standardization on the MacArthur-Bates Communicative Development Inventories (CDI; Fenson et al. 2007) establishes that the 50th percentile for an 18-month-old child is approximately 50 spoken words, but typical variability spans from 10 words to over 170 words. Automated daylong LENA recordings demonstrate that adult–child conversational turns at 18–24 months account for 14–27% of variance in IQ, verbal comprehension, and vocabulary a decade later after socioeconomic status is controlled, whereas raw adult word counts in the same window are weakened by covariate controls.

## How Confident We Are

**Grade**: Moderate that turns are a stronger *predictor* than raw adult word counts in this design. **Moderate** for CDI population percentile norms at 18 months across broad language cohorts. **Low** that increasing turns or drills mechanically causes later scores (child expressive skill is part of the turn count; families are not randomized). **Low** for the original Hart & Risley “30-million-word gap” as a causal metric.

## Evidence and Causal Assessment

- Fenson et al. (2007), *MacArthur-Bates Communicative Development Inventories (CDI)*: Normative tracking across thousands of toddlers shows that expressive language accelerates non-linearly around 18 months. An 18-month-old child saying 15–20 words is well within the typical distribution if receptive language, gesture pointing, and communicative reciprocity are intact. Asking how many words an 18-month-old child should say requires looking at the wide distribution (10th percentile $\sim 10$ words, median $\sim 50$ words, 90th percentile $\sim 170+$ words) rather than a single cutoff.
- Gilkerson et al. (2018), *Pediatrics*: 146 children with monthly daylong recordings; follow-up at 9–14 years (WISC-V, PPVT, EVT). Observational, automated measurement, SES covariate. Turn-taking was substantially more predictive than raw adult word counts. Child-to-adult reciprocal exchange and shared communicative engagement drive the statistical link.

## Effect Size and Persistence

Reported 14–27% variance at a decade is a prediction interval in one cohort, not an artificial intervention effect. Normative word counts at 18 months show modest rank-order stability that strengthens as grammar emerges after 24 months.

## Bias, Heterogeneity, and Confounding

GI attenuation: **partially confounded (20–50%)** (conversational turn-taking and early vocabulary share unmeasured genetic variance with parental verbal ability and child communicative drive; partially attenuated when family background and parental education are controlled).

LENA classification error; who talks more may already be the more verbal child; SES residual confounding; clinical late bloomers who catch up by age 3 without intervention.

## What Remains Uncertain

Which specific ingredients of a conversational turn (prosody, latency, lexical variety, contingent gaze) carry the predictive association; the extent to which 18-month vocabulary variation reflects temporary maturation lag versus structural differences.

## What This Does Not Mean

Does not mean an 18-month-old child saying fewer than 50 words has a cognitive deficit or that parents should drill flashcards; the typical range at 18 months is wide (10 to 170+ words). Does not mean families with fewer recorded words care less, or that a missed month of conversation writes a child's future.

## What Action Is Reasonably Justified

Support time and natural conditions for contingent reciprocal conversation and shared reading. If an 18-month-old toddler says fewer than 10 words, does not respond to their name, or does not use pointing/gestures, a standard pediatric evaluation and hearing assessment is reasonably justified.

## Sources

- Gilkerson et al. (2018), *Pediatrics* (PMC6192025)
- Fenson et al. (2007), *MacArthur-Bates Communicative Development Inventories: User's Guide and Technical Manual* (2nd ed.), Brookes Publishing
