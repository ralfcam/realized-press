# Chapter 3 — The Original 1997 Architecture: Cell State, Input Gate, Output Gate

---

## I. The Three-Piece Machine

When Sepp Hochreiter and Jürgen Schmidhuber published their landmark paper in 1997, the architecture looked very different from modern textbooks.[^hochreiter1997]

The 1997 machine had no forget gate.

Instead, it was a tripartite mechanism built around a single priority: keep the Constant Error Carousel stable. To accomplish this, the authors placed the linear state between two protective shields. The first shield, the input gate, protected the memory from unwanted writes. The second shield, the output gate, protected downstream layers from premature reads.

Understanding why the original design took this form requires looking past modern assumptions. The 1997 model was not an abstract ideal. It was a practical compromise between constant gradient flow, local learning rules, and available computing power.

---

## II. Shielding the Carousel: Decoupling Storage from Expression

In a standard recurrent network, every unit is directly tied to its neighbors. When a unit receives input, its state changes immediately. When its state changes, downstream connections immediately broadcast that update. There is no containment.

The 1997 design severed this tight coupling by introducing the memory cell. Inside the cell, an internal state unit runs on an identity self-loop. Around this loop sit two multiplicative valves.

The input gate decides when incoming signals may alter the cell state.[^cell-math] When closed, external noise cannot perturb the stored memory. The output gate decides when the internal value may influence the rest of the network. When closed, the stored value continues to circulate in silence. Downstream layers cannot see it.

This separation between storage and expression changed everything. A cell can capture a critical signal at step five, keep its input gate closed for hundreds of steps to block noise, and keep its output gate shut until step one thousand.[^hochreiter1997] Crucially, early training relied on truncated gradient flows outside the carousel, insulating the core loop from infinite loops.[^greff2017] The carousel became a protected sanctuary of exact gradient preservation.

---

## III. Intake Governance and Disclosure Control

The three-piece structure of the 1997 architecture mirrors the access controls that complex organizations build to survive in volatile environments.

In a noisy company, messages flow without gates. Every urgent email or chat ping hijacks the team's focus on the spot. Simple recurrence rules the floor: raw noise sweeps the room, while long-term plans vanish. Leaders spend their days fighting fires.

To protect long-term work, resilient enterprises create institutional equivalents of the input and output gates:

First is intake governance, the institutional input gate. In clinical trials, software architecture, or defense programs, new work cannot be dropped straight into production. Requests must pass through formal review boards and intake triage. The input gate asks whether the proposal matches the charter. If the gate remains shut, the engineering team works undisturbed.

Second comes the corporate output gate: release control. Firms hold private facts like trade secrets, draft patents, and early audit numbers. Those records must never leak out too soon. Legal review acts as an output valve, holding inner drafts back until sign-off clears them for public release.

Organizational survival requires bidirectional isolation. If a company cannot gate what enters its memory, it drowns in triviality. If it cannot gate what leaves, it destroys its own security.

---

## IV. Locke and the Architecture of Discernment

In his *Essay Concerning Human Understanding*, John Locke split mental work into keeping ideas and telling them apart.[^locke1689] Locke noted that storing facts in memory helps no one unless the mind can sort them and call them up at the right moment.

The 1997 design turned Locke's split into working code. While the Constant Error Carousel locks a trace across time, raw keeping remains blind on its own. Learned gates supply the judgment: the input gate filters what deserves recording, and the output gate decides when that stored trace should drive action.

By separating the container from its regulators, the architecture affirmed that memory is not a single passive storehouse. Memory is an active relationship between an invariant trace and learned boundaries.

---

## V. The Missing Dimension: The Saturation Trap

The 1997 architecture was a major breakthrough. It solved long time lags that had defeated connectionist systems for decades.

Yet it contained a silent, compounding flaw. Because the self-connection weight was fixed at 1.0, the only operation applied to the cell state was addition.[^cell-math] If a network processes an ongoing, unsegmented stream of data, the state can only grow.

The cell had no way to prune its own contents. Left running over endless sequences, the state accumulated without bound, driving activation curves into saturation and freezing the network.

To handle continuous learning, the machine needed one more valve. It needed a gate dedicated to erasure. Chapter 4 examines the missing piece: the forget gate.

<aside class="chapter-takeaway">
### Chapter 3 Takeaways: Architecture, Signal, and Retained Memory

- **The Technical Signal:** The 1997 LSTM used two gates: an input gate to shield the cell from incoming noise and an output gate to control when stored states affect downstream layers.
- **The Organizational Fallacy:** Operating without intake and disclosure boundaries exposes teams to constant disruption; long-term initiatives require formal gates on both intake and release.
- **The Core Rule:** Pure retention is blind without discernment: memory systems must separate the storage vessel from the valves that govern write and read access.
</aside>

## Notes

[^hochreiter1997]: **Grade: High** across artificial benchmark tasks that input and output gating combined with the Constant Error Carousel eliminate vanishing gradients across lags exceeding 1,000 steps (Hochreiter & Schmidhuber 1997). S. Hochreiter and J. Schmidhuber, "Long Short-Term Memory," *Neural Computation* 9, no. 8 (1997): 1735–1780, DOI: 10.1162/neco.1997.9.8.1735. Evidence Card: `evidence-cards/hochreiter-1997-constant-error-carousel.md`.

[^greff2017]: **Grade: High** across 5,400 experimental runs demonstrating that gating mechanisms account for the majority of LSTM performance gains across speech, handwriting, and music benchmarks (Greff et al. 2017). K. Greff, R. K. Srivastava, J. Koutník, B. R. Steunebrink, and J. Schmidhuber, "LSTM: A Search Space Odyssey," *IEEE Transactions on Neural Networks and Learning Systems* 28, no. 10 (2017): 2222–2232, DOI: 10.1109/TNNLS.2016.2582924. Evidence Card: `evidence-cards/greff-2017-lstm-search-space-odyssey.md`.

[^cell-math]: **1997 Memory Cell Equations:** The candidate state is $net_c(t) = \sum_i w_{ci} y_i(t-1)$, and the state updates by $s_c(t) = s_c(t-1) + y^{in}(t) \cdot g(net_c(t))$, where $g$ squashes incoming values. The cell output is $y^c(t) = y^{out}(t) \cdot h(s_c(t))$, with $h$ squashing the cell state for external emission.

[^locke1689]: **Historical Locus:** John Locke, *An Essay Concerning Human Understanding* (London: Thomas Basset, 1689), Book II, Chapter X ("Of Retention") and Chapter XI ("Of Discerning, and Other Operations of the Mind").
