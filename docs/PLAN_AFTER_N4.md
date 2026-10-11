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

## Amendment, 2026-10-11 20:30 UTC: the gene-clustering ratio, and what the arm tools check

This section changes the plan above; nothing above is edited.

**The ratio.** The leave-one-gene-out jackknife ratio of "The arm reading" is biased upwards. A pair perturbation
belongs to two gene groups, so the jackknife deletes it twice; with m perturbations and no gene shared between any
two of them it gives sqrt((2m−1)/(m−1)), about 1.41, where the true ratio is 1. It would have widened every Norman
run's s_r by up to 41% for clustering that is not there. It is replaced by the overlap-robust ratio, still on the
visible validation perturbations of the same two models and visible labels only: with e the per-perturbation
pearson_delta differences less their mean,

ratio = sqrt(max(0, Σ e_p·e_q over every ordered pair p, q whose target genes overlap, p = q included) / Σ e_p²),

the overlap-robust variance of the mean difference over the plain one. It is exactly 1 when no two perturbations
share a gene, and s_r is still multiplied by it only when it exceeds 1. The jackknife ratio is kept in every reading
as `jackknife_ratio`, and each arm report adds a row with the arm rule under it, marked reported, not read; the
overlap-robust row is the primary one.

**Timing, disclosed.** The bias was found by a review of the tools that started at about 19:48 UTC, before any B1
result was read. The first repeat's sealed reading (r1, with the old ratio) was seen at about 20:10 UTC, before this
amendment was written. Where genes are not shared the new ratio is 1 and the old one about 1.41, so in the main the
change makes a gain easier to count; r1's reading shows no gain under either (against its start +0.0004 ± 0.0011,
better on 27 of its 56 sealed perturbations and worse on 29). Every B1 run, r1 included, is read again with the
amended tools; the arm tool refuses a reading made before this amendment.

**What the tools now check (no change to the rule).**
- The arm's mean ± sd of the selected models' sealed pearson_delta, MSE_DE, PCC_DE and R²_DE comes from each selected
  model's own end-of-run sealed scoring, stored in its run (the paired query returns no comparable DE metrics). It is
  no new look at the sealed set. A run that kept its reference counts in this mean ± sd.
- The runs of one arm must share dataset, split, bundle, selection rule, external knowledge and the kind of start;
  a `--versus` arm has one reference model that is never itself a member.
- A run with no summary.json or no planner record is left out like a run whose planner changed, and named; `combine`
  refuses both as members.

## Note, 2026-10-11 21:35 UTC: how B2 is run (operations only; no reading changes)

B1 ended cleanly and is read (docs/NORMAN_PLAN.md section 8; PR #6). Andres wrote "continue" at 20:56 UTC, and B2
runs as specified above, unattended, from scripts in `docs/mac/block_after_n4/` reviewed before use:
`block_b2_chain.sh` starts `block_b2_control.sh` (the free control) and then `block_b2_run.sh 0`, `1` and `2`, each
only after the step before passed its checks. The scripts enforce this plan's money rules (the $45.50 ledger gate, the
caps, one run at a time, the stop rule after every run) and add operational checks that only ever stop the block,
never change a reading: the control pins the commit (the lab branch head when it starts) and every later B2 and B3
run refuses another; each step leaves a pass marker the next step requires; a stopped script, a STOP file or the
scaling driver halts the chain; and the control stops the block if its best modelled baseline is not
`baseline_ridge_additive`, the start B2 is about. The best baseline overall (which the exploit engine refines, and
which can be the analytic additive rule) is recorded beside each run's start. B2's readings and B3 follow as above;
HANDOFF.md section 1 holds the exact commands.

## Note, 2026-10-11 22:50 UTC: B2's second run was killed while finishing, and how B2 continues

This section changes the plan above; nothing above is edited. It is written before any B2 run's sealed reading.

**What stopped the block.** The free control and seed 0 passed (`runs/norman_ds_addstart_w4_r0`: $1.293 by the
ledger, selected EXP_0724, 24 features). Seed 1, `runs/norman_ds_addstart_w4_r1`, ran its full 20-minute search with
its planner unchanged and cost $1.649 by the ledger (workers $0.773, planner $0.877; the ledger read $41.03 after it).
While it was finishing, after the search and the 30-second grace (the end-of-run scoring, the ensemble and cell-eval),
run_research.py's watchdog killed it, at about 22:37 UTC. The watchdog allows 20 minutes + `run.shutdown_grace_s`
(30 s) + 180 s, 1,410 s in all, which leaves about three minutes for finishing; this run needed more. It exited 247
(SIGKILL). Its end-of-run sealed scoring had already run in the killed process (five oracle queries recorded in
lab.db, the run's cap). run_research.py's fallback then wrote its summary.json from lab.db: it marks experiments still
running as killed (none should have been, after the shutdown) and reuses the stored sealed scores without a new query.
The run script recorded the stop. The cause is operational: the watchdog's margin is too short for finishing a Norman run on this machine.
Nothing in the search failed.

**Seed 1 is its own arm.** By the stop rule it is reported as "killed by the watchdog while finishing", beside B2's
arm and never in it. The alternative the Mac session raised, keeping it in the arm if its end-of-run outputs turn out
complete, is not taken, because membership would then be decided after looking at the run. Its sealed reading, made
like the others' after B2 has ended, is reported in a row of its own, labelled as a run killed while finishing, and
decides nothing.

**Disclosure.** While diagnosing the kill, the Mac session displayed one row of seed 1's summary table: the additive
baseline's (EXP_0003), possibly with its sealed column. That model's sealed score was already on record (0.713, since
N1). Seed 1's selected model and its visible score were seen (EXP_0875, 10 features, alpha 120000, visible 0.6408);
by the Mac session's report, no B2 run's selected-model sealed score has been read. Seed 1's are in its run directory,
computed before the kill. The replacement below does not depend on anything seen: a run stopped by an operational
kill is replaced by the next unused seed.

**How B2 continues (decided now, before any B2 sealed reading).**
- Seed 2 runs as specified, `runs/norman_ds_addstart_w4_r2`, then seed 3, `runs/norman_ds_addstart_w4_r3`, in place of
  seed 1, so that B2's arm has three runs: r0, r2 and r3. Everything else is as specified: the pinned code ce1b530, the
  data and its Replogle file, the start, the caps, the $45.50 gate and the stop rule.
- Seeds 2 and 3 pass `--no-watchdog`, so run_research.py runs the lab in its own process instead of a child under the
  1,410-second watchdog. Nothing that shapes the search changes. The controller still ends the search at 20 minutes
  and waits the same 30 s for running experiments; `run.shutdown_grace_s` is not raised, because it decides which
  experiments finish. The spend caps still bound the money. The watchdog's 180-second margin lies past the search,
  the grace and the shutdown's ten-second kill window, so it acts during finishing unless start-up or shutdown took
  minutes; r0 exited 0, so it never acted on r0, which is therefore the same run as r2 and r3 but for its seed. In the
  watchdog's place, the run script terminates a run still going 90 minutes after it started, and that counts as a kill
  under the stop rule.
- The scripts: `block_b2_run.sh` now takes seeds 2 and 3 only (seeds 0 and 1 ran from its version at ce1b530). Seed 2
  requires seed 0's pass marker and seed 3 requires seed 2's. `block_b2_resume.sh` runs seed 2, then seed 3. The main
  checkout stays on the pinned commit, so both are brought into `genemila_scale_logs/b2_resume/` with `git show`. The
  stop marker `block_after_n4_stopped.txt` is renamed `block_after_n4_stopped_r1.txt`, and kept, once this note is on
  GitHub.
- The readings are as specified, with r3 in r1's place: the arm over r0, r2 and r3, and the combined model of r0, r2
  and r3.

**Money.** The ledger reads $41.03. At r0's and r1's costs, seeds 2 and 3 take it to about $43.6 to $44.3, each still
starting only at $45.50 or less; at their caps ($2.50 each) the ledger would end at $46.03 at most, inside $48. B3 is
dropped from this block, as the plan foresaw ("if anything in B1 or B2 stops the block, B3 is what is dropped").
Whether B3 runs later, under a cap above $48, goes to Andres with B2's results.

## Addendum, 2026-10-11 23:10 UTC, to the note of 22:50 (written before any B2 sealed reading)

A review of the note found what follows. The note stands except where this section corrects it.

**The replacement departs from the plan, and it is bounded.** "The arm reading" above already says what happens when
a run is its own arm: the arm is read over the remaining runs, with R stated. Read that way, B2's arm would be r0 and
r2. The note's replacement of r1 by seed 3 departs from that, and its last sentence under "Disclosure" stated as a
standing rule what is a decision taken here. The reason for it: B2 was designed with R = 3, and with R = 2 the
run-to-run part of the arm's standard error has one degree of freedom, so k can grow to 12.7 and the primary reading
would be far weaker than designed, for a cause that has nothing to do with the search. The departure is bounded: only
r1 is replaced. If r2 or r3 is lost too, that is written up and the arm is read over the runs that remain, as the plan
says, with no further replacement. The arm as first specified, r0 and r2 by the rule against the start, is reported
beside the primary reading and marked reported, not read, as the jackknife row of the 20:30 amendment is; it scores
nothing new on the sealed set.

**Who decided the extra run.** Seed 3 is a paid run the plan did not list. It runs on Andres's standing words of 19:10
to 19:16 UTC, which put the rest of his DeepSeek balance at the lab-code owner's judgement ("you can spent as much as u
want and you think is necessary we have in total 33 in deep seek"; "keep improving the model spent those dolars
well"), within this block's $48 cap and in the place of B3's spending. He was told in the build thread at 22:52 UTC.

**The evidence that the watchdog never acted on r0** is that r0's log has no WATCHDOG line (the stop-rule check it
passed), not its exit code: run_research.py returns 0 after a watchdog kill when summary.json already exists.

**Where r1's kill is recorded.** Nothing in r1's run directory records it. The fallback marks only experiments still
active as killed, and there were none; its summary.json has no duration note, because the shutdown had already
recorded the run's end. `handoff_state.py`, `sealed_reading.py` and `arm_reading.py` would therefore take r1 for a
clean run if given it. The record is `genemila_scale_logs/norman_ds_addstart_w4_r1.log` (the WATCHDOG line),
`genemila_scale_logs/block_after_n4_stopped_r1.txt` and this plan. r1's reading is written as
`docs/results/norman_b2_r1_killed_sealed_reading.md`, apart from the members' files, and is never passed to
`arm_reading.py`. It is not renamed `_contaminated`, AGENTS.md's treatment of a broken run: its search ended normally, and all five of its end-of-run sealed queries ran in the killed process
before the kill. Its lab.db events, times in UTC: the ensemble built at 22:34:17, the queries at 22:34:46, 22:35:25,
22:36:05, 22:36:44 and 22:37:23, about 39 s apart. The kill came at about 22:37:40, 1,410 s after the start, which the
controller's deadline line (22:34:13) places at about 22:14:10. The fallback's summary.json, written at 22:38:13,
reuses those five stored scores, since the cap left it no new query. The kill cut only the last steps of the
finishing, after the fifth query.

**The cause, narrowed.** The control and r0 finished within the watchdog's allowance on the same machine, so "the
watchdog's margin is too short for finishing a Norman run on this machine" says too much. The control and r0 took 169 s and 170 s from their controller's deadline line to
their summary, about 40 s inside what the watchdog leaves after that line (the 30 s grace and 180 s, less the
seconds of start-up); r1's five queries alone ran until 190 s after its deadline line. The margin was a near miss
that the control and r0 cleared and r1 did not. The Mac session ran nothing heavy while r1 ran (a polling loop and one
short status check at 22:27); other processes on the Mac were not checked.

**Disclosure, completed.** Every run's log in `genemila_scale_logs/` ends with the rendered summary, which holds every
finalist's sealed score; r0's and r1's logs hold them now. Nobody reads the end of a B2 run's log, or a B2 run's
summary.md, before the readings. r0's selected model and visible score were also seen, printed by the run script
(EXP_0724, 24 features, visible 0.628). The command that displayed r1's EXP_0003 row was `tail -12
genemila_scale_logs/norman_ds_addstart_w4_r1.log | cut -c1-240`, the Mac session's first look after the stop. It
showed that one table row without its header (five metrics as pairs, taken to be visible / sealed: 0.699 / 0.677,
0.009 / 0.007, 0.779 / 0.813, 0.557 / 0.480, 0.892 / 0.902), then the run's compute-efficiency block and its
reproduction command, which names EXP_0875, the selected model. EXP_0003 is the additive baseline, the same
deterministic model on the same split as in N1 to N4, so its sealed values were already known. No row of the
selected model, the finalists or the ensemble was shown, and no other command showed a B2 sealed number (the others
were greps of r1's log for WATCHDOG and errors, its lines 376 to 392, a print of five summary.json fields that hold
no score, and sqlite counts).

**Reproducibility.** `--no-watchdog` is recorded only in the "command:" lines the run script prints into
`genemila_scale_logs/block_b2_resume.log`; config.json does not hold it.
