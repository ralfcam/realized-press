"""Complete metadata definitions for all 143 OKF v0.3 Evidence Cards.
Includes 61 unique AoM cards (65 files) and 78 unique PA cards (78 files).
"""

AOM_METADATA = {
    # Book 1: The Vanishing Signal
    "rosenblatt-1958-perceptron-convergence-theorem": {
        "tier": "formal_proof",
        "anchors": ["finite error-correction convergence bound k <= (R / gamma)^2", "linear separability assumption in R^d", "single-layer threshold logic unit step function"],
        "relates": ["BOUNDS:minsky-papert-1969-perceptrons-xor-locality", "EXTENDS:rumelhart-1986-backpropagation"]
    },
    "minsky-papert-1969-perceptrons-xor-locality": {
        "tier": "formal_proof",
        "anchors": ["order-1 perceptron diameter predicate insolvability", "XOR parity function requires >= 2 layers", "diameter-limited predicate connectivity bound"],
        "relates": ["BOUNDS:rosenblatt-1958-perceptron-convergence-theorem", "MITIGATES:rumelhart-1986-backpropagation"]
    },
    "rumelhart-1986-backpropagation": {
        "tier": "formal_proof",
        "anchors": ["generalized delta rule for multi-layer perceptrons", "O(W) reverse-mode automatic differentiation time complexity", "gradient chain rule across hidden layer activations"],
        "relates": ["EXTENDS:rosenblatt-1958-perceptron-convergence-theorem", "BOUNDS:hochreiter-1991-vanishing-gradient"]
    },
    "elman-1990-simple-recurrent-networks": {
        "tier": "robust_<20%",
        "anchors": ["context layer copy operation h_t = sigma(W x_t + U h_{t-1} + b)", "temporal sequence prediction on artificial grammar", "fixed context representation without BPTT unrolling limit"],
        "relates": ["EXTENDS:rumelhart-1986-backpropagation", "BOUNDS:hochreiter-1991-vanishing-gradient"]
    },
    "hochreiter-1991-vanishing-gradient": {
        "tier": "formal_proof",
        "anchors": ["Jacobian spectral norm bound ||d h_t / d h_k|| <= (W^T * f')^{t-k}", "exponential decay factor lambda^{t-k} for lambda < 1", "vanishing error signals across > 10 time steps"],
        "relates": ["BOUNDS:elman-1990-simple-recurrent-networks", "MITIGATES:pascanu-2013-exploding-vanishing-gradient-clipping", "EXTENDS:hochreiter-1997-constant-error-carousel"]
    },
    "bengio-1994-long-term-dependencies-gradient-descent": {
        "tier": "formal_proof",
        "anchors": ["trade-off between robust information latching and gradient descent trainability", "spectral radius of recurrent Jacobian strictly bounded by unity", "hyperbolic attractor basins inducing zero gradient transmission"],
        "relates": ["EXTENDS:hochreiter-1991-vanishing-gradient", "BOUNDS:elman-1990-simple-recurrent-networks"]
    },
    "pascanu-2013-exploding-vanishing-gradient-clipping": {
        "tier": "robust_<20%",
        "anchors": ["norm clipping threshold g_hat = g * (threshold / ||g||) when ||g|| > threshold", "geometrical analysis of cliff-like curvature in recurrent loss surfaces", "Hessian-free and regularization baselines on long-term sequence benchmarks"],
        "relates": ["MITIGATES:hochreiter-1991-vanishing-gradient", "EXTENDS:hochreiter-1997-constant-error-carousel"]
    },
    "nonaka-1994-seci-knowledge-conversion": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["SECI conversion cycle (Socialization, Externalization, Combination, Internalization)", "ontological knowledge spiral across individual, group, and organizational levels", "tacit-to-explicit knowledge codification asymmetry"],
        "relates": ["CONTRASTS:walsh-ungson-1991-organizational-memory", "BRIDGES_LENS:tan-2023-code-comment-rot"]
    },
    "walsh-ungson-1991-organizational-memory": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["5 organizational memory retention bins (Individuals, Culture, Transformations, Structures, Ecology)", "external archives retention locus", "retrieval failure costs in post-acquisition mergers"],
        "relates": ["EXTENDS:nonaka-1994-seci-knowledge-conversion", "BRIDGES_LENS:tan-2023-code-comment-rot"]
    },
    "tan-2023-code-comment-rot": {
        "tier": "robust_<20%",
        "anchors": ["empirical analysis of 1,000+ open-source software repositories", "semantic decay rate of source code comments over multi-year commits", "divergence between natural-language documentation and executable syntax"],
        "relates": ["BOUNDS:walsh-ungson-1991-organizational-memory", "BRIDGES_LENS:bergson-1896-matter-and-memory-duration"]
    },
    "bergson-1896-matter-and-memory-duration": {
        "tier": "formal_proof",
        "anchors": ["distinction between habit-memory (motor mechanism) and pure memory (durée réelle)", "cone of memory representation mapping onto perceptual action plane", "spatialized clock-time vs. lived temporal consciousness"],
        "relates": ["CONTRASTS:hobbes-1655-de-corpore-ship-of-theseus", "BRIDGES_LENS:elman-1990-simple-recurrent-networks"]
    },
    "hobbes-1655-de-corpore-ship-of-theseus": {
        "tier": "formal_proof",
        "anchors": ["Ship of Theseus material identity paradox across continuous plank substitution", "formal distinction between formal, material, and functional continuity", "computational representation of diachronic entity persistence"],
        "relates": ["CONTRASTS:bergson-1896-matter-and-memory-duration", "BRIDGES_LENS:walsh-ungson-1991-organizational-memory"]
    },

    # Book 2: The Forget Gate
    "hochreiter-1997-constant-error-carousel": {
        "tier": "formal_proof",
        "anchors": ["constant error carousel unit with linear activation f(x) = x and weight 1.0", "multiplicative input and output gates shielding internal state", "preservation of error gradient across 1,000+ unrolled time steps"],
        "relates": ["EXTENDS:hochreiter-1991-vanishing-gradient", "BOUNDS:gers-2000-forget-gate-continual-prediction"]
    },
    "schmidhuber-1992-learning-complex-extended-sequences": {
        "tier": "formal_proof",
        "anchors": ["neural sequence chunker and history-compressing neural predictor hierarchy", "sub-sampling recurrent state transitions on predictable subsequences", "logarithmic information compression across multi-timescale sequences"],
        "relates": ["EXTENDS:hochreiter-1991-vanishing-gradient", "CONTRASTS:hochreiter-1997-constant-error-carousel"]
    },
    "gers-2000-forget-gate-continual-prediction": {
        "tier": "formal_proof",
        "anchors": ["adaptive forget gate f_t = sigma(W_f x_t + U_f h_{t-1} + b_f)", "state update c_t = f_t * c_{t-1} + i_t * g_t", "release of obsolete internal cell state on non-segmented continual sequences"],
        "relates": ["EXTENDS:hochreiter-1997-constant-error-carousel", "BOUNDS:gers-2000-peephole-connections"]
    },
    "gers-2000-peephole-connections": {
        "tier": "robust_<20%",
        "anchors": ["peephole connections from cell state c_{t-1} into input, forget, and output gates", "precise timing spike detection and interval counting tasks", "monotonic clock synchronization in recurrent architectures"],
        "relates": ["EXTENDS:gers-2000-forget-gate-continual-prediction", "BOUNDS:greff-2017-lstm-search-space-odyssey"]
    },
    "cho-2014-gru-vs-lstm-gating-mechanisms": {
        "tier": "robust_<20%",
        "anchors": ["gated recurrent unit coupling reset gate r_t and update gate z_t", "elimination of separate memory cell c_t in favor of hidden state h_t", "parameter reduction by ~25% compared to standard LSTM"],
        "relates": ["CONTRASTS:gers-2000-forget-gate-continual-prediction", "BOUNDS:greff-2017-lstm-search-space-odyssey"]
    },
    "greff-2017-lstm-search-space-odyssey": {
        "tier": "robust_<20%",
        "anchors": ["ablation of 8 LSTM components across 5,400 experimental runs", "forget gate and output activation identified as most critical components", "no variant significantly outperforms standard vanilla LSTM across diverse benchmarks"],
        "relates": ["BOUNDS:cho-2014-gru-vs-lstm-gating-mechanisms", "BOUNDS:gers-2000-peephole-connections"]
    },
    "argote-1990-persistence-of-learning-industrial": {
        "tier": "robust_<20%",
        "anchors": ["organizational learning curves across 16 manufacturing plants", "depreciation rate of organizational knowledge stock up to 5% per month", "forgetting rates during production line interruptions and shift turnovers"],
        "relates": ["CONTRASTS:hochreiter-1997-constant-error-carousel", "BRIDGES_LENS:holan-2004-dynamics-of-organizational-forgetting"]
    },
    "holan-2004-dynamics-of-organizational-forgetting": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["4-cell matrix of organizational forgetting (Memory Dissipation, Failure to Capture, Unlearning, Purged Memory)", "intentional unlearning vs. accidental decay taxonomy", "empirical case studies across manufacturing and healthcare transitions"],
        "relates": ["EXTENDS:argote-1990-persistence-of-learning-industrial", "BRIDGES_LENS:levitt-march-1988-organizational-learning-routines"]
    },
    "levitt-march-1988-organizational-learning-routines": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["competency traps arising from reinforcing familiar organizational routines", "recording of organizational history into standard operating procedures", "path dependency and institutional memory retention constraints"],
        "relates": ["EXTENDS:holan-2004-dynamics-of-organizational-forgetting", "BRIDGES_LENS:kirkpatrick-2017-overcoming-catastrophic-forgetting-ewc"]
    },
    "kirkpatrick-2017-overcoming-catastrophic-forgetting-ewc": {
        "tier": "robust_<20%",
        "anchors": ["elastic weight consolidation loss L = L_B + sum_i (F_i / 2) (theta_i - theta_{A,i}^*)^2", "Fisher information matrix F quantifying parameter importance for task A", "maintenance of performance across sequential Atari 2600 games without catastrophic forgetting"],
        "relates": ["MITIGATES:hochreiter-1997-constant-error-carousel", "BOUNDS:davis-2017-biology-of-active-forgetting"]
    },
    "richards-2017-biology-of-adaptive-forgetting": {
        "tier": "robust_<20%",
        "anchors": ["neurobiological mechanisms of active forgetting promoting cognitive flexibility and generalization", "adult hippocampal neurogenesis uncoupling established synaptic potentiations", "reduction of overfitting in biological neural networks through transience"],
        "relates": ["EXTENDS:davis-2017-biology-of-active-forgetting", "BRIDGES_LENS:gers-2000-forget-gate-continual-prediction"]
    },
    "davis-2017-biology-of-active-forgetting": {
        "tier": "robust_<20%",
        "anchors": ["dopamine receptor dDA1 signaling mediating active memory forgetting in Drosophila", "Rac1 small G-protein activation driving dendritic spine decay", "distinction between passive decay and regulated molecular erasure"],
        "relates": ["EXTENDS:richards-2017-biology-of-adaptive-forgetting", "BRIDGES_LENS:gers-2000-forget-gate-continual-prediction"]
    },

    # Book 3: The Weight of Attention
    "bahdanau-2015-neural-machine-translation-attention": {
        "tier": "robust_<20%",
        "anchors": ["additive attention mechanism e_{ij} = v_a^T tanh(W_a s_{i-1} + U_a h_j)", "soft alignment vector generating dynamic context vector c_i", "BLEU score preservation on long sentences > 30 words in English-to-French translation"],
        "relates": ["EXTENDS:cho-2014-gru-vs-lstm-gating-mechanisms", "BOUNDS:vaswani-2017-attention-is-all-you-need"]
    },
    "vaswani-2017-attention-is-all-you-need": {
        "tier": "formal_proof",
        "anchors": ["scaled dot-product attention Attention(Q,K,V) = softmax(Q K^T / sqrt(d_k)) V", "multi-head attention projection across h = 8 heads with d_model = 512", "O(1) sequential path length and O(n^2) computational complexity per layer"],
        "relates": ["EXTENDS:bahdanau-2015-neural-machine-translation-attention", "BOUNDS:devlin-2019-bert-pretraining-deep-bidirectional"]
    },
    "devlin-2019-bert-pretraining-deep-bidirectional": {
        "tier": "robust_<20%",
        "anchors": ["masked language modeling predicting 15% randomly masked tokens", "next sentence prediction objective across 3,300M words corpus", "11 state-of-the-art NLP task records with BERT-Base (110M) and BERT-Large (340M)"],
        "relates": ["EXTENDS:vaswani-2017-attention-is-all-you-need", "CONTRASTS:radford-2019-language-models-unsupervised-multitask"]
    },
    "radford-2019-language-models-unsupervised-multitask": {
        "tier": "robust_<20%",
        "anchors": ["autoregressive unidirectional transformer trained on 40GB WebText", "zero-shot task transfer on reading comprehension, translation, and summarization", "1.5 billion parameter GPT-2 architecture without task-specific fine-tuning"],
        "relates": ["EXTENDS:vaswani-2017-attention-is-all-you-need", "BOUNDS:brown-2020-language-models-few-shot-learners"]
    },
    "brown-2020-language-models-few-shot-learners": {
        "tier": "robust_<20%",
        "anchors": ["175 billion parameter GPT-3 architecture with 96 attention layers", "in-context few-shot learning performance scaling with parameter count", "zero-shot, one-shot, and few-shot evaluation across 24 language benchmarks"],
        "relates": ["EXTENDS:radford-2019-language-models-unsupervised-multitask", "BOUNDS:kaplan-2020-scaling-laws-neural-language-models"]
    },
    "kaplan-2020-scaling-laws-neural-language-models": {
        "tier": "robust_<20%",
        "anchors": ["power-law cross-entropy loss L(N) = (N_c / N)^{alpha_N} with alpha_N ~ 0.076", "power-law data scaling L(D) = (D_c / D)^{alpha_D} with alpha_D ~ 0.057", "compute-optimal model scaling showing parameter scaling dominates dataset scaling"],
        "relates": ["EXTENDS:brown-2020-language-models-few-shot-learners", "BRIDGES_LENS:march-1991-exploration-exploitation-organizational-learning"]
    },
    "march-1991-exploration-exploitation-organizational-learning": {
        "tier": "formal_proof",
        "anchors": ["formal computational model of exploration (discovery, risk-taking) vs. exploitation (efficiency, refinement)", "mutual learning rates p_1 and p_2 regulating organizational socialization vs. innovation", "equilibrium performance traps resulting from rapid organizational homogenization"],
        "relates": ["CONTRASTS:kaplan-2020-scaling-laws-neural-language-models", "BRIDGES_LENS:simon-1971-designing-organizations-information-rich-world"]
    },
    "simon-1971-designing-organizations-information-rich-world": {
        "tier": "formal_proof",
        "anchors": ["wealth of information creates a poverty of attention", "allocation of scarce attention among overabundant information sources", "organizational design focusing on passive filtering and selective attention"],
        "relates": ["EXTENDS:march-1991-exploration-exploitation-organizational-learning", "BRIDGES_LENS:sparrow-2011-google-effects-on-memory"]
    },
    "sparrow-2011-google-effects-on-memory": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["transactive memory adaptation in digital information access across 4 experiments", "higher recall of where information is stored than what information was stored", "Stroop color-naming latency elevation when primed with search-engine concepts"],
        "relates": ["EXTENDS:simon-1971-designing-organizations-information-rich-world", "BRIDGES_LENS:clark-chalmers-1998-extended-mind-external-memory"]
    },
    "clark-chalmers-1998-extended-mind-external-memory": {
        "tier": "formal_proof",
        "anchors": ["parity principle for cognitive processes realized through external artifacts", "Otto's notebook vs. Inga's biological memory thought experiment", "epistemic action vs. pragmatic action distinction in embodied cognition"],
        "relates": ["CONTRASTS:searle-1980-minds-brains-programs-chinese-room", "BRIDGES_LENS:tulving-1985-episodic-semantic-autonoetic-memory"]
    },
    "searle-1980-minds-brains-programs-chinese-room": {
        "tier": "formal_proof",
        "anchors": ["Chinese Room thought experiment demonstrating syntax is not sufficient for semantics", "formal refutation of strong AI claim that programmed manipulation constitutes understanding", "distinction between observer-relative and observer-independent intentionality"],
        "relates": ["CONTRASTS:clark-chalmers-1998-extended-mind-external-memory", "BRIDGES_LENS:tulving-1985-episodic-semantic-autonoetic-memory"]
    },
    "tulving-1985-episodic-semantic-autonoetic-memory": {
        "tier": "robust_<20%",
        "anchors": ["tripartite classification of memory systems (anoetic, noetic, autonoetic)", "episodic memory as mental time travel enabling subjective self-recollection", "dissociation of episodic from semantic memory in amnesic patients (e.g. K.C.)"],
        "relates": ["EXTENDS:clark-chalmers-1998-extended-mind-external-memory", "CONTRASTS:searle-1980-minds-brains-programs-chinese-room"]
    },

    # Book 4: The Context Window
    "dao-2022-flashattention-fast-memory-efficient": {
        "tier": "robust_<20%",
        "anchors": ["tiling technique computing exact softmax in SRAM without materializing N x N intermediate matrices", "IO-awareness reducing high-bandwidth memory (HBM) read/writes by up to 80%", "2-4x speedup over standard attention and up to 20x memory reduction on long sequences"],
        "relates": ["EXTENDS:vaswani-2017-attention-is-all-you-need", "BOUNDS:su-2024-roformer-rotary-position-embedding"]
    },
    "su-2024-roformer-rotary-position-embedding": {
        "tier": "formal_proof",
        "anchors": ["rotary position embedding (RoPE) encoding relative position via complex rotation matrix R_{Theta,m}^d", "preservation of inner-product vector norms across arbitrary relative token offsets", "linear extrapolation capabilities on sequence lengths exceeding pre-training windows"],
        "relates": ["EXTENDS:dao-2022-flashattention-fast-memory-efficient", "BOUNDS:press-2022-train-short-test-long-alibi"]
    },
    "press-2022-train-short-test-long-alibi": {
        "tier": "robust_<20%",
        "anchors": ["attention with linear biases (ALiBi) adding static penalty m * (i - j) to attention scores", "zero trainable positional embeddings enabling zero-shot context extrapolation", "stable perplexity when testing on sequences up to 8x longer than training length"],
        "relates": ["EXTENDS:su-2024-roformer-rotary-position-embedding", "BOUNDS:liu-2024-lost-in-the-middle-long-context"]
    },
    "liu-2024-lost-in-the-middle-long-context": {
        "tier": "robust_<20%",
        "anchors": ["U-shaped retrieval accuracy curve across multi-document QA benchmarks", "performance degradation of over 30% when relevant facts are placed in the middle of context", "robust replication across open and closed long-context models up to 32k tokens"],
        "relates": ["BOUNDS:press-2022-train-short-test-long-alibi", "BOUNDS:lewis-2020-retrieval-augmented-generation"]
    },
    "lewis-2020-retrieval-augmented-generation": {
        "tier": "robust_<20%",
        "anchors": ["retrieval-augmented generation combining dense retrieval with parametric seq2seq model", "RAG-Sequence and RAG-Token marginalization across retrieved passages", "state-of-the-art results on open-domain QA (Natural Questions, CuratedTREC, WebQuestions)"],
        "relates": ["EXTENDS:karpukhin-2020-dense-passage-retrieval", "BOUNDS:liu-2024-lost-in-the-middle-long-context"]
    },
    "karpukhin-2020-dense-passage-retrieval": {
        "tier": "robust_<20%",
        "anchors": ["dual-encoder architecture mapping questions and passages into 768-dimensional space", "top-20 retrieval accuracy of 78.4% on Natural Questions compared to 59.1% for BM25", "in-batch negative sampling technique optimizing dense semantic search"],
        "relates": ["EXTENDS:devlin-2019-bert-pretraining-deep-bidirectional", "BOUNDS:lewis-2020-retrieval-augmented-generation"]
    },
    "gu-2023-mamba-linear-time-sequence-modeling": {
        "tier": "robust_<20%",
        "anchors": ["selective state space model (SSM) with input-dependent time-varying parameters B, C, Delta", "hardware-aware parallel scan computing in linear time O(N) with O(1) inference state", "5x higher inference throughput than transformers on long sequences up to 1M tokens"],
        "relates": ["CONTRASTS:dao-2022-flashattention-fast-memory-efficient", "BOUNDS:ji-2023-survey-hallucination-natural-language-generation"]
    },
    "ji-2023-survey-hallucination-natural-language-generation": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["taxonomy of intrinsic vs. extrinsic hallucinations in NLG systems", "evaluation of hallucination rates across summarization, dialog, and translation benchmarks", "survey of factuality verification methods and factual consistency metrics"],
        "relates": ["BOUNDS:lewis-2020-retrieval-augmented-generation", "BRIDGES_LENS:raji-2020-closing-ai-accountability-gap"]
    },
    "bender-2020-climbing-towards-nlu-octopus-test": {
        "tier": "formal_proof",
        "anchors": ["Octopus test thought experiment showing form cannot yield meaning without communicative intent", "formal distinction between linguistic form and communicative meaning", "critique of evaluating semantic understanding solely via statistical language modeling"],
        "relates": ["CONTRASTS:brown-2020-language-models-few-shot-learners", "BRIDGES_LENS:gopnik-2012-reconstructing-constructivism-bayesian-models"]
    },
    "gopnik-2012-reconstructing-constructivism-bayesian-models": {
        "tier": "robust_<20%",
        "anchors": ["Bayesian causal inference models of cognitive development in young children", "blicket detector experiments demonstrating rapid causal model learning from sparse data", "integration of structured symbolic representations with probabilistic statistical learning"],
        "relates": ["CONTRASTS:bender-2020-climbing-towards-nlu-octopus-test", "BRIDGES_LENS:selbst-2018-intuitive-appeal-explainable-machines"]
    },
    "raji-2020-closing-ai-accountability-gap": {
        "tier": "robust_<20%",
        "anchors": ["end-to-end internal audit framework for algorithmic systems across 5 lifecycle stages", "SMACTR framework (Scoping, Mapping, Artifact Collection, Testing, Post-deployment)", "accountability verification gap between vendor documentation and deployed model risks"],
        "relates": ["EXTENDS:selbst-2018-intuitive-appeal-explainable-machines", "BRIDGES_LENS:ji-2023-survey-hallucination-natural-language-generation"]
    },
    "selbst-2018-intuitive-appeal-explainable-machines": {
        "tier": "formal_proof",
        "anchors": ["inscrutability and non-intuitiveness of complex machine learning systems", "legal limitations of explanation rights under GDPR and algorithmic accountability doctrines", "distinction between procedural explanations and substantive justification in law"],
        "relates": ["EXTENDS:raji-2020-closing-ai-accountability-gap", "BRIDGES_LENS:bender-2020-climbing-towards-nlu-octopus-test"]
    },

    # Book 5: The Architecture of Forgetting
    "bourtoule-2021-sisa-machine-unlearning": {
        "tier": "robust_<20%",
        "anchors": ["Sharded, Isolated, Sliced, Aggregated (SISA) training framework for machine unlearning", "up to 4.4x speedup in unlearning requests compared to retraining from scratch", "exact unlearning guarantees via certified data partitioning"],
        "relates": ["EXTENDS:abadi-2016-deep-learning-with-differential-privacy", "BOUNDS:eldan-2023-whos-harry-potter-approximate-unlearning"]
    },
    "eldan-2023-whos-harry-potter-approximate-unlearning": {
        "tier": "robust_<20%",
        "anchors": ["approximate unlearning of copyrighted fiction from Llama-7B via negative target reinforcement", "prompt completion accuracy reduction from 80%+ to baseline zero on Harry Potter trivia", "preservation of general benchmark performance on MMLU and ARC"],
        "relates": ["CONTRASTS:bourtoule-2021-sisa-machine-unlearning", "BOUNDS:carlini-2021-extracting-training-data-from-large-language-models"]
    },
    "carlini-2021-extracting-training-data-from-large-language-models": {
        "tier": "robust_<20%",
        "anchors": ["black-box extraction of memorized private training data from GPT-2", "extraction of 604 verified training examples across verbatim text sequences", "memorization risk scales with model parameter size and sequence duplication frequency"],
        "relates": ["BOUNDS:eldan-2023-whos-harry-potter-approximate-unlearning", "MITIGATES:feldman-2020-does-learning-require-memorization"]
    },
    "feldman-2020-does-learning-require-memorization": {
        "tier": "formal_proof",
        "anchors": ["mathematical proof that memorization of rare/atypical examples is necessary for near-optimal generalization", "long-tailed distribution setting where subpopulation frequencies scale as O(1/k)", "lower bound on excess error for classifiers that do not memorize atypical instances"],
        "relates": ["EXTENDS:carlini-2021-extracting-training-data-from-large-language-models", "BOUNDS:dwork-2006-differential-privacy-noise-calibration"]
    },
    "dwork-2006-differential-privacy-noise-calibration": {
        "tier": "formal_proof",
        "anchors": ["epsilon-differential privacy definition P[M(D) in S] <= exp(epsilon) * P[M(D') in S] + delta", "Laplace and Gaussian noise addition calibrated to global sensitivity Delta f", "composition theorems for sequential and parallel privacy loss accumulation"],
        "relates": ["EXTENDS:abadi-2016-deep-learning-with-differential-privacy", "BOUNDS:feldman-2020-does-learning-require-memorization"]
    },
    "abadi-2016-deep-learning-with-differential-privacy": {
        "tier": "robust_<20%",
        "anchors": ["differentially private stochastic gradient descent (DP-SGD) with per-sample gradient clipping", "moments accountant technique tracking privacy loss across training epochs", "certified (epsilon = 1.25, delta = 10^-5) privacy on MNIST and CIFAR-10"],
        "relates": ["EXTENDS:dwork-2006-differential-privacy-noise-calibration", "BOUNDS:mcmahan-2017-federated-learning-communication-efficient"]
    },
    "mcmahan-2017-federated-learning-communication-efficient": {
        "tier": "robust_<20%",
        "anchors": ["FederatedAveraging (FedAvg) algorithm aggregating local client SGD updates", "10-100x reduction in network communication rounds compared to centralized SGD", "evaluation across non-IID data distributions on mobile device keyboard prediction"],
        "relates": ["EXTENDS:abadi-2016-deep-learning-with-differential-privacy", "BOUNDS:patterson-2021-carbon-footprint-machine-learning"]
    },
    "nader-2000-fear-memories-reconsolidation-amygdala": {
        "tier": "robust_<20%",
        "anchors": ["protein synthesis inhibitor anisomycin infused into basolateral amygdala after memory reactivation", "erasure of consolidated conditioned fear memory upon retrieval", "discovery of memory reconsolidation window lasting several hours post-reactivation"],
        "relates": ["EXTENDS:davis-2017-biology-of-active-forgetting", "BRIDGES_LENS:ricoeur-2004-memory-history-forgetting"]
    },
    "floridi-2014-right-to-be-forgotten-epistemic-privacy": {
        "tier": "formal_proof",
        "anchors": ["epistemic privacy framework analyzing Google Spain ECJ ruling (Case C-131/12)", "ontological distinction between personal data as asset vs. personal data as constituent of identity", "information ethics analysis of digital forgetting vs. censorship"],
        "relates": ["CONTRASTS:ricoeur-2004-memory-history-forgetting", "BRIDGES_LENS:veale-2018-algorithms-that-remember-model-inversion-gdpr"]
    },
    "patterson-2021-carbon-footprint-machine-learning": {
        "tier": "robust_<20%",
        "anchors": ["552 metric tons CO2e for GPT-3 training", "4-M energy efficiency best practices (Model, Machine, Mech, Map)", "up to 100x emission reduction through datacenter optimization"],
        "relates": ["BOUNDS:mcmahan-2017-federated-learning-communication-efficient", "BRIDGES_LENS:zuboff-2019-age-of-surveillance-capitalism"]
    },
    "ricoeur-2004-memory-history-forgetting": {
        "tier": "formal_proof",
        "anchors": ["epistemological distinction between happy forgetting and commanded forgetting", "temporal unbinding of debt from action", "forgiveness as asymmetrical moral gift"],
        "relates": ["CONTRASTS:floridi-2014-right-to-be-forgotten-epistemic-privacy", "BRIDGES_LENS:veale-2018-algorithms-that-remember-model-inversion-gdpr"]
    },
    "veale-2018-algorithms-that-remember-model-inversion-gdpr": {
        "tier": "formal_proof",
        "anchors": ["Article 17 GDPR Right to Erasure legal scope applied to machine learning models", "model weight data retention gap in trained neural networks", "membership inference attacks classified as personal data disclosures"],
        "relates": ["EXTENDS:bourtoule-2021-sisa-machine-unlearning", "BRIDGES_LENS:floridi-2014-right-to-be-forgotten-epistemic-privacy"]
    },
    "zuboff-2019-age-of-surveillance-capitalism": {
        "tier": "partially_confounded_20_50%",
        "anchors": ["behavioral surplus extraction mechanism in digital platforms", "instrumentarian power architecture modifying human behavior at scale", "asymmetric corporate memory accumulation vs. user surveillance"],
        "relates": ["CONTRASTS:abadi-2016-deep-learning-with-differential-privacy", "BRIDGES_LENS:veale-2018-algorithms-that-remember-model-inversion-gdpr"]
    }
}
