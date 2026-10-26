---
type: Evidence Card
title: "The Carbon and Energy Cost of Memory at Scale (Patterson et al. 2021)"
description: "Quantifying the energy consumption and carbon emissions of foundation model training reveals that hardware efficiency, datacenter PUE, and clean energy grids alter emissions by up to 1000×."
tags: [carbon-footprint, energy-cost, compute-scaling, green-ai]
status: stable
confidence: high
generated: { by: agent:antigravity, at: 2026-10-23T18:30:00Z }
stale_after: 2028-01-01T00:00:00Z
series_domains: [technical, organizational]
chapter_hooks: [mechanism, boundary, action]
sources:
  - id: patterson2021arxiv
    resource: https://arxiv.org/abs/2104.10350
    title: "Patterson et al. (2021), Carbon Emissions and Large Neural Network Training"
---

# The Carbon and Energy Cost of Memory at Scale

> Domain: systems / carbon-footprint
> Last updated: 2026-10-23
> Status: Stable (definitive empirical measurement)

## What We Know

Training foundation models to encode petabytes of text into parametric weights requires immense electrical energy. Patterson et al. (2021) calculate the exact energy consumption and carbon emissions of landmark models (GPT-3, T5, GShard). While training GPT-3 consumed 1,287 MWh and generated 552 metric tons of CO2e, emissions vary by up to 1000× depending on algorithmic efficiency, accelerator architecture, datacenter Power Usage Effectiveness (PUE), and grid carbon intensity.

## How Confident We Are

**Grade**: High

Joint study across UC Berkeley and Google evaluating actual datacenter telemetry, providing the empirical foundation for energy accounting in modern foundation model governance.

## Evidence and Causal Assessment

Careful measurement proves that naive estimates based solely on theoretical peak FLOPs wildly miscalculate emissions; training in low-carbon datacenters (hydro/nuclear/solar) reduces operational emissions by factors of 10× to 100× compared to coal-dependent regional grids.

## Effect Size and Persistence

Operational optimization (the "4M" best practices: Model, Machine, Mechanization, Map) reduces energy consumption by up to 100× and emissions by 1000×, demonstrating that memory costs are deeply sensitive to physical infrastructure choices.

## Bias, Heterogeneity, and Confounding

Classified as `robust (<20%)`. Pretraining accounts for one-time capital emissions, but ongoing aggregate inference across hundreds of millions of daily queries can surpass pretraining energy over the system lifecycle.

## What Remains Uncertain

Embodied carbon costs of manufacturing specialized silicon (H100/B200 GPUs) and high-density packaging relative to operational electricity consumption.

## What This Does Not Mean

Model size alone does not dictate environmental catastrophe; a larger, sparse, well-optimized model trained on clean energy can emit far less carbon than a smaller model trained naively on a dirty grid.

## What Action Is Reasonably Justified

Mandate transparent reporting of MWh energy use, datacenter carbon intensity, and location grids in foundation model system documentation (Model Cards); schedule pretraining runs in regions and times with surplus renewable energy.

## Sources

- Patterson, D., Gonzalez, J., Le, Q., Liang, C., Munguia, L.-M., Rothchild, D., So, D., Texier, M., & Dean, J. (2021). Carbon Emissions and Large Neural Network Training. *arXiv preprint arXiv:2104.10350*. https://arxiv.org/abs/2104.10350
