# The comparison paper: skeleton (goal b of `docs/GOAL_CRITERIA.md`)

Written 2026-10-17 by the lead (claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)) under `docs/ROADMAP.md`: the skeleton of the machine-learning paper for a
methods venue, in the lab's voice. The Methods are final where the protocol is fixed (`docs/FEATURE_COMPARISON_PROTOCOL.md`, `docs/PLAN_H_COMPARISON.md`,
`docs/PLAN_R_FRESH_TEST.md`); the Results are a template. Every number comes from a file in this repository, named beside it; where a number does not exist yet, a bracketed
placeholder names the record that will hold it. Nothing of block H or the fresh test has run. It supersedes `docs/archive/plans/PAPER_FRAMEWORK_PROPOSAL.md`.

## Title (working)

Agent-written features for a fixed linear model: comparing autonomous research systems on unseen genetic perturbations.

## Abstract

Deep models for predicting the transcriptional response to a genetic perturbation do not yet beat simple linear baselines (Ahlmann-Eltze, Huber and Anders, 2025). We ask a
narrower question: with the model fixed to one ridge regression, can autonomous agents find features that make it predict perturbations it has never seen, and which system
finds the better ones. In Gene-Mila a planner LLM proposes hypotheses, worker LLMs write one feature each as a small Python file, and a Python controller owns the clock,
the spending, the fitting and the scoring. We exported the task as a package in the style of karpathy/autoresearch and gave it, unchanged, to [N arms;
`docs/PLAN_H_COMPARISON.md`, Arms] systems on the Adamson 2016 CRISPRi screen: this lab with four workers and with one, Biomni's general biomedical agent, an
autoresearch-style coding-agent loop, a scripted no-LLM control and four features translated by hand from CellForge's design, each for three 20-minute sessions under the
same wall clock, the same LLM and a $2.50 session cap. Every feature was then scored by one procedure, out of fold on fold seeds no system used, against two matched
permutation nulls with a family-wise correction. Out of fold, the system rows scored [mean ± sd per arm; `docs/results/adamson_cf_h_compare/feature_compare.json`]. On a
fresh test, a slice of the Replogle 2022 K562 CRISPRi screen held and scored once by a collaborator after the predictions' hashes were posted, [the arm that won, its gain
and paired SE; the holder's R2 report under `docs/results/`]. In an earlier block on Norman the agents recovered a published dependence from sequence alone, the additive
prediction scaled by the targets' promoter CpG content, a gain of 0.00056 ± 0.00015 pearson_delta (`docs/results/norman_f_readings.md`).

## Introduction

Predicting how gene expression changes under a perturbation the model has not seen is the task of GEARS (Roohani, Huang and Leskovec, 2024), of foundation models and of
CellForge's agent-built models (Tang et al., 2025). A 2025 study in Nature Methods found that none of the deep models tested outperformed simple linear baselines
(Ahlmann-Eltze, Huber and Anders, 2025), and PerturBench reached a similar reading (Wu et al., 2024). If linear models are hard to beat, the question is not which
architecture to build but which inputs a linear model lacks.

We fix the model and move the search to the features. A feature maps a (perturbation, gene) pair to one or a few numbers from public knowledge and the training screen; one
ridge regression over all pairs weighs the features. The question is whether an autonomous system can find features that raise the fixed model's held-out score, and whether
this lab's planner-and-workers design finds better ones than a single coding agent in a loop, a general biomedical agent, or a scripted control, on the identical task.

Gene-Mila is that lab. Agents write the code; Python fits, scores, keeps the deadline and the spending, and reads the sealed set once, after the run (`README.md`, Methods).
On the Adamson screen the agents' arms scored 0.566 to 0.602 sealed pearson_delta against 0.554 for a no-LLM control and 0.520 for the starting model, and nearly all of the
gain was one feature family, the transfer of measured responses between related knockdowns (`README.md`, Results on Adamson; `docs/results/scaling.md`). On Norman no arm's
mean gain over its start was established. Those numbers come from sealed sets read many times and from arms that ran only in this lab. This paper makes the comparison fair
in both respects: every system runs on one exported task package with equal feedback, every feature is scored by one tool, and the headline numbers come from a fresh cohort
that no system and no person on the project has scored before.

## Methods

### The task

Datasets. The Adamson et al. 2016 screen (CRISPRi in K562, the unfolded protein response) has 88 knockdowns; the bundle keeps 2,055 genes, 2,000 highly variable genes plus
every target, and CellForge's seed-42 split by perturbation gives 50 training, 17 visible-validation and 21 sealed perturbations, `split_450515be1a0d8d2e` (`README.md`,
Results on Adamson; `docs/FEATURE_COMPARISON_PROTOCOL.md`, section 5). The Norman et al. 2019 screen (CRISPRa, single genes and pairs) has 231 perturbations, 112 training,
63 visible and 56 sealed, `split_a391fa9e7b4eccb7` (`docs/results/norman_manifest.json`). The prediction is the change of the per-perturbation mean (counts per 10,000,
log1p) from the control mean. The comparison block runs on Adamson only, from the clean bundle `data/adamson_cf_clean_tables`, whose knowledge is tier 1 (Reactome, curated
GO, CORUM, CollecTRI, STRING physical links, per-gene tables from GENCODE and hg38, gnomAD and UniProt) and holds no perturbation screen (`docs/PLAN_G_CLEAN_ARM.md`, Arms;
`docs/PLAN_H_COMPARISON.md`).

Metric. The primary metric is pearson_delta: for each held-out perturbation, the Pearson correlation between predicted and true change over all genes, averaged over
perturbations (`genemila/benchmark/evaluator.py`). Beside it: the same without the perturbation's own targets; MSE over all entries; MSE, R², Pearson of the change and
direction accuracy on each perturbation's 20 most-changed genes; and the delta scale ratio (M1 to M7 and M12 of the protocol, section 5). CellForge's and VCWorld's DE
metrics need held-out cells and are reported where cells exist; every DE column names its top-20 ranking, since three definitions are in use.

The fixed model and the parents. One ridge regression over (perturbation, gene) rows, the penalty chosen on out-of-fold scores of one fold seed and reported on another,
over every ordered pair of the fold seeds 101, 102 and 103 (`tools/feature_compare.py`, docstring). Every arm starts from the same parent P0, the lab's built-in start:
`control_mean`, `mean_response`, `is_target`, and `additive_response` on a bundle with pairs (`genemila/features/registry.py`; protocol, section 2); on Adamson the parent
has no `additive_response` (`HANDOFF.md`, section 1, note of 2026-10-17). A second parent P1, a strong known set, is a second reading.

### The lab

A planner LLM reads a research state of at most 20,000 characters and proposes hypotheses as JSON. Worker LLMs each write one feature plugin, a class with `compute(ctx,
perts, params)` returning an array of shape (perturbations, genes, dim) (`genemila/features/api.py`), seeing the API, one example, summaries of the data and knowledge files
and the names of the model's other features, never the repository. `FeatureContext` is the only door to the data. The guard (`genemila/guard.py`) allows numeric imports
only, no file I/O, network, processes or reflection, and a smoke test swaps one training label for noise and checks that the feature's rows for it do not move. The
controller schedules, fits, scores and stops everything at the wall clock; the sealed set is read once after the run through a capped oracle (`README.md`, Methods, rules 1
to 6). In block H the lab runs with the DeepSeek planner `deepseek-v4-pro`, `deepseek-flash` workers, 20 minutes, per-run caps of $1.00 for the workers and $1.50 for the
planner, and the shared spend ledger (`docs/PLAN_H_COMPARISON.md`, Arms).

### The task package

`tools/export_task_package.py` writes the task as one folder: the public data every lab experiment receives, the knowledge files, `features/` as the one editable surface,
`evaluate.py` as the fixed evaluator, `literal.py`, which caps the literals a feature file may hold so that training labels cannot be pasted in, `MANIFEST.json` with the
fold seeds, keep rule and parent features, and `program.md` as the whole prompt (`tools/task_package/program.md`). `evaluate.py` keeps a change only when its gain exceeds
twice its standard error and 0.002, wins on more than half the perturbations and is positive under every fold seed; a deletion is kept when it costs less than one plain
standard error (`program.md`, The keep rule). One feature file may change per evaluation; the kept state in `runs/kept/features/` is the arm's hand-back (protocol, section
2).

The harness tier. The lab's controller selects on the visible validation perturbations and the out-of-fold training perturbations together (`genemila/lab.py`). So the
package ships the visible validation labels as `harness/val1.npz`, `evaluate.py` decides on the combined score with the same noise rule, and `program.md` tells the agent
the file is readable from the shell, that feature code cannot open it, and that reads are scanned and recorded (`docs/ROADMAP.md` D5). The visible tier is then a seen tier
for every arm, and the fresh test the one tier whose labels no arm had (protocol, note of 2026-10-17). Andres may veto the tier (`docs/ROADMAP.md`, section 7, item 3); a
package exported with `--no-harness-val1` keeps the earlier rules.

### The other systems

All arms run on the same package, three sessions each (seeds 0, 2 and 3 name the sessions), 20 minutes each, the same LLM where the system allows it, through a proxy that
adds the key, prices every call, writes the shared ledger and refuses calls past a $2.50 session cap (`tools/baselines/ledger_proxy.py`; `docs/PLAN_H_COMPARISON.md`,
Money). The agents receive a dummy token and the proxy's address, never the key.

- A1, this lab, four workers: block G's `runs/adamson_cf_g1_ds_w4_r{0,2,3}`, not re-run; A1-ablation, the same bundle without the three per-gene tables,
  `runs/adamson_cf_g0_ds_w4_r{0,2,3}` (`docs/PLAN_H_COMPARISON.md`, Arms).
- A2, this lab with one worker: `runs/adamson_cf_h_a2_ds_w1_r{0,2,3}`, settings of `docs/PLAN_B4_SINGLE_WORKER.md`.
- A3, an autoresearch-style loop: one coding agent with a shell inside a copy of the package, `program.md` as its prompt, editing one feature file and running `python
  evaluate.py` until the clock kills it, as karpathy/autoresearch does. It runs through the Codex CLI the Mac has, pointed at `deepseek-v4-pro` through the proxy's
  Responses-API route, web tools off; Claude Code is the disclosed fallback, `run.json["client"]` records which ran, and Codex's 10-second shell timeout and its sandbox are
  disclosed per session (`docs/PLAN_H_COMPARISON.md`, note of 2026-10-17 03:52 UTC).
- A4, Biomni: its A1 agent (`source="OpenAI"`, `llm="deepseek-v4-pro"`, no data lake) given `program.md`. Biomni runs agent code with `exec()` in its own process, has no
  budget cap, and two of its code paths print the key; so it runs in isolation with a dummy key, the proxy as its only route, and a runner that stops at the cap (protocol,
  section 2, A4). A $0.05 probe settles whether `deepseek-v4-pro` accepts its consecutive assistant messages; if not, the arm is reported as "could not run on DeepSeek
  v4-pro" (`docs/ROADMAP.md`, section 5, B.1).
- C0, the scripted no-LLM control: the lab with `--planner-provider scripted --worker-provider mock`, fixed hypothesis templates, free,
  `runs/adamson_cf_h_c0_scripted_w4_r{0,2,3}`.
- C2, CellForge's ideas translated by us: four plugins written by hand from CellForge's public code and model cards, gene-network propagation, pathway transfer, a latent
  perturbation offset and a pair-interaction term (`docs/comparison/cellforge_c2/README.md`); the pair term is constant on Adamson and is rejected there. Nothing in them is
  CellForge's output; the arm is spelled "CellForge ideas, translated by us".

Not comparable, and why. CellForge produces a deep model and a training script, not features; it ships no weights, one run takes 4 to 8 GPU-hours, and in the released code
the plan that reaches code generation is built from fixed templates (protocol, section 2, A5). Its published Table 1 rows cannot be reproduced under any metric definition
tried, and its unperturbed baseline has an all-gene PCC of 0.0001 where every model on this data scores about 0.98 (`docs/results/calibration_adamson_cf_val2.md`;
`README.md`, Results on Adamson). Its rows stay marked not comparable (`docs/ROADMAP.md` D9). STATE (Adduri et al., 2025) is out: its public weights were trained on the
Replogle K562 screen that the fresh test uses (D9).

Isolation. Only the package folder is mounted, never the lab checkout; network only to the proxy. On the Mac this is Docker with an internal network and a relay, or a
second macOS account holding only the package, where the filesystem isolation holds, the network isolation does not, and the proxy log and the transcript scan are the check
(`docs/PLAN_H_COMPARISON.md`, Isolation). Without either, the foreign arms wait; transcripts are scanned for credential patterns, network calls and reads outside the
package.

### The fair test

`tools/feature_compare.py` scores every arm alike: one system row (parent plus all the arm's kept features) and one add-one row per feature (parent plus that feature
alone), with the same ridge, alpha grid, fold seeds and metrics, in one call per bundle so every row shares one parent scoring (protocol, sections 4 and 6). Foreign code
never runs in the scoring process: each file passes the guard and the literal caps statically and is computed in child processes, every feature recomputed in every fold
view. The pieces, fixed on 16 and 17 October 2026 after block F (`docs/ROADMAP.md` D2):

- Two matched nulls. The gene null permutes the candidate across genes within bins of control expression and refits the whole procedure. A candidate that is, within every
  perturbation's row, a per-perturbation scalar times one parent column cannot fail that null, because the parent factor stays in the model; such a row is marked
  proportional (relative residual 1e-6, checked in every fold view) and also gets the perturbation null, in which the scalars are permuted across training perturbations
  within deciles of the targets' mean control expression with the parent columns left in place. It must pass both.
- Family-wise correction. A max-gain step-down permutation test (Westfall and Young) over one source's add-one rows, the permutation of each replicate shared by every row,
  at B = 999 replicates (floor 0.001); a family with fewer reads "null too coarse", not failed. The Holm p of the raw null p is kept for comparison only.
- Deduplication. Rows of one source with an identical prediction hash (out-of-fold predictions rounded to 1e-9) collapse to one before the correction; a column and its
  rescaling are one member.
- The minimum effect. The mean gain must exceed max(2 SE_adj, 0.002), where SE_adj is the paired standard error widened by the perturbations' target-gene overlap
  (`tools/sealed_reading.py`) and 0.002 is the package's noise rule (`docs/ROADMAP.md` D3); wins on more than half the perturbations; a gain outside the targets; `mse_top`
  not significantly worse; every fold-seed report positive.
- The coefficient sign. The standardised add-one coefficient is saved per report, so the sign is read against the one pre-registered in `docs/PREREG_G_KNOWN_BIOLOGY.md`.

Every system selected on these training labels, so a development verdict screens candidates for the fresh test and proves nothing. Candidate lists are fixed with sha256 on
#41 before the tool runs, and `--with-val1` stays off (protocol, section 6; `docs/ROADMAP.md` D5).

### The fresh test

Design and holder. Commit, then reveal, on the Replogle et al. 2022 genome-wide K562 CRISPRi screen (`ReplogleWeissman2022_K562_gwps.h5ad`, Zenodo 13350497, md5
`13db594f8f1d2ccb88fec44a13e414dc`; 1,989,578 cells by 8,248 genes; `docs/PLAN_R_FRESH_TEST.md`, section 1). Adamson is K562 CRISPRi, so the Adamson arms are scored; Norman
gets no fresh test, since the two CRISPRa cohorts audited give four usable genes (`docs/EXTERNAL_COHORT_METADATA.md`). The holder, Andres's ML collaborator [handle: PLAN_R,
section 8], obtains the file from the public record, never from the Mac, posts its sha256 on #41, keeps it and every score where no agent can reach, scores one deposit once
and posts two dated reports, the replication slice R1 then the fresh slice R2, nothing changed between them (PLAN_R, sections 1 and 7).

Eligibility. `tools/replogle_slice_manifest.py` reads only the file's obs and var tables through a guard that refuses every other key. A target is eligible when it has at
least 20 cells, names exactly one gene, is not among the Adamson or Norman bundle targets (matched under current and retired HGNC symbols) and is inside the frozen gene
universe. An in-distribution subset is pre-registered from metadata alone, targets sharing a Reactome or CORUM class with an Adamson training target; the rest is reported
separately; under 30 in-distribution targets, the arm criteria are reported as not powered. The draw uses a public seed named before the file is opened (PLAN_R, sections 2
and 3). [Eligible counts: the manifest's `manifest.md` and its sha256 on #41.]

The deposit. Every model in the batch predicts every eligible target through `tools/frozen_model.py predict-targets` without refitting, after the adapter has reproduced
each arm's saved predictions to 1e-6 (`docs/results/norman_frozen_export_20261013/report.md`: three B1 members exact). The batch is, per arm, its three system models and at
most three single features with a development verdict and the largest out-of-fold gain, plus the additive rule and C0; only arms from bundles without a perturbation screen
enter. The deposit is one archive (manifest, `predictions.npz`, `receipt.json` and `queries.json` per model, the common gene panel) whose sha256 goes on #41 before the
holder is told it exists (PLAN_R, sections 4 to 6).

Reading rule. The holder computes per-perturbation means and the control mean with the ingest's normalisation and scores with the evaluator's metrics unchanged. A feature
is useful when its model beats its parent in pearson_delta by more than twice the paired standard error with wins on more than half the in-distribution perturbations of R2,
with the pre-registered sign; an arm beats a baseline under `tools/arm_reading.py`'s rule (gain above k·SE, SE from the paired spread and the run-to-run spread, every run
the same sign, most wins). Every paired comparison in the batch enters one Holm correction at 0.05. Then nobody refits, re-exports, adds a model or deposits again (PLAN_R,
section 7). Physical access, stated as the plan requires: the raw file has been on the Mac since 10 October 2026 at the latest, and a knowledge file built from it was in
later Adamson and Norman development bundles; it holds the Replogle responses of those bundles' own targets, which every slice excludes. The test is held out by protocol
and by the holder, not by physical separation (PLAN_R, section 1).

### Costs and ledger accounting

Every paid call lands in one shared SQLite ledger, priced from `configs/default.toml`. The ledger counts about twice what DeepSeek bills: block F cost $2.82 on the ledger
and $1.41 billed, a ratio of 2.0 (`docs/ROADMAP.md`, note of 2026-10-17 02:10 UTC). Every cap counts ledger dollars. B2's three Norman runs cost $1.29, $1.37 and $1.19 and
block F's $1.29, $0.29 and $1.25 (`docs/results/norman_f_readings.md`, reading 4). Block H's cap is ledger + $15, expected $8 to $13 (`docs/PLAN_H_COMPARISON.md`, Money).
[Per-arm minutes, calls, tokens and cost: the proxy logs `h_<arm>_r<S>.jsonl` and `summary.json["llm_usage"]`; the reading in `docs/results/block_h/`.]

### Pre-registration, and what changed when

Each block is a plan fixed before any run; from the first paid call a change is a dated note at the end, never an edit. Three changes belong in the paper. (1) B2's seed 1
was killed by the watchdog while finishing and seed 3 took its place, recorded before any B2 reading (`README.md`, Results on Norman). (2) Block F's two-stage reading rule
was amended at 04:20 UTC on 16 October and committed at 19:45 UTC, after the paid search had begun and before any reading (`docs/results/norman_f_readings.md`, Provenance).
Under it ten rows passed and A.1 was declared met at 22:05 UTC; at 23:40 UTC that reading was withdrawn, because the gene null cannot fail a feature that is a parent column
times a per-perturbation number (null sd 0.00001 against a gain of 0.00056; 14 of 20 tested rows, a random projection among them, hit the same p floor;
`docs/results/norman_f_stage2/feature_compare.json`), and because with 20·m − 1 replicates the smallest pooled Holm p equalled the 0.05 cutoff by construction
(`docs/GOAL_CRITERIA.md`, Status). The corrected test is the one above; block F is re-read under it. (3) The harness tier and the Codex client were added on 17 October,
before any session (`docs/ROADMAP.md` D5; `docs/PLAN_H_COMPARISON.md`, note of 03:52 UTC). The known biology of every family the per-gene tables allow was written down with
its sign before any block G score was read, in a file the pinned run code predates (`docs/PREREG_G_KNOWN_BIOLOGY.md`).

## Results (template)

### Table 1. The metrics table, one row per arm (columns from `docs/FEATURE_COMPARISON_PROTOCOL.md`, section 5)

Out-of-fold tier, parent P0, fold seeds 101 to 103, B = 999; mean ± sd over three sessions; gains are candidate minus parent (parent minus candidate for MSE), so positive
is better. Source for every cell: `docs/results/adamson_cf_h_compare/feature_compare.json` [not yet run; `docs/PLAN_H_COMPARISON.md`, reading 1].

| arm | n sessions | OOF M1 | ΔM1 ± SE_adj vs P0 | wins | ΔM2 | ΔM3 | ΔM4 | ΔM5 | ΔM7 | M12 | features kept | with a verdict | minutes, calls, tokens, $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 lab, 4 workers (G1) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [`summary.json["llm_usage"]`] |
| A1-ablation, no tables (G0) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| A2 lab, 1 worker | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| A3 autoresearch-style (Codex) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [proxy log] |
| A4 Biomni | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [proxy log] |
| C0 scripted control | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | $0 |
| C2 CellForge ideas, translated by us | 1 set | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | 3 | [ ] | $0 |
| Additive rule / P0 | reference | [ ] | | | | | | | | | 0 | | $0 |
| CellForge-Models, as reported, other split | not comparable | | | | | | | | | | | | |

The fresh-test columns of the same table (R2 in-distribution M1, Δ vs P0 ± paired SE, wins, Holm p; the out-of-distribution subset beside them) come from [the holder's R2
report, posted on #41 and copied unedited under `docs/results/`]. A session that handed back no kept feature is a row with the parent's score, not a dropped row.

### Table 2. Found features, per arm, under the fair test

One row per add-one row with a development verdict, after deduplication; source `docs/results/adamson_cf_h_compare/feature_compare.json`, then the holder's R2 report.

| arm | feature | knowledge it reads | proportional to | ΔM1 ± SE_adj (OOF) | p_fwer gene | p_fwer pert | coefficient sign | pre-registered family and verdict | R2 gain ± SE, wins, Holm p |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [`docs/PREREG_G_KNOWN_BIOLOGY.md`] | [ ] |

### Figures

- Figure 2. Per arm, each session's out-of-fold M1 against its parent, with the arm mean; the fresh-test M1 beside it. [`feature_compare.json`; the R2 report.]
- Figure 3. Every feature's add-one gain against its null distributions, proportional rows marked, with the step-down threshold. [`feature_compare.json`, `null.gains`,
  `null_pert.gains`.]
- Figure 4. Cost and throughput per arm: evaluations per session, tokens and ledger dollars against the gain. [proxy logs; each package copy's `results.tsv`;
  `summary.json`.]

### The one existing result: block F on Norman

Three Norman runs from B2's start with one change, a per-gene table built from GENCODE and hg38 added to the bundle and no hypothesis given, wrote 94 plugins, 66 of them
scoreable as add-one rows (`docs/results/norman_f_readings.md`). In two runs independently the agents built the same feature: the additive prediction scaled by the targets'
mean promoter CpG observed/expected ratio (r0 twice, r3 once). Its gain over the parent is +0.00056 ± 0.00015 pearson_delta, wins 69 of 112, a thousandth of the score; a
TSS-distance scaler gained +0.0014 ± 0.0005 (`norman_f_readings.md`, Primary feature reading). The feature restates published biology: CRISPRa raises highly expressed genes
least, and CpG-island promoters mark that class (Konermann et al., 2015; Chavez et al., 2016; Wu et al., 2023). Its coefficients in the runs' own models were +0.0147,
+0.0143 and −0.0100, so no sign is stated (`docs/results/norman_f_coefficient_signs.md`). At the arm level the table did not raise the score: selected models 0.7196 ±
0.0012 sealed against B2's 0.722, 0.720 and 0.730, and out of fold 0.5805 ± 0.0023 against 0.5825 ± 0.0081 (`norman_f_readings.md`, readings 2 and 3). Two lessons carry
into the Methods: a null must match the feature's structure (a random projection passed beside the CpG feature), and a permutation floor that equals the cutoff is not a
p-value. Block F's rows are re-read under the corrected test [`docs/results/norman_f_stage2_corrected/`, or the path the operator names].

## Discussion

Claims this design can support. (1) Whether a fixed linear model gains from agent-built features at all, out of fold and on a fresh cohort, with the gain's size and paired
uncertainty. (2) Which of the systems run on the identical package supplies the better features, under the arm rule, with three sessions per arm, and what each cost. (3)
That the agents recover known dependencies from sequence alone, as block F shows, read against a pre-registered list of known biology. (4) That the fair test as first built
passed a feature it could not fail, and what a matched test needs. (5) That CellForge's published rows are not comparable on this data, with the reasons.

Claims it cannot support. No biology discovery claim: a feature that passes the fair test and the fresh test is a predictive feature, and a new rule only with a named
mechanism, a predicted sign, a replication and a wet-lab test (`docs/GOAL_CRITERIA.md`, A.2 to A.6); every family the per-gene tables allow has a known rule behind it
except one (`docs/PREREG_G_KNOWN_BIOLOGY.md`). No claim that the fresh test is physically sealed: the raw file was on the Mac, so the test is held out by protocol and by
the holder. No claim of a difference inside run-to-run noise: three sessions per arm, and a coding agent has no seed, so a session is a draw. No claim from the sealed sets:
both have been scored many times and are descriptive. No claim about Biomni or CellForge as systems, nor about the model class: a feature may itself fit a model on training
responses.

Limitations. One cell line and modality for the fresh test; one dataset for the comparison block; 20-minute sessions; one LLM; the lab's own package and keep rule shape
every foreign arm; the paste check rests on the guard, the literal caps and a transcript scan; the client and isolation differences are disclosed, not removed; the ledger
is a priced estimate at about twice the bill; the fresh test is one scoring with no second look.

What would strengthen it. More sessions per arm; a second fresh cohort in another cell line; Norman package arms (a later dated section, if the ledger allows;
`docs/ROADMAP.md` D6); CellForge's own model through our evaluator on a GPU; a control that hides gene identities, to separate recalled biology from the screen; the wet-lab
test of `docs/ROADMAP.md` D13 for any feature that survives.

## Data and code availability

The code is this repository. The Adamson and Norman screens come from Zenodo record 13350497; the Replogle 2022 K562 file from the same record, obtained by the holder
independently. Knowledge sources and receipts: `docs/PLAN_G_CLEAN_ARM.md`, `docs/mac/block_g/`. Committed: every plan, every dated result under `docs/results/`, the run
records under `docs/mac/`, the C2 plugins, the frozen B1 export, and [the block H hand-backs, proxy logs and `feature_compare` outputs; the fresh-test manifest, deposit
hashes and the holder's reports]. Data bundles, run directories and the ledger stay on Andres's Mac, excluded from Git.

## References

Marked as in `docs/CANDIDATE_LITERATURE_CHECK.md` (VERIFIED: an abstract or page was fetched there; UNVERIFIED: a search summary, or not in that file).

- Ahlmann-Eltze, C., Huber, W. and Anders, S. Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Nature Methods 22,
  1657 to 1661 (2025). VERIFIED.
- Roohani, Y., Huang, K. and Leskovec, J. Predicting transcriptional outcomes of novel multigene perturbations with GEARS. Nature Biotechnology (2024), doi
  10.1038/s41587-023-01905-6. VERIFIED.
- Wu, Y. et al. PerturBench: benchmarking machine learning models for cellular perturbation analysis. arXiv 2408.10609 (2024). VERIFIED.
- Tang, X. et al. AI scientists for building virtual-cell models (CellForge). arXiv 2508.02276 (2025; v3 2026-10-14 retitled). VERIFIED.
- Adduri, A. et al. Predicting cellular responses to perturbation across diverse contexts with STATE. bioRxiv 10.1101/2025.06.26.661135 (2025). VERIFIED.
- Huang, K. et al. Biomni: a general-purpose biomedical AI agent. bioRxiv 10.1101/2025.05.30.656746 (2025). VERIFIED.
- Karpathy, A. autoresearch (code repository), github.com/karpathy/autoresearch (2026). VERIFIED (README fetched); not a peer-reviewed paper.
- Adamson, B. et al. A multiplexed single-cell CRISPR screening platform enables systematic dissection of the unfolded protein response. Cell 167, 1867 to 1882 (2016).
  VERIFIED.
- Norman, T. M. et al. Exploring genetic interaction manifolds constructed from rich single-cell phenotypes. Science 365, 786 to 793 (2019). VERIFIED.
- Replogle, J. M. et al. Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Cell 185, 2559 to 2575 (2022). VERIFIED.
- Konermann, S. et al. Genome-scale transcriptional activation by an engineered CRISPR-Cas9 complex. Nature 517, 583 to 588 (2015). VERIFIED (abstract); its
  inverse-basal-expression dependence is figure-level, UNVERIFIED.
- Chavez, A. et al. Comparison of Cas9 activators in multiple species. Nature Methods 13, 563 to 567 (2016). VERIFIED (abstract); the locus-to-locus variability is
  full-text level, UNVERIFIED.
- Wu, Y. et al. Massively parallel characterization of CRISPR activator efficacy in human induced pluripotent stem cells and neurons. Molecular Cell 83 (2023), doi
  10.1016/j.molcel.2023.02.011. VERIFIED.
- Westfall, P. H. and Young, S. S. Resampling-based multiple testing (Wiley, 1993). UNVERIFIED: not in the literature check; the method the step-down follows.
- VCWorld, ICLR 2026 (the DE and direction metrics). UNVERIFIED: cited from `README.md`, not in the literature check.
