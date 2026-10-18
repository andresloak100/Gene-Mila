# Block D: the first discovery-mode runs, on Adamson, fixed before any run

Written 2026-10-18 02:45 UTC by the lab-code owner (the "Autonomous research system" session, claim
[#68](https://github.com/andresloak100/Gene-Mila/issues/68)) on Andres's delegation of the DeepSeek runs (17 October
21:18 UTC, "you have access to the deepseek agents so you can do the direct runs", recorded on
[#41](https://github.com/andresloak100/Gene-Mila/issues/41)) and on his typed words of 18 October 02:41 UTC in the
project chat: **"go discovery, cap $10"**, answering the coordinator's line that the first discovery-mode run on
Adamson is the fastest real result and starts only on his words. Under `docs/ROADMAP.md` section 5 the agents' path on
the tier-1 tables paused after block G; this block changes what the planner is shown and how the run judges novelty
(`docs/DISCOVERY_MODE.md`, draft PR [#71](https://github.com/andresloak100/Gene-Mila/pull/71), claim #69), not the
inputs, and runs as its own arm. The lead may veto it before the first paid call; Andres's cap is for this block only.
**Nothing below has run.** From the first paid call on, a change is a new dated section at the end, never an edit.
Every number in the readings comes from a run directory named here. Scripts: `docs/mac/block_d/`.

## Question

1. Shown where its best model fails (training folds only) and which bundle inputs no feature has read, does a
   DeepSeek-planned run propose features that read unread inputs, and how many (`summary.json["discovery"]`)?
2. Does any feature it builds pass the corrected fair test (`docs/GOAL_CRITERIA.md` A.1), on the same bundle, test and
   family rule as block G's negative reading? If one does, its `mechanism` and `predicted_sign` were written by the
   planner before the feature was fitted, so A.2's sign check reads from the record, not from hindsight.
3. Descriptive only: does the arm score differently out of fold from block G's G1 arm, which differs from it only by
   the mode (and PR #71's code on top of block G's)?

## Arms, bundle `data/adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`, the eight knowledge files of block G's g1 arm, `docs/PLAN_G_CLEAN_ARM.md`)

| arm | what | runs | cost |
|---|---|---|---|
| D1 | block G's g1 settings (DeepSeek planner `deepseek-v4-pro`, 4 `deepseek-flash` workers, 20 min, fresh start, caps `budget.max_total_usd=1.0` and `budget.max_planner_usd=1.5`, `--no-watchdog`) plus `--set schedule.discovery=true` (dry rounds 3, `derived_r2` 0.8, the defaults of `configs/default.toml` on PR #71), code `D_COMMIT` = `23b3b12` (PR #71's head), `runs/adamson_cf_d1_ds_w4_r{0,2,3}_discovery` | 3 | paid here |
| G1 | block G's `runs/adamson_cf_g1_ds_w4_r{0,2,3}` (code `baa7dfd`): the comparison arm | not re-run | paid in G |
| G0 | block G's `runs/adamson_cf_g0_ds_w4_r{0,2,3}`, the same bundle without the three tables: context | not re-run | paid in G |

Seeds 0, 2 and 3 (B2's and G's). The run directory suffix `_discovery` is issue
[#72](https://github.com/andresloak100/Gene-Mila/issues/72)'s convention: `run_arm` in the protected results table does
not label the arm until PR [#73](https://github.com/andresloak100/Gene-Mila/pull/73) lands, so its rows are tabulated
apart by hand until then. Why Adamson: the comparison block and the fresh test are on Adamson, and G1 is the arm where
the tables did not help, so the planner has the most to learn from its errors there; Norman follows only as a later
dated section, on Andres's word. Why PR #71's head rather than the integration branch: the mode exists only there;
the code is recorded in `summary.json["base_commit"]` and the arm is never pooled with G1 (a different code version
and a different planner view). If PR #71 is merged before the chain starts, the merge commit replaces `D_COMMIT` in
the dated note below and in `block_d_run.sh`, nothing else changes.

**The key** stays `API_KEY` in Andres's `~/.zshenv` and reaches the run as `DEEPSEEK_API_KEY` in the chain's process
environment only (`DEEPSEEK_API_KEY="$API_KEY" ...` in the login shell that starts the chain); the run script unsets
`API_KEY`. Never on a command line, in a file or in a log.

## Money

Andres's words: "go discovery, cap $10" (18 October 02:41 UTC, project chat). **Block cap: the shared DeepSeek ledger
(provider `deepseek`) may rise by at most $10 over its reading when the block starts.** Expected: three runs at about
block G's $1.08 per run on the ledger ($12.97 for twelve), $3 to $5 in all (discovery mode adds planner calls within
the $1.50 planner cap per run); the ledger counts about twice what DeepSeek bills (`docs/ROADMAP.md` D12). The cap is
written once, before anything paid, by `block_d_cap.sh 10` into `genemila_scale_logs/block_d/block_d_cap.txt` as
`<cap> <ledger at the start> <UTC date>`; the command refuses if the file exists. Each run passes
`--set budget.cumulative_usd.deepseek=<cap>` with its two run caps and starts only when the ledger plus $2.50 stays
within the cap (exit 2 otherwise: the block ends incomplete and what ran is reported as it is). Floor (D12): no paid run
when the console's topped-up balance is under $8; the balance read of claim #68, made on the Mac before the chain, is
the reading before the block and goes in the dated note. This block's $10 sits beside block H's conditional $15
(ledger + $15 on Andres's line, `docs/PLAN_H_COMPARISON.md`); the two never run at once.

**Stop rules** (the run becomes its own row, the chain stops with `block_d_stopped.txt`, the cause goes in a dated
note): a run that fails (exit code not 0); costs more than $2.00 on the ledger, or the ledger cannot be read after it
(or reads below its start); ends with `planner.mixed` true; records a knowledge list other than the bundle's own
(`run.external_knowledge` not empty); has `schedule.discovery` other than true in its `config.json`; or writes no
`discovery` record in `summary.json`.

## Exact commands (Mac; one paid run at a time; never beside block H's chain, a proxy, a feature_compare reading or the scaling driver)

From a login zsh, `L=~/Documents/Mila/Gene-Mila/genemila_scale_logs`, the three scripts copied to `$L/block_d/`.

1. **State.** `python handoff_state.py --fetch`; `pgrep -fl 'run_research.py|scale_seq.sh|feature_compare.py|ledger_proxy.py|block_h_chain.sh'`
   (nothing may be running); the balance read (claim #68, step 1) at or above $8 topped up.
2. **The checkout** (free): `cd ~/Documents/Mila/Gene-Mila && git clone https://github.com/andresloak100/Gene-Mila.git gene-mila-23b3b12 && cd gene-mila-23b3b12 && git checkout -q 23b3b12`
   (PR #71's head; `git rev-parse --short=7 HEAD` prints `23b3b12`). It uses the main checkout's `.venv` (read-only) and
   bundle, as block G's checkout did. Then, free, `nice -n 19`: `PYTHONPATH=$PWD ../gene-mila/.venv/bin/python -m pytest -q tests/test_discovery.py`
   (PR #71's tests on this Mac; its output goes in the dated note).
3. **The cap**, once, after step 1: `bash $L/block_d/block_d_cap.sh 10`.
4. **The chain**, detached, from the login shell (never a tool shell), with the key reaching only this process:
   ```bash
   cd $L/block_d; screen -dmS blockd zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" caffeinate -i bash block_d_chain.sh > block_d_chain.log 2>&1'
   ```
   Order: r0, r2, r3. A run whose `.passed` marker exists is skipped, so a pre-run refusal (exit 1 or 2) is fixed and
   the chain restarted the same way; a stop after a run (`block_d_stopped.txt`, exit 3) is not resumed until the cause
   is written up here. Each run: the checks above, then `run_research.py --minutes 20 --workers 4 --dataset adamson_cf
   --planner-provider deepseek --planner-model deepseek-v4-pro --worker-provider deepseek --worker-model deepseek-flash
   --run-dir <MAIN>/runs/adamson_cf_d1_ds_w4_r${S}_discovery --set run.seed=$S --set run.data_dir=<MAIN>/data/adamson_cf_clean_tables
   --set budget.ledger=<ledger> --set budget.cumulative_usd.deepseek=<cap> --set budget.max_total_usd=1.0
   --set budget.max_planner_usd=1.5 --set schedule.discovery=true --no-watchdog` (`block_d_run.sh`), its log at
   `$L/block_d/<run>.log`, its check at `$L/block_d/<run>.check.txt`, one line per event in `progress.md`.
5. **Other work on the Mac during the chain:** only `nice -n 19` reads (claim #68's manifest and adapter checks are
   allowed; no Docker image build, no second lab run, no feature_compare, no proxy).

## Readings, fixed now, made only after the chain has ended (free; `nice -n 19`; from a clone at `D_COMMIT` or later into its `docs/results/`)

1. **Discovery readings, descriptive,** per run from `summary.json["discovery"]`, `planner/discovery_rounds.json` and
   `planner/discovery_EXP_*.json`: rounds and counted rounds, hypotheses and how many named an unread input, which
   inputs were proposed, the round the planner went dry (or never), features scored for derivability, the
   `new_input_features` and `derived_features` lists with their `derived_r2`; the `.check.txt` counts of features
   reading each knowledge file and control statistic. Reported per run and as mean ± sd over the three.
2. **The fair test (A.1), primary.** Exactly block G's corrected reading (tool at `2f2e683` or later, the commands in
   `docs/results/adamson_cf_g_stage1.command.txt`, `_select`, `_stage2`, `_pool`), with D1's plugins in place of G1's:
   per run the plugins copied from `runs/adamson_cf_d1_ds_w4_r$S_discovery/feature_store/*.py` into
   `docs/results/adamson_cf_d_plugins/r$S` (**the family is every plugin of the three runs**, not only table readers:
   discovery mode does not restrict what the planner proposes); stage 1 with `--null-reps 0` on
   `data/adamson_cf_clean_tables`, `select` (every status-ok row), stage 2 at `--null-reps 999` (the gene null for every
   row, the perturbation null for the rows proportional to a parent column), `pool` into
   `docs/results/adamson_cf_d_pooled_holm`. Parent: the built-in start; fold seeds the tool's default; OOF only, no
   `--with-val1`. Candidate hashes (`shasum -a 256` of every copied plugin) go on #41 before the tool runs. A row is
   found when `pooled_holm.json` says `found` (the mapping onto A.1's parts is block G's, `docs/PLAN_G_CLEAN_ARM.md`,
   reading 1). A.1 is met when at least one row is found; the dated status line of `docs/GOAL_CRITERIA.md` then names
   the row and run, and A.2 is read from the planner's recorded `mechanism` and `predicted_sign` for that feature
   (`planner/plan_<round>.json`, `proposed_feature_json`) against the sign of the saved standardised add-one
   coefficient in `feature_compare.json`: the sign was stated before the fit, so it counts as pre-registered for that
   feature only; a mismatch is reported, not explained away. Secondary, labelled: the same table restricted to the rows
   in `new_input_features` (the features that read an unread input plainly), with the family-wise p from the full
   family, so no second correction is invented.
3. **Arm against arm, development tier (descriptive).** One call rebuilds the nine selected models under the same
   parent and fold seeds (`tools/feature_compare.py --null-reps 0 --source-run d1_r0=... d1_r2 d1_r3 g1_r0 g1_r2 g1_r3
   g0_r0 g0_r2 g0_r3`, `docs/results/adamson_cf_d1_vs_g`): each run's `(set)` row (OOF M1 to M12, ΔM1 ± SE_adj over the
   start, wins), per arm the mean ± sd over its runs. No test; no difference is claimed inside either arm's spread;
   OOF is not held out for any arm.
4. **Per run, sealed, last:** the run's own capped oracle queries at its end are the lab's usual finalist scoring
   (`final.top_k`, logged), not a choice; `tools/sealed_reading.py --runs <run> --out docs/results/adamson_cf_d1_r$S_sealed_reading.md`
   as for G. Adamson's sealed set is worn (read in every earlier Adamson block): indicative only, read after readings
   1 to 3, chosen from by nobody.
5. **Descriptive:** per run the number of experiments, the largest planner state (24,000-character cut in discovery
   mode), the planner's cost and calls (`summary.json["llm_usage"]`), and whether `planner.dry` fired.

Nothing is chosen from a sealed score. A found row is a candidate for replication (A.3) and the fresh test (A.4), not a
discovery (`docs/GOAL_CRITERIA.md` A.2 to A.6); the lead reads the block against the criteria and names the next step.

## To be filled in before the chain (dated notes go below this line)

- Andres's cap line with its date (copied from the project chat); the console reading before the block (topped-up
  balance, granted balance); the ledger at the start and the cap record line.
- `D_COMMIT` confirmed (`23b3b12`, or PR #71's merge commit), the Mac's `tests/test_discovery.py` result on it.
- The bundle check output of the first run script (`bundle adamson_cf_clean_tables: split_id ..., knowledge ...`).

- **2026-10-18 03:35 UTC (lab-code owner), before the chain.** Console reading at 02:29 UTC from the Mac
  (PR [#77](https://github.com/andresloak100/Gene-Mila/pull/77), `docs/mac/mac_checks_20261017/balance_reading.txt`):
  topped-up balance $28.19, granted $8.35, over the $8 floor. `D_COMMIT` is `23b3b12` (PR #71's head, not yet merged);
  the checkout `gene-mila-23b3b12` is clean at it and its `tests/test_discovery.py` gives 7 passed on the Mac. The
  three scripts are copied to `genemila_scale_logs/block_d/` and hash-checked against this branch. Not started: the
  Mac session's own permission check refused `block_d_cap.sh 10` (classed a real-world transaction), so no cap file
  exists and nothing paid has run; Andres runs steps 3 and 4 himself in a Terminal. Still to record here: the cap
  record line and the ledger at the start, then the first run's bundle check output.

- **2026-10-18 17:58 UTC (lab-code owner), the chain is running.** Andres pasted the plan's two commands into the lab
  thread and wrote "started" at 17:53 UTC; he ran them himself in a Terminal on the Mac. Console reading just before the
  start: topped-up balance $28.19, total $36.55 (the $8 floor holds). Cap record line: `70.23 60.23 2026-10-18` (the
  ledger at $60.23 plus $10), written once; a second cap command a few seconds later was refused by the script's
  `noclobber`, so nothing was doubled. The first run script's bundle check passed: `adamson_cf_clean_tables`,
  `split_450515be1a0d8d2e`, the 8 knowledge files. Running: `adamson_cf_d1_ds_w4_r0_discovery`, then r2 and r3 one at a
  time; progress on [#68](https://github.com/andresloak100/Gene-Mila/issues/68). No other paid run while it runs.

- **2026-10-18 19:15 UTC (lab-code owner), the chain is finished; the exact records.** Cap: Andres's typed "go discovery,
  cap $10" (02:41 UTC); he ran steps 3 and 4 himself from a Terminal at 17:53 UTC and wrote "started" at 17:53:12 UTC.
  Console reading before the block (17:53:25 UTC, HTTP 200): topped-up 28.19, granted 8.35, total 36.55 (the 02:29 UTC
  reading was the same). Cap record line: `70.23 60.232225 2026-10-18T17:53Z`. `D_COMMIT` 23b3b12 (PR #71 not merged);
  `tests/test_discovery.py` on the Mac: 7 passed in 70.34 s. Bundle check line of the first run script:
  `bundle adamson_cf_clean_tables: split_id split_450515be1a0d8d2e, knowledge gene_annotation.json gene_constraint.json
  gene_sets.json ppi_network.json prior_network.json protein_annotation.json targets.json transcription_factors.json;
  knowledge summary 2721 characters (section budget 8000)`. Outcome: the chain ended at 18:57:45 UTC, three runs, every
  after-run check passed, no stop; ledger 60.232225 to 61.240534 (the block cost $1.008309; per run r0 0.546548,
  r2 0.137546, r3 0.324215). Discovery record per run (r0/r2/r3): dry at rounds 25/6/14; hypotheses 192/48/113; naming
  an unread input 54/10/37; below-threshold features naming an unread input 48/9/33; derived features 6/1/4;
  visible-tier best 0.552/0.506/0.551 (not a result). The 270 plugin hashes are on #41 before stage 2; stage 1 of the
  fair test runs on the Mac at nice 19 in the clone `gene-mila-d-readings` at 23b3b12; the readings PR comes from
  `claude/block-d-readings`.
