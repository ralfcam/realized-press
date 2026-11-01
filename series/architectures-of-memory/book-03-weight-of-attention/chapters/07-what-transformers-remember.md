# Chapter 7 — What Transformers Remember (and What They Forget)

---

## I. The Illusion of Memory

When an engineer interacts with a modern Transformer language model. the machine creates a powerful illusion: it feels as if it possesses an encyclopedic memory.

Ask the model about the Peloponnesian War. the synthesis of aspirin, or the syntax of Python generators. It replies with fluent, detailed prose.

Yet if you open the neural network and search for a traditional memory bank—a hard drive. a database table, or an isolated filing cabinet—you will find nothing of the sort.

The Transformer does not store documents. It possesses no internal recurrent hidden state that accumulates experience across conversations.

Once a response is emitted and the prompt cleared. the model returns instantly to its initial state. The machine. That seems to remember everything actually retains nothing at all.

---

## II. Parametric Weights and In-Context Workspace

To understand the Transformer, we must distinguish between two completely different forms of memory:
- **Parametric Memory:** The static weights stored in the network's matrices. These weights are frozen during training. They do not store specific text files; they store statistical associations, linguistic grammar, and conceptual coordinates.
- **In-Context Working Memory:** The dynamic activations generated across the context window while processing a specific prompt.[^vaswani2017]

When an engineer supplies five documents in a prompt. the Transformer does not learn them permanently. It holds them in its temporary attention switchboard.

Every token in the context window can attend to every other token. The model reads its working memory in real time. reasoning across facts. That exist only within that single execution pass.

The moment the inference run concludes, that working memory dissolves completely.

---

## III. Power-Law Scaling and Capacity

How much knowledge can a Transformer absorb into its static weights?

In 2020. Jared Kaplan and his colleagues at OpenAI published a landmark study investigating the scaling laws of neural language models.[^kaplan2020]

They showed. That cross-entropy loss scales as a smooth power-law function of three variables: weight count. dataset size, and training compute.[^scaling-math]

Over six orders of magnitude. performance did not plateau. As models grew from millions to billions of weights, their capacity to store world knowledge and generalize across novel tasks expanded predictably.

Yet Kaplan's scaling laws revealed a core trade-off: parametric memory is extraordinarily expensive to update. Adding a single new fact to a 100-billion weight model requires re-running gradient descent or risking catastrophic forgetting.

---

## IV. The Handoff to the company

With the Transformer, computing achieved a clean separation between static intelligence and dynamic search.

The weights provide the reasoning engine. the grammar, and the associative index. The context window provides the active workspace.

Yet this technical split mirrors an ancient company dilemma:
- A corporation cannot retrain all its employees whenever a new contract is signed.
- Instead, the company relies on general competencies stored in human habits, coupled with external records retrieved as needed.

Part II turns from machine learning design to collective human systems. Chapter 8 begins by examining how human companies adapted when looking up permanently replaced memorizing.

<aside class="chapter-takeaway">
### Chapter 7 Takeaways: Parametric Weights, Working Memory, and Scale.

- **The Technical Signal:** Transformers decouple frozen parametric weights (reasoning engine) from dynamic in-context working memory (the prompt context window).
- **The company Fallacy:** Expecting employees to memorize every corporate policy rather than giving them agile search tools leads to daily fatigue.
- **The Core Rule:** Sustainable intelligence combines a stable underlying reasoning model with dynamic, on-demand retrieval of current factual evidence.
</aside>

## Notes

[^vaswani2017]: **Grade: High** for Transformer self-attention providing temporary in-context working memory across token positions (Vaswani et al. 2017). A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention Is All You Need," *NeurIPS* 30 (2017): 5998–6008, arXiv:1706.03762. Evidence Card: `evidence-cards/vaswani-2017-attention-is-all-you-need.md`.

[^kaplan2020]: **Grade: High** for empirical power-law scaling governing language model performance across parameters, dataset size, and compute budget (Kaplan et al. 2020). J. Kaplan, S. McCandlish, T. Henighan, T. B. Brown, B. Chess, R. Child, ... and D. Amodei, "Scaling Laws for Neural Language Models," *arXiv:2001.08361* (2020). Evidence Card: `evidence-cards/kaplan-2020-scaling-laws-neural-language-models.md`.

[^scaling-math]: **Power-Law Scaling Formulation:** Cross-entropy test loss scales smoothly via (N) \approx (N_c/N)^{\alpha_N}$, (D) \approx (D_c/D)^{\alpha_D}$, and (C) \approx (C_c/C)^{\alpha_C}$, showing predictable loss reductions over multiple orders of magnitude.
