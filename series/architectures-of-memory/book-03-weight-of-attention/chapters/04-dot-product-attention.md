# Chapter 4 — How Dot-Product Attention Works

---

## I. The Filing Cabinet and the Switchboard

To understand how a Transformer processes language, imagine an office filing system.

In an old clerical office, documents were stored in physical folders. If a clerk wanted to find data, they had to walk down rows of cabinets, opening drawers one by one until they found the relevant page. This was the world of the recurrent neural network: linear, sequential, and slow.

The Transformer replaces the filing cabinet with a digital switchboard.

Every piece of data arrives tagged with three distinct features: a Query, a Key, and a Value.[^vaswani2017]

When the system processes a word, it does not search through drawers. It broadcasts a query across the entire switchboard, compares it against every available key, and retrieves the corresponding values in parallel.

---

## II. Queries, Keys, and Values

The trio of Queries, Keys, and Values is adapted from modern database retrieval:
- **The Query ($Q$):** What the current word is looking for. A pronoun like "it" broadcasts a query asking for an antecedent noun.
- **The Key ($K$):** What each word offers. A noun like "bank" or "river" advertises its grammatical and semantic identity.
- **The Value ($V$):** The actual substantive content that will be retrieved and blended into the word's updated feature.

Each word in a sentence is projected into these three vectors through learned weight matrices.[^vaswani2017]

To determine how much attention word $A$ should pay to word $B$, the model computes the dot product of word $A$'s Query with word $B$'s Key.[^qkv-math]

A dot product measures geometric alignment: if two vectors point in similar directions in space, their product is large and positive. If they are perpendicular, their product is zero.

---

## III. The Softmax Normalization

Raw dot products produce arbitrary numerical scores. To convert these scores into practical weights, the Transformer applies two mathematical tasks.

First, it divides the scores by the square root of the key dimension.[^vaswani2017] In high-dimensional spaces, dot products can grow very large, pushing activation functions into flat regions where gradients vanish. Scaling restores numerical stability.

Second, the model passes the scaled scores through the softmax function.

Softmax exponentiates each value and divides by the sum of all values. This normalizes the scores into positive probabilities that sum to exactly one.

If word $A$'s query strongly matches word $B$'s key, word $B$ receives a weight near one, while irrelevant words receive weights near zero.

---

## IV. The Geometrical Meaning of Weight

In the final step, the attention weights are multiplied by the Value vectors.[^vaswani2017]

The updated feature of a word is not an isolated dictionary entry. It is a weighted blend of the values of every word in the sentence that proved relevant to its query.

Consider the word "bank". In the sentence "The river bank was muddy," the query for "bank" aligns with the key for "river". The resulting attention weight pulls the semantic value of "river" directly into the feature of "bank".

In a single task, ambiguity is resolved. The word is no longer an abstract token in a lexicon. it is a contextualized concept grounded in its surroundings.

<aside class="chapter-takeaway">
### Chapter 4 Takeaways: Queries, Keys, and Contextual Meaning.

- **The Technical Signal:** Scaled dot-product attention computes pairwise vector alignments between queries and keys, dynamically weighting value vectors into contextual features.
- **The company Fallacy:** Believing that words or policies possess fixed, isolated meanings leads companies into rigid misunderstandings; meaning is always contextual.
- **The Core Rule:** Efficient retrieval requires separating what a query seeks from what a record advertises, matching them through transparent relevance scores.
</aside>

## Notes

[^vaswani2017]: **Grade: High** for scaled dot-product attention establishing efficient pairwise routing across sequence positions (Vaswani et al. 2017). A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention Is All You Need," *NeurIPS* 30 (2017): 5998–6008, arXiv:1706.03762. Evidence Card: `evidence-cards/vaswani-2017-attention-is-all-you-need.md`.

[^qkv-math]: **Attention Formulation:** Given packed matrices $\mathbf{Q}, \mathbf{K}, \mathbf{V}$, attention computes $\text{softmax}(\mathbf{Q}\mathbf{K}^\top / \sqrt{d_k})\mathbf{V}$. Each output row is a convex combination of values weighted by query-key affinity.
