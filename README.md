# Gene-Mila

*Agent-discovered features for linear prediction of genetic perturbation responses*

Research software · Adamson and Norman Perturb-seq · Updated 16 October 2026

## Abstract

Gene-Mila asks how far LLM agents can improve a linear model's prediction of gene-expression changes
under a genetic perturbation the model has never seen, within a fixed wall-clock budget. A planner
LLM proposes hypotheses; worker LLMs write one feature per experiment; a Python controller owns the
clock, the spend, the fitting and the scoring, and the model that uses the features stays ridge,
lasso, elastic net or OLS. On the Adamson CRISPRi screen (21 sealed knockdowns), agent arms score
0.566 to 0.602 sealed pearson_delta against 0.554 for a no-LLM control and 0.520 for the starting
model. Nearly all of that gain is one feature family, transfer of measured responses between related
knockdowns, and a control given one hand-written feature of that kind reaches 0.593. On the Norman
CRISPRa screen (56 sealed perturbations), neither of two repeated agent arms establishes a mean gain
over its start; averaging each arm's three models gives a small secondary gain. Every feature, every
failure and every score stays readable. The reference point is that linear baselines are still hard
to beat ([Ahlmann-Eltze, Huber and Anders, *Nature Methods*, 2025](https://www.nature.com/articles/s41592-025-02772-6)).

## Current status, 16 October 2026

The next question is whether the agents can find a *new kind* of biological feature, not another
variant of response transfer; the evidence so far says the limit is the information they can read,
not the search ([below](#can-the-agents-find-new-biology)). Ready but not run: a proposed rule for
which data sources are allowed (awaiting Andres's confirmation), a first source derived from the
genome sequence, tools that score any system's features on one fixed linear model against a matched
null, and a paid test on Norman (block F) fixed in advance; Andres allowed DeepSeek runs on
16 October, and the plan's $8 ledger cap awaits his OK. B1 remains the delivered Norman ensemble by
the fixed visible-validation rule; its three saved members reproduce exactly from the
[frozen export](https://github.com/andresloak100/Gene-Mila/pull/19). Both real-data sealed sets have
been scored repeatedly, so later readings on them are descriptive; a fresh test needs a separate
evaluator and an untouched cohort, and the
[cohort audit](https://github.com/andresloak100/Gene-Mila/blob/66ed4c69462b723bf2b800fb8a503ee198cc15c9/docs/EXTERNAL_COHORT_METADATA.md)
approves none yet. Continuation steps:
[HANDOFF section 1](HANDOFF.md#1-current-state-whoever-is-working-keeps-this-true); what is
integrated, draft or dated evidence: [documentation status](docs/DOCUMENTATION_STATUS.md).

## Results on Adamson

<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/hero-narrow.svg">
    <img src="docs/assets/hero.svg" width="100%" alt="Gene-Mila. Agents write the features. Only a linear model may use them. The clock stops everyone. Adamson Perturb-seq screen (CRISPRi, K562), pearson_delta on 21 sealed held-out knockdowns, mean ± sd over 2 runs per agent arm: starting model (OLS on 3 features) 0.520; no-LLM control 0.554; agents with 1 worker 0.566 ± 0.032, 4 workers 0.602 ± 0.002, 8 workers 0.584 ± 0.001, 16 workers 0.577 ± 0.022.">
  </picture>
</p>

**Fig. 1 | Worker count and predictive accuracy on Adamson.** Sealed pearson_delta on 21 held-out
knockdowns, mean ± sd over two repeats per agent arm. More workers increased throughput without a
corresponding rise in accuracy. The 8-worker arm includes one hash-sensitive selected model (table
footnote). Source: [worker-scaling report](docs/results/scaling.md).

The Adamson et al. 2016 screen of the unfolded protein response (CRISPRi in K562 cells) has 88
knockdowns; the bundle keeps 2,055 genes (2,000 highly variable genes plus every target).
CellForge's seed-42 split by perturbation gives 50 training, 17 visible-validation and 21 sealed
perturbations. Each run lasts 20 minutes; Claude Opus plans and DeepSeek workers write the
features. A run picks its finalists on the visible score only, each finalist is scored once on
the sealed set after the deadline, and the number reported is the sealed score of the finalist
with the best visible score, never the best sealed one.

| Sealed set, n = 21 | Runs | pearson_delta ↑ | MSE, top-20 DE ↓ | R², top-20 DE ↑ |
|---|---|---|---|---|
| Linear regression, refit on the same split | 1 | – | 0.160 | 0.714 |
| Starting model: OLS on three built-in features | 1 | 0.520 | 0.154 | 0.734 |
| No-LLM control: fixed scripted hypotheses | 6, identical | 0.554 | 0.145 | 0.756 |
| No-LLM control plus one hand-written transfer feature | 1 | 0.593 | 0.142 | 0.755 |
| Agents, 1 worker | 2 | 0.566 ± 0.032 | 0.109 ± 0.005 | 0.817 ± 0.006 |
| Agents, 4 workers | 2 | 0.602 ± 0.002 | 0.117 ± 0.002 | 0.803 ± 0.003 |
| Agents, 8 workers † | 2 | 0.584 ± 0.001 | 0.119 ± 0.003 | 0.802 ± 0.001 |
| Agents, 16 workers | 2 | 0.577 ± 0.022 | 0.111 ± 0.009 | 0.816 ± 0.020 |
| Agents, 4 workers, cross-validated selection, Opus planner | 2 | 0.594 ± 0.009 | 0.124 ± 0.008 | 0.791 ± 0.017 |
| Agents, 4 workers, cross-validated selection, DeepSeek V4 Pro planner † | 2 | 0.570 ± 0.044 | 0.133 ± 0.022 | 0.776 ± 0.038 |

† Each marked arm includes one hash-sensitive selected model (`runs/scale_w8_r0` and
`runs/newcode_ds_w4_r0`): one feature in each used Python's process-salted `hash()`, making its
score an arbitrary process-dependent draw. The [v3 feature audit](docs/results/feature_audit_v3.md)
identified them; the table and figure preserve the original readings. The integrated
[guard and hash-seed fix, `3d7c519`](https://github.com/andresloak100/Gene-Mila/commit/3d7c519)
prevents this path in new experiments but does not reproduce the historical draw.

Mean ± sd over runs. pearson_delta is the Pearson correlation between predicted and measured change
from control over all 2,055 genes, per perturbation, averaged. The DE columns use the bundle's stored
top-20 reference: the absolute Wilcoxon rank-sum statistic, with absolute log fold change as a
tie-breaker ([definition](genemila/benchmark/reference.py)). This differs from the
largest-absolute-change subset used by the paired ensemble readings on Norman; neither establishes a
matched CellForge evaluation. Sources:
[`summary_for_collaborators.md`](docs/results/summary_for_collaborators.md),
[`results_table.md`](docs/results/results_table.md) (every arm, labelled by code version, in
CellForge's Table 1 layout) and [`scaling.md`](docs/results/scaling.md) (cost, throughput and
significance by arm).

- **Agents average above the fixed recipe, modestly.** Every agent arm's mean is above the starting
  model and the no-LLM control on sealed pearson_delta, and above every refit baseline and the
  control on the DE columns; but for the 1-worker and DeepSeek-planned arms the margin (+0.012,
  +0.016) is inside their spread (sd 0.032, 0.044), and two agent runs scored below the control
  (0.544 and 0.538).
- **The gain is one idea.** Nearly all of it is transfer of the measured responses of training
  knockdowns whose targets share gene sets or protein-interaction neighbours with the new target.
  Given one hand-written feature of that kind, the no-LLM control reaches 0.593, level with the
  agent arms on pearson_delta; the agents keep their lead on the DE columns.
- **More workers bought throughput, not accuracy.** From 1 to 16 workers, experiments per run rose
  from 88 ± 8 to 690 ± 46 and DeepSeek cost from $0.182 ± 0.015 to $1.287 ± 0.125; the sealed score
  did not rise. The archived Welch comparison of 4 against 8 workers (p = 0.01, two runs per arm)
  includes the hash-sensitive 8-worker model and establishes no reproducible difference. Most of a
  run's gain arrives in its first half ([`time_to_best.md`](docs/results/time_to_best.md)).
- **The limit is information about the targets.** Under cell-sampling noise alone a perfect
  predictor would score about 0.944 on the 17 visible-validation perturbations; the selected models
  of 28 runs reach 0.563 to 0.664 ([`noise_ceiling.md`](docs/results/noise_ceiling.md)). Longer
  runs, refits on more labels and pruning did not help ([`LAB_STATE.md`](docs/LAB_STATE.md)). The
  one lever found is another K562 screen: in leave-one-out on the 50 training perturbations, a ridge
  stack that uses the Replogle 2022 genome-wide screen scores 0.616 ± 0.233 against 0.545 ± 0.264
  for gene-set nearest-neighbour transfer, +0.072 ± 0.020 paired (SE), better on 34 of 50
  ([`external_loo_replogle2022_k562.md`](docs/results/external_loo_replogle2022_k562.md)); without
  the screen's columns the stack scores 0.543. Added without an LLM to one Opus-planned agent run's
  features, the screen reads 0.646 on the sealed set, in one run, on a set already scored for dozens
  of finalists across about 30 runs: one more look, not a result.
- **Left out on purpose.** Every model in the table, and predicting no change at all, has an
  all-gene PCC between 0.979 and 0.987, so all-gene MSE, PCC and R² cannot separate models.
  CellForge's published rows are not placed beside these: a fixed Table 1 evaluator was not located
  in the inspected release, and no tested metric definition reproduces its own baseline rows (its
  unperturbed baseline has PCC 0.0001; on this data it scores 0.98;
  [comparability audit](https://github.com/andresloak100/Gene-Mila/pull/13)).

## Results on Norman

The Norman et al. 2019 screen (CRISPRa activation in K562, single genes and gene pairs) is read
only at points fixed in advance ([`NORMAN_PLAN.md`](docs/NORMAN_PLAN.md),
[`PLAN_AFTER_N4.md`](docs/PLAN_AFTER_N4.md)). The bundle has 231 perturbations on a split that
keeps every held-out single gene out of training: 112 training, 63 visible and 56 sealed. The
reference is the additive baseline (a pair predicted as control plus its two single-gene
responses). A single model's gain counts when it exceeds twice its paired standard error and the
model is better on more than half the perturbations. For an arm of three DeepSeek runs (4 workers,
20 minutes each) the primary question is whether the search adds to the model it starts from: the
arm's mean gain over its start must exceed about twice a standard error that includes the spread
between runs and the target genes perturbations share, every run must point the same way, and the
arm must be better on more than half the 168 perturbation-run pairs. Every B1 and B2 number is in
[`NORMAN_PLAN.md`](docs/NORMAN_PLAN.md) section 8.

| Arm of three runs, sealed set, n = 56 | pearson_delta of the selected models, mean ± sd | Mean gain over the start (SE) | Better on | Verdict |
|---|---|---|---|---|
| B1: N4 repeated with seeds 1 to 3, continuing N2's model (0.719) | 0.719 ± 0.007 | 0.000 (0.007) | 88 of 168 | not established: the runs differ in sign |
| B2: fresh runs from ridge with the additive prediction as a feature (0.716) | 0.724 ± 0.005 | +0.008 (0.006) | 110 of 168 | not established: under its bar of 0.012; every run positive |

In neither arm is the runs' mean gain over their start established (the primary reading). Against
the additive baseline, a secondary reading: B1's arm +0.006, SE 0.013, not established; B2's clears
its bar by the narrowest margin (0.011290 against 0.011267), too thin to rest on. The average of
each arm's three models does better than its start (below).

| Sealed set, n = 56 | pearson_delta | minus additive (paired SE) | Better on |
|---|---|---|---|
| Additive baseline | 0.713 | | |
| No-LLM control (N1) | 0.717 | +0.004 ± 0.008 | 28 of 56 |
| No-LLM control with the Replogle screen (N2) | 0.719 | +0.006 ± 0.007 | 32 of 56 |
| N3: agents with the screen, from scratch; best agent-built model | 0.671 | not read | |
| N4: agents continuing N2; planner lost at minute 18.7 of 20 | 0.726 | +0.014 ± 0.008 | 37 of 56 |
| B1's combined model: the average of its three runs' models | 0.723 | +0.010 ± 0.007 | 36 of 56 |
| Ridge with the additive prediction as a feature, B2's start | 0.716 | not read | |
| No-LLM control from that start | 0.719 | not read | |
| B2's combined model: the average of its three runs' models | 0.727 | +0.014 ± 0.003 | 45 of 56 |

**Controls.** Neither N1 nor N2 is established above the additive baseline on the sealed set,
although on the 175 visible and out-of-fold training perturbations both led it (+0.030 ± 0.009 and
+0.031 ± 0.008, paired SE): selection overfits the perturbations it chooses on. The Replogle screen
adds +0.002 ± 0.001 (paired SE) pooled, better on 40 of 56: it passes the reading rule but is too
small to matter ([`norman_sealed_reading.md`](docs/results/norman_sealed_reading.md)).

**Single agent runs.** N3 (DeepSeek planner and workers, the screen in its bundle, no warm start)
selected the additive baseline itself, because no agent-built model beat it on the visible score;
its best agent-built model scores 0.671 sealed
([`norman_n3_sealed_reading.md`](docs/results/norman_n3_sealed_reading.md)), and one of 355 plugins
read the screen. N4 (the same agents continuing from N2's model, $1.16) selected a model that
scores 0.726 but establishes neither +0.014 ± 0.008 over the additive baseline nor +0.008 ± 0.004
over its start ([`norman_n4_sealed_reading.md`](docs/results/norman_n4_sealed_reading.md)); its
planner ran out at minute 18.7, when the spending cap then in force bound, so it is an arm of its own.

**Repeated arms.** B1 repeated N4 three times on the same code; the selected models scored 0.711 to
0.726, so N4's +0.008 looks like one draw from a search whose mean gain over the start is 0.000 (SE
0.007). Averaging is what helps: B1's combined model, the plain average of the three runs' models,
scores 0.723, +0.004 ± 0.001 over N2's model (paired SE, better on 38 of 56), where single runs
gained −0.008 to +0.007. The gain is small and a secondary reading; it is the delivered Norman
model. B2's runs started fresh from ridge with the additive prediction as a feature, as fresh agent
runs on pairs do from commit `c6fadc0` on; seed 1 was killed by the watchdog while finishing and
decides nothing, and seed 3 took its place, a departure from the plan recorded before any B2 reading
(over seeds 0 and 2 as first specified, the arm is not established either). B2's combined model
scores 0.727, +0.011 ± 0.002 over its start (44 of 56) and +0.014 ± 0.003 over the additive baseline
(45 of 56): the first Norman model whose gain over that baseline passes the reading rule, as a
secondary reading (N4's was as large, with an SE of 0.008). It is not established over the no-LLM
control from the same start (+0.008 ± 0.006) or over B1's combined model (+0.004 ± 0.006). The
delivered model stays B1's, by a choice fixed before B2 and made on the 63 visible perturbations
(0.780 against 0.751).

**Top-20 DE genes.** On the stored top-20 DE reference the agents' models do no better than the
additive baseline: R²_DE 0.847 ± 0.008 for B1's runs and 0.828 ± 0.027 for B2's, against 0.846
(N4: 0.819). B2's most shrunk run (ridge alpha 300,000) has its best pearson_delta and its worst DE
scores. A development-only diagnostic on four built-in features under three fixed fold seeds did
not support a benefit from magnitude calibration
([saved report](https://github.com/andresloak100/Gene-Mila/blob/a699d449050e5aee8def1e9eed848df720b5ce96/docs/results/norman_development_shrinkage_20261013/report.md));
it does not diagnose B1's larger feature models, and B1 is unchanged.

**Development tests on B1, 13 October, training cohort only.** A fixed gene-hidden comparison
supports a simpler r1+r2 average over the three-member refit ensemble: pearson_delta 0.584 ± 0.011
against 0.459 ± 0.021, paired gain 0.125 ± 0.016, with lower overall and top-20 error but mean
errors still above additive ([results](docs/B1_TWO_MEMBER_RESULTS.md)). Three further fixed tests
failed their gates and stay unmerged: a
[nested blend](https://github.com/andresloak100/Gene-Mila/blob/72e26bd/docs/B1_NESTED_BLEND_RESULTS.md)
(too much correlation lost), a
[stronger r2 penalty](https://github.com/andresloak100/Gene-Mila/blob/618c4da/docs/B1_R2_REGULARIZATION_RESULTS.md)
(over its top-20 error limit) and a
[copied per-pair feature correction](https://github.com/andresloak100/Gene-Mila/blob/dab64d0/docs/B1_PAIR_BATCH_RESULTS.md)
(Pearson change −0.000003 ± 0.000028; additive MSE guard failed). The
[recipe diagnosis](docs/B1_DIAGNOSTIC_RESULTS.md) explains B1's weakness. All are partitions of one
training cohort after member selection, not a fresh held-out evaluation; B1 stays delivered.

Norman's sealed set has now been scored for many models (B2's readings alone made 58 sealed
scorings), so from here on comparisons on it are descriptive
([`PLAN_AFTER_N4.md`](docs/PLAN_AFTER_N4.md), "What happens after"). By the spend ledger, B1 cost
$4.11 and B2 $5.51, its killed run included; the ledger counts about twice what DeepSeek bills.

## Can the agents find new biology?

On 15 October Andres asked for one biological feature that the current linear model lacks, found by
the agents without being told where to look. The plan he and his machine-learning collaborator set
that day: if one holds up, the work becomes a biology paper; if the agents only raise the score, a
machine-learning paper comparing systems. Holding up means naming the biology, replicating on
another cohort and passing a wet-lab test. [`docs/NOVEL_FEATURE_NEEDS.md`](docs/NOVEL_FEATURE_NEEDS.md)
sets out what that takes. Nothing in this section has run on real perturbation data.

**The limit is information, not search.** On Adamson, every winning model so far copies the
measured responses of knockdowns whose targets resemble the new one
([`docs/NEXT_LEVER.md`](docs/NEXT_LEVER.md)); on Norman the agents start from the additive pair
rule. In leave-one-out over Adamson's 50 training perturbations, only another K562 perturbation
screen added clearly (Replogle 2022, +0.072 ± 0.020 paired SE over gene-set neighbours); a learned
mix of the bundle's own gene sets, interactions and co-expression added +0.010, inside the noise.

**Which data may be added.** Proposed rule, awaiting Andres's confirmation: a source is allowed if
it was measured or derived without perturbing genes and holds none of the responses being
predicted. Tier 1 (genome and protein sequence, curated complexes, population constraint,
unperturbed K562 chromatin and binding maps) is allowed; tier 2 (MitoCarta, mRNA half-lives,
recruitment screens) only as separately labelled arms; perturbation screens, Replogle included, and
expression atlases stay out of the main claim (needs document, section 7).

**A first tier-1 source.** `tools/build_gene_annotation.py` turns GENCODE and the hg38 sequence
into a per-gene table: locus, opposite-strand TSS partners, neighbours, message lengths, promoter
CpG content and amino-acid composition. For Norman's 2,083 genes it matched 2,041; the other 42 are
retired symbols (SEPP1, KIAA0101, TCEB1, …). Of the measured genes, 96 have their TSS within 1 kb
of another's on the opposite strand (mostly head-to-head shared promoters; 16 of the 48 pairs
overlap at their 5' ends instead), so a CRISPRa or CRISPRi guide at one can also reach the other.
That is known biology: if the agents find it, it is a methods result, not a new rule. Adamson names
some targets by retired symbols too (SRPR, MARS, ATP5B), so they may get no gene sets or
interactions from the knowledge files; `tools/knowledge_coverage.py` counts this per target once it
runs on the Mac's data.

**A stricter test of a feature.** The planner calls a feature helpful after a +0.002 visible gain:
one parent-to-child difference, with no standard error. `tools/feature_compare.py` refits one fixed
ridge model, the lab's starting model plus a system's whole feature set or one of its features, out
of fold on the training perturbations, and reports pearson_delta, MSE and four metrics on each
perturbation's 20 most-changed genes, a paired gain whose standard error allows for shared target
genes, and a matched null (the feature's values shuffled between genes of similar control
expression), Holm-corrected within each system. Every system has seen these training labels, so a
verdict only screens candidates; a claim needs the fresh test, whose separate evaluator does not
exist yet.

**Other systems on the same task.** `tools/export_task_package.py` writes the task as a folder in
the style of [karpathy/autoresearch](https://github.com/karpathy/autoresearch): the public data
every lab experiment receives, a fixed evaluator that keeps or discards each change by an
out-of-fold noise rule, caps on the constants a file may hold (so training labels cannot be pasted
in), and one editable `features/` directory, for a coding agent (Claude Code or Codex) or Biomni
to work in. [`docs/FEATURE_COMPARISON_PROTOCOL.md`](docs/FEATURE_COMPARISON_PROTOCOL.md) fixes the
arms (the lab with four workers and with one, a coding agent, Biomni, CellForge, STATE), the
fairness controls and the metrics table. No outside system has run yet; who pays, an isolating
container on the Mac and a GPU for CellForge and STATE are Andres's decisions.

**The first paid test is fixed before it runs.**
[`docs/PLAN_F_GENOME_ANNOTATION.md`](docs/PLAN_F_GENOME_ANNOTATION.md) (block F) repeats the three
B2 Norman runs with one change: the genome annotation file is added beside B2's Replogle file. The
agents get no list of hypotheses, so whatever they build from it is theirs. The primary reading is
`tools/feature_compare.py` on every feature that reads the file; the comparison with B2 on Norman's
sealed set is one more look at a set already read many times. The prior expectation is that a
table of this kind usually adds 0.01 or less. Andres allowed DeepSeek runs on 16 October; the plan
proposes an $8 ledger cap (about $4 billed), which awaits his OK. It has not run. Because F keeps
B2's Replogle file, a perturbation screen outside tier 1, only gene_annotation features that do not
also read that file can support a tier-1 claim.

**Genes and cost.** The bundles keep about 2,000 genes. The LLM bill does not grow with genes
(agents write code and never read the matrix); CPU time and memory do. A feature is code, so one
found on 2,000 genes can be rescored on all expressed genes without an LLM call. More
perturbations, not more genes, narrow the error bars. Commands for these tools:
[`docs/USAGE.md`](docs/USAGE.md#tools-for-the-feature-comparison).

## Methods

<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/loop-narrow.svg">
    <img src="docs/assets/loop.svg" width="100%" alt="How one experiment moves through the lab, inside a dashed deadline frame. Claude, as planner, reads the research memory and proposes hypotheses as JSON. The Python controller queues them and adds sweeps and replicates. A worker LLM writes a single plugin file in its own git worktree. Python guards check it: AST rules, a smoke and label-leakage test, and a diff limited to that file. Code that fails goes back to the worker for a fix; if it still fails it is recorded as failed, or as rejected when forbidden code remains or the edit reaches outside its file. A ridge, lasso, elastic net or OLS model is fitted on CPU in a limited subprocess, the controller scores it by pearson_delta on visible validation, and the result goes into the research memory the planner reads next round. After the deadline: running fits get 30 seconds and are killed, the top 3 candidates and the best baseline are scored once each on the query-only set, finalists are scored with Arc's cell-eval when held-out cells exist, and a watchdog kills the process group if anything overruns.">
  </picture>
</p>

**Fig. 2 | The experiment lifecycle.** LLMs propose hypotheses and write feature code; Python
schedules, fits, scores and keeps the deadline, then makes the capped sealed-set queries after the
run. Source: [architecture](docs/ARCHITECTURE.md).

**Roles.** The planner (Claude Opus, or DeepSeek V4 Pro) reads a compressed research state of at
most 20,000 characters, however long the run, and proposes hypotheses as JSON. Workers (DeepSeek,
Claude Haiku or any OpenAI-compatible model) see the spec, a 30-line API reference, one example
plugin, short summaries of the data and the prior-knowledge files, and the names of the model's
other features; never the repository or the experiment history. The Python controller sees
everything: deadline, queue, retries, concurrency, evaluation, the query-only oracle, SQLite.

Six rules make a gain mean something. Each is enforced in code, not in a prompt.

| # | Rule | How the code enforces it |
|:-:|---|---|
| **1** | **The clock kills everything.** | A run gets `--minutes` or `--hours`. At the deadline the controller stops new experiments and LLM calls, gives running fits `run.shutdown_grace_s` (30 s), then kills them. `run_research.py` runs the lab as its own process group and SIGKILLs the group if it is still alive 180 s later, then writes the summary from `lab.db`. Completed models are kept. |
| **2** | **Linear models only.** | Ridge, lasso, elastic net or OLS, on CPU; any other model type is refused when the experiment is specified (`ALLOWED_MODELS` in `genemila/spec.py`). Fits run in a limited subprocess with a wall timeout, `RLIMIT_CPU` and `RLIMIT_AS`, and the controller picks alpha on visible validation. The rule binds the model fitted on the features; feature code may use numpy, scipy and scikit-learn, including models fitted on leave-one-out training responses. |
| **3** | **One new feature per experiment.** | A worker may change exactly one file, its plugin under `genemila/features/plugins/`, so a score change has one candidate cause. The diff guard rejects any other edit and any touch of the evaluator, data, splits or guards (`genemila/guard.py`). |
| **4** | **Numbers decide, never an LLM.** | The controller scores every experiment with its own evaluator (`genemila/benchmark/evaluator.py`). Ranking, sweeps, replicates, duplicate detection and scheduling are Python. |
| **5** | **The sealed set is read only after the run.** | Perturbations, not cells, are split 60/20/20 (or by an external split, `--splits`) into train, visible validation and query-only validation, hashed into a `split_id`. Experiments predict both validation sets without knowing which is which. Only `QueryOracle` reads the query-only labels, after the run: one query each for the top `final.top_k` distinct candidates and the best baseline, capped at `final.max_queries`, every query logged. |
| **6** | **Every feature is tested for leakage.** | Before a feature runs, the smoke test swaps one training perturbation's label for noise and checks that the feature's rows for it do not move. It also checks shape, NaN, determinism and constancy. An AST guard allows numeric imports only: no file I/O, network, processes or reflection. |

Compute limits, spend caps, spec hygiene and integrity checks are listed in
[`docs/USAGE.md`](docs/USAGE.md#architecture).

### The prediction

For perturbation $p$ and gene $g$, one linear model shared across all rows predicts the change in
mean expression:

```math
\Delta_{p,g} \;=\; \bar{x}_{g \mid p} \;-\; \bar{x}_{g \mid \text{control}} \;\approx\; w^{\top} f(p, g) + b
```

A feature $f$ maps $(p, g)$ to one or a few numbers (`genemila/features/api.py`), so each
coefficient weighs one named signal for every perturbation and gene. The primary metric,
`pearson_delta`, is the Pearson correlation between predicted and true change across genes for each
held-out perturbation, averaged over perturbations. Model selection uses every visible perturbation:
each experiment also predicts the training perturbations out of fold (`experiment.cv_folds`, folds
fixed per run by the lab, not by agents), so the search signal rests on 60-70 perturbations instead
of 15-20. Baselines run first: no change, the mean training response, and OLS, ridge and lasso on
control mean, leave-one-out mean response and a target indicator; on the synthetic example run's
visible validation they score 0 (a constant prediction has no correlation), 0.4755 and 0.6054.
`pearson_delta` has two known soft spots: it correlates over every gene, the knocked-out gene
included, whose own drop is easy to predict, and it is measured against control, so a response that
all perturbations share scores well on its own (the mean training response's 0.4755 on the synthetic
screen; the systematic-variation problem described by Systema, Viñas Torné et al., 2025). Every
experiment is therefore also scored with CellForge's metrics (MSE, PCC and R² on mean expression,
over all genes and over the top-20 DE genes) and VCWorld's DE and direction classification metrics
(`genemila/benchmark/comparable.py`), and finalists with Arc Institute's
[cell-eval](https://github.com/ArcInstitute/cell-eval) when held-out cells exist.

### Synthetic check of the machinery

<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/example-run-narrow.svg">
    <img src="docs/assets/example-run.svg" width="100%" alt="Every experiment of the synthetic example run, plotted in queue order by pearson_delta on 16 visible-validation perturbations. Worker-written features range from 0.6053 to 0.7775. Twelve alpha sweeps sit on the 0.6054 linear baseline or the 0.7633 plateau, and one planner-proposed combination briefly held the best score at 0.7683. The winning lineage adds one feature per step: target_coexpression +0.1579 to 0.7633, target_knockdown_scaled +0.0136 to 0.7769, tf_gated_coexpression +0.0007 to 0.7775. EXP_0027 failed because its feature leaked the label. On 16 sealed query-only perturbations the best model scored 0.7764, a scripted control with no LLM 0.7776, and the linear baseline 0.5942.">
  </picture>
</p>

**Fig. 3 | Feature lineage in the synthetic screen.** Experiments in queue order, with the selected
lineage highlighted. The synthetic biology tests the machinery; it is separate from the real-data
campaigns. Source: [example-run artifacts](docs/example_run/).

Before the real screens, the lab ran on a synthetic knockout screen whose biology is known (300
genes, 80 knockouts; Claude Opus planning, four Claude Haiku workers). One worker-written feature,
the knocked-out gene's co-expression row in control cells, took pearson_delta on visible validation
from 0.6054 to 0.7633; two smaller steps reached 0.7775, and the sealed set gave 0.7764 against
0.5942 for the baseline. The same split with no LLM at all, a scripted planner and hand-written
template features, reached 0.7702 and 0.7776 in 2 minutes for $0
([control](docs/example_run/control_scripted_summary.md)); the agents, who never saw the templates,
re-derived them. One feature that read its own label was caught by the smoke test and recorded as
failed. So the run shows that the machinery works and that the agents reach a hand-written
reference, not what they add beyond one. The lineage, the worker's code, the fitted coefficients
and a second test with DeepSeek workers are in [`docs/USAGE.md`](docs/USAGE.md#the-synthetic-example-in-detail).

### Benchmark

Gene-Mila follows CellForge's benchmark ([arXiv 2508.02276](https://arxiv.org/abs/2508.02276)):
its datasets (Adamson, then Norman; Srivatsan's sci-Plex 3 waits on drug and dose ingestion) and
its metrics, with Unperturbed, Random Forest and Linear Regression refitted on the same split and
laid out like its Table 1 ([`results_table.md`](docs/results/results_table.md)). CellForge's
published rows stay marked as reported, not comparable, until a metric definition reproduces its
baseline rows; a real comparison needs CellForge's model run through this evaluation on the same
split, which needs a GPU. VCWorld's benchmark ([ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/file/767ff070c27c8954babe74eccf3fbe91-Paper-Conference.pdf))
is drug perturbations only, so its DE and direction metrics are computed on Adamson and Norman, not
on its data. What each system produces and scores is tabulated in
[`docs/USAGE.md`](docs/USAGE.md#relation-to-cellforge-and-vcworld).

## Limitations

- **Both sealed sets are worn.** Adamson's 21 sealed perturbations have been scored for dozens of
  finalists across about 30 runs, and the hand-written transfer feature was designed after 26
  sealed results had been read. Norman's 56 were read only at pre-specified points, but after B1
  and B2 the set has been scored for many models. Later readings on either set are descriptive and
  weaker evidence than the first.
- **No arm's mean gain over its start is established on Norman.** Averaging each arm's three
  models gives small gains that pass only as secondary readings.
- **Few, short runs.** Two runs per agent arm on Adamson; on Norman three per arm for B1 and B2,
  one for N3 and N4; 20 minutes each, one split per dataset. Most differences between arms are
  inside run-to-run noise. The no-LLM control is deterministic, so its six identical runs are not a
  noise estimate.
- **A small gain, of one kind.** The agents' lead over the fixed no-LLM control on sealed
  pearson_delta (+0.01 to +0.05 by arm, the smallest inside run-to-run spread) disappears against
  a control given one hand-written transfer feature, written after the agent runs had shown what
  works; their lead on the DE columns remains.
- **Continuation feedback and the oracle.** Warm starts used to expose the prior winner's
  aggregate sealed score to the planner; [PR #13](https://github.com/andresloak100/Gene-Mila/pull/13)
  removed that path, but historical exposure remains part of the record. The oracle shares
  filesystem access with orchestration: the process-level guards stop accidental leakage, not a
  determined program running as the same OS user.
- **Features may learn, and may recall.** A feature can fit its own model on training responses,
  leaving its own perturbation out; the linear-only rule binds the outer model, so reading a gain
  means reading its feature's code. On real genes, worker LLMs know the literature, so a gain may
  come from recalled biology rather than from the screen; only a control that hides gene
  identities would separate the two.
- **Comparable metrics, not comparable runs.** CellForge's and VCWorld's metrics are
  reimplemented from their papers (`genemila/benchmark/comparable.py`), not run from their code,
  and no tested definition reproduces CellForge's baseline rows. cell-eval scores only the
  finalists, and because the lab predicts each perturbation's mean change, cell-eval's
  distribution metrics see a point mass per perturbation.

## Data and code availability

The code is public in this repository. The Adamson et al. 2016 screen (scPerturb file
`AdamsonWeissman2016_GSM2406681_10X010.h5ad`) and the Norman et al. 2019 screen
(`NormanWeissman2019_filtered.h5ad`) come from [Zenodo record 13350497](https://zenodo.org/records/13350497);
`prepare_data.py` normalises raw counts (counts per 10k, log1p), merges guides against the same
gene, keeps 2,000 highly variable genes plus every target, and splits by perturbation. Prior
knowledge is downloaded once from Reactome, GO Biological Process, MSigDB Hallmark, CollecTRI and
STRING v12; the Replogle 2022 K562 screen was added as audited external knowledge and is recorded
in each run's configuration. Data bundles and fitted run artifacts stay on Andres's Mac and are
excluded from Git. Committed here: the dated [result reports](docs/results/), the
[Mac archives](docs/mac/) (summaries, configurations, checksums), the Norman split and manifest
(`docs/results/norman_splits.json`, `docs/results/norman_manifest.json`), the
[frozen B1 export](docs/results/norman_frozen_export_20261013/), the synthetic
[example run](docs/example_run/) and the figure sources.

## Reproducibility

Every reported arm names its dataset, split (`split_id` in `summary.json`), run directories and
code version, and runs are compared only within one bundle and split. Repeat means and sds are
kept separate from paired standard errors and single-ensemble estimates. Each run writes `lab.db`,
`summary.md` and `summary.json`, pins every experiment's code at `refs/genemila/<run>/<experiment>`
and logs every sealed-set query. The frozen export reproduces all three saved B1 members exactly,
and their average passes the fixed numerical tolerance
([PR #19](https://github.com/andresloak100/Gene-Mila/pull/19)). The figures are drawn from the run
reports by `docs/assets/build_figures.py`, and `tools/readme_check.py` traces every score on this
page to a file under `docs/`.

Needs Python 3.11 or newer. An offline run with no API keys, the no-LLM control of the synthetic
example:

```bash
pip install -r requirements.txt
python -m pytest -q
python run_research.py --minutes 2 --workers 4 --worker-provider mock --planner-provider scripted
```

Paid runs state their planner provider, the shared ledger and their caps explicitly, and start only
on Andres's own words ([AGENTS.md](AGENTS.md)). Data preparation, configuration, providers, the
outputs of a run, scaling and the synthetic example in detail: [`docs/USAGE.md`](docs/USAGE.md).

## References

- Adamson, B. et al. [A multiplexed single-cell CRISPR screening platform enables systematic
  dissection of the unfolded protein response](https://doi.org/10.1016/j.cell.2016.11.048).
  *Cell* **167**, 1867–1882 (2016).
- Norman, T. M. et al. [Exploring genetic interaction manifolds constructed from rich single-cell
  phenotypes](https://doi.org/10.1126/science.aax4438). *Science* **365**, 786–793 (2019).
- Replogle, J. M. et al. [Mapping information-rich genotype–phenotype landscapes with genome-scale
  Perturb-seq](https://doi.org/10.1016/j.cell.2022.05.013). *Cell* **185**, 2559–2575 (2022).
- Ahlmann-Eltze, C., Huber, W. and Anders, S. [Deep-learning-based gene perturbation effect prediction
  does not yet outperform simple linear baselines](https://www.nature.com/articles/s41592-025-02772-6).
  *Nature Methods* **22**, 1657–1661 (2025).
- [CellForge](https://arxiv.org/abs/2508.02276), arXiv 2508.02276. Dataset and reported-metric reference;
  its published rows remain contextual until both methods are evaluated on identical locked data.
- [VCWorld](https://proceedings.iclr.cc/paper_files/paper/2026/file/767ff070c27c8954babe74eccf3fbe91-Paper-Conference.pdf),
  ICLR 2026. DE and direction-classification reference; Gene-Mila has not yet run its drug benchmark.
