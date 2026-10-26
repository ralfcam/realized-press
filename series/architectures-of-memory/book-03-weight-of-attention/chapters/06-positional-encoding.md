# Chapter 6: Positional Encoding: The Prosthetic of Time

In abolishing recurrence, the creators of the Transformer solved the hardware bottleneck of sequential processing. But their victory immediately precipitated a bizarre computational crisis: pure self-attention is entirely blind to sequence order.

Mathematically, self-attention is **permutation equivariant**. If $\mathbf{P} \in \{0, 1\}^{n \times n}$ is an arbitrary permutation matrix that reorders the rows of the input sequence $\mathbf{X}$, the self-attention operation commutes perfectly with the permutation:

$$\text{Attention}(\mathbf{P}\mathbf{Q}, \mathbf{P}\mathbf{K}, \mathbf{P}\mathbf{V}) = \mathbf{P} \cdot \text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V})$$

For a Transformer, the sentence "Dog bites man" and the sentence "Man bites dog" produce identical pairwise inner products between words. The network evaluates language not as a directed timeline of events, but as an unordered bag of tokens floating in space.

Because human syntax depends fundamentally on word order, an architecture devoid of temporal awareness cannot distinguish an agent from a patient, a question from a declaration, or a condition from a consequence. Having eliminated the sequential clock of recurrence, the engineers had to invent an artificial prosthetic of time.

```
"Dog bites man"  ──┐
                   ├──► [ Pure Self-Attention ] ──► Identical Unordered Set
"Man bites dog"  ──┘                                (Permutation Equivariance)
```

## The Sinusoidal Harmonic Ladder

In "Attention Is All You Need," Vaswani and his colleagues solved this deficiency by injecting a deterministic mathematical pattern directly into the token embeddings before the first attention layer.[^vaswani2017]

For every token at sequence position $pos \in [0, n-1]$ and channel index $i \in [0, d_{\text{model}}/2 - 1]$, they added a unique positional coordinate vector:

$$\mathbf{x}_{pos}' = \mathbf{x}_{pos} + \mathbf{p}_{pos}$$

where the positional vector $\mathbf{p}_{pos}$ is constructed from interleaved sine and cosine functions of geometric frequencies:

$$\text{PE}_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

$$\text{PE}_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

The wavelengths of these trigonometric functions form a geometric progression from $2\pi$ to $10,000 \cdot 2\pi$.

```
Dimension Channels (0 → d_model)
Pos 0  [ sin(0)  cos(0)   sin(0)  cos(0) ...  sin(0)  cos(0) ]
Pos 1  [ sin(ω_0) cos(ω_0) sin(ω_1) cos(ω_1) ... sin(ω_k) cos(ω_k) ]
Pos 2  [ sin(2ω_0) cos(2ω_0) sin(2ω_1) cos(2ω_1) ... sin(2ω_k) cos(2ω_k) ]
         ◄──────────────────────────────────────────────────►
          High Frequency (Rapid)      Low Frequency (Slow Drift)
```

In the low-numbered channels ($i \approx 0$), the functions oscillate rapidly with a tiny wavelength, allowing the network to distinguish immediate neighboring tokens ($pos$ versus $pos+1$). In the high-numbered channels ($i \approx d/2$), the functions oscillate with immense wavelengths, changing minutely across thousands of tokens and providing an absolute anchor of global position across the entire text.

Why choose trigonometric sinusoids rather than simply assigning each position an integer index ($1, 2, 3, \dots, n$)?

The choice rests on the trigonometric addition theorems:

$$\sin(\alpha + \beta) = \sin(\alpha)\cos(\beta) + \cos(\alpha)\sin(\beta)$$

$$\cos(\alpha + \beta) = \cos(\alpha)\cos(\beta) - \sin(\alpha)\sin(\beta)$$

Because of these identities, for any fixed offset $k$, the positional encoding at position $pos + k$ can be represented as a linear transformation of the positional encoding at position $pos$:

$$\begin{bmatrix} \text{PE}_{(pos+k, 2i)} \\ \text{PE}_{(pos+k, 2i+1)} \end{bmatrix} = \begin{bmatrix} \cos(k \cdot \omega_i) & \sin(k \cdot \omega_i) \\ -\sin(k \cdot \omega_i) & \cos(k \cdot \omega_i) \end{bmatrix} \begin{bmatrix} \text{PE}_{(pos, 2i)} \\ \text{PE}_{(pos, 2i+1)} \end{bmatrix}$$

The rotation matrix depends solely on the relative distance $k$, not on the absolute position $pos$. This allowed the attention mechanism to learn to attend by relative offset: a verb could learn to look back three positions ($k = -3$) regardless of whether the clause appeared at the beginning, middle, or end of a chapter.

## The Evolution toward Rotary Geometry

While sinusoidal addition restored order to the Transformer, adding positional coordinates directly to semantic token embeddings created an uncomfortable representational entanglement: semantic features and positional signals occupied the same vector channels.

Subsequent architectures explored multiple variations:
1. **Learned Absolute Embeddings:** In BERT and early GPT models, positions were assigned trainable weight vectors $\mathbf{W}_{\text{pos}} \in \mathbb{R}^{n_{\text{max}} \times d}$.[^devlin2018][^radford2019] While effective within a fixed window, learned embeddings failed catastrophically when evaluated on sequence lengths exceeding the training horizon.
2. **Relative Positional Encodings:** Formulated by Peter Shaw and colleagues, relative attention directly modified the attention logit $S_{ij}$ based on the distance $i - j$.[^shaw2018]
3. **Rotary Position Embedding (RoPE):** Introduced by Jianlin Su, RoPE unified absolute and relative positioning by rotating the query and key vectors in complex two-dimensional planes before the dot product is computed.[^su2024]

## The Synthetic *A Priori* of Time

The necessity of positional encoding exposes a deep philosophical truth about intelligence.

In the *Critique of Pure Reason* (1781), Immanuel Kant established in the "Transcendental Aesthetic" that space and time are not empirical qualities derived from external sensation; they are *a priori* forms of sensible intuition (*reine Formen der Anschauung*).[^kant1781] A conscious mind does not discover time by observing events; rather, time is the cognitive framework that the mind must project onto sensory inputs in order for events to be experienced as distinct and sequential.

The recurrent neural network possessed an organic, physical time: time was the physical sequence of state transitions inside the Constant Error Carousel.

When the Transformer abolished recurrence to achieve parallel scale, it produced an entity that possessed no intrinsic temporal intuition. It had to be handed an *a priori* coordinate grid. Positional encoding is the Transformer's synthetic Kantian intuition: the mathematical scaffolding that must be grafted onto a timeless set operator so that it can experience the flow of human thought.

---

## Notes

[^vaswani2017]: A. Vaswani et al., "Attention Is All You Need," in *Advances in Neural Information Processing Systems* 30 (2017): 5998–6008. arXiv:1706.03762.

[^devlin2018]: J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding," *arXiv preprint arXiv:1810.04805* (2018).

[^radford2019]: A. Radford et al., "Language Models are Unsupervised Multitask Learners," *OpenAI Technical Report* (2019).

[^shaw2018]: P. Shaw, J. Uszkoreit, and A. Vaswani, "Self-Attention with Relative Position Representations," in *Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)*, 2018, pp. 464–468. doi:10.18653/v1/N18-2074.

[^su2024]: J. Su, M. Ahmed, Y. Lu, S. Pan, W. Bo, and Y. Liu, "RoFormer: Enhanced Transformer with Rotary Position Embedding," *Neurocomputing* 568 (2024): 127063. doi:10.1016/j.neucom.2023.127063.

[^kant1781]: I. Kant, *Kritik der reinen Vernunft*, Riga: Johann Friedrich Hartknoch, 1781; "Transzendentale Ästhetik," §4–§7.
