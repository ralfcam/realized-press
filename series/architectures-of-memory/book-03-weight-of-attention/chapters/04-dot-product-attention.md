# Chapter 4: How Dot-Product Attention Works: Queries, Keys, and Values

At the mathematical core of the Transformer lies a single algebraic expression that has become the governing equation of contemporary artificial intelligence:

$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^\top}{\sqrt{d_k}}\right)\mathbf{V}$$

To understand why this formula replaced decades of complex recurrent gates and memory cells, one must deconstruct its three constituent matrices: Queries ($\mathbf{Q}$), Keys ($\mathbf{K}$), and Values ($\mathbf{V}$).

The terminology is borrowed directly from classical computer science and relational database theory. In a traditional key-value store (such as a hash table or dictionary), an external agent submits a *query*. The database compares the query against a discrete set of stored *keys*. When an exact match is identified ($\text{query} = \text{key}_i$), the database returns the corresponding *value* ($\mathbf{v}_i$). Classical retrieval is discrete, binary, and brittle: a key either matches or it does not.

Attention transforms this database transaction into a smooth, continuous, and fully differentiable operation. Instead of returning a single value, attention computes a continuous compatibility score between the query and every key in the system, returning a weighted convex combination of all values simultaneously.

```
DATABASE RETRIEVAL (Discrete):
Query "fox" ──► Match Key "fox" ──► Return Exact Value v_3

ATTENTION RETRIEVAL (Differentiable):
Query Q_i ──► [ Dot Product with ALL Keys K_j ] ──► Softmax Weights α_j ──► Return Σ α_j · V_j
```

## The Geometry of Self-Attention

In the self-attention mechanism, the queries, keys, and values are not separate entities provided from outside. They are all projected from the very same input sequence.

Let $\mathbf{X} \in \mathbb{R}^{n \times d_{\text{model}}}$ represent a sequence of $n$ token representations. Before any comparison occurs, the input matrix is passed through three learned linear transformations:

$$\mathbf{Q} = \mathbf{X} \mathbf{W}^Q, \quad \mathbf{K} = \mathbf{X} \mathbf{W}^K, \quad \mathbf{V} = \mathbf{X} \mathbf{W}^V$$

where $\mathbf{W}^Q, \mathbf{W}^K \in \mathbb{R}^{d_{\text{model}} \times d_k}$ and $\mathbf{W}^V \in \mathbb{R}^{d_{\text{model}} \times d_v}$.

These three projections assign each token three distinct functional identities:
1. **The Query ($\mathbf{q}_i$):** What the token is currently looking for ("I am a transitive verb; where is my direct object?").
2. **The Key ($\mathbf{k}_j$):** What the token offers to others ("I am an accusative noun phrase appearing downstream").
3. **The Value ($\mathbf{v}_j$):** The actual semantic payload that will be transmitted if a match occurs ("Here is my full semantic representation").

The interaction begins by computing the matrix product $\mathbf{Q}\mathbf{K}^\top \in \mathbb{R}^{n \times n}$. The entry at row $i$ and column $j$ is the dot product of the $i$-th query and the $j$-th key:

$$S_{ij} = \mathbf{q}_i \cdot \mathbf{k}_j = \sum_{m=1}^{d_k} q_{im} k_{jm}$$

In Euclidean space, the dot product between two unit vectors is proportional to the cosine of the angle between them. If vector $\mathbf{q}_i$ and vector $\mathbf{k}_j$ point in similar directions in the $d_k$-dimensional latent space, their dot product is large and positive. If they are orthogonal, their dot product is zero. If they point in opposite directions, it is negative.

Through gradient descent, the network learns to rotate the weight matrices $\mathbf{W}^Q$ and $\mathbf{W}^K$ so that words that share grammatical, syntactic, or semantic dependencies point toward one another in the projection space.

## The Vital Importance of $\sqrt{d_k}$

Why did Vaswani and his colleagues divide the inner product matrix by $\sqrt{d_k}$ before applying the softmax operator?[^vaswani2017]

The answer reveals a subtle trap in high-dimensional probability. Suppose the components of $\mathbf{q}$ and $\mathbf{k}$ are independent random variables with a mean of zero and a variance of one:

$$\mathbb{E}[q_m] = 0, \quad \text{Var}(q_m) = 1; \quad \mathbb{E}[k_m] = 0, \quad \text{Var}(k_m) = 1$$

Their dot product is the sum of $d_k$ independent random terms:

$$Z = \mathbf{q} \cdot \mathbf{k} = \sum_{m=1}^{d_k} q_m k_m$$

By the properties of variance for independent products, the variance of each product term is $\text{Var}(q_m k_m) = 1$. Consequently, the variance of the sum scales linearly with the dimensionality:

$$\text{Var}(Z) = \sum_{m=1}^{d_k} \text{Var}(q_m k_m) = d_k$$

The standard deviation of the dot product is therefore $\sqrt{d_k}$.

When $d_k$ is small (such as $4$ or $8$), the magnitude of the dot products remains moderate. But in modern architectures where $d_k = 64$ or $128$, typical dot products grow to magnitudes of $\pm 8$ or $\pm 11$.

When values of this magnitude enter the softmax function:

$$\text{softmax}(\mathbf{z})_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$$

the largest value dominates completely, driving its softmax probability to near $1.0$ while all competing tokens are crushed to near $0.0$. In this saturated regime, the gradient of the softmax function vanishes toward zero:

$$\frac{\partial \text{softmax}(z)_i}{\partial z_j} = \text{softmax}(z)_i (\delta_{ij} - \text{softmax}(z)_j) \approx 0$$

Without scaling, the network suffers the exact vanishing gradient pathology that had plagued early recurrent networks—not over temporal sequence steps, but across the dot-product normalization layer!

Dividing by the scaling factor $\sqrt{d_k}$ normalizes the variance back to unity:

$$\text{Var}\left(\frac{\mathbf{q} \cdot \mathbf{k}}{\sqrt{d_k}}\right) = \frac{1}{d_k} \text{Var}(\mathbf{q} \cdot \mathbf{k}) = 1$$

This single scaling operation keeps the softmax distribution in a responsive, non-saturated regime where gradients can flow freely during backpropagation.

## The Epistemic Shift: Continuous Reconstruction

Notice the profound epistemic difference between the LSTM's memory and dot-product attention.

In the LSTM, memory is an accumulated object: $\mathbf{C}_t$ is an entity that exists in storage, modified by gates.

In dot-product attention, there is no accumulated object. Every token's contextual state is computed fresh by projecting its query across the entire field of keys and assembling a custom composite from the values. Memory is not a file that is retrieved intact. Memory is a dynamic, continuous reconstruction synthesized on demand to satisfy the question asked by the query.

To understand is no longer to store. To understand is to project, to match, and to recombine.

---

## Notes

[^vaswani2017]: A. Vaswani et al., "Attention Is All You Need," in *Advances in Neural Information Processing Systems* 30 (2017): 5998–6008. arXiv:1706.03762.
