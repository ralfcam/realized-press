# Chapter 2 — The Constant Error Carousel: Why Addition Beats Multiplication

---

## I. The Arithmetic of Persistence

Multiply 0.9 by itself fifty times, and you get roughly 0.005. Multiply 1.1 by itself fifty times, and you pass 117. In the arithmetic of repeated scaling, there is no middle ground. Any number below one collapses toward zero. Any number above one explodes toward infinity. Only exactly 1.0 remains unchanged across depth.

This arithmetic reality was the graveyard of early recurrent neural networks. When an error signal travels backward through time, standard backpropagation multiplies weight matrices at every step.[^bengio1994] If a network tries to bridge fifty or one hundred steps, the credit signal must survive dozens of successive multiplications. It never does. The learning signal either dissolves into floating-point dust or explodes into numerical chaos.

In 1997, Sepp Hochreiter and Jürgen Schmidhuber proposed a simple alternative: stop multiplying.[^hochreiter1997] Hierarchical chunking had tried to bypass the bottleneck through discrete sequence summaries,[^schmidhuber1992] but continuous sequence learning required smooth error flow. To ensure a learning signal survives across long time spans, an architecture must replace repeated multiplication with addition. They named this mechanism the Constant Error Carousel.

---

## II. The Identity Self-Loop: Replacing Multiplication with Addition

The core of the Constant Error Carousel is a single internal state unit with a fixed linear self-connection. Its self-weight is fixed at exactly 1.0.[^cec-math]

Unlike ordinary hidden units, this inner cell applies no squashing curve to its self-loop. Its response stays linear, holding a slope of 1.0 at every point, so when an error signal travels backward through this cell, the scale never shrinks or swells. Ten steps or a thousand: the error spins on without losing a single percent.[^hochreiter1997]

This is why addition beats multiplication in the architecture of memory. Addition accumulates; it does not scale.

When new information arrives, the unit adds it to the existing state rather than multiplying over it. In the forward pass, data survives by linear combination. In the backward pass, gradients survive through constant flow. The vanishing gradient problem was not solved by clever tuning. It was solved by replacing a geometric series with an arithmetic constant.

---

## III. Cumulative Ledgers and Executive Summaries

Adding versus multiplying shapes human teams with the same force.

Watch how facts travel up a company ladder or across project handoffs. When an engineer spots a major outage, she writes a full fault report. If the firm passes news by multiplying losses, a lead trims that report, a director squeezes it into a slide deck, and a vice president boils it down to a single bullet point.

At each handoff, the signal is scaled down to fit busy executive schedules. Nuance and boundary warnings vanish. By the fourth managerial layer, the original warning has disappeared. Leadership sees a green dashboard for a system that is failing in the field.

In contrast, an additive memory operates like an append-only ledger. In double-entry bookkeeping, flight data recorders, and signed engineering change orders, new events are added to the permanent record.

They do not overwrite past entries. Regulated safety relies on additive recording. When investigators review an airframe failure, they do not read executive summaries. They inspect raw maintenance logs signed across decades of service. Where addition rules, accountability survives. Where multiplication rules, history is rewritten at every handoff.

---

## IV. Bergson and the Pile of the Past

In *Matter and Memory*, philosopher Henri Bergson argued that real duration is additive and irreversible.[^bergson1896] Consciousness does not erase past moments or multiply them by a fading factor. Instead, the past accumulates like snow rolling down a hillside.

Bergson rejected the notion of memory as an external filing drawer where facts are stored and retrieved on demand. The Constant Error Carousel reflects this intuition. It rejects the classical model of memory as an addressable database. Instead, the internal state carries a cumulative duration, preserving the weight of past inputs across time.

Yet Bergson's view hits a hard engineering wall. If duration saves every trace without loss, the pileup soon chokes the system. A vault that keeps every old signal forever cannot adapt when the world shifts.

---

## V. The Trapped Carousel

Addition stopped gradients from vanishing, but it created an immediate mechanical crisis. If an identity self-loop preserves error forever, how does the system keep noise from polluting the carousel? And once an error signal has done its job, how does the network turn it off?

The early researchers realized that the carousel could not remain naked. It required specialized gates to control access to its invariant channel. Chapter 3 examines that original 1997 machine: the cell state, the input gate, and the output gate.

<aside class="chapter-takeaway">
### Chapter 2 Takeaways: Architecture, Signal, and Retained Memory

- **The Technical Signal:** Standard recurrent networks multiply gradients across time, causing exponential decay; a linear self-loop with unit weight replaces geometric shrinkage with constant gradient flow.
- **The Organizational Fallacy:** Relying on multiplicative summaries across management tiers strips out critical failure signals; robust accountability requires additive, append-only records.
- **The Core Rule:** An invariant memory channel preserves signal across time, but an ungated accumulator inevitably traps noise unless shielded by active boundaries.
</aside>

## Notes

[^schmidhuber1992]: **Grade: High** for neural sequence chunkers and history compression demonstrating that predictable sequence segments can be collapsed into compressed representations (Schmidhuber 1992). J. Schmidhuber, "Learning Complex, Extended Sequences Using the Principle of History Compression," *Neural Computation* 4, no. 2 (1992): 234–242, https://doi.org/10.1162/neco.1992.4.2.234. Evidence Card: `evidence-cards/schmidhuber-1992-learning-complex-extended-sequences.md`.

[^hochreiter1997]: **Grade: High** for the Constant Error Carousel (CEC) eliminating exponential gradient decay across long temporal lags via an identity self-connection weight of 1.0 (Hochreiter & Schmidhuber 1997). S. Hochreiter and J. Schmidhuber, "Long Short-Term Memory," *Neural Computation* 9, no. 8 (1997): 1735–1780, DOI: 10.1162/neco.1997.9.8.1735. Evidence Card: `evidence-cards/hochreiter-1997-constant-error-carousel.md`.

[^bengio1994]: **Grade: High** that gradient descent in standard recurrent networks faces an inevitable tradeoff between robust latching and long-term gradient propagation. Y. Bengio, P. Simard, and P. Frasconi, "Learning Long-Term Dependencies with Gradient Descent is Difficult," *IEEE Transactions on Neural Networks* 5, no. 2 (1994): 157–166, DOI: 10.1109/72.279181.

[^cec-math]: **Constant Error Flow Equation:** The internal state unit follows $s_j(t) = s_j(t-1) + \text{net}_j(t)$. Because the self-connection weight is $w_{jj} = 1.0$ and no squashing function is applied ($f'(net) = 1.0$), the backward scaling factor $\frac{\partial s_j(t)}{\partial s_j(t-1)}$ remains identically 1.0.

[^bergson1896]: **Grade: High** for Bergson's philosophical distinction between spatialized discrete clock-time and cumulative lived duration (*la durée réelle*). H. Bergson, *Matter and Memory*, trans. N. M. Paul and W. S. Palmer (London: George Allen and Unwin, 1911; orig. French 1896).
