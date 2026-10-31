# Chapter 5 — How Backpropagation Works: The Chain Rule as Accumulating Debt

---

## I. The Credit Puzzle

Before backpropagation was a standard software tool, it was a deep puzzle of blame. In 1961, Marvin Minsky published a paper in the *Proceedings of the IRE* titled “Steps Toward Artificial Intelligence.”[^minsky1961] There he gave the credit assignment problem its classic framing: in a long chain of choices where only the final outcome is seen, which early move deserves credit, and which should take the blame?

> “If the outcome is poor, one must discover which decisions were at fault and correct them. This is the problem of *credit assignment*: given a sequence of decisions leading to some terminal outcome, assign credit (or blame) for the outcome to each decision in the sequence.”

Minsky’s insight was not limited to neural networks; it applies to any layered system. Yet it describes precisely what backpropagation does. The algorithm runs a backward pass that measures the mathematical role of every weight, layer by layer, based on how much that weight altered the final error. The engine powering this math is the calculus chain rule. And in deep networks, that chain is long.

---

## II. Three Passes and One Chain: The Math of Debt

A neural network learns through three connected steps:

**The forward pass.** Input signals enter the network. Each layer takes incoming activations, computes a weighted sum, applies a squashing curve, and passes the result forward. At the final output layer, a loss function measures how far the prediction fell from the target label.

**The backward pass.** The change in loss for an early weight is never calculated alone. Because each layer depends directly on the one before it, computing the gradient for an early weight requires multiplying local rates of change across every layer in between. Backpropagation is simply an efficient way to evaluate that chain of derivatives.

**The update pass.** Weights shift slightly in the direction that reduces overall loss. This is gradient descent, moving one step at a time.

**Gradient as debt.** That backward chain behaves like an invoice traveling upstream. The error at the output is the initial bill. Every layer the signal crosses takes a cut from the amount owed. For a standard sigmoid curve, the slope is never more than 0.25, and it is usually much lower. When you multiply a string of fractions below one, the product shrinks fast. The signal fades at every step.

**Who invented the method?** The popular story and the academic record diverge sharply. Paul J. Werbos derived neural backpropagation in his 1974 Harvard thesis, *Beyond Regression*.[^backprop-attr] David E. Rumelhart, Geoffrey E. Hinton, and Ronald J. Williams re-derived and popularized the method in their 1986 *Nature* paper, unaware of Werbos's earlier text. David Parker at MIT arrived at a similar rule in 1985. The 1986 paper trained a generation of researchers, while Werbos established original priority.

**The shadow of depth.** Computing gradients across many layers involves multiplying intermediate matrices of derivatives. When those multipliers are consistently small, early layers receive virtually zero gradient. This mathematical decay is an unavoidable result of the chain rule. In the 1990s, Sepp Hochreiter in Munich and Yoshua Bengio in Montreal would study this exact decay from independent angles.[^ch05-independence]

---

## III. Forward Pass Only: The Corporate Illusion of Learning

Modern corporations run a forward pass almost constantly. Quarterly targets roll up, sales figures are tallied, and headline metrics shift. But running a genuine backward pass—tracing which early choice caused a real failure—demands time, clear data, and political courage. Without that backward pass, leaders see the loss but cannot identify the necessary fixes. That is Minsky’s credit dilemma applied to management.

Corporate hierarchies add another barrier. Whenever technical details are condensed into summary slides, the nuance that could have corrected a flaw is smoothed away. Executive dashboards show alignment, yet the actionable signal pointing toward the true cause of failure has already vanished.

---

## IV. Credit in the Head: Brains and Learning Rules

Do biological brains perform backpropagation? Neuroscientists Blake A. Richards and Timothy P. Lillicrap suggested in 2019 that complex branching structures in brain cells might approximate credit assignment.[^richards2019] Yet they framed this as an idea rather than an established biological fact. We do not need the brain to validate the machine; we need intellectual honesty about what is proven.

There is a big difference between feeling that an action mattered and calculating exactly how much it altered a distant result. Backpropagation gives a formal method for the second. Human intuition without formal credit leads to superstition. But formal metrics without human judgment produce empty scorecards that nobody reads.

---

## V. The Unfolded Horizon: From Depth to Time

Chapter 3 traced credit across feedforward layers. This chapter showed the mathematical origin of that process: the calculus chain rule multiplied step by step. Unfolding that exact same math across time rather than depth governs what recurrent neural networks can retain. The next three chapters examine what happens when that chain of time stretches toward the horizon.

<aside class="chapter-takeaway">
### Chapter 5 Takeaways: Architecture, Signal, and Retained Memory

- **The Technical Signal:** Backpropagation computes weight updates by chaining partial derivatives through intermediate Jacobian matrices. When non-linearities like sigmoid saturate (derivative $\le 0.25$), multiplying those factors across layers causes multiplicative discounting that starves early layers of learning signal.
- **The Organizational Fallacy:** Most organizations operate in an eternal forward pass—aggregating revenue, reporting outcomes, and celebrating top-line numbers—while failing to execute the backward pass that identifies which upstream decisions caused the result.
- **The Core Rule:** Accountability requires exact credit assignment. Without a functioning backward signal, feedback collapses into superficial alignment, rewarding proximity to success rather than true causal contribution.
</aside>

## Notes

[^minsky1961]: M. Minsky, “Steps Toward Artificial Intelligence,” *Proceedings of the IRE* 49, no. 1 (1961): 8–30.

[^backprop-attr]: P. J. Werbos, *Beyond Regression: New Tools for Prediction and Analysis in the Behavioral Sciences*, Ph.D. dissertation, Harvard University, 1974; D. B. Parker, *Learning-Logic*, Technical Report TR-47, MIT, 1985; D. E. Rumelhart, G. E. Hinton, and R. J. Williams, “Learning representations by back-propagating errors,” *Nature* 323 (1986): 533–536.

[^ch05-independence]: S. Hochreiter, *Untersuchungen zu dynamischen neuronalen Netzen*, Diploma thesis, TU München, 1991; Y. Bengio, P. Simard, and P. Frasconi, “Learning long-term dependencies with gradient descent is difficult,” *IEEE Transactions on Neural Networks* 5, no. 2 (1994): 157–166.

[^richards2019]: B. A. Richards and T. P. Lillicrap, “Dendritic solutions to the credit assignment problem,” *Current Opinion in Neurobiology* 54 (2019): 28–36.
