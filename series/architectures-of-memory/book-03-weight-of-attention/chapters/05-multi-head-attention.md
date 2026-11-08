# Chapter 5 — Multi-Head Attention as Multiple Interpretations

---

## I. The Monolithic Vector Trap

In human thought, a single word rarely performs just one job.

Consider the sentence: "The bank approved the loan because it had sufficient capital".

To understand this statement. a reader must resolve multiple relationships at once. Syntactically, "approved" needs its grammatical subject ("bank") and its direct object ("loan"). Semantically, the pronoun "it" must connect back to "bank" rather than "loan".

If an attention system relies on a single set of queries and keys, it falls into a trap.

A single attention distribution can only highlight one pattern at a time. If it focuses on grammar. it blurs reference. If it averages all relationships together, it dilutes the clarity of each one.[^vaswani2017]

---

## II. Eight Parallel Lenses

To resolve this dilemma, the authors of the Transformer introduced multi-head attention.[^vaswani2017]

Rather than computing a single attention pass over large vectors. the model projects Queries, Keys, and Values into several smaller subspaces. In the original design, the model uses eight distinct attention heads operating in parallel.

Each head possesses its own learned projection matrices.[^mha-math] Because each head starts with random initial weights. gradient descent steers each head toward a different aspect of language.

One head specializes in subject-verb agreement. Another head tracks pronoun reference across clauses. A third head monitors prepositional phrases. Meanwhile. a fourth attends to distant punctuation.

The model does not force language into a single interpretation. It inspects the text through eight distinct lenses at once.

---

## III. Syntactic, Semantic, and Positional Projections

Empirical research confirmed that attention heads naturally divide labor.

Elena Voita and her colleagues analyzed the internal heads of trained Transformers.[^voita2019] They discovered. That heads fell into distinct functional categories:
- **Syntactic Heads:** Reliably tracked grammatical dependencies, connecting verbs to their direct objects with near-perfect accuracy.
- **Positional Heads:** Attended primarily to adjacent tokens, functioning like localized convolutional filters.
- **Rare-Word Heads:** Focused heavily on uncommon technical terms or proper nouns across the entire passage.

The network had discovered the core concepts of traditional linguistics without human rules.

---

## IV. Bidirectional Encodings and BERT

The power of multi-head attention culminated in 2018 with Jacob Devlin's introduction of BERT at Google.[^devlin2018]

Earlier models like GPT-1 processed language strictly from left to right. Devlin showed. That deep bidirectional attention—allowing every head to look both forward and backward across the entire sentence—unlocked far greater grasp.[^devlin2018]

By training the network to fill in masked words using clues from both directions. BERT set new records across eleven natural language benchmarks.

Multi-head attention proved a vital truth: grasping language never reduces to a single flat number. Instead, it works as a chorus of parallel readings, where each head tracks a distinct layer of structure across the sentence.

<aside class="chapter-takeaway">
### Chapter 5 Takeaways: Multiple Perspectives, focus, and Synthesis.

- **The Technical Signal:** Multi-head attention projects vectors into multiple subspaces, allowing independent heads to attend at once to syntax, semantics, and reference.
- **The company Fallacy:** Expecting a single team or committee to evaluate a complex decision from all angles at once leads to diluted consensus.
- **The Core Rule:** Complex environments require multiple focused perspectives operating in parallel, whose independent findings are synthesized into a coherent decision.
</aside>

## Notes

[^vaswani2017]: **Grade: High** for multi-head attention enabling simultaneous projection into distinct representation subspaces (Vaswani et al. 2017). A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention Is All You Need," *NeurIPS* 30 (2017): 5998–6008, arXiv:1706.03762. Evidence Card: `evidence-cards/vaswani-2017-attention-is-all-you-need.md`.

[^devlin2018]: **Grade: High** for deep bidirectional Transformer representations outperforming unidirectional language models across diverse language understanding benchmarks (Devlin et al. 2019). J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding," *NAACL-HLT* (2019): 4171–4186, arXiv:1810.04805. Evidence Card: `evidence-cards/devlin-2019-bert-pretraining-deep-bidirectional.md`.

[^voita2019]: **Grade: High** for empirical identification of specialized linguistic roles (syntactic, positional, rare-token) across Transformer attention heads. E. Voita, D. Talbot, F. Moiseev, R. Sennrich, and I. Titov, "Analyzing Multi-Head Self-Attention: Specialized Heads Do the Heavy Lifting, the Rest Can Be Pruned," *ACL* (2019): 5797–5808.

[^mha-math]: **Multi-Head Projection:** $\text{MultiHead}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{Concat}(\text{head}_1, \dots, \text{head}_h)\mathbf{W}^O$, where each $\text{head}_i = \text{Attention}(\mathbf{Q}\mathbf{W}_i^Q, \mathbf{K}\mathbf{W}_i^K, \mathbf{V}\mathbf{W}_i^V)$.
