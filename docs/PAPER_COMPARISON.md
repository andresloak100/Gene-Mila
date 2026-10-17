# The comparison paper: skeleton (goal b of `docs/GOAL_CRITERIA.md`)

Written 2026-10-17 by the lead (claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)), serving goal b of
`docs/GOAL_CRITERIA.md` (B.1 to B.5): the paper's skeleton for a methods venue. The Methods are final where the
protocol is fixed (`docs/FEATURE_COMPARISON_PROTOCOL.md`, `docs/PLAN_H_COMPARISON.md`, `docs/PLAN_R_FRESH_TEST.md`);
the Results are a template. Every number comes from a file in this repository, named beside it; where a number does
not exist yet, a bracketed placeholder names the record that will hold it. Nothing of block H or the fresh test has
run. It supersedes `docs/archive/plans/PAPER_FRAMEWORK_PROPOSAL.md`. Working title: Agent-written features for a fixed
linear model: comparing autonomous research systems on unseen genetic perturbations.

## Abstract

Deep models for predicting the transcriptional response to a genetic perturbation do not yet beat simple linear
baselines (Ahlmann-Eltze, Huber and Anders, 2025). We ask a narrower question: with the model fixed to one ridge
regression, can autonomous agents find features that make it predict perturbations it has never seen, and which system
finds the better ones. In Gene-Mila a planner LLM proposes hypotheses, worker LLMs write one feature each as a Python
file, and a Python controller owns the clock, the spending, the fitting and the scoring. On the Adamson 2016 CRISPRi
screen we compare [N arms; `docs/PLAN_H_COMPARISON.md`, Arms]: this lab with four workers and with one, run in the lab
on one clean data bundle; Biomni's general biomedical agent and an autoresearch-style coding-agent loop, each given
the task exported from that bundle as a package in karpathy/autoresearch's style; a scripted no-LLM control; and four
features translated by hand from CellForge's design. The four LLM arms ran three 20-minute sessions each on one LLM,
the package arms under a $2.50 session cap and the lab arms under the lab's own per-run caps; the control is scripted
and free; the CellForge translation is one hand-written set. Every feature was then scored by one procedure, out of
fold on fold seeds no system used, against two matched permutation nulls with a family-wise correction: [mean ± sd per
arm; `docs/results/adamson_cf_h_compare/feature_compare.json`]. On a fresh test, a slice of the Replogle 2022 K562
CRISPRi screen held and scored once by a collaborator after the predictions' hashes were posted, [the arm that won,
its gain and paired SE; the holder's R2 report under `docs/results/`]. In an earlier block on Norman the agents built,
unprompted, a feature whose formula matches a published CRISPRa dependence, the additive prediction scaled by the
targets' promoter CpG content. Its development-tier gain was 0.00056 ± 0.00015 pearson_delta (mean ± adjusted paired
SE; `docs/results/norman_f_readings.md`), below the pre-registered minimum effect of 0.002, under a test later found
degenerate for that feature class; under the corrected test it fails the minimum effect and the perturbation
null, and the fitted signs were mixed.

## Introduction

Predicting how gene expression changes under a perturbation the model has not seen is the task of GEARS (Roohani,
Huang and Leskovec, 2024), of foundation models and of CellForge's agent-built models (Tang et al., 2025). A 2025
study in Nature Methods found that none of the deep models tested outperformed simple linear baselines (Ahlmann-Eltze,
Huber and Anders, 2025), and PerturBench found simple architectures competitive (Wu et al., 2024). If linear models
are hard to beat, the question is which inputs a linear model lacks. We fix the model and move the search to the
features: a feature maps a (perturbation, gene) pair to one or a few numbers from public knowledge and the training
screen, and one ridge regression over all pairs weighs the features. The question is whether an autonomous system can
find features that raise the fixed model's held-out score, and whether this lab's planner-and-workers design finds
better ones than a single coding agent in a loop, a general biomedical agent, or a scripted control, on the same task.
Gene-Mila is that lab. Agents write the code; Python fits, scores, keeps the deadline and the spending, and reads the
sealed set only after the run, through a capped and logged number of oracle queries (`README.md`, Methods, rule 5). On
the Adamson screen the agents' arms scored 0.566 to 0.602 sealed pearson_delta against 0.554 for a no-LLM control and
0.520 for the starting model, and nearly all the gain was one feature family, the transfer of measured responses
between related knockdowns (`README.md`, Results on Adamson; `docs/results/scaling.md`). Those numbers come from
sealed sets read many times and from arms run only in this lab. This paper makes the comparison fair in both respects:
the lab arms run on one clean bundle and the foreign systems on the task exported from it, with the same two feedback
tiers; every feature is scored by one tool; and the headline numbers come from a fresh cohort that no system and no
person on the project has scored before.

## Methods

### The task

Datasets. The Adamson et al. 2016 screen (CRISPRi in K562, the unfolded protein response) has 88 knockdowns; the
bundle keeps 2,055 genes, 2,000 highly variable genes plus every target, and CellForge's seed-42 split by perturbation
gives 50 training, 17 visible-validation and 21 sealed perturbations, `split_450515be1a0d8d2e` (`README.md`, Results
on Adamson; `docs/FEATURE_COMPARISON_PROTOCOL.md`, section 5; `docs/PLAN_H_COMPARISON.md`, Arms). The Norman et al.
2019 screen (CRISPRa, single genes and pairs) has 231 perturbations, 112 training, 63 visible and 56 sealed,
`split_a391fa9e7b4eccb7` (`docs/results/norman_manifest.json`). The prediction is the change of the per-perturbation
mean (counts per 10,000, log1p) from the control mean. The comparison block runs on Adamson only, from the clean
bundle `data/adamson_cf_clean_tables`, whose knowledge is tier 1 (Reactome, curated GO, CORUM, CollecTRI, STRING
physical links, per-gene tables from GENCODE and hg38, gnomAD and UniProt) and holds no perturbation screen
(`docs/PLAN_G_CLEAN_ARM.md`, Arms; `docs/PLAN_H_COMPARISON.md`).

Metric. The primary metric is pearson_delta: for each held-out perturbation, the Pearson correlation between predicted
and true change over all genes, averaged over perturbations (`genemila/benchmark/evaluator.py`). Beside it, M2 to M7
and M12 of the protocol, section 5; CellForge's and VCWorld's DE metrics need held-out cells.

The fixed model and the parent. One ridge regression over (perturbation, gene) rows, the penalty chosen on out-of-fold
scores of one fold seed and reported on another, over every ordered pair of the fold seeds 101, 102 and 103
(`tools/feature_compare.py`, docstring). Every arm starts from the same parent P0, the lab's built-in start:
`control_mean`, `mean_response` and `is_target`, plus `additive_response` only on a bundle with pairs
(`genemila/features/registry.py`, `BUILTIN_FEATURES` and `PAIR_BUILTIN_FEATURES`); Adamson has no pairs, so its parent
has no additive rule. The protocol allows a second parent P1, a strong known set (`--parent-run`); block H does not
score one (`docs/PLAN_H_COMPARISON.md`, Readings, item 1).

### The lab and the task package

A planner LLM reads a research state of at most 20,000 characters and proposes hypotheses as JSON. Worker LLMs each
write one feature plugin, a class with `compute(ctx, perts, params)` returning an array of shape (perturbations,
genes, dim) (`genemila/features/api.py`), seeing the API, one example and summaries of the data and knowledge files,
never the repository. `FeatureContext` is the only door to the data; the guard (`genemila/guard.py`) allows numeric
imports only, no file I/O, network, processes or reflection, and a smoke test checks that a training label swapped for
noise does not move the feature's rows. The controller schedules, fits, scores and stops everything at the wall clock,
keeps every completed experiment and calls the highest selection score the best (`genemila/db.py`, `best()`). After
the run a capped oracle scores the top `final.top_k` candidates and the best baseline on the sealed set, every query
logged (`README.md`, Methods, rules 1 to 6). In block H the lab runs with the DeepSeek planner `deepseek-v4-pro`,
`deepseek-flash` workers, 20 minutes, per-run caps of $1.00 for the workers and $1.50 for the planner, enforced by the
lab, and the shared ledger (`docs/PLAN_H_COMPARISON.md`, Arms).

`tools/export_task_package.py` writes the task as one folder: the public data every lab experiment receives, the
knowledge files, `features/` as the one editable surface, `evaluate.py` as the fixed evaluator, `literal.py` (caps on
literals, so labels cannot be pasted in), `MANIFEST.json` with the fold seeds, keep rule and parent features, and
`program.md` as the whole prompt (`tools/task_package/program.md`). `evaluate.py` keeps a change only when its gain
exceeds twice its standard error and 0.002, wins on more than half the perturbations and is positive under every fold
seed; a deletion is kept when it costs less than one plain standard error (`program.md`, The keep rule). The kept
state in `runs/kept/features/` is the arm's hand-back (protocol, section 2). The harness tier: the lab's controller
selects on the visible validation perturbations and the out-of-fold training perturbations together
(`genemila/lab.py`), so the package ships the visible labels as `harness/val1.npz`, `evaluate.py` decides on the
combined score, and `program.md` says the file is readable from the shell, that feature code cannot open it, and that
reads are scanned and recorded (`docs/ROADMAP.md` D5). The visible tier is then a seen tier for every arm, and the
fresh test the one tier whose labels no arm had. Andres may veto it (`docs/ROADMAP.md`, section 7, item 3).

### The other systems

Two kinds of arm share one bundle, one split, one clock and one final scoring. The lab arms (A1, A1-ablation, A2 and
C0) are `run_research.py` runs on `data/adamson_cf_clean_tables` under the lab's own caps, the key in the run's
process environment only. The package arms (A3 and A4) run on the package exported from that bundle, three sessions
each (seeds 0, 2 and 3), 20 minutes, through a proxy that adds the key, prices every call, writes the ledger and
refuses calls past a $2.50 session cap; the agents receive a dummy token and the proxy's address
(`tools/baselines/ledger_proxy.py`; `docs/PLAN_H_COMPARISON.md`, Arms, Money and The key). C2 is a hand-written set
with no session. Goal B.1's "identical task package" is read for the lab arms as the same public data, knowledge files
and two feedback tiers, which the package ships from the bundle.

- A1, this lab, four workers: block G's `runs/adamson_cf_g1_ds_w4_r{0,2,3}`, not re-run; A1-ablation, the same bundle without the three per-gene tables,
  `runs/adamson_cf_g0_ds_w4_r{0,2,3}` (`docs/PLAN_H_COMPARISON.md`, Arms).
- A2, this lab with one worker: `runs/adamson_cf_h_a2_ds_w1_r{0,2,3}`, settings of `docs/PLAN_B4_SINGLE_WORKER.md`.
- A3, an autoresearch-style loop: one coding agent with a shell inside a copy of the package, `program.md` as its prompt, editing one feature file and running `python
  evaluate.py` until the clock kills it. It runs through the Codex CLI, pointed at `deepseek-v4-pro` through the proxy's Responses-API route, web tools off; Claude Code is
  the disclosed fallback and `run.json["client"]` records which ran. The probe clears Codex for the arm only with two priced calls and no 400. Codex's 10-second shell
  timeout is disclosed per session; in account mode its sandbox is a second layer, in Docker mode the container is the isolation and Codex's own sandbox is off
  (`docs/PLAN_H_COMPARISON.md`, notes of 2026-10-17 03:52 and 04:32 UTC).
- A4, Biomni: its A1 agent (`source="OpenAI"`, `llm="deepseek-v4-pro"`, no data lake) given `program.md`. It has no budget cap and two of its code paths print the key, so
  it runs in isolation with a dummy key, the proxy as its only route and a runner that stops at the cap (protocol, section 2, A4). A session can end on `<solution>` before
  the clock, so the equal wall clock holds only approximately; `ended_by` is logged (`tools/baselines/run_biomni.py`). Two $0.05 probe sessions run first, one for Biomni
  and one for the selected A3 client. If `deepseek-v4-pro` rejects Biomni's consecutive assistant messages, one disclosed rerun with the proxy merging them follows; if that
  fails too, the arm is reported as "could not run on DeepSeek v4-pro" (`docs/PLAN_H_COMPARISON.md`, The probe; `docs/ROADMAP.md`, note of 01:10 UTC, D6).
- C0, the scripted no-LLM control: the lab with `--planner-provider scripted --worker-provider mock`, fixed hypothesis templates, free,
  `runs/adamson_cf_h_c0_scripted_w4_r{0,2,3}`. It is deterministic on this dataset and ends when its templates run out, after two to three minutes in the earlier runs, so
  its three runs bound timing noise only and it is a fixed-recipe reference, not an equal-time search (`docs/results/scaling.md`, Is the ordering real?).
- C2, CellForge's ideas translated by us: four plugins written by hand from CellForge's public code and model cards, gene-network propagation, pathway transfer, a latent
  perturbation offset and a pair-interaction term (`docs/comparison/cellforge_c2/README.md`); the pair term is constant on Adamson and is rejected there, so three are
  scoreable. Nothing in them is CellForge's output; the arm is spelled "CellForge ideas, translated by us".

Not comparable, and why. CellForge produces a deep model and a training script, not features; it ships no weights, one
run takes 4 to 8 GPU-hours, and by our reading of `graph_discussion.py` and `refinement.py`, not run and possibly not
the code behind the paper (UNVERIFIED), the plan that reaches code generation is built from fixed templates (protocol,
section 2, A5). Its published Table 1 rows cannot be reproduced under any metric definition tried
(`docs/results/calibration_adamson_cf_val2.md`; `README.md`, Results on Adamson). Its rows stay marked not comparable
(`docs/ROADMAP.md` D9). STATE (Adduri et al., 2025) is out: its public weights were trained on the Replogle K562
screen that the fresh test uses (D9). Isolation of the foreign arms: only the package folder is mounted and only the
proxy is reachable, in Docker or in a second macOS account checked by the proxy log and the transcript scan; without
either, the foreign arms wait (`docs/PLAN_H_COMPARISON.md`, Isolation).

### The fair test

`tools/feature_compare.py` scores every arm alike: one system row (parent plus all the arm's kept features) and one
add-one row per feature (parent plus that feature alone), with the same ridge, alpha grid, fold seeds and metrics, in
one call per bundle so every row shares one parent scoring (protocol, sections 4 and 6). Foreign code never runs in
the scoring process: each file passes the guard and the literal caps statically and is computed in child processes.
Every system selected on these training labels, so a development verdict screens candidates for the fresh test and
proves nothing; candidate lists are fixed with sha256 on #41 before the tool runs, and `--with-val1` stays off
(protocol, section 6; `docs/ROADMAP.md` D5). The pieces, fixed on 16 and 17 October 2026 after block F
(`docs/ROADMAP.md` D2):

- Two selection rules, one scoring. The lab keeps every completed experiment and picks the highest combined score; the package keeps a change only under the noise keep rule
  (protocol, section 8, item 5; `program.md`). The tool rescores every hand-back from its parent, so the difference does not reach the table.
- Two matched nulls. The gene null permutes the candidate across genes within bins of control expression and refits the whole procedure. A candidate that is, within every
  perturbation's row, a per-perturbation scalar times one parent column cannot fail that null, because the parent factor stays in the model; such a row is marked
  proportional (relative residual 1e-6) and also gets the perturbation null, in which the scalars are permuted across training perturbations within deciles of the targets'
  mean control expression with the parent columns left in place. It must pass both.
- Family-wise correction and deduplication. A max-gain step-down permutation test (Westfall and Young) over one source's add-one rows, the permutation of each replicate
  shared by every row, at B = 999 replicates (floor 0.001); a family with fewer reads "null too coarse", not failed. Rows of one source with an identical prediction hash
  (out-of-fold predictions rounded to 1e-9) collapse to one before the correction.
- The minimum effect. The mean gain must exceed max(2 SE_adj, 0.002), where SE_adj is the paired standard error widened by the perturbations' target-gene overlap
  (`tools/sealed_reading.py`) and 0.002 is the package's noise rule (`docs/ROADMAP.md` D3); wins on more than half the perturbations; a gain outside the targets; `mse_top`
  not significantly worse; every fold-seed report positive.
- The coefficient sign. The standardised add-one coefficient is saved per report, so the sign is read against the one pre-registered in `docs/PREREG_G_KNOWN_BIOLOGY.md`.

### The fresh test

Design and holder. Commit, then reveal, on the Replogle et al. 2022 K562 CRISPRi screens
(`ReplogleWeissman2022_K562_gwps.h5ad`, Zenodo 13350497, md5 `13db594f8f1d2ccb88fec44a13e414dc`; 1,989,578 cells by
8,248 genes; `docs/PLAN_R_FRESH_TEST.md`, section 1). Two slices: the replication slice R1 and the fresh slice R2. R1
is the essential-gene library, a separate smaller file whose availability is unverified at writing, and R2 is the
genome-wide file with every target eligible in R1 excluded; if only the genome-wide file is available, R1 and R2 are
two disjoint halves of its eligible targets drawn by the manifest tool with `--role both`, a weaker design because the
slices share one experiment, its batch structure and its controls (PLAN_R, section 2). [Which path was taken, and the
R1 file's sha256: PLAN_R, section 8; #41.] Adamson is K562 CRISPRi, so the Adamson arms are scored; Norman gets no
fresh test, since the two CRISPRa cohorts audited give four candidate genes and a same-gene dosage series, too few to
read the gain rule (`docs/EXTERNAL_COHORT_METADATA.md`). The holder, Andres's ML collaborator [handle: PLAN_R, section
8], obtains the file from the public record, never from the Mac, posts its sha256 on #41, keeps it and every score out
of every agent's reach, scores one deposit once and posts two dated reports, R1 then R2 (PLAN_R, sections 1 and 7).

Eligibility and the deposit. `tools/replogle_slice_manifest.py` reads only the file's obs and var tables through a
guard that refuses every other key. A target is eligible when it has at least 20 cells, names exactly one gene, is not
among the Adamson or Norman bundle targets and is inside the frozen gene universe. An in-distribution subset is
pre-registered from metadata alone: targets sharing a Reactome or CORUM class with a target of the Adamson bundle (its
whole target list; no split file is read); under 30 such targets in R2, re-checked after the R1 exclusion, the arm
criteria are reported as not powered. The draw uses a public seed named before the file is opened (PLAN_R, sections 2
and 3). [Eligible counts: the manifest's `manifest.md` and its sha256 on #41.] Every model predicts every eligible
target through `tools/frozen_model.py predict-targets` without refitting, after the adapter reproduced each arm's
saved predictions to 1e-6 (`docs/results/norman_frozen_export_20261013/report.md`: three B1 members exact). The batch
is, per arm, its three system models and at most three single features with a development verdict and the largest
out-of-fold gain, plus P0 (the built-in start; Adamson has no additive rule) and C0; only clean-bundle arms enter. The
deposit is one archive (manifest, `predictions.npz`, `receipt.json` and `queries.json` per model, the gene panel)
whose sha256 goes on #41 before the holder hears of it (PLAN_R, sections 4 to 6).

Reading rule. The holder computes per-perturbation means and the control mean with the ingest's normalisation and
scores with the evaluator's metrics unchanged. A feature is useful when its model beats its parent in pearson_delta by
more than twice the paired standard error with wins on more than half the in-distribution perturbations of R2, with
the pre-registered sign. An arm beats a baseline under `tools/arm_reading.py`'s rule: the mean gain G over the R runs
exceeds k·SE with SE = sqrt(S² + sd_g²/R), S the mean of the runs' paired standard errors and sd_g the spread of the
runs' gains, k = max(2, Student t at 0.975 on Welch-Satterthwaite degrees of freedom), every run's gain has G's sign,
and the favoured side wins on more than half the perturbation-run pairs. Every paired comparison in the batch enters
one Holm correction at 0.05. Then nobody refits, re-exports, adds a model or deposits again (PLAN_R, section 7).
Physical access, stated as the plan requires: the raw file has been on the Mac since 10 October 2026 at the latest,
and a knowledge file built from it, holding the Replogle responses of the bundles' own targets, which every slice
excludes, was in later development bundles. The test is held out by protocol and by the holder, not by physical
separation (PLAN_R, section 1).

### Costs, pre-registration, and what changed when

Every paid call lands in one shared SQLite ledger, priced from `configs/default.toml`. The ledger counts about twice
what DeepSeek bills: block F cost $2.82 on the ledger and $1.41 billed, inferred from the console's granted balance
before and after the block ($16.25 to $14.84), one block, so the ratio of 2.0 is a single measurement
(`docs/ROADMAP.md`, note of 2026-10-17 02:10 UTC). B2's three Norman runs cost $1.29, $1.37 and $1.19 and block F's
$1.29, $0.29 and $1.25 (`docs/results/norman_f_readings.md`, reading 4). Block H's cap is ledger + $15, expected $8 to
$13 (`docs/PLAN_H_COMPARISON.md`, Money). [Per-arm minutes, calls, tokens and cost: the proxy logs
`h_<arm>_r<S>.jsonl` and `summary.json["llm_usage"]`; the reading in `docs/results/block_h/`, the results index's
convention, with the tool output at `docs/results/adamson_cf_h_compare/`.]

Each block is a plan fixed before any run; from the first paid call a change is a dated note at the end, never an
edit. Three changes belong in the paper. (1) B2's seed 1 was killed by the watchdog while finishing and seed 3 took
its place, recorded before any B2 reading (`README.md`, Results on Norman). (2) Block F's two-stage reading rule was
amended at 04:20 UTC on 16 October and committed at 19:45 UTC, after the paid search had begun and before any reading
(`docs/results/norman_f_readings.md`, Provenance). Under it ten rows passed and A.1 was declared met at 22:05 UTC; at
23:40 UTC that reading was withdrawn, because the gene null cannot fail a feature that is a parent column times a
per-perturbation number (null sd 0.00001 against a gain of 0.00056;
`docs/results/norman_f_stage2/feature_compare.json`), and because with 20·m − 1 replicates the smallest pooled Holm p
equalled the 0.05 cutoff by construction (`docs/GOAL_CRITERIA.md`, Status). The corrected test is the one above; block
F was re-read under it on 17 October, after block G (the block F result below). (3) The harness tier and the Codex client were
added on 17 October, before any session (`docs/ROADMAP.md` D5; `docs/PLAN_H_COMPARISON.md`, note of 03:52 UTC). The
known biology of every family the per-gene tables allow was written down with its sign before any block G score was
read, in a file the pinned run code predates, written after block F's CpG feature was seen; it governs block G
(`docs/PREREG_G_KNOWN_BIOLOGY.md`, family 1, Already seen).

## Results (template)

### Table 1. The metrics table, one row per arm (columns from `docs/FEATURE_COMPARISON_PROTOCOL.md`, section 5)

Out-of-fold tier, parent P0, fold seeds 101 to 103, B = 999; mean ± sd over three sessions (for C0, three
near-identical runs); gains are candidate minus parent, sign flipped for MSE. Source for every cell:
`docs/results/adamson_cf_h_compare/feature_compare.json` [not yet run; `docs/PLAN_H_COMPARISON.md`, reading 1]. The
fresh-test columns (R2 in-distribution M1, Δ vs P0 ± paired SE, wins, Holm p; the out-of-distribution subset beside
them) come from [the holder's R2 report, posted on #41 and copied unedited under `docs/results/`]. A session that
handed back no kept feature is a row with the parent's score, not a dropped row.

| arm | n sessions | OOF M1 | ΔM1 ± SE_adj vs P0 | wins | ΔM2 | ΔM3 | ΔM4 | ΔM5 | ΔM7 | M12 | features kept | with a verdict | minutes, calls, tokens, $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 lab, 4 workers (G1) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [`summary.json["llm_usage"]`] |
| A1-ablation, no tables (G0) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| A2 lab, 1 worker | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| A3 autoresearch-style (Codex) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [proxy log] |
| A4 Biomni | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [proxy log] |
| C0 scripted control (deterministic) | 3 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | $0 |
| C2 CellForge ideas, translated by us | 1 set | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | 4 written, 3 scoreable (`cellforge_c2/README.md`) | [ ] | $0 |
| P0, the built-in start (no additive rule on Adamson) | reference | [ ] | | | | | | | | | 0 | | $0 |
| CellForge-Models, as reported, other split | not comparable | | | | | | | | | | | | |

### Table 2. Found features, per arm, under the fair test

One row per add-one row with a development verdict, after deduplication; source `feature_compare.json` above, then the
holder's R2 report.

| arm | feature | knowledge it reads | proportional to | ΔM1 ± SE_adj (OOF) | p_fwer gene | p_fwer pert | coefficient sign | pre-registered family and verdict | R2 gain ± SE, wins, Holm p |
|---|---|---|---|---|---|---|---|---|---|
| [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [`docs/PREREG_G_KNOWN_BIOLOGY.md`] | [ ] |

### Figures

- Figure 1. The design: lab arms on the clean bundle, the package exported from it to the foreign arms, one scoring tool, one deposit, one holder. [`docs/assets/loop.svg`;
  PLAN_H; PLAN_R.]
- Figure 2. Per arm, each session's out-of-fold M1 against its parent, with the arm mean; the fresh-test M1 beside it. [`feature_compare.json`; the R2 report.]
- Figure 3. Every add-one gain against its nulls, proportional rows marked, with the step-down threshold; cost and throughput per arm beside it. [`feature_compare.json`;
  proxy logs; `results.tsv`.]

### The one existing result: block F on Norman

Three Norman runs from B2's start with a per-gene table built from GENCODE and hg38 added to the bundle and no
hypothesis given wrote 94 plugins, 66 of them scoreable as add-one rows (`docs/results/norman_f_readings.md`). The
bundle still held the Replogle 2022 screen, so block F is not a clean arm and six of its ten passing rows read that
screen; the CpG feature itself reads only the annotation table (`norman_f_readings.md`, Provenance;
`docs/GOAL_CRITERIA.md`, note of 22:05 UTC). Runs r0 and r3 each built the feature, the additive prediction scaled by
the targets' mean promoter CpG observed/expected ratio; r0 built two variants of one formula with identical
predictions, so the three rows are formula variants, not independent replications. Its gain is +0.00056 ± 0.00015
pearson_delta (adjusted SE), wins 69 of 112, below the minimum effect of 0.002 of the corrected test, so no verdict
under that test; a TSS-distance scaler gained +0.0014 ± 0.0005 (`norman_f_readings.md`, Primary feature reading). It
restates published biology: CRISPRa raises highly expressed genes least (Konermann et al., 2015; Chavez et al., 2016;
Wu et al., 2023), and CpG-island promoters mark that class (Deaton and Bird, 2011). Its coefficients in the runs' own
models were +0.0147, +0.0143 and −0.0100, so no sign is stated (`docs/results/norman_f_coefficient_signs.md`). The
table did not raise the arm's score: selected models 0.7196 ± 0.0012 sealed (`norman_f_readings.md`, reading 2)
against B2's 0.722, 0.720 and 0.730 (`docs/results/norman_b2_r{0,2,3}_sealed_reading.json`; arm mean 0.7239 ± 0.0054,
`docs/results/norman_b2_arm_vs_additive.md`), and out of fold 0.5805 ± 0.0023 against 0.5825 ± 0.0081
(`norman_f_readings.md`, reading 3). Two lessons carry into the Methods: a null must match the feature's structure (a
random projection passed beside the CpG term), and a permutation floor at the cutoff is not a p-value. Block F re-read under the corrected test (17 October; `docs/results/norman_f_corrected_stage2/feature_compare.json`
and `docs/results/norman_f_corrected_pooled_holm/pooled_holm.json`, PR #63): of the 66 scoreable rows 59 were tested and
53 are unique predictions; six pass every gate (pooled family-wise p 0.001, the floor; gains 0.0026 to 0.0047
pearson_delta at 2.05 to 2.69 adjusted SEs; wins 60 to 64 of 112; coefficient positive in every fold-seed report), and
every one of the six multiplies the sign-flipped Replogle 2022 K562 CRISPRi response of the perturbation's targets by a
per-gene annotation quantity (promoter CpG observed/expected in four, promoter GC in one, transcript length in one): one
theme, from runs r0 (one row) and r3 (five). Replogle 2022 is a tier-3 source, so none is tier 1; the annotation
factor's own contribution is unmeasured, since the family has no screen-only row. Of the 38 screen-free unique rows none
passes: the CpG feature gains 0.00056 ± 0.00015, below the 0.002 minimum, and fails the perturbation null the first test
lacked (pooled p 0.363); the random projection that passed beside it then has pooled p 1.0 now; the step-down over the
38 screen-free rows alone changes nothing. What the six passes show is that the test is not blind: a source known to
carry the answer passes, while the class the first test could not fail now fails.

### The second existing result: block G, the clean arm with and without the three per-gene tables

Twelve twenty-minute runs on 17 October 2026 (DeepSeek v4-pro planner, four deepseek-flash workers, code `baa7dfd`,
$12.97 on the ledger): on each dataset three seeds with the clean tier-1 knowledge plus the genome, gnomAD constraint
and UniProt tables (G1) and three without them (G0), the knowledge rebuilt from Reactome, GO, CORUM, CollecTRI and
STRING with no perturbation screen (`docs/PLAN_G_CLEAN_ARM.md`). The G1 agents wrote 395 scoreable features that read
a table, 221 on Adamson and 174 on Norman, and the pre-registered list of what the tables could encode was written
before any score (`docs/PREREG_G_KNOWN_BIOLOGY.md`). Under the corrected fair test (the gene null for every row, the
perturbation null for the rows proportional to a parent column), 999 replicates and the
family-wise correction, none passes on either dataset (Adamson 210 unique predictions, Norman 158; the operator's
readings on #51, comments 6233130270 and 6236179594, files `adamson_cf_g_pooled_holm` and `norman_g_pooled_holm` on
the results PR). The tables did not raise the arm: out of fold, Adamson G1 0.491 ± 0.004 against G0 0.526 ± 0.035 and
Norman G1 0.579 ± 0.008 against G0 0.578 ± 0.001 (mean ± sd over seeds 0, 2, 3; `adamson_cf_g1_vs_g0`,
`norman_g1_vs_g0`); on the worn sealed sets, indicative only, Adamson G0 0.566 ± 0.036 and G1 0.491 ± 0.069, Norman
G0 0.719 ± 0.001 and G1 0.720 ± 0.007 (`*_sealed_summary`). The G1 agents did read the tables (the direct-call audit,
`*_direct_table_audit`), so the negative is not for want of use. Two readings carry into the Results: a result about
what these agents find in this setting, with the per-gene tables adding nothing that survives a matched null; and the
two G arms are the lab's rows of Table 1 (A1 and A1-ablation on Adamson), not re-run for block H. With block F this
closes the agents' biology path for this window (`docs/ROADMAP.md`, note of 16:50 UTC).

## Discussion

Claims this design can support. (1) Whether a fixed linear model gains from agent-built features at all, out of fold
and on a fresh cohort, with the gain's size and paired uncertainty. (2) Which system, lab arms on the bundle and
foreign arms on the package exported from it, supplies the better features under the arm rule, and what each cost. (3)
That the agents built, unprompted, a feature that restates known biology, whose development-tier gain is below the
minimum effect; the pre-registered list was written after block F and governs block G; a mechanism claim needs its
sign rule and the fresh test. (4) That the fair test as first built passed a feature it could not fail, and what a
matched test needs. (5) That CellForge's published rows are not comparable on this data, with the reasons.

Claims it cannot support. No biology discovery claim: a feature that passes the fair test and the fresh test is a
predictive feature, and a new rule only with a named mechanism, a predicted sign, a replication and a wet-lab test
(`docs/GOAL_CRITERIA.md`, A.2 to A.6); every family the per-gene tables allow has a known rule behind it except three
OPEN families, of which one, constraint residualised on expression and essentiality, has power
(`docs/PREREG_G_KNOWN_BIOLOGY.md`, families 4, 5 and 8). No claim that the fresh test is physically sealed: the raw
file was on the Mac, so the test is held out by protocol and by the holder. No claim of a difference inside run-to-run
noise: three sessions per LLM arm, a coding agent has no seed, and the control's spread is timing noise, not search
noise. No claim from the sealed sets: both have been scored many times. No claim about Biomni's or CellForge's
performance on their own tasks: here each is one more agent writing feature files on our package, and CellForge enters
only through our translation of its ideas.

Limitations. One cell line and modality for the fresh test; one dataset for the comparison block; 20-minute sessions;
one LLM, `deepseek-v4-pro`, unless the probe forces the disclosed `deepseek-flash` fallback for A3; the lab's own
package and keep rule shape every foreign arm; the paste check rests on the guard, the literal caps and a transcript
scan; the client and isolation differences are disclosed, not removed; the ledger is a priced estimate; the fresh test
is one scoring with no second look. What would strengthen it: more sessions per arm; a second fresh cohort in another
cell line; a control hiding gene identities, to separate recalled biology from the screen; the wet-lab test of
`docs/ROADMAP.md` D13 for any feature that survives. Norman package arms and CellForge's own model on a GPU are
dropped for this window (`docs/ROADMAP.md`, section 9).

Data and code. The code is this repository; the screens come from Zenodo record 13350497, the Replogle file obtained
by the holder independently; knowledge receipts are in `docs/PLAN_G_CLEAN_ARM.md` and `docs/mac/block_g/`. Committed:
every plan, every dated result under `docs/results/`, the run records under `docs/mac/`, the C2 plugins, the frozen B1
export, and [the block H hand-backs, proxy logs and `feature_compare` outputs; the fresh-test manifest, deposit hashes
and the holder's reports]. Data bundles, run directories and the ledger stay on Andres's Mac, excluded from Git.

## References

Cited as `docs/CANDIDATE_LITERATURE_CHECK.md` lists them (year, journal, DOI; no volumes or pages, which that file
does not hold and its VERIFIED mark does not cover). VERIFIED: an abstract or page was fetched there; UNVERIFIED: a
search summary only, or not in that file.

- Ahlmann-Eltze, Huber, Anders. Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines. Nature Methods, 2025, doi
  10.1038/s41592-025-02772-6. VERIFIED.
- Roohani, Huang, Leskovec. Predicting transcriptional outcomes of novel multigene perturbations with GEARS. Nature Biotechnology, 2024, doi 10.1038/s41587-023-01905-6.
  VERIFIED.
- Wu, Wershof, Schmon, et al. PerturBench: benchmarking machine learning models for cellular perturbation analysis. arXiv 2408.10609, 2024. VERIFIED.
- Tang, Chen, Shao, et al. AI scientists for building virtual-cell models (CellForge). arXiv 2508.02276, 2025 (v3 2026-10-14 retitled). VERIFIED.
- Adduri, Gautam, Bevilacqua, et al. Predicting cellular responses to perturbation across diverse contexts with STATE. bioRxiv 10.1101/2025.06.26.661135, 2025. VERIFIED.
- Huang, Zhang, Wang, et al. Biomni: a general-purpose biomedical AI agent. bioRxiv 10.1101/2025.05.30.656746, 2025. VERIFIED.
- Karpathy. autoresearch, github.com/karpathy/autoresearch, 2026. VERIFIED (README fetched); a code repository, not a paper.
- Adamson, Norman, Jost, et al. A multiplexed single-cell CRISPR screening platform enables systematic dissection of the unfolded protein response. Cell, 2016, doi
  10.1016/j.cell.2016.11.048. VERIFIED.
- Norman, Horlbeck, Replogle, et al. Exploring genetic interaction manifolds constructed from rich single-cell phenotypes. Science, 2019, doi 10.1126/science.aax4438.
  VERIFIED.
- Replogle, Saunders, Pogson, et al. Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Cell 185(14):2559, 2022, doi
  10.1016/j.cell.2022.05.013. VERIFIED.
- Konermann, Brigham, Trevino, et al. Genome-scale transcriptional activation by an engineered CRISPR-Cas9 complex. Nature, 2015. VERIFIED (abstract); the
  inverse-basal-expression dependence is figure-level, UNVERIFIED.
- Chavez, Tuttle, Pruitt, et al. Comparison of Cas9 activators in multiple species. Nature Methods, 2016. VERIFIED (abstract); the locus variability is full-text level,
  UNVERIFIED.
- Wu, Wu, Karim, et al. Massively parallel characterization of CRISPR activator efficacy in human induced pluripotent stem cells and neurons. Molecular Cell 83(7), 2023,
  doi 10.1016/j.molcel.2023.02.011. VERIFIED.
- Deaton, Bird. CpG islands and the regulation of transcription. Genes & Development, 2011, doi 10.1101/gad.2037511. VERIFIED.
- Westfall, Young. Resampling-based multiple testing (Wiley, 1993). UNVERIFIED: not in the literature check; the method the step-down follows.
- VCWorld, ICLR 2026 (the DE and direction metrics). UNVERIFIED: cited from `README.md`, not in the literature check.
