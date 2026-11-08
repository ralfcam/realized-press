# Changelog

All notable additions and revisions to the evidence atlas are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/), adapted for a research synthesis project rather than software.

Entry types:
- `Added` - new evidence cards or topics
- `Revised` - updated confidence grades, new studies incorporated, corrected attenuation estimates
- `Retracted` - claims withdrawn or downgraded due to failed replication or new genetically informed evidence
- `Structure` - changes to templates, methodology, or repository organization

## [v1.0-gold-master] - 2026-11-08

### SotA Phrasal Poetics, Micro-QA, Co-Located Bottom Footnotes & Multilingual Gold-Master (`ARC-100` – `ARC-105`)
- **Apparatus Sanitization & Same-Page Co-Located Footnotes (`ARC-100`):**
  - Decoupled build-time graph binding (`Evidence Card: <slug>`, `Grade: <grade>`, `Tarjeta de evidencia:`, `Certeza:`) from reader-facing typography across `scripts/render_publishing_pdfs.py`, `scripts/merge_book_chapters.py`, and `scripts/audit_pdf_layout.py`.
  - Replaced chapter-end note dumps with true same-page bottom footnote reservoirs (`141/141` co-located footnotes across `154` KDP 6"×9" pages in EN; `148/148` co-located footnotes across `165` KDP 6"×9" pages in ES) and interactive `<aside epub:type="footnote">` pop-up notes in Kindle EPUB 3.0.
- **Sentence & Paragraph Micro-QA Gates (`ARC-101` & `ARC-102`):**
  - Added `--micro-strict` (Rules 8a–8d: spoken-breath ceiling $\le 35\text{w}$ EN / $\le 38\text{w}$ ES, dense paragraph visual geometry cap $\le 135\text{w}$ and $\le 6$ sentences, uncited empirical claim detector, and sentence-starter cadence linter) to `scripts/audit_manuscript.py`.
- **Frozen-Skeleton Phrasal-Sculpting Pass (`ARC-102`, `ARC-103`, `ARC-104`):**
  - Implemented `style/phrasal-poetics.yml` and `bwe/style_sculptor.py` (`--poetics`, Rule 8e) enforcing kinetic verb density, copula ratio $\le 38\%$, zero nominalization bloat, zero participial tail-drags, and paragraph poetics $\ge 82.0$.
  - Executed the 15-chapter English phrasal-sculpting pass (`FK Grade 8.2–9.4`, `Avg Sent 16.4w–18.4w`, `0` dense paragraphs, `0` cadence flags, `Poetics Score 98.4–99.7`).
- **Spanish Posterior Phrasal-Sculpting Pass & Two-Pass Translation Standard (`ARC-105`):**
  - Codified Directive IX (Mandatory Two-Pass Translation & Posterior Phrasal-Sculpting Standard) across `.agents/rules/narrative-rigor.md` and `series/parenthood-atlas/i18n/es/style/translation-brief.md`.
  - Executed the 15-chapter posterior phrasal-sculpting pass on *El atlas de la crianza* (`Szigriszt 55.6–70.9`, `Avg Sent 16.7w–19.7w`, `0` dense paragraphs reduced from `140`, `0` cadence flags reduced from `7`, `Poetics Score 97.6–99.2`, `100%` EN $\leftrightarrow$ ES citation parity + `7` Spanish regional health anchors).

## [v1.0-rc1] - 2026-10-21

### Commercial Publishing Pipeline & Release Candidate
- **Publishing Harness & Build Artifacts:**
  - Compiled Amazon KDP 6"×9" trade paperback print interior PDF (`parenthood-atlas-kdp-6x9.pdf`, 139 pages).
  - Generated Kindle EPUB 3 reflowable eBook archive (`parenthood-atlas-kdp.epub`, 116 KB).
  - Rendered Patreon / private circulation A4 Reader Edition PDF (`parenthood-atlas-reader-edition.pdf`, 94 pages) and standalone HTML.
  - Generated Gemini TTS Audiobook Transcript (`parenthood-atlas-audiobook.md`, 40,654 words, 93 chunks, ~4.5 hours estimated runtime).
  - Built internal Evidence Briefs Compendium (`parenthood-atlas-evidence-briefs-compendium.pdf`, 10 pages across 9 stable cards).
- **v1.0 Human & Verification Release Gates (Active in Linear Milestone `v1.0`):**
  - Reader Edition circulation and triage (`ARC-53`): awaiting authentic physical proofs and reader feedback.
  - Audio files generation: synthesized mp3 chapters using Gemini Voice Kore.
  - Preprint deposit: PsyArXiv / OSF deposit packet preparation.
  - KDP Print cover: wrap cover formatting, spine width calculation, and Amazon KDP Print Previewer inspection.
  - EPUB verification: `epubcheck` validation.

## [v0.4] - 2026-10-21

### Added
- Authored four new OKF v0.2 domain evidence cards completing the remaining unstarted domain coverage for milestone `v0.4`:
  - `guided-play-efficacy.md` (CH12): Skene 2022 meta-analysis / Weisberg 2016; separates adult-scaffolded guided play in early mathematics/spatial concepts from broad literacy, EF, and home curricula.
  - `delivery-mode-neonatal-transition.md` (CH03): Jain & Dudell 2006 / Curran 2015 sibling design; distinguishes immediate neonatal fluid clearance/stress physiology from long-term neurodevelopment/ASD which attenuates to null in sibling comparisons.
  - `working-memory-cognitive-shifting-infancy.md` (CH11): Diamond 1985 / Zelazo 2006; characterizes the normative developmental progression of working memory delay tolerance and dimensional shifting across infancy and toddlerhood.
  - `routines-and-adult-modeling.md` (CH10): Fiese 2002 / Mindell 2009; frames predictable routines and adult modeling as supportive regulatory scaffolding rather than an autonomous machine that installs moral conscience.
- Catalog expanded to **72** live cards (**9 `stable`**, **63 `draft`**); **127** verified `SOURCES.md` IDs and `sources.bib` BibTeX entries. Chapters 3, 10, 11, and 12 linked and synchronized. Closes Linear issue `ARC-50`.
- Promoted `looking-time-as-measurement.md` from `draft` to `status: stable` under the OKF v0.2 Five-Rule Promotion Gate for the *narrow* methodological measurement claim: infant looking-time methods reliably index perceptual discrimination, stimulus novelty, and attentional allocation under controlled conditions; looking duration is not a transparent readout of rich conceptual knowledge, belief, or innate theories. Triangulated Aslin 2007 (linking-hypothesis logic) with Haith 1998 (critique of perceptual confounding in nativist infant cognition) and ManyBabies Consortium / Frank et al. 2020 (empirical multi-lab measurement dynamics across 2,329 infants and 67 laboratories; DOI 10.1177/2515245919900809). Closes Linear issue `ARC-52`.
- Upgraded Book Writing Environment (BWE) mechanical harness (`scripts/five_rule_check.py` and `.agents/hooks/post_edit_guard.py`):
  - Mechanically audits and enforces explicit GI attenuation tokens across Section 5 of evidence cards.
  - Hardened regex to require structured line matching: `(?:gi attenuation|genetically informed attenuation|confounding|classified as)[:\s]+...`.
  - Enforces required frontmatter schema (`atlas_domains` / `series_domains` and `chapter_hooks`).

### Revised
- **Strict Promotion Gate Enforcement (Fourth Wave Audit):**
  - Demoted 3 candidate cards from `stable` back to `draft`:
    - `prenatal-auditory-learning.md`: In-body Grade is Moderate; promotion requires a narrow High claim.
    - `paternal-age-de-novo-mutations.md`: Kong 2012 and Jónsson 2017 are both Icelandic deCODE genetics under Stefánsson; lacks independent multi-laboratory replication.
    - `dual-language-does-not-confuse.md`: Byers-Heinlein 2010 newborn laboratory phonetic discrimination does not replicate the NAP 2017 developmental milestone impairment claim (construct mismatch).
  - Confirmed exactly **9** `status: stable` cards satisfying all five promotion rules.
- **GI Attenuation Honesty Pass:**
  - Audited all 72 evidence cards. Reclassified 9 cards lacking cited twin/sibling/adoption/MR designs from `partially confounded (20–50%)` to `untested-in-GI`: `behavioral-inhibition-anxiety-risk.md`, `childhood-self-control-gradient.md`, `committed-compliance-not-obedience.md`, `conversational-turns-language.md`, `father-kin-sibling-heterogeneous-network.md`, `household-food-insecurity-health.md`, `routines-and-adult-modeling.md`, `screen-time-language-development.md`, and `toddler-physical-aggression-trajectories.md`. Closes Linear issue `ARC-51`.
- **Chapter 02 Integrity (`chapters/02-first-environment.md`):**
  - Reverted to canonical 2,358 words per `.cursor/rules/02-chapters.mdc` ("Chapter 2 may sit slightly under the floor; do not pad"), removing unsourced word-count padding. Closes Linear issue `ARC-60`.
- **Reader Feedback Log Reset:**
  - Removed simulated triage report and reset `reader-edition-01--feedback-log.csv` to header-only. Reopened `ARC-53` in Linear backlog pending human physical reader circulation.

### Structure
- Reader Edition 0.1 manuscript-sharing packet: froze all 15 curated chapters at post-PR-#18 commit `9f3b151`; added private reader/evidence notes, page-numbered contents, feedback guide/log/triage templates, and two-copy proof-print checklist; generated a deterministic 84-page US Letter PDF, HTML proof, and extraction report. This is private circulation, not a public preprint or KB release. Physical proofs and reader feedback remain human steps. No chapter, evidence-card, grade, source, or archival-draft changes; no `v0.4` tag.
- Harness and research-workflow pass after PR #17: `.cursor/rules/` (four scoped `.mdc` files); exact-version Crossref/PubMed packages in `.cursor/mcp.json`; exact read-only research tools allowlisted for unattended use (not an absolute deny policy); issue templates for `extraction` and `stable-candidate`; input-hardened GitHub Action that comments a non-decisive five-rule checklist without promoting cards. Org-level Issue Fields cannot be created on this User-owned repository (documented). Internal Evidence Brief #1 (six `stable` lab/prevention claims, 2-page PDF) and Chapter 1 preprint PDF are in `preliminary/publishing/` — not posted to PsyArXiv/OSF; public briefs wait until 10–12 `stable` cards. Chapter 1’s source-ID wording and PDF table rendering were corrected. No auto-merge. No `v0.4` tag. No new cards. Sleep/attachment/screen theory not rewritten. Archival drafts untouched.
- Second-pass promotions after `v0.3`: flipped **four** additional *narrow* laboratory claims to `status: stable` (contingency learning; social referencing; still-face procedure effect; perceptual narrowing after adding Kuhl 1992). Looking-time, dual-language, babbling, Lillard, and deferred imitation remain `draft` with explicit five-rule reasons. Deferred-imitation YAML/description aligned to Meltzoff 1988 (14-month one-week delay). Light manuscript pass: Ch. 5–9 name the new stables; Ch. 11 one-line that EF is not Chapter 4 co-regulation. Sleep/attachment/screen theory not rewritten. No new cards or chapters. Catalog is now 68 cards (7 `stable`; 61 `draft`); 114 verified `SOURCES.md` IDs. Do not tag `v0.4` from this pass.
- Tagged **`v0.3`** on `main` at `21d1a0d` (PR #15 merge). See `preliminary/releases/v0.3-slice.md`.
- Began quality deepening after the 15-chapter arc: second-pass audit of all 65 draft cards; cross-chapter consistency note (regulation, causation, risk, resilience, attachment, institutions); manuscript pass naming remaining-domain cards in Ch. 1/10/12/13/15 and adding a Science / Interpretation / Art close to Chapter 14. Aligned YAML compound `confidence` with in-body grades on manuscript-core cards. Looking-time, perceptual-narrowing, and contingency remain `draft`. Sleep/attachment/screen theory not rewritten. **No additional card moved to `status: stable`.**
- Tagged **`v0.2`** on `main` at `9bbc2d9` (PR #14 merge). See `preliminary/releases/v0.2-slice.md`.
- Promoted a curated, voice-checked Chapter 15 (`chapters/15-three-years.md`) in the Appendix B range. Archival `chapter 15` untouched. C15-S1 not double-extracted. Continuity, Dunedin, and ordinary-resilience cards named; Watts/BEIP/preschool RCT reconciled, not rewritten. **No card moved to `status: stable`.**
- Source-audited remaining unstarted domains into five first-pass draft cards: Warneken helping, outdoor/risky play, parental leave, food insecurity, preconception nutrition beyond folate. Folate NTD card not re-estimated. Sperm-epigenetic stories remain excluded. **Now tagged** as `v0.3`.
- Promoted curated, voice-checked Chapters 8–13 into `chapters/` in the Appendix B range (Expanding World through Ecology). Reviews under `preliminary/drafts-chapters/reviews/`. Archival originals untouched. **Now tagged** as `v0.2`.
- Defined the v0.3 release slice (`preliminary/releases/v0.3-slice.md`): curated Chapter 15 plus remaining-domain cards. **Now tagged** on `main` at `21d1a0d`.
- Tagged **`v0.1`** on `main` at `c7c2a7a` (PR #12 merge). See `preliminary/releases/v0.1-slice.md`. Chapter 2 curated copy remains ~2,358 words (slightly under Appendix B 2,500); not padded.
- Began Chapter 15 triage (age-three waypoint). Evidence map, source audit, and three first-pass draft cards. Archival `chapter 15` untouched. Temperament, Watts delay, EF, BEIP, and preschool-RCT cards reconciled, not rewritten. **No card moved to `status: stable`.**
- Defined the v0.2 release slice (`preliminary/releases/v0.2-slice.md`): curated Chapters 8–13. **Now tagged** on `main` at `9bbc2d9`. Chapter 15 is the v0.3 manuscript center.
- Began Part II remainder: Chapter 8 father/kin/sibling card; first triage, maps, and draft cards for Chapters 10 (rules/behavior) and 13 (ecology). Archival drafts untouched. Sleep/attachment/screen theory not rewritten. EF, delay, childcare, BEIP, and preschool-RCT cards reconciled, not rewritten. **No card moved to `status: stable`.**
- Second editorial pass on curated Chapters 6 and 7: named embodiment, exploration, physical-reasoning, deferred-imitation, joint-attention, and parent-implemented cards in-body; recorded Saffran laboratory `stable` and the repaired Madigan/Jing screen IDs. Voice reviews updated. Archival drafts untouched. Lengths remain in the Appendix B range.
- Defined the v0.1 release slice (`preliminary/releases/v0.1-slice.md`): Prenatal through Language (Ch. 1–7) plus What Actually Works (Ch. 14). **Now tagged** on `main` at `c7c2a7a`.
- Began Part II triage for Chapters 9, 11, and 12 (emotional revolution, developing executive, play). Evidence maps, source audits, and first-pass draft cards added. Archival drafts untouched. Sleep/attachment/screen theory not rewritten. Co-regulation and Watts delay cards reconciled, not rewritten.
- Trimmed curated Chapter 14 (`chapters/14-what-actually-works.md`) to the Appendix B range (~2,970 words). Archival `preliminary/drafts-chapters/chapter 14` untouched. Voice review updated.
- Wrote a replication note for the three strongest physiology/lab `stable` candidates and flipped **three** cards to `status: stable` for *narrow* claims only: folate NTD, Saffran laboratory segmentation, neonatal cardiopulmonary sequence. YAML/in-body grades matched; Czeizel 1992, Aslin 1998, and Hillman 2012 added as independent sources. `who-anc-2016` demoted from folate identification. Looking-time and perceptual-narrowing remain `draft`.
- Promoted a curated, voice-checked Chapter 1 (`chapters/01-before-the-child-is-born.md`) in the Appendix B range. Leftover seed `chapters/01-first-environment.md` removed; Chapter 2 remains `chapters/02-first-environment.md`. Archival draft untouched.
- Began second-wave Chapter 8 triage and evidence map. Social-referencing, multiple-caregiver, and peer cards added; childcare quality vs quantity reconciled, not rewritten. Stranger anxiety ≠ insecure attachment; group care ≠ deprivation.
- Closed remaining Chapter 6 extraction gaps (embodiment, exploration-as-sampling, physical reasoning, deferred imitation) and the Chapter 7 parent-implemented language gap.
- Recorded explicit dispositions for the five catalog IDs without a journal DOI in `SOURCES.md` (NIH/WHO/Kramer identified; `hiscock-2016` remains retired). **No card moved to `status: stable`.**
- Staged a curated Chapter 14 (`chapters/14-what-actually-works.md`) that strips 29 `:contentReference` artifacts. Archival draft untouched. Over Appendix B length; later trim after Part II cards.
- Named first `stable` candidates (`preliminary/research/extraction/stable-promotion-candidates.md`). Physiology/lab cards are the realistic path; none flipped.
- Started extraction plans for preconception, play, and social-beyond-attachment.
- Classified replication/genetically informed attenuation for every live card (`preliminary/research/extraction/catalog-wide-replication-attenuation.md`). **No card moved to `status: stable`.**
- Citation-repaired `screen-time-language-development.md`: `madigan-2020` now points at Madigan et al. 2020 *JAMA Pediatrics* (DOI 10.1001/jamapediatrics.2020.0327). Jing, Ye, Kirkorian & Mares 2023 *Child Development* is a separate vocabulary meta-analysis (`jing-2023-cdev`). Grade unchanged.
- Reconciled GitHub history: [PR #4](https://github.com/ralfcam/parenthood-atlas/pull/4) was never squash-merged. Its unique files (Ch. 3 transition/SSC, Ch. 4 co-regulation/BEIP, selected-card re-audit, curated Ch. 6) first reached `main` in the [PR #5](https://github.com/ralfcam/parenthood-atlas/pull/5) squash (`4bba8a7`) because that branch was stacked on `cursor/ch3-ch4-ch6-7d96`. Do not merge PR #4; it is superseded and would regress later Chapter 4 and catalog work.
- Repaired the five remaining no-DOI listings and ran a catalog-wide Retraction Watch dump (`preliminary/research/extraction/five-listings-and-retraction-watch-dump.md`). `hiscock-2016` retired and replaced by Mindell 2006, Gradisar 2016, and Bilgin & Wolke 2020. WHO/NIH/Kramer 1987 now have IRIS or NIH identifiers. **No card moved to `status: stable`.**
- Promoted a curated, voice-checked Chapter 5 (`chapters/05-becoming-a-mind.md`) in the Appendix B range. Archival draft untouched. Looking-time, attention, object-permanence, and joint-attention cards added; narrowing, statistical-segmentation, and contingency cards reconciled, not rewritten.
- Recovered DOIs for 15 of 20 previously Crossref-unchecked catalog IDs and queried Crossref/PubMed/Retraction Watch (`preliminary/research/extraction/doi-recovery-retraction-watch.md`). Five IDs remain without a journal DOI (WHO, NICHD report, 1987 bulletin, mismatched sleep listing). **No card moved to `status: stable`.**
- Promoted curated, voice-checked Chapter 3 (`chapters/03-the-great-transition.md`) and Chapter 4 (`chapters/04-regulatory-relationship.md`, replacing the 10-step seed). Archival drafts untouched.
- Source-audited Chapter 4 feeding-as-regulation (Black & Aboud 2011). Sleep and attachment cards still not rewritten in that pass. `hiscock-2016` was later retired.
- Source-audited Chapter 7 language claims into draft cards (perceptual narrowing, statistical segmentation, conversational turns, dual-language). Existing `screen-time-language-development.md` and `prenatal-auditory-learning.md` reconciled, not rewritten. C07-P1 vs C07-S1 hash-compared (not identical).
- Promoted a curated, voice-checked Chapter 7 to `chapters/07-the-birth-of-language.md` (Appendix B range). Archival `preliminary/drafts-chapters/chapter 7` unchanged.
- Ran a catalog-wide Crossref/PubMed retraction lookup (`preliminary/research/extraction/catalog-wide-retraction-search.md`). No retraction or expression-of-concern titles among DOI-resolved records. Cochrane updates are new review versions. **No card moved to `status: stable`.**
- Source-audited remaining Chapter 3 C04/C05/C07 (crying, feeding coordination, preterm group risk). Mode of delivery still held.
- Source-audited Chapter 3 transition physiology and Chapter 4 co-regulation/deprivation claims into draft cards; C03-P1 vs C03-S1 hash-compared (not identical). Sleep and attachment cards reconciled, not rewritten. Mode of delivery still held.
- Began a selected-card replication/bias re-audit (`preliminary/research/extraction/selected-cards--replication-bias-reaudit.md`). No card moved to `status: stable`.
- Finished a curated, voice-checked Chapter 6 expansion at `chapters/06-the-mind-in-motion.md` (Appendix B range). Archival `preliminary/drafts-chapters/chapter 6` unchanged.
- Initialized repository: README, CONTRIBUTING guide, evidence card template, and directory structure.
- Added `REPO_DIGEST.md`, a repository map covering the three-layer layout (preliminary workbench, OKF evidence cards, canonical manuscript), current inventories, the 8- vs 15-chapter numbering split, and known gaps. Linked from `index.md` and `README.md`.
- Renamed `preliminary/drafts-chapters/chapter 16` to `chapter 15` so the filename matches its Chapter 15 heading (*Three Years: What Has Been Built?*).
- Added the preliminary corpus governance layer: `preliminary/MANIFEST.md` (inventory of every uploaded file), naming convention for future curated copies (originals not renamed), `triage/` (Part I sequence plus Ch. 1–2 notes), `research/extraction/` (atomic-claim pipeline and Chapter 2 Evidence Map), and `drafts-chapters/reviews/` (voice review kept separate from draft text).
- Adopted the 15-chapter draft sequence as the working TOC in `chapters/_OUTLINE.md`; kept seed outlines as sketches for draft Ch. 2 and 4.
- Added `SPEC.md` as a pointer to the external OKF v0.2 specification.
- Synced `evidence-cards/_TEMPLATE.md` with live OKF frontmatter (`type`, `title`, `description`, `tags`, `status`, `confidence`, `generated`, `stale_after`, `sources`; optional `atlas_domains` / `chapter_hooks`).
- Added Chapter 3 and Chapter 4 triage notes (Part I). Archival drafts not overwritten.
- Promoted a curated, voice-checked Chapter 2 to `chapters/02-first-environment.md`. Relocated the regulatory seed sketch to `chapters/04-regulatory-relationship.md`. Archival `preliminary/drafts-chapters/chapter 2` unchanged.

### Added
- Populated evidence-cards/ with 8 preliminary evidence cards (prenatal maternal stress/anxiety, breastfeeding and cognitive development, early childcare quality, screen time and language development, responsive caregiving and attachment interventions, infant sleep training, self-regulation/delay of gratification, preschool early education RCTs) plus an index.
- Source-audited Chapter 2 claims C05 and C07: added `prenatal-auditory-learning.md` and `prenatal-folate-ntd.md`.
- Source-audited remaining Chapter 2 claims C01–C04 and C08–C12: added timing, placenta, neural-construction, fetal-autonomic, iodine, FASD, tobacco-growth, mixtures, and fetal-growth cards. C13 held as interpretive continuity on the growth card.
- Source-audited Chapter 3 C02/C06 and Chapter 4 C01/C02: added neonatal-transition, skin-to-skin, co-regulation, and severe-deprivation cards. Added a Chapter 6 contingency-learning card to support the curated expansion.
- Source-audited Chapter 7 C02/C03/C07–C09: added perceptual-narrowing, statistical-segmentation, conversational-turns, and dual-language cards. Screen-time card reconciled, not rewritten.
- Source-audited remaining Chapter 3 C04/C05/C07: added crying-as-signal, suck–swallow–breathe, and preterm group-risk cards.
- Source-audited Chapter 4 C04: added `responsive-feeding-as-regulation.md`.
- Source-audited Chapter 5 C01/C03/C06/C07: added looking-time, attention, object-permanence, and joint-attention cards. Narrowing, statistical-segmentation, and contingency cards reconciled, not rewritten.
- Source-audited remaining Chapter 7 C05/C06: added pointing and babbling cards. Screen-time card IDs repaired, not re-theorized.
- Source-audited Chapter 1 paternal-age (Kong 2012) and remaining Chapter 6/7/8 claims: paternal-age, social referencing, multiple-caregiver attachments, toddler peer interaction, embodied perception–action, exploration-as-sampling, physical reasoning, deferred imitation, parent-implemented language. Sleep/attachment/screen theory not rewritten.
- Source-audited Chapter 9 still-face, temperament, and behavioral inhibition; Chapter 11 EF unity/diversity and inhibitory control; Chapter 12 symbolic play and Lillard overclaim. Watts delay and co-regulation cards reconciled, not rewritten.
- Source-audited Chapter 8 remainder (fathers/kin/siblings), Chapter 10 committed compliance / aggression trajectories / physical punishment, and Chapter 13 income-cash (Baby’s First Years) / neighborhood mobility (MTO). Sleep/attachment/screen theory not rewritten.

- Source-audited Chapter 15 waypoint claims: rank-order continuity (Roberts 2000), childhood self-control gradient (Moffitt 2011), ordinary resilience (Masten 2001). Watts delay, temperament, BEIP, and preschool RCT reconciled, not rewritten.
- Source-audited remaining unstarted domains: Warneken 2006, Brussoni 2015, Carneiro 2015, Cook 2004, Dean 2014.

### Revised
- Aligned YAML `confidence` on all eight first-pass cards with in-body grades (cards remain `status: draft`).
- Resolved the 12 previously unresolved `SOURCES.md` citations (two were already verified; two titles were corrected to the matching papers).
- Citation-repaired `infant-sleep-training.md`: retired `hiscock-2016`; identified Mindell 2006, Gradisar 2016, and Bilgin & Wolke 2020. Harm claim and Low-to-Moderate grade unchanged.
- Citation-repaired `screen-time-language-development.md`: separated Madigan 2020 *JAMA Pediatrics* from Jing et al. 2023 *Child Development*. Low-to-Moderate grade unchanged.
- Re-audited folate, Saffran, and neonatal-transition cards against the five promotion rules. Compound YAML on folate (`high-ntd; low-other-anomalies-cognition`). Added Czeizel 1992, Aslin 1998, Hillman 2012. Narrow claims moved to `status: stable`.
- Aligned YAML `confidence` with in-body compound grades on manuscript-core draft cards (timing, fetal growth, auditory, mixtures, stress, narrowing, resilience, dual-language, pretend, MTO, BEIP, EF/inhibition/symbolic, remaining-domain cards). Grades themselves unchanged. Sleep/attachment/screen YAML not reopened.

## [v0.3] — 2026-09-16

Annotated tag `v0.3` on `main` at `21d1a0d` (PR #15 merge). Snapshot: v0.2 plus voice-checked curated Chapter 15 (age-three waypoint) and five remaining-domain draft cards. 68 cards (3 `stable` for a narrow claim; 65 `draft`); 113 verified sources on that commit. See `preliminary/releases/v0.3-slice.md`.

## [v0.2] — 2026-09-16

Annotated tag `v0.2` on `main` at `9bbc2d9` (PR #14 merge). Snapshot: v0.1 plus voice-checked curated Chapters 8–13 (Expanding World through Ecology). 63 cards (3 `stable` for a narrow claim; 60 `draft`); 108 verified sources on that commit. See `preliminary/releases/v0.2-slice.md`.

## [v0.1] — 2026-09-16

Annotated tag `v0.1` on `main` at `c7c2a7a` (PR #12 merge). Snapshot: Prenatal through Language (Ch. 1–7) + What Actually Works (Ch. 14). 60 cards (3 `stable` for a narrow claim; 57 `draft`); 105 verified sources. See `preliminary/releases/v0.1-slice.md`. Chapter 2 curated copy is ~2,358 words (slightly under Appendix B); not padded.

## [2026-09-14]

### Structure
- Retrofitted all 8 existing evidence cards with Open Knowledge Format (OKF) v0.2 frontmatter (`type`, `title`, `description`, `tags`, `status`, `generated`, `stale_after`, `sources`), making the bundle machine-readable and agent-traversable without changing card bodies.
- Replaced `evidence-cards/_INDEX.md` with OKF-reserved `evidence-cards/index.md` (no frontmatter, per OKF section 8).
- Added a bundle-root `index.md` declaring `okf_version: "0.2"` and linking to the evidence-cards directory and core documentation files, per OKF section 8/12.
- All cards remain `status: draft` pending confidence-grade assignment and deeper source audit; `stale_after` set to 2027-03-14 as a 6-month re-audit horizon.

## [2026-09-14b]

### Structure
- Added `SOURCES.md`, a bundle-root Master Source Catalog cataloging every reference cited across the 8 evidence cards: 19 sources with verified, resolvable resource links (mirrored in the file's OKF frontmatter `sources` array) and 12 sources named in card bibliographies during the initial pass but not yet matched to a stable verified link ("Unresolved Citations"). Those 12 were resolved on 2026-09-15; see `[Unreleased]`.
- Updated `index.md` and `evidence-cards/index.md` to reference `SOURCES.md`.
- Established a maintenance rule: all future evidence-card additions/revisions must update `SOURCES.md` in the same commit.
