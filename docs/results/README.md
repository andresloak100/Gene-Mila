# Results index

Every file here is a record produced by a run or a tool on Andres's Mac and committed as it was on disk: never edited,
never deleted; a new check gets a new file. Every number in the README traces to one of these files
(`tools/readme_check.py`). A `.md` and `.json` pair is one result (the `.md` is the reading, the `.json` the numbers).

The block-directory convention applies to future readings. The G, corrected F and H8 records below retain the exact generated paths pinned in their pre-score commands and hash manifests; their already referenced files were not moved or overwritten. They are indexed one row per reading; the per-file list, with hashes, is the publication's manifest (below).

## Linear AE: fixed Adamson baseline (30 October 2026)

Read [the report](linear_ae_adamson.md) ([full-precision JSON](linear_ae_adamson.json)) and [the complete receipt index](linear_ae_adamson/README.md). One deterministic CPU run at the prescribed defaults and one bridge call exited 0. Pearson delta is 0.485442177; the prescribed lab comparator (newcode_opus_w4_r0:EXP_0441, 0.598665038) meets the paired rule on 21 conditions. All 50 training targets were used, with no fallback predictions. The report records the approved corrected GEARS export's path and SHA-256, its cohort caveat, and the worn sealed interpretation. Raw predictions and input remain outside Git; there is no seed SD or parameter selection.

## GEARS: fixed CPU seeds on Adamson (28–29 October 2026)

Read [the three-seed report](gears_adamson/aggregate.md) ([full-precision JSON](gears_adamson/aggregate.json)). All training and the once-per-seed prescribed bridge calls exited 0. Sealed pearson_delta is 0.407282874 ± sample SD 0.011648347. The prescribed lab comparator (newcode_opus_w4_r0:EXP_0441, 0.598665038) meets the paired rule against every GEARS seed. The sealed cohort is worn and descriptive; the corrected export's additional training cells and controls are disclosed.

| Files | What they are |
|---|---|
| [gears_adamson_s0.md](gears_adamson_s0.md), [JSON](gears_adamson_s0.json) | Unchanged score tool report for seed 0 |
| [gears_adamson_s2.md](gears_adamson_s2.md), [JSON](gears_adamson_s2.json) | Unchanged score tool report for seed 2 |
| [gears_adamson_s3.md](gears_adamson_s3.md), [JSON](gears_adamson_s3.json) | Unchanged score tool report for seed 3 |
| [gears_adamson/](gears_adamson/README.md) | Every environment, training, graph, prediction validation, scoring, command, exit, runtime, issue and publication receipt, individually indexed and hashed; raw inputs/predictions/work remain outside Git |

## C2: CellForge checkpoint-edited matched attempt (30–31 October 2026)

Read [the CPU failure report](cellforge_c2/training_failure.md) ([full-precision JSON](cellforge_c2/training_failure.json)) and [every receipt](cellforge_c2/README.md). The lead reversed the earlier checkpoint-2 rejection; Andres adopted that decision, and the identical script was approved and executed once. It exited 1 before training when pandas rejected filling a categorical cell-type column with a new `unknown` category. Wall time was 4.261185541 seconds; aggregate CPU time 0.0013975094444444445 hours. No predictions or score exists. The original rejection, reversal, approval and traceback are preserved; no repair or retry followed. C2 planning cost $0.160981140 on the shared ledger. Label: “CellForge (pinned release, checkpoint plan edited to the input as its README allows)”, beside the original attempt below. Block H remains unstarted.

## Plan C: CellForge matched Adamson attempt (28 October 2026)

Read [the checkpoint review](cellforge_c/checkpoint1_review.md) ([JSON](cellforge_c/checkpoint1_review.json)). Task analysis and method design completed; the research plan was rejected before code generation because it requires inputs and processing incompatible with the supplied export. No training or score exists; B.5 remains unmet. DeepSeek ledger cost $0.161134200.

| Files | What they are |
|---|---|
| [cellforge_c/](cellforge_c/README.md) | Complete generated plan, task analysis, export receipts, source/input audit, commands, logs, meter/cap/ledger and tests; every file is individually indexed and hashed in the directory manifest. Raw exports and packages remain outside Git. |

## Adamson (4 to 11 October 2026; CellForge's split of `data/adamson_cf`)

Read first: [summary_for_collaborators.md](summary_for_collaborators.md).

| File | What it is | Produced by |
|---|---|---|
| `results_table.{md,json}` | every arm, by code version, in CellForge's Table 1 layout | `results_table.py build` |
| `cellforge_table1.json` | CellForge's published Table 1 numbers (protected; marked not comparable) | transcribed from arXiv 2508.02276 |
| `calibration_adamson_cf_val2.{md,json}` | the calibration showing CellForge's numbers cannot be reproduced under any metric definition tried (moved here from `docs/mac/` on 17 October) | `results_table.py calibrate` |
| `scaling.{md,json}` | the 1/4/8/16-worker comparison: cost, throughput, significance | `scaling_report.py` |
| `selection_replay.{md,json}` | selection-rule replay on visible data, 4 October (the `.json` moved here from `docs/mac/` on 17 October) | `tools/replay_selection.py` |
| `time_to_best.md` | when each run stopped improving, 5 October | `tools/time_to_best.py` |
| `refit_visible.{md,json}` | every scored model refit on all visible labels, scored once more on the sealed set, 11 October | `tools/refit_visible.py` |
| `ceiling_analysis.{md,json}` | noise and transfer ceilings on training perturbations | `tools/ceiling_analysis.py` |
| `noise_ceiling.{md,json}` | the noise ceiling from cell-sampling noise (input `docs/mac/adamson_cf_ncells.json`) | `tools/noise_ceiling.py` |
| `compact_model_curve.md`, `compact_model_curve_newcode_opus_w4_r0.json` | how few features the best Opus run's model needs | `tools/compact_model_curve.py` |
| `learned_kernel_experiment.json` | a learned transfer kernel against the oracle-weighted ceiling, training only | `tools/learned_kernel_experiment.py` |
| `feature_audit_v3.{md,json}`, `feature_audit_v3_feature_box.json` | the feature audit the README cites: redundancy, compact models, the failed-feature box, stable under three hash seeds (v1 and v2 are in `docs/archive/results/`) | `tools/feature_audit.py` |
| `nondeterminism_scan.{md,json}` | static scan of 33 runs' plugins for `hash()`, `id()` and unseeded random draws | `tools/nondeterminism_scan.py` |
| `external_loo_replogle2022_k562{,_v2,_v2_widegrid,_v3}.{md,json}`, `external_replogle2022_k562_v2.md` | does the Replogle 2022 K562 screen carry information the transfer features lack (leave-one-out on visible data; v3 is the final protocol) | `tools/external_loo.py`, `tools/build_external_screen.py` |

## Norman (11 to 17 October 2026; [`docs/NORMAN_PLAN.md`](../NORMAN_PLAN.md))

| File | What it is | Produced by |
|---|---|---|
| `norman_manifest.json`, `norman_splits.json`, `norman_check.txt` | the ingest manifest, the split identity (gene-grouped) and the public check of the bundle (NORMAN_PLAN sections 2 and 4) | `prepare_data.py h5ad --name norman`; the checks of NORMAN_PLAN section 2 |
| `external_loo_norman_v1.{md,json}`, `external_replogle2022_k562_norman.md` | the external-screen check on Norman (sign-aware for CRISPRa) | `tools/external_loo.py` |
| `norman_sealed_reading.{md,json}` (N1, N2), `norman_n3_sealed_reading.{md,json}`, `norman_n4_sealed_reading.{md,json}` | the pre-specified sealed readings of NORMAN_PLAN section 5 | `tools/sealed_reading.py` |
| `norman_b1_r1_sealed_reading.{md,json}`, `norman_b1_r1_sealed_reading_amended.{md,json}`, `norman_b1_r2_sealed_reading.{md,json}`, `norman_b1_r3_sealed_reading.{md,json}` | B1 ([`docs/PLAN_AFTER_N4.md`](../PLAN_AFTER_N4.md); three DeepSeek repeats of N4 at code 076282c, runs `norman_ds_from_n2_w4_r1`, `_r2`, `_r3`, records in [`docs/mac/`](../mac/README.md)): each run's selected model against its additive baseline and against its starting model, 11 October. r1 was read at tool code 203a1bd (leave-one-gene-out SE) and again, `_amended`, at d0fb635 with the overlap-robust SE of the plan's 20:30 UTC amendment, as r2 and r3 were | `tools/sealed_reading.py` |
| `norman_b1_arm_vs_additive.{md,json}`, `norman_b1_arm_vs_start.{md,json}` | the B1 arm reading: the three selected models against their additive baselines and against their starting models (tool code d0fb635; scores nothing on the sealed set) | `tools/arm_reading.py` |
| `norman_b1_combined_vs_additive.{md,json}`, `norman_b1_combined_vs_n2.{md,json}` | the B1 combined model (the equal average of the three selected members, the delivered Norman model) against the additive baseline and against N2's selected model `norman_control_replogle_w4_r0:EXP_0198` | `tools/arm_reading.py combine` |
| `norman_b2_{r0,r2,r3,control}_sealed_reading.{md,json}`, `norman_b2_r1_killed_sealed_reading.{md,json}`, `norman_b2_r{0,2,3}_versus_control.{md,json}` | B2 (fresh DeepSeek runs from the additive start at code ce1b530, runs `norman_ds_addstart_w4_r0`, `_r2`, `_r3`, and the scripted control `norman_control_addstart_w4_r0`; records in [`docs/mac/`](../mac/README.md)): each run's sealed reading, the three runs against the control, and r1, killed by the watchdog while finishing (exit 247), read on its own and deciding nothing (PLAN_AFTER_N4, note of 22:50 UTC) | `tools/sealed_reading.py` |
| `norman_b2_arm_vs_additive`, `norman_b2_arm_vs_start`, `norman_b2_arm_vs_control` (`.md` and `.json`), `norman_b2_arm_r0_r2_vs_start_reported.{md,json}` | the B2 arm (r0, r2, r3) against its additive baselines, its starting models and the control; the arm as first specified, r0 and r2 against the start, is reported beside it, not read (the addendum of 23:00 UTC) | `tools/arm_reading.py` |
| `norman_b2_combined_vs_additive`, `norman_b2_combined_vs_start`, `norman_b2_combined_vs_control`, `norman_b2_combined_vs_b1_combined` (`.md` and `.json`) | the B2 combined model against the additive baseline, its start, the control's selected model and B1's combined model | `tools/arm_reading.py combine` |
| `b2_handoff_verification_20261013.md` | Astra's verification of the B2 records, 13 October (claim #8, PR #10): completion and stop history, every run's reading, the ledger; no new run, spend or sealed scoring. Its md5 is in `docs/mac/MD5SUMS_b2_verification_20261013.txt` | Astra, from the readings above and the Mac's logs |
| `norman_b1_frozen_test_review_20261013.{md,json}` | frozen B1: the saved held-out evaluation, model and source hashes (PR #13) | saved evaluation, 13 October |
| `norman_frozen_export_20261013/` | the frozen B1 export and its independent verification (PR #19); read `report.md` first | `tools/frozen_model.py`, `verification_driver.py` |
| `b1_development_diagnostic_20261013/` | the fixed B1 recipe diagnosis on training gene folds; reading [`docs/B1_DIAGNOSTIC_RESULTS.md`](../B1_DIAGNOSTIC_RESULTS.md) | `tools/b1_development_diagnostic.py` |
| `b1_two_member_test_20261013/` | the fixed two-member screen; reading [`docs/B1_TWO_MEMBER_RESULTS.md`](../B1_TWO_MEMBER_RESULTS.md); `run_with_deadline.py` is executed by `tests/test_b1_two_member_test.py` | `tools/b1_two_member_test.py` |
| `norman_development_shrinkage_20261013/` | the training-only shrinkage diagnostic of the four built-in additive-ridge features, 13 October (claim #15, PR #17; plan [`docs/NORMAN_SHRINKAGE_PLAN.md`](../NORMAN_SHRINKAGE_PLAN.md)); read `report.md` first; run `gene-mila-shrinkage/runs/norman_development_shrinkage_20261013` in Astra's workspace, $0 | `tools/shrinkage_diagnostic.py` |
| `b1_nested_blend_20261013/` | one nested error-calibration weight blending additive with the fixed r1+r2 mean, rejected by its predeclared gate (claim #30, PR #31); reading [`docs/B1_NESTED_BLEND_RESULTS.md`](../B1_NESTED_BLEND_RESULTS.md); run `gene-mila-nested-blend/runs/b1_nested_blend_20261013`, $0; `run_with_deadline.py` is executed by `tests/test_b1_nested_blend.py` | `tools/b1_nested_blend.py` |
| `b1_r2_regularization_20261013/` | r2's ridge penalty fixed at 20000 (r1's), rejected by its predeclared gate (claim #32, PR #33); reading [`docs/B1_R2_REGULARIZATION_RESULTS.md`](../B1_R2_REGULARIZATION_RESULTS.md); run `gene-mila-r2-regularization/runs/b1_r2_regularization_20261013`, $0; `run_with_deadline.py` is executed by `tests/test_b1_r2_regularization.py` | `tools/b1_r2_regularization.py` |
| `b1_pair_batch_20261013/` | a per-pair fallback in the r2 prior-edge feature (`pair_target_prior_edge_e34` version 3), rejected by its predeclared gate (claim #34, PR #35); reading [`docs/B1_PAIR_BATCH_RESULTS.md`](../B1_PAIR_BATCH_RESULTS.md); run `gene-mila-pair-batch/runs/b1_pair_batch_20261013`, $0; `run_with_deadline.py` is executed by `tests/test_b1_pair_batch_correction.py` | `tools/b1_pair_batch_correction.py`, `tools/feature_variants/pair_target_prior_edge_e34.py` |
| `external_cohort_metadata_20261013.json` | the data behind [`docs/EXTERNAL_COHORT_METADATA.md`](../EXTERNAL_COHORT_METADATA.md) | metadata audit |
| `test_readiness_20261013/` | the untouched-test preparation of 13 October (claim #22, PR #23): two paid DeepSeek text reviews of fixed public metadata (cohort eligibility, frozen-test protocol), their prompts, the driver and its hashes, and the pre-registered `plan.md`; $0.010 by the ledger, no model scored; reading [`docs/TEST_READINESS_20261013.md`](../TEST_READINESS_20261013.md); run `gene-mila-test-readiness/runs/test_readiness_20261013` | `deepseek_review_driver.py` (in the directory) |
| `b4_existing_readings_20261017.{md,json}` | B4, the existing one-worker readings (PLAN_B4), 17 October | the lead, from the stored run summaries |

## Block F (historical 16 October and corrected 17 October 2026; [`docs/PLAN_F_GENOME_ANNOTATION.md`](../PLAN_F_GENOME_ANNOTATION.md))

Read first: [the corrected F reading](g_f_h8_readings.md#corrected-f-stage2-and-pool-only), [independent primary audit](norman_f_corrected_primary_audit.md) and [selection audit](norman_f_corrected_selection_audit.md). The original stage1 and94plugin sources were reused unchanged; only the corrected stage2 and complete-family pool decide the current result.

The original 16 October files listed below are historical and remain byte-identical. Their old top-limited/null/positive interpretations are superseded by the corrected17October reading; the old sealed files were not reread.

| File | What it is |
|---|---|
| `norman_f_r0_sealed_reading`, `norman_f_r2_sealed_reading`, `norman_f_r3_sealed_reading` (`.md` and `.json`), `norman_f_sealed_summary.json`, `norman_f_summary.json` | the three runs' sealed readings and their summary |
| `norman_f_stage1/`, `norman_f_stage2/`, `norman_f_pooled_holm/`, `norman_f_arm_vs_b2/` | the two-stage feature-level reading (`tools/block_f_readings.py`, `tools/feature_compare.py`) |
| `norman_f_stage1_audit.md`, `norman_f_primary_audit.md`, `norman_f_coefficient_signs.{md,json}`, `norman_f_coefficient_manifest.json`, `norman_f_source_inventory.md` | the audits of the stage-1 result, the primary result, the fitted coefficient signs and the annotation sources |
| `norman_f_plugins/` (94 files), `norman_f_top/` (the top candidates, a copy by design), `norman_f_plugin_manifest.json`, `norman_f_metadata.json`, `norman_f_collect_metadata.py` | every feature plugin the three runs wrote, the candidates, and the collector that produced the manifests (it imports `tools/feature_audit.py`) |
| `norman_f_artifact_manifest.json` | the integrity manifest of every block F file above |
| `norman_f_pytest.{exit,log}`, `norman_f_stage2.{exit,log}` | kept: `norman_f_readings.md` links the test log and says it is retained, HANDOFF cites the stage-2 pair, and the artifact manifest lists all four |

## Block G (17 October 2026; [`docs/PLAN_G_CLEAN_ARM.md`](../PLAN_G_CLEAN_ARM.md))

| File | What it is |
|---|---|
| `block_g_prepare_refusal_20261017.json` | the first clean-bundle preparation's refusal (GO ancestor ordering), 17 October; the receipts of the rebuild are in [`docs/mac/block_g/`](../mac/block_g/) |
| knowledge input | `docs/mac/knowledge/gene_constraint_norman.json.gz` (gnomAD constraint, `tools/build_gene_constraint.py`) |
| readings | All four readings are complete for both datasets: the consolidated publication below, one row per reading; generated paths were preserved. |

## Block G, corrected F and the lead's H8: the consolidated publication (17 October 2026, PR #63)

Read first: [G, corrected F and lead H8 readings](g_f_h8_readings.md) ([JSON twin](g_f_h8_readings.json)). Block G's complete-family result is negative on both datasets; corrected F has six development candidates, all reading the Replogle screen, and no tier-1 candidate; the lead's H8 hypothesis is unsupported on both datasets. The verdicts against the goal are in [`docs/GOAL_CRITERIA.md`](../GOAL_CRITERIA.md), Status.

One row per reading. A step run by a tool keeps three receipts beside its output, `<step>.command.txt` (the exact command), `<step>.exit` (its exit code) and `<step>.log` (its output); "receipts" below means those three. `pooled_holm` is a legacy file name: the decision is the pooled step-down p under the gene null and, for a row proportional to a parent column, the perturbation null. Every file, with its size and sha256, is in [`g_f_h8_completion_manifest.json`](g_f_h8_completion_manifest.json) (1,200 paths: the 1,199 other files of the publication and this index as it stood at `dbd0693`, when it listed every file on a row of its own; that version is `git show dbd0693:docs/results/README.md`). [`g_f_h8_publication_manifest.json`](g_f_h8_publication_manifest.json) pins the first 1,174 paths at `0f18626`. Every file is an unchanged record; none was moved or renamed.

### Block G, both datasets (PLAN_G's readings 1 to 4)

| Files | What they are |
|---|---|
| `{adamson_cf,norman}_g_input_manifest.json` | the hashes of every public and source input, fixed before reading 1 scored |
| `{adamson_cf,norman}_g_stage1/feature_compare.{md,json}`; `{adamson_cf,norman}_g_stage1` receipts | reading 1, stage 1: the out-of-fold screen of every G1 plugin that reads a table |
| `{adamson_cf,norman}_g_select` receipts; `{adamson_cf,norman}_g_top/selection.json`, `{adamson_cf,norman}_g_top/r{0,2,3}/*.py` | reading 1, the family taken to stage 2: every eligible row, no `--k`, with an unchanged copy of each candidate's source (221 on Adamson, 174 on Norman) |
| `{adamson_cf,norman}_g_stage2/feature_compare.{md,json}`; `{adamson_cf,norman}_g_stage2` receipts | reading 1, stage 2: the matched nulls at 999 replicates |
| `{adamson_cf,norman}_g_pooled_holm/pooled_holm.{md,json}`; `{adamson_cf,norman}_g_pool` receipts | reading 1, the decision: the complete-family step-down; no row passes on either dataset (210 and 158 unique predictions) |
| `{adamson_cf,norman}_g1_vs_g0/feature_compare.{md,json}`, `{adamson_cf,norman}_g1_vs_g0_input_manifest.json`; `{adamson_cf,norman}_g1_vs_g0` receipts; `{adamson_cf,norman}_g_arm_summary.{md,json}` | reading 2, arm against arm: the six runs' selected models out of fold, descriptive, with the per-run values and each arm's mean and sample sd |
| `{adamson_cf,norman}_g{0,1}_r{0,2,3}_sealed_reading.{md,json}` and their receipts; `{adamson_cf,norman}_g_sealed_phase` receipts, `{adamson_cf,norman}_g_sealed_phase.input_manifest.json`; `{adamson_cf,norman}_g_sealed_summary.{md,json}`; `norman_g_sealed_audit.{md,json}` | reading 3, each run on the worn sealed set: indicative only, nothing chosen from it; on Norman an arithmetic audit of the new sealed outputs |
| `{adamson_cf,norman}_g_direct_table_audit.{md,json}`; `{adamson_cf,norman}_g_source_audit.{md,json}` and its command; `norman_g_primary_audit.{md,json}`, `norman_g_audit_addendum.{md,json}` | reading 4 and the audits: which knowledge files each plugin reads (the G1 agents did read the tables), and on Norman the independent audits of the primary result |
| `{adamson_cf,norman}_g_plugins/r{0,2,3}/*.py` | unchanged copies of every plugin source the readings scored (276 on Adamson, 223 on Norman) |
| `norman_g_complete_results_issue51.{md,json}` | the Norman result as posted on #51 |

### Block F, corrected (stage 2 and the pool only; stage 1 and the 94 plugin sources are block F's originals above)

| Files | What they are |
|---|---|
| `norman_f_corrected_input_manifest.json` | the input hashes, fixed before the corrected reading scored |
| `norman_f_corrected_select` receipts; `norman_f_corrected_top/selection.json`, `norman_f_corrected_top/r{0,2,3}/*.py` | all 66 eligible rows of the original stage 1, with an unchanged copy of each candidate's source |
| `norman_f_corrected_stage2/feature_compare.{md,json}`; `norman_f_corrected_stage2` receipts | stage 2: 59 rows tested at 999 replicates |
| `norman_f_corrected_pooled_holm/pooled_holm.{md,json}`; `norman_f_corrected_pool` receipts | the decision: 53 unique predictions, six rows pass, every one reading the Replogle screen (tier 3), so none is tier 1 |
| `norman_f_corrected_primary_audit.{md,json}`, `norman_f_corrected_selection_audit.{md,json}` | the independent audits of the result and of the family's selection |
| `norman_f_corrected_h8_launch_issue51.{md,json}` | the result and the H8 launch as posted on #51 |

### The lead's hypothesis H8 (family 8; a human hypothesis, never A.1)

| Files | What they are |
|---|---|
| `lead_h8_prescore_protocol.{md,json}` | the protocol, the parent-column clarification and the hashes, fixed before scoring |
| `{adamson_cf,norman}_lead_h8_prerun.{md,json}` and their receipts | the pre-runs: the public-knowledge lists and counts the plugin reads |
| `{adamson_cf,norman}_lead_h8/feature_compare.{md,json}`; `{adamson_cf,norman}_lead_h8` receipts | the scoring at 999 replicates under both nulls |
| `{adamson_cf,norman}_lead_h8_summary.{md,json}`, `{adamson_cf,norman}_lead_h8_audit.{md,json}` | the result with every metric, and its independent audit: not supported on either dataset |
| `adamson_h8_norman_launch_issue51.{md,json}`, `norman_h8_complete_pytest_launch_issue51.{md,json}` | the posts on #51 |

### The publication itself, the package export and the block H tool check

| Files | What they are |
|---|---|
| `g_f_h8_readings.{md,json}` | the consolidated reading (read first) |
| `g_f_h8_publication_manifest.{md,json}`, `g_f_h8_completion_manifest.{md,json}` | the per-file manifests, with sizes and sha256 (the paragraph above) |
| `g_f_h8_publication_verification.{md,json}`, `g_f_h8_completion.{md,json}`, `g_f_h8_completion_verification.{md,json}`, `g_f_h8_preservation_audit.{md,json}`, `g_f_h8_report_audit.{md,json}` | the verifications and audits of the publication: completeness, unchanged sources, the report against its numbers |
| `g_f_h8_publication_pytest` receipts | the full test suite before publication (656 passed, 1 skipped) |
| `g_f_h8_pr_issue51.{md,json}` | the pull request as posted on #51 |
| `adamson_cf_task_export` receipts; `adamson_cf_task_export_receipt.{md,json}`, `adamson_cf_task_export_audit.{md,json}`, `adamson_cf_task_export_issue51.{md,json}` | the export of the Adamson task package for block H from `data/adamson_cf_clean_tables` (the package itself stays on the Mac), its hashes and audit |
| `block_h_freecheck_20261017` receipts; `block_h_freecheck_report.{md,json}`, `block_h_freecheck_audit.{md,json}`, `block_h_freecheck_issue51.{md,json}` | the free block H tool check of 17 October (`docs/mac/block_h/check_tools.sh`): block H not ready |

## Fresh-test preparation (17 October 2026; [`docs/PLAN_R_FRESH_TEST.md`](../PLAN_R_FRESH_TEST.md))

Free checks on Andres's Mac, claim [#68](https://github.com/andresloak100/Gene-Mila/issues/68); commands and logs in
[`docs/mac/mac_checks_20261017/`](../mac/mac_checks_20261017/README.md).

| File | What it is | Produced by |
|---|---|---|
| `replogle_k562_gwps_manifest_20261017/` | the Replogle 2022 K562 genome-wide eligibility manifest (obs and var only, no draw) against a **provisional** gene universe (the Adamson clean bundle's 2,055 public genes; no Adamson frozen export exists yet): 1,820 eligible targets, 1,331 in-distribution; read `README.md` first | `tools/replogle_slice_manifest.py` |
| `frozen_adapter_check_20261017/` | the PLAN_R section 6 gate on the B1 Norman frozen export: `predict-targets` (31 single-gene anchors), `predict` (88 pairs) and a full 119-anchor replay, every member bit-exact; plus an extra diagnostic outside the gate: the new-condition branch, bit-exact on the 31 single-gene anchors renamed as new conditions; read `README.md` first | `tools/frozen_model.py` |

- `null_degeneracy_sim/` (28 October 2026): 200 null features (a parent column times a random per-perturbation scalar) scored
  against both nulls; false-positive rate 0.285 for the gene null, 0.09 for the perturbation null. Tool:
  `tools/null_degeneracy_sim.py`; note: `docs/NOTE_DEGENERATE_NULL.md`.

## Archived from here

`feature_audit.{md,json}`, `feature_audit_feature_box.json`, `feature_audit_v2.{md,json}`, `feature_audit_v2_feature_box.json`
(audit versions 1 and 2, superseded by v3): [`docs/archive/results/`](../archive/README.md).
