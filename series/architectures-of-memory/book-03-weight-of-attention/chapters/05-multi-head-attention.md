# Chapter 5: Multi-Head Attention as Parallel Perspectives

In human cognition, an individual word rarely performs a single semantic duty. Consider the sentence:

> "The bank refused the loan because it feared insolvency."

To comprehend this single statement, a reading mind must resolve several fundamentally different linguistic relationships simultaneously:
1. **Coreference Resolution:** What does the pronoun "it" refer to? (The bank, not the loan).
2. **Syntactic Dependency:** What is the subject of "feared"? ("it"). What is the direct object? ("insolvency").
3. **Lexical Disambiguation:** Does "bank" refer to a financial institution or a muddy riverbank? (The presence of "loan" and "insolvency" decides the meaning).
4. **Causal Reasoning:** Why was the loan refused? (Because of fear of insolvency).

If a neural network possesses only a single attention mechanism, all these competing relationships are forced into a single softmax probability distribution. To attend to "bank" to resolve coreference, the token "it" must divert attention weight away from "feared." The network is forced to average disparate syntactic and semantic relationships into a single compromise vector.

To overcome this compression trap, Vaswani and his colleagues introduced **Multi-Head Attention** (MHA).[^vaswani2017]

## The Architecture of Multiple Subspaces

Rather than computing a single attention function with queries, keys, and values of full dimensionality $d_{\text{model}}$, Multi-Head Attention linearly projects the queries, keys, and values $h$ times with different, learned parameter matrices:

$$\mathbf{Q}_i = \mathbf{Q}\mathbf{W}_i^Q, \quad \mathbf{K}_i = \mathbf{K}\mathbf{W}_i^K, \quad \mathbf{V}_i = \mathbf{V}\mathbf{W}_i^V, \quad i = 1, \dots, h$$

where $\mathbf{W}_i^Q, \mathbf{W}_i^K \in \mathbb{R}^{d_{\text{model}} \times d_k}$ and $\mathbf{W}_i^V \in \mathbb{R}^{d_{\text{model}} \times d_v}$.

On each of these projected versions of queries, keys, and values, the attention function is executed in parallel, yielding $h$ independent output representations:

$$\text{head}_i = \text{Attention}(\mathbf{Q}\mathbf{W}_i^Q, \mathbf{K}\mathbf{W}_i^K, \mathbf{V}\mathbf{W}_i^V) = \text{softmax}\left(\frac{\mathbf{Q}_i \mathbf{K}_i^\top}{\sqrt{d_k}}\right)\mathbf{V}_i$$

These $h$ head outputs are concatenated along their channel dimension and projected back to the primary model dimensionality through an output projection matrix $\mathbf{W}^O$:

$$\text{MultiHead}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{Concat}(\text{head}_1, \text{head}_2, \dots, \text{head}_h)\mathbf{W}^O$$

```
                                  [ Queries Q, Keys K, Values V ]
                                                 │
          ┌──────────────────────┬───────────────┴──────────────┬──────────────────────┐
          ▼                      ▼                              ▼                      ▼
    [ Head 1 Proj ]        [ Head 2 Proj ]                [ Head 3 Proj ]        [ Head 8 Proj ]
          │                      │                              │                      │
          ▼                      ▼                              ▼                      ▼
    [ Attention 1 ]        [ Attention 2 ]                [ Attention 3 ]        [ Attention 8 ]
    (Local Syntax)         (Coreference)                  (Semantic Roles)       (Punctuation)
          │                      │                              │                      │
          └──────────────────────┴───────────────┬──────────────┴──────────────────────┘
                                                 ▼
                                     [ Concatenation Layer ]
                                                 │
                                                 ▼
                                     [ Output Projection W^O ]
```

Crucially, this parallelization does not increase computational cost. In the standard Transformer, the full model dimension $d_{\text{model}} = 512$ is divided evenly across $h = 8$ heads, so that each head operates on vectors of dimension $d_k = d_v = 512 / 8 = 64$. Because of the reduced dimension of each head, the total computational complexity is identical to that of single-head attention with full dimensionality.

## Functional Specialization in Learned Heads

What do these parallel heads actually learn?

When researchers probed the internal activations of trained Transformers (such as BERT and GPT), they discovered an astonishing degree of spontaneous functional specialization.[^devlin2018][^voita2019] Although the eight or sixteen heads are initialized identically with random weights and trained with no explicit linguistic guidance, they naturally differentiate into distinct cognitive roles:

- **Syntactic Heads:** Specific heads consistently track immediate grammatical dependencies—pointing from nouns to their governing prepositions, or from verbs to their auxiliary particles.
- **Coreference Heads:** Distinct heads specialize in bridging long-range distances, pointing from pronouns to candidate noun phrases occurring fifty or one hundred tokens earlier.
- **Delimiter Heads:** Other heads focus almost entirely on punctuation tokens (periods, commas, end-of-sequence markers), serving as global anchors that aggregate paragraph-level discourse state.
- **Positional Heads:** Certain heads attend almost exclusively to the immediately adjacent token ($i-1$ or $i+1$), replicating the local n-gram filtering of convolutional neural networks.

Multi-head attention prevents the representation from collapsing into an undifferentiated average. It gives the network the capacity to maintain multiple parallel interpretations of the same sentence at the same time.

## Philosophical Perspectivism

The structure of multi-head attention embodies a philosophical principle articulated a century earlier by Friedrich Nietzsche in *On the Genealogy of Morals* (1887):

> "There is *only* a perspective seeing, *only* a perspective 'knowing'; and the *more* affects we allow to speak about one thing, the *more* eyes, different eyes we know how to use, the more complete will our 'concept' of this thing, our 'objectivity' be."[^nietzsche1887]

In classical epistemologies tracing back to Descartes, objectivity was imagined as a single, absolute point of view—a "view from nowhere" that apprehends reality in an immutable, unified representation. The recurrent neural network attempted to emulate this ideal: it sought a single internal hidden state $\mathbf{h}_t$ that would synthesize everything into a unified vector.

The Transformer abandons the search for the single view from nowhere. It recognizes that meaning is inherently relational and multidimensional. To understand a word is not to distill it into a solitary essence; it is to observe how it behaves through multiple, simultaneous lenses.

By deploying parallel heads, the Transformer enacts Nietzsche’s computational perspectivism: true understanding emerges not by eliminating perspectives, but by synthesizing as many different eyes as the architecture can support.

---

## Notes

[^vaswani2017]: A. Vaswani et al., "Attention Is All You Need," in *Advances in Neural Information Processing Systems* 30 (2017): 5998–6008. arXiv:1706.03762.

[^devlin2018]: J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding," *arXiv preprint arXiv:1810.04805* (2018).

[^voita2019]: E. Voita, D. Talbot, F. Moiseev, R. Sennrich, and I. Titov, "Analyzing Multi-Head Self-Attention: Specialized Heads Do the Heavy Lifting, the Rest Can Be Pruned," in *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics (ACL)*, 2019, pp. 5797–5808. doi:10.18653/v1/P19-1580.

[^nietzsche1887]: F. Nietzsche, *Zur Genealogie der Moral: Eine Streitschrift*, Leipzig: C. G. Naumann, 1887, Dritte Abhandlung, §12.
