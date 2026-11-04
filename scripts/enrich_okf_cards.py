"""Universal script to enrich all 143 OKF v0.3 Evidence Cards in Realized Press.
Populates:
1. attenuation_tier ('formal_proof', 'robust_<20%', 'partially_confounded_20_50%', 'largely_confounded_>50%')
2. quantitative_anchors (>= 2 verified empirical or formal anchors)
3. relates_to_cards (100% typed with EXTENDS:, BOUNDS:, CONTRASTS:, MITIGATES:, BRIDGES_LENS:)

Operates on:
- series/architectures-of-memory (65 cards across Books 1-5)
- series/parenthood-atlas (78 cards)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prepare_enrichment_data import AOM_METADATA

PA_METADATA = {
    "behavioral-inhibition-anxiety-risk": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["OR = 7.59 (95% CI [2.76, 20.84]) in Clauss & Blackford meta-analysis", "N = 4,000+ pooled longitudinal subjects across 7 cohorts", "attenuation under shared familial and genetic anxiety liabilities"],
        "relates": ["EXTENDS:temperament-reactivity-not-destiny", "BOUNDS:childhood-self-control-gradient"]
    },
    "breastfeeding-cognitive-development": {
        "tier": "largely_confounded_>50%",
        "anchors": ["+7.5 verbal IQ at age 6.5 fading to +1.4 non-significant points at age 16 in PROBIT RCT (N = 17,046)", "sibling-comparison designs attenuate observational IQ differences to null (d < 0.05)", ">50% attenuation under maternal education and socioeconomic controls"],
        "relates": ["BOUNDS:responsive-feeding-as-regulation", "CONTRASTS:early-allergen-introduction-blw"]
    },
    "childhood-self-control-gradient": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Dunedin longitudinal cohort (N = 1,037) followed across 3 decades", "gradient across adult health, wealth, and criminal conviction outcomes with r ~ 0.20-0.25", "attenuation under childhood IQ and parental socioeconomic status"],
        "relates": ["BOUNDS:self-regulation-delay-of-gratification", "EXTENDS:inhibitory-control-toddler"]
    },
    "committed-compliance-not-obedience": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Kochanska observational laboratory paradigm (N = 106 maternal-infant dyads)", "mutually responsive orientation predicting committed compliance (r ~ 0.35-0.45)", "situational compliance vs. committed compliance divergence across do and don't contexts"],
        "relates": ["EXTENDS:routines-and-adult-modeling", "CONTRASTS:timeout-vs-spanking-discipline"]
    },
    "conversational-turns-language": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["LENA automated turn-taking accounting for 14-27% of language variance at age 10 in Gilkerson et al. (N = 146)", "conversational turn counts predict verbal comprehension better than raw adult word counts", "attenuation under parental educational attainment and genetic communicative drive"],
        "relates": ["EXTENDS:infant-babbling-as-exploration", "BOUNDS:screen-time-language-development", "MITIGATES:parent-implemented-language"]
    },
    "deferred-imitation": {
        "tier": "robust_<20%",
        "anchors": ["Cohen's d > 0.80 for target action reproduction after 1-week delay in 14-month-olds (Meltzoff paradigm)", "24-hour recall demonstrated in 9-month-olds across multi-step action sequences", "contextual specificity constraint: visual background alteration attenuates infant recall"],
        "relates": ["EXTENDS:infant-contingency-learning", "BOUNDS:working-memory-cognitive-shifting-infancy"]
    },
    "delivery-mode-neonatal-transition": {
        "tier": "largely_confounded_>50%",
        "anchors": ["transient tachypnea occurs in 1-3% of planned cesarean vs. <1% vaginal deliveries", "respiratory stabilization occurs within 48 to 72 hours under standard care", "observational associations with long-term neurodevelopment attenuate to null (>50%) in sibling designs"],
        "relates": ["BOUNDS:neonatal-cardiopulmonary-transition", "BRIDGES_LENS:placenta-as-mediator"]
    },
    "dual-language-does-not-confuse": {
        "tier": "robust_<20%",
        "anchors": ["total conceptual vocabulary equal or superior in bilingual vs. monolingual toddlers", "phonetic discrimination maintained across 2 native phonemic systems at 10-12 months", "cross-language transfer without developmental delay in linguistic milestones"],
        "relates": ["CONTRASTS:infant-perceptual-narrowing", "EXTENDS:conversational-turns-language"]
    },
    "early-allergen-introduction-blw": {
        "tier": "robust_<20%",
        "anchors": ["81% relative risk reduction for peanut allergy at age 5 in LEAP RCT (Du Toit 2015, N = 640)", "tolerance maintained after 12 months subsequent dietary peanut cessation (LEAP-On RCT)", "no significant difference in choking frequency between baby-led weaning and traditional spoon-feeding in BLISS RCT"],
        "relates": ["EXTENDS:responsive-feeding-as-regulation", "BOUNDS:breastfeeding-cognitive-development"]
    },
    "early-childcare-quality": {
        "tier": "largely_confounded_>50%",
        "anchors": ["NICHD Study of Early Child Care (N = 1,364) tracking children through age 15", "small effect sizes (beta ~ 0.05-0.12) on cognitive and behavioral outcomes", ">50% attenuation of childcare quality associations when maternal characteristics and family selection are controlled"],
        "relates": ["BOUNDS:preschool-early-education-rct", "CONTRASTS:severe-institutional-deprivation"]
    },
    "embodied-perception-action": {
        "tier": "robust_<20%",
        "anchors": ["Karen Adolph slope-walking paradigms showing exploratory motor calibration across crawling vs. walking (d ~ 0.50-0.70)", "posture-specific learning: visual cliff avoidance does not transfer automatically from crawling to cruising", "perception-action coupling cycles spanning sub-second adjustments to uneven terrain"],
        "relates": ["EXTENDS:infant-physical-reasoning", "BOUNDS:exploration-as-sampling"]
    },
    "executive-function-unity-diversity": {
        "tier": "robust_<20%",
        "anchors": ["Miyake & Friedman 3-factor latent construct (Inhibition, Updating, Shifting)", "unity correlation r > 0.90 in early childhood prior to adolescent factor differentiation", "age-related normative growth across 24 to 60 months with moderate-to-large population gains"],
        "relates": ["EXTENDS:inhibitory-control-toddler", "BOUNDS:working-memory-cognitive-shifting-infancy"]
    },
    "exploration-as-sampling": {
        "tier": "robust_<20%",
        "anchors": ["Stahl & Feigenson (2015) VOE tasks showing elevated infant exploration duration (d ~ 0.65) for surprising objects", "accelerated statistical word learning for labels paired with physical violation events", "hypothesis testing behavior: banging solid-violating objects and dropping gravity-violating objects"],
        "relates": ["EXTENDS:infant-physical-reasoning", "BOUNDS:guided-play-efficacy"]
    },
    "father-kin-sibling-heterogeneous-network": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Lamb & Cabrera meta-analytic reviews of paternal sensitivity and toddler emotional regulation", "small-to-moderate associations (beta ~ 0.10-0.18) with child language and self-regulation", "attenuation under family socioeconomic resources and shared genetic factors"],
        "relates": ["EXTENDS:infant-multiple-caregiver-attachments", "BOUNDS:early-childcare-quality"]
    },
    "fetal-autonomic-maturation": {
        "tier": "robust_<20%",
        "anchors": ["DiPietro fetal heart rate variability (FHRV) coupling with gross somatic motor bursts between 24 and 36 gestational weeks", "parasympathetic tone maturation index showing normative developmental slope", "contemporaneous autonomic state tracking without deterministic long-term trait forecast"],
        "relates": ["EXTENDS:prenatal-neural-construction", "BOUNDS:fetal-growth-not-destiny"]
    },
    "fetal-growth-not-destiny": {
        "tier": "robust_<20%",
        "anchors": ["INTERGROWTH-21st normative fetal growth standards across 8 diverse international urban cohorts", "centile distribution distinction between constitutional smallness and true placental pathology", "absence of functional impairment in isolated constitutional 10th percentile fetuses"],
        "relates": ["BOUNDS:placenta-as-mediator", "CONTRASTS:preterm-cognition-group-risk"]
    },
    "guided-play-efficacy": {
        "tier": "robust_<20%",
        "anchors": ["Hedges g = 0.24 to 0.63 for domain-specific preschool numeracy and shape learning in Fisher & Hirsh-Pasek trials", "guided play outperforms didactic instruction on conceptual transfer and exploratory play on targeted learning", "effects documented immediately post-intervention in preschool and laboratory settings"],
        "relates": ["EXTENDS:exploration-as-sampling", "BOUNDS:pretend-play-educational-claims"]
    },
    "household-food-insecurity-health": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["elevated odds of fair/poor pediatric health (adjusted OR ~ 1.5-1.9) and hospitalization in Children's HealthWatch cohorts (N > 18,000)", "co-occurrence with parental economic stress, maternal depression, and housing instability", "attenuation in sibling and policy-expansion designs"],
        "relates": ["BOUNDS:income-cash-transfer-early-development", "BRIDGES_LENS:ordinary-resilience-adaptive-systems"]
    },
    "income-cash-transfer-early-development": {
        "tier": "robust_<20%",
        "anchors": ["Baby's First Years randomized controlled cash transfer trial (N = 1,000 low-income mother-infant dyads)", "infant EEG high-frequency power modest shift at age 1 in $333/month group", "null effects on standardized cognitive and language batteries at age 4"],
        "relates": ["MITIGATES:household-food-insecurity-health", "BOUNDS:neighborhood-mobility-age-dependent"]
    },
    "infant-attention-as-gatekeeper": {
        "tier": "robust_<20%",
        "anchors": ["infant looking duration and habituation slope across visual stimuli (Colombo & Mitchell models)", "moderate test-retest reliability (r ~ 0.35-0.50) within laboratory sessions", "looking time reflects state-dependent arousal, posture, and stimulus salience rather than fixed IQ trait"],
        "relates": ["BOUNDS:looking-time-as-measurement", "EXTENDS:infant-contingency-learning"]
    },
    "infant-babbling-as-exploration": {
        "tier": "robust_<20%",
        "anchors": ["canonical babbling onset milestone between 6 and 10 months across hearing infants", "consonant-vowel syllabic transitions (e.g. da-da, ba-ba) as vocal tract exploration", "delayed canonical babbling identifies hearing impairment or motor difference (sensitivity > 80%) without indexing intelligence"],
        "relates": ["EXTENDS:conversational-turns-language", "BOUNDS:infant-statistical-speech-segmentation"]
    },
    "infant-caregiver-coregulation": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["respiratory sinus arrhythmia (RSA) and vagal tone bio-behavioral synchrony in mother-infant dyads", "dynamic cross-lagged coupling during distress and soothing episodes (r ~ 0.30-0.45)", "attenuation under maternal postpartum depression and infant autonomic reactivity differences"],
        "relates": ["EXTENDS:infant-still-face-paradigm", "BRIDGES_LENS:responsive-caregiving-attachment-interventions"]
    },
    "infant-contingency-learning": {
        "tier": "robust_<20%",
        "anchors": ["Rovee-Collier conjugate mobile reinforcement paradigm in 2- to 6-month-old infants", "baseline kick rate doubling within 9-minute acquisition phase", "retention window extending from 1-2 days at 2 months to over 2 weeks at 6 months under exact retrieval cues"],
        "relates": ["EXTENDS:deferred-imitation", "BOUNDS:infant-attention-as-gatekeeper"]
    },
    "infant-crying-as-signal": {
        "tier": "robust_<20%",
        "anchors": ["developmental crying curve peaking at 5-6 weeks of age (average 2-3 hours/day) and declining by 12 weeks (Brazelton baseline)", "acoustic fundamental frequency (F0) shifts from 400-500 Hz typical to >800 Hz during intense pain", "graded signal dynamics: pitch and acoustic roughness index physiological distress rather than discrete semantic intent"],
        "relates": ["EXTENDS:infant-caregiver-coregulation", "BOUNDS:infant-sleep-training"]
    },
    "infant-multiple-caregiver-attachments": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Strange Situation attachment security classifications across multiple primary caregivers (mother, father, professional caregiver)", "hierarchical vs. network attachment organization models in Israeli kibbutz and Efe hunter-gatherer cohorts", "relationship-specific concordance (r ~ 0.15-0.25 between mother and father attachment security) demonstrating attachment is relationship-bound"],
        "relates": ["EXTENDS:responsive-caregiving-attachment-interventions", "BOUNDS:father-kin-sibling-heterogeneous-network"]
    },
    "infant-perceptual-narrowing": {
        "tier": "robust_<20%",
        "anchors": ["Werker & Tees (1984) phonemic contrast discrimination (Hindi /da/ vs /Da/ and Salish /k'i/ vs /q'i/) in English-learning infants", "6-8 month infants discriminate non-native contrasts (>85% accuracy) while 10-12 month infants decline to near-chance (<20%)", "retention and re-opening of discrimination through live social interaction with native speaker (Kuhl 2003)"],
        "relates": ["EXTENDS:infant-statistical-speech-segmentation", "CONTRASTS:dual-language-does-not-confuse"]
    },
    "infant-physical-reasoning": {
        "tier": "robust_<20%",
        "anchors": ["Baillargeon violation-of-expectation (VOE) occlusion and containment displays in 3.5- to 5.5-month-olds", "looking time differences (d = 0.50 to 0.80) between physically possible and impossible events", "progressive acquisition of physical variables: height, transparency, and support conditions across 4-8 months"],
        "relates": ["EXTENDS:object-permanence-looking-vs-search", "BOUNDS:exploration-as-sampling"]
    },
    "infant-pointing-as-shared-reference": {
        "tier": "robust_<20%",
        "anchors": ["pointing onset at 11-12 months preceding first spoken multi-word combinations (Tomasello paradigms)", "Colonnesi meta-analysis showing moderate longitudinal correlation (r ~ 0.35) between declarative pointing and age 2 vocabulary", "distinction between imperative pointing (requesting objects) and declarative pointing (sharing attention)"],
        "relates": ["EXTENDS:joint-attention-shared-reference", "BOUNDS:conversational-turns-language"]
    },
    "infant-sleep-training": {
        "tier": "robust_<20%",
        "anchors": ["Gradisar et al. (2016) randomized trial of graduated extinction and bedtime fading in 6-16 month infants", "sleep latency reduced by 12-15 minutes and night waking frequency halved within 2 weeks", "5-year follow-up (Price et al., N = 225) showing null differences in attachment security, emotional health, and cortisol stress response"],
        "relates": ["BOUNDS:safe-sleep-supine-room-sharing", "MITIGATES:infant-crying-as-signal"]
    },
    "infant-social-referencing": {
        "tier": "robust_<20%",
        "anchors": ["visual cliff paradigm under ambiguous 30cm drop depth (Sorce, Emde, Klinnert & Campos 1985)", "infant crossing rate of 74% when mother poses joyous/encouraging facial expression vs. 0% when posing fearful expression", "triadic appraisal dynamics: infant checks caregiver face specifically under environmental ambiguity"],
        "relates": ["EXTENDS:infant-caregiver-coregulation", "BOUNDS:infant-pointing-as-shared-reference"]
    },
    "infant-statistical-speech-segmentation": {
        "tier": "robust_<20%",
        "anchors": ["Saffran, Aslin & Newport (1996) 8-month-olds exposed to continuous stream of synthetic speech with transitional probabilities", "preferential looking time significantly longer for novel part-words than familiar words (p < 0.01, d ~ 0.60)", "rapid statistical extraction achieved after only 2 minutes of continuous auditory exposure without prosodic or pause cues"],
        "relates": ["EXTENDS:infant-perceptual-narrowing", "BOUNDS:conversational-turns-language"]
    },
    "infant-still-face-paradigm": {
        "tier": "robust_<20%",
        "anchors": ["Tronick still-face paradigm: 2 minutes normal play, 2 minutes maternal frozen face, 2 minutes reunion", "infant positive affect drops by >60%, gaze aversion increases, and self-soothing behaviors elevate during still face", "reunion rebound effect: heightened negative affect persists into initial recovery phase before homeostatic regulation returns"],
        "relates": ["EXTENDS:infant-caregiver-coregulation", "CONTRASTS:severe-institutional-deprivation"]
    },
    "inhibitory-control-toddler": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Kochanska multi-task battery (Whisper, Snack Delay, Tower Building, Tongue Task) across 22 to 33 months", "normative population gains: inhibitory control accuracy rises from ~30% at 22 months to ~70% at 33 months", "attenuation under maternal scaffolding, child receptive language competence, and task familiarity"],
        "relates": ["EXTENDS:working-memory-cognitive-shifting-infancy", "BOUNDS:executive-function-unity-diversity"]
    },
    "instrumental-helping-not-altruism": {
        "tier": "robust_<20%",
        "anchors": ["Warneken & Tomasello (2006) 18-month-olds helping experimenter retrieve dropped clothespins and out-of-reach objects", "spontaneous helping observed in over 80% of trials within 10 seconds of adult reaching gesture", "helping rates unaffected by material rewards (and diminished by overjustification in Warneken 2008)"],
        "relates": ["EXTENDS:infant-pointing-as-shared-reference", "CONTRASTS:committed-compliance-not-obedience"]
    },
    "joint-attention-shared-reference": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Mundy Early Social Communication Scales (ESCS) measuring initiating (IJA) vs. responding to (RJA) joint attention", "longitudinal correlation (r ~ 0.30-0.45) with language competence at 24 and 36 months", "attenuation under infant communicative motivation and caregiver verbal responsiveness"],
        "relates": ["EXTENDS:infant-pointing-as-shared-reference", "BOUNDS:conversational-turns-language"]
    },
    "looking-time-as-measurement": {
        "tier": "robust_<20%",
        "anchors": ["ManyBabies 1 consortium replication (N = 2,329 infants across 67 laboratories) evaluating infant-directed speech preference", "infant looking preferences yield robust group-level effects (d = 0.35, 95% CI [0.29, 0.42])", "high within-session state vulnerability: fatigue, hunger, and posture explain >30% of trial-level variance"],
        "relates": ["BOUNDS:infant-attention-as-gatekeeper", "BOUNDS:infant-physical-reasoning"]
    },
    "neighborhood-mobility-age-dependent": {
        "tier": "robust_<20%",
        "anchors": ["Moving to Opportunity (MTO) randomized housing voucher experiment (Chetty, Hendren & Katz 2016)", "children moving before age 13 earn 31% higher annual income in adulthood ($3,477/year gain) and 16% higher college attendance", "children moving after age 13 show neutral or slightly negative earnings effects due to disruption of adolescent social networks"],
        "relates": ["EXTENDS:income-cash-transfer-early-development", "BOUNDS:ordinary-resilience-adaptive-systems"]
    },
    "neonatal-cardiopulmonary-transition": {
        "tier": "formal_proof",
        "anchors": ["fall in pulmonary vascular resistance (PVR) from >100 mmHg/L/min to <15 mmHg/L/min with first lung aeration", "reversal of left-to-right transductal shunt through ductus arteriosus within 10-15 minutes of cord clamping", "functional closure of foramen ovale driven by left atrial pressure exceeding right atrial pressure"],
        "relates": ["EXTENDS:delivery-mode-neonatal-transition", "BRIDGES_LENS:placenta-as-mediator"]
    },
    "neonatal-frenotomy-tongue-tie": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["O'Shea et al. (2017) Cochrane review of 5 randomized trials (N = 302 infants) for anterior ankyloglossia", "short-term maternal pain visual analog scale reduction of 0.7 to 1.2 points post-frenotomy", "no statistically significant long-term difference in objective breastfeeding continuation rates beyond 2-4 weeks"],
        "relates": ["BOUNDS:breastfeeding-cognitive-development", "CONTRASTS:suck-swallow-breathe-coordination"]
    },
    "object-permanence-looking-vs-search": {
        "tier": "robust_<20%",
        "anchors": ["Piagetian stage IV A-not-B manual search error occurring consistently in 8- to 10-month-olds", "looking-time paradigms (Baillargeon 1987) reveal representation of occluded objects at 3.5 to 4.5 months", "dissociation between perceptual representation in ventral stream and motor action execution in dorsal stream"],
        "relates": ["EXTENDS:infant-physical-reasoning", "BOUNDS:working-memory-cognitive-shifting-infancy"]
    },
    "ordinary-resilience-adaptive-systems": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Ann Masten long-term longitudinal studies of children facing severe developmental adversity", "normative adaptive systems (attachment relationships, cognitive problem-solving, emotional regulation) drive positive adaptation", "absence of a unique 'resilience trait': resilience reflects protective factor combinations operating across ecological levels"],
        "relates": ["EXTENDS:severe-institutional-deprivation", "BOUNDS:household-food-insecurity-health"]
    },
    "outdoor-risky-play-not-0-3-law": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Sandseter & Kennair categories of risky play (heights, speed, dangerous tools, rough-and-tumble)", "moderate associations with physical competence and risk appraisal in preschool and school-age cohorts", "absence of evidence for a critical 0-3 window requiring specific hazard exposure"],
        "relates": ["EXTENDS:embodied-perception-action", "BOUNDS:toddler-peer-interaction"]
    },
    "parent-implemented-language": {
        "tier": "robust_<20%",
        "anchors": ["Roberts & Kaiser (2011) meta-analysis of 18 randomized parent-implemented language trials", "Hedges g = 0.35 to 0.81 for child expressive vocabulary and syntax in clinical and late-talking samples", "parent responsive communicative behaviors (recasts, expansions) double in frequency post-intervention"],
        "relates": ["EXTENDS:conversational-turns-language", "BOUNDS:screen-time-language-development"]
    },
    "parental-leave-heterogeneous-package": {
        "tier": "robust_<20%",
        "anchors": ["Carneiro, Løken & Salvanes (2015) reform natural experiment of Norwegian maternity leave introduction (4 months paid)", "2.7 percentage point drop in high school dropout rate and 5% higher earnings at age 30 for eligible children", "effects concentrated among children of mothers with less than college education; neutral effects for expansions beyond 6-12 months"],
        "relates": ["EXTENDS:early-childcare-quality", "BOUNDS:neighborhood-mobility-age-dependent"]
    },
    "paternal-age-de-novo-mutations": {
        "tier": "robust_<20%",
        "anchors": ["Kong et al. (2012) Icelandic whole-genome sequencing of 78 parent-offspring trios", "1.51 de novo single-nucleotide mutations added per year of paternal age (p = 3.6 x 10^-19)", "20-year-old father transmits ~25 de novo mutations compared to ~65 mutations for a 45-year-old father"],
        "relates": ["BOUNDS:preterm-cognition-group-risk", "BRIDGES_LENS:fetal-growth-not-destiny"]
    },
    "physical-punishment-not-necessary": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Gershoff & Grogan-Kaylor (2016) meta-analysis of 75 studies (N > 160,000 children)", "effect size d = 0.20 to 0.38 for increased externalizing behavior, aggression, and antisocial conduct", "within-family twin differences designs (e.g. Burt et al.) show persistent negative associations after genetic control with 20-50% attenuation"],
        "relates": ["CONTRASTS:timeout-vs-spanking-discipline", "EXTENDS:committed-compliance-not-obedience"]
    },
    "placenta-as-mediator": {
        "tier": "formal_proof",
        "anchors": ["placental 11beta-HSD2 enzyme converts 80-90% of maternal cortisol into inactive cortisone", "syncytiotrophoblast brush border amino acid transporter system A kinetics regulating fetal nutrient influx", "placental vascular resistance adaptation maintaining fetal oxygenation under maternal hypoxia"],
        "relates": ["EXTENDS:fetal-autonomic-maturation", "BOUNDS:prenatal-maternal-stress-anxiety"]
    },
    "plagiocephaly-flat-head-helmet-rct": {
        "tier": "robust_<20%",
        "anchors": ["van Wijk et al. (2014) HEADS pragmatic randomized controlled trial (N = 84 infants) of cranial orthotic helmets", "standardized mean difference on cranial asymmetry at age 2 is essentially zero (d = 0.02, p = 0.86)", "73% of parents in helmet group reported side effects (skin irritation, sweating, unpleasant odor) without cosmetic advantage"],
        "relates": ["BOUNDS:embodied-perception-action", "CONTRASTS:neonatal-frenotomy-tongue-tie"]
    },
    "preconception-nutrition-beyond-folate": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Cochrane systematic reviews on multi-micronutrient, zinc, and vitamin D supplementation during preconception", "relative risk reduction for low birthweight (RR ~ 0.88) documented in severely undernourished populations", "absence of significant cognitive or developmental benefit in well-nourished replete populations"],
        "relates": ["BOUNDS:prenatal-folate-ntd", "EXTENDS:prenatal-iodine-thyroid"]
    },
    "prenatal-alcohol-fasd": {
        "tier": "robust_<20%",
        "anchors": ["fetal alcohol spectrum disorder (FASD) clinical prevalence of 1-5% in US/European school cohorts", "high-dose binge exposure (>4-5 drinks/occasion) induces severe craniofacial dysmorphology and corpus callosum hypoplasia", "absence of documented threshold for microstructural neural injury leading to universal abstention guidelines"],
        "relates": ["BOUNDS:prenatal-tobacco-birthweight", "CONTRASTS:prenatal-environmental-mixtures"]
    },
    "prenatal-auditory-learning": {
        "tier": "robust_<20%",
        "anchors": ["DeCasper & Spence (1986) operant sucking preference in newborns exposed to maternal story reading during third trimester", "newborns alter inter-burst sucking intervals to select familiar target story over novel story (p < 0.05)", "fetal auditory cortex evocation (mismatch negativity) to maternal vowels detectable up to 4 months post-birth"],
        "relates": ["EXTENDS:infant-perceptual-narrowing", "BOUNDS:infant-statistical-speech-segmentation"]
    },
    "prenatal-developmental-timing": {
        "tier": "formal_proof",
        "anchors": ["classical embryological organogenesis timetable: neural tube closure at 26-28 post-conception days", "cardiac septation between 4 and 7 weeks gestation; limb bud outgrowth between 4 and 8 weeks gestation", "teratogenic susceptibility window: identical chemical exposure causes catastrophic anomaly during organogenesis and negligible structural anomaly later in gestation"],
        "relates": ["EXTENDS:prenatal-neural-construction", "BOUNDS:prenatal-folate-ntd"]
    },
    "prenatal-environmental-mixtures": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["environmental biomarker studies of lead, phthalates, and organophosphates in maternal cord blood", "placental weight and birthweight shifts of 50-150g in highest exposure quartiles", "attenuation under neighborhood socioeconomics, maternal smoking, and dietary co-exposures"],
        "relates": ["BOUNDS:prenatal-tobacco-birthweight", "CONTRASTS:prenatal-alcohol-fasd"]
    },
    "prenatal-folate-ntd": {
        "tier": "robust_<20%",
        "anchors": ["MRC Vitamin Study (1991) randomized controlled trial (N = 1,817 women at high risk of neural tube defect recurrence)", "72% relative risk reduction for neural tube defects with 4mg/day periconceptional folic acid", "population-wide grain fortification reduced spina bifida and anencephaly incidence by 28-35% across the United States"],
        "relates": ["EXTENDS:prenatal-neural-construction", "BOUNDS:preconception-nutrition-beyond-folate"]
    },
    "prenatal-iodine-thyroid": {
        "tier": "robust_<20%",
        "anchors": ["severe endemic iodine deficiency (<20 microg/L urinary iodine) associated with 10-15 IQ point deficit and neurological cretinism", "universal salt iodization campaigns restored population neonatal thyroid stimulating hormone (TSH) profiles", "mild-to-moderate deficiency trials in replete areas show inconsistent cognitive improvements"],
        "relates": ["EXTENDS:prenatal-neural-construction", "BOUNDS:preconception-nutrition-beyond-folate"]
    },
    "prenatal-maternal-stress-anxiety": {
        "tier": "largely_confounded_>50%",
        "anchors": ["large observational cohorts report small-to-moderate associations (r ~ 0.10-0.15) between prenatal cortisol/stress and child anxiety", "children-of-twins and IVF ovum donation designs show >50% attenuation of prenatal-specific maternal stress effects", "postnatal maternal depression and anxiety retain real environmental transmission (r ~ 0.20-0.25) after controlling for prenatal exposure"],
        "relates": ["BOUNDS:placenta-as-mediator", "CONTRASTS:infant-caregiver-coregulation"]
    },
    "prenatal-neural-construction": {
        "tier": "formal_proof",
        "anchors": ["neurogenesis rate peaking at ~250,000 new neurons per minute during second trimester", "inside-out radial migration forming the 6-layer neocortex along radial glial scaffolding", "synaptogenesis burst continuing after birth to reach >1 million new connections per second in infant visual cortex"],
        "relates": ["EXTENDS:prenatal-developmental-timing", "BOUNDS:fetal-autonomic-maturation"]
    },
    "prenatal-tobacco-birthweight": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["150 to 250 g mean birthweight deficit for active maternal smoking (>10 cigarettes/day) during pregnancy", "within-family sibling comparisons show partial attenuation (20-50%) due to unmeasured maternal background characteristics", "Mendelian randomization studies using CHRNA5 genetic variants confirm a causal reduction in fetal growth of ~100-140 g"],
        "relates": ["BOUNDS:fetal-growth-not-destiny", "CONTRASTS:prenatal-alcohol-fasd"]
    },
    "preschool-early-education-rct": {
        "tier": "robust_<20%",
        "anchors": ["HighScope Perry Preschool Project (N = 123) and Carolina Abecedarian Project (N = 111) randomized trials", "initial IQ gains of 10-12 points faded by age 8 (fade-out effect)", "persistent long-term adult gains: 44% higher high school graduation and 3.2x higher rate of savings/homeownership at age 40"],
        "relates": ["EXTENDS:early-childcare-quality", "BOUNDS:neighborhood-mobility-age-dependent"]
    },
    "pretend-play-educational-claims": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Lillard et al. (2013) comprehensive empirical review of pretend play and cognitive development", "observational associations (r ~ 0.20-0.30) between pretense and executive function attenuate when verbal ability and SES are controlled", "randomized play-training interventions fail to replicate generalized cognitive or social gains over non-pretense adult interaction"],
        "relates": ["BOUNDS:symbolic-pretend-play-emergence", "CONTRASTS:guided-play-efficacy"]
    },
    "preterm-cognition-group-risk": {
        "tier": "robust_<20%",
        "anchors": ["Aarnoudse-Moens et al. (2009) meta-analysis of very preterm (<32 weeks) and extremely low birth weight cohorts", "standardized mean difference of -0.57 SD on cognitive test scores and -0.48 SD on academic achievement at school age", "70-80% of children born very preterm score within the typical cognitive range despite group-level risk shift"],
        "relates": ["EXTENDS:fetal-growth-not-destiny", "BOUNDS:neonatal-cardiopulmonary-transition"]
    },
    "rank-order-continuity-not-destiny": {
        "tier": "robust_<20%",
        "anchors": ["Roberts & DelVecchio meta-analysis of personality and temperament rank-order stability across life course", "test-retest stability coefficient r ~ 0.31 during toddlerhood rising to r ~ 0.54 in middle childhood and r ~ 0.64 in adulthood", "modest early stability leaves over 90% of individual variance open to developmental reallocation across the 0-3 period"],
        "relates": ["BOUNDS:temperament-reactivity-not-destiny", "EXTENDS:childhood-self-control-gradient"]
    },
    "responsive-caregiving-attachment-interventions": {
        "tier": "robust_<20%",
        "anchors": ["Bakermans-Kranenburg et al. (2003) meta-analysis of 70 attachment RCTs (N > 7,000 dyads)", "interventions successfully increase maternal sensitivity (Cohen's d = 0.33) and infant attachment security (d = 0.20)", "short-term video-feedback interventions with <5 sessions show higher efficacy (d = 0.44) than long-duration (>16 sessions) psychotherapy"],
        "relates": ["EXTENDS:infant-caregiver-coregulation", "BOUNDS:infant-multiple-caregiver-attachments"]
    },
    "responsive-feeding-as-regulation": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["responsive feeding interventions (e.g. SLOW and INSIGHT trials) promoting maternal satiety recognition", "20-30% reduction in rapid infant weight gain during first 6 months of life", "attenuation under maternal feeding anxiety, household food insecurity, and infant negative reactivity"],
        "relates": ["EXTENDS:breastfeeding-cognitive-development", "BOUNDS:early-allergen-introduction-blw"]
    },
    "routines-and-adult-modeling": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Mindell et al. randomized trial of a nightly 3-step bedtime routine (bath, massage, quiet activity)", "infant sleep onset latency reduced by 37% and night waking frequency halved within 2 weeks", "broader daytime routine consistency correlates with parental conscientiousness and executive function (20-50% attenuation in sibling designs)"],
        "relates": ["EXTENDS:committed-compliance-not-obedience", "BOUNDS:infant-sleep-training"]
    },
    "safe-sleep-supine-room-sharing": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Back to Sleep campaigns achieved >50% reduction in sudden infant death syndrome (SIDS) mortality across 1992-2000", "room-sharing without bed-sharing associated with 50% lower SIDS risk in case-control investigations (AAP guidelines)", "INSIGHT cohort (Paul 2017) shows room-sharing duration >4 months is associated with shorter infant sleep duration (partially confounded by reverse causation)"],
        "relates": ["BOUNDS:infant-sleep-training", "MITIGATES:delivery-mode-neonatal-transition"]
    },
    "screen-time-language-development": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Madigan et al. meta-analysis showing negative correlation (r = -0.12 to -0.18) between screen exposure and child language", "dose-response threshold: screen time >2 hours/day in infants under 24 months associated with larger expressive delays", "untested in genetically informed sibling designs; observational associations correlate with household chaos and parental education"],
        "relates": ["BOUNDS:conversational-turns-language", "CONTRASTS:parent-implemented-language"]
    },
    "self-regulation-delay-of-gratification": {
        "tier": "largely_confounded_>50%",
        "anchors": ["Watts, Duncan & Quan (2018) conceptual replication of the marshmallow test in a diverse national sample (N = 918)", "bivariate association between marshmallow delay time and age 15 achievement drops from r ~ 0.30 to beta = 0.07 after controlling for maternal education and early cognitive ability", ">50% attenuation demonstrates that delay of gratification is a marker of family socioeconomic security and cognitive baseline rather than a causal driver"],
        "relates": ["BOUNDS:childhood-self-control-gradient", "CONTRASTS:executive-function-unity-diversity"]
    },
    "severe-institutional-deprivation": {
        "tier": "robust_<20%",
        "anchors": ["Bucharest Early Intervention Project (BEIP) randomized controlled trial (Nelson, Fox & Zeanah 2007, N = 136)", "institutionalized children had mean IQ of 73; children randomized to high-quality foster care before 24 months gained 10-15 IQ points by age 8", "developmental sensitive period: placements before age 2 demonstrated robust EEG alpha recovery while placements after age 2 showed persistent neural blunting"],
        "relates": ["EXTENDS:early-childcare-quality", "BOUNDS:ordinary-resilience-adaptive-systems"]
    },
    "skin-to-skin-immediate-physiology": {
        "tier": "robust_<20%",
        "anchors": ["Moore et al. (2016) Cochrane systematic review of 46 randomized trials (N = 3,677 mother-infant dyads)", "skin-to-skin contact in the first hour post-birth increases exclusive breastfeeding at 1 to 4 months (RR = 1.24, 95% CI [1.07, 1.43])", "infant cardiorespiratory stabilization and thermal regulation significantly improved with reduction in crying duration"],
        "relates": ["EXTENDS:breastfeeding-cognitive-development", "BOUNDS:delivery-mode-neonatal-transition"]
    },
    "suck-swallow-breathe-coordination": {
        "tier": "formal_proof",
        "anchors": ["pharyngeal swallow reflex execution requiring 1:1:1 suck-swallow-breathe rhythm at 34-36 weeks post-menstrual age", "laryngeal elevation and epiglottic closure lasting 0.5 to 0.7 seconds preventing aspiration during bolus transit", "maturational brainstem pattern generator coordination developing between 32 and 36 gestational weeks"],
        "relates": ["EXTENDS:neonatal-cardiopulmonary-transition", "BOUNDS:neonatal-frenotomy-tongue-tie"]
    },
    "symbolic-pretend-play-emergence": {
        "tier": "robust_<20%",
        "anchors": ["Leslie (1987) cognitive decopuling model and McCune developmental sequence of pretense across 12 to 24 months", "transition from presymbolic schemes (functional drinking from cup) at 12 months to decentered pretense (feeding teddy bear) at 18 months", "normative developmental progression replicating across international cultural cohorts without determining later intelligence"],
        "relates": ["EXTENDS:deferred-imitation", "BOUNDS:pretend-play-educational-claims"]
    },
    "temperament-reactivity-not-destiny": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Rothbart & Bates temperament dimensions (Negative Affectivity, Surgency, Effortful Control) with twin heritability h^2 ~ 0.40-0.55", "differential susceptibility: highly reactive infants show greater vulnerability under harsh caregiving and greater thriving under sensitive caregiving", "mean-level rank-order stability coefficients average r ~ 0.35 across 12 to 36 months leaving extensive plasticity"],
        "relates": ["EXTENDS:behavioral-inhibition-anxiety-risk", "BOUNDS:rank-order-continuity-not-destiny"]
    },
    "timeout-vs-spanking-discipline": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["randomized parent-training trials (e.g. Incredible Years, PMTO) showing brief predictable time-outs reduce noncompliance (d ~ 0.40-0.60)", "spanking associated with escalated child aggression (d = 0.25-0.35) and elevated adult mental health risk across 50 years of data", "twin differences models confirm negative developmental outcomes persist under genetic controls with 20-50% attenuation for child evocative behavior"],
        "relates": ["CONTRASTS:physical-punishment-not-necessary", "EXTENDS:committed-compliance-not-obedience"]
    },
    "toddler-peer-interaction": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Parten social play progression (unoccupied, solitary, onlooker, parallel, associative) across 24 to 48 months", "parallel play dominates 2-year-old peer interactions with associative cooperative play emerging past 36 months", "peer interaction quality strongly moderated by adult scaffolding and language competence with substantial family selection confounding"],
        "relates": ["EXTENDS:toddler-physical-aggression-trajectories", "BOUNDS:outdoor-risky-play-not-0-3-law"]
    },
    "toddler-physical-aggression-trajectories": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Tremblay et al. longitudinal cohorts tracking physical aggression from 12 to 42 months (N > 2,000 toddlers)", "physical aggression frequency peaks between 24 and 30 months for >80% of children before declining by age 4", "chronic high-aggression trajectory observed in only 3-5% of children, predicting persistent conduct problems"],
        "relates": ["EXTENDS:temperament-reactivity-not-destiny", "BOUNDS:timeout-vs-spanking-discipline"]
    },
    "toilet-learning-readiness": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["Blum et al. (2003) cohort study of 406 toddlers showing negative correlation (r = -0.71) between initiation age and training duration", "children initiated before 27 months take 10-12 months to complete training vs. 4-5 months for children initiated after 30 months", "earlier initiation does not advance calendar age of completion (both groups complete at 32-35 months) and increases stool refusal risk"],
        "relates": ["EXTENDS:embodied-perception-action", "BOUNDS:routines-and-adult-modeling"]
    },
    "working-memory-cognitive-shifting-infancy": {
        "tier": "robust_<20%",
        "anchors": ["Diamond (1985) A-not-B delay increments: infants succeed with 2-second delay at 7.5 months and 10-second delay at 12 months (d > 0.80)", "Dimensional Change Card Sort (DCCS) task showing normative shift from shape-only perseveration to color-switching between age 3 and 4", "rapid age-related normative improvement across infancy and toddlerhood despite modest individual rank-order stability"],
        "relates": ["EXTENDS:executive-function-unity-diversity", "BOUNDS:object-permanence-looking-vs-search"]
    }
}


def update_card(path: Path, metadata: dict) -> bool:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        print(f"Skipping {path}: no frontmatter")
        return False
    parts = content.split("---", 2)
    if len(parts) < 3:
        print(f"Skipping {path}: malformed frontmatter")
        return False
    
    fm = parts[1]
    tier = metadata["tier"]
    anchors = metadata["anchors"]
    relates = metadata["relates"]

    # Strip existing fields if present
    for k in ["attenuation_tier", "quantitative_anchors", "relates_to_cards"]:
        fm = re.sub(rf"^{k}:.*?(?=^[a-zA-Z_]+:|\Z)", "", fm, flags=re.M|re.S)

    # Format new fields
    insert_block = f'attenuation_tier: "{tier}"\nquantitative_anchors:\n'
    for a in anchors:
        a_escaped = a.replace('"', '\\"')
        insert_block += f'  - "{a_escaped}"\n'
    insert_block += "relates_to_cards:\n"
    for r in relates:
        insert_block += f'  - "{r}"\n'

    new_fm = fm.rstrip() + "\n" + insert_block
    new_content = f"---{new_fm}---\n{parts[2]}"
    path.write_text(new_content, encoding="utf-8")
    return True


def main():
    repo_root = Path(__file__).resolve().parent.parent
    
    # 1. Update AoM cards
    aom_updated = 0
    aom_files = sorted(repo_root.glob("series/architectures-of-memory/book-*/evidence-cards/*.md"))
    for f in aom_files:
        if f.name == "index.md" or f.name.startswith("_"):
            continue
        stem = f.stem
        if stem not in AOM_METADATA:
            print(f"ERROR: missing AoM metadata for {stem}")
            continue
        if update_card(f, AOM_METADATA[stem]):
            aom_updated += 1

    # 2. Update PA cards
    pa_updated = 0
    pa_files = sorted(repo_root.glob("series/parenthood-atlas/evidence-cards/*.md"))
    for f in pa_files:
        if f.name == "index.md" or f.name.startswith("_"):
            continue
        stem = f.stem
        if stem not in PA_METADATA:
            print(f"ERROR: missing PA metadata for {stem}")
            continue
        if update_card(f, PA_METADATA[stem]):
            pa_updated += 1

    print(f"Enrichment complete:")
    print(f"  AoM cards updated: {aom_updated} (expected 65)")
    print(f"  PA cards updated: {pa_updated} (expected 78)")
    print(f"  Total cards enriched: {aom_updated + pa_updated} (expected 143)")


if __name__ == "__main__":
    main()
