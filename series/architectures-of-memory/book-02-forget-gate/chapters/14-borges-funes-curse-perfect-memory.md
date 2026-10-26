# Chapter 14: Borges' Funes: The Curse of Perfect Memory

In 1942, Jorge Luis Borges published a short story that diagnosed the central pathology of neural networks fifty years before connectionist computer science possessed the vocabulary to articulate it.[^borges1944] In "Funes el memorioso" ("Funes the Memorious"), the narrator encounters Ireneo Funes, a young man from Fray Bentos, Uruguay, who after being thrown from a half-tamed horse awakens with a catastrophic cognitive condition: he can no longer forget.

Before the fall, Funes had lived like any other human being, perceiving the world through selective filters. After the injury, his perception and memory became total, instantaneous, and completely unattenuated:

> "He remembered not only every leaf of every tree of every wood, but every one of the times he had perceived or imagined it... He was, let us not forget, almost incapable of ideas of a general, Platonic sort. Not only was it difficult for him to comprehend that the generic symbol *dog* embraced so many unlike specimens of differing sizes and different forms; he was disturbed by the fact that a dog at three-fourteen (seen from the side) should have the same name as the dog at three-fifteen (seen from the front)... To think is to forget differences, to generalize, to abstract. In the overly replete world of Funes, there were nothing but details, almost contiguous details."

Borges’ fictional diagnosis found its exact clinical counterpart in Alexander Luria’s famous thirty-year longitudinal study of Solomon Shereshevsky, documented in *The Mind of a Mnemonist* (1968).[^luria1968] Shereshevsky—referred to in neurological literature simply as "S."—possessed an extraordinary capacity for sensory memory fueled by fivefold synesthesia. He could recall complex mathematical formulas, tables of seventy random numbers, and poetry in languages he did not speak decades after a single exposure.

```
       INPUT EXPERIENCE                   UNFILTERED RETENTION               COGNITIVE RESULT
┌─────────────────────────────┐        ┌─────────────────────────────┐    ┌────────────────────┐
│ Dog at 3:14 PM (profile)    │───────►│ Unique memory vector c_1    │    │                    │
├─────────────────────────────┤        ├─────────────────────────────┤    │ Incapacity to form │
│ Dog at 3:15 PM (frontal)    │───────►│ Unique memory vector c_2    │───►│ generic concept    │
├─────────────────────────────┤        ├─────────────────────────────┤    │ "Dog"              │
│ Dog at 3:16 PM (in shadow)  │───────►│ Unique memory vector c_3    │    │                    │
└─────────────────────────────┘        └─────────────────────────────┘    └────────────────────┘
```

Yet this immense capacity crippled his higher-order reasoning. S. struggled to comprehend simple metaphors or literary texts because the literal imagery triggered by individual words overwhelmed the thematic meaning of sentences. When reading a fable, the sensory detail of the color of a table or the pitch of a voice derailed his comprehension of the moral. To grasp an abstract concept, one must discard the idiosyncratic noise of immediate perception. S. spent decades attempting to discover techniques for active forgetting—writing items on slips of paper and burning them, or imagining black cloths covering his mental images—in an agonizing search for an internal forget gate.

In statistical machine learning, the predicament of Funes and Shereshevsky is recognized as the ultimate consequence of catastrophic overfitting. If a neural network possesses infinite capacity and zero decay, its training objective is trivially minimized by memorizing the training dataset:

$$\min_{\theta} \frac{1}{N} \sum_{i=1}^N \mathcal{L}(f(x_i; \theta), y_i) \to 0$$

The empirical error on the training corpus drops to zero. But when presented with an unseen test instance $x_{\text{test}}$, the network fails catastrophically ($E_{\text{test}} \to \infty$). Because it retained every idiosyncratic noise vector, background pixel, and irrelevant correlation present in the training distribution, it failed to extract the invariant underlying structure. It memorized every leaf on the tree, and therefore could not recognize a forest.

This was precisely what Felix Gers discovered when he examined the behavior of the original 1997 LSTM on continual prediction tasks.[^gers2000] In Hochreiter and Schmidhuber's initial design, the Constant Error Carousel preserved the cell state indefinitely:

$$C_t = C_{t-1} + i_t \odot \tilde{C}_t$$

By setting the recurrent self-connection to an immutable constant ($w_{jj} = 1.0$) with no multiplicative decay, the architecture was engineered to defeat the vanishing gradient. But without a forget gate, the carousel was an artificial Funes. As the input stream continued, the cell accumulated historical activations without erasure. The internal state drifted toward extreme values, saturating the squashing functions and stripping the network of the ability to distinguish newly arriving contextual boundaries from ancient noise.

The introduction of the forget gate:

$$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$

was connectionism's realization of Borges' axiom. The gate does not represent a compromise with hardware limits; it represents the structural condition of possibility for thought itself. By scaling previous memory states by a learned vector $f_t \in (0, 1)$, the network learns which differences matter and which must be discarded. It suppresses the idiosyncratic angle of the dog at 3:14 PM so that the persistent representation of the animal can emerge.

Philosophically, the tragedy of Funes reveals that memory is not a passive mirror of reality. A mirror preserves everything and understands nothing. Human intelligence is an act of ruthless, disciplined curation. We are conscious not because we register the world, but because we discard nearly all of it in order to preserve the few invariant relationships that allow us to navigate the next moment.

---

## Notes

[^borges1944]: J. L. Borges, "Funes el memorioso," in *Ficciones*, Buenos Aires: Editorial Sur, 1944; originally published in *La Nación*, 7 June 1942.

[^luria1968]: A. R. Luria, *The Mind of a Mnemonist: A Little Book About a Vast Memory*, trans. L. Solotaroff, New York: Basic Books, 1968.

[^gers2000]: F. A. Gers, J. Schmidhuber, and F. Cummins, "Learning to Forget: Continual Prediction with LSTM," *Neural Computation* 12, no. 10 (2000): 2451–2471. doi:10.1162/089976600300015015.
