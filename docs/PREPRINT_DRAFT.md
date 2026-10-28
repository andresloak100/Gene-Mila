# Can LLM agents find the biology a simple model is missing? A pre-registered, cost-capped autonomous lab for predicting unseen genetic perturbations

Draft for a preprint (bioRxiv or arXiv, q-bio.GN / cs.AI), started 2026-10-28 by the lead (claim #41). Authors:
[Andres Arriaga, collaborators: to be decided by Andres]. Every number names the file it comes from; `[PENDING: ...]`
marks the two results due this week (block D's verdict, the GEARS runs). Longer methods: `docs/PAPER_COMPARISON.md`.

## Abstract

Deep models do not yet beat simple linear baselines at predicting the transcriptional response to a genetic
perturbation never seen in training. We ask whether LLM agents can supply what a linear model lacks: we fix the model
to a linear regression and let agents search only over features, so any gain is a biological claim written as code.
In our lab, Gene-Mila, a planner LLM proposes hypotheses, worker LLMs write each as a Python feature, and a Python
controller (never an LLM) owns the clock, the spending, the fitting and the held-out data, which it reads once, after
the run. Every experiment is pre-registered with its budget and pass rule. On the Adamson CRISPRi screen, agent arms
raised the sealed correlation of predicted and observed expression change from 0.520 (starting model) and 0.554 (the
same lab without an LLM) to 0.602 ± 0.002, yet one hand-written feature, transferring measured responses between
related knockdowns, gives the no-LLM lab 0.593. On the Norman CRISPRa pair screen no arm beat summing the two single-
gene effects (0.713; best arm 0.724 ± 0.005). Given clean biological knowledge and per-gene tables (genome annotation,
gnomAD constraint, UniProt), agents wrote 395 table-reading features, none of which passed a corrected fair test with
matched permutation nulls; a pre-registered human hypothesis failed too. We show that a standard gene-permutation
null cannot reject a feature that rescales an existing prediction, and give the corrected test. Under matched
conditions, CellForge's public release produced a templated plan unfit for the task, and GEARS scored
[PENDING: GEARS mean ± sd]. Twenty minutes of agent search costs about $0.50 to $1 and most of the gain arrives in the
first ten minutes. The bottleneck is information about which perturbations behave alike, not search.

## 1. Introduction

Predicting how every gene's expression changes under a perturbation not seen in training is the task of GEARS
(Roohani et al., 2024), of single-cell foundation models and of agent-built models such as CellForge (Tang et al.,
2025). A recent comparison found that none of the deep models tested outperformed simple linear baselines
(Ahlmann-Eltze, Huber and Anders, 2025). If linear models are hard to beat, the useful question is which inputs a
linear model is missing. That is a biological question, and it is the kind LLM research agents are claimed to answer.

We test that claim under conditions designed so that a negative result means something. The model is fixed to a
linear regression on CPU; agents may change only the features; held-out labels never enter a run; and every block of
paid experiments, with its readings and stop rule, is written into the repository before it starts. We report what
the agents found, what it cost, how it compares with a no-LLM control and with standard deep models, and one
statistical pitfall the design exposed.

## 2. Methods

**Task and data.** For a perturbation p and gene g the target is the change of g's mean log-normalised expression
from control. Adamson et al. (2016): CRISPRi in K562, 88 knockdowns, 2,055 genes, CellForge's seed-42 split by
perturbation (50 training, 17 visible validation, 21 sealed). Norman et al. (2019): CRISPRa in K562, 231 singles and
pairs, 2,083 genes, a gene-grouped split that keeps every held-out gene out of training (112 training, 63 visible,
56 sealed). Primary metric: pearson_delta, the per-perturbation correlation across genes of predicted and true change,
averaged; also MSE and top-20 differentially expressed gene metrics, including CellForge's own definitions.

**The lab.** A planner LLM (Claude Opus or DeepSeek v4-pro) reads a compressed, size-capped research state (scores,
coefficients, which features helped) and proposes hypotheses; worker LLMs (deepseek-flash) each implement one as a
plugin file through a read-only feature API; a static guard refuses file, network and reflection access and any read
of labels beyond the leave-one-out training changes; a smoke test checks shape, determinism and leakage; the
controller fits ridge, lasso, elastic net or OLS on CPU and scores on the visible tier. A no-LLM exploit engine adds
combinations between planner rounds. At the 20-minute deadline one model is chosen by a fixed visible-tier rule and
scored once on the sealed set through a capped oracle. Every LLM call is priced into a shared ledger with per-run and
per-block caps. (Figure 1: the system; Figure 2: the loop.)

**Controls.** The same lab with a scripted planner and no LLM; the starting model (OLS on three built-in features);
on Norman the additive rule (sum of the two single-gene changes).

**The fair test.** Each feature is added to a fixed parent model and refitted out of fold on fold seeds no run used.
Its gain is compared with a gene-permutation null (the feature's values shuffled across genes within expression bins)
and, when the feature is a parent column times a per-perturbation scalar, a perturbation null (the scalar shuffled
across perturbations). The family-wise max-gain step-down p must be at most 0.05 with 999 replicates (floor 0.001),
the gain above max(2 × overlap-robust SE, 0.002), winning on more than half the perturbations, every fold seed
positive, and the source must read no perturbation screen.

**Matched baselines.** CellForge (pinned commit 6585ff9) and GEARS 0.1.2 receive the same export: control and
training-perturbation cells on the same genes and normalisation, and the list of held-out perturbations; their
predictions are scored once by the same oracle (`tools/cellforge_bridge.py`, `tools/baselines_dl/run_gears.py`).

## 3. Results

**3.1 Agents beat a no-LLM control on Adamson, through one idea.** Sealed pearson_delta (two runs per arm): start
0.520; no-LLM control 0.554; agents with 1, 4, 8 and 16 workers 0.566 ± 0.032, 0.602 ± 0.002, 0.584 ± 0.001,
0.577 ± 0.022 (Opus planner); DeepSeek planner 0.570 ± 0.044 (`docs/results/summary_for_collaborators.md`). Only
4 versus 8 workers differs beyond run-to-run noise. Nearly all of the gain is response transfer: predict a new
knockdown from the measured responses of training knockdowns whose targets share pathways, complexes or interaction
partners. A compact model keeps a median of 4 of 15 selected features (`docs/results/feature_audit_v3.md`), and one
hand-written transfer feature gives the no-LLM lab 0.593. On leave-one-out training perturbations gene-set transfer
scores 0.540 against 0.474 for the mean response, and learning a richer similarity adds only 0.010
(`docs/results/ceiling_analysis.md`). The noise ceiling on the visible tier is 0.944 (`docs/results/noise_ceiling.md`).
(Figure 3.)

**3.2 On Norman nobody beats addition.** Sealed pearson_delta: additive rule 0.713; no-LLM control 0.717; agent arms
0.719 ± 0.007 (continuing a model), 0.724 ± 0.005 (from the additive start), 0.721 (one worker), 0.720 ± 0.001
(with a genome table). No arm establishes a gain over its own start under the reading rule. Selection overfits the
visible tier: the controls led the additive rule by 0.030 there and by 0.004 to 0.006 sealed. (Figure 4.)

**3.3 A permutation test that cannot fail.** In a block where agents read a genome-annotation table, they built,
unprompted in two of three runs, the additive prediction scaled by the targets' promoter CpG content, which restates a
known CRISPRa dependence. It first passed the pre-registered test. The pass was withdrawn: shuffling a per-
perturbation scalar across genes leaves the feature's shape intact, so the gene null had a standard deviation of
0.00001 and could not reject it, and with 20m − 1 replicates the smallest attainable p equalled the cutoff. Under the
corrected test (perturbation null, family-wise step-down, minimum effect) the feature gains 0.00056 ± 0.00015 and
fails (`docs/results/norman_f_corrected_pooled_holm/pooled_holm.json`). Six features do pass the corrected test, every
one built on another CRISPRi screen (Replogle et al., 2022), which the test is meant to exclude: the test has power
when a source carries the answer.

**3.4 Clean knowledge produced no new feature.** With knowledge restricted to sources measured without perturbing
genes (Reactome, curated GO, CORUM, CollecTRI, STRING physical links) plus three per-gene tables, twelve runs wrote 395
table-reading features (221 Adamson, 174 Norman); none passes, and the arms with and without the tables score alike
out of fold (Adamson 0.491 ± 0.004 vs 0.526 ± 0.035; Norman 0.579 ± 0.008 vs 0.578 ± 0.001;
`docs/results/*_g_pooled_holm`, `*_g1_vs_g0`). The known biology of every feature family the tables allow was written
with its predicted sign before scoring (`docs/PREREG_G_KNOWN_BIOLOGY.md`). Our own pre-registered hypothesis, gene
constraint residualised on expression and essentiality, failed on both datasets (Adamson gain −0.0013 ± 0.0011, whose
interval excludes the minimum effect; `docs/results/adamson_cf_lead_h8`).

**3.5 Showing the planner its errors.** A discovery mode shows the planner where its model fails and which inputs no
feature has read. In three Adamson runs it proposed 353 hypotheses, 101 on inputs never read before, for $1.01
(`docs/results/adamson_cf_d1_discovery_record.md`). [PENDING: block D fair-test verdict, PR #81.]

**3.6 Matched baselines.** CellForge's pinned public release, given our export and a DeepSeek model, completed task
analysis and method design but produced a plan built for drug-dose experiments (count-based filtering of normalised
data, batch correction without batches, dose curricula, three GPUs), traced to fixed templates in its code; it was
rejected at its first human checkpoint and nothing was trained ($0.16; `docs/results/cellforge_c/`, PR #84).
GEARS trained on the same export scored [PENDING: GEARS sealed pearson_delta mean ± sd over seeds 0, 2, 3, and paired
against the Opus-planned agent run; `docs/results/gears_adamson_s*.md`]. (Table 1.)

**3.7 Cost and time.** A 20-minute run costs $0.45 to $1.65 on the lab's ledger, about half that billed; all 43 paid
runs cost about $31 billed. A median 86% of a run's final gain arrives by minute 10; two 2-hour continuations added
0.003 sealed (`tools/time_to_best.py` report).

## 4. Discussion

The agents did useful work: they found, repeatedly and without being told, that related knockdowns respond alike,
and they did it for under a dollar per run. They did not find biology a careful person would not have written in an
afternoon, and when given richer tables they produced products and transforms of what the model already had. The
binding limit on these screens is information about which perturbations behave alike, not search, model or time.
Two lessons generalise. First, autonomous research systems need controls that are the same system without the LLM,
and baselines that receive exactly the same inputs; without them the Adamson gain would read as agent insight.
Second, permutation tests for engineered features must match the feature's structure, or they pass what they cannot
fail.

**Limitations.** Both sealed sets have been read many times, so sealed numbers are descriptive; a fresh, externally
held test set (a slice of the Replogle 2022 K562 screen) is planned, not run. Arms have two or three runs. Comparisons
with Biomni and a single coding agent are prepared, not run. Two datasets, one cell line.

**Availability.** Code, plans, every reading with its command and log, and 1,230 agent-written plugins:
github.com/andresloak100/Gene-Mila (MIT).

## References

Adamson B. et al. (2016) A multiplexed single-cell CRISPR screening platform... Cell 167, 1867.
Ahlmann-Eltze C., Huber W., Anders S. (2025) Deep-learning-based gene perturbation effect prediction does not yet
outperform simple linear baselines. Nature Methods.
Norman T.M. et al. (2019) Exploring genetic interaction manifolds constructed from rich single-cell phenotypes.
Science 365, 786.
Replogle J.M. et al. (2022) Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq.
Cell 185, 2559.
Roohani Y., Huang K., Leskovec J. (2024) Predicting transcriptional outcomes of novel multigene perturbations with
GEARS. Nature Biotechnology 42, 927.
Tang X. et al. (2025) CellForge: agentic design of virtual cell models. arXiv 2508.02276.
[Konermann 2015, Chavez 2016, Deaton and Bird 2011 for the CpG dependence; citation pass pending.]

## Figures and table (to build from the deck and `docs/results/`)

1. The system (inputs, one run, what is kept). 2. The agentic loop. 3. Adamson arms, sealed. 4. Norman arms, sealed.
5. The degenerate null: gene-null distribution vs perturbation-null distribution for the CpG feature.
Table 1: every arm on the Adamson sealed set (start, no-LLM, agents, hand-written transfer, GEARS, CellForge),
pearson_delta, MSE, CellForge DE metrics, cost.
