# Chapter 3 — The Original 1997 Architecture: Cell State, Input Gate, Output Gate

*Sources: research/SOURCES.md (`Hochreiter_1997`, `Greff_2017`); evidence card `hochreiter-1997-constant-error-carousel.md`; characters — Hochreiter, Schmidhuber.*

---

## The three-piece machine

In November 1997, when Sepp Hochreiter and Jürgen Schmidhuber published the definitive specification of Long Short-Term Memory in *Neural Computation*, the architecture looked strikingly different from the standard four-gate block taught in contemporary textbooks.[^hochreiter1997]

The 1997 machine had **no forget gate**.

Instead, it was a precise tripartite mechanism designed around a single imperative: keep the Constant Error Carousel stable. To accomplish this, the authors encapsulated the linear cell state between two multiplicative shields. The first shield, the **input gate**, guarded the memory against unwanted writes. The second shield, the **output gate**, guarded the rest of the network against premature reads.

Understanding why this original design took the shape it did requires looking past modern simplifications. The 1997 LSTM was not an abstract mathematical ideal; it was an intricate engineering compromise between constant gradient flow, computational complexity, and local learning rules.

---

## Technical lens — Shielding the carousel

In a standard feedforward or simple recurrent network, every unit is directly coupled to its neighbors. If a unit receives an input, its state changes; if its state changes, its downstream connections immediately transmit that change. There is no concept of containment.

The 1997 LSTM severed this direct coupling by introducing the **memory cell**. A cell contains an internal state $s_c$ governed by the Constant Error Carousel, surrounded by two multiplicative units:

1. **The Input Gate ($in$):** A sigmoidal unit whose activation $y^{in} \in (0, 1)$ scales the incoming candidate state before it can reach the carousel:
   $$net_c(t) = \sum_i w_{ci} y_i(t-1)$$
   $$s_c(t) = s_c(t-1) + y^{in}(t) \cdot g(net_c(t))$$
   Here, $g$ is a squashing function (typically scaled to $[-2, 2]$ in the 1997 paper). When $y^{in}(t) \approx 0$, the input gate is closed: external inputs cannot perturb the internal state, and the cell retains its existing memory unchanged.

2. **The Output Gate ($out$):** A sigmoidal unit whose activation $y^{out} \in (0, 1)$ scales the cell's emission to the rest of the network:
   $$y^c(t) = y^{out}(t) \cdot h(s_c(t))$$
   Here, $h$ is a squashing function (typically $[-1, 1]$). When $y^{out}(t) \approx 0$, the output gate is closed: the internal state continues to circulate on its carousel, but it is invisible to downstream layers.

```
       [ Output Gate (y^out) ] ---> Multiplier ---> Visible Output y^c(t)
                                         ^
                                         | h(s_c)
             +---------------------------+
             |
             v
   +--------------------+
   |  Cell State s_c    | <--- Identity Self-Loop (w_cc = 1.0)
   +--------------------+
             ^
             |
       [ Multiplier ] <--- [ Input Gate (y^in) ]
             ^
             | g(net_c)
     Incoming Inputs
```

The mathematical elegance of this arrangement lies in how it decouples **storage** from **expression**. A cell can store a critical bit of information at step $t=5$, keep its input gate closed from step $6$ through $999$ to block noise, and keep its output gate closed until step $1000$, when the information is finally needed to make a classification.[^hochreiter1997]

Crucially, the 1997 algorithm did not use full Backpropagation Through Time (BPTT). Because computing full recurrent gradients across long sequences was prohibitively expensive in 1997, the authors used a hybrid algorithm: Real-Time Recurrent Learning (RTRL) for the gate units, while gradient flow into the cell was **truncated** outside the carousel.[^greff2017] Error signals flowed backward through the linear self-loop without decay, but once they exited the cell to update input connections, they were cut off to prevent infinite loops. The carousel was an isolated sanctuary of exact gradient preservation.

---

## Organizational lens — Access controls and information compartmentalization

The tripartite structure of the 1997 LSTM mirrors the access-control architectures that large organizations build to survive in adversarial or highly regulated environments.

In an undisciplined organization, communication is un-gated: every email, Slack message, or hallway comment immediately alters the priorities of everyone who hears it. This is organizational simple recurrence: high susceptibility to immediate noise, zero long-term retention of strategic focus. The organization suffers from what executive leadership calls "firefighting mode."

To protect long-term initiatives, sophisticated enterprises implement institutional equivalents of the input and output gates:

- **The Institutional Input Gate (Intake Governance):** In defense contracting, clinical research, or software engineering, new work cannot simply be injected into a production system. It must pass through formal **Change Control Boards (CCB)**, intake triage, or IRB approvals. The input gate evaluates incoming requests: *Is this proposal aligned with the charter? Does it meet the specification?* If the gate remains closed, the engineering team preserves its internal roadmap undisturbed by external distraction.
- **The Institutional Output Gate (Disclosure Governance):** Conversely, organizations hold sensitive internal states—trade secrets, preliminary audit findings, unannounced financial earnings—that must not leak prematurely into public activation. The legal compliance department acts as an output gate: the internal state is preserved on the corporate ledger, but its visible expression is gated until regulatory clearance (such as an SEC 10-K filing or FDA announcement) is formally triggered.

The lesson of the 1997 LSTM is that organizational durability requires **bidirectional isolation**. If an institution cannot gate what enters its memory, it drowns in triviality. If it cannot gate what leaves its memory, it destroys its own operational security.

---

## Philosophical lens — Locke and the dual faculties of memory

In *An Essay Concerning Human Understanding* (1689), John Locke divided the mind's handling of ideas into distinct operations: **retention** (the power to keep ideas in mind) and **discernment** (the power to distinguish between ideas and deploy them at the proper moment).[^locke1689] Locke observed that having ideas stored in the mind is useless if the mind lacks the ability to control their emergence:

> "The next faculty of the mind, whereby it makes a further progress towards knowledge, is that which I call discernment, and distinguishing between several ideas... Memory is as it were the storehouse of our ideas... but if they are produced in confusion, they serve rather to perplex than to instruct."[^locke1689]

The 1997 LSTM instantiated Locke's dual faculties in silicon. The Constant Error Carousel provides pure retention—the storage of the trace across time. But retention alone is blind. Discernment is provided by the gates: the input gate discerns **what is worth recording**, and the output gate discerns **when a memory is relevant to judgment**.

By separating the vessel (the cell state) from the regulators (the gates), the architecture affirmed that memory is not a unitary substance. Memory is a relationship between an invariant trace and active, learned boundaries.

---

## Coda — The missing dimension

The 1997 architecture was a triumphant proof of concept. It solved long time lag problems that had defied connectionism for decades.

Yet it contained a silent, compounding flaw. Notice the cell state update equation:

$$s_c(t) = s_c(t-1) + y^{in}(t) \cdot g(net_c(t))$$

Because $w_{cc}$ is fixed at $1.0$, the only operation applied to the existing state is **addition**. If the network processes a continuous, uninterrupted sequence—such as an infinite text stream or continuous audio—the cell state can only grow. It has no mechanism to prune its own contents. Left to run indefinitely, the cell state grows without bound, eventually driving the output squashing function $h(s_c)$ into saturation and paralyzing the network.

To solve continual prediction, the machine needed one more gate. It needed a gate dedicated to erasure. Chapter 4 tells the story of Felix Gers and the missing piece: the forget gate.

---

## Notes

[^hochreiter1997]: S. Hochreiter and J. Schmidhuber, "Long Short-Term Memory," *Neural Computation* 9, no. 8 (1997): 1735–1780. doi:10.1162/neco.1997.9.8.1735.

[^greff2017]: K. Greff, R. K. Srivastava, J. Koutník, B. R. Steunebrink, and J. Schmidhuber, "LSTM: A Search Space Odyssey," *IEEE Transactions on Neural Networks and Learning Systems* 28, no. 10 (2017): 2222–2232. doi:10.1109/tnnls.2016.2582924.

[^locke1689]: J. Locke, *An Essay Concerning Human Understanding*, London: Thomas Basset, 1689. Book II, Chapter X ("Of Retention") and Chapter XI ("Of Discerning, and Other Operations of the Mind").
