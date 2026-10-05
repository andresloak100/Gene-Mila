# Gene-Mila progress summary

*2026-10-04. A one-page summary for collaborating labs. Every number here is generated from the run outputs committed under `docs/results/`; the shareable copy is a Claude Doc kept in step with this file.*

## What we built

Gene-Mila is an autonomous research lab that predicts a cell's expression response to a genetic perturbation. A planner model (Claude Opus) proposes biological hypotheses. Cheap worker models (DeepSeek) implement each one as a Python feature. A controller tests every feature under a hard time limit, scores it, and keeps the result with its lineage; the planner reads the scores and proposes the next round.

The predictors are simple CPU models (ridge regression on agent-built features). The intelligence is in the features the agents find, and numbers alone decide which model wins. About 5,200 experiments have completed on the Adamson 2016 Perturb-seq screen across 27 runs (2,380 in the eight worker-count comparison runs, 2,345 in the five planner-check and selection-rule runs, 495 in fourteen no-LLM control runs), with the held-out perturbations' labels hidden from every agent.

## Headline result on Adamson

On CellForge's 21 held-out perturbations, every agent arm beats every baseline refit on the same split on the three DE columns below (pearson_delta is not computed for the baselines), and beats the seven-hypothesis no-LLM control on every column. Run by run, the exceptions are one 1-worker run (pearson_delta 0.544) and one DeepSeek-planned run (0.538), both below the control's 0.554.

| Model | pearson_delta ↑ | MSE, top-20 DE genes ↓ | PCC, top-20 DE genes ↑ | R², top-20 DE genes ↑ |
|---|---|---|---|---|
| Unperturbed (control mean), refit | – | 0.226 | 0.899 | 0.606 |
| Linear regression, refit (predicts the mean training response for an unseen perturbation) | – | 0.160 | 0.920 | 0.714 |
| Random forest, refit (3 seeds) | – | 0.198 ± 0.000 | 0.909 ± 0.000 | 0.650 ± 0.000 |
| Gene-Mila starting model (OLS, 3 built-in features) | 0.520 | 0.154 | 0.932 | 0.734 |
| No-LLM control (fixed scripted hypotheses; 6 identical runs) | 0.554 | 0.145 | 0.943 | 0.756 |
| No-LLM control plus one hand-written transfer feature (`response_components`, written after the agent runs; 1 run) | 0.593 | 0.142 | 0.943 | 0.755 |
| Agents, 1 worker (2 runs) | 0.566 ± 0.032 | 0.109 ± 0.005 | 0.957 ± 0.001 | 0.817 ± 0.006 |
| Agents, 4 workers (2 runs) | 0.602 ± 0.002 | 0.117 ± 0.002 | 0.955 ± 0.001 | 0.803 ± 0.003 |
| Agents, 8 workers (2 runs) | 0.584 ± 0.001 | 0.119 ± 0.003 | 0.954 ± 0.001 | 0.802 ± 0.001 |
| Agents, 16 workers (2 runs) | 0.577 ± 0.022 | 0.111 ± 0.009 | 0.958 ± 0.004 | 0.816 ± 0.020 |
| Agents, 4 workers, new selection code, Opus planner (2 runs) | 0.594 ± 0.009 | 0.124 ± 0.008 | 0.953 ± 0.003 | 0.791 ± 0.017 |
| Agents, 4 workers, new selection code, DeepSeek V4 Pro planner (2 runs) | 0.570 ± 0.044 | 0.133 ± 0.022 | 0.946 ± 0.010 | 0.776 ± 0.038 |

pearson_delta is the lab's primary metric: the Pearson correlation between the predicted and the true change from control, per perturbation, averaged; it is not computed for the refit baselines. The DE columns use each perturbation's top-20 DE genes by |log fold change|, CellForge's definition. Values are mean ± sd over runs. The first four agent rows and the control ran the original selection code; the last two rows ran the cross-validated selection described in the last section.

All-gene MSE, PCC and R² are left out on purpose: every model in the table scores an all-gene PCC between 0.979 (the unperturbed refit) and 0.987 (16 workers), plain OLS at 0.985, so those columns say nothing about quality. The features the agents found are readable biology, mostly transfer of responses from perturbations whose targets share gene sets or protein-interaction neighbours with the new target. Each 20-minute run cost $0.17 to $1.38 of DeepSeek worker calls plus an estimated $1.7 to $10.1 of Claude Opus planner usage (the Claude CLI's estimate; drawn from a subscription, not billed per run), and ran on CPU only.

## Three caveats that travel with the result

1. No valid comparison with CellForge's published numbers yet. None of the metric definitions we tried reproduces their own baseline rows: they report the unperturbed baseline at PCC 0.0001, and on this data it scores 0.98. Their rows must not sit next to ours as the same measurement.
2. More agents did not give a better model. From 4 to 16 workers the visible validation score rose but the held-out score did not. 4 workers was best on pearson_delta (on the top-20 DE columns 1 and 16 workers score slightly higher, within repeat noise), and only "4 beats 8" exceeds repeat noise (Welch p = 0.01). Throughput scales, quality has not.
3. One dataset, one split, 20-minute runs, two repeats per setting. The gain over the no-LLM control is +0.01 to +0.05 pearson_delta by arm (+0.05 for the best arm, 4 workers; about +0.03 averaged over the eight agent runs): real in these runs, modest, and untested on Norman and Srivatsan. That control runs seven fixed hypotheses. Given one more hand-written feature, a fitted transfer over low-rank response components written after the agent runs had shown that transfer between related targets is what works, the control scores 0.593 sealed pearson_delta, level with the agent arms (0.584 to 0.602), while the agents keep their lead on the DE columns (MSE_DE 0.117 to 0.124 against 0.142, R²_DE 0.79 to 0.80 against 0.755). So on pearson_delta the agents' margin over a strong hand-written feature is not established; on the DE genes it is. One run, designed after 26 sealed results on this split had been read, so its clean test is Norman.

## Efficiency across worker counts

Throughput rose 8x from 1 to 16 workers; the held-out score did not. Per run (pearson_delta on the 17 visible validation perturbations / on the 21 held-out test perturbations; experiments completed; DeepSeek $):

| Workers | Run 0 | Run 1 |
|---|---|---|
| 1 | 0.627 / 0.544; 82; $0.19 | 0.619 / 0.589; 93; $0.17 |
| 4 | 0.628 / 0.601; 159; $0.46 | 0.609 / 0.604; 112; $0.22 |
| 8 | 0.636 / 0.585; 280; $0.71 | 0.651 / 0.583; 275; $0.82 |
| 16 | 0.648 / 0.562; 657; $1.20 | 0.664 / 0.593; 722; $1.38 |

From 4 to 16 workers the visible and held-out scores diverge (mean visible-minus-held-out gap 0.02, 0.06 and 0.08; the 1-worker arm's is 0.06): the agents overfit the 17 visible perturbations they select on, which the new selection rule in the planner check below addresses. Only the 4-versus-8 difference exceeds repeat noise (Welch p = 0.01; every other pair p ≥ 0.35). Cost per run rises almost linearly with workers, DeepSeek from about $0.18 at 1 worker to $1.29 at 16 and the planner estimate from $1.75 to $9.55, for no held-out gain. Worker utilisation averaged 26% to 61% by arm (19% to 67% in individual runs), which points to the planner, not CPU, as the bound on throughput. The full efficiency report is [scaling.md](scaling.md).

## Methods in brief

- Data: the Adamson et al. 2016 Perturb-seq screen of the unfolded protein response (CRISPRi, K562 cells), scPerturb file `AdamsonWeissman2016_GSM2406681_10X010.h5ad` from [Zenodo record 13350497](https://zenodo.org/records/13350497). Raw counts normalised to counts per 10k and log1p; 2,000 highly variable genes plus every target gene (2,055 genes); guides against the same gene merged; 88 knockdowns.
- Task and split: predict the mean expression profile of the cells carrying a perturbation the model has never seen, from the control cells and the training perturbations. CellForge's seed-42 split by perturbation: 50 train, 17 validation (visible to the agents), 21 test (held-out). A run's finalists, chosen on the visible score, are scored on the test set once each at the end; the held-out number reported is that of the finalist with the best visible score, never the best held-out one, and the test labels are never shown to any agent.
- Metrics: pearson_delta (primary); CellForge's MSE, PCC and R² on all genes and on each perturbation's top-20 DE genes by |log fold change|; VCWorld's change-direction metrics are computed for every experiment as well. Every score is per perturbation, averaged.
- Models: ridge regression on features. A feature is a Python function the agents write from the training perturbations' expression and public prior knowledge (gene sets, transcription-factor targets, protein-protein interactions). Selection uses the visible score only (the selection score: the visible-set pearson_delta each run optimises and picks its finalist by).
- Agents: Claude Opus plans (hypotheses with a biological rationale), DeepSeek workers implement; 20 minutes per run; 1, 4, 8 and 16 workers, two repeats each. The no-LLM control is the same controller fed a fixed, scripted list of 10 feature hypotheses instead of a planner's proposals, under the same time limit; it is deterministic (six runs gave identical scores, so its ± 0 is not a noise estimate) and finishes its list in about two minutes.
- Code and tables: this repository, branch `claude/autonomous-research-system-3k435s`, with [results_table.md](results_table.md) (CellForge's Table 1 layout; it also shows CellForge's reported rows, marked as reported and not comparable, and a second DE definition, Wilcoxon BH p < 0.05 and |log2FC| > 0.5; its rank markers run across all rows and are not the comparison caveat 1 withholds) and [scaling.md](scaling.md) (the efficiency report), both generated from the run outputs.

## Planner check and selection-rule test, complete, and what comes next

- Planner check, complete (new selection code, 4 workers, 20 minutes, two runs per planner). The selection score, now cross-validated over all 67 perturbations whose labels the agents can see (50 training plus 17 validation), tracks the held-out score within 0.03, where the old code overestimated it by 0.005 to 0.086. Held-out pearson_delta did not improve: Opus-planned 0.601 and 0.587 against the old code's 0.601 and 0.604. DeepSeek V4 Pro as planner, at about $1.20 of DeepSeek per run and no Claude usage, matched Opus in one run (0.601) and fell below the no-LLM control in the other (0.538).
- Why the two DeepSeek runs differ: both planners received the same prompt and knowledge files, and the score tracks one idea, transferring responses between perturbations whose targets are similar. Opus proposed it in both runs within its first plan (107 and 101 such hypotheses); DeepSeek proposed it in one run (155) and almost never in the other (3 of 379). Two runs per planner, so this is a reading, not a measurement.
- The DE-column regression, and the selection rule we tested for it. On the top-20 DE columns the new code is worse than the old code for the agents (MSE_DE 0.124 against 0.117, R²_DE 0.791 against 0.803) and for the control (MSE_DE 0.163 against 0.145). The suspected cause was that the cross-validated selection favours much heavier regularisation (ridge alpha 300 to 30,000 against 0.001 to 100 before), which shrinks the predicted changes on the strongest DE genes, and that correlation cannot see the shrinkage. We therefore tested a selection score that also rewards R² on each perturbation's 20 most changed genes. On visible data alone (selecting on 50 perturbations and scoring on the other 17; the held-out labels were never read) it picked models better on the DE metrics in 9 or 10 of 11 runs, by about +0.02 R²_DE. In the one paid confirmation run, the same configuration and seed as an Opus-planned run under the old rule, that did not carry over: held-out pearson_delta 0.584 against 0.601, MSE_DE 0.116 against 0.118, R²_DE 0.804 against 0.802, and its finalists chose alpha 17,000 against 100 to 510. The rule is not adopted, the default stays pearson_delta, and heavier regularisation is not established as the cause of the regression. One run, one seed.
- Two free checks on the plateau (02:30 UTC 2026-10-05; design in docs/NEXT_LEVER.md). (a) Longer runs are not the lever: following each run's running best visible score, 60 to 92% of the final gain arrives in the first five minutes and 74 to 97% by ten; the last quarter adds +0.000 to +0.004 in 11 of 13 agent runs, and the two exceptions are 8- and 16-worker runs whose visible gains did not carry to the sealed set (tools/time_to_best.py; its report lands in docs/results/time_to_best.md). (b) A second kind of feature does move the control: the hand-written transfer over low-rank response components described in caveat 3 takes the no-LLM control from 0.554 to 0.593 sealed pearson_delta in one three-minute run, with heavier regularisation again (ridge alpha 41,000) and no gain on the DE columns.
- Next: the agents starting from that feature (first a free warm start of the scripted control from an agent run, then two Opus-planned 4-worker runs, paid, on Andres's word); the same protocol on Norman et al. 2019 (combinatorial knockouts), where the new feature gets its clean test, and Srivatsan et al. 2020 (sci-Plex drug perturbations); and the CellForge comparison once a metric definition reproduces their baseline rows or their evaluation code is available.
