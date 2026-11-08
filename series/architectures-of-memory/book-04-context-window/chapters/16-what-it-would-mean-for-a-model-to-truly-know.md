# Chapter 16: What It Would Mean for a Model to Truly Know Something

A master carpenter in a boatyard on the coast of Maine runs his palm along the oak stem of a lobster boat. He does not use a digital gauge. Through decades of working timber, his fingers detect a tiny hollow where the grain runs against the bevel. If asked why the stem requires that curve, he explains how waves strike the hull in a heavy storm.

He knows how green timber swells in brine and how fastenings shear if planks seat unevenly. His knowledge is an integrated, causal grasp of wood, salt, and ocean swells. Hand him cedar instead of oak, and he adapts right away. He alters his chisel angle for the softer fiber.

When a benchmark reports that a foundation model scores high on academic tests, industry releases claim the system knows law, medicine, or physics. In philosophy, however, knowledge requires more than producing correct answers on a multiple-choice exam. Since ancient Greece, thinkers have defined knowledge as justified true belief. To know a fact, one must believe it, it must be true, and one must possess valid justification. In modern thought, this belief must stem from a reliable process that holds up under changing conditions.

## I. The Carpenter's Touch

The boatbuilder’s skill shows what genuine understanding looks like. It is counterfactual. If wind speeds rise, he knows how the frame responds. If timber dries too fast, he predicts where splits will form.

A language model possesses no such causal foundation. When it answers questions about boatbuilding, it pulls from text written by human carpenters. It can describe the tools and timber with remarkable fluency. But if a prompt subtly changes a physical law, the model falters. It repeats memorized text even when the physical scenario makes the words absurd.

## II. The Fragility of Benchmark Knowledge

Standardized benchmarks created an illusion of cognitive mastery. For years, multiple-choice exams served as proof that models were acquiring knowledge.

Adversarial research exposed the fragility of these scores. When scientists made simple, meaning-preserving changes to math and logic problems, model accuracy dropped sharply. Swapping names, altering premise order, or adding irrelevant sentences caused reasoning to collapse. The systems were not reasoning from robust world models. They were matching surface token patterns to patterns in their training sets. They knew what test answers looked like, not how the world worked.

## III. Syntax, Semantics, and Meaning

This distinction returns us to the core limits of symbol manipulation.

John Searle's classic critique shows that shuffling word tokens never sparks real intent.[^searle1980] Building on that proof, Emily Bender and Alexander Koller show that models trained only on text form have no link to the physical world that words name.[^bender2020] When a model picks the next token, it runs matrix math over strings. It never weighs truth, doubts its own guess, or checks the outside world.

## IV. The Epistemic Boundary

Defining machine capability requires three clear distinctions.

First, foundation models possess vast associative recall over human text. They reformat, correlate, and retrieve complex prose with unmatched speed. Second, models lack genuine belief and causal grounding. They do not defend claims with empirical evidence, and they switch answers if a prompt gently challenges them. Third, users must treat model outputs as candidate drafts rather than verified facts. True knowledge requires empirical testing, falsification, and causal inquiry in the physical world.

<aside class="chapter-takeaway">
<header>Chapter Takeaway: The Boundaries of Knowledge</header>
Standardized benchmark scores measure statistical pattern matching rather than genuine epistemological knowledge. Autoregressive models lack counterfactual robustness, intentional belief, and causal grounding. Reliable application requires treating model outputs as statistical hypotheses subject to empirical human verification.
</aside>

The boatbuilder in Maine sets down his plane and sweeps oak shavings from the keel. The wood is solid, cold, and true. Outside, the tide rises in the harbor. In a distant server farm, billions of transistors switch states in picoseconds. They generate prose describing every ship that ever sailed, yet know neither the salt of the sea nor the bite of the wood.

## Notes

[^searle1980]: John R. Searle, "Minds, Brains, and Programs," *Behavioral and Brain Sciences* 3, no. 3 (1980): 417–424, https://doi.org/10.1017/S0140525X00005756.

[^bender2020]: Emily M. Bender and Alexander Koller, "Climbing towards NLU: On Meaning, Form, and Understanding in the Age of Data," in *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics* (Stroudsburg, PA: Association for Computational Linguistics, 2020), 5185–5198, https://doi.org/10.18653/v1/2020.acl-main.463.
