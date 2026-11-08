# Chapter 6 — Positional Encoding: Injecting Time into Space

---

## I. The Bag of Words Dilemma

When the authors of the Transformer removed recurrence. they solved the hardware bottleneck of sequential training. But in doing so, they created a startling new problem: the design became completely blind to word order.

In a standard recurrent neural network. order is enforced by time. Word two cannot be processed until word one has updated the hidden state.

In a Transformer. however, all words enter the model at once. The scaled dot-product attention calculation compares pairs of words regardless of where they sit in the sentence.

If you feed the model the sentence "The dog bit the man," the set of pairwise dot products is mathematically identical to the sentence "The man bit the dog".

Without an explicit mechanism to represent order. a self-attention network is not a sequence processor at all. It is a bag of words.

---

## II. Sinusoidal Waves across Dimensions

To restore temporal order without reintroducing recurrent bottlenecks, Vaswani and his team invented sinusoidal positional encodings.[^vaswani2017]

Rather than passing order through a sequential state. they injected order directly into the input embeddings. Before the word vectors enter the first attention layer, the model adds a unique positional vector to each word.

The team generated these vectors using pairs of sine and cosine functions operating at varying frequencies.[^pe-math]

For the first few dimensions of the vector. the wave oscillates rapidly, completing a full cycle every few tokens. For deeper dimensions, the wave oscillates slowly, stretching across hundreds of words.

Because every position in the sequence receives a unique combination of wave heights. every position acquires a distinct numerical fingerprint.

---

## III. Learned and Relative Position Encodings

The mathematical beauty of sinusoidal waves is that they allow the model to learn relative distances easily.

Through simple wave rules, the code for spot $k + p$ works as a linear shift of the code for spot $k$. Attention heads can then tell whether two words sit side by side or ten steps apart just by taking the dot product of their wave patterns.

Later models tested three new paths:

- **Learned Absolute Encodings:** Models like BERT gave a dedicated trainable vector to each slot from one to 512.[^devlin2018]
- **Relative Position Encodings:** Designs like Shaw et al. and T5 scaled attention scores by the direct step gap between words.[^shaw2018]
- **Rotary Position Encodings (RoPE):** Modern designs like LLaMA spin query and key vectors in the complex plane, which scales cleanly to long texts.[^su2024]

---

## IV. Time Restored to the Spatial Matrix

Positional encoding accomplished something profound in computing history. It proved. That time does not need to be processed sequentially to be understood.

Recurrent networks forced the computer to experience time as an unrolling scroll. The Transformer converts time into a spatial dimension. stamping each word with its temporal coordinates and analyzing the entire landscape at once.

Time is not lost. it is mapped. The machine does not wait for history to unfold. it inspects history as a finished tapestry.

<aside class="chapter-takeaway">
### Chapter 6 Takeaways: Word Order, Waves, and Spatial Time.

- **The Technical Signal:** Self-attention is permutation-invariant; inject positional encodings into input embeddings to preserve sequence order without recurrence.
- **The company Fallacy:** Treating company events as a flat checklist without recording chronological sequence erases the causal chain of decisions.
- **The Core Rule:** Sequential history can be represented as spatial coordinates, allowing systems to analyze temporal order without suffering sequential processing delays.
</aside>

## Notes

[^vaswani2017]: **Grade: High** for sinusoidal positional encodings injecting sequence order into permutation-invariant self-attention (Vaswani et al. 2017). A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention Is All You Need," *NeurIPS* 30 (2017): 5998–6008, arXiv:1706.03762. Evidence Card: `evidence-cards/vaswani-2017-attention-is-all-you-need.md`.

[^devlin2018]: **Grade: High** for learned positional encodings in bidirectional Transformer pre-training (Devlin et al. 2019). J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, "BERT," *NAACL-HLT* (2019): 4171–4186. Evidence Card: `evidence-cards/devlin-2019-bert-pretraining-deep-bidirectional.md`.

[^shaw2018]: **Grade: High** for relative position representations in self-attention models. P. Shaw, J. Uszkoreit, and A. Vaswani, "Self-Attention with Relative Position Representations," *NAACL-HLT* (2018): 464–468.

[^su2024]: **Grade: High** for Rotary Position Embedding (RoPE) unifying absolute and relative positional encoding via complex rotation. J. Su, M. Ahmed, Y. Lu, S. Pan, W. Bo, and Y. Liu, "RoFormer: Enhanced Transformer with Rotary Position Embedding," *Neurocomputing* 568 (2024): 127063.

[^pe-math]: **Sinusoidal Position Formulation:** $PE_{(pos, 2i)} = \sin(pos / 10000^{2i/d_{model}})$ and $PE_{(pos, 2i+1)} = \cos(pos / 10000^{2i/d_{model}})$, establishing fixed geometric progressions across channels.
