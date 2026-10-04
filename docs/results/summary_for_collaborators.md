# Gene-Mila progress summary

*2026-10-04. A one-page summary for collaborating labs. Every number here is generated from the run outputs committed under `docs/results/`; the shareable copy is a Claude Doc kept in step with this file.*

## What we built

Gene-Mila is an autonomous research lab that predicts a cell's expression response to a genetic perturbation. A planner model (Claude Opus) proposes biological hypotheses. Cheap worker models (DeepSeek) implement each one as a Python feature. A controller tests every feature under a hard time limit, scores it, and keeps the result with its lineage; the planner reads the scores and proposes the next round.

The predictors are simple CPU models (ridge regression on agent-built features). The intelligence is in the features the agents find, and numbers alone decide which model wins. Over 3,000 experiments have run on the Adamson 2016 Perturb-seq screen, with the held-out perturbations' labels hidden from every agent.

## Headline result on Adamson

On CellForge's 21 held-out perturbations, every agent arm beats every baseline refit on the same split and the no-LLM control, on every column below. Run by run, the one exception is a single 1-worker run at pearson_delta 0.544, below the control's 0.554.

| Model | pearson_delta ↑ | MSE, top-20 DE genes ↓ | PCC, top-20 DE genes ↑ | R², top-20 DE genes ↑ |
|---|---|---|---|---|
| Unperturbed (control mean), refit | – | 0.226 | 0.900 | 0.606 |
| Linear regression, refit | – | 0.160 | 0.920 | 0.714 |
| Random forest, refit (3 seeds) | – | 0.198 ± 0.000 | 0.909 ± 0.000 | 0.650 ± 0.001 |
| Gene-Mila starting model (OLS, 3 built-in features) | 0.520 | 0.154 | 0.932 | 0.734 |
| No-LLM control (fixed template features; 6 identical runs) | 0.554 | 0.145 | 0.943 | 0.756 |
| Agents, 1 worker (2 runs) | 0.566 ± 0.032 | 0.109 ± 0.005 | 0.957 ± 0.001 | 0.817 ± 0.006 |
| Agents, 4 workers (2 runs) | 0.602 ± 0.002 | 0.117 ± 0.002 | 0.955 ± 0.001 | 0.803 ± 0.003 |
| Agents, 8 workers (2 runs) | 0.584 ± 0.001 | 0.119 ± 0.003 | 0.954 ± 0.001 | 0.802 ± 0.001 |
| Agents, 16 workers (2 runs) | 0.577 ± 0.022 | 0.111 ± 0.009 | 0.958 ± 0.004 | 0.816 ± 0.020 |

pearson_delta is the lab's primary metric: the Pearson correlation between the predicted and the true change from control, per perturbation, averaged; it is not computed for the refit baselines. The DE columns use each perturbation's top-20 DE genes by |log fold change|, CellForge's definition. Values are mean ± sd over runs.

All-gene PCC is left out on purpose: every model scores 0.985 to 0.988 on it, plain OLS included, so it says nothing about quality. The features the agents found are readable biology, mostly transfer of responses from perturbations whose targets share gene sets or protein-interaction neighbours with the new target. Each 20-minute run cost $0.17 to $1.38 of DeepSeek and ran on CPU only.

## Three caveats that travel with the result

1. No valid comparison with CellForge's published numbers yet. None of the metric definitions we tried reproduces their own baseline rows: they report the unperturbed baseline at PCC 0.0001, and on this data it scores 0.98. Their rows must not sit next to ours as the same measurement.
2. More agents did not give a better model. From 4 to 16 workers the visible validation score rose but the held-out score did not; 4 workers was best, and only "4 beats 8" exceeds repeat noise (Welch p = 0.01). Throughput scales, quality has not.
3. One dataset, one split, 20-minute runs, two repeats per setting. The gain over the no-LLM control is about +0.05 pearson_delta: real in these runs, modest, and untested on Norman and Srivatsan.

## Efficiency across worker counts

Throughput rose 8x from 1 to 16 workers; the held-out score did not. Per run (pearson_delta on the visible validation set / on the held-out set; experiments completed; DeepSeek $):

| Workers | Run 0 | Run 1 |
|---|---|---|
| 1 | 0.627 / 0.544; 82; $0.19 | 0.619 / 0.589; 93; $0.17 |
| 4 | 0.629 / 0.601; 159; $0.46 | 0.609 / 0.604; 112; $0.22 |
| 8 | 0.637 / 0.585; 280; $0.71 | 0.651 / 0.583; 275; $0.82 |
| 16 | 0.648 / 0.562; 657; $1.20 | 0.664 / 0.593; 722; $1.38 |

The visible and held-out scores diverge as workers are added: the agents overfit the 17 visible perturbations they select on, which the new selection rule in the planner check below addresses. Only the 4-versus-8 difference exceeds repeat noise (Welch p = 0.01; every other pair p ≥ 0.35). DeepSeek cost per run rises almost linearly with workers, from about $0.18 at 1 worker to $1.29 at 16, for no held-out gain. Worker utilisation stayed between 26% and 61%, because the planner, not CPU, bounds throughput. The full efficiency report is [scaling.md](scaling.md).

## Methods in brief

- Data: the Adamson et al. 2016 Perturb-seq screen of the unfolded protein response (CRISPRi, K562 cells), scPerturb file `AdamsonWeissman2016_GSM2406681_10X010.h5ad` from [Zenodo record 13350497](https://zenodo.org/records/13350497). Raw counts normalised to counts per 10k and log1p; 2,000 highly variable genes plus every target gene (2,055 genes); guides against the same gene merged; 88 knockdowns.
- Task and split: predict the mean expression profile of the cells carrying a perturbation the model has never seen, from the control cells and the training perturbations. CellForge's seed-42 split by perturbation: 50 train, 17 validation (visible to the agents), 21 test (held-out, scored once per finalist and never shown to any agent).
- Metrics: pearson_delta (primary); CellForge's MSE, PCC and R² on all genes and on each perturbation's top-20 DE genes by |log fold change|; VCWorld's change-direction metrics are computed for every experiment as well. Every score is per perturbation, averaged.
- Models: ridge regression on features. A feature is a Python function the agents write from the training perturbations' expression and public prior knowledge (gene sets, transcription-factor targets, protein-protein interactions). Selection uses the visible score only.
- Agents: Claude Opus plans (hypotheses with a biological rationale), DeepSeek workers implement; 20 minutes per run; 1, 4, 8 and 16 workers, two repeats each. The no-LLM control runs the same controller with fixed template features and the same time limit, and exhausts its ideas in about two minutes.
- Code and tables: this repository, branch `claude/autonomous-research-system-3k435s`, with [results_table.md](results_table.md) (CellForge's Table 1 layout) and [scaling.md](scaling.md) (the efficiency report), both generated from the run outputs.

## Running now and next

- Planner check on the new selection code, which averages the selection score over all 67 visible perturbations by cross-validation instead of the 17 validation perturbations: the two Opus-planned 4-worker runs finished at held-out 0.601 and 0.587, the same as the old code, and the lab's running score now tracks the held-out score within 0.01, where the old code overestimated it by 0.005 to 0.086. Two runs planned by DeepSeek V4 Pro are in progress; their rows are added here when they finish.
- Next: the same protocol on Norman et al. 2019 (combinatorial knockouts) and Srivatsan et al. 2020 (sci-Plex drug perturbations), then the CellForge comparison once a metric definition reproduces their baseline rows or their evaluation code is available. With selection now honest, longer runs are the next lever on the model itself.
