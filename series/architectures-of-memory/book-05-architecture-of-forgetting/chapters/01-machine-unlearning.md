# Chapter 1: Machine Unlearning — Can a Model Be Made to Forget?

In a secure facility near Zurich, an industrial machine destroys corporate records. Bundles of bank statements and tax filings drop between spinning steel blades. The paper is sliced into tiny strips. By the time the pulp falls into the bin, the text has undergone total destruction. The words and numbers have been erased beyond recovery. In the physical world, deletion is a mechanical act. When paper tears or burns, the record ceases to exist.

In a deep neural network, however, there is no paper and no flame. If an individual asks a company to erase personal data from a foundation model, engineers meet a mathematical roadblock. A neural network does not store facts in rows or folders. Through millions of training steps, an individual’s records dissolve across billions of weights. The data is entangled with every surrounding concept. Asking a model to unlearn a training record is like asking a baker to remove sugar from a baked cake. The sugar is no longer a separate object. It has changed the structure of the entire sponge.

## I. The Industrial Shredder in Zurich

The contrast between physical destruction and neural storage reveals a fundamental divide. An archivist can shred a single file folder without touching the rest of the warehouse.

In contrast, deep learning blends every data point into shared parameters. When a model reads a document, it adjusts weights across every layer. Those adjustments depend on every other document seen during the run. Erasing the document requires untangling those shared updates. You cannot simply flip a bit to make the record disappear.

## II. The Illusion of Simple Subtraction

In the late 2010s, researchers hoped that unlearning could be achieved through simple math. They assumed that running gradient steps in reverse would neatly subtract unwanted data.

That hope proved false when tested against real attacks. Reversing gradients degrades performance on the target file. Yet it leaves subtle traces in weight space. Using membership tests, an attacker can still detect that the target data was present during pretraining. Surface amnesia does not equal mathematical deletion.

## III. Compartments and Shards

To achieve reliable deletion, researchers turned to modular architectures.

Empirical research by Lucas Bourtoule and colleagues demonstrates that approximate gradient ascent leaves detectable statistical residues in model weights.[^bourtoule2021] Their findings establish the SISA framework—sharding and slicing training corpora—as a provable architecture for exact unlearning. By dividing data into isolated shards, teams need to retrain only the slice that held the target data.

Further work by Ronen Eldan and Mark Russinovich shows how target tokens can be replaced with generic completions to approximate unlearning in large language models.[^eldan2023] Their experiments prove that while approximate erasure suppresses surface recall, full mathematical removal remains difficult without architectural isolation.

## IV. The Engineering of Selective Amnesia

Building systems that can forget requires three operational disciplines.

First, absolute unlearning demands that final weights match a model trained without the deleted data. Second, post-hoc patching leaves mathematical residuals that remain open to forensic discovery. Third, organizations must build modular training pipelines with data sharding from the start. Sensitive records should reside in external retrieval layers rather than permanent weights.

<aside class="chapter-takeaway">
<header>Chapter Takeaway: The Cost of Erasure</header>
In monolithic neural networks, individual training examples are entangled across billions of continuous parameters. Post-hoc gradient subtraction leaves forensic traces that remain vulnerable to membership inference. Verifiable machine unlearning requires modular data sharding and architectural foresight before training begins.
</aside>

The Zurich shredder stops its blades. The hydraulic motor falls silent. In a cloud datacenter, an engineer reviews a large checkpoint file. She weighs the steep cost of a full training run against a single deletion request. The machine was engineered with breathtaking power to remember. It was never taught how to let anything go.

## Notes

[^bourtoule2021]: Lucas Bourtoule, Varun Chandrasekaran, Christopher A. Choquette-Choo, Hengrui Jia, Adelin Travers, Baiwu Zhang, David Lie, and Nicolas Papernot, "Machine Unlearning," in *2021 IEEE Symposium on Security and Privacy (SP)* (Los Alamitos, CA: IEEE Computer Society, 2021), 141–159, https://doi.org/10.1109/SP40001.2021.00019.

[^eldan2023]: Ronen Eldan and Mark Russinovich, "Who's Harry Potter? Approximate Unlearning in LLMs," *arXiv preprint* arXiv:2310.02238 (2023), https://doi.org/10.48550/arXiv.2310.02238.
