# Chapter 7: Emerging Architectures — Longer Contexts, Memory-Augmented Models, State Space Models

At a physics lab in California, digital sensors record voltage samples during a plasma test. The stream produces millions of data points every second. 

Feeding this raw data into a standard Transformer quickly crashes the system. Memory usage spikes within seconds. 

For years, the Transformer’s heavy memory footprint seemed like an unavoidable tax. To attend to everything, every token had to be compared with every other word. 

As teams push toward million-token contexts and live streams, a quiet shift has begun to challenge that model.

---

## I. Tiling and Rotary Coordinates

The first major fixes targeted chips and code. Engineers realized that standard attention was slowed by memory bottlenecks. Shuffling data between main memory and on-chip cache created delays. 

By splitting the attention grid into small blocks, engineers stopped storing large temporary files in slow memory. This change cut training time in half. It reduced memory growth without changing final answers. 

In parallel, improvements in position markers emerged. Rotary embeddings rotate vectors in vector space.[^su2021] This geometry preserves relative distance. Networks trained on short prompts can now handle longer sequences at runtime.

---

## II. The Mamba Breakthrough: Linear Time and Selection

Yet a deeper change came from a revival of older recurrent concepts: state space systems. When the Transformer appeared in 2017, many concluded that recurrent models were obsolete. Recurrent networks ran one step at a time, making them hard to scale on chips, while their fixed vectors lost details over long horizons.

In late 2023, Albert Gu and Tri Dao introduced Mamba, combining state space models with input selection.[^gu2023] Earlier linear recurrent models treated all incoming words the same way. They could not filter out background noise.

Mamba added a dynamic selection filter.[^mamba-math] The state transitions change based on the current input word. Paired with a fast parallel scan, Mamba achieved parallel training during learning, but linear speed and constant memory during generation. 

On standard tests, Mamba matched Transformers of equal size while processing sequences up to one million tokens without a runaway cache.

---

## III. Three Tiers of Post-Transformer Memory

Evaluating these new models requires looking at three clear points:

1. **The Population Signal:** Basic attention is no longer the only choice. Hybrid models—combining state spaces for long inputs with sparse attention for precision lookup—represent the new direction for foundation models.
2. **The Mechanistic Trade-off:** State space models compress history into a compact vector. While this removes the heavy memory cache, exact copying of long random sequences remains harder for a state space model than for full attention.
3. **The Operator's Actionable Judgment:** Teams building live systems should deploy tiled attention for exact document reviews, while testing state space models for continuous sensor feeds, audio, and streaming tasks.

The sensors at the lab stream their readings into an experimental code kernel. The numbers flow in a continuous river, filtered into state vectors in real time, without filling chip memory. The rigid frame of the context window has begun to soften, opening toward tools that process, retain, and let go.

<aside class="chapter-takeaway">
### Chapter 7 Takeaways: State Spaces, Linear Complexity, and Hybrid Models.

- **The Technical Signal:** Selective state space models achieve linear computational complexity and constant inference memory by filtering inputs into continuous state transitions.
- **The Company Fallacy:** Assuming that one model architecture fits every problem leads teams to force quadratic Transformers into high-speed continuous streaming tasks.
- **The Core Rule:** Use full attention for dense multi-document analysis, and deploy selective state space models for continuous, long-horizon data streams.
</aside>

## Notes

[^su2021]: **Grade: High** for Rotary Position Embedding rotating query and key representations in complex space to enable relative attention scaling (Su et al. 2021). J. Su, M. Ahmed, Y. Lu, S. Pan, B. Wen, and Y. Liu, "RoFormer: Enhanced Transformer with Rotary Position Embedding," *Neurocomputing* 568 (2024): 127063, arXiv:2104.09864. Evidence Card: `evidence-cards/su-2024-roformer-rotary-position-embedding.md`.

[^gu2023]: **Grade: High** for selective state space models achieving linear-time sequence modeling and constant-memory inference matching Transformer quality (Gu & Dao 2023). A. Gu and T. Dao, "Mamba: Linear-Time Sequence Modeling with Selective State Spaces," *arXiv:2312.00752* (2023). Evidence Card: `evidence-cards/gu-2023-mamba-linear-time-sequence-modeling.md`.

[^mamba-math]: **Selective State Space Formulation:** The continuous state-space equation $h'(t) = A h(t) + B x(t)$ discretizes via zero-order hold with input-dependent parameters $\Delta, B, C = \text{Linear}(x_t)$, establishing linear $O(N)$ computational complexity across long sequences.
