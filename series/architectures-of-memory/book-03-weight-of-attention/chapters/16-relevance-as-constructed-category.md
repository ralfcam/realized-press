# Chapter 16: What Attention Reveals About Relevance as a Constructed Category

In ordinary conversation and traditional information science, "relevance" is treated as an objective, pre-existing feature of reality. When an attorney presents evidence in a courtroom, a physician reviews a patient's medical history, or a scholar conducts literature research, they speak of discovering facts that are "inherently relevant" to the case.

In this intuitive view, reality comes pre-sorted into clear categories: Fact A is naturally relevant to Question B; Document C is objectively irrelevant to Topic D.

The mathematical formulation of self-attention destroys this naive realist illusion.

## The Inner Product of Subjectivity

In the Transformer, relevance is not an inherent property of a token. It is a dynamic scalar computed through the inner product of two projected vectors:

$$S_{ij} = \frac{\mathbf{q}_i \cdot \mathbf{k}_j}{\sqrt{d_k}} = \frac{(\mathbf{x}_i \mathbf{W}^Q) \cdot (\mathbf{x}_j \mathbf{W}^K)}{\sqrt{d_k}}$$

Consider what this equation reveals about the mechanics of attention:
1. Token $j$ does not possess an intrinsic score of importance. Its key $\mathbf{k}_j$ is completely inert until a query $\mathbf{q}_i$ is projected toward it.
2. The dot product $S_{ij}$ is determined entirely by the projection matrices $\mathbf{W}^Q$ and $\mathbf{W}^K$.
3. Those projection matrices are not derived from fundamental laws of physics or universal logic. They are arbitrary floating-point tensors shaped through backpropagation to minimize a specific loss function $\mathcal{L}$.

Relevance is never discovered. **Relevance is constructed by the objective function.**

```
                               THE RELEVANCE MANIFOLD
                               
   Training Objective (Loss Function L) ──► Shapes Projection Weights (W^Q, W^K)
                                                           │
                                                           ▼
Query Token (x_i) ──► Query Vector q_i ◄─── Inner Product ───► Key Vector k_j ◄── Key Token (x_j)
                                              S_{ij}
Relevance is not an intrinsic property of x_j; it is a relational projection dictated by L.
```

If a neural network is trained on the objective of next-token predictive translation, its attention weights construct a linguistic definition of relevance: verbs attend to subjects, prepositions attend to objects, and pronouns attend to antecedents.

If the very same network were trained on a loss function optimized for user engagement on social media platforms, its attention weights would construct a radically different definition of relevance: sensational words would attend to tribal identities, outrage triggers would attend to out-group signifiers, and nuanced qualifications would be crushed to zero weight.

In both cases, the machine computes "relevance" with mathematical precision. But the two geometries inhabit entirely different universes of meaning.

## Relevance Theory and Cognitive Economics

This computational insight mirrors the foundational thesis of modern cognitive linguistics, formulated by Dan Sperber and Deirdre Wilson in *Relevance: Communication and Cognition* (1986).[^sperber1986]

Sperber and Wilson demonstrated that human communication does not proceed through an objective code where words have fixed, context-free meanings. Rather, human cognition is governed by the **Principle of Relevance**: an input is relevant to an individual when its processing in a given context produces a positive cognitive effect (a revision or addition to their belief system) at an acceptable cost in mental effort:

$$\text{Relevance} \propto \frac{\text{Cognitive Effect}}{\text{Processing Effort}}$$

Relevance is fundamentally relational and contextual. A weather report warning of sudden snowfall is intensely relevant to a traveler boarding a flight, and completely irrelevant to a reader sitting in a subterranean subway car.

When we build artificial attention mechanisms, we are translating Sperber and Wilson’s cognitive ratio into silicon. The query vector represents the current search context; the keys represent candidate cognitive effects; and the softmax normalization enforces the metabolic effort constraint.

## The Politics of the Corporate Projection Matrix

In organizational sociology, the realization that relevance is a constructed category carries profound political and ethical implications.

Every human enterprise possesses an unwritten **organizational projection matrix** ($\mathbf{W}_{\text{org}}$) that dictates what signals are deemed relevant to executive decision-making.

In contemporary corporate capitalism, this matrix is shaped almost exclusively by financial accounting standards and quarterly shareholder returns:
- Signals that translate directly into short-term cash flow, EBITDA margins, and regulatory fines receive massive positive dot products. They dominate the organizational context window.
- Signals concerning employee chronic stress, long-term technical debt accumulation, ecological habitat destruction, or social polarization receive near-zero dot products.

When an executive ignores a whistle-blower's warning about working conditions or environmental contamination, it is rarely because the executive is a cartoon villain who relishes destruction. It is because the organization’s attention mechanism is mathematically blind to the signal. The whistle-blower’s memo produces an inner product of zero with the corporate query vector. The organization looks directly at the disaster and sees nothing, because its projection weights have defined the disaster as irrelevant.

## The Epistemic Responsibility

When computer scientists design attention mechanisms, they are not neutral toolmakers measuring an objective world. They are ontological engineers.

By choosing what enters the query, what is indexed in the keys, and what loss function governs the updates, the architects of AI systems decide what will be brought into the light of human attention and what will be cast into algorithmic darkness.

To construct an attention mechanism is to make a philosophical claim about what matters.

And in a world increasingly mediated by automated attention engines, the values encoded in that mathematical projection will determine what humanity is permitted to see.

---

## Notes

[^sperber1986]: D. Sperber and D. Wilson, *Relevance: Communication and Cognition*, Cambridge, MA: Harvard University Press, 1986.
