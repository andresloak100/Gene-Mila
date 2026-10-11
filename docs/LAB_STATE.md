# Lab state: read this first

The single catch-up document for any agent (Claude, Astra or another) picking up Gene-Mila. It records what the lab
is, where everything lives, what has been measured, what is in progress and what waits on Andres. Update it at every
milestone and before stopping; newest state wins. Last updated 2026-10-11 22:55 UTC.

## What this is

An autonomous research lab for single-cell perturbation prediction: an LLM planner (Claude Opus, or DeepSeek V4 Pro)
proposes hypotheses, DeepSeek workers implement each as a feature in its own git worktree, and a Python controller
schedules, guards, fits simple CPU models (ridge, Lasso, OLS) and scores them. Numbers decide, never an LLM. Goal set
by Andres (GitHub andresloak100): a paper-grade result evaluated like CellForge (arXiv 2508.02276v2) and VCWorld, on
CellForge's datasets: Adamson 2016 first, then Norman 2019 and Srivatsan sci-Plex 3. No GPU anywhere, so deep models
appear only as reported rows. Design: docs/ARCHITECTURE.md. Every prompt, built-in feature and control:
docs/PROMPTS.md.

## Where things live

- **Code:** branch `claude/autonomous-research-system-3k435s` of github.com/andresloak100/Gene-Mila, the repository's
  default branch (there is no `main`, so pull requests target this branch). AGENTS.md and HANDOFF.md (PR #2) are
  merged; draft PR #1 (README design) is being updated to merge.
- **Astra's code** is on GitHub as two branches, unchanged, both from lab commit 8261c57:
  `astra/deepseek-continuation-memory` (6a3e8a8e; 28 files, +2,844) and `astra/compact-master-selection` (74114d43;
  43 files, +5,127, contains the first); her clones on the Mac are in ~/Documents/Codex/2026-10-08/pl/work/. No pull
  request; merging is Andres's call.
- **Data and runs:** only on Andres's Mac, in ~/Documents/Mila/Gene-Mila/ since 11 Oct 2026 (moved out of
  ~/Documents/Loak-documents at his request; ~/Documents/Mila is his checkout of andresloak100/Mila, whose
  .git/info/exclude holds `Gene-Mila/`, and nothing else in it may be touched). Lab checkout gene-mila (.venv inside),
  run directories under its runs/, logs and Mac-side reports in genemila_scale_logs (a STOP file there halts a running
  driver; progress.md and STATE.md; `python handoff_state.py` prints live state), external downloads in
  data_downloads, the old-code worktree gene-mila-2492e11. Symlinks with those four names stay in
  ~/Documents/Loak-documents because run configs, bundle manifests, the .venv's scripts and Astra's runs record the old
  absolute paths; write nothing new there. Cloud sessions have no data, cannot reach Zenodo or api.deepseek.com, and
  have no DeepSeek key.
- **Results files:** generated on the Mac and committed under docs/results/ byte for byte (md5-verified); the
  Mac-only reports, run summaries and configs are under docs/mac/ (PR #3, md5 list docs/mac/MD5SUMS.txt). New reports
  reach GitHub by pasting (md5-checked) or by the Mac's push script,
  `bash ~/Documents/Mila/Gene-Mila/genemila_scale_logs/push_to_github.sh --check-only` first.
- **Team-facing pages (private claude.ai links):** results page https://claude.ai/artifact/5MsYpCgiUhah3aXuTLYPwg
  (version 8, 28 runs), editable summary https://claude.ai/code/artifact/6668e638-6fec-499d-ad9d-e68c78d95477;
  text source docs/results/summary_for_collaborators.md.

## Rules every agent follows

- The DeepSeek key: Andres keeps it in ~/.zshenv on the Mac as API_KEY (11 Oct 19:22); each run gets it as
  `DEEPSEEK_API_KEY="$API_KEY" <command>`, in its own process environment only. Never print, log, commit, quote or
  ask for it. He pasted keys in chat at 15:34 and 17:48 and asked that the second be used ("use the same key", 19:17).
- Paid work (DeepSeek, or a planner run) starts only on Andres's own words. On 11 Oct 19:10 to 19:16 he put the rest
  of his DeepSeek balance at the lab-code owner's disposal ("you can spent as much as u want and you think is
  necessary we have in total 33 in deep seek"; "keep improving the model spent those dolars well"); the console then
  showed $33.01 left and $16.98 billed. Shared ledger: runs/spend_ledger.sqlite in the Mac checkout, **$33.97 after
  N4** (11 Oct 18:08; $31.78 before the two Norman runs; Astra's two campaigns about $21.50); it counts about twice
  what DeepSeek bills (likely off-peak pricing; not checked call by call) and is never repriced. Spending goes in
  pre-specified blocks: the current one, docs/PLAN_AFTER_N4.md, lets the ledger reach $48 and starts a run only when
  the ledger plus its own caps stays within it. `budget.max_total_usd` caps a run's workers only and
  `budget.max_planner_usd` its planner (default derived: $5.33 for 4 workers and 20 minutes). Earlier caps: $15,
  then $34 (02:39 UTC 11 Oct). Claude usage is limited and shared.
- The sealed held-out perturbations (val2) are read only through `genemila.benchmark.oracle.QueryOracle`, never to
  choose a model, feature, penalty, rule or protocol. Analysis tools read visible data only, and tests assert that
  tool sources never name the sealed files. The Adamson sealed set has been scored for dozens of finalists across
  about 30 runs, so any new number on it is one more look at a used set; Norman, or a new split, is the clean test.
- Every arm is labelled by code version and never pooled with another (tables generated by tools/results_table.py
  and tools/scaling_report.py from run outputs). Report spread next to means; never claim a difference inside the
  noise; never headline all-gene PCC (plain OLS reaches 0.985).

## Results so far (Adamson, CellForge's seed-42 split: 50 training, 17 visible validation, 21 sealed perturbations)

Sealed pearson_delta (Pearson correlation of predicted and measured expression change over 2,055 genes):

| what | sealed pearson_delta | source |
|---|---|---|
| start: OLS on the three built-in features | 0.520 | docs/results/results_table.md |
| scripted no-LLM control, seven hand-written hypotheses | 0.553 to 0.554 | same |
| scripted control plus a hand-written transfer feature | 0.593 | docs/NEXT_LEVER.md |
| agent arms, 1 / 4 / 8 / 16 workers (Opus planner) | 0.566 / 0.602 / 0.584 / 0.577 | docs/results/scaling.md |
| Astra's two DeepSeek continuation campaigns (8 workers, 2 h each) | 0.599 to 0.602 | Astra's notes on the Mac |
| scripted no-LLM control with the Replogle 2022 screen (control_replogle_w4_r0, one run, labelled arm) | 0.621 | Mac report, 11 Oct 02:55 UTC; files on the push list |
| no-LLM continuation of newcode_opus_w4_r0 with the Replogle screen (control_replogle_from_opus_r0, one run) | 0.638 (ensemble 0.640) | Mac report, 11 Oct 03:20 UTC; files on the push list |
| the same with the kernel-ridge Replogle feature (control_replogle3_from_opus_r0, code 89ab4fb, one run) | 0.646 (ensemble 0.646) | Mac report, 11 Oct 03:50 UTC; files on the push list |
| best of any run without an external screen | under 0.604 | |
| noise ceiling (a perfect predictor, limited by cell sampling) | 0.89 (training) / 0.94 (visible validation) | docs/results/ceiling_analysis.md, docs/results/noise_ceiling.md |
| transfer ceiling (best mix of other perturbations' responses, with hindsight) | 0.73 to 0.78 | same |

The first lever with evidence of new information is an external screen (visible data only, leave-one-out over the
50 training perturbations, docs/results/external_loo_replogle2022_k562.md):

| predictor (leave-one-out, training perturbations) | pearson_delta mean ± sd | paired gain vs gene-set kNN |
|---|---|---|
| mean response of the other perturbations | 0.474 ± 0.261 | -0.071 ± 0.019 |
| gene-set kNN (close to what the agents found) | 0.545 ± 0.264 | |
| Replogle 2022 response of the same target | 0.461 ± 0.211 | -0.084 ± 0.035 |
| kNN weighted by Replogle response similarity | 0.572 ± 0.257 | +0.027 ± 0.017 |
| ridge stack of the four | 0.616 ± 0.233 | +0.072 ± 0.020 (better for 34 of 50) |

The same stack without the two external columns scored 0.543 on the Mac, so the gain comes from the screen. Rebuilt with 97 gene renames matched by Ensembl id (83 targets with a row, 2,035 of 2,055 genes; FECH dropped under the 20-cell minimum; ATP5B and SLMO2 rescued), the result holds: stack 0.616, +0.071 ± 0.021 over gene-set kNN, better for 35 of 50 (docs/results/external_loo_replogle2022_k562_v2.md); with the wider alpha grid, a second look, 0.620, +0.075 ± 0.020, 37 of 50, alpha 10,000 in every fold (..._v2_widegrid.md). Kernel ridge through the screen (external_krr, added after the first reading, so a second look; ..._v3.md, md5 a727c156aed42757b2cdc0578bca2694, code 89ab4fb): 0.590 as a single predictor against 0.568 for the Replogle kNN (+0.022 ± 0.010, better for 29 of 50) and 0.590 against 0.545 for gene-set kNN (+0.045 ± 0.015, 33 of 50), lambda 0.1 or 0.3 in every fold; stacked with the other four columns it adds nothing (0.614 against 0.616, -0.001 ± 0.007): the screen's information is already used by the four-column stack.

Readings: only "4 workers beats 8" is significant (p = 0.01); cost rises linearly with workers; Opus and DeepSeek V4
Pro plan equally well when DeepSeek finds response transfer (it did in one of two runs). The whole gain over the
start is one feature family, transfer of responses from related knockdowns. Agents beat every baseline on all six
held-out metrics; against the control with the hand-written transfer feature they lead only on the DE genes.

**Against CellForge (asked by Andres 11 Oct 02:48 UTC).** Side by side with CellForge's reported Adamson row
(arXiv 2508.02276v2 Table 1), tonight's best model (the scripted control with the Replogle screen) reads PCC all genes
0.990 vs 0.988 ± 0.046, MSE_DE 0.084 vs 0.201 ± 0.044, PCC_DE 0.964 vs 0.947 ± 0.060, R²_DE 0.848 vs 0.891 ± 0.052.
This is not a valid comparison and must not be reported as "beats CellForge": their evaluation code is unpublished
and no metric definition reproduces their own baseline rows (docs/results/results_table.md), their split holds out
guides, not genes (6 of 21 test genes have another guide in training), their spreads exceed the differences, and
all-gene PCC is saturated (our 3-feature start already scores 0.984). The comparable statement is against baselines
rerun on our split with our code: DE-gene MSE 0.084 vs 0.160 and R² 0.85 vs 0.71 for linear regression. A real
claim needs CellForge's model run through our evaluation on our split (a GPU). pearson_delta cannot reach 0.99 for
any model here (noise ceiling 0.94). Asked again 11 Oct 17:10 UTC; the side by side with the current best models,
CellForge's reported row against ours: Adamson (control_replogle3_from_opus_r0, sealed) MSE 0.0051 / 0.0044, PCC
0.9883 / 0.9902, R² 0.9761 / 0.9787, MSE_DE 0.2013 / 0.0735, PCC_DE 0.9474 / 0.9698, R²_DE 0.8912 / 0.8683; Norman
(N2, norman_control_replogle_w4_r0, sealed, our own gene-held-out split) MSE 0.0034 / 0.0054, PCC 0.9846 / 0.9887,
R² 0.9609 / 0.9746, MSE_DE 0.1736 / 0.1104, PCC_DE 0.8109 / 0.9374, R²_DE 0.5975 / 0.8424. Ours is ahead on 5 of 6 in
each, but on Norman the additive rule alone (no model) scores PCC_DE 0.941 and R²_DE 0.846 against their 0.811 and
0.598, which says the two evaluations differ rather than that our method is better. The statement we can make: a
ridge regression on a few interpretable features, fitted on a CPU in minutes, matches or exceeds CellForge's reported
numbers on five of six metrics under our splits; the evaluations are not verified to be equivalent.

## Levers tested and closed (all free unless noted)

- More workers, longer runs (86 percent of a run's gain comes by its midpoint: docs/results/time_to_best.md), a
  DE-aware selection rule (one paid run, negative: docs/results/selection_replay.md), a hand-written transfer feature
  (redundant with the agents' features).
- Astra's continuation campaigns: +0.003 held-out for about $21.50; models grew from 12 features to 176 columns.
- A learned target similarity from the knowledge files: +0.010 leave-one-out, inside the noise
  (docs/results/learned_kernel_experiment.json).
- Refitting every run's finalists on all 67 visible perturbations (tools/refit_visible.py): -0.003 +/- 0.010 held-out;
  among the 14 agent-derived runs 6 up, 8 down. More labels of the same kind do not help. Report on the Mac
  (genemila_scale_logs/refit_visible.md, md5 a324302d30d580e6718d9d7029c16e16), not yet pushed.
- Averaging two runs' predictions (arm ensembles) gains 0.01 to 0.03 on the used sealed set; not a clean result.
- Noise ceiling on the 17 visible validation perturbations (tools/noise_ceiling.py with the cell counts from
  tools/count_target_cells.py): 0.944 (docs/results/noise_ceiling.md; the first run's 0.902 used only the 300 stored
  cells and was a lower bound); the 28 runs' selected models reach 0.56 to 0.66 there. The largest gaps (XRN1, PSMD4,
  SOCS1, MARS) are knockdowns with no close relative among the training targets.
- Feature count: three features match the twelve-feature model (0.577 against 0.583 out of fold); the pool is
  saturated by near-duplicates (docs/results/compact_model_curve.md).

Conclusion: the limit on this bundle is information about the targets, not search, data size or model size.

## In progress (2026-10-11)

0. **The paid block after N4 (docs/PLAN_AFTER_N4.md, written 19:15 to 19:45 UTC, reviewed independently before
   any result; amended 20:30 UTC: the gene-clustering ratio of the arm reading is now overlap-robust, since the
   leave-one-gene-out jackknife first specified counts a pair twice and reads about 1.41 where it should read 1).**
   B1: three repeats of N4 on its code 076282c (seeds 1 to 3; r1 started 19:16:54, $1.436, read: selected model
   0.719 sealed; r2 0.726, r3 0.711; the last ended about 21:08 UTC, ledger $38.08). B1's primary reading: the arm
   against its start G −0.0000, SE 0.0071, no difference established, so the agents' search adds nothing; its
   combined model scores 0.723 sealed, +0.0041 ± 0.0011 over N2's selected model (better on 38 of 56) and +0.010 ±
   0.007 over the additive rule (not established); details in docs/NORMAN_PLAN.md section 8 and PR #6; N4 is not in the
   arm because its planner ran out at 18.7 of 20 minutes (the $34 cap bound; summary.json `planner.mixed`), so it
   is its own arm "(lost its planner)". B2: a free no-LLM control on the additive start, then three fresh DeepSeek
   runs from it (the control and seed 0 passed; seed 1 was killed by run_research.py's watchdog while finishing, is
   its own arm and stopped the block; seeds 2 and 3, with --no-watchdog and a 90-minute backstop, are to complete the arm;
   plan note of 22:50 UTC). B3, dropped from this block when seed 1 stopped it: an Adamson re-split (gene mode, seed 20261011; not a clean test, since every Adamson
   perturbation's labels or sealed scores were used in development; only the agents-versus-control contrast is
   read). Each arm's deliverable is its combined model, the average of its runs' selected models; for Norman the
   delivered model is B1's unless B2's scores higher on the visible validation perturbations. One primary reading
   per block, by the arm rule (G against k·SE, SE = sqrt(S² + sd_g²/R), one sign, most wins), with Norman's SE
   inflated by a gene-clustering ratio estimated on visible labels. Tools: tools/sealed_reading.py (fresh starts,
   --versus, the clustering ratio, the planner record) and tools/arm_reading.py (the rule, the combined model).

1. **External K562 screen (Andres chose Replogle 2022 on 11 Oct).** Downloaded on the Mac
   (ReplogleWeissman2022_K562_gwps.h5ad, Zenodo 13350497, md5 13db594f8f1d2ccb88fec44a13e414dc) and built into
   data/adamson_cf/knowledge/replogle2022_k562.json there: 82 bundle targets with a row, 1,938 of 2,055 genes
   measured. Leave-one-out result above. Done in code since: a run whose bundle holds knowledge files added after the
   build records them (run.external_knowledge) and is its own arm, "... (external knowledge: replogle2022_k562)", so
   it is never pooled with earlier runs; the builder takes gene renames (--alias SLMO2=PRELID3B, SRPR=SRPRA,
   ATP5B=ATP5F1B; the first build missed SLMO2 and SRPR for that reason) and drops targets with fewer than 20 cells
   (--min-cells; FECH had 6); tools/external_loo.py takes --alpha-grid (the stack chose the largest pre-specified alpha,
   1000, in all 50 folds, so a wider grid is a second look and the report says so); the scripted no-LLM control adds
   two fixed hypotheses per external screen (same-target response, kNN by external similarity). Next, all free on the
   Mac: rebuild with the aliases, rerun the leave-one-out with a wider grid, then one scripted control run with the
   file (a labelled arm; one more look at the used sealed set). The rebuild and both leave-one-out readings are done
   (02:30 UTC; knowledge file md5 2a1b40429977ed9be1239dc48c883515, alias table genemila_scale_logs/replogle_aliases.json
   on the Mac). **Control result (control_replogle_w4_r0, code 074c239, 264 s, 348 experiments, no LLM, ledger
   unchanged):** selected model EXP_0076 (ridge, alpha 23,409; features mean_response, is_target, external_knn,
   external_direct, target_level, response_components, shared_module) scores visible 0.625, sealed pearson_delta 0.621,
   MSE_DE 0.084, PCC_DE 0.964, R2_DE 0.848, against 0.593 / 0.142 / 0.943 / 0.755 for the control without the file
   and 0.599 / 0.117 / 0.955 / 0.803 for the Opus agent run newcode_opus_w4_r0; three finalists agree (0.6214 to
   0.6217); each external feature alone lifts the visible score from 0.501 to 0.570 (direct) and 0.582 (kNN). How far
   to trust it: one run on a sealed set already read many times; the pearson_delta gain over the agents (about 0.02)
   is the size of the run-to-run spread, the DE-gene gains are larger; Norman, or a fresh split, is the clean test.
   summary.json md5 6a79a78d33e030a2fb08fa6d60a4972c (on the push list).
   **Combination (control_replogle_from_opus_r0, code c903c1a, free, full 1,200 s, 483 experiments):** the scripted
   control continued from newcode_opus_w4_r0 with the Replogle hypotheses; selected EXP_0416 (ridge, alpha 14,872,
   13 features: is_target, both Replogle features, target_level, shared_module and eight of the agents' transfer
   features) scores visible 0.647, sealed pearson_delta 0.638, MSE_DE 0.078, PCC_DE 0.968, R2_DE 0.863, all-gene
   PCC 0.990; the other finalists 0.640 and 0.641. Same caveats: one run, used sealed set. summary.json md5
   203d99f4d0fbcaebcccaf135ad9ab39d. It was the warm start for the paid run B (chosen on visible score: 0.647 vs
   0.625) until the kernel-ridge run below scored higher on visible. A paid agent arm with the file needs
   Andres's words (card posted 02:22 UTC in the build thread). external_krr (kernel ridge through the screen: signed
   weights on the other training responses, kernel = Pearson correlation of the targets' external rows, lambda by an
   inner leave-one-out) now exists both as a leave-one-out predictor in tools/external_loo.py, with
   external_stack_krr (the stack plus that column), both appended after the five pre-specified predictors and
   reported in their own "second look" section (old JSON twins re-render unchanged; the full analysis took 12 s on a
   synthetic 50 x 2,055 case in the cloud), and as a third scripted-control template and hypothesis
   (external_krr_<file>, so a control with the file from this code on is a new arm; docs/PROMPTS.md section 5); it
   was added after the first reading. On real data (leave-one-out, visible only, docs/results/
   external_loo_replogle2022_k562_v3.md) it beats the Replogle kNN as a single column (0.590 vs 0.568) but adds
   nothing to the stack (0.614 vs 0.616).
   **With kernel ridge (control_replogle3_from_opus_r0, code 89ab4fb, free, full 1,200 s, 469 experiments, 20
   duplicates, 1 failed; config byte-identical to control_replogle_from_opus_r0, so the code version, recorded as
   base_commit in summary.json and appended to the arm label by the results table, is what separates the two arms):**
   selected EXP_0466 (ridge, alpha 14,434, 12 features: is_target, external_direct, external_krr, target_level,
   is_target_x_control_mean, and seven of the agents' transfer features: knn_response_symbol_family,
   knn_two_hop_response_cluster, knn_response_ppi_diffusion, normalized_mean_response, rwr_target_proximity,
   knn_response_geneset, shared_module) scores visible 0.657 (MSE_DE 0.048, PCC_DE 0.977, R2_DE 0.934), sealed
   pearson_delta 0.646, MSE_DE 0.0735, PCC_DE 0.970, R2_DE 0.868, all-gene PCC 0.990; all four finalists and the
   ensemble give 0.646. The visible selection replaced external_knn with external_krr. Added alone to the three
   built-in features, the Replogle features lift the visible score from 0.501 to 0.570 (direct), 0.582 (kNN) and
   0.603 (kernel ridge). No LLM calls, ledger unchanged ($31.778). summary.json md5
   89538745c528903098b3470d61d74e92, analysis log md5 1ab591c844f3536297d1486947006481, config.json md5
   9743f34b8177420715a44442294787e9 (all on the push list). How far to trust it: this is the fourth look at the
   used sealed set tonight, each from a new arm, so the sealed numbers grow more optimistic as evidence; the visible
   scores rose in step (0.625, 0.647, 0.657), and the gain over control_replogle_from_opus_r0 (+0.008) is inside
   run-to-run spread. Norman, or a fresh split, is the clean test. This run is now the warm start for the paid run
   B (highest visible score).
2. **Compact model rules (Andres's ask, 11 Oct 00:32 UTC):** a box of failed features that agents cannot re-propose; an
   admission rule (a feature joins only if its gain beats the fold noise, checked under two fold seeds); a redundancy
   check that rejects a feature correlating above 0.9 with one already in the model before it is fitted; a
   deterministic curator that keeps the smallest feature set within noise of the best and asks workers to merge
   near-duplicates; a monitor that closes a direction after two failures on the visible cross-validated score, never
   the sealed one. Astra's unpushed branch already has a feature board (master and worker roles), a failure archive,
   in-fold Lasso screening, a curator and a compact incumbent, never run on real data; it lacks the admission
   threshold, the second fold seed, the redundancy pre-check and the monitor. Plan: push Astra's branch, review and
   merge it into the lab branch, add the four missing rules. tools/feature_audit.py is committed (6a2eb65; visible data only by default; per run: redundancy clusters, single-feature and drop-one scores, Lasso stability, a one-SE compact set chosen on training out-of-fold scores and checked on the visible validation perturbations, and a failed-feature box a lab component can import); all 30 runs audited on the Mac (11 Oct, about 45 min of computing; the 28 table runs on code 7010889, Astra's two on 89ab4fb, tools/feature_audit.py identical in both; no sealed scores). Result, docs/results/feature_audit.md (md5 fd691105506db73b7e62e492221e0784; the JSON, 4.75 MB, md5 dae9e03f95bc26b5a37ec5c935413880, and the feature box, md5 e20be2838e9a905b3347cdff36fdd37e, are on the push list): the compact model keeps a median of 5 of 16 features, but on the 17 validation perturbations it is within one paired SE of the full model in 8 of 15 agent runs and lower in 7 (mean -0.0074; the two 16-worker runs -0.033 and -0.024), so pruning does not raise accuracy, as the 00:38 UTC check found. Of the 269 selected-model features outside their compact sets, 207 add nothing measurable, 30 are redundant copies, 15 substitutable, 17 harmful. Astra's second campaign: 87 features, 176 columns, rank 91, effective rank 11.2, 11 duplicate and 16 constant columns, 178 pairs with |r| >= 0.9; its search mostly re-mixed the same information (about 40 random-projection and random-Fourier variants of existing features); its compact set starts from random_projection_all_features_e2763, 50 columns projecting other features, which alone scores 0.594 against 0.598 for the full model. Two tool issues found and fixed (01483d9, review fixes 53ed1cb; AUDIT_FORMAT 3): a composite feature that calls ctx.feature(...) counted as one feature and its inputs could be boxed although the kept composite needs them (now verdict required_input, never boxed, listed in the box file with each run's dependency map; compact and full sizes reported with inputs expanded); the merge-test "min abs r" was the minimum over every pair of a single-linkage cluster (0.010 printed for a cluster defined at 0.9; now the weakest link, >= 0.9). Rerun with the fixed code (6eb17a2, 39 min, docs/results/feature_audit_v2.md, md5 16d0c0d9c955a6e51eea647d576787db; JSON md5 d89f7154d91418073ef6bec4d4518932 and box md5 9f413372df158ac3b34d71aaa2c73fee on the push list; use this box, not the first one): 35 features of the selected agent models are required inputs of kept composites, all in Astra's two runs, so her compact models honestly compute 31 features (83 columns) and 49 features (120 columns), not 1 and 20; the compact model is within one paired SE of the full model on validation in 9 of 15 agent runs and lower in 6 (mean -0.0073). Two rows changed although composites do not apply to them (scale_w8_r0 full 0.5762 to 0.5767; newcode_ds_w4_r0, the run whose stored score the audit never reproduced, compact 5 to 3 features), and two backward-path steps removed a different one of two perfectly correlated features: the cause (two identical audits on the Mac at 8c3b374 disagreed too) is one agent-written feature in each run that uses Python's builtin hash() of a perturbation name as a number (contrastive_near_far_transfer_e258 in scale_w8_r0, target_degree_times_gene_response_e521 in newcode_ds_w4_r0, the run marked † because the audit never reproduced its stored score): str hashes are salted per process, so these features are noise that differs in every process, and the smoke test, which checks determinism within one process, let them through; with PYTHONHASHSEED=0 every block is identical across processes. Fixed in 3d7c519 (reviewed, 361 tests pass): the plugin guard refuses hash(), .__hash__, id() and iteration over a set of objects in new agent plugins, with a message naming the stable replacements (sorted order, ctx.gene_index, zlib.crc32 or hashlib); every experiment process runs with PYTHONHASHSEED=0 (sandbox.HASH_SEED, recorded as run.hash_seed; a run directory recorded with another seed is refused); feature_audit.py, refit_visible.py and compact_model_curve.py re-execute themselves under that seed; the audit (AUDIT_FORMAT 4) recomputes each feature's full-training block in fresh processes under seeds 0, 1 and 2 and gives one whose block differs the verdict unstable (never kept, always boxed); a warm start runs every imported plugin through today's guard with id() allowed (past plugins use it as a cache key) and refuses a hash() plugin and any plugin computing it. Audit v3 on the Mac (02e7021, fresh cache, same 30 runs, 54 min; docs/results/feature_audit_v3.md, md5 55c6fcc7bba4248782efe3758f91ecaf; JSON md5 a1818f09a8f3a9670dec0d784f541338 and box md5 0c1485da4c39017a022a1cccabd7a604 on the push list; use this box): exactly the two hash() features come out unstable (each in its run's selected model and pool), no other feature in any run; with them removed the engine reproduces the stored visible scores of 28 of 28 remaining selected models; compact within one paired SE of full on validation in 8 of 15 agent runs, lower in 7 (mean -0.0074), as before. Open on it: newcode_ds_w4_r0's Lasso column went from 4/16 to 15/15 stable once the noise feature left (likely a smaller cross-validated penalty; being checked), and one backward-path step in an Astra run drops the other of two features correlated +1.000 than v2 did (numbers unchanged; a rerun of that run under v3 checks the audit now repeats itself). Scan of all 33 runs' feature stores (5,553 plugin files, static, genemila_scale_logs/nondeterminism_scan.md, md5 ce2350c3793c3cb334a4000b61b0e74f, on the push list): 84 hash() lines, 85 id(), 3 unseeded np.random draws, 1 __hash__; 72 of the hash() lines are in Astra's two DeepSeek campaigns, none in a reported model. Only scale_w8_r0 and newcode_ds_w4_r0 have a hash() feature in a reported model (selected model and other sealed finalists); the id() hits in reported models (newcode_opus_w4_r0's kernel_ridge_annotation_embedding_e430 and seven others) are cache keys into a per-context dict or counts of distinct objects, read one by one and harmless. The 0.646 model (control_replogle3_from_opus_r0), 0.621 and 0.638 are clean. Visible pearson_delta of the two affected selected models over separate processes: scale_w8_r0 0.628 to 0.636 (stored 0.6365), newcode_ds_w4_r0 0.555 to 0.564 (stored 0.5628), identical to every digit with PYTHONHASHSEED=0: about 0.008 of spread from one feature, a third of the differences between arms, which also applies to those two runs' sealed scores (each one arbitrary draw); their rows in the results tables need that footnote when the tables are next regenerated. The static scan does not see iteration over sets of strings; the cross-process block check in the audit does. Three plugins of Astra's second campaign fail to import outside her code (NameError FeatureContext), none in the selected model.
3. **Files to push from the Mac** (genemila_scale_logs/push_to_github.sh, Andres runs it): noise_ceiling.json,
   refit_visible.{md,json}, the Mac's STATE.md and notes, adamson_cf_ncells.json, the Replogle build report,
   external_loo JSON and the stack control without external columns, external_loo_replogle2022_k562_v3.json (md5
   b527a1128ee4166c9e59389b6f1e10a9), the control_replogle3_from_opus_r0 config, summary and analysis log,
   feature_audit.json and feature_audit_feature_box.json, and Astra's two branches. The whole list exists on disk as of
   04:00 UTC, so the script can run now.

## Waiting on Andres

- **Rotate the DeepSeek key** when he chooses (pasted in the thread at 15:34 and 17:48 UTC 11 Oct; it went only into
  run process environments and is in no file or commit; the key now comes from his ~/.zshenv).
- **N4 (done 18:08 UTC 11 Oct, $1.16; pre-specified in docs/NORMAN_PLAN.md section 8, started on his typed "start
  the paid run" at 17:47):** the DeepSeek agents continued the no-LLM control N2 for 20 minutes with 4 workers.
  Selected EXP_0790 (ridge, alpha 50,000, 11 features: five of N2's six plus the agents' own copy of the additive
  sum, a one-number version of the Replogle feature and four that added 0.0000 when tried). Sealed pearson_delta
  0.726, the best Norman number so far, against 0.719 for its start (N2's model) and 0.713 for the additive rule;
  MSE_DE 0.129, PCC_DE 0.928, R2_DE 0.819 against 0.102 / 0.941 / 0.846 for the rule. Pre-set paired reading
  (docs/results/norman_n4_sealed_reading.md): against its start +0.008 ± 0.004, better on 40 of 56, not established;
  against the rule +0.014 ± 0.008, better on 37 of 56, not established (pairs with one gene in training: +0.021 ±
  0.006, better on 22 of 27, established). So a small gain that is not proven, and worse than the rule on the
  most-changed genes (likely the heavy ridge penalty shrinking predicted changes; not yet checked).
- **The additive start model (code c6fadc0, free, no run yet):** on a bundle with pairs every fresh run now starts
  its agents from ridge on the three built-ins plus `additive_response`, the additive baseline's prediction as a
  built-in feature, so they no longer start below the rule as N3's did. Adamson is unchanged. Next, free: a no-LLM
  run on Norman measures the new start's visible score.
- **N3 (done 15:54 UTC 11 Oct, $1.03):** DeepSeek planner and workers, 4 workers, 20 minutes, Replogle file, no warm
  start. It selected its additive baseline (visible 0.611; sealed 0.713); its best agent model scored 0.671 sealed
  (visible 0.579; ridge, alpha 1000), below the additive rule and N2's 0.719. No agent fed the plain additive
  prediction to the model (the best feature multiplies it by a per-perturbation factor) and only 1 of 355 plugins read
  the Replogle file; details and the prompt changes made since in NORMAN_PLAN section 8.
- **Pull requests:** all merged 11 Oct: PR #2 (AGENTS.md, HANDOFF.md), PR #1 (README design, ca35f88; Andres chose
  "Merge both" at 15:52 UTC), and the Mac's reports, PR #3 and PR #4 (N4), each md5-verified against its
  docs/mac/MD5SUMS file and scanned for keys. Astra's two branches are on GitHub
  unchanged, with no pull request: merging them is his call. Still his: a `main` branch, if he wants one.
- **Norman 2019: Claude takes it** (Andres chose "Claude now" on the build-thread card at 12:02 UTC 11 Oct; the Mac
  was briefed at 12:05 UTC for section 6 steps 2 to 7, all free; Andres typed "download norman" at 12:04 UTC).
  Steps 2 and 3 done by 12:20 UTC: file verified, every section 2 check passes, bundle built (231
  perturbations, split_a391fa9e7b4eccb7); details and three decisions (old symbols, cell-quality flags, modality)
  in docs/NORMAN_PLAN.md section 8. Steps 4 to 7 done by 13:36 UTC, all free (section 8 has the numbers): the
  Replogle gate passes (81% of training perturbations covered); the pre-specified norman_v1 leave-one-out passes
  its rule (external_stack +0.023 ± 0.006 over stack_inbundle, better on 68 of 112), so the screen adds
  information on Norman too; but on the sealed set the scripted control with the screen (N2) scores 0.7188
  pearson_delta against 0.7170 without it (N1) and 0.7126 for the additive baseline, a +0.002 that is no finding
  (its selection kept the flipped direct response and left out the kernel-ridge feature). Paired sealed
  readings (docs/results/norman_sealed_reading.md): N2 minus N1 +0.002 ± 0.001, better on 40 of 56, passes the
  rule pooled in the expected direction, singles not established; neither control beats the additive baseline
  pooled (+0.004 and +0.006, within error; +0.012 on pair_seen1), while on visible and out-of-fold
  perturbations they led it by +0.030: selection overfits the perturbations it chooses on. Before that: plan items 1 to 13 of section 4 and the `norman_v1` leave-one-out are
  implemented and reviewed, see the commit after b63491d; every new behaviour is gated on a bundle with pairs, a
  recorded modality or a gene split, and a frozen-output test (tests/data/adamson_text_b63491d.json) pins Adamson's
  prompts, scripted hypotheses and templates; on the Mac's macOS suite (anndata 0.13.4, pandas 3) nine
  external-screen tests failed because anndata 0.13 writes string indexes as encoded groups, fixed in ff4318b,
  which also adds pytest.ini so run directories' worktree copies of tests/ are not collected; the Mac reruns the
  fixed feature audit as feature_audit_v2 (free); next on the Mac: section 6 steps 2 to 7, free); either follows docs/NORMAN_PLAN.md (gene-grouped split, order-independent pair labels, additive
  baseline, sign-aware Replogle features for CRISPRa, a pre-specified leave-one-out, run order). The download needs
  his words in the build thread. Srivatsan needs new drug and dose ingestion.
- Answer the comment in the summary doc.

## Next after Adamson

Norman 2019 (NormanWeissman2019_filtered.h5ad on Zenodo 13350497) is the first clean test of everything above, then
Srivatsan sci-Plex 3. The timeline given on 05 Oct (a three-dataset result around 10 to 12 Oct) has slipped: Norman
started on 11 Oct (N1 to N4 above and in docs/NORMAN_PLAN.md section 8); Srivatsan has not.
