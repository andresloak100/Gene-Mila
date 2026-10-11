# The paid block after N4: what runs, in what order, and how it is read

Written 2026-10-11 between 19:15 and 19:45 UTC by the lab-code owner ("Autonomous research system" session), before
any run below has a result and before the fresh Adamson bundle is built. One run had already started: B1's first
repeat, at 19:16:54 UTC (B1 says how it was set up). Every number these runs produce is read by the rules here, and
nothing below changes once this file is committed; a change is a new, dated section, never an edit.

## Why these runs

After N4 the open questions are about evidence, not search. Every paid Norman arm so far is one run, so no Norman
claim has a spread (AGENTS.md: each arm is reported as mean ± sd over its repeats). Adamson's sealed set has been
scored for dozens of finalists across about 30 runs, so the best Adamson number (0.646) is not established. More
agent hours on the same data have not moved the numbers (Adamson: 4 workers beat 8 and 16, longer runs flat; Norman:
N4 added +0.008 ± 0.004 over its start). So the block buys repeats, whose selected models are averaged into one
combined model per arm (the improvement it aims at, below), and one re-split of Adamson that asks again whether the
agents add anything to the no-LLM recipe, about $11 by the ledger, then reports.

## Money

Andres in the build thread, 2026-10-11 UTC: "you can spent as much as u want and you think is necessary we have in
total 33 in deep seek" (19:10); "its what we have" (19:16, with a screenshot of the DeepSeek console: balance $33.01,
DeepSeek's own total cost $16.98 over the last 30 days); "keep improving the model spent those dolars well" (19:16);
"use the same key" (19:17); "I've configured my API key in ~/.zshenv as the environment variable API_KEY" (19:22).
So $33.01 is what is left in the account and the aim is a better model as well as evidence. B1's first repeat runs on
the key he pasted in the thread at 17:48; every later run takes the key from API_KEY in his ~/.zshenv and gets it as
DEEPSEEK_API_KEY in its own process environment only (`DEEPSEEK_API_KEY="$API_KEY" <command>`), never on a command
line, in a file or in a log. The shared ledger read $33.97 after N4 against DeepSeek's billed
$16.98: the ledger prices every call at the configured rates, and DeepSeek bills off-peak hours (weekends among
them) at lower rates, which likely explains most of the gap (inferred, not checked call by call). The ledger is never
repriced (AGENTS.md); its higher figure is what the caps below count, so they hold with margin.

- This block's cap: the shared ledger may reach **$48.00** (about $7 of real money above today's bill at the observed
  ratio). Every paid run passes `--set budget.cumulative_usd.deepseek=48`, and starts only when the ledger plus its
  own two caps stays at or below $48, so the cumulative cap can never bind part-way through a run: it did in N4, whose
  planner stopped at 18.7 of 20 minutes when the ledger reached the $34 cap then in force (its summary.json:
  `planner.exhausted_at_min` 18.7, `mixed` true).
- B1's repeats keep r1's caps, so the three are the same run but for the seed: `--set budget.max_total_usd=1.3` and
  the planner cap left at its default ($5.33); they start only at a ledger of **$41.37** or less. B2's and B3's
  runs: `--set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5` (N3, N4 and r1 spent $0.36, $0.48 and $0.61
  on workers and $0.67, $0.68 and $0.82 on the planner, N4's cut short at 18.7 minutes, so neither cap is expected to
  bind); they start only at a ledger of **$45.50** or less. Every paid run also passes `--set budget.ledger=<absolute path to the shared ledger>`,
  `--planner-provider deepseek --planner-model deepseek-v4-pro`, and runs its workers on deepseek-flash as N3 and N4.
- One run at a time, in the order below. A run that fails, is killed, costs more than $2.00, or ends with a planner
  that changed or ran out (summary.json `planner.mixed` true) stops the block until the cause is written up; such a
  run is its own arm (AGENTS.md) and is reported beside its arm, never in it.
- After this block the results go to Andres with the next block proposed; the remaining balance is spent in blocks
  like this one, each pre-specified here before it starts.

## B1. Three repeats of N4 (Norman, about $4.30)

N4 (runs/norman_ds_from_n2_w4_r0, seed 0) repeated on its own code, **076282c**: the DeepSeek agents continuing the
no-LLM control N2, with `--set run.seed=1`, `2` and `3` (the seed sets the cross-validation folds; the LLM calls vary
on their own), run directories `runs/norman_ds_from_n2_w4_r1`, `_r2` and `_r3`, plus the budget settings above. Run
from a checkout or worktree at 076282c, with the starting run, the run directory, the bundle and the shared ledger
given by absolute path, as in the command below.

N4 itself is not in the arm. Its planner ran out at 18.7 of its 20 minutes, when the shared ledger reached the cap
then in force, so by AGENTS.md it is its own arm, "deepseek:deepseek-v4-pro planner (lost its planner)", reported
beside the repeats and never pooled with them. Its result (+0.008 over its start) is also what prompted these
repeats, which would bias any arm that counted it. The arm is r1, r2 and r3, three runs that differ only in the seed.

Readings, each with `tools/sealed_reading.py` per run as for N4 (selected against the additive baseline and against
its starting model) and `tools/arm_reading.py` over runs:
- **Primary: the arm over r1, r2 and r3 against their starting model, pooled.** Each run re-fits N2's selected
  model as its first experiment under its own seed, so each run's reference is its own re-fitted start; whether its
  alpha equals N2's EXP_0198 is reported beside.
- Secondary: the arm against the additive baseline; N4's two readings beside the arm, as its own arm.

How r1 was started: the Mac session started it at 19:16:54 UTC on Andres's messages of 19:10 and 19:16, before this
file existed, from the main checkout at 076282c with `--set run.seed=1`, `budget.max_total_usd=1.3`,
`budget.cumulative_usd.deepseek=40` and the planner cap left to its default (4.0 x 4 workers x 1/3 hour = $5.33); the
shared ledger read $33.969876 at its start. Its reading was written in the Mac's STATE.md at 19:20 UTC, before any
result: seeds 1 and 2 are replicates of N4, nothing is dropped, nothing replaces N4, each is read with
tools/sealed_reading.py and the three paired differences are reported side by side with their mean and range. This
file keeps the per-run readings and the side-by-side report, adds the arm rule and the combined model, and, after
the review of this file found N4's planner record (above), leaves N4 out of the arm. r2 and r3 run from the worktree
`~/Documents/Mila/Gene-Mila/gene-mila-076282c` (also at 076282c) with r1's caps, and every stop rule above applies to
r1 as well. The command, with the key taken from API_KEY as above:

    cd ~/Documents/Mila/Gene-Mila/gene-mila-076282c && DEEPSEEK_API_KEY="$API_KEY" \
      ~/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python run_research.py --minutes 20 --workers 4 \
      --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro \
      --continue-from <MAIN>/runs/norman_control_replogle_w4_r0 --run-dir <MAIN>/runs/norman_ds_from_n2_w4_r<SEED> \
      --set run.seed=<SEED> --set run.data_dir=<MAIN>/data/norman --set budget.ledger=<MAIN>/runs/spend_ledger.sqlite \
      --set budget.cumulative_usd.deepseek=48 --set budget.max_total_usd=1.3

with `<MAIN>` the absolute path of the main checkout and `<SEED>` 2, then 3. r1 ended cleanly before this file was
committed: 1,203.6 s, exit 0, no budget, breaker or error events, $1.436 (workers $0.614 over 521 calls, planner
$0.822 over 62 rounds), ledger $33.970 to $35.406. As agreed before it ended, nobody opened its sealed scores or ran
its reading before this file was on GitHub.

The seed also sets the cross-validation folds, so visible scores differ between seeds for the same model (N4's start
EXP_0007 scores 0.6423 visible with seed 0 and 0.6525 with seed 1). Visible scores that include out-of-fold
perturbations are therefore compared only within a run; across runs, only scores on the visible validation
perturbations (the same perturbations and labels for every run) and the sealed readings are compared.

## B2. Three fresh Norman runs that start from the additive rule (about $4.30)

Code: the lab branch head when B2's control starts, which holds this file and the reading tools it names
(recorded in each run's summary.json as base_commit; all of B2 and B3 run on that one commit). The DeepSeek agents start fresh (no
`--continue-from`), Replogle file in the bundle as in N3, 4 workers, 20 minutes, seeds 0, 1 and 2, run directories
`runs/norman_ds_addstart_w4_r0` to `_r2`. On this code their starting model is `baseline_ridge_additive`, ridge on
the three built-ins plus `additive_response` (docs/NORMAN_PLAN.md section 8, "Changes after N4"). Before them, free:
one no-LLM control on the same code, `runs/norman_control_addstart_w4_r0` (scripted planner, mock workers,
deterministic), so the new start's score and the scripted recipe on the new code are on record.

Readings:
- **Primary: the arm over the three runs against `baseline_ridge_additive`, pooled.**
- Secondary: per run, selected against its start and against the additive baseline; the arm against the additive
  baseline; each run's selected model against the control's (`--versus`).
N3 (one run, built-in start, code 5fe6e76) is set beside them descriptively only: it is another code version and one
run.

## B3. Adamson re-split (one free run, then about $2.40)

What this is and is not: every Adamson perturbation's labels, or its sealed scores, were used while the lab and its
recipe were developed (the 50 training and 17 visible ones by every run, the 21 sealed ones through about 30 runs'
sealed scorings, the hand-written transfer control among them). A new split therefore gives no clean Adamson number.
What it can still answer is a contrast: whether the DeepSeek agents add anything to the no-LLM recipe with the
Replogle screen when the held-out genes are different ones, since both arms share the recipe. Only that contrast is
read; the arm's absolute scores are reported as a re-split of a dataset used in development, never as a clean result
and never pooled with the adamson_cf rows. The clean held-out tests left are Norman, within its limits, and Srivatsan.
B3 runs last, so if anything in B1 or B2 stops the block, B3 is what is dropped.

The bundle `data/adamson_fresh`: the same ingest as `data/adamson_cf` (its manifest records the options; the same
file AdamsonWeissman2016_GSM2406681_10X010.h5ad, the same gene selection and cell-sample seed), except the split:
`--split-mode gene --gene-frac 0.57 0.19 0.24 --seed 20261011` instead of CellForge's split file, with
`--sample-seed 0` so only the split changes: adamson_cf's manifest predates the sample-seed field, and the Mac's logs
show it was built with the default seed 0, which then also seeded the cell samples. Expected: 50 training, 17 visible
and 21 sealed perturbations (make_gene_splits rounds 88 genes to these counts), a new split_id, 2,055 genes as
before. Checks, all printed and logged: the three counts, a split_id other than adamson_cf's, and the gene list
and the control cells in public.npz and knowledge/targets.json identical to adamson_cf's (so the same genes, the same
control cells and the same targets; nobody reads either bundle's splits.json or private files to compare the two
splits). The Replogle builder reads only the raw screen, the bundle's gene list and targets.json, so with those
identical its output is the same but for the build date and duration it records (source.date, source.seconds).
adamson_cf's Replogle file is therefore copied into adamson_fresh/knowledge/ after these checks pass, and the copy's
md5 is checked against the original's. If a check fails, nothing runs and the failure is reported.

Runs, in order: F0, the no-LLM control with the screen (scripted planner, mock workers, seed 0, free),
`runs/adamsonfresh_control_replogle_w4_r0`; then F1, the DeepSeek agents with the screen, fresh start, 4 workers,
20 minutes, seeds 0 and 1, `runs/adamsonfresh_ds_replogle_w4_r0` and `_r1`. Same code as B2.

Readings:
- **Primary: the arm over F1's two runs against F0's selected model (`tools/sealed_reading.py --versus`), pooled.**
  With two runs the arm reading is weak (below); a null is the likely outcome unless the agents' gain is large.
- Secondary: per run, selected against its own reported start (its best baseline) and against F0's.

## The combined model of an arm (the improvement this block aims at, fixed now)

Each run's search lands on a different model, and the spread between runs is as large as the gains (Adamson's
repeats; N4's +0.008). The average of independently searched models is a standard way to turn that spread into
accuracy. So each paid arm's deliverable model is its **combined model**: the plain average of the predicted changes
of its runs' selected models (each run's summary.json "best", chosen on visible data only; equal weights, no
selection among runs). For B1 the members are r1, r2 and r3; for B2 the three addstart runs; for B3 F1's two runs.

Which model this block delivers is fixed now, from visible data only: for Norman, B1's combined model, unless B2's
combined model scores higher on pooled pearson_delta over the visible validation perturbations (the same
perturbations for every model; out-of-fold scores are left out of this choice because the seeds draw different
folds). No sealed reading below chooses a model; they are evaluations of the model chosen this way.

Evaluations (`tools/arm_reading.py combine`; one paired sealed query per comparison, on an oracle of the tool's own),
all secondary, read by the per-run rule (a gain above twice its paired SE, better on more than half of the sealed
perturbations):
- B1: the combined model against N2's selected model (runs/norman_control_replogle_w4_r0, EXP_0198, the start every
  B1 run continued, sealed 0.719) and against the additive baseline. N4's selected model (sealed 0.726) is set beside
  them as its own arm, not compared.
- B2: the combined model against `baseline_ridge_additive`, against the control's selected model
  (norman_control_addstart_w4_r0), against the additive baseline, and against the B1 combined model. The last asks
  whether the fresh start is better or worse than continuing N2; a null there does not mean the two are as good as
  each other.
- B3: the combined model against F0's selected model.
The combined model's visible comparison (the visible validation perturbations, and out of fold the training ones,
each member's stored predictions averaged) is reported beside each, not read. Expected direction: none.

## The arm reading (fixed now)

For an arm of R runs and one reference (the starting model, the additive baseline, or another run's selected
model), each run r gives a pooled sealed paired difference g_r (selected minus reference) with paired standard
error s_r from its own reading, over n sealed perturbations. A run that selected its reference enters with g_r = 0
and s_r = 0. A run whose planner changed during the run is its own arm (AGENTS.md): it is reported separately, and
the arm is read over the remaining runs, with R stated; with fewer than two left, the arm is not read.

- G = mean of g_r. S = mean of s_r bounds the perturbation-sampling part of G's standard error whatever the
  correlation between runs (the standard error of an average is at most the average of the standard errors);
  sd_g = the standard deviation of the g_r (ddof 1) is the run-to-run part. The arm's standard error is
  SE = sqrt(S² + sd_g² / R).
- **The gain counts when G exceeds k·SE, every g_r has G's sign, and, summed over the runs, the side G favours wins
  on more than half of the perturbation-run pairs.** k = max(2, t at 0.975 with ν degrees of freedom), ν from
  Welch–Satterthwaite: ν = SE⁴ / (S⁴/(n−1) + (sd_g²/R)²/(R−1)). With R = 2 or 3 the run-to-run part has one or two
  degrees of freedom, so when the runs disagree k grows quickly towards 12.7 (R = 2) or 4.3 (R = 3).
- Norman's sealed perturbations are not independent: pairs share genes. For each run's comparison the ratio of a
  leave-one-gene-out jackknife standard error to the plain paired standard error is estimated on the visible
  validation perturbations of the same two models (visible labels only); when it exceeds 1, s_r is multiplied by it
  in the arm reading. The per-run readings keep the plain rule, as N4's was read, with the ratio reported beside.
- Per-category arm readings follow the same rule in every category with at least 10 sealed perturbations in each
  run, as secondary readings. The same is computed on the visible and out-of-fold perturbations and reported, not
  read. Each arm is also reported as mean ± sd over its runs of the selected model's sealed pearson_delta, MSE_DE,
  PCC_DE and R²_DE. The arm reading uses only the runs' own readings: it scores nothing on the sealed set.

One primary reading per block, named above; every other verdict is secondary and descriptive, and a summary leads
with the primary ones. Expected directions, fixed now: none for any comparison. A null is a result and is reported as
one.

## What happens after

Results go into docs/NORMAN_PLAN.md section 8 (B1, B2), docs/LAB_STATE.md and HANDOFF.md section 1, with every run
directory, cost and md5, and to Andres in the build thread before anything more is spent. After this block Norman's
sealed set has been scored for many models and used to decide what to run next, as Adamson's was: from then on,
statements on it that compare arms ("the best Norman model") are descriptive, and the design of later blocks goes by
visible results only.
