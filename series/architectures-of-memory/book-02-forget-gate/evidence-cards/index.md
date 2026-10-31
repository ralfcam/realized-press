# Evidence Cards — Book 2: The Forget Gate

OKF v0.2 atomic evidence cards anchoring this volume across technical, organizational, and philosophical lenses.

| Card File | Grade | Status | Lens Domain | Core Claim / Finding |
|---|---|---|---|---|
| [`hochreiter-1997-constant-error-carousel.md`](hochreiter-1997-constant-error-carousel.md) | High | Stable | Technical | Linear identity self-connection ($w_{jj}=1.0$) enforces constant error flow, circumventing exponential vanishing/exploding gradients. |
| [`gers-2000-forget-gate-continual-prediction.md`](gers-2000-forget-gate-continual-prediction.md) | High | Stable | Technical | Learned multiplicative forget gates ($f_t \in (0, 1)$) prevent internal cell state saturation on continual sequences without explicit resets. |
| [`gers-2000-peephole-connections.md`](gers-2000-peephole-connections.md) | High | Stable | Technical | Direct connections from internal cell states to gates enable precise interval duration measurement and spike counting without premature output leakage. |
| [`cho-2014-gru-vs-lstm-gating-mechanisms.md`](cho-2014-gru-vs-lstm-gating-mechanisms.md) | High | Draft | Technical | Coupled update/reset gates in GRUs achieve comparable sequence modeling to LSTMs with 25% fewer parameters. |
| [`kirkpatrick-2017-overcoming-catastrophic-forgetting-ewc.md`](kirkpatrick-2017-overcoming-catastrophic-forgetting-ewc.md) | High | Draft | Technical | Elastic Weight Consolidation preserves sequential competencies via Fisher-weighted quadratic parameter anchoring. |
| [`holan-2004-dynamics-of-organizational-forgetting.md`](holan-2004-dynamics-of-organizational-forgetting.md) | Moderate | Draft | Organizational | 4-quadrant taxonomy distinguishes accidental memory loss (decay, failure to capture) from purposeful forgetting (unlearning, managed forgetting). |
| [`argote-1990-persistence-of-learning-industrial.md`](argote-1990-persistence-of-learning-industrial.md) | High | Stable | Organizational | Industrial production knowledge depreciates rapidly over interruptions (15–25%/month), proving institutional memory is a perishable stock. |
| [`greff-2017-lstm-search-space-odyssey.md`](greff-2017-lstm-search-space-odyssey.md) | High | Stable | Technical | 5,400-run ablation proves forget gate is the single most critical LSTM component and popular variants do not beat standard vanilla. |
| [`richards-2017-biology-of-adaptive-forgetting.md`](richards-2017-biology-of-adaptive-forgetting.md) | High | Stable | Philosophical | Neurobiological memory transience is an active, regulated computational process promoting generalization and preventing overfitting. |
| [`davis-2017-biology-of-active-forgetting.md`](davis-2017-biology-of-active-forgetting.md) | High | Stable | Philosophical | Dedicated intracellular pathways (Rac1, dopamine) actively dismantle synaptic traces to maintain behavioral flexibility. |
