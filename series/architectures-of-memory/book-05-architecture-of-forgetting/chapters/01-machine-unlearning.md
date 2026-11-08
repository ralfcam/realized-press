# Chapter 1: Machine Unlearning — Can a Model Be Made to Forget?

In a secure facility near Zurich, an industrial machine destroys corporate records. Bundles of bank statements and tax filings drop between spinning steel blades. The paper is sliced into tiny strips.

By the time the pulp falls into the bin, the text has undergone total destruction. The words and numbers have been erased beyond recovery. In the physical world, deletion is a mechanical act. When paper tears or burns, the record ceases to exist.

In a deep neural network, however, there is no paper and no flame. If an individual asks a company to erase personal data from a foundation model, engineers meet a mathematical roadblock. A neural network does not store facts in rows or folders. Through millions of training steps, an individual’s records dissolve across billions of weights.

The data is entangled with every surrounding concept. Asking a model to unlearn a training record is like asking a baker to remove sugar from a baked cake. The sugar is no longer a separate object. It has changed the structure of the entire sponge.

## I. The Industrial Shredder in Zurich

The contrast between physical destruction and neural storage reveals a fundamental divide. An archivist can shred a single file folder without touching the rest of the warehouse.

In contrast, deep learning blends every data point into shared weights. When a model reads a file, it nudges numbers across every layer, and those shifts depend on every other file seen during the run. Erasing one file means untangling that whole web. You cannot just flip a bit to make a record vanish.

## II. The Illusion of Simple Subtraction

In the late 2010s, researchers hoped that unlearning could be achieved through simple math. They assumed that running gradient steps in reverse would neatly subtract unwanted data.

That hope proved false when tested against real attacks. Reversing gradients degrades performance on the target file. Yet it leaves subtle traces in weight space. Using membership tests, an attacker can still detect that the target data was present during pretraining. Surface amnesia does not equal mathematical deletion.

## III. Compartments and Shards

To achieve reliable deletion, researchers turned to modular architectures.

Empirical work by Lucas Bourtoule and his team shows that rough gradient steps leave telltale traces inside model weights.[^bourtoule2021] Their SISA design—sharding and slicing training sets—gives teams a clean path to exact erasure. By splitting data into walled-off shards, engineers retrain only the single slice that held the deleted file.

Further work by Ronen Eldan and Mark Russinovich shows how swapping target words with plain fillers can mimic erasure in large language models.[^eldan2023] While fast patching hides surface recall, true removal still demands clean shard walls.

## IV. The Engineering of Selective Amnesia

Building systems that can forget requires three operational disciplines.

First, true unlearning demands that final weights match a model trained without the deleted file. Second, quick patches leave hidden traces that forensic probes can still uncover. Third, teams must build sharded training pipelines from day one, keeping private records in outside search layers rather than frozen weights.

<aside class="chapter-takeaway">
<header>Chapter Takeaway: The Cost of Erasure</header>
In monolithic neural networks, individual training examples are entangled across billions of continuous parameters. Post-hoc gradient subtraction leaves forensic traces that remain vulnerable to membership inference. Verifiable machine unlearning requires modular data sharding and architectural foresight before training begins.
</aside>

The Zurich shredder stops its blades. The hydraulic motor falls silent. In a cloud datacenter, an engineer reviews a large checkpoint file. She weighs the steep cost of a full training run against a single deletion request. The machine was engineered with breathtaking power to remember. It was never taught how to let anything go.

## Notes

[^bourtoule2021]: Lucas Bourtoule, Varun Chandrasekaran, Christopher A. Choquette-Choo, Hengrui Jia, Adelin Travers, Baiwu Zhang, David Lie, and Nicolas Papernot, "Machine Unlearning," in *2021 IEEE Symposium on Security and Privacy (SP)* (Los Alamitos, CA: IEEE Computer Society, 2021), 141–159, https://doi.org/10.1109/SP40001.2021.00019.

[^eldan2023]: Ronen Eldan and Mark Russinovich, "Who's Harry Potter? Approximate Unlearning in LLMs," *arXiv preprint* arXiv:2310.02238 (2023), https://doi.org/10.48550/arXiv.2310.02238.
