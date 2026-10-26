# Chapter 2: Bahdanau and the First Attention Mechanism

In September 2014, Dzmitry Bahdanau, working under Kyunghyun Cho and Yoshua Bengio at the Université de Montréal, posted a preprint that fundamentally reordered the trajectory of artificial intelligence.[^bahdanau2014] Titled "Neural Machine Translation by Jointly Learning to Align and Translate," the paper tackled the exact failure mode diagnosed by Cho’s degradation curve: the catastrophic loss of signal when long sentences were forced through a fixed-dimensional bottleneck.

Bahdanau’s conceptual leap was deceptively simple: why force the decoder to rely on a single, static vector produced at the end of the input sequence? Why not allow the decoder to inspect the entire source sentence at every single step of generation?

## The Dynamic Context Vector

In Bahdanau’s architecture, the encoder remains a recurrent network—specifically, a bidirectional Gated Recurrent Unit (GRU). As the forward GRU reads the source sentence from left to right and the backward GRU reads from right to left, they generate a sequence of continuous annotation vectors:

$$\mathbf{h}_j = \begin{bmatrix} \overrightarrow{\mathbf{h}}_j \\ \overleftarrow{\mathbf{h}}_j \end{bmatrix}, \quad j = 1, \dots, T_x$$

Each annotation $\mathbf{h}_j$ does not attempt to summarize the entire sentence. It represents the $j$-th word conditioned on its immediate surrounding context.

The breakthrough occurs at the decoder. When generating target word $y_i$, the decoder maintains an internal state $\mathbf{s}_{i-1}$. Instead of taking a fixed summary vector, the decoder computes an explicit relevance score between its current search state $\mathbf{s}_{i-1}$ and every source annotation $\mathbf{h}_j$:

$$e_{ij} = \mathbf{v}_a^\top \tanh(\mathbf{W}_a \mathbf{s}_{i-1} + \mathbf{U}_a \mathbf{h}_j)$$

This formulation—known as additive or Bahdanau attention—passes the query $\mathbf{s}_{i-1}$ and the candidate memory $\mathbf{h}_j$ through learned linear projections, combines them with a hyperbolic tangent non-linearity, and projects the result down to a single scalar alignment energy $e_{ij}$ via vector $\mathbf{v}_a$.

```
Decoder State (s_{i-1}) ──┐
                          ├──► [ Alignment Network ] ──► Energy e_{ij} ──► [ Softmax ] ──► Weights α_{ij}
Source Memory (h_j)     ──┘                                                                     │
                                                                                                ▼
Context Vector: c_i = Σ α_{ij} · h_j ◄──────────────────────────────────────────────────────────┘
```

These raw energies are converted into a probability distribution over the input sequence using the softmax operator:

$$\alpha_{ij} = \frac{\exp(e_{ij})}{\sum_{k=1}^{T_x} \exp(e_{ik})}$$

The coefficients $\alpha_{ij} \in [0, 1]$ satisfy $\sum_j \alpha_{ij} = 1$. They represent how much computational "attention" the decoder should allocate to source word $j$ while generating target word $i$.

Finally, the decoder constructs a bespoke context vector $\mathbf{c}_i$ for the current time step as a weighted convex combination of all source annotations:

$$\mathbf{c}_i = \sum_{j=1}^{T_x} \alpha_{ij} \mathbf{h}_j$$

This dynamic vector $\mathbf{c}_i$ is concatenated with the decoder state to emit the next translated token.

## The Alignment Matrix and Discovered Grammar

The empirical consequence of Bahdanau’s mechanism was electric. When Cho’s length degradation curve was evaluated on the attention-equipped model, the precipitous drop vanished: sentences of thirty, forty, and fifty words were translated with flat, sustained high fidelity.[^bahdanau2014]

Even more striking was the interpretability of the learned attention weights. When Bahdanau plotted $\alpha_{ij}$ as a two-dimensional heatmap—with source English words along the columns and target French words along the rows—the network produced an interpretable alignment matrix.

```
Target (French)
"zone"        │  .  .  .  .  .  .  █  .
"économique"  │  .  .  .  .  .  .  .  █
"européenne"  │  .  .  .  .  .  .  .  .  █
              └─────────────────────────────► Source (English)
               ... "European" "Economic" "Area"
```

In English, adjectives precede nouns: "European Economic Area." In French, adjectives follow nouns: "zone économique européenne."

Without receiving any hardcoded linguistic rules, parse trees, or syntactic dictionaries, the attention weights dynamically flipped the sequence: while emitting "zone," the network focused heavily on "Area"; while emitting "économique," its focus shifted back to "Economic"; and while emitting "européenne," it attended to "European." The network had discovered grammatical inversion purely through gradient descent on the objective of predictive translation.

## The Unfinished Revolution

Bahdanau’s attention mechanism altered the relationship between computation and memory in neural networks. Prior to 2014, memory was treated as a state variable: an internal physical register that had to be maintained and carried forward across time. Bahdanau transformed memory from a noun into a verb: memory was no longer a static container; it was an act of *querying*.

Yet Bahdanau’s model remained an incomplete transition. Although the decoder could search across the source sentence, the representations $\mathbf{h}_j$ being searched were still generated by recurrent GRU layers. The network was still shackled to $O(T)$ sequential step-by-step recurrence. To produce the annotation for the fiftieth word, the encoder still had to step sequentially through words one through forty-nine.

The field had discovered the power of looking directly at the past. But it was still paying the temporal tax of walking to it one step at a time.

The final rupture would occur three years later, when a group of researchers at Google asked an audacious question: if attention can search across the entire sequence in parallel, why do we need recurrence at all?

---

## Notes

[^bahdanau2014]: D. Bahdanau, K. Cho, and Y. Bengio, "Neural Machine Translation by Jointly Learning to Align and Translate," in *3rd International Conference on Learning Representations (ICLR)*, 2015. arXiv:1409.0473.
