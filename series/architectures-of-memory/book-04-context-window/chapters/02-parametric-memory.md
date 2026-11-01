# Chapter 2: In-Context Learning vs Parametric Memory — Knowledge Stored in Weights, Not States

In an old courthouse archive in lower Manhattan, deed records from 1892 sit in acid-free folders on heavy steel shelves. If an auditor wants to verify who owns a parcel at Mercer and Prince, they walk to aisle four. They pull box 312. They read the ink strokes written by a clerk with a steel pen. 

The memory of the property transfer is clear, local, and easy to find. If a fire burns folder 312, that specific legal record is lost. The surrounding land titles remain intact on the adjacent shelves.

---

## I. Blended Numbers Across Layered Arrays

A large language model possesses no steel shelves and no individual paper folders. When an autoregressive Transformer is asked where a historic peace treaty was signed, it does not check a file. It cannot open an isolated drawer. 

Instead, a numeric vector passes through stacked attention and feed-forward layers. In each layer, the vector is projected by large weight matrices, added to residual streams, and smoothed. 

The final word emerges from the blended math of billions of static numbers. This is parametric memory. 

Knowledge is not stored in persistent runtime states or tidy file drawers. It is baked directly into connection weights during the initial training run.

---

## II. The LAMA Test and the Illusion of Storage

In 2019, researchers built the LAMA test to see if pretrained language models could replace relational databases. For decades, computer science held that human facts required clear symbolic triples stored in structured tables. Unstructured text seemed like raw data for parsers to turn into clean rows.

The research team fed fill-in-the-blank prompts into frozen networks without task-specific training. The models accurately predicted missing words across thousands of common facts. For a short time, enthusiasm surged across the field. Commentators claimed that deep networks had replaced databases by absorbing facts directly into weights.

Yet later causal tests revealed the fragility of this storage method. While factual links sit in specific feed-forward blocks at mid-network depths, they remain bound to surface words. 

Editing a single weight to update one fact often damages related knowledge. Parametric memory is not a clean database of verified truths. It is an entangled web of statistical patterns.

---

## III. Active Scratchpads Versus Frozen Weights

To understand parametric memory is to confront its runtime partner: in-context learning.[^brown2020] In modern neural design, this tension defines the central trade-off. 

Parametric memory embeds knowledge directly into billions of static connection weights during pre-training. In-context learning operates purely inside the prompt window. Examples and facts provided in the prompt guide the attention heads without changing a single weight.[^rome-math]

The context window acts as temporary RAM. It provides a fast scratchpad for immediate reasoning. Parametric weights serve as frozen read-only storage. 

The moment the answer finishes and the prompt clears, all in-context learning disappears. Parametric memory provides permanence, while in-context learning provides speed and flexibility.

To evaluate in-context learning versus parametric memory in live systems, engineers balance three distinct tiers:

1. **The Population Signal:** Across broad public text, billions of parameters store millions of facts with high fluency. The network functions as a lossy, high-dimensional encyclopedia.
2. **The Internal Link:** Knowledge in weights cannot be isolated or edited without collateral drift. Unlike relational databases that enforce strict keys, neural weights overlap across shared layers.
3. **The Operator's Actionable Judgment:** In production systems where facts carry legal or economic risk, operators must never rely on parametric memory for volatile data. Knowledge requiring verification must be decoupled from weights and kept in external storage.

When the courthouse locks its iron doors at five in the afternoon, the deed books rest motionless in the darkness. A deep neural network resting on an idling server contains no pages and no ink. Its knowledge is a landscape of high-dimensional valleys, frozen until the next prompt sets numbers tumbling down its slopes.

<aside class="chapter-takeaway">
### Chapter 2 Takeaways: Parametric Memory, Weights, and Verification.

- **The Technical Signal:** Parametric memory stores knowledge across shared connection weights, entangling factual associations and preventing clean, localized updates.
- **The Company Fallacy:** Assuming that a foundation model can serve as an internal company database risks severe factual errors and data corruption.
- **The Core Rule:** Use parametric weights for linguistic reasoning and grammar, but store verified organizational facts in external, auditable databases.
</aside>

## Notes

[^brown2020]: **Grade: High** for in-context few-shot learning emerging at foundation scale without gradient updates or weight alterations (Brown et al. 2020). T. B. Brown, B. Mann, N. Ryder, M. Subbiah, J. Kaplan, P. Dhariwal, ... and D. Amodei, "Language Models are Few-Shot Learners," *NeurIPS* 33 (2020): 1877–1901, arXiv:2005.14165. Evidence Card: `evidence-cards/brown-2020-language-models-few-shot-learners.md`.

[^rome-math]: **Parametric Memory Formulation:** Parametric association updates store factual associations $(s, r, o)$ via rank-one weight adjustments $\Delta W = (v - W k) k^\top / \|k\|^2$, demonstrating that localized factual editing can be achieved without full retrain loops.
