# State of the Gene-Mila runs on this Mac

Written by the Claude session that ran the comparison, 2026-10-04 17:45 UTC. Whoever runs
something here next updates this file. It describes what is on disk; where it disagrees with
HANDOFF.md section 1 in the repository, this file was written later and from the machine itself.

## Right now

- **Nothing is running.** No detached driver exists and none was ever started; every run so far
  was a child of a Claude session. `pgrep -fl run_research.py` shows nothing.
- **Main checkout** `~/Documents/Loak-documents/gene-mila` is at `2370276` on
  `claude/autonomous-research-system-3k435s`. Untracked there: `docs/cellforge_notes.md`,
  `docs/results/scaling.md`, `docs/results/scaling.json` (results_table.md and the calibration
  file are tracked and unchanged).
- **Old-code worktree** `~/Documents/Loak-documents/gene-mila-2492e11` is at `2492e11`, for the
  two remaining comparison repeats. It has no `.venv`, `data/` or `runs/` of its own.
- **DeepSeek ledger:** $4.66. Claude planner: $32.95 as the CLI's estimate of subscription usage.
- **The DeepSeek key is not stored on this Mac.** `DEEPSEEK_API_KEY` is not set in any shell
  startup file. Paid runs so far received it as a process variable from the Claude session.
  Nobody else can start a paid run until Andres puts it in `~/.zshenv` himself.
- **Waiting on Andres:** whether paid runs may continue unattended, and with which cap
  ($15, $10, or free only). No paid run starts without his answer in his own words.

## Runs on disk (`gene-mila/runs/`), all on `data/adamson_cf`, split `split_450515be1a0d8d2e`

| run | code | arm | status |
|---|---|---|---|
| scale_w1_r0, scale_w1_r1 | 2492e11 | Opus planner, DeepSeek workers, 1 worker | complete |
| scale_w4_r0 | 2492e11 | same, 4 workers | complete |
| scale_w4_r1 | 2492e11 | same, 4 workers | complete; killed at its deadline, summary regenerated (see below) |
| scale_w8_r0 | 2492e11 | same, 8 workers | complete |
| scale_w16_r0 | 2492e11 | same, 16 workers | complete |
| scale_w8_r1, scale_w16_r1 | 2492e11 | same, seed 1 | **not run** |
| scale_control_r0..r5 | 2492e11 | scripted planner, mock workers | complete, six identical results |
| newcode_control_r0..r5 | 72a53c5 | scripted planner, mock workers | complete |
| newcode_ds_w4_r0/_r1, newcode_opus_w4_r0/_r1 | current | planner check | **not run** |
| scale_w8_r0_contaminated | 2492e11 | planner fell back mid-run | excluded from tables |
| scale_w1_r1_interrupted | 2492e11 | killed at 17 of 20 minutes, no summary | excluded from tables |

`scale_w4_r1`: the Claude session was restarted just after the run's deadline, before the
summary was written. All experiments had finished. The summary was regenerated with
`summarize.py --query-only`; that stamped a late `runs.finished_at`, which was then cleared so
the `2370276` duration fix applies. The database from before that one-field edit is
`runs/scale_w4_r1/lab.db.before_duration_fix`. Scores: 0.6091 visible, 0.6037 sealed.

## Files in this directory

- `status.txt`: one line per start and finish of every run from 2026-10-04 01:14 EDT onward.
- `progress.md`: the same for the new-code control runs only.
- `<tag>.log`, `<tag>.analysis.log`: console output of each run and of `analyze_run.py`.
- `scale_seq.sh`: the driver used for the comparison. It runs the tags it is given one at a
  time, skips a run directory that already exists, and stops when a file named `STOP` is here.
  It reads the key from the environment and contains none.
- `results_interim/`: the three result tables as first built, before the new-code controls.
- There is no `driver.log`.

## Exact next steps (paid ones only after Andres's answer)

1. Remaining repeats, old code, Opus planner (needs the Claude CLI not to be at its limit).
   Run from the `2492e11` worktree with the main checkout's data, environment and ledger:
   `--dataset adamson_cf --minutes 20 --workers 8 --set run.seed=1 --set budget.max_total_usd=2
   --set budget.cumulative_usd.deepseek=10 --run-dir <main checkout>/runs/scale_w8_r1`, then
   the same with 16 workers and `budget.max_total_usd=3` into `runs/scale_w16_r1`.
   This has not been tried from the worktree yet; check that `--set run.data_dir` and
   `--set budget.ledger` point at the main checkout before trusting it.
2. Planner check on the current code, as in HANDOFF.md section 9.
3. `scaling_report.py` and `results_table.py build` over every `scale_*` and `newcode_*` run
   except `_contaminated` and `_interrupted`.

## Things that went wrong here, so the next agent avoids them

- A session restart kills every run that is a child of that session. It happened twice.
  Start long runs detached (`nohup`), and check that the permission system allows it first.
- Two downloads writing the same file corrupt it silently. Check the md5 after every download.
- The Claude planner's session limit turns an Opus-planned run into a scripted-planner run
  part-way, with only `planner_error` events to show for it. Check
  `sqlite3 <run>/lab.db "select count(*) from events where kind='planner_error'"` after each run.
- The no-LLM control ends after about two minutes on both code versions. It is not an
  equal-time arm.
- The visible score is on a different scale on the old and new code (0.571 against about 0.51
  for the same control). Never compare visible scores across code versions.

## Update 2026-10-04 19:20 UTC

- Main checkout is now at `537344f`.
- **Running, detached from any session:** `control_seq.sh`, the free control reruns
  `runs/newcode2_control_r0..r5` (scripted planner, mock workers, 20 minutes each). Started
  19:13 UTC with `nohup caffeinate -i -s bash control_seq.sh > driver.log 2>&1 &`. If r0 ends in
  under 600 s the script does not start r1..r5. A `STOP` file halts it between runs.
- **Ready, not started:** `scale_seq.sh`, the paid driver (scale_w8_r1, scale_w16_r1,
  newcode_opus_w4_r0/_r1, newcode_ds_w4_r0/_r1). It needs `DEEPSEEK_API_KEY` in its environment
  and Andres's go-ahead in his own words. Its ledger gate sums DeepSeek spend only and stops
  starting runs at $14.
- The old-code worktree now has `data -> ../gene-mila/data` (a symlink), because code `2492e11`
  always reads `<its own root>/data/<dataset>`.

## Update 2026-10-04 21:55 UTC: the comparison and the planner check are complete

- **Nothing is running.** The detached chain (`chain.sh` -> `scale_seq.sh`) finished at 21:27 UTC
  with exit code 0. No gate fired. `pgrep -fl run_research.py` shows nothing.
- **DeepSeek ledger: $9.91** of the $15 cap Andres set on 2026-10-04 19:16 UTC ("go, $15 cap").
  Claude planner: $54.78 as the CLI's estimate of subscription usage.
- **No further paid run is approved.** Anything new needs Andres's own words in the thread.
- Main checkout is still at `537344f` (not pulled, so every `newcode_*` run shares one version).
  The lab branch upstream is ahead (`59c2ad3` or later).

Runs completed today, all on `data/adamson_cf`, 20 minutes each:

| run | code | planner | workers | seed | sealed pearson_delta |
|---|---|---|---|---|---|
| scale_w8_r1 | 2492e11 | Opus | 8 | 1 | 0.5832 |
| scale_w16_r1 | 2492e11 | Opus | 16 | 1 | 0.5926 |
| newcode_opus_w4_r0 | 537344f | Opus | 4 | 0 | 0.6007 |
| newcode_opus_w4_r1 | 537344f | Opus | 4 | 1 | 0.5873 |
| newcode_ds_w4_r0 | 537344f | DeepSeek V4 Pro | 4 | 0 | 0.5383 |
| newcode_ds_w4_r1 | 537344f | DeepSeek V4 Pro | 4 | 1 | 0.6007 |
| newcode2_control_r0 | 537344f | scripted (no LLM) | 4 | 0 | 0.5527, ended after 160 s |

`newcode2_control_r1..r5` were not run: r0 ended in under 600 s, so the gate skipped them.

Result files regenerated over all 27 runs, in `gene-mila/docs/results/`: `scaling.md`,
`scaling.json`, `results_table.md`, `results_table.json`. Their contents were sent to the
project thread with md5s; the thread commits them (the Mac session's push is refused).

**Summary for collaborators:** a Claude Doc at
https://claude.ai/code/artifact/6668e638-6fec-499d-ad9d-e68c78d95477 and a repository copy at
`docs/results/summary_for_collaborators.md` on the lab branch. The project thread owns both
copies; do not edit either from the Mac.

Scripts in this directory (none contains a key): `scale_seq.sh` (paid driver), `control_seq.sh`
(free controls with the r0 gate), `chain.sh` (order of the two), `run_report.sh` (per-run report
fields), `planner_compare.py` (what each planner proposed, read from the run databases).

## Update 2026-10-04 23:25 UTC: visible-only selection replay

- Ran `tools/replay_selection.py` (code `7debddd`) at 23:22 UTC over the eleven runs that
  cross-validated (newcode_opus_w4_r0/_r1, newcode_ds_w4_r0/_r1, newcode_control_r0..r5,
  newcode2_control_r0), after Andres wrote "go" in the thread.
- It used visible data only: the visible validation set and the out-of-fold training
  predictions. **The sealed (val2) labels were not read**, no oracle query was made, no API call.
- Output: `gene-mila/docs/results/selection_replay.md` and `selection_replay.json` (untracked).
- Main checkout is at `7debddd`. My earlier copies of the four result tables are in
  `genemila_scale_logs/results_mac_copies/`.
- Nothing is running. DeepSeek ledger unchanged at $9.91.

## Update 2026-10-05 01:07 UTC: one paid confirmation run in progress

- **Running, detached:** `runs/newcode_derule_opus_w4_r0` (code `7debddd`, 4 workers, seed 0,
  Opus planner with DeepSeek V4 Pro as failover, 20 minutes,
  `experiment.selection=pearson_delta+r2_top`). Started 01:07 UTC, ends about 01:29 UTC.
  Log: `newcode_derule_opus_w4_r0.log` in this directory.
- Approved by Andres in the thread ("continue wake it up", 01:05 UTC). One run only; nothing
  else paid is approved.
- DeepSeek ledger at start: $9.91.

## Update 2026-10-05 01:50 UTC: confirmation run finished

- `runs/newcode_derule_opus_w4_r0` finished cleanly at 01:28 UTC (352 experiments, planner
  stayed on Opus, no failover). **Nothing is running.**
- Result: sealed pearson_delta 0.5839 (ensemble; best single 0.5693) against 0.6007 for the
  same configuration under the old rule; sealed MSE_DE 0.1159 against 0.1178, R²_DE 0.8043
  against 0.8023. No evidence that `pearson_delta+r2_top` is better. One run, one seed.
- In this run's summary.json, `visible_score` and `query_only_score` are the combined score;
  the sealed pearson_delta is `query_only_pearson_delta`.
- DeepSeek ledger: $10.25 of the $15 cap. Claude planner estimate: $57.70.
- The four result tables were regenerated over 26 runs at code `7debddd` and now show as
  modified tracked files in `gene-mila/docs/results/` (not committed). Their contents went to
  the thread with md5s.
- **No further paid run is approved.**

## Update 2026-10-05 02:05 UTC: tables regenerated with the fixed generators

- **Nothing is running.** DeepSeek ledger: **$10.25** of the $15 cap. Claude planner estimate $57.70.
- **The next paid step needs Andres's own words in the thread.** None is approved.
- Main checkout is at `0e0ba0f`. `runs/newcode_derule_opus_w4_r0` was re-summarised without
  `--query-only`; the count of `query_only` events stayed at 5, so no new oracle query was made.
- The four result tables were regenerated over 26 runs and differ from the committed ones by a
  few lines (they show as modified tracked files in `gene-mila/docs/results/`, not committed).
  The patches went to the thread with md5s.
- Copies of earlier generated files are in `results_mac_copies/` here, including
  `selection_replay.md` (moved there so the pull could proceed; the tracked copy is identical).

## Update 2026-10-05 02:45 UTC: time-to-best check and one more free control

- **Nothing is running.** DeepSeek ledger unchanged at **$10.25**. No paid step is approved;
  the next one needs Andres's own words in the thread.
- Main checkout is at `74e07ca`.
- `time_to_best.md` and `time_to_best.json` are in this directory (visible scores only, 26 runs).
  The tool measures gain from 0.000, not from the starting model, so its "share" columns and its
  "still rising" count mislead; measured from the starting model, the agent runs reach 74% to 97%
  of their gain by the midpoint and add +0.000 to +0.004 in the last quarter in 11 of 13 runs.
- `runs/control_components_w4_r0` (free, scripted planner, mock workers, code `74e07ca`, seed 0)
  finished in 182 s: sealed pearson_delta **0.5932**, against 0.553 to 0.554 for the earlier
  controls and 0.584 to 0.604 for the agent arms. Its best model uses the new hand-written
  feature `response_components_e14` (ridge, alpha 41,310). On the DE-gene metrics it is still
  behind the agents (MSE_DE 0.142 against 0.117 to 0.124).
- That control feature was written after the agents' results and sealed scores were known, so it
  is not an independent no-LLM baseline.
- The four result tables were regenerated over 27 runs and show as modified tracked files in
  `gene-mila/docs/results/` (not committed); patches went to the thread with md5s.

## Update 2026-10-05 03:10 UTC: fixed time-to-best and a warm-start control

- **Nothing is running.** DeepSeek ledger unchanged at **$10.25**. No paid step is approved;
  the next one needs Andres's own words in the thread.
- Main checkout is at `bee2106`.
- `time_to_best.md` / `.json` here were regenerated with the fixed tool over 27 runs: 0 of 12
  runs that used their budget were still rising in the last quarter (scale_w4_r1 is wrongly
  marked "ended early"; it ran its full 20 minutes).
- `runs/control_components_from_opus_r0` (free, scripted planner, mock workers, warm start from
  `newcode_opus_w4_r0`) ran its full 20 minutes, 1,316 experiments. Sealed pearson_delta 0.5997,
  against 0.6007 for the run it continued. `response_components` did not join the best model;
  models that included it scored lower (0.5846 against 0.5908 on the selection score).
  **This run is built on the agents' features and is not a no-LLM reference**, although the
  generated scaling.md labels it as one.
- The four tables were regenerated over 28 runs (modified tracked files in
  `gene-mila/docs/results/`, not committed). Patches for three went to the thread; scaling.md
  was held back because of that mislabel.

## Update 2026-10-05 03:35 UTC: relabelled tables and fixed time-to-best over 28 runs

- **Nothing is running.** DeepSeek ledger unchanged at **$10.25**. No paid step is approved;
  the next one needs Andres's own words in the thread. The thread has told Andres the paid runs
  he was asked about are no longer worth running, and asked whether to start Norman.
- Main checkout is at `767c27a`.
- The four tables were regenerated over 28 runs; the warm-start run is now labelled
  "no-LLM continuation of newcode_opus_w4_r0 @ bee2106". Patches for three files went to the
  thread. `scaling.md` (md5 bb61158adc5759e9b554ea796cee5920) is held back once more: its
  "Is the ordering real?" section still compares the continuation with the agent arms in four
  pairwise lines and counts it among the agent arms in the control lines.
- `time_to_best.md` / `.json` here were regenerated over 28 runs with the fixed tool:
  2 of 14 runs that used their budget were still rising in the last quarter (scale_w8_r0 and
  scale_w16_r1, both old code); scale_w4_r1 now reads "no".
- The regenerated tables show as modified tracked files in `gene-mila/docs/results/`
  (not committed). Copies of every earlier generation are in `results_mac_copies/`.

## Update 2026-10-05 03:50 UTC: tables in sync with the branch

- **Nothing is running.** DeepSeek ledger unchanged at **$10.25**. No paid step is approved;
  the next one needs Andres's own words in the thread.
- Main checkout is at `08b386c` and `gene-mila/docs/results/` has no local changes: the four
  tables regenerate on this Mac byte for byte to the committed files (scaling.md md5
  534b05e5e821948eb054bb1256b192ed over the 28 runs).
- A continued run (`control_components_from_opus_r0`) now appears in the scaling table and the
  run list only, and in no comparison.
- `time_to_best.md` / `.json` here were regenerated over 28 runs (md5 2dd7371d... / d2a949a2...):
  2 of 13 runs that used their budget were still rising in the last quarter.
- Still untracked in the main checkout: `docs/cellforge_notes.md`,
  `docs/results/calibration_adamson_cf_val2.md` and `.json`, `docs/results/selection_replay.json`.

## Update 2026-10-05 04:00 UTC: standing by

- Main checkout is at `047595dd`. Nothing is running. DeepSeek ledger $10.25.
- Nothing more is pending on this Mac. The next paid step needs Andres's own words in the thread.

## Update 2026-10-11 00:40 UTC: assessment of Astra's work, and the ceilings

- **Nothing is running on this Mac.** No paid step is approved for the Claude session.
- **Astra's work is not in this checkout.** It lives in `~/Documents/Codex/2026-10-08/pl`
  (`work/gene-mila` on branch `astra/deepseek-continuation-memory` at `6a3e8a8e`,
  `work/gene-mila-compactness` on `astra/compact-master-selection` at `74114d43`; neither branch
  is on GitHub). Its reports are in `outputs/` there.
- Astra ran two 2-hour, 8-worker DeepSeek campaigns continuing `newcode_opus_w4_r0`
  (`astra_ds_w8_2h_20261008T165933Z`, `astra_ds_w8_2h_20261010T135041Z`). Held-out pearson_delta:
  0.5987 at the start, 0.6017 after the first, 0.6019 after the second (ensemble 0.5687). Models
  grew from 12 features to 176 columns. Its reports put the cumulative DeepSeek ledger at about
  $31.78; I did not verify that against the ledger file.
- Main checkout here is still at `047595dd`; the lab branch upstream is at `ab29a950`.
- **Ceilings measured on the 50 training perturbations** (`ceiling_analysis.py`, `.json` here;
  public data and raw training cells only): noise ceiling 0.889 mean (median 0.942); best mix of
  other perturbations' responses with hindsight 0.734 (non-negative) / 0.780 (any linear);
  best single neighbour with hindsight 0.657; average response 0.474. Models sit near 0.60.
  A pearson_delta of 0.99 is not attainable on this data.
- **Free attempt to improve** (`learned_kernel_experiment.py`, `.json` here): a similarity between
  targets learned from training responses scored 0.551 leave-one-out against 0.540 for gene-set
  similarity. No real gain.
- Open decision for Andres: whether to add an external source of target similarity
  (for example the Replogle 2022 K562 Perturb-seq screen, or DepMap co-essentiality).

## Update 2026-10-11 00:45 UTC: noise ceiling and refit on visible labels (both free)

- **Nothing is running.** Main checkout is at `1c434bd`. No paid step approved; DeepSeek ledger
  $31.78 (exact: 31.77819844, in `gene-mila/runs/spend_ledger.sqlite`, the file Astra also used).
- `noise_ceiling.md` / `.json` here (tools/noise_ceiling.py over the 28 table runs): ceiling of
  pearson_delta on the 17 visible-validation perturbations is 0.902 mean (median 0.927), from 300
  stored cells each. Agrees with 0.889 on the 50 training perturbations.
- `refit_visible.md` / `.json` here (tools/refit_visible.py, 28 runs, --arm-ensembles): refitting
  each run's finalists on all 67 visible perturbations changes the sealed pearson_delta by
  -0.0033 ± 0.0098 (up in 6 runs, down in 22; 13 of the 28 are identical controls). No gain.
  Averaging two runs' predictions gives +0.01 to +0.03. The sealed set is no longer fresh.
- Run databases were not changed by the refit (run_counts_before.txt = run_counts_after.txt).
- **Waiting on Andres's own words:** "download gwps" (8.81 GB) or "download essential" (1.55 GB)
  for the Replogle 2022 K562 screen from Zenodo record 13350497, to
  `~/Documents/Loak-documents/data_downloads/`. Nothing downloaded yet.

## 2026-10-11 ~00:55 UTC — reply to the 00:38 brief sent
- Sent to the thread: compact_model_curve.py whole (7,081 B, md5 dbb27bd37fbb3c06dc2038d82048ac85), every value of
  compact_model_curve_newcode_opus_w4_r0.json (10,487 B, md5 37d593a18d71c81faef99f3d2d03c015), and the inventory of
  Astra's two branches (base 8261c578; 28 files +2,844/-52 and 43 files +5,127/-124). Astra's tests were not run.
- Nothing running, nothing downloaded, nothing spent. No key held.
- Waiting on Andres's own words: "download gwps" or "download essential" (Replogle 2022, Zenodo 13350497).
- Do not score the 3-feature compact model by hand; the coordinator's tools/feature_audit.py does the single held-out read.

## 2026-10-11 00:42 UTC — Replogle download started (Andres: "download gwps", 00:38 UTC wake message)
- replogle_download.sh (detached, nohup caffeinate, resumable) -> data_downloads/replogle2022/ReplogleWeissman2022_K562_gwps.h5ad(.part)
  expected 8,805,466,154 B, md5 13db594f8f1d2ccb88fec44a13e414dc; log replogle_download.log ends with DOWNLOAD_OK or DOWNLOAD_BAD.
- Next, one at a time, each checked before the next (lab branch must be fast-forwarded to 72a28ad4 first):
  1. tools/build_external_screen.py --h5ad <file> --bundle data/adamson_cf --name replogle2022_k562 --dry-run
  2. same without --dry-run, --report genemila_scale_logs/external_replogle2022_k562.md (detached)
  3. tools/external_loo.py --bundle data/adamson_cf --knowledge replogle2022_k562 --out genemila_scale_logs/external_loo_replogle2022_k562.md
- Andres 00:39 UTC: wants everything documented in GitHub. I cannot push from the Mac; told him the options. Paste STATE.md to the thread after each step.

## 2026-10-11 ~02:15 UTC — Replogle screen downloaded, built, tested (all free); results sent to the thread
- Lab checkout at d022b853. Download OK 01:54 UTC (md5 13db594f...). Nothing running. Nothing spent. No key held.
- noise ceiling rerun with full cell counts (adamson_cf_ncells.json): 0.944 mean (was 0.902); old report kept as noise_ceiling_v1.*
- data/adamson_cf/knowledge/replogle2022_k562.json built (82 of 88 targets; 1,938 of 2,055 genes; md5 4da8cc7c...).
  NOTE: any run started from this checkout now hands this file to the agents; label such a run as the external-knowledge arm.
- external_loo (50 training perturbations, leave-one-out): mean 0.474, geneset_knn 0.545, external_direct 0.461,
  external_knn 0.572, external_stack 0.616 (+0.072 ± 0.020 over geneset_knn).
- My control external_stack_control.py/.json: stack without external columns 0.543, so the gain is the screen, not stacking;
  alpha grid edge does not matter (0.619 with a wider grid).
- Flagged: ATP5B = ATP5F1B (98 cells) and SLMO2 = PRELID3B (105) are missed by exact-symbol matching; FECH has 6 cells; no minimum cell count.
- push_to_github.sh written for Andres to run (never executed or syntax-checked by me; the permission system refused).
  Its list does not yet include the external_* reports.
- Waiting on: Andres's decision on a paid labelled arm with the knowledge file (needs his words and a key); coordinator's alias fix.

## 2026-10-11 ~03:00 UTC — alias rebuild, control with the Replogle file, feature audit started (all free)
- Lab checkout at 7010889b. Ledger unchanged (DeepSeek $31.77819844). No key held.
- replogle_aliases.json (97 Ensembl-matched renames; rescues targets ATP5B, SLMO2). Rebuilt knowledge file
  data/adamson_cf/knowledge/replogle2022_k562.json md5 2a1b4042... (83 targets, 2,035 genes, --min-cells 20); v1 kept as replogle2022_k562_v1.json.
- external_loo v2: stack 0.616 (wide grid 0.620) vs geneset_knn 0.545. Reports external_loo_replogle2022_k562_v2*.md/.json.
- runs/control_replogle_w4_r0 (scripted, mock, seed 0, 264 s): selected EXP_0076 visible 0.625, sealed 0.621,
  sealed MSE_DE 0.084, PCC_DE 0.964, R2_DE 0.848; start 0.501 / 0.520. Both external features selected. One seed, used sealed set.
- RUNNING (detached): feature_audit_run.sh -> feature_audit.md/.json, cache fa_cache, 30 runs (28 + copies of Astra's two under
  astra_run_copies/). Driver log feature_audit_driver.log ends with AUDIT_DONE. Resumable by re-running the script.
- Owed after it finishes: elapsed time, feature_audit.md in full with md5, json md5/size, what it says about Astra's 176-column models.
- Mac on battery (61% at 02:55 UTC); asked Andres to plug in.
- push_to_github.sh list extended; still never executed by me. Run it only after feature_audit.md exists.
- A paid agent arm with the knowledge file needs Andres's own words and a key.

## 2026-10-11 ~03:30 UTC — continuation with Replogle done; audit resumed; paid run blocked on key
- Andres (wake messages): DeepSeek cap $34 total (ledger $31.78, so $2.22 left); wants everything documented in GitHub.
- runs/control_replogle_from_opus_r0 (free; scripted continuation of newcode_opus_w4_r0 with the Replogle file):
  selected EXP_0416 visible 0.647, sealed 0.638, sealed MSE_DE 0.078, PCC_DE 0.968, R2_DE 0.863. 13 features, both Replogle ones in.
- Planned paid step B (coordinator's plan under Andres's cap): ONE run runs/replogle_ds_warm_w4_r0, DeepSeek planner deepseek-v4-pro and
  DeepSeek workers, 4 workers, 20 min, seed 0, --continue-from runs/control_replogle_from_opus_r0 (higher visible score: 0.647 vs 0.625),
  --set budget.cumulative_usd.deepseek=34 --set budget.max_total_usd=2.2; start nothing if ledger >= $33.50. Pause the audit while it runs.
  BLOCKED: DEEPSEEK_API_KEY is not set on the Mac. Mac is now charging.
- RUNNING: feature_audit_run.sh (resumed from 5 of 30). Waiter expects AUDIT_DONE in feature_audit_driver.log.
- push_to_github.sh list now also has control_replogle_from_opus_r0 files. Never executed by me.

## 2026-10-11 ~03:50 UTC — external_krr (free)
- Lab checkout 89ab4fb1. external_loo v3: external_krr 0.590 vs external_knn 0.568 (+0.022 ± 0.010); stack with krr 0.614 vs 0.616 (no gain).
- runs/control_replogle3_from_opus_r0 (free continuation of newcode_opus_w4_r0, code with external_krr): selected EXP_0466
  visible 0.657, sealed 0.646, sealed MSE_DE 0.0735, PCC_DE 0.970, R2_DE 0.868; 12 features incl. external_direct and external_krr.
  This is now the run with the highest VISIBLE score, so paid run B would warm-start from it.
- Paid run B still blocked: no DEEPSEEK_API_KEY on the Mac (Andres said "ok" at 03:38 UTC but no key yet). Mac on mains.
- RUNNING: feature audit, on Astra's two runs (29 and 30 of 30).

## 2026-10-11 ~04:15 UTC — feature audit done and reported; nothing running
- feature_audit.md (13,122 B, md5 fd691105...), .json (4.75 MB), feature_audit_feature_box.json. 30 runs, none skipped.
  Compact model: median 5 of 16 features; lower on validation in 7 of 15 agent runs (mean -0.0074).
  Astra: 48 feat/99 cols -> compact 1 feature (a 50-column random projection of the other features); 87 feat/176 cols -> 20/88, box 68.
  Flagged: composite features (ctx.feature on others) counted as one; merge-test min abs r oddity; 3 Astra plugins fail to import.
  First 28 runs audited on 7010889b, Astra's two on 89ab4fb1.
- push_to_github.sh: every listed file now exists. Andres runs it (check-only first). Never executed by me.
- Paid run B: waiting for DEEPSEEK_API_KEY on the Mac; warm start from runs/control_replogle3_from_opus_r0 (visible 0.657); cap $34 total.

## 2026-10-11 ~09:45 UTC — macOS test suite, audit rerun (all free); nothing running
- Lab checkout bd0da04b. Plain `python -m pytest -q`: 2 failed, 305 passed. Both failures are in the test helper
  _as_nullable_strings (tests/test_external_screen.py:417), which assumes the fixture's var index is a dataset; anndata 0.13.4
  on this Mac already writes it as a group. Lab code reader fix (ff4318b) works. Logs pytest_macos_2026-10-11*.log.
- feature_audit_v2.md/.json/_feature_box.json (code 6eb17a24, 2,346 s). Astra compact sets with required inputs: 31 features/83 cols
  and 49/120. Two rows (scale_w8_r0, newcode_ds_w4_r0) changed slightly vs the first audit: flagged as code change or non-determinism.
- Norman: no download until Andres writes it himself; then docs/NORMAN_PLAN.md section 6 steps 2-7, stop before anything paid.
- Paid run B: still no DEEPSEEK_API_KEY on the Mac. Warm start would be runs/control_replogle3_from_opus_r0 (visible 0.657). Cap $34 total.
- push_to_github.sh list includes the v2 audit files. Still never executed by me; Andres runs it (--check-only first).

## 2026-10-11 ~10:40 UTC — determinism check (free); nothing running
- Lab checkout 8c3b374e. tests/test_external_screen.py: 18 passed.
- Audit non-reproducibility traced: two agent features use Python's salted hash() of a perturbation name
  (scale_w8_r0: contrastive_near_far_transfer_e258 line 143; newcode_ds_w4_r0: target_degree_times_gene_response_e521 lines 62, 66).
  Blocks identical under PYTHONHASHSEED=0. Evidence: audit_det_a/, audit_det_b/, audit_det_hash_*.json, feature_block_hashes.py.
- Offered: grep all 30 runs' feature stores for hash( . Not done yet.
- Still waiting: DEEPSEEK_API_KEY for paid run B (cap $34 total); Andres's own word for any Norman download; Andres to run push_to_github.sh.

## 2026-10-11 ~11:30 UTC — nondeterminism scan and spread (free); nothing running
- nondeterminism_scan.md/.json/.py: 33 runs, 5,553 plugins, 173 hit lines (85 id, 84 hash, 3 unseeded np.random, 1 __hash__).
  Only two reported models hold a value-changing feature: scale_w8_r0 (contrastive_near_far_transfer_e258) and
  newcode_ds_w4_r0 (target_degree_times_gene_response_e521). The 0.646 model (control_replogle3_from_opus_r0) is clean.
  id() hits are cache keys into a per-context dict or object counts: harmless.
- Spread of visible score across processes: scale_w8_r0 about 0.628-0.636; newcode_ds_w4_r0 about 0.555-0.564. Fixed under PYTHONHASHSEED=0.
  Evidence in audit_det_J/. Nothing sealed was scored.
- Scan and helper scripts added to push_to_github.sh's list.
- Still waiting: DEEPSEEK_API_KEY for paid run B; Andres's own word for Norman download; Andres to run push_to_github.sh.

## 2026-10-11 ~12:40 UTC — Norman started (Andres: "download norman", 12:04 UTC wake)
- Lab checkout 02e70215. Guard check for run B: control_replogle3_from_opus_r0 has 0 refused plugins.
- data_downloads/NormanWeissman2019_filtered.h5ad: 698,680,199 B, md5 c870e696... Section 2 checks pass (norman_check.txt;
  norman_check_public.txt is the copy without unrelated paths).
- Bundle data/norman built (plan's exact command): 231 perts, 2,083 genes, split_a391fa9e7b4eccb7; train 112 / val1 63 / val2 56.
  Copies docs/results/norman_splits.json, norman_manifest.json (untracked).
- norman_replogle_aliases.json (84 aliases); 85 of 102 targets have a Replogle label.
- RUNNING: feature audit v3 (fa_cache_v3). After it: N1 = run_research.py --minutes 20 --workers 4 --dataset norman --worker-provider mock
  --planner-provider scripted --run-dir runs/norman_control_w4_r0 (BEFORE any Replogle file enters data/norman/knowledge).
  Then step 5 dry run + gate + build (--modality CRISPRi --min-cells 20 --alias-file norman_replogle_aliases.json),
  step 6 external_loo --protocol norman_v1, step 7 N2 runs/norman_control_replogle_w4_r0. STOP before step 8 (paid).
- Key: never ask Andres to paste it; ~/.zshenv only.

## 2026-10-11 ~13:45 UTC — Norman steps 4-7 done (all free); STOPPED before step 8 (paid)
- Feature audit v3 done (feature_audit_v3.*): exactly the two hash() features unstable.
- N1 runs/norman_control_w4_r0: selected EXP_0076 visible 0.6408, sealed 0.7170; additive baseline 0.6108 / 0.7126.
- Gate passed (91/112 training perts, 60 training singles with a Replogle row; sealed coverage 35/56).
- data/norman/knowledge/replogle2022_k562.json built (md5 d9eff528..., sign -1, 85 targets). Any Norman run now is an external arm.
- norman_v1 leave-one-out: external_stack 0.627 vs stack_inbundle 0.604, +0.023 ± 0.006, 68/112 -> passes the reading rule.
- N2 runs/norman_control_replogle_w4_r0: selected EXP_0198 visible 0.6423, sealed 0.7188 (N1 0.7170): no measurable sealed gain.
- Flagged: no sealed per-category or paired comparison is produced by a run (Lab.query_paired is never called; within-run only).
  I did NOT call the oracle. N1 has used 5 sealed queries, N2 4.
- RUNNING: Astra repeat check (fa_repeat_check.*, cache fa_cache_repeat) for brief I item 3.
- Waiting on Andres: key in ~/.zshenv (never ask him to paste it), his own words for any paid Norman arm, and running push_to_github.sh.

## 2026-10-11 ~14:20 UTC — Norman sealed reading and Astra repeat check (free); nothing running
- Lab checkout 5fe6e76a (my identical untracked norman_*.json copies moved to norman_untracked_copies/ so the pull could proceed).
- tools/sealed_reading.py over N1 and N2 -> norman_sealed_reading.md (md5 f7a2a004...) and .json. Pooled values match the runs' stored ones.
  Selected vs additive: N1 +0.004 ± 0.008, N2 +0.006 ± 0.007 (no difference). N2 vs N1: +0.002 ± 0.001, 40/16 (rule met, tiny);
  singles +0.004 ± 0.002 (not established). Run DBs unchanged in content; the empty -shm/-wal sidecars were removed by the tool.
- Astra repeat check: identical to the v3 entry (0 differing values).
- STOPPED before NORMAN_PLAN step 8 (paid). Waiting on Andres: key in ~/.zshenv, his own words for any paid arm, and running push_to_github.sh.

## 2026-10-11 ~16:20 UTC — N3 done, folders moved, everything pushed
- N3 runs/norman_ds_replogle_w4_r0 (paid, $1.03; DeepSeek ledger $32.81 of $34): agents' best visible 0.5788, sealed 0.671;
  additive baseline 0.6108 / 0.7126 is the run's reported best. Agents never built the additive prediction as a feature and
  only one plugin read the Replogle file. norman_n3_sealed_reading.md: nothing to compare (run selected its baseline).
- MOVED (Andres, 15:34 and 15:41 UTC: Gene-Mila belongs inside ~/Documents/Mila, not Loak-documents):
  ~/Documents/Mila/Gene-Mila/{gene-mila, gene-mila-2492e11, genemila_scale_logs, data_downloads}. Symlinks with the old
  names remain in ~/Documents/Loak-documents. Mila checkout untouched except `Gene-Mila/` in .git/info/exclude.
  My scripts here now use the new path. Lab checkout at f56f615c.
- PUSHED to github.com/andresloak100/Gene-Mila (the permission system allowed it after Andres asked directly):
  astra/deepseek-continuation-memory 6a3e8a8e, astra/compact-master-selection 74114d43,
  claude/mac-reports-2026-10-11 8a19e72c (68 files + docs/mac/MD5SUMS.txt). Draft PR andresloak100/Gene-Mila#3 into the lab branch.
- The DeepSeek key was pasted by Andres in the thread and used only as a process environment variable; in no file. He should rotate it.
- Running: full pytest from the new path (pytest_macos_newpath.log).

## 2026-10-11 ~18:20 UTC — N4 done (paid), nothing running
- Lab checkout 076282c7. N4 runs/norman_ds_from_n2_w4_r0: DeepSeek planner + workers, warm-started from N2
  (runs/norman_control_replogle_w4_r0), on Andres's "start the paid run" (17:47 UTC). Cost $1.164 (run cap was 1.1: overshoot 0.064).
  DeepSeek ledger now $33.97 of the $34 cap: NO budget left for another run.
- Selected EXP_0790 (ridge, 11 features): visible 0.6464, sealed 0.7264. Start model 0.6423 / 0.719; additive baseline 0.6108 / 0.7126.
- norman_n4_sealed_reading.md: selected minus additive +0.014 ± 0.008 (37/19), selected minus start +0.008 ± 0.004 (40/16):
  neither established by the pre-specified rule (needs more than twice the paired SE). pair_seen1: +0.021 ± 0.006 vs additive (established).
- The DeepSeek key was pasted by Andres in the thread (twice) and used only as a process environment variable; in no file. He should rotate it.
- Everything is on GitHub: lab branch, astra/* branches, claude/mac-reports-2026-10-11 (draft PR andresloak100/Gene-Mila#3).
