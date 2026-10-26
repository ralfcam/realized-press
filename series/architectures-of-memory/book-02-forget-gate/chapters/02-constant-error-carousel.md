# Chapter 2 — The Constant Error Carousel: Why Addition Beats Multiplication

*Sources: research/SOURCES.md (`Hochreiter_1997`, `Bengio_1994`); evidence card `hochreiter-1997-constant-error-carousel.md`; characters — Hochreiter, Schmidhuber.*

---

## The arithmetic of persistence

If you multiply $0.9$ by itself fifty times, you obtain roughly $0.00515$. If you multiply $1.1$ by itself fifty times, you obtain over $117$. In the elementary arithmetic of repeated scaling, there is no stable plateau: any factor strictly less than one collapses into nothingness, and any factor strictly greater than one explodes toward infinity. Only exactly $1.0$ remains unchanged across depth.

This elementary mathematical property was the graveyard of early recurrent neural networks. In backpropagation through time, the error signal flowing backward from time step $T$ to time step $t$ is computed by chaining Jacobians:

$$\frac{\partial \mathcal{E}(T)}{\partial s(t)} = \frac{\partial \mathcal{E}(T)}{\partial s(T)} \prod_{k=t+1}^{T} \frac{\partial s(k)}{\partial s(k-1)}$$

Because the state transition in a standard recurrent unit applies both a weight matrix and a nonlinear squashing function (such as $\tanh$ or logistic sigmoid), the Jacobian product is scaled by repeated multiplications of weight values and derivative slopes.[^bengio1994] If the network tries to preserve memory across one hundred steps, the gradient must survive one hundred successive multiplications. It never does. The learning signal either dissolves into floating-point underflow or detonates into numerical overflow.

In 1997, Sepp Hochreiter and Jürgen Schmidhuber proposed an alternative that was almost insolent in its simplicity: **stop multiplying**.[^hochreiter1997] To ensure an error signal survives across arbitrary temporal distance, an architecture must replace the multiplicative cascade with an **additive accumulator**. They named this mechanism the **Constant Error Carousel (CEC)**.

---

## Technical lens — The identity self-loop

The core of the Constant Error Carousel is a single internal state unit, denoted $s_j$ (or later $c_j$ for cell state), equipped with a fixed linear self-connection of weight exactly $w_{jj} = 1.0$.

Unlike ordinary hidden units, the internal state unit has **no nonlinear squashing function** applied to its self-loop. Its activation function is strictly the identity $f(x) = x$, whose derivative is everywhere:

$$f'(x) = 1.0$$

When the error gradient $\delta_j(t)$ is propagated backward through this self-loop from time step $t$ to step $t-1$, the backward scaling factor is:

$$\frac{\partial s_j(t)}{\partial s_j(t-1)} = w_{jj} \cdot f'(net_j(t-1)) = 1.0 \times 1.0 = 1.0$$

The mathematical consequence is profound: the error backpropagated through the carousel does not decay by a single percentage point, whether the temporal distance is ten steps or ten thousand steps.[^hochreiter1997] Error trapped inside the carousel circulates indefinitely—like passengers on a perpetual carousel—until it is extracted to update incoming connection weights.

$$\delta_j(t-1) = \delta_j(t) \cdot 1.0 = \delta_j(t)$$

This is why addition beats multiplication in the architecture of memory. Addition accumulates; it does not scale. When new information arrives at time $t$, it is **added** to the existing state rather than replacing it:

$$s_j(t) = s_j(t-1) + \text{input}(t)$$

In the forward pass, information is conserved by superposition. In the backward pass, gradient flow is conserved by linearity. The vanishing gradient problem was not circumvented by clever parameter initialization or regularization penalties; it was structurally eliminated by replacing a geometric series with an arithmetic invariant.

---

## Organizational lens — The cumulative ledger versus the executive summary

The arithmetic distinction between addition and multiplication governs human institutions with the same mathematical severity.

Consider how knowledge moves across hierarchical tiers or successive project phases in an enterprise. When a field engineer discovers a critical failure mode, they write a detailed incident report. If the organization relies on **multiplicative transmission**, that report is summarized by a team lead, whose summary is condensed into a slide deck by a director, which is further compressed into a single bullet point by a vice president.

At each hierarchical handoff, the signal is multiplied by a managerial transmission factor $\alpha_k < 1.0$. The slope of that compression is steep: nuance, edge cases, and boundary conditions are stripped away to fit executive attention spans. By the fourth or fifth organizational layer, the derivative of the original truth has vanished. Leadership receives a green dashboard status for a system that is actively failing in the field.

Conversely, a **Constant Error Carousel** inside an organization looks like an **immutable append-only ledger**: a double-entry bookkeeping ledger, an engineering Change Order log, or a flight data recorder. In these systems, new events are **added** to the historical record; they do not overwrite or scale down previous entries.

$$\text{Ledger}(t) = \text{Ledger}(t-1) + \text{Transaction}(t)$$

The auditability of regulated industries—pharmaceutical manufacturing, nuclear power, commercial aviation—rests entirely on enforcing additive rather than multiplicative recording. When the Federal Aviation Administration investigates an airframe incident, it does not read executive summaries; it inspects the raw, additive maintenance logs signed by certified mechanics across thirty years of service. Where addition governs, accountability survives. Where multiplication governs, history is rewritten at every handoff.

---

## Philosophical lens — Bergson and the conservation of duration

In *Matter and Memory* (1896), Henri Bergson argued that real duration—*la durée réelle*—is fundamentally additive and non-reversible.[^bergson1896] For Bergson, consciousness does not replace past moments with present ones, nor does it multiply past states by a fading factor. Rather, the past automatically preserves itself, accumulating like snow rolling down a hillside:

> "The pile of the past increases without ceasing... memory is not a faculty of putting away recollections in a drawer, or of inscribing them in a register. There is no register, no drawer; there is not even, properly speaking, a faculty, for a faculty works intermittently... the past preserves itself automatically."[^bergson1896]

The Constant Error Carousel is the closest computational realization of Bergson's intuition. It rejects the classical computational metaphor of memory as an addressable drawer where symbols are stored and retrieved on demand. Instead, the cell state is a **cumulative duration**: it carries the exact superposition of its past inputs forward through time without letting the passage of time erode their weight.

Yet Bergson's model, like Hochreiter's early carousel, confronts an inescapable boundary. If duration preserves everything without loss, the accumulation eventually threatens to suffocate the system. A carousel that preserves every signal forever is incapable of adapting to a world that changes its mind.

---

## Coda — The trapped carousel

Addition solved the vanishing gradient, but it created an immediate mechanical crisis. If an identity self-loop preserves error forever, how does the network prevent irrelevant noise from polluting the carousel? And once an error signal has completed its work, how does the network turn the carousel off?

In the original 1997 formulation, Hochreiter and Schmidhuber realized that the Constant Error Carousel could not be left bare. It required specialized gates to control access to its invariant channel. Chapter 3 examines that original 1997 three-piece machine: the cell state, the input gate, and the output gate.

---

## Notes

[^hochreiter1997]: S. Hochreiter and J. Schmidhuber, "Long Short-Term Memory," *Neural Computation* 9, no. 8 (1997): 1735–1780. doi:10.1162/neco.1997.9.8.1735.

[^bengio1994]: Y. Bengio, P. Simard, and P. Frasconi, "Learning Long-Term Dependencies with Gradient Descent is Difficult," *IEEE Transactions on Neural Networks* 5, no. 2 (1994): 157–166. doi:10.1109/72.279181.

[^bergson1896]: H. Bergson, *Matière et mémoire: essai sur la relation du corps à l'esprit*, Paris: Félix Alcan, 1896. English translation by N. M. Paul and W. S. Palmer, *Matter and Memory*, London: George Allen and Unwin, 1911.
