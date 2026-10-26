# Chapter 7: What Transformers Remember and What They Cannot

When modern users interact with large language models built on the Transformer architecture, they routinely experience an illusion of memory. An AI assistant remembers the user’s name from ten messages earlier, adheres to formatting constraints specified at the beginning of a session, and recalls obscure historical facts from eighteenth-century physics. In common parlance, the machine is said to "remember."

Yet beneath this conversational interface lies an architecture whose memory mechanisms are completely decoupled from the temporal continuity of biological or recurrent minds. To understand the Transformer’s limits, one must dissect its dual memory architecture: the split between **parametric memory** and **non-parametric in-context attention**.[^geva2021]

```
                                TRANSFORMER DUAL MEMORY MODEL
                                
      PARAMETRIC MEMORY (Static Weights)              NON-PARAMETRIC WORKING MEMORY (Attention)
┌───────────────────────────────────────────┐    ┌───────────────────────────────────────────┐
│ Locus: Feed-forward layers (W_1, W_2)     │    │ Locus: Active context window (Q, K, V)    │
│ Update: Gradient descent during training  │    │ Update: Ephemeral activations in forward  │
│ State: Frozen during inference            │    │         pass; zero weight change          │
│ Function: Associative key-value facts     │    │ Function: Working scratchpad; disappears  │
│ Analogy: Long-term crystalline storage    │    │           the instant execution finishes  │
└───────────────────────────────────────────┘    └───────────────────────────────────────────┘
```

## The Frozen Parametric Archive

The first memory system of a Transformer resides in its parameter weights $\theta$. In a model with seventy billion parameters, these values are fixed floating-point numbers stored in high-bandwidth GPU memory.

Where do facts live inside this vast parameter matrix?

In a landmark 2021 study, Mor Geva and colleagues demonstrated that the two-layer feed-forward networks (FFNs) operating between attention layers function as **key-value associative memories**.[^geva2021] In an FFN block:

$$\text{FFN}(\mathbf{x}) = \sigma(\mathbf{x}\mathbf{W}_1 + \mathbf{b}_1)\mathbf{W}_2 + \mathbf{b}_2$$

The first weight matrix $\mathbf{W}_1$ acts as a set of keys: each row detects specific semantic or linguistic patterns (e.g., detecting the subject "Eiffel Tower" in Paris). The intermediate activation acts as a soft coefficient, and the second weight matrix $\mathbf{W}_2$ acts as a set of values, storing the factual completion ("Gustave Eiffel" or "Champ de Mars").

Crucially, this parametric memory is **static**. During inference—when the model is generating answers for an end user—gradient descent is turned off ($\nabla_\theta \mathcal{L} = 0$). The model cannot learn a new fact, modify an obsolete belief, or record a conversational transaction into its weights. Its parametric memory is a crystalline fossil: an immutable archive of the internet as it existed at the moment pre-training concluded.

## The Ephemeral Working Surface

Because its weights cannot change, the Transformer must accomplish all short-term adaptation within its **context window** using self-attention.

When an AI remembers your name across a chat session, it does not do so by writing your name into memory. It does so because the client software re-submits your entire conversation history with every single query:

$$\mathbf{X} = [\text{Prompt}, \text{Turn 1}, \text{Turn 2}, \dots, \text{Current Message}]$$

The model reads the entire conversation from the beginning on every forward pass. Self-attention projects queries across this prompt, matching keys and extracting values to construct a response.

The moment the forward pass terminates and the final token is emitted, the activations $\mathbf{Q}, \mathbf{K}, \mathbf{V}$ are instantly deallocated from GPU VRAM. The network retains no physical residue of having spoken with you. It does not possess episodic memory; it possesses an automated looking-glass that repeatedly inspects a supplied transcript.

## The Quadratic Wall: $O(n^2)$

This reliance on non-parametric attention encounters a severe physical boundary: the **quadratic complexity** of dot-product attention.

Computing the attention matrix requires evaluating pairwise affinities between every token and every other token:

$$\mathbf{S} = \frac{\mathbf{Q}\mathbf{K}^\top}{\sqrt{d_k}} \in \mathbb{R}^{n \times n}$$

The memory and computational requirements scale with the square of sequence length:

$$\text{Memory Complexity} = O(n^2), \quad \text{Compute Complexity} = O(n^2 \cdot d)$$

| Sequence Length ($n$) | Attention Matrix Entries ($n^2$) | Attention VRAM per Layer (Float16) |
| :--- | :---: | :---: |
| **1,000 tokens** | $1 \times 10^6$ | $2\text{ MB}$ |
| **8,000 tokens** | $6.4 \times 10^7$ | $128\text{ MB}$ |
| **32,000 tokens** | $1.02 \times 10^9$ | $2.05\text{ GB}$ |
| **128,000 tokens** | $1.64 \times 10^{10}$ | $32.8\text{ GB}$ |

For an enterprise attempting to feed an entire corporate archive of one million documents into a single model, full quadratic attention requires petabytes of memory for a single forward pass. Even with engineering optimizations like FlashAttention, sequence length cannot expand indefinitely without catastrophic resource expenditure.

## The Illusion of Continuity

The Transformer represents a triumph of engineering: it replaced the fragile, recurrent compression of the LSTM with an omniscient, parallel search across active context.

Yet it achieved this speed by abandoning the very definition of subjective memory. An LSTM carried time within itself; its cell state was a living accumulation of its history. A Transformer carries no time. It is an extraordinary pattern engine that stands outside time, endlessly querying whatever transient snapshot is placed before it.

When we rely on Transformers for organizational knowledge, we are not consulting a mind that remembers our history. We are consulting an engine of real-time search.

And as organizations began replacing institutional memory with automated search, they began discovering that looking up the past is not the same as understanding it.

---

## Notes

[^geva2021]: M. Geva, R. Schuster, J. Berant, and O. Levy, "Transformer Feed-Forward Layers Are Key-Value Memories," in *Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing*, 2021, pp. 5484–5495. doi:10.18653/v1/2021.emnlp-main.446.
