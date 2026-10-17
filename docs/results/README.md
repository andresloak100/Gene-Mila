# Results index

Every file here is a record produced by a run or a tool on Andres's Mac and committed as it was on disk: never edited,
never deleted; a new check gets a new file. Every number in the README traces to one of these files
(`tools/readme_check.py`). A `.md` and `.json` pair is one result (the `.md` is the reading, the `.json` the numbers).

The block-directory convention applies to future readings. The G, corrected F and H8 records below retain the exact generated paths pinned in their pre-score commands and hash manifests; their already referenced files were not moved or overwritten. Every new file in this consolidated publication has a separate row in the exhaustive index below.

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
| readings | All four readings are complete for both datasets. See the consolidated reading and exact-file index below; generated paths were preserved. |

## Lead H8 and consolidated publication (17 October 2026)

Read first: [G, corrected F and lead H8 readings](g_f_h8_readings.md), with its [JSON twin](g_f_h8_readings.json). G's complete-family result is negative on both datasets; corrected F has six Replogle-assisted development candidates and no tier1 candidate; the lead's H8 hypothesis is unsupported on both datasets. H8 is the lead's pre-registered human hypothesis, never an agent discovery/A.1. Fixed pre-score interpretation, both pre-runs, both nulls, signs and failed gates are preserved.

The tables below enumerate every new file separately, including duplicate-by-design candidate snapshots and both members of every JSON/Markdown pair. Pooled_holm is a legacy filename: the corrected decision uses pooled step-down gene and perturbation p-values, not old Holm thresholds. All source snapshots are unchanged copies. Old142Fartifacts and source runs remain unchanged; raw data/private/harness/package files and credentials are excluded.

### Adamson G — exact new files

| File | Record |
|---|---|
| [adamson_cf_g0_r0_sealed_reading.command.txt](adamson_cf_g0_r0_sealed_reading.command.txt) | Exact command receipt. |
| [adamson_cf_g0_r0_sealed_reading.exit](adamson_cf_g0_r0_sealed_reading.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g0_r0_sealed_reading.json](adamson_cf_g0_r0_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g0_r0_sealed_reading.log](adamson_cf_g0_r0_sealed_reading.log) | Captured tool output. |
| [adamson_cf_g0_r0_sealed_reading.md](adamson_cf_g0_r0_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g0_r2_sealed_reading.command.txt](adamson_cf_g0_r2_sealed_reading.command.txt) | Exact command receipt. |
| [adamson_cf_g0_r2_sealed_reading.exit](adamson_cf_g0_r2_sealed_reading.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g0_r2_sealed_reading.json](adamson_cf_g0_r2_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g0_r2_sealed_reading.log](adamson_cf_g0_r2_sealed_reading.log) | Captured tool output. |
| [adamson_cf_g0_r2_sealed_reading.md](adamson_cf_g0_r2_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g0_r3_sealed_reading.command.txt](adamson_cf_g0_r3_sealed_reading.command.txt) | Exact command receipt. |
| [adamson_cf_g0_r3_sealed_reading.exit](adamson_cf_g0_r3_sealed_reading.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g0_r3_sealed_reading.json](adamson_cf_g0_r3_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g0_r3_sealed_reading.log](adamson_cf_g0_r3_sealed_reading.log) | Captured tool output. |
| [adamson_cf_g0_r3_sealed_reading.md](adamson_cf_g0_r3_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_r0_sealed_reading.command.txt](adamson_cf_g1_r0_sealed_reading.command.txt) | Exact command receipt. |
| [adamson_cf_g1_r0_sealed_reading.exit](adamson_cf_g1_r0_sealed_reading.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g1_r0_sealed_reading.json](adamson_cf_g1_r0_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_r0_sealed_reading.log](adamson_cf_g1_r0_sealed_reading.log) | Captured tool output. |
| [adamson_cf_g1_r0_sealed_reading.md](adamson_cf_g1_r0_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_r2_sealed_reading.command.txt](adamson_cf_g1_r2_sealed_reading.command.txt) | Exact command receipt. |
| [adamson_cf_g1_r2_sealed_reading.exit](adamson_cf_g1_r2_sealed_reading.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g1_r2_sealed_reading.json](adamson_cf_g1_r2_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_r2_sealed_reading.log](adamson_cf_g1_r2_sealed_reading.log) | Captured tool output. |
| [adamson_cf_g1_r2_sealed_reading.md](adamson_cf_g1_r2_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_r3_sealed_reading.command.txt](adamson_cf_g1_r3_sealed_reading.command.txt) | Exact command receipt. |
| [adamson_cf_g1_r3_sealed_reading.exit](adamson_cf_g1_r3_sealed_reading.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g1_r3_sealed_reading.json](adamson_cf_g1_r3_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_r3_sealed_reading.log](adamson_cf_g1_r3_sealed_reading.log) | Captured tool output. |
| [adamson_cf_g1_r3_sealed_reading.md](adamson_cf_g1_r3_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [adamson_cf_g1_vs_g0.command.txt](adamson_cf_g1_vs_g0.command.txt) | Exact command receipt. |
| [adamson_cf_g1_vs_g0.exit](adamson_cf_g1_vs_g0.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g1_vs_g0.log](adamson_cf_g1_vs_g0.log) | Captured tool output. |
| [adamson_cf_g1_vs_g0/feature_compare.json](adamson_cf_g1_vs_g0/feature_compare.json) | Exact six-run descriptive selected-model OOF comparison. |
| [adamson_cf_g1_vs_g0/feature_compare.md](adamson_cf_g1_vs_g0/feature_compare.md) | Exact six-run descriptive selected-model OOF comparison. |
| [adamson_cf_g1_vs_g0_input_manifest.json](adamson_cf_g1_vs_g0_input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [adamson_cf_g_arm_summary.json](adamson_cf_g_arm_summary.json) | Per-run and arm mean/sample-SD summary. |
| [adamson_cf_g_arm_summary.md](adamson_cf_g_arm_summary.md) | Per-run and arm mean/sample-SD summary. |
| [adamson_cf_g_direct_table_audit.json](adamson_cf_g_direct_table_audit.json) | Static source/direct-table-use and permitted metadata audit. |
| [adamson_cf_g_direct_table_audit.md](adamson_cf_g_direct_table_audit.md) | Static source/direct-table-use and permitted metadata audit. |
| [adamson_cf_g_input_manifest.json](adamson_cf_g_input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [adamson_cf_g_plugins/r0/annotation_nonlinear_interaction_e224.py](adamson_cf_g_plugins/r0/annotation_nonlinear_interaction_e224.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_nonlinear_interaction_e225.py](adamson_cf_g_plugins/r0/annotation_nonlinear_interaction_e225.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_projection_elementwise_produc_e350.py](adamson_cf_g_plugins/r0/annotation_projection_elementwise_produc_e350.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_projection_similarity_v2_e197.py](adamson_cf_g_plugins/r0/annotation_projection_similarity_v2_e197.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_projection_target_interaction_e149.py](adamson_cf_g_plugins/r0/annotation_projection_target_interaction_e149.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_projection_target_interaction_e173.py](adamson_cf_g_plugins/r0/annotation_projection_target_interaction_e173.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_projection_target_interaction_e174.py](adamson_cf_g_plugins/r0/annotation_projection_target_interaction_e174.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_projection_x_response_entropy_e471.py](adamson_cf_g_plugins/r0/annotation_projection_x_response_entropy_e471.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/annotation_random_projection_target_inte_e379.py](adamson_cf_g_plugins/r0/annotation_random_projection_target_inte_e379.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/chromatin_accessibility_corr_e478.py](adamson_cf_g_plugins/r0/chromatin_accessibility_corr_e478.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/coessentiality_corr_target_gene_e268.py](adamson_cf_g_plugins/r0/coessentiality_corr_target_gene_e268.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/coessentiality_interaction_e289.py](adamson_cf_g_plugins/r0/coessentiality_interaction_e289.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/combined_annotation_ppi_random_projectio_e185.py](adamson_cf_g_plugins/r0/combined_annotation_ppi_random_projectio_e185.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/combined_annotation_ppi_random_projectio_e548.py](adamson_cf_g_plugins/r0/combined_annotation_ppi_random_projectio_e548.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/combined_annotation_projection_target_in_e398.py](adamson_cf_g_plugins/r0/combined_annotation_projection_target_in_e398.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/combined_annotation_projection_x_essenti_e419.py](adamson_cf_g_plugins/r0/combined_annotation_projection_x_essenti_e419.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/combined_annotation_projection_x_target__e439.py](adamson_cf_g_plugins/r0/combined_annotation_projection_x_target__e439.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/complex_membership_interaction_e479.py](adamson_cf_g_plugins/r0/complex_membership_interaction_e479.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/complex_partner_avg_response_e154.py](adamson_cf_g_plugins/r0/complex_partner_avg_response_e154.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/constraint_flag_x_mean_response_e468.py](adamson_cf_g_plugins/r0/constraint_flag_x_mean_response_e468.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/constraint_product_exxx_e594.py](adamson_cf_g_plugins/r0/constraint_product_exxx_e594.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/cpg_island_promoter_interaction_e155.py](adamson_cf_g_plugins/r0/cpg_island_promoter_interaction_e155.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/cpg_promoter_score_e81.py](adamson_cf_g_plugins/r0/cpg_promoter_score_e81.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/cpg_target_tf_interaction_e168.py](adamson_cf_g_plugins/r0/cpg_target_tf_interaction_e168.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_gene_x_ppi_neighbor_mean_de_e436.py](adamson_cf_g_plugins/r0/essentiality_gene_x_ppi_neighbor_mean_de_e436.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_pathway_interaction_e65.py](adamson_cf_g_plugins/r0/essentiality_pathway_interaction_e65.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_ppi_neighbor_interaction_e384.py](adamson_cf_g_plugins/r0/essentiality_ppi_neighbor_interaction_e384.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_response_interaction_e329.py](adamson_cf_g_plugins/r0/essentiality_response_interaction_e329.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_selfdelta_interaction_e234_e249.py](adamson_cf_g_plugins/r0/essentiality_selfdelta_interaction_e234_e249.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_target_x_mean_response_g_e361.py](adamson_cf_g_plugins/r0/essentiality_target_x_mean_response_g_e361.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_target_x_response_entropy_e433.py](adamson_cf_g_plugins/r0/essentiality_target_x_response_entropy_e433.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_weighted_tf_motif_score_e386.py](adamson_cf_g_plugins/r0/essentiality_weighted_tf_motif_score_e386.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_x_ppi_neighbor_mean_delta_e502.py](adamson_cf_g_plugins/r0/essentiality_x_ppi_neighbor_mean_delta_e502.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_x_response_entropy_e491.py](adamson_cf_g_plugins/r0/essentiality_x_response_entropy_e491.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/essentiality_x_response_entropy_e543.py](adamson_cf_g_plugins/r0/essentiality_x_response_entropy_e543.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/full_annotation_projection_target_e459.py](adamson_cf_g_plugins/r0/full_annotation_projection_target_e459.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/full_annotation_projection_with_protein_e645.py](adamson_cf_g_plugins/r0/full_annotation_projection_with_protein_e645.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/gene_annotation_random_projection_e113.py](adamson_cf_g_plugins/r0/gene_annotation_random_projection_e113.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/gene_essentiality_x_target_self_delta_e362.py](adamson_cf_g_plugins/r0/gene_essentiality_x_target_self_delta_e362.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/gene_loeuf_e94.py](adamson_cf_g_plugins/r0/gene_loeuf_e94.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/gene_loeuf_x_pathway_response_e712.py](adamson_cf_g_plugins/r0/gene_loeuf_x_pathway_response_e712.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/gene_loeuf_x_target_selfdelta_e569.py](adamson_cf_g_plugins/r0/gene_loeuf_x_target_selfdelta_e569.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/gene_set_overlap_x_essentiality_e505.py](adamson_cf_g_plugins/r0/gene_set_overlap_x_essentiality_e505.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/learned_annotation_projection_interactio_e300.py](adamson_cf_g_plugins/r0/learned_annotation_projection_interactio_e300.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_interaction_squared_e481.py](adamson_cf_g_plugins/r0/loeuf_interaction_squared_e481.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_interaction_target_gene_e122.py](adamson_cf_g_plugins/r0/loeuf_interaction_target_gene_e122.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_interaction_target_gene_e601_e578.py](adamson_cf_g_plugins/r0/loeuf_interaction_target_gene_e601_e578.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_product_target_gene_e217.py](adamson_cf_g_plugins/r0/loeuf_product_target_gene_e217.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_target_gene_interaction_e641.py](adamson_cf_g_plugins/r0/loeuf_target_gene_interaction_e641.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_target_x_gene_entropy_exxx_e592.py](adamson_cf_g_plugins/r0/loeuf_target_x_gene_entropy_exxx_e592.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_target_x_ppi_neighbor_mean_delta_e465.py](adamson_cf_g_plugins/r0/loeuf_target_x_ppi_neighbor_mean_delta_e465.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_target_x_response_entropy_e339.py](adamson_cf_g_plugins/r0/loeuf_target_x_response_entropy_e339.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/loeuf_weighted_ppi_neighbor_mean_delta_e_e554.py](adamson_cf_g_plugins/r0/loeuf_weighted_ppi_neighbor_mean_delta_e_e554.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/nuclear_gene_x_loeuf_target_e467.py](adamson_cf_g_plugins/r0/nuclear_gene_x_loeuf_target_e467.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/nuclear_gene_x_pathway_overlap_interacti_e519.py](adamson_cf_g_plugins/r0/nuclear_gene_x_pathway_overlap_interacti_e519.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/nuclear_gene_x_target_nuclear_e506.py](adamson_cf_g_plugins/r0/nuclear_gene_x_target_nuclear_e506.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/nuclear_target_x_gene_loeuf_e697.py](adamson_cf_g_plugins/r0/nuclear_target_x_gene_loeuf_e697.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/nuclear_target_x_nuclear_gene_e493.py](adamson_cf_g_plugins/r0/nuclear_target_x_nuclear_gene_e493.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/pathway_overlap_weighted_by_essentiality_e516.py](adamson_cf_g_plugins/r0/pathway_overlap_weighted_by_essentiality_e516.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/pathway_overlap_x_target_loeuf_e407.py](adamson_cf_g_plugins/r0/pathway_overlap_x_target_loeuf_e407.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/pathway_overlap_x_target_loeuf_e565.py](adamson_cf_g_plugins/r0/pathway_overlap_x_target_loeuf_e565.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/ppi_neighbor_mean_delta_x_target_essenti_e415.py](adamson_cf_g_plugins/r0/ppi_neighbor_mean_delta_x_target_essenti_e415.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/promoter_cpg_response_e602_e579.py](adamson_cf_g_plugins/r0/promoter_cpg_response_e602_e579.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/protein_annotation_projection_target_int_e410.py](adamson_cf_g_plugins/r0/protein_annotation_projection_target_int_e410.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/protein_compartment_flag_e82.py](adamson_cf_g_plugins/r0/protein_compartment_flag_e82.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/protein_compartment_similarity_e169.py](adamson_cf_g_plugins/r0/protein_compartment_similarity_e169.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/protein_domain_overlap_target_gene_e270.py](adamson_cf_g_plugins/r0/protein_domain_overlap_target_gene_e270.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/protein_domain_similarity_e327.py](adamson_cf_g_plugins/r0/protein_domain_similarity_e327.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/random_projection_annotation_ppi_diffusi_e701.py](adamson_cf_g_plugins/r0/random_projection_annotation_ppi_diffusi_e701.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/random_projection_annotation_ppi_e525_e539.py](adamson_cf_g_plugins/r0/random_projection_annotation_ppi_e525_e539.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/random_projection_gene_annotation_e124.py](adamson_cf_g_plugins/r0/random_projection_gene_annotation_e124.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/rbf_annotation_projection_e606_e584.py](adamson_cf_g_plugins/r0/rbf_annotation_projection_e606_e584.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/response_entropy_target_essentiality_int_e389.py](adamson_cf_g_plugins/r0/response_entropy_target_essentiality_int_e389.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/secreted_membrane_x_response_entropy_e694.py](adamson_cf_g_plugins/r0/secreted_membrane_x_response_entropy_e694.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/selfdelta_x_cpg_promoter_exxx_e595.py](adamson_cf_g_plugins/r0/selfdelta_x_cpg_promoter_exxx_e595.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/shared_tf_binding_score_e191.py](adamson_cf_g_plugins/r0/shared_tf_binding_score_e191.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_cpg_x_response_entropy_e614_e619.py](adamson_cf_g_plugins/r0/target_cpg_x_response_entropy_e614_e619.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_cpg_x_response_entropy_e614_e620.py](adamson_cf_g_plugins/r0/target_cpg_x_response_entropy_e614_e620.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_essentiality_combo_e50.py](adamson_cf_g_plugins/r0/target_essentiality_combo_e50.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_essentiality_ppi_neighbor_delta_i_e515.py](adamson_cf_g_plugins/r0/target_essentiality_ppi_neighbor_delta_i_e515.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_essentiality_x_neighbor_response_e665.py](adamson_cf_g_plugins/r0/target_essentiality_x_neighbor_response_e665.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_expression_variability_x_loeuf_e417.py](adamson_cf_g_plugins/r0/target_expression_variability_x_loeuf_e417.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_knockdown_proxy_e14.py](adamson_cf_g_plugins/r0/target_knockdown_proxy_e14.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_localization_interaction_e403.py](adamson_cf_g_plugins/r0/target_localization_interaction_e403.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_e24.py](adamson_cf_g_plugins/r0/target_loeuf_e24.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_e35.py](adamson_cf_g_plugins/r0/target_loeuf_e35.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_x_mean_response_e404.py](adamson_cf_g_plugins/r0/target_loeuf_x_mean_response_e404.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_x_ppi_neighbor_mean_delta_e317.py](adamson_cf_g_plugins/r0/target_loeuf_x_ppi_neighbor_mean_delta_e317.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_x_ppi_neighbor_response_e62_e628.py](adamson_cf_g_plugins/r0/target_loeuf_x_ppi_neighbor_response_e62_e628.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_x_ppi_neighbor_response_v2_e682.py](adamson_cf_g_plugins/r0/target_loeuf_x_ppi_neighbor_response_v2_e682.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_x_response_entropy_e543_e555.py](adamson_cf_g_plugins/r0/target_loeuf_x_response_entropy_e543_e555.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_loeuf_x_second_neighbor_response_e746.py](adamson_cf_g_plugins/r0/target_loeuf_x_second_neighbor_response_e746.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_ppi_neighbor_essentiality_weighte_e764.py](adamson_cf_g_plugins/r0/target_ppi_neighbor_essentiality_weighte_e764.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_ppi_neighbor_mean_response_loeuf__e775.py](adamson_cf_g_plugins/r0/target_ppi_neighbor_mean_response_loeuf__e775.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/target_self_delta_x_loeuf_gene_e523_e535.py](adamson_cf_g_plugins/r0/target_self_delta_x_loeuf_gene_e523_e535.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/tf_binding_overlap_e610_e604.py](adamson_cf_g_plugins/r0/tf_binding_overlap_e610_e604.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/tf_motif_similarity_target_gene_e269.py](adamson_cf_g_plugins/r0/tf_motif_similarity_target_gene_e269.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/tf_target_motif_density_e600_e577.py](adamson_cf_g_plugins/r0/tf_target_motif_density_e600_e577.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/tf_target_overlap_score_e476.py](adamson_cf_g_plugins/r0/tf_target_overlap_score_e476.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/tfbs_count_promoter_e341.py](adamson_cf_g_plugins/r0/tfbs_count_promoter_e341.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r0/utr3_length_response_e604_e581.py](adamson_cf_g_plugins/r0/utr3_length_response_e604_e581.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/chromatin_state_similarity_e720.py](adamson_cf_g_plugins/r2/chromatin_state_similarity_e720.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/domain_similarity_e123.py](adamson_cf_g_plugins/r2/domain_similarity_e123.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/localization_overlap_e604_e611.py](adamson_cf_g_plugins/r2/localization_overlap_e604_e611.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/nearest_neighbor_response_e9.py](adamson_cf_g_plugins/r2/nearest_neighbor_response_e9.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/promoter_cpg_features_e35.py](adamson_cf_g_plugins/r2/promoter_cpg_features_e35.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/promoter_motif_similarity_e602_e609.py](adamson_cf_g_plugins/r2/promoter_motif_similarity_e602_e609.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/protein_stability_proxy_e81.py](adamson_cf_g_plugins/r2/protein_stability_proxy_e81.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/random_projection_target_annotation_e737.py](adamson_cf_g_plugins/r2/random_projection_target_annotation_e737.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/random_projection_target_annotation_e738.py](adamson_cf_g_plugins/r2/random_projection_target_annotation_e738.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/random_projection_target_annotation_e750.py](adamson_cf_g_plugins/r2/random_projection_target_annotation_e750.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/same_compartment_indicator_e268.py](adamson_cf_g_plugins/r2/same_compartment_indicator_e268.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/same_tad_indicator_e719.py](adamson_cf_g_plugins/r2/same_tad_indicator_e719.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/shared_cpg_promoter_e195.py](adamson_cf_g_plugins/r2/shared_cpg_promoter_e195.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/shared_tf_motif_similarity_e175.py](adamson_cf_g_plugins/r2/shared_tf_motif_similarity_e175.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/shared_tf_motifs_e629.py](adamson_cf_g_plugins/r2/shared_tf_motifs_e629.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/stability_x_nuclear_flag_e255.py](adamson_cf_g_plugins/r2/stability_x_nuclear_flag_e255.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_compartment_flag_e252.py](adamson_cf_g_plugins/r2/target_compartment_flag_e252.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_compartment_x_gene_annotation_e333.py](adamson_cf_g_plugins/r2/target_compartment_x_gene_annotation_e333.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_e2_e304.py](adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_e2_e304.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_e745.py](adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_e745.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_sp_e566.py](adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_sp_e566.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_sp_e567.py](adamson_cf_g_plugins/r2/target_compartment_x_gene_compartment_sp_e567.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_constraint_x_pathway_similarity_e418.py](adamson_cf_g_plugins/r2/target_constraint_x_pathway_similarity_e418.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_cpg_oe_promoter_x_is_target_e246.py](adamson_cf_g_plugins/r2/target_cpg_oe_promoter_x_is_target_e246.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_cpg_promoter_broadcast_e257.py](adamson_cf_g_plugins/r2/target_cpg_promoter_broadcast_e257.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_cpg_promoter_x_gene_cpg_promoter_e723.py](adamson_cf_g_plugins/r2/target_cpg_promoter_x_gene_cpg_promoter_e723.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_cpg_promoter_x_gene_loeuf_e526.py](adamson_cf_g_plugins/r2/target_cpg_promoter_x_gene_loeuf_e526.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_cpg_promoter_x_gene_tf_indicator_e321.py](adamson_cf_g_plugins/r2/target_cpg_promoter_x_gene_tf_indicator_e321.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_degradation_signal_x_gene_ubiquit_e670.py](adamson_cf_g_plugins/r2/target_degradation_signal_x_gene_ubiquit_e670.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_depmap_essentiality_e703.py](adamson_cf_g_plugins/r2/target_depmap_essentiality_e703.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_er_membrane_x_gene_upr_set_e354.py](adamson_cf_g_plugins/r2/target_er_membrane_x_gene_upr_set_e354.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_essentiality_x_coexpression_e638.py](adamson_cf_g_plugins/r2/target_essentiality_x_coexpression_e638.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_essentiality_x_gene_constraint_e500.py](adamson_cf_g_plugins/r2/target_essentiality_x_gene_constraint_e500.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_essentiality_x_gene_loeuf_e512.py](adamson_cf_g_plugins/r2/target_essentiality_x_gene_loeuf_e512.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_essentiality_x_ppi_interaction_e417.py](adamson_cf_g_plugins/r2/target_essentiality_x_ppi_interaction_e417.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gc_cds_x_is_target_e243.py](adamson_cf_g_plugins/r2/target_gc_cds_x_is_target_e243.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gc_content_x_is_target_e284.py](adamson_cf_g_plugins/r2/target_gc_content_x_is_target_e284.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_coexpression_rank_x_target_l_e412.py](adamson_cf_g_plugins/r2/target_gene_coexpression_rank_x_target_l_e412.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_compartment_match_e652.py](adamson_cf_g_plugins/r2/target_gene_compartment_match_e652.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_compartment_similarity_e370.py](adamson_cf_g_plugins/r2/target_gene_compartment_similarity_e370.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_constraint_similarity_e429.py](adamson_cf_g_plugins/r2/target_gene_constraint_similarity_e429.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_loeuf_product_e537.py](adamson_cf_g_plugins/r2/target_gene_loeuf_product_e537.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_loeuf_ratio_e477.py](adamson_cf_g_plugins/r2/target_gene_loeuf_ratio_e477.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_loeuf_similarity_e551.py](adamson_cf_g_plugins/r2/target_gene_loeuf_similarity_e551.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_same_compartment_e394.py](adamson_cf_g_plugins/r2/target_gene_same_compartment_e394.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_same_compartment_indicator_e409.py](adamson_cf_g_plugins/r2/target_gene_same_compartment_indicator_e409.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e454.py](adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e454.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e473.py](adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e473.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e589.py](adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e589.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e694.py](adamson_cf_g_plugins/r2/target_gene_shared_domain_count_e694.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_shared_domains_count_e510.py](adamson_cf_g_plugins/r2/target_gene_shared_domains_count_e510.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_gene_shared_protein_domain_e500_e483.py](adamson_cf_g_plugins/r2/target_gene_shared_protein_domain_e500_e483.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_has_signal_peptide_x_gene_membran_e525.py](adamson_cf_g_plugins/r2/target_has_signal_peptide_x_gene_membran_e525.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_has_signal_peptide_x_is_target_e247.py](adamson_cf_g_plugins/r2/target_has_signal_peptide_x_is_target_e247.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_knockdown_magnitude_e32.py](adamson_cf_g_plugins/r2/target_knockdown_magnitude_e32.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_length_x_gene_function_e269.py](adamson_cf_g_plugins/r2/target_length_x_gene_function_e269.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_length_x_gene_membrane_propensity_e420.py](adamson_cf_g_plugins/r2/target_length_x_gene_membrane_propensity_e420.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_length_x_gene_membrane_raw_e538.py](adamson_cf_g_plugins/r2/target_length_x_gene_membrane_raw_e538.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_localization_entropy_e673.py](adamson_cf_g_plugins/r2/target_localization_entropy_e673.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_broadcast_e253.py](adamson_cf_g_plugins/r2/target_loeuf_broadcast_e253.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_e22.py](adamson_cf_g_plugins/r2/target_loeuf_e22.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_coexpr_rank_e649.py](adamson_cf_g_plugins/r2/target_loeuf_x_coexpr_rank_e649.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_e264.py](adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_e264.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_e350.py](adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_e350.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_rank_e560.py](adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_rank_e560.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_rank_e561.py](adamson_cf_g_plugins/r2/target_loeuf_x_coexpression_rank_e561.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_connectivity_e332.py](adamson_cf_g_plugins/r2/target_loeuf_x_connectivity_e332.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_control_expression_e523.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_control_expression_e523.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_control_mean_e320.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_control_mean_e320.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_cv_e397.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_cv_e397.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_loeuf_e367.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_loeuf_e367.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_loeuf_e380.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_loeuf_e380.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_loeuf_squared_e444.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_loeuf_squared_e444.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_set_similarity_e575.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_set_similarity_e575.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_gene_specificity_e291_e301.py](adamson_cf_g_plugins/r2/target_loeuf_x_gene_specificity_e291_e301.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_is_target_e240.py](adamson_cf_g_plugins/r2/target_loeuf_x_is_target_e240.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_loeuf_x_is_target_e286.py](adamson_cf_g_plugins/r2/target_loeuf_x_is_target_e286.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_n_exons_x_is_target_e245.py](adamson_cf_g_plugins/r2/target_n_exons_x_is_target_e245.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_n_transcripts_x_is_target_e242.py](adamson_cf_g_plugins/r2/target_n_transcripts_x_is_target_e242.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_phospho_density_x_gene_signaling__e672.py](adamson_cf_g_plugins/r2/target_phospho_density_x_gene_signaling__e672.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_promoter_cpg_overlap_gene_e626.py](adamson_cf_g_plugins/r2/target_promoter_cpg_overlap_gene_e626.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_promoter_cpg_strength_e110.py](adamson_cf_g_plugins/r2/target_promoter_cpg_strength_e110.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_promoter_cpg_strength_e71.py](adamson_cf_g_plugins/r2/target_promoter_cpg_strength_e71.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_promoter_cpg_strength_x_gene_set__e168.py](adamson_cf_g_plugins/r2/target_promoter_cpg_strength_x_gene_set__e168.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_promoter_cpg_strength_x_mean_resp_e163.py](adamson_cf_g_plugins/r2/target_promoter_cpg_strength_x_mean_resp_e163.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_half_life_e671.py](adamson_cf_g_plugins/r2/target_protein_half_life_e671.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_length_x_gene_binding_fun_e527.py](adamson_cf_g_plugins/r2/target_protein_length_x_gene_binding_fun_e527.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_length_x_gene_folding_set_e353.py](adamson_cf_g_plugins/r2/target_protein_length_x_gene_folding_set_e353.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_length_x_gene_membrane_e2_e300.py](adamson_cf_g_plugins/r2/target_protein_length_x_gene_membrane_e2_e300.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_length_x_is_target_e241.py](adamson_cf_g_plugins/r2/target_protein_length_x_is_target_e241.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_length_x_is_target_e285.py](adamson_cf_g_plugins/r2/target_protein_length_x_is_target_e285.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_protein_localization_e53.py](adamson_cf_g_plugins/r2/target_protein_localization_e53.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_span_x_gene_intron_length_e568.py](adamson_cf_g_plugins/r2/target_span_x_gene_intron_length_e568.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_stability_x_gene_proteasome_sensi_e725.py](adamson_cf_g_plugins/r2/target_stability_x_gene_proteasome_sensi_e725.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_tf_x_gene_cpg_promoter_e653.py](adamson_cf_g_plugins/r2/target_tf_x_gene_cpg_promoter_e653.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/target_tfbs_x_gene_tf_e539.py](adamson_cf_g_plugins/r2/target_tfbs_x_gene_tf_e539.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r2/weighted_gene_set_similarity_e256.py](adamson_cf_g_plugins/r2/weighted_gene_set_similarity_e256.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/annotation_random_projection_similarity_e704.py](adamson_cf_g_plugins/r3/annotation_random_projection_similarity_e704.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/bidirectional_partner_coexpression_e387.py](adamson_cf_g_plugins/r3/bidirectional_partner_coexpression_e387.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/bidirectional_promoter_indicator_e45.py](adamson_cf_g_plugins/r3/bidirectional_promoter_indicator_e45.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/chromatin_modifier_cpg_interaction_e87.py](adamson_cf_g_plugins/r3/chromatin_modifier_cpg_interaction_e87.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/coessentiality_correlation_e725.py](adamson_cf_g_plugins/r3/coessentiality_correlation_e725.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/coessentiality_correlation_e744.py](adamson_cf_g_plugins/r3/coessentiality_correlation_e744.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/coessentiality_rank_correlation_e809.py](adamson_cf_g_plugins/r3/coessentiality_rank_correlation_e809.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/complex_member_target_loeuf_interaction_e116.py](adamson_cf_g_plugins/r3/complex_member_target_loeuf_interaction_e116.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/cpg_oe_promoter_binary_e44.py](adamson_cf_g_plugins/r3/cpg_oe_promoter_binary_e44.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/essentiality_interaction_e561.py](adamson_cf_g_plugins/r3/essentiality_interaction_e561.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/essentiality_interaction_e803.py](adamson_cf_g_plugins/r3/essentiality_interaction_e803.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/essentiality_times_kurtosis_e629.py](adamson_cf_g_plugins/r3/essentiality_times_kurtosis_e629.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_annotation_random_projection_e717.py](adamson_cf_g_plugins/r3/gene_annotation_random_projection_e717.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_annotation_random_projection_e736.py](adamson_cf_g_plugins/r3/gene_annotation_random_projection_e736.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_annotation_random_projection_tanh_e572.py](adamson_cf_g_plugins/r3/gene_annotation_random_projection_tanh_e572.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_essentiality_buffering_e92.py](adamson_cf_g_plugins/r3/gene_essentiality_buffering_e92.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_loeuf_e254.py](adamson_cf_g_plugins/r3/gene_loeuf_e254.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_promoter_cpg_island_e642.py](adamson_cf_g_plugins/r3/gene_promoter_cpg_island_e642.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_response_variance_over_essentiality_e651.py](adamson_cf_g_plugins/r3/gene_response_variance_over_essentiality_e651.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/gene_response_variance_over_target_essen_e430.py](adamson_cf_g_plugins/r3/gene_response_variance_over_target_essen_e430.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/is_target_x_loeuf_gene_e37.py](adamson_cf_g_plugins/r3/is_target_x_loeuf_gene_e37.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/mean_response_x_gene_loeuf_e274.py](adamson_cf_g_plugins/r3/mean_response_x_gene_loeuf_e274.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/prior_knowledge_random_projection_e344.py](adamson_cf_g_plugins/r3/prior_knowledge_random_projection_e344.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/promoter_motif_jaccard_e759.py](adamson_cf_g_plugins/r3/promoter_motif_jaccard_e759.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/protein_compartment_similarity_e42.py](adamson_cf_g_plugins/r3/protein_compartment_similarity_e42.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/protein_domain_similarity_e743.py](adamson_cf_g_plugins/r3/protein_domain_similarity_e743.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_all_priors_e226.py](adamson_cf_g_plugins/r3/random_projection_all_priors_e226.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_combined_e542.py](adamson_cf_g_plugins/r3/random_projection_combined_e542.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_prior_features_e301.py](adamson_cf_g_plugins/r3/random_projection_prior_features_e301.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_prior_knowledge_e310.py](adamson_cf_g_plugins/r3/random_projection_prior_knowledge_e310.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_prior_knowledge_e328.py](adamson_cf_g_plugins/r3/random_projection_prior_knowledge_e328.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_static_features_e409.py](adamson_cf_g_plugins/r3/random_projection_static_features_e409.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_static_features_e410.py](adamson_cf_g_plugins/r3/random_projection_static_features_e410.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_static_features_e424.py](adamson_cf_g_plugins/r3/random_projection_static_features_e424.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_static_features_e425.py](adamson_cf_g_plugins/r3/random_projection_static_features_e425.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_static_plus_target_res_e607.py](adamson_cf_g_plugins/r3/random_projection_static_plus_target_res_e607.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/random_projection_static_plus_target_var_e436.py](adamson_cf_g_plugins/r3/random_projection_static_plus_target_var_e436.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/same_protein_complex_e93_e102.py](adamson_cf_g_plugins/r3/same_protein_complex_e93_e102.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/shared_compartment_similarity_e559.py](adamson_cf_g_plugins/r3/shared_compartment_similarity_e559.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/shared_tf_binding_count_promoter_e419.py](adamson_cf_g_plugins/r3/shared_tf_binding_count_promoter_e419.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/static_annotation_random_proj_e545_e554.py](adamson_cf_g_plugins/r3/static_annotation_random_proj_e545_e554.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/static_annotation_random_projection_e518.py](adamson_cf_g_plugins/r3/static_annotation_random_projection_e518.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/static_annotation_random_projection_e530.py](adamson_cf_g_plugins/r3/static_annotation_random_projection_e530.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/static_annotation_random_projection_e588.py](adamson_cf_g_plugins/r3/static_annotation_random_projection_e588.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/static_feature_random_projection_e390.py](adamson_cf_g_plugins/r3/static_feature_random_projection_e390.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_annotation_random_projection_e178.py](adamson_cf_g_plugins/r3/target_annotation_random_projection_e178.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_annotation_random_projection_e201.py](adamson_cf_g_plugins/r3/target_annotation_random_projection_e201.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_chromatin_accessibility_e211.py](adamson_cf_g_plugins/r3/target_chromatin_accessibility_e211.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_cpg_oe_promoter_e352.py](adamson_cf_g_plugins/r3/target_cpg_oe_promoter_e352.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_essentiality_e223.py](adamson_cf_g_plugins/r3/target_essentiality_e223.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_essentiality_rank_e445.py](adamson_cf_g_plugins/r3/target_essentiality_rank_e445.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_essentiality_score_e284.py](adamson_cf_g_plugins/r3/target_essentiality_score_e284.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_gc_cds_e188.py](adamson_cf_g_plugins/r3/target_gc_cds_e188.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_gene_constraint_correlation_e682.py](adamson_cf_g_plugins/r3/target_gene_constraint_correlation_e682.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_half_life_interaction_e91.py](adamson_cf_g_plugins/r3/target_half_life_interaction_e91.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_is_nuclear_e35.py](adamson_cf_g_plugins/r3/target_is_nuclear_e35.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_knockdown_proxy_e13.py](adamson_cf_g_plugins/r3/target_knockdown_proxy_e13.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_loeuf_e34.py](adamson_cf_g_plugins/r3/target_loeuf_e34.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_loeuf_rank_e190.py](adamson_cf_g_plugins/r3/target_loeuf_rank_e190.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_loeuf_x_half_life_e134.py](adamson_cf_g_plugins/r3/target_loeuf_x_half_life_e134.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_lof_intolerance_e25.py](adamson_cf_g_plugins/r3/target_lof_intolerance_e25.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_mrna_stability_e363.py](adamson_cf_g_plugins/r3/target_mrna_stability_e363.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_n_exons_e187.py](adamson_cf_g_plugins/r3/target_n_exons_e187.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_neighbor_coexpression_e386.py](adamson_cf_g_plugins/r3/target_neighbor_coexpression_e386.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_pli_e253.py](adamson_cf_g_plugins/r3/target_pli_e253.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_pli_e336.py](adamson_cf_g_plugins/r3/target_pli_e336.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_promoter_accessibility_e365.py](adamson_cf_g_plugins/r3/target_promoter_accessibility_e365.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_promoter_cpg_content_e317.py](adamson_cf_g_plugins/r3/target_promoter_cpg_content_e317.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_promoter_cpg_density_e167.py](adamson_cf_g_plugins/r3/target_promoter_cpg_density_e167.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_promoter_cpg_island_e444.py](adamson_cf_g_plugins/r3/target_promoter_cpg_island_e444.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_promoter_cpg_island_e78.py](adamson_cf_g_plugins/r3/target_promoter_cpg_island_e78.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_protein_half_life_e362.py](adamson_cf_g_plugins/r3/target_protein_half_life_e362.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_protein_length_e186.py](adamson_cf_g_plugins/r3/target_protein_length_e186.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_protein_length_e354.py](adamson_cf_g_plugins/r3/target_protein_length_e354.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_protein_length_e619.py](adamson_cf_g_plugins/r3/target_protein_length_e619.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_protein_length_normalized_e446.py](adamson_cf_g_plugins/r3/target_protein_length_normalized_e446.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/target_transcript_diversity_e640.py](adamson_cf_g_plugins/r3/target_transcript_diversity_e640.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_plugins/r3/tf_binding_site_overlap_e742.py](adamson_cf_g_plugins/r3/tf_binding_site_overlap_e742.py) | Unchanged G comparison source snapshot. |
| [adamson_cf_g_pool.command.txt](adamson_cf_g_pool.command.txt) | Exact command receipt. |
| [adamson_cf_g_pool.exit](adamson_cf_g_pool.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g_pool.log](adamson_cf_g_pool.log) | Captured tool output. |
| [adamson_cf_g_pooled_holm/pooled_holm.json](adamson_cf_g_pooled_holm/pooled_holm.json) | Complete-family pooled step-down null result; legacy filename. |
| [adamson_cf_g_pooled_holm/pooled_holm.md](adamson_cf_g_pooled_holm/pooled_holm.md) | Complete-family pooled step-down null result; legacy filename. |
| [adamson_cf_g_sealed_phase.command.txt](adamson_cf_g_sealed_phase.command.txt) | Exact command receipt. |
| [adamson_cf_g_sealed_phase.exit](adamson_cf_g_sealed_phase.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g_sealed_phase.input_manifest.json](adamson_cf_g_sealed_phase.input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [adamson_cf_g_sealed_phase.log](adamson_cf_g_sealed_phase.log) | Captured tool output. |
| [adamson_cf_g_sealed_summary.json](adamson_cf_g_sealed_summary.json) | Worn-cohort sealed summary; descriptive only. |
| [adamson_cf_g_sealed_summary.md](adamson_cf_g_sealed_summary.md) | Worn-cohort sealed summary; descriptive only. |
| [adamson_cf_g_select.command.txt](adamson_cf_g_select.command.txt) | Exact command receipt. |
| [adamson_cf_g_select.exit](adamson_cf_g_select.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g_select.log](adamson_cf_g_select.log) | Captured tool output. |
| [adamson_cf_g_source_audit.command.txt](adamson_cf_g_source_audit.command.txt) | Exact command receipt. |
| [adamson_cf_g_source_audit.json](adamson_cf_g_source_audit.json) | Static source/direct-table-use and permitted metadata audit. |
| [adamson_cf_g_source_audit.md](adamson_cf_g_source_audit.md) | Static source/direct-table-use and permitted metadata audit. |
| [adamson_cf_g_stage1.command.txt](adamson_cf_g_stage1.command.txt) | Exact command receipt. |
| [adamson_cf_g_stage1.exit](adamson_cf_g_stage1.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g_stage1.log](adamson_cf_g_stage1.log) | Captured tool output. |
| [adamson_cf_g_stage1/feature_compare.json](adamson_cf_g_stage1/feature_compare.json) | Stage1 OOF family-screening result. |
| [adamson_cf_g_stage1/feature_compare.md](adamson_cf_g_stage1/feature_compare.md) | Stage1 OOF family-screening result. |
| [adamson_cf_g_stage2.command.txt](adamson_cf_g_stage2.command.txt) | Exact command receipt. |
| [adamson_cf_g_stage2.exit](adamson_cf_g_stage2.exit) | Explicit terminal exit receipt. |
| [adamson_cf_g_stage2.log](adamson_cf_g_stage2.log) | Captured tool output. |
| [adamson_cf_g_stage2/feature_compare.json](adamson_cf_g_stage2/feature_compare.json) | Stage2 matched-null result. |
| [adamson_cf_g_stage2/feature_compare.md](adamson_cf_g_stage2/feature_compare.md) | Stage2 matched-null result. |
| [adamson_cf_g_top/r0/annotation_nonlinear_interaction_e224.py](adamson_cf_g_top/r0/annotation_nonlinear_interaction_e224.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_nonlinear_interaction_e225.py](adamson_cf_g_top/r0/annotation_nonlinear_interaction_e225.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_projection_elementwise_produc_e350.py](adamson_cf_g_top/r0/annotation_projection_elementwise_produc_e350.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_projection_similarity_v2_e197.py](adamson_cf_g_top/r0/annotation_projection_similarity_v2_e197.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_projection_target_interaction_e149.py](adamson_cf_g_top/r0/annotation_projection_target_interaction_e149.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_projection_target_interaction_e173.py](adamson_cf_g_top/r0/annotation_projection_target_interaction_e173.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_projection_target_interaction_e174.py](adamson_cf_g_top/r0/annotation_projection_target_interaction_e174.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/annotation_random_projection_target_inte_e379.py](adamson_cf_g_top/r0/annotation_random_projection_target_inte_e379.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/chromatin_accessibility_corr_e478.py](adamson_cf_g_top/r0/chromatin_accessibility_corr_e478.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/coessentiality_corr_target_gene_e268.py](adamson_cf_g_top/r0/coessentiality_corr_target_gene_e268.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/coessentiality_interaction_e289.py](adamson_cf_g_top/r0/coessentiality_interaction_e289.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/combined_annotation_ppi_random_projectio_e185.py](adamson_cf_g_top/r0/combined_annotation_ppi_random_projectio_e185.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/combined_annotation_ppi_random_projectio_e548.py](adamson_cf_g_top/r0/combined_annotation_ppi_random_projectio_e548.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/combined_annotation_projection_target_in_e398.py](adamson_cf_g_top/r0/combined_annotation_projection_target_in_e398.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/combined_annotation_projection_x_essenti_e419.py](adamson_cf_g_top/r0/combined_annotation_projection_x_essenti_e419.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/combined_annotation_projection_x_target__e439.py](adamson_cf_g_top/r0/combined_annotation_projection_x_target__e439.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/complex_membership_interaction_e479.py](adamson_cf_g_top/r0/complex_membership_interaction_e479.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/complex_partner_avg_response_e154.py](adamson_cf_g_top/r0/complex_partner_avg_response_e154.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/constraint_flag_x_mean_response_e468.py](adamson_cf_g_top/r0/constraint_flag_x_mean_response_e468.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/constraint_product_exxx_e594.py](adamson_cf_g_top/r0/constraint_product_exxx_e594.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/cpg_island_promoter_interaction_e155.py](adamson_cf_g_top/r0/cpg_island_promoter_interaction_e155.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/cpg_promoter_score_e81.py](adamson_cf_g_top/r0/cpg_promoter_score_e81.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/cpg_target_tf_interaction_e168.py](adamson_cf_g_top/r0/cpg_target_tf_interaction_e168.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/essentiality_response_interaction_e329.py](adamson_cf_g_top/r0/essentiality_response_interaction_e329.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/essentiality_target_x_response_entropy_e433.py](adamson_cf_g_top/r0/essentiality_target_x_response_entropy_e433.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/essentiality_x_response_entropy_e543.py](adamson_cf_g_top/r0/essentiality_x_response_entropy_e543.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/full_annotation_projection_target_e459.py](adamson_cf_g_top/r0/full_annotation_projection_target_e459.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/full_annotation_projection_with_protein_e645.py](adamson_cf_g_top/r0/full_annotation_projection_with_protein_e645.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/gene_annotation_random_projection_e113.py](adamson_cf_g_top/r0/gene_annotation_random_projection_e113.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/gene_loeuf_e94.py](adamson_cf_g_top/r0/gene_loeuf_e94.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/gene_loeuf_x_pathway_response_e712.py](adamson_cf_g_top/r0/gene_loeuf_x_pathway_response_e712.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/gene_loeuf_x_target_selfdelta_e569.py](adamson_cf_g_top/r0/gene_loeuf_x_target_selfdelta_e569.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/gene_set_overlap_x_essentiality_e505.py](adamson_cf_g_top/r0/gene_set_overlap_x_essentiality_e505.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/learned_annotation_projection_interactio_e300.py](adamson_cf_g_top/r0/learned_annotation_projection_interactio_e300.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/loeuf_interaction_squared_e481.py](adamson_cf_g_top/r0/loeuf_interaction_squared_e481.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/loeuf_interaction_target_gene_e601_e578.py](adamson_cf_g_top/r0/loeuf_interaction_target_gene_e601_e578.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/loeuf_product_target_gene_e217.py](adamson_cf_g_top/r0/loeuf_product_target_gene_e217.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/loeuf_weighted_ppi_neighbor_mean_delta_e_e554.py](adamson_cf_g_top/r0/loeuf_weighted_ppi_neighbor_mean_delta_e_e554.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/nuclear_gene_x_loeuf_target_e467.py](adamson_cf_g_top/r0/nuclear_gene_x_loeuf_target_e467.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/nuclear_gene_x_pathway_overlap_interacti_e519.py](adamson_cf_g_top/r0/nuclear_gene_x_pathway_overlap_interacti_e519.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/nuclear_gene_x_target_nuclear_e506.py](adamson_cf_g_top/r0/nuclear_gene_x_target_nuclear_e506.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/nuclear_target_x_gene_loeuf_e697.py](adamson_cf_g_top/r0/nuclear_target_x_gene_loeuf_e697.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/pathway_overlap_weighted_by_essentiality_e516.py](adamson_cf_g_top/r0/pathway_overlap_weighted_by_essentiality_e516.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/pathway_overlap_x_target_loeuf_e407.py](adamson_cf_g_top/r0/pathway_overlap_x_target_loeuf_e407.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/ppi_neighbor_mean_delta_x_target_essenti_e415.py](adamson_cf_g_top/r0/ppi_neighbor_mean_delta_x_target_essenti_e415.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/promoter_cpg_response_e602_e579.py](adamson_cf_g_top/r0/promoter_cpg_response_e602_e579.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/protein_annotation_projection_target_int_e410.py](adamson_cf_g_top/r0/protein_annotation_projection_target_int_e410.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/protein_compartment_flag_e82.py](adamson_cf_g_top/r0/protein_compartment_flag_e82.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/protein_compartment_similarity_e169.py](adamson_cf_g_top/r0/protein_compartment_similarity_e169.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/protein_domain_similarity_e327.py](adamson_cf_g_top/r0/protein_domain_similarity_e327.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/random_projection_annotation_ppi_diffusi_e701.py](adamson_cf_g_top/r0/random_projection_annotation_ppi_diffusi_e701.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/random_projection_annotation_ppi_e525_e539.py](adamson_cf_g_top/r0/random_projection_annotation_ppi_e525_e539.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/random_projection_gene_annotation_e124.py](adamson_cf_g_top/r0/random_projection_gene_annotation_e124.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/rbf_annotation_projection_e606_e584.py](adamson_cf_g_top/r0/rbf_annotation_projection_e606_e584.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/response_entropy_target_essentiality_int_e389.py](adamson_cf_g_top/r0/response_entropy_target_essentiality_int_e389.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/selfdelta_x_cpg_promoter_exxx_e595.py](adamson_cf_g_top/r0/selfdelta_x_cpg_promoter_exxx_e595.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_cpg_x_response_entropy_e614_e619.py](adamson_cf_g_top/r0/target_cpg_x_response_entropy_e614_e619.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_cpg_x_response_entropy_e614_e620.py](adamson_cf_g_top/r0/target_cpg_x_response_entropy_e614_e620.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_essentiality_combo_e50.py](adamson_cf_g_top/r0/target_essentiality_combo_e50.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_essentiality_ppi_neighbor_delta_i_e515.py](adamson_cf_g_top/r0/target_essentiality_ppi_neighbor_delta_i_e515.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_expression_variability_x_loeuf_e417.py](adamson_cf_g_top/r0/target_expression_variability_x_loeuf_e417.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_knockdown_proxy_e14.py](adamson_cf_g_top/r0/target_knockdown_proxy_e14.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_localization_interaction_e403.py](adamson_cf_g_top/r0/target_localization_interaction_e403.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_loeuf_e24.py](adamson_cf_g_top/r0/target_loeuf_e24.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_loeuf_x_mean_response_e404.py](adamson_cf_g_top/r0/target_loeuf_x_mean_response_e404.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_loeuf_x_second_neighbor_response_e746.py](adamson_cf_g_top/r0/target_loeuf_x_second_neighbor_response_e746.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_ppi_neighbor_essentiality_weighte_e764.py](adamson_cf_g_top/r0/target_ppi_neighbor_essentiality_weighte_e764.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_ppi_neighbor_mean_response_loeuf__e775.py](adamson_cf_g_top/r0/target_ppi_neighbor_mean_response_loeuf__e775.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/target_self_delta_x_loeuf_gene_e523_e535.py](adamson_cf_g_top/r0/target_self_delta_x_loeuf_gene_e523_e535.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/tf_binding_overlap_e610_e604.py](adamson_cf_g_top/r0/tf_binding_overlap_e610_e604.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/tf_motif_similarity_target_gene_e269.py](adamson_cf_g_top/r0/tf_motif_similarity_target_gene_e269.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/tf_target_motif_density_e600_e577.py](adamson_cf_g_top/r0/tf_target_motif_density_e600_e577.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/tf_target_overlap_score_e476.py](adamson_cf_g_top/r0/tf_target_overlap_score_e476.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/tfbs_count_promoter_e341.py](adamson_cf_g_top/r0/tfbs_count_promoter_e341.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r0/utr3_length_response_e604_e581.py](adamson_cf_g_top/r0/utr3_length_response_e604_e581.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/chromatin_state_similarity_e720.py](adamson_cf_g_top/r2/chromatin_state_similarity_e720.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/domain_similarity_e123.py](adamson_cf_g_top/r2/domain_similarity_e123.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/localization_overlap_e604_e611.py](adamson_cf_g_top/r2/localization_overlap_e604_e611.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/nearest_neighbor_response_e9.py](adamson_cf_g_top/r2/nearest_neighbor_response_e9.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/promoter_cpg_features_e35.py](adamson_cf_g_top/r2/promoter_cpg_features_e35.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/promoter_motif_similarity_e602_e609.py](adamson_cf_g_top/r2/promoter_motif_similarity_e602_e609.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/protein_stability_proxy_e81.py](adamson_cf_g_top/r2/protein_stability_proxy_e81.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/random_projection_target_annotation_e737.py](adamson_cf_g_top/r2/random_projection_target_annotation_e737.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/random_projection_target_annotation_e750.py](adamson_cf_g_top/r2/random_projection_target_annotation_e750.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/same_compartment_indicator_e268.py](adamson_cf_g_top/r2/same_compartment_indicator_e268.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/same_tad_indicator_e719.py](adamson_cf_g_top/r2/same_tad_indicator_e719.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/shared_cpg_promoter_e195.py](adamson_cf_g_top/r2/shared_cpg_promoter_e195.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/shared_tf_motif_similarity_e175.py](adamson_cf_g_top/r2/shared_tf_motif_similarity_e175.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/stability_x_nuclear_flag_e255.py](adamson_cf_g_top/r2/stability_x_nuclear_flag_e255.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_compartment_flag_e252.py](adamson_cf_g_top/r2/target_compartment_flag_e252.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_compartment_x_gene_annotation_e333.py](adamson_cf_g_top/r2/target_compartment_x_gene_annotation_e333.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_compartment_x_gene_compartment_sp_e566.py](adamson_cf_g_top/r2/target_compartment_x_gene_compartment_sp_e566.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_cpg_oe_promoter_x_is_target_e246.py](adamson_cf_g_top/r2/target_cpg_oe_promoter_x_is_target_e246.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_cpg_promoter_broadcast_e257.py](adamson_cf_g_top/r2/target_cpg_promoter_broadcast_e257.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_cpg_promoter_x_gene_cpg_promoter_e723.py](adamson_cf_g_top/r2/target_cpg_promoter_x_gene_cpg_promoter_e723.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_cpg_promoter_x_gene_loeuf_e526.py](adamson_cf_g_top/r2/target_cpg_promoter_x_gene_loeuf_e526.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_cpg_promoter_x_gene_tf_indicator_e321.py](adamson_cf_g_top/r2/target_cpg_promoter_x_gene_tf_indicator_e321.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_degradation_signal_x_gene_ubiquit_e670.py](adamson_cf_g_top/r2/target_degradation_signal_x_gene_ubiquit_e670.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_depmap_essentiality_e703.py](adamson_cf_g_top/r2/target_depmap_essentiality_e703.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_er_membrane_x_gene_upr_set_e354.py](adamson_cf_g_top/r2/target_er_membrane_x_gene_upr_set_e354.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_essentiality_x_coexpression_e638.py](adamson_cf_g_top/r2/target_essentiality_x_coexpression_e638.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_essentiality_x_gene_constraint_e500.py](adamson_cf_g_top/r2/target_essentiality_x_gene_constraint_e500.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_essentiality_x_gene_loeuf_e512.py](adamson_cf_g_top/r2/target_essentiality_x_gene_loeuf_e512.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_essentiality_x_ppi_interaction_e417.py](adamson_cf_g_top/r2/target_essentiality_x_ppi_interaction_e417.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gc_cds_x_is_target_e243.py](adamson_cf_g_top/r2/target_gc_cds_x_is_target_e243.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_coexpression_rank_x_target_l_e412.py](adamson_cf_g_top/r2/target_gene_coexpression_rank_x_target_l_e412.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_compartment_similarity_e370.py](adamson_cf_g_top/r2/target_gene_compartment_similarity_e370.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_constraint_similarity_e429.py](adamson_cf_g_top/r2/target_gene_constraint_similarity_e429.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_loeuf_product_e537.py](adamson_cf_g_top/r2/target_gene_loeuf_product_e537.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_loeuf_ratio_e477.py](adamson_cf_g_top/r2/target_gene_loeuf_ratio_e477.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_loeuf_similarity_e551.py](adamson_cf_g_top/r2/target_gene_loeuf_similarity_e551.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_shared_domain_count_e454.py](adamson_cf_g_top/r2/target_gene_shared_domain_count_e454.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_shared_domain_count_e589.py](adamson_cf_g_top/r2/target_gene_shared_domain_count_e589.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_shared_domain_count_e694.py](adamson_cf_g_top/r2/target_gene_shared_domain_count_e694.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_shared_domains_count_e510.py](adamson_cf_g_top/r2/target_gene_shared_domains_count_e510.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_gene_shared_protein_domain_e500_e483.py](adamson_cf_g_top/r2/target_gene_shared_protein_domain_e500_e483.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_has_signal_peptide_x_gene_membran_e525.py](adamson_cf_g_top/r2/target_has_signal_peptide_x_gene_membran_e525.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_has_signal_peptide_x_is_target_e247.py](adamson_cf_g_top/r2/target_has_signal_peptide_x_is_target_e247.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_knockdown_magnitude_e32.py](adamson_cf_g_top/r2/target_knockdown_magnitude_e32.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_length_x_gene_function_e269.py](adamson_cf_g_top/r2/target_length_x_gene_function_e269.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_length_x_gene_membrane_propensity_e420.py](adamson_cf_g_top/r2/target_length_x_gene_membrane_propensity_e420.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_length_x_gene_membrane_raw_e538.py](adamson_cf_g_top/r2/target_length_x_gene_membrane_raw_e538.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_localization_entropy_e673.py](adamson_cf_g_top/r2/target_localization_entropy_e673.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_broadcast_e253.py](adamson_cf_g_top/r2/target_loeuf_broadcast_e253.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_coexpression_e264.py](adamson_cf_g_top/r2/target_loeuf_x_coexpression_e264.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_coexpression_rank_e561.py](adamson_cf_g_top/r2/target_loeuf_x_coexpression_rank_e561.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_connectivity_e332.py](adamson_cf_g_top/r2/target_loeuf_x_connectivity_e332.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_control_expression_e523.py](adamson_cf_g_top/r2/target_loeuf_x_gene_control_expression_e523.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_control_mean_e320.py](adamson_cf_g_top/r2/target_loeuf_x_gene_control_mean_e320.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_cv_e397.py](adamson_cf_g_top/r2/target_loeuf_x_gene_cv_e397.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_loeuf_e367.py](adamson_cf_g_top/r2/target_loeuf_x_gene_loeuf_e367.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_loeuf_e380.py](adamson_cf_g_top/r2/target_loeuf_x_gene_loeuf_e380.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_loeuf_squared_e444.py](adamson_cf_g_top/r2/target_loeuf_x_gene_loeuf_squared_e444.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_gene_specificity_e291_e301.py](adamson_cf_g_top/r2/target_loeuf_x_gene_specificity_e291_e301.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_loeuf_x_is_target_e240.py](adamson_cf_g_top/r2/target_loeuf_x_is_target_e240.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_n_exons_x_is_target_e245.py](adamson_cf_g_top/r2/target_n_exons_x_is_target_e245.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_n_transcripts_x_is_target_e242.py](adamson_cf_g_top/r2/target_n_transcripts_x_is_target_e242.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_phospho_density_x_gene_signaling__e672.py](adamson_cf_g_top/r2/target_phospho_density_x_gene_signaling__e672.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_promoter_cpg_strength_x_gene_set__e168.py](adamson_cf_g_top/r2/target_promoter_cpg_strength_x_gene_set__e168.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_promoter_cpg_strength_x_mean_resp_e163.py](adamson_cf_g_top/r2/target_promoter_cpg_strength_x_mean_resp_e163.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_protein_half_life_e671.py](adamson_cf_g_top/r2/target_protein_half_life_e671.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_protein_length_x_gene_binding_fun_e527.py](adamson_cf_g_top/r2/target_protein_length_x_gene_binding_fun_e527.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_protein_length_x_gene_folding_set_e353.py](adamson_cf_g_top/r2/target_protein_length_x_gene_folding_set_e353.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_protein_length_x_gene_membrane_e2_e300.py](adamson_cf_g_top/r2/target_protein_length_x_gene_membrane_e2_e300.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_protein_length_x_is_target_e241.py](adamson_cf_g_top/r2/target_protein_length_x_is_target_e241.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_protein_localization_e53.py](adamson_cf_g_top/r2/target_protein_localization_e53.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_span_x_gene_intron_length_e568.py](adamson_cf_g_top/r2/target_span_x_gene_intron_length_e568.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_stability_x_gene_proteasome_sensi_e725.py](adamson_cf_g_top/r2/target_stability_x_gene_proteasome_sensi_e725.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_tf_x_gene_cpg_promoter_e653.py](adamson_cf_g_top/r2/target_tf_x_gene_cpg_promoter_e653.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/target_tfbs_x_gene_tf_e539.py](adamson_cf_g_top/r2/target_tfbs_x_gene_tf_e539.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r2/weighted_gene_set_similarity_e256.py](adamson_cf_g_top/r2/weighted_gene_set_similarity_e256.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/annotation_random_projection_similarity_e704.py](adamson_cf_g_top/r3/annotation_random_projection_similarity_e704.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/bidirectional_partner_coexpression_e387.py](adamson_cf_g_top/r3/bidirectional_partner_coexpression_e387.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/bidirectional_promoter_indicator_e45.py](adamson_cf_g_top/r3/bidirectional_promoter_indicator_e45.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/chromatin_modifier_cpg_interaction_e87.py](adamson_cf_g_top/r3/chromatin_modifier_cpg_interaction_e87.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/coessentiality_correlation_e725.py](adamson_cf_g_top/r3/coessentiality_correlation_e725.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/coessentiality_correlation_e744.py](adamson_cf_g_top/r3/coessentiality_correlation_e744.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/coessentiality_rank_correlation_e809.py](adamson_cf_g_top/r3/coessentiality_rank_correlation_e809.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/complex_member_target_loeuf_interaction_e116.py](adamson_cf_g_top/r3/complex_member_target_loeuf_interaction_e116.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/cpg_oe_promoter_binary_e44.py](adamson_cf_g_top/r3/cpg_oe_promoter_binary_e44.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/essentiality_interaction_e561.py](adamson_cf_g_top/r3/essentiality_interaction_e561.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/essentiality_interaction_e803.py](adamson_cf_g_top/r3/essentiality_interaction_e803.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/essentiality_times_kurtosis_e629.py](adamson_cf_g_top/r3/essentiality_times_kurtosis_e629.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/gene_annotation_random_projection_e717.py](adamson_cf_g_top/r3/gene_annotation_random_projection_e717.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/gene_annotation_random_projection_e736.py](adamson_cf_g_top/r3/gene_annotation_random_projection_e736.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/gene_annotation_random_projection_tanh_e572.py](adamson_cf_g_top/r3/gene_annotation_random_projection_tanh_e572.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/gene_essentiality_buffering_e92.py](adamson_cf_g_top/r3/gene_essentiality_buffering_e92.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/gene_response_variance_over_essentiality_e651.py](adamson_cf_g_top/r3/gene_response_variance_over_essentiality_e651.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/gene_response_variance_over_target_essen_e430.py](adamson_cf_g_top/r3/gene_response_variance_over_target_essen_e430.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/is_target_x_loeuf_gene_e37.py](adamson_cf_g_top/r3/is_target_x_loeuf_gene_e37.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/mean_response_x_gene_loeuf_e274.py](adamson_cf_g_top/r3/mean_response_x_gene_loeuf_e274.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/prior_knowledge_random_projection_e344.py](adamson_cf_g_top/r3/prior_knowledge_random_projection_e344.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/protein_compartment_similarity_e42.py](adamson_cf_g_top/r3/protein_compartment_similarity_e42.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/protein_domain_similarity_e743.py](adamson_cf_g_top/r3/protein_domain_similarity_e743.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_all_priors_e226.py](adamson_cf_g_top/r3/random_projection_all_priors_e226.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_combined_e542.py](adamson_cf_g_top/r3/random_projection_combined_e542.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_prior_features_e301.py](adamson_cf_g_top/r3/random_projection_prior_features_e301.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_prior_knowledge_e310.py](adamson_cf_g_top/r3/random_projection_prior_knowledge_e310.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_prior_knowledge_e328.py](adamson_cf_g_top/r3/random_projection_prior_knowledge_e328.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_static_features_e409.py](adamson_cf_g_top/r3/random_projection_static_features_e409.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_static_features_e410.py](adamson_cf_g_top/r3/random_projection_static_features_e410.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_static_features_e424.py](adamson_cf_g_top/r3/random_projection_static_features_e424.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_static_features_e425.py](adamson_cf_g_top/r3/random_projection_static_features_e425.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_static_plus_target_res_e607.py](adamson_cf_g_top/r3/random_projection_static_plus_target_res_e607.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/random_projection_static_plus_target_var_e436.py](adamson_cf_g_top/r3/random_projection_static_plus_target_var_e436.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/same_protein_complex_e93_e102.py](adamson_cf_g_top/r3/same_protein_complex_e93_e102.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/shared_compartment_similarity_e559.py](adamson_cf_g_top/r3/shared_compartment_similarity_e559.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/shared_tf_binding_count_promoter_e419.py](adamson_cf_g_top/r3/shared_tf_binding_count_promoter_e419.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/static_annotation_random_proj_e545_e554.py](adamson_cf_g_top/r3/static_annotation_random_proj_e545_e554.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/static_annotation_random_projection_e518.py](adamson_cf_g_top/r3/static_annotation_random_projection_e518.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/static_annotation_random_projection_e530.py](adamson_cf_g_top/r3/static_annotation_random_projection_e530.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/static_annotation_random_projection_e588.py](adamson_cf_g_top/r3/static_annotation_random_projection_e588.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/static_feature_random_projection_e390.py](adamson_cf_g_top/r3/static_feature_random_projection_e390.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_annotation_random_projection_e178.py](adamson_cf_g_top/r3/target_annotation_random_projection_e178.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_annotation_random_projection_e201.py](adamson_cf_g_top/r3/target_annotation_random_projection_e201.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_chromatin_accessibility_e211.py](adamson_cf_g_top/r3/target_chromatin_accessibility_e211.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_cpg_oe_promoter_e352.py](adamson_cf_g_top/r3/target_cpg_oe_promoter_e352.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_essentiality_e223.py](adamson_cf_g_top/r3/target_essentiality_e223.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_essentiality_rank_e445.py](adamson_cf_g_top/r3/target_essentiality_rank_e445.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_essentiality_score_e284.py](adamson_cf_g_top/r3/target_essentiality_score_e284.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_gc_cds_e188.py](adamson_cf_g_top/r3/target_gc_cds_e188.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_gene_constraint_correlation_e682.py](adamson_cf_g_top/r3/target_gene_constraint_correlation_e682.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_half_life_interaction_e91.py](adamson_cf_g_top/r3/target_half_life_interaction_e91.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_is_nuclear_e35.py](adamson_cf_g_top/r3/target_is_nuclear_e35.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_knockdown_proxy_e13.py](adamson_cf_g_top/r3/target_knockdown_proxy_e13.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_loeuf_e34.py](adamson_cf_g_top/r3/target_loeuf_e34.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_loeuf_rank_e190.py](adamson_cf_g_top/r3/target_loeuf_rank_e190.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_loeuf_x_half_life_e134.py](adamson_cf_g_top/r3/target_loeuf_x_half_life_e134.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_mrna_stability_e363.py](adamson_cf_g_top/r3/target_mrna_stability_e363.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_n_exons_e187.py](adamson_cf_g_top/r3/target_n_exons_e187.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_neighbor_coexpression_e386.py](adamson_cf_g_top/r3/target_neighbor_coexpression_e386.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_promoter_accessibility_e365.py](adamson_cf_g_top/r3/target_promoter_accessibility_e365.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_promoter_cpg_content_e317.py](adamson_cf_g_top/r3/target_promoter_cpg_content_e317.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_promoter_cpg_island_e444.py](adamson_cf_g_top/r3/target_promoter_cpg_island_e444.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_promoter_cpg_island_e78.py](adamson_cf_g_top/r3/target_promoter_cpg_island_e78.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_protein_half_life_e362.py](adamson_cf_g_top/r3/target_protein_half_life_e362.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_protein_length_e186.py](adamson_cf_g_top/r3/target_protein_length_e186.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_protein_length_e619.py](adamson_cf_g_top/r3/target_protein_length_e619.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_protein_length_normalized_e446.py](adamson_cf_g_top/r3/target_protein_length_normalized_e446.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/target_transcript_diversity_e640.py](adamson_cf_g_top/r3/target_transcript_diversity_e640.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/r3/tf_binding_site_overlap_e742.py](adamson_cf_g_top/r3/tf_binding_site_overlap_e742.py) | Unchanged G stage2 candidate snapshot. |
| [adamson_cf_g_top/selection.json](adamson_cf_g_top/selection.json) | Complete fixed stage2 family-selection manifest. |

### Norman G — exact new files

| File | Record |
|---|---|
| [norman_g0_r0_sealed_reading.command.txt](norman_g0_r0_sealed_reading.command.txt) | Exact command receipt. |
| [norman_g0_r0_sealed_reading.exit](norman_g0_r0_sealed_reading.exit) | Explicit terminal exit receipt. |
| [norman_g0_r0_sealed_reading.json](norman_g0_r0_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [norman_g0_r0_sealed_reading.log](norman_g0_r0_sealed_reading.log) | Captured tool output. |
| [norman_g0_r0_sealed_reading.md](norman_g0_r0_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [norman_g0_r2_sealed_reading.command.txt](norman_g0_r2_sealed_reading.command.txt) | Exact command receipt. |
| [norman_g0_r2_sealed_reading.exit](norman_g0_r2_sealed_reading.exit) | Explicit terminal exit receipt. |
| [norman_g0_r2_sealed_reading.json](norman_g0_r2_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [norman_g0_r2_sealed_reading.log](norman_g0_r2_sealed_reading.log) | Captured tool output. |
| [norman_g0_r2_sealed_reading.md](norman_g0_r2_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [norman_g0_r3_sealed_reading.command.txt](norman_g0_r3_sealed_reading.command.txt) | Exact command receipt. |
| [norman_g0_r3_sealed_reading.exit](norman_g0_r3_sealed_reading.exit) | Explicit terminal exit receipt. |
| [norman_g0_r3_sealed_reading.json](norman_g0_r3_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [norman_g0_r3_sealed_reading.log](norman_g0_r3_sealed_reading.log) | Captured tool output. |
| [norman_g0_r3_sealed_reading.md](norman_g0_r3_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [norman_g1_r0_sealed_reading.command.txt](norman_g1_r0_sealed_reading.command.txt) | Exact command receipt. |
| [norman_g1_r0_sealed_reading.exit](norman_g1_r0_sealed_reading.exit) | Explicit terminal exit receipt. |
| [norman_g1_r0_sealed_reading.json](norman_g1_r0_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [norman_g1_r0_sealed_reading.log](norman_g1_r0_sealed_reading.log) | Captured tool output. |
| [norman_g1_r0_sealed_reading.md](norman_g1_r0_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [norman_g1_r2_sealed_reading.command.txt](norman_g1_r2_sealed_reading.command.txt) | Exact command receipt. |
| [norman_g1_r2_sealed_reading.exit](norman_g1_r2_sealed_reading.exit) | Explicit terminal exit receipt. |
| [norman_g1_r2_sealed_reading.json](norman_g1_r2_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [norman_g1_r2_sealed_reading.log](norman_g1_r2_sealed_reading.log) | Captured tool output. |
| [norman_g1_r2_sealed_reading.md](norman_g1_r2_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [norman_g1_r3_sealed_reading.command.txt](norman_g1_r3_sealed_reading.command.txt) | Exact command receipt. |
| [norman_g1_r3_sealed_reading.exit](norman_g1_r3_sealed_reading.exit) | Explicit terminal exit receipt. |
| [norman_g1_r3_sealed_reading.json](norman_g1_r3_sealed_reading.json) | Prescribed separate per-run sealed reading. |
| [norman_g1_r3_sealed_reading.log](norman_g1_r3_sealed_reading.log) | Captured tool output. |
| [norman_g1_r3_sealed_reading.md](norman_g1_r3_sealed_reading.md) | Prescribed separate per-run sealed reading. |
| [norman_g1_vs_g0.command.txt](norman_g1_vs_g0.command.txt) | Exact command receipt. |
| [norman_g1_vs_g0.exit](norman_g1_vs_g0.exit) | Explicit terminal exit receipt. |
| [norman_g1_vs_g0.log](norman_g1_vs_g0.log) | Captured tool output. |
| [norman_g1_vs_g0/feature_compare.json](norman_g1_vs_g0/feature_compare.json) | Exact six-run descriptive selected-model OOF comparison. |
| [norman_g1_vs_g0/feature_compare.md](norman_g1_vs_g0/feature_compare.md) | Exact six-run descriptive selected-model OOF comparison. |
| [norman_g1_vs_g0_input_manifest.json](norman_g1_vs_g0_input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [norman_g_arm_summary.json](norman_g_arm_summary.json) | Per-run and arm mean/sample-SD summary. |
| [norman_g_arm_summary.md](norman_g_arm_summary.md) | Per-run and arm mean/sample-SD summary. |
| [norman_g_audit_addendum.json](norman_g_audit_addendum.json) | Independent primary/family/gate audit evidence. |
| [norman_g_audit_addendum.md](norman_g_audit_addendum.md) | Independent primary/family/gate audit evidence. |
| [norman_g_complete_results_issue51.json](norman_g_complete_results_issue51.json) | Issue51 publication body or exact publication receipt. |
| [norman_g_complete_results_issue51.md](norman_g_complete_results_issue51.md) | Issue51 publication body or exact publication receipt. |
| [norman_g_direct_table_audit.json](norman_g_direct_table_audit.json) | Static source/direct-table-use and permitted metadata audit. |
| [norman_g_direct_table_audit.md](norman_g_direct_table_audit.md) | Static source/direct-table-use and permitted metadata audit. |
| [norman_g_input_manifest.json](norman_g_input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [norman_g_plugins/r0/bidirectional_target_overlap_e582.py](norman_g_plugins/r0/bidirectional_target_overlap_e582.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/bidirectional_target_proximity_e566.py](norman_g_plugins/r0/bidirectional_target_proximity_e566.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/chromatin_proximity_to_target_e552.py](norman_g_plugins/r0/chromatin_proximity_to_target_e552.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/compartment_weighted_target_response_sim_e231.py](norman_g_plugins/r0/compartment_weighted_target_response_sim_e231.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/constraint_interaction_e462.py](norman_g_plugins/r0/constraint_interaction_e462.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/constraint_weighted_additive_response_e415.py](norman_g_plugins/r0/constraint_weighted_additive_response_e415.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/constraint_weighted_target_mean_similari_e332.py](norman_g_plugins/r0/constraint_weighted_target_mean_similari_e332.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/constraint_weighted_target_response_simi_e179.py](norman_g_plugins/r0/constraint_weighted_target_response_simi_e179.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/constraint_weighted_target_response_simi_e234.py](norman_g_plugins/r0/constraint_weighted_target_response_simi_e234.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/constraint_weighted_target_similarity_e2_e250.py](norman_g_plugins/r0/constraint_weighted_target_similarity_e2_e250.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/distance_to_nearest_target_tss_e182.py](norman_g_plugins/r0/distance_to_nearest_target_tss_e182.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/distance_weighted_target_similarity_e204.py](norman_g_plugins/r0/distance_weighted_target_similarity_e204.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/essentiality_weighted_response_similarit_e368.py](norman_g_plugins/r0/essentiality_weighted_response_similarit_e368.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/essentiality_weighted_response_similarit_e379.py](norman_g_plugins/r0/essentiality_weighted_response_similarit_e379.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/essentiality_weighted_response_similarit_e397.py](norman_g_plugins/r0/essentiality_weighted_response_similarit_e397.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/gene_annotation_random_projection_e680.py](norman_g_plugins/r0/gene_annotation_random_projection_e680.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/genomic_distance_weighted_neighbor_respo_e635.py](norman_g_plugins/r0/genomic_distance_weighted_neighbor_respo_e635.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/genomic_distance_weighted_response_simil_e581.py](norman_g_plugins/r0/genomic_distance_weighted_response_simil_e581.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/loef_weighted_target_response_similarity_e287.py](norman_g_plugins/r0/loef_weighted_target_response_similarity_e287.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/loeuf_weighted_target_response_similarit_e664.py](norman_g_plugins/r0/loeuf_weighted_target_response_similarit_e664.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/loeuf_weighted_target_similarity_e262.py](norman_g_plugins/r0/loeuf_weighted_target_similarity_e262.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_inverse_weighted_target_response_sim_e274.py](norman_g_plugins/r0/lof_inverse_weighted_target_response_sim_e274.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_response_similarity_interaction_e570.py](norman_g_plugins/r0/lof_response_similarity_interaction_e570.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_weighted_neighbor_response_similarit_e471.py](norman_g_plugins/r0/lof_weighted_neighbor_response_similarit_e471.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_weighted_pair_additivity_residual_e1_e646.py](norman_g_plugins/r0/lof_weighted_pair_additivity_residual_e1_e646.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_weighted_random_projection_e478.py](norman_g_plugins/r0/lof_weighted_random_projection_e478.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_weighted_response_similarity_v2_e495.py](norman_g_plugins/r0/lof_weighted_response_similarity_v2_e495.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/lof_weighted_target_response_similarity_e201.py](norman_g_plugins/r0/lof_weighted_target_response_similarity_e201.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/nearest_target_neighbor_distance_e567.py](norman_g_plugins/r0/nearest_target_neighbor_distance_e567.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/nearest_target_tss_distance_e189.py](norman_g_plugins/r0/nearest_target_tss_distance_e189.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/pair_genomic_distance_e676.py](norman_g_plugins/r0/pair_genomic_distance_e676.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_annotation_random_projection_e668.py](norman_g_plugins/r0/protein_annotation_random_projection_e668.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_feature_weighted_target_similari_e380.py](norman_g_plugins/r0/protein_feature_weighted_target_similari_e380.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_length_weighted_target_similarit_e260.py](norman_g_plugins/r0/protein_length_weighted_target_similarit_e260.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_length_weighted_target_similarit_e263.py](norman_g_plugins/r0/protein_length_weighted_target_similarit_e263.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_localization_similarity_e475.py](norman_g_plugins/r0/protein_localization_similarity_e475.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_localization_similarity_e484.py](norman_g_plugins/r0/protein_localization_similarity_e484.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/protein_localization_similarity_e661.py](norman_g_plugins/r0/protein_localization_similarity_e661.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/random_projection_annotation_target_simi_e692.py](norman_g_plugins/r0/random_projection_annotation_target_simi_e692.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_compartment_diversity_e73.py](norman_g_plugins/r0/target_compartment_diversity_e73.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_constraint_interaction_e553.py](norman_g_plugins/r0/target_constraint_interaction_e553.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_constraint_score_e72.py](norman_g_plugins/r0/target_constraint_score_e72.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_gc_promoter_mean_e427.py](norman_g_plugins/r0/target_gc_promoter_mean_e427.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_loeuf_e544.py](norman_g_plugins/r0/target_loeuf_e544.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_loeuf_interaction_e162.py](norman_g_plugins/r0/target_loeuf_interaction_e162.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_loeuf_mean_e428.py](norman_g_plugins/r0/target_loeuf_mean_e428.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_mean_protein_length_e444.py](norman_g_plugins/r0/target_mean_protein_length_e444.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_promoter_cpg_content_e180.py](norman_g_plugins/r0/target_promoter_cpg_content_e180.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_promoter_cpg_density_e547.py](norman_g_plugins/r0/target_promoter_cpg_density_e547.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_promoter_cpg_interaction_e161.py](norman_g_plugins/r0/target_promoter_cpg_interaction_e161.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_promoter_cpg_oe_e191.py](norman_g_plugins/r0/target_promoter_cpg_oe_e191.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/target_response_similarity_weighted_by_g_e219.py](norman_g_plugins/r0/target_response_similarity_weighted_by_g_e219.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r0/transmembrane_count_difference_e662.py](norman_g_plugins/r0/transmembrane_count_difference_e662.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/is_target_times_target_loeuf_e377.py](norman_g_plugins/r2/is_target_times_target_loeuf_e377.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/is_target_times_target_protein_length_e118.py](norman_g_plugins/r2/is_target_times_target_protein_length_e118.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_aa_fraction_similarity_e341.py](norman_g_plugins/r2/target_aa_fraction_similarity_e341.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_annotation_random_projection_e488.py](norman_g_plugins/r2/target_annotation_random_projection_e488.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_bidirectional_count_e89.py](norman_g_plugins/r2/target_bidirectional_count_e89.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_chromatin_accessibility_mean_e587.py](norman_g_plugins/r2/target_chromatin_accessibility_mean_e587.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_compartment_count_times_additive__e470.py](norman_g_plugins/r2/target_compartment_count_times_additive__e470.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_compartment_diversity_e503.py](norman_g_plugins/r2/target_compartment_diversity_e503.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_compartment_diversity_times_addit_e493.py](norman_g_plugins/r2/target_compartment_diversity_times_addit_e493.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_compartment_similarity_times_addi_e322.py](norman_g_plugins/r2/target_compartment_similarity_times_addi_e322.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_conservation_composite_e265.py](norman_g_plugins/r2/target_conservation_composite_e265.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_conservation_score_e276.py](norman_g_plugins/r2/target_conservation_score_e276.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_conservation_times_additive_e558.py](norman_g_plugins/r2/target_conservation_times_additive_e558.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_constraint_response_e77.py](norman_g_plugins/r2/target_constraint_response_e77.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_mean_nonlinear_e298.py](norman_g_plugins/r2/target_cpg_mean_nonlinear_e298.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_mean_times_additive_response_e375.py](norman_g_plugins/r2/target_cpg_mean_times_additive_response_e375.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_promoter_times_additive_respo_e369.py](norman_g_plugins/r2/target_cpg_promoter_times_additive_respo_e369.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_times_additive_response_e137.py](norman_g_plugins/r2/target_cpg_times_additive_response_e137.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_times_control_mean_e103.py](norman_g_plugins/r2/target_cpg_times_control_mean_e103.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_times_control_mean_e162.py](norman_g_plugins/r2/target_cpg_times_control_mean_e162.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_times_gene_gc_promoter_e115.py](norman_g_plugins/r2/target_cpg_times_gene_gc_promoter_e115.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_times_target_similarity_respo_e174.py](norman_g_plugins/r2/target_cpg_times_target_similarity_respo_e174.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_cpg_variance_times_additive_e578.py](norman_g_plugins/r2/target_cpg_variance_times_additive_e578.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_essentiality_times_additive_e319.py](norman_g_plugins/r2/target_essentiality_times_additive_e319.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_essentiality_times_additive_respo_e450.py](norman_g_plugins/r2/target_essentiality_times_additive_respo_e450.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_exon_count_times_additive_respons_e438.py](norman_g_plugins/r2/target_exon_count_times_additive_respons_e438.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_expression_variance_mean_e585.py](norman_g_plugins/r2/target_expression_variance_mean_e585.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_expression_variance_times_additiv_e596.py](norman_g_plugins/r2/target_expression_variance_times_additiv_e596.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_g_cpg_overlap_e555.py](norman_g_plugins/r2/target_g_cpg_overlap_e555.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_gc_cds_times_additive_response_e435.py](norman_g_plugins/r2/target_gc_cds_times_additive_response_e435.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_gc_promoter_times_additive_e482.py](norman_g_plugins/r2/target_gc_promoter_times_additive_e482.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_gc_promoter_times_additive_e611.py](norman_g_plugins/r2/target_gc_promoter_times_additive_e611.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_gene_essentiality_product_e203.py](norman_g_plugins/r2/target_gene_essentiality_product_e203.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_intron_length_times_additive_e483.py](norman_g_plugins/r2/target_intron_length_times_additive_e483.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_intron_length_times_additive_resp_e437.py](norman_g_plugins/r2/target_intron_length_times_additive_resp_e437.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_additive_interaction_e138.py](norman_g_plugins/r2/target_localization_additive_interaction_e138.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_diversity_e277.py](norman_g_plugins/r2/target_localization_diversity_e277.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_diversity_e397.py](norman_g_plugins/r2/target_localization_diversity_e397.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_diversity_e413.py](norman_g_plugins/r2/target_localization_diversity_e413.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_diversity_e430.py](norman_g_plugins/r2/target_localization_diversity_e430.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_diversity_times_addi_e613.py](norman_g_plugins/r2/target_localization_diversity_times_addi_e613.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_entropy_e539.py](norman_g_plugins/r2/target_localization_entropy_e539.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_localization_entropy_times_additi_e520.py](norman_g_plugins/r2/target_localization_entropy_times_additi_e520.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_mean_e85.py](norman_g_plugins/r2/target_loeuf_mean_e85.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_squared_times_additive_e505.py](norman_g_plugins/r2/target_loeuf_squared_times_additive_e505.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_squared_times_additive_e569.py](norman_g_plugins/r2/target_loeuf_squared_times_additive_e569.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_squared_times_additive_resp_e553.py](norman_g_plugins/r2/target_loeuf_squared_times_additive_resp_e553.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_additive_response_e104.py](norman_g_plugins/r2/target_loeuf_times_additive_response_e104.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_additive_response_v2_e415.py](norman_g_plugins/r2/target_loeuf_times_additive_response_v2_e415.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_control_mean_e116.py](norman_g_plugins/r2/target_loeuf_times_control_mean_e116.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_control_mean_e163.py](norman_g_plugins/r2/target_loeuf_times_control_mean_e163.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_is_target_v2_e149.py](norman_g_plugins/r2/target_loeuf_times_is_target_v2_e149.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_nonadditivity_e331.py](norman_g_plugins/r2/target_loeuf_times_nonadditivity_e331.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_times_target_similarity_res_e173.py](norman_g_plugins/r2/target_loeuf_times_target_similarity_res_e173.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_loeuf_variance_times_additive_e651.py](norman_g_plugins/r2/target_loeuf_variance_times_additive_e651.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_mean_loeuf_times_corr_e230.py](norman_g_plugins/r2/target_mean_loeuf_times_corr_e230.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_membrane_fraction_times_additive__e441.py](norman_g_plugins/r2/target_membrane_fraction_times_additive__e441.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_min_loeuf_times_additive_e661.py](norman_g_plugins/r2/target_min_loeuf_times_additive_e661.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_min_loeuf_times_additive_response_e186.py](norman_g_plugins/r2/target_min_loeuf_times_additive_response_e186.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_n_transcripts_times_additive_e484.py](norman_g_plugins/r2/target_n_transcripts_times_additive_e484.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_neighbor_count_times_additive_e515.py](norman_g_plugins/r2/target_neighbor_count_times_additive_e515.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_neighbor_distance_e105.py](norman_g_plugins/r2/target_neighbor_distance_e105.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_nuclear_fraction_e86.py](norman_g_plugins/r2/target_nuclear_fraction_e86.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e148.py](norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e148.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e159.py](norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e159.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e370.py](norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e370.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e384.py](norman_g_plugins/r2/target_nuclear_fraction_times_additive_r_e384.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_nucleus_fraction_times_additive_r_e442.py](norman_g_plugins/r2/target_nucleus_fraction_times_additive_r_e442.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_pair_nonadditivity_protein_length_e498.py](norman_g_plugins/r2/target_pair_nonadditivity_protein_length_e498.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_pli_times_additive_response_e216.py](norman_g_plugins/r2/target_pli_times_additive_response_e216.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_pli_times_additive_response_e475.py](norman_g_plugins/r2/target_pli_times_additive_response_e475.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_ppi_degree_mean_e300.py](norman_g_plugins/r2/target_ppi_degree_mean_e300.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_promoter_activity_score_e537.py](norman_g_plugins/r2/target_promoter_activity_score_e537.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_promoter_cpg_oe_e84.py](norman_g_plugins/r2/target_promoter_cpg_oe_e84.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_promoter_gc_similarity_e551.py](norman_g_plugins/r2/target_promoter_gc_similarity_e551.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_cv_e460.py](norman_g_plugins/r2/target_protein_length_cv_e460.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_e52.py](norman_g_plugins/r2/target_protein_length_e52.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_mean_e231.py](norman_g_plugins/r2/target_protein_length_mean_e231.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_mean_squared_e670.py](norman_g_plugins/r2/target_protein_length_mean_squared_e670.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_ratio_times_additi_e517.py](norman_g_plugins/r2/target_protein_length_ratio_times_additi_e517.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_squared_times_addi_e440.py](norman_g_plugins/r2/target_protein_length_squared_times_addi_e440.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_protein_length_times_additive_e217.py](norman_g_plugins/r2/target_protein_length_times_additive_e217.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_transcript_count_times_additive_r_e439.py](norman_g_plugins/r2/target_transcript_count_times_additive_r_e439.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_upstream_atg_times_additive_e612.py](norman_g_plugins/r2/target_upstream_atg_times_additive_e612.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_utr5_length_times_additive_e429.py](norman_g_plugins/r2/target_utr5_length_times_additive_e429.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_utr5_length_times_additive_respon_e436.py](norman_g_plugins/r2/target_utr5_length_times_additive_respon_e436.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r2/target_weighted_cpg_promoter_e459.py](norman_g_plugins/r2/target_weighted_cpg_promoter_e459.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_compartment_similari_e461.py](norman_g_plugins/r3/additive_response_x_compartment_similari_e461.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_constraint_e170_e182.py](norman_g_plugins/r3/additive_response_x_constraint_e170_e182.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_gene_constraint_e315.py](norman_g_plugins/r3/additive_response_x_gene_constraint_e315.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_gene_essentiality_e4_e399.py](norman_g_plugins/r3/additive_response_x_gene_essentiality_e4_e399.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_loeuf_e203.py](norman_g_plugins/r3/additive_response_x_loeuf_e203.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_log_target_protein_l_e466.py](norman_g_plugins/r3/additive_response_x_log_target_protein_l_e466.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_conservation_e662.py](norman_g_plugins/r3/additive_response_x_target_conservation_e662.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_constraint_e1_e138.py](norman_g_plugins/r3/additive_response_x_target_constraint_e1_e138.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_constraint_e302.py](norman_g_plugins/r3/additive_response_x_target_constraint_e302.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_constraint_e360.py](norman_g_plugins/r3/additive_response_x_target_constraint_e360.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_constraint_e81.py](norman_g_plugins/r3/additive_response_x_target_constraint_e81.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_constraint_v2_e154.py](norman_g_plugins/r3/additive_response_x_target_constraint_v2_e154.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_constraint_v2_e171.py](norman_g_plugins/r3/additive_response_x_target_constraint_v2_e171.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_cpg_oe_e523.py](norman_g_plugins/r3/additive_response_x_target_cpg_oe_e523.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_cytoplasm_e543.py](norman_g_plugins/r3/additive_response_x_target_cytoplasm_e543.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_essentiality_e391.py](norman_g_plugins/r3/additive_response_x_target_essentiality_e391.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_essentiality_e419.py](norman_g_plugins/r3/additive_response_x_target_essentiality_e419.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_essentiality_e448.py](norman_g_plugins/r3/additive_response_x_target_essentiality_e448.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_essentiality_e658.py](norman_g_plugins/r3/additive_response_x_target_essentiality_e658.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_gc_cds_e575.py](norman_g_plugins/r3/additive_response_x_target_gc_cds_e575.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_gc_promoter_e312.py](norman_g_plugins/r3/additive_response_x_target_gc_promoter_e312.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_loeuf_e535.py](norman_g_plugins/r3/additive_response_x_target_loeuf_e535.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_lof_intoleran_e412.py](norman_g_plugins/r3/additive_response_x_target_lof_intoleran_e412.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_membrane_e544.py](norman_g_plugins/r3/additive_response_x_target_membrane_e544.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_membrane_secr_e559.py](norman_g_plugins/r3/additive_response_x_target_membrane_secr_e559.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_n_transcripts_e220.py](norman_g_plugins/r3/additive_response_x_target_n_transcripts_e220.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_n_transcripts_e574.py](norman_g_plugins/r3/additive_response_x_target_n_transcripts_e574.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_nuclear_cytop_e648.py](norman_g_plugins/r3/additive_response_x_target_nuclear_cytop_e648.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_nuclear_e542.py](norman_g_plugins/r3/additive_response_x_target_nuclear_e542.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_nuclear_local_e530.py](norman_g_plugins/r3/additive_response_x_target_nuclear_local_e530.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_promoter_cpg__e644.py](norman_g_plugins/r3/additive_response_x_target_promoter_cpg__e644.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_promoter_cpg_e589.py](norman_g_plugins/r3/additive_response_x_target_promoter_cpg_e589.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_promoter_gc_e447.py](norman_g_plugins/r3/additive_response_x_target_promoter_gc_e447.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_protein_lengt_e442.py](norman_g_plugins/r3/additive_response_x_target_protein_lengt_e442.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_protein_lengt_e453.py](norman_g_plugins/r3/additive_response_x_target_protein_lengt_e453.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_protein_lengt_e657.py](norman_g_plugins/r3/additive_response_x_target_protein_lengt_e657.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/additive_response_x_target_total_protein_e573.py](norman_g_plugins/r3/additive_response_x_target_total_protein_e573.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/bidirectional_promoter_overlap_e252.py](norman_g_plugins/r3/bidirectional_promoter_overlap_e252.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/chromatin_state_similarity_with_target_e634.py](norman_g_plugins/r3/chromatin_state_similarity_with_target_e634.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/compartment_overlap_with_target_e82.py](norman_g_plugins/r3/compartment_overlap_with_target_e82.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/compartment_overlap_with_target_v2_e170.py](norman_g_plugins/r3/compartment_overlap_with_target_v2_e170.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/essentiality_interaction_e281.py](norman_g_plugins/r3/essentiality_interaction_e281.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/pair_target_compartment_similarity_e431.py](norman_g_plugins/r3/pair_target_compartment_similarity_e431.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/pair_target_constraint_aggregate_e433.py](norman_g_plugins/r3/pair_target_constraint_aggregate_e433.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/pair_target_constraint_interaction_e242.py](norman_g_plugins/r3/pair_target_constraint_interaction_e242.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/pair_target_constraint_product_e476.py](norman_g_plugins/r3/pair_target_constraint_product_e476.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/pair_target_constraint_product_interacti_e462.py](norman_g_plugins/r3/pair_target_constraint_product_interacti_e462.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/pair_target_lof_intolerance_e253.py](norman_g_plugins/r3/pair_target_lof_intolerance_e253.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/ppi_distance_weighted_constraint_e118.py](norman_g_plugins/r3/ppi_distance_weighted_constraint_e118.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/promoter_cpg_overlap_with_target_e519.py](norman_g_plugins/r3/promoter_cpg_overlap_with_target_e519.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/promoter_motif_count_for_target_tf_e361.py](norman_g_plugins/r3/promoter_motif_count_for_target_tf_e361.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/promoter_motif_divergence_to_target_e609.py](norman_g_plugins/r3/promoter_motif_divergence_to_target_e609.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/promoter_motif_similarity_to_target_e623.py](norman_g_plugins/r3/promoter_motif_similarity_to_target_e623.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/promoter_motif_similarity_with_target_e660.py](norman_g_plugins/r3/promoter_motif_similarity_with_target_e660.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/protein_compartment_overlap_e77.py](norman_g_plugins/r3/protein_compartment_overlap_e77.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/protein_domain_random_projection_e613.py](norman_g_plugins/r3/protein_domain_random_projection_e613.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/protein_localization_similarity_e251.py](norman_g_plugins/r3/protein_localization_similarity_e251.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_chromatin_accessibility_e590.py](norman_g_plugins/r3/target_chromatin_accessibility_e590.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_compartment_similarity_e121_e135.py](norman_g_plugins/r3/target_compartment_similarity_e121_e135.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_constraint_e59.py](norman_g_plugins/r3/target_constraint_e59.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_constraint_interaction_e91.py](norman_g_plugins/r3/target_constraint_interaction_e91.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_cpg_island_overlap_e125_e139.py](norman_g_plugins/r3/target_cpg_island_overlap_e125_e139.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_cpg_promoter_e190.py](norman_g_plugins/r3/target_cpg_promoter_e190.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_essentiality_score_e380.py](norman_g_plugins/r3/target_essentiality_score_e380.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_gene_compartment_overlap_e411.py](norman_g_plugins/r3/target_gene_compartment_overlap_e411.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_gene_cpg_similarity_e304.py](norman_g_plugins/r3/target_gene_cpg_similarity_e304.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_gene_motif_similarity_e262.py](norman_g_plugins/r3/target_gene_motif_similarity_e262.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_localization_overlap_e92.py](norman_g_plugins/r3/target_localization_overlap_e92.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_localization_similarity_e239.py](norman_g_plugins/r3/target_localization_similarity_e239.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_localization_similarity_e263.py](norman_g_plugins/r3/target_localization_similarity_e263.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_localization_similarity_e520.py](norman_g_plugins/r3/target_localization_similarity_e520.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_lof_intolerance_e191.py](norman_g_plugins/r3/target_lof_intolerance_e191.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_promoter_accessibility_proxy_e379.py](norman_g_plugins/r3/target_promoter_accessibility_proxy_e379.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_promoter_cpg_density_e201.py](norman_g_plugins/r3/target_promoter_cpg_density_e201.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_promoter_cpg_island_e375.py](norman_g_plugins/r3/target_promoter_cpg_island_e375.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_promoter_cpg_island_e534.py](norman_g_plugins/r3/target_promoter_cpg_island_e534.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_property_modulated_response_e105.py](norman_g_plugins/r3/target_property_modulated_response_e105.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_protein_length_x_constraint_e477.py](norman_g_plugins/r3/target_protein_length_x_constraint_e477.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_tf_binding_site_count_e510.py](norman_g_plugins/r3/target_tf_binding_site_count_e510.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_tf_motif_enrichment_e331_e347.py](norman_g_plugins/r3/target_tf_motif_enrichment_e331_e347.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_tfbs_count_e204.py](norman_g_plugins/r3/target_tfbs_count_e204.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/target_transmembrane_count_interaction_e531.py](norman_g_plugins/r3/target_transmembrane_count_interaction_e531.py) | Unchanged G comparison source snapshot. |
| [norman_g_plugins/r3/tf_motif_promoter_score_e119.py](norman_g_plugins/r3/tf_motif_promoter_score_e119.py) | Unchanged G comparison source snapshot. |
| [norman_g_pool.command.txt](norman_g_pool.command.txt) | Exact command receipt. |
| [norman_g_pool.exit](norman_g_pool.exit) | Explicit terminal exit receipt. |
| [norman_g_pool.log](norman_g_pool.log) | Captured tool output. |
| [norman_g_pooled_holm/pooled_holm.json](norman_g_pooled_holm/pooled_holm.json) | Complete-family pooled step-down null result; legacy filename. |
| [norman_g_pooled_holm/pooled_holm.md](norman_g_pooled_holm/pooled_holm.md) | Complete-family pooled step-down null result; legacy filename. |
| [norman_g_primary_audit.json](norman_g_primary_audit.json) | Independent primary/family/gate audit evidence. |
| [norman_g_primary_audit.md](norman_g_primary_audit.md) | Independent primary/family/gate audit evidence. |
| [norman_g_sealed_audit.json](norman_g_sealed_audit.json) | New sealed output arithmetic/integrity audit. |
| [norman_g_sealed_audit.md](norman_g_sealed_audit.md) | New sealed output arithmetic/integrity audit. |
| [norman_g_sealed_phase.command.txt](norman_g_sealed_phase.command.txt) | Exact command receipt. |
| [norman_g_sealed_phase.exit](norman_g_sealed_phase.exit) | Explicit terminal exit receipt. |
| [norman_g_sealed_phase.input_manifest.json](norman_g_sealed_phase.input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [norman_g_sealed_phase.log](norman_g_sealed_phase.log) | Captured tool output. |
| [norman_g_sealed_summary.json](norman_g_sealed_summary.json) | Worn-cohort sealed summary; descriptive only. |
| [norman_g_sealed_summary.md](norman_g_sealed_summary.md) | Worn-cohort sealed summary; descriptive only. |
| [norman_g_select.command.txt](norman_g_select.command.txt) | Exact command receipt. |
| [norman_g_select.exit](norman_g_select.exit) | Explicit terminal exit receipt. |
| [norman_g_select.log](norman_g_select.log) | Captured tool output. |
| [norman_g_source_audit.command.txt](norman_g_source_audit.command.txt) | Exact command receipt. |
| [norman_g_source_audit.json](norman_g_source_audit.json) | Static source/direct-table-use and permitted metadata audit. |
| [norman_g_source_audit.md](norman_g_source_audit.md) | Static source/direct-table-use and permitted metadata audit. |
| [norman_g_stage1.command.txt](norman_g_stage1.command.txt) | Exact command receipt. |
| [norman_g_stage1.exit](norman_g_stage1.exit) | Explicit terminal exit receipt. |
| [norman_g_stage1.log](norman_g_stage1.log) | Captured tool output. |
| [norman_g_stage1/feature_compare.json](norman_g_stage1/feature_compare.json) | Stage1 OOF family-screening result. |
| [norman_g_stage1/feature_compare.md](norman_g_stage1/feature_compare.md) | Stage1 OOF family-screening result. |
| [norman_g_stage2.command.txt](norman_g_stage2.command.txt) | Exact command receipt. |
| [norman_g_stage2.exit](norman_g_stage2.exit) | Explicit terminal exit receipt. |
| [norman_g_stage2.log](norman_g_stage2.log) | Captured tool output. |
| [norman_g_stage2/feature_compare.json](norman_g_stage2/feature_compare.json) | Stage2 matched-null result. |
| [norman_g_stage2/feature_compare.md](norman_g_stage2/feature_compare.md) | Stage2 matched-null result. |
| [norman_g_top/r0/bidirectional_target_overlap_e582.py](norman_g_top/r0/bidirectional_target_overlap_e582.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/bidirectional_target_proximity_e566.py](norman_g_top/r0/bidirectional_target_proximity_e566.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/chromatin_proximity_to_target_e552.py](norman_g_top/r0/chromatin_proximity_to_target_e552.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/compartment_weighted_target_response_sim_e231.py](norman_g_top/r0/compartment_weighted_target_response_sim_e231.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/constraint_interaction_e462.py](norman_g_top/r0/constraint_interaction_e462.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/constraint_weighted_additive_response_e415.py](norman_g_top/r0/constraint_weighted_additive_response_e415.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/constraint_weighted_target_response_simi_e179.py](norman_g_top/r0/constraint_weighted_target_response_simi_e179.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/constraint_weighted_target_response_simi_e234.py](norman_g_top/r0/constraint_weighted_target_response_simi_e234.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/constraint_weighted_target_similarity_e2_e250.py](norman_g_top/r0/constraint_weighted_target_similarity_e2_e250.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/distance_to_nearest_target_tss_e182.py](norman_g_top/r0/distance_to_nearest_target_tss_e182.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/distance_weighted_target_similarity_e204.py](norman_g_top/r0/distance_weighted_target_similarity_e204.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/essentiality_weighted_response_similarit_e379.py](norman_g_top/r0/essentiality_weighted_response_similarit_e379.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/essentiality_weighted_response_similarit_e397.py](norman_g_top/r0/essentiality_weighted_response_similarit_e397.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/gene_annotation_random_projection_e680.py](norman_g_top/r0/gene_annotation_random_projection_e680.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/genomic_distance_weighted_neighbor_respo_e635.py](norman_g_top/r0/genomic_distance_weighted_neighbor_respo_e635.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/genomic_distance_weighted_response_simil_e581.py](norman_g_top/r0/genomic_distance_weighted_response_simil_e581.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/loef_weighted_target_response_similarity_e287.py](norman_g_top/r0/loef_weighted_target_response_similarity_e287.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/loeuf_weighted_target_response_similarit_e664.py](norman_g_top/r0/loeuf_weighted_target_response_similarit_e664.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/loeuf_weighted_target_similarity_e262.py](norman_g_top/r0/loeuf_weighted_target_similarity_e262.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/lof_response_similarity_interaction_e570.py](norman_g_top/r0/lof_response_similarity_interaction_e570.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/lof_weighted_neighbor_response_similarit_e471.py](norman_g_top/r0/lof_weighted_neighbor_response_similarit_e471.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/lof_weighted_pair_additivity_residual_e1_e646.py](norman_g_top/r0/lof_weighted_pair_additivity_residual_e1_e646.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/lof_weighted_random_projection_e478.py](norman_g_top/r0/lof_weighted_random_projection_e478.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/lof_weighted_response_similarity_v2_e495.py](norman_g_top/r0/lof_weighted_response_similarity_v2_e495.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/lof_weighted_target_response_similarity_e201.py](norman_g_top/r0/lof_weighted_target_response_similarity_e201.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/nearest_target_neighbor_distance_e567.py](norman_g_top/r0/nearest_target_neighbor_distance_e567.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/nearest_target_tss_distance_e189.py](norman_g_top/r0/nearest_target_tss_distance_e189.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/pair_genomic_distance_e676.py](norman_g_top/r0/pair_genomic_distance_e676.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/protein_annotation_random_projection_e668.py](norman_g_top/r0/protein_annotation_random_projection_e668.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/protein_feature_weighted_target_similari_e380.py](norman_g_top/r0/protein_feature_weighted_target_similari_e380.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/protein_length_weighted_target_similarit_e260.py](norman_g_top/r0/protein_length_weighted_target_similarit_e260.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/protein_length_weighted_target_similarit_e263.py](norman_g_top/r0/protein_length_weighted_target_similarit_e263.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/protein_localization_similarity_e475.py](norman_g_top/r0/protein_localization_similarity_e475.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/protein_localization_similarity_e661.py](norman_g_top/r0/protein_localization_similarity_e661.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/random_projection_annotation_target_simi_e692.py](norman_g_top/r0/random_projection_annotation_target_simi_e692.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_compartment_diversity_e73.py](norman_g_top/r0/target_compartment_diversity_e73.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_constraint_interaction_e553.py](norman_g_top/r0/target_constraint_interaction_e553.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_constraint_score_e72.py](norman_g_top/r0/target_constraint_score_e72.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_gc_promoter_mean_e427.py](norman_g_top/r0/target_gc_promoter_mean_e427.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_loeuf_interaction_e162.py](norman_g_top/r0/target_loeuf_interaction_e162.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_mean_protein_length_e444.py](norman_g_top/r0/target_mean_protein_length_e444.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_promoter_cpg_density_e547.py](norman_g_top/r0/target_promoter_cpg_density_e547.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/target_response_similarity_weighted_by_g_e219.py](norman_g_top/r0/target_response_similarity_weighted_by_g_e219.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r0/transmembrane_count_difference_e662.py](norman_g_top/r0/transmembrane_count_difference_e662.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/is_target_times_target_loeuf_e377.py](norman_g_top/r2/is_target_times_target_loeuf_e377.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/is_target_times_target_protein_length_e118.py](norman_g_top/r2/is_target_times_target_protein_length_e118.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_aa_fraction_similarity_e341.py](norman_g_top/r2/target_aa_fraction_similarity_e341.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_annotation_random_projection_e488.py](norman_g_top/r2/target_annotation_random_projection_e488.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_bidirectional_count_e89.py](norman_g_top/r2/target_bidirectional_count_e89.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_chromatin_accessibility_mean_e587.py](norman_g_top/r2/target_chromatin_accessibility_mean_e587.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_compartment_count_times_additive__e470.py](norman_g_top/r2/target_compartment_count_times_additive__e470.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_compartment_diversity_e503.py](norman_g_top/r2/target_compartment_diversity_e503.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_compartment_diversity_times_addit_e493.py](norman_g_top/r2/target_compartment_diversity_times_addit_e493.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_compartment_similarity_times_addi_e322.py](norman_g_top/r2/target_compartment_similarity_times_addi_e322.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_conservation_composite_e265.py](norman_g_top/r2/target_conservation_composite_e265.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_conservation_score_e276.py](norman_g_top/r2/target_conservation_score_e276.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_conservation_times_additive_e558.py](norman_g_top/r2/target_conservation_times_additive_e558.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_constraint_response_e77.py](norman_g_top/r2/target_constraint_response_e77.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_cpg_mean_nonlinear_e298.py](norman_g_top/r2/target_cpg_mean_nonlinear_e298.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_cpg_mean_times_additive_response_e375.py](norman_g_top/r2/target_cpg_mean_times_additive_response_e375.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_cpg_promoter_times_additive_respo_e369.py](norman_g_top/r2/target_cpg_promoter_times_additive_respo_e369.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_cpg_times_control_mean_e103.py](norman_g_top/r2/target_cpg_times_control_mean_e103.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_cpg_times_gene_gc_promoter_e115.py](norman_g_top/r2/target_cpg_times_gene_gc_promoter_e115.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_cpg_variance_times_additive_e578.py](norman_g_top/r2/target_cpg_variance_times_additive_e578.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_exon_count_times_additive_respons_e438.py](norman_g_top/r2/target_exon_count_times_additive_respons_e438.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_expression_variance_mean_e585.py](norman_g_top/r2/target_expression_variance_mean_e585.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_expression_variance_times_additiv_e596.py](norman_g_top/r2/target_expression_variance_times_additiv_e596.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_g_cpg_overlap_e555.py](norman_g_top/r2/target_g_cpg_overlap_e555.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_gc_cds_times_additive_response_e435.py](norman_g_top/r2/target_gc_cds_times_additive_response_e435.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_gc_promoter_times_additive_e482.py](norman_g_top/r2/target_gc_promoter_times_additive_e482.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_gene_essentiality_product_e203.py](norman_g_top/r2/target_gene_essentiality_product_e203.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_intron_length_times_additive_e483.py](norman_g_top/r2/target_intron_length_times_additive_e483.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_localization_additive_interaction_e138.py](norman_g_top/r2/target_localization_additive_interaction_e138.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_localization_diversity_e277.py](norman_g_top/r2/target_localization_diversity_e277.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_localization_diversity_times_addi_e613.py](norman_g_top/r2/target_localization_diversity_times_addi_e613.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_squared_times_additive_e505.py](norman_g_top/r2/target_loeuf_squared_times_additive_e505.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_squared_times_additive_resp_e553.py](norman_g_top/r2/target_loeuf_squared_times_additive_resp_e553.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_times_additive_response_e104.py](norman_g_top/r2/target_loeuf_times_additive_response_e104.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_times_additive_response_v2_e415.py](norman_g_top/r2/target_loeuf_times_additive_response_v2_e415.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_times_control_mean_e116.py](norman_g_top/r2/target_loeuf_times_control_mean_e116.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_times_control_mean_e163.py](norman_g_top/r2/target_loeuf_times_control_mean_e163.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_times_nonadditivity_e331.py](norman_g_top/r2/target_loeuf_times_nonadditivity_e331.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_loeuf_variance_times_additive_e651.py](norman_g_top/r2/target_loeuf_variance_times_additive_e651.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_mean_loeuf_times_corr_e230.py](norman_g_top/r2/target_mean_loeuf_times_corr_e230.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_membrane_fraction_times_additive__e441.py](norman_g_top/r2/target_membrane_fraction_times_additive__e441.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_min_loeuf_times_additive_e661.py](norman_g_top/r2/target_min_loeuf_times_additive_e661.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_n_transcripts_times_additive_e484.py](norman_g_top/r2/target_n_transcripts_times_additive_e484.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_neighbor_count_times_additive_e515.py](norman_g_top/r2/target_neighbor_count_times_additive_e515.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_neighbor_distance_e105.py](norman_g_top/r2/target_neighbor_distance_e105.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_nuclear_fraction_e86.py](norman_g_top/r2/target_nuclear_fraction_e86.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_nuclear_fraction_times_additive_r_e148.py](norman_g_top/r2/target_nuclear_fraction_times_additive_r_e148.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_pli_times_additive_response_e216.py](norman_g_top/r2/target_pli_times_additive_response_e216.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_pli_times_additive_response_e475.py](norman_g_top/r2/target_pli_times_additive_response_e475.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_ppi_degree_mean_e300.py](norman_g_top/r2/target_ppi_degree_mean_e300.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_promoter_activity_score_e537.py](norman_g_top/r2/target_promoter_activity_score_e537.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_promoter_cpg_oe_e84.py](norman_g_top/r2/target_promoter_cpg_oe_e84.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_promoter_gc_similarity_e551.py](norman_g_top/r2/target_promoter_gc_similarity_e551.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_protein_length_cv_e460.py](norman_g_top/r2/target_protein_length_cv_e460.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_protein_length_e52.py](norman_g_top/r2/target_protein_length_e52.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_protein_length_mean_squared_e670.py](norman_g_top/r2/target_protein_length_mean_squared_e670.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_protein_length_ratio_times_additi_e517.py](norman_g_top/r2/target_protein_length_ratio_times_additi_e517.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_protein_length_squared_times_addi_e440.py](norman_g_top/r2/target_protein_length_squared_times_addi_e440.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_protein_length_times_additive_e217.py](norman_g_top/r2/target_protein_length_times_additive_e217.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_upstream_atg_times_additive_e612.py](norman_g_top/r2/target_upstream_atg_times_additive_e612.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_utr5_length_times_additive_e429.py](norman_g_top/r2/target_utr5_length_times_additive_e429.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r2/target_weighted_cpg_promoter_e459.py](norman_g_top/r2/target_weighted_cpg_promoter_e459.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_compartment_similari_e461.py](norman_g_top/r3/additive_response_x_compartment_similari_e461.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_constraint_e170_e182.py](norman_g_top/r3/additive_response_x_constraint_e170_e182.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_gene_constraint_e315.py](norman_g_top/r3/additive_response_x_gene_constraint_e315.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_gene_essentiality_e4_e399.py](norman_g_top/r3/additive_response_x_gene_essentiality_e4_e399.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_loeuf_e203.py](norman_g_top/r3/additive_response_x_loeuf_e203.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_log_target_protein_l_e466.py](norman_g_top/r3/additive_response_x_log_target_protein_l_e466.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_conservation_e662.py](norman_g_top/r3/additive_response_x_target_conservation_e662.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_constraint_e1_e138.py](norman_g_top/r3/additive_response_x_target_constraint_e1_e138.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_constraint_e302.py](norman_g_top/r3/additive_response_x_target_constraint_e302.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_constraint_e360.py](norman_g_top/r3/additive_response_x_target_constraint_e360.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_constraint_e81.py](norman_g_top/r3/additive_response_x_target_constraint_e81.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_constraint_v2_e154.py](norman_g_top/r3/additive_response_x_target_constraint_v2_e154.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_constraint_v2_e171.py](norman_g_top/r3/additive_response_x_target_constraint_v2_e171.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_cpg_oe_e523.py](norman_g_top/r3/additive_response_x_target_cpg_oe_e523.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_cytoplasm_e543.py](norman_g_top/r3/additive_response_x_target_cytoplasm_e543.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_essentiality_e391.py](norman_g_top/r3/additive_response_x_target_essentiality_e391.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_essentiality_e448.py](norman_g_top/r3/additive_response_x_target_essentiality_e448.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_gc_cds_e575.py](norman_g_top/r3/additive_response_x_target_gc_cds_e575.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_gc_promoter_e312.py](norman_g_top/r3/additive_response_x_target_gc_promoter_e312.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_loeuf_e535.py](norman_g_top/r3/additive_response_x_target_loeuf_e535.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_membrane_e544.py](norman_g_top/r3/additive_response_x_target_membrane_e544.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_membrane_secr_e559.py](norman_g_top/r3/additive_response_x_target_membrane_secr_e559.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_n_transcripts_e220.py](norman_g_top/r3/additive_response_x_target_n_transcripts_e220.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_n_transcripts_e574.py](norman_g_top/r3/additive_response_x_target_n_transcripts_e574.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_nuclear_cytop_e648.py](norman_g_top/r3/additive_response_x_target_nuclear_cytop_e648.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_nuclear_e542.py](norman_g_top/r3/additive_response_x_target_nuclear_e542.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_nuclear_local_e530.py](norman_g_top/r3/additive_response_x_target_nuclear_local_e530.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_promoter_cpg_e589.py](norman_g_top/r3/additive_response_x_target_promoter_cpg_e589.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_promoter_gc_e447.py](norman_g_top/r3/additive_response_x_target_promoter_gc_e447.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_protein_lengt_e442.py](norman_g_top/r3/additive_response_x_target_protein_lengt_e442.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_protein_lengt_e453.py](norman_g_top/r3/additive_response_x_target_protein_lengt_e453.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_protein_lengt_e657.py](norman_g_top/r3/additive_response_x_target_protein_lengt_e657.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/additive_response_x_target_total_protein_e573.py](norman_g_top/r3/additive_response_x_target_total_protein_e573.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/bidirectional_promoter_overlap_e252.py](norman_g_top/r3/bidirectional_promoter_overlap_e252.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/chromatin_state_similarity_with_target_e634.py](norman_g_top/r3/chromatin_state_similarity_with_target_e634.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/compartment_overlap_with_target_e82.py](norman_g_top/r3/compartment_overlap_with_target_e82.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/compartment_overlap_with_target_v2_e170.py](norman_g_top/r3/compartment_overlap_with_target_v2_e170.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/essentiality_interaction_e281.py](norman_g_top/r3/essentiality_interaction_e281.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/pair_target_compartment_similarity_e431.py](norman_g_top/r3/pair_target_compartment_similarity_e431.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/pair_target_constraint_aggregate_e433.py](norman_g_top/r3/pair_target_constraint_aggregate_e433.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/pair_target_constraint_interaction_e242.py](norman_g_top/r3/pair_target_constraint_interaction_e242.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/pair_target_constraint_product_e476.py](norman_g_top/r3/pair_target_constraint_product_e476.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/pair_target_constraint_product_interacti_e462.py](norman_g_top/r3/pair_target_constraint_product_interacti_e462.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/pair_target_lof_intolerance_e253.py](norman_g_top/r3/pair_target_lof_intolerance_e253.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/ppi_distance_weighted_constraint_e118.py](norman_g_top/r3/ppi_distance_weighted_constraint_e118.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/promoter_cpg_overlap_with_target_e519.py](norman_g_top/r3/promoter_cpg_overlap_with_target_e519.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/promoter_motif_count_for_target_tf_e361.py](norman_g_top/r3/promoter_motif_count_for_target_tf_e361.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/promoter_motif_similarity_with_target_e660.py](norman_g_top/r3/promoter_motif_similarity_with_target_e660.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/protein_domain_random_projection_e613.py](norman_g_top/r3/protein_domain_random_projection_e613.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_chromatin_accessibility_e590.py](norman_g_top/r3/target_chromatin_accessibility_e590.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_constraint_interaction_e91.py](norman_g_top/r3/target_constraint_interaction_e91.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_cpg_island_overlap_e125_e139.py](norman_g_top/r3/target_cpg_island_overlap_e125_e139.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_essentiality_score_e380.py](norman_g_top/r3/target_essentiality_score_e380.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_gene_compartment_overlap_e411.py](norman_g_top/r3/target_gene_compartment_overlap_e411.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_gene_cpg_similarity_e304.py](norman_g_top/r3/target_gene_cpg_similarity_e304.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_gene_motif_similarity_e262.py](norman_g_top/r3/target_gene_motif_similarity_e262.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_localization_overlap_e92.py](norman_g_top/r3/target_localization_overlap_e92.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_localization_similarity_e520.py](norman_g_top/r3/target_localization_similarity_e520.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_promoter_accessibility_proxy_e379.py](norman_g_top/r3/target_promoter_accessibility_proxy_e379.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_promoter_cpg_density_e201.py](norman_g_top/r3/target_promoter_cpg_density_e201.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_promoter_cpg_island_e375.py](norman_g_top/r3/target_promoter_cpg_island_e375.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_property_modulated_response_e105.py](norman_g_top/r3/target_property_modulated_response_e105.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_protein_length_x_constraint_e477.py](norman_g_top/r3/target_protein_length_x_constraint_e477.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_tf_binding_site_count_e510.py](norman_g_top/r3/target_tf_binding_site_count_e510.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_tf_motif_enrichment_e331_e347.py](norman_g_top/r3/target_tf_motif_enrichment_e331_e347.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_tfbs_count_e204.py](norman_g_top/r3/target_tfbs_count_e204.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/target_transmembrane_count_interaction_e531.py](norman_g_top/r3/target_transmembrane_count_interaction_e531.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/r3/tf_motif_promoter_score_e119.py](norman_g_top/r3/tf_motif_promoter_score_e119.py) | Unchanged G stage2 candidate snapshot. |
| [norman_g_top/selection.json](norman_g_top/selection.json) | Complete fixed stage2 family-selection manifest. |

### Corrected F — exact new files

| File | Record |
|---|---|
| [norman_f_corrected_h8_launch_issue51.json](norman_f_corrected_h8_launch_issue51.json) | Issue51 publication body or exact publication receipt. |
| [norman_f_corrected_h8_launch_issue51.md](norman_f_corrected_h8_launch_issue51.md) | Issue51 publication body or exact publication receipt. |
| [norman_f_corrected_input_manifest.json](norman_f_corrected_input_manifest.json) | Frozen pre-score public/source input-hash receipt. |
| [norman_f_corrected_pool.command.txt](norman_f_corrected_pool.command.txt) | Exact command receipt. |
| [norman_f_corrected_pool.exit](norman_f_corrected_pool.exit) | Explicit terminal exit receipt. |
| [norman_f_corrected_pool.log](norman_f_corrected_pool.log) | Captured tool output. |
| [norman_f_corrected_pooled_holm/pooled_holm.json](norman_f_corrected_pooled_holm/pooled_holm.json) | Complete-family pooled step-down null result; legacy filename. |
| [norman_f_corrected_pooled_holm/pooled_holm.md](norman_f_corrected_pooled_holm/pooled_holm.md) | Complete-family pooled step-down null result; legacy filename. |
| [norman_f_corrected_primary_audit.json](norman_f_corrected_primary_audit.json) | Independent primary/family/gate audit evidence. |
| [norman_f_corrected_primary_audit.md](norman_f_corrected_primary_audit.md) | Independent primary/family/gate audit evidence. |
| [norman_f_corrected_select.command.txt](norman_f_corrected_select.command.txt) | Exact command receipt. |
| [norman_f_corrected_select.exit](norman_f_corrected_select.exit) | Explicit terminal exit receipt. |
| [norman_f_corrected_select.log](norman_f_corrected_select.log) | Captured tool output. |
| [norman_f_corrected_selection_audit.json](norman_f_corrected_selection_audit.json) | Independent primary/family/gate audit evidence. |
| [norman_f_corrected_selection_audit.md](norman_f_corrected_selection_audit.md) | Independent primary/family/gate audit evidence. |
| [norman_f_corrected_stage2.command.txt](norman_f_corrected_stage2.command.txt) | Exact command receipt. |
| [norman_f_corrected_stage2.exit](norman_f_corrected_stage2.exit) | Explicit terminal exit receipt. |
| [norman_f_corrected_stage2.log](norman_f_corrected_stage2.log) | Captured tool output. |
| [norman_f_corrected_stage2/feature_compare.json](norman_f_corrected_stage2/feature_compare.json) | Stage2 matched-null result. |
| [norman_f_corrected_stage2/feature_compare.md](norman_f_corrected_stage2/feature_compare.md) | Stage2 matched-null result. |
| [norman_f_corrected_top/r0/additive_times_bidirectional_count_e485.py](norman_f_corrected_top/r0/additive_times_bidirectional_count_e485.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_bidirectional_partner_e469.py](norman_f_corrected_top/r0/additive_times_bidirectional_partner_e469.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_bidirectional_proximity_e541.py](norman_f_corrected_top/r0/additive_times_bidirectional_proximity_e541.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_bidirectional_proximity_e542.py](norman_f_corrected_top/r0/additive_times_bidirectional_proximity_e542.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_cds_length_e445.py](norman_f_corrected_top/r0/additive_times_cds_length_e445.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_cds_length_e449.py](norman_f_corrected_top/r0/additive_times_cds_length_e449.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_cpg_oe_promoter_e455.py](norman_f_corrected_top/r0/additive_times_cpg_oe_promoter_e455.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_cpg_oe_promoter_squared_e473.py](norman_f_corrected_top/r0/additive_times_cpg_oe_promoter_squared_e473.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_cpg_promoter_e325.py](norman_f_corrected_top/r0/additive_times_cpg_promoter_e325.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_exon_count_e415.py](norman_f_corrected_top/r0/additive_times_exon_count_e415.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_gc_cds_e418.py](norman_f_corrected_top/r0/additive_times_gc_cds_e418.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_gene_span_e331.py](norman_f_corrected_top/r0/additive_times_gene_span_e331.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_gene_span_e347.py](norman_f_corrected_top/r0/additive_times_gene_span_e347.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_intron_length_e443.py](norman_f_corrected_top/r0/additive_times_intron_length_e443.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_n_transcripts_e453.py](norman_f_corrected_top/r0/additive_times_n_transcripts_e453.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_promoter_cpg_e420.py](norman_f_corrected_top/r0/additive_times_promoter_cpg_e420.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_cpg_promoter_e489.py](norman_f_corrected_top/r0/additive_times_target_cpg_promoter_e489.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_exon_count_e548.py](norman_f_corrected_top/r0/additive_times_target_exon_count_e548.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_gene_span_e401.py](norman_f_corrected_top/r0/additive_times_target_gene_span_e401.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_hydrophobic_fracti_e679.py](norman_f_corrected_top/r0/additive_times_target_hydrophobic_fracti_e679.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_promoter_cpg_e428.py](norman_f_corrected_top/r0/additive_times_target_promoter_cpg_e428.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_promoter_cpg_e666.py](norman_f_corrected_top/r0/additive_times_target_promoter_cpg_e666.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_span_product_e545.py](norman_f_corrected_top/r0/additive_times_target_span_product_e545.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_target_transcript_length_e407.py](norman_f_corrected_top/r0/additive_times_target_transcript_length_e407.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_transcript_length_e310.py](norman_f_corrected_top/r0/additive_times_transcript_length_e310.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_transcript_length_e316.py](norman_f_corrected_top/r0/additive_times_transcript_length_e316.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_utr3_length_e441.py](norman_f_corrected_top/r0/additive_times_utr3_length_e441.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/additive_times_utr3_length_e451.py](norman_f_corrected_top/r0/additive_times_utr3_length_e451.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/gene_annotation_ppi_random_projection_e721.py](norman_f_corrected_top/r0/gene_annotation_ppi_random_projection_e721.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/gene_annotation_random_projection_e697.py](norman_f_corrected_top/r0/gene_annotation_random_projection_e697.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/screen_delta_over_transcript_length_e416.py](norman_f_corrected_top/r0/screen_delta_over_transcript_length_e416.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/screen_delta_over_transcript_length_e546.py](norman_f_corrected_top/r0/screen_delta_over_transcript_length_e546.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/screen_delta_over_transcript_length_e547.py](norman_f_corrected_top/r0/screen_delta_over_transcript_length_e547.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/screen_delta_times_cds_length_e446.py](norman_f_corrected_top/r0/screen_delta_times_cds_length_e446.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/screen_delta_times_promoter_cpg_e377.py](norman_f_corrected_top/r0/screen_delta_times_promoter_cpg_e377.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/screen_delta_times_target_promoter_cpg_e694.py](norman_f_corrected_top/r0/screen_delta_times_target_promoter_cpg_e694.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/target_gene_span_times_screen_e717.py](norman_f_corrected_top/r0/target_gene_span_times_screen_e717.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/target_hydrophobic_fraction_e675.py](norman_f_corrected_top/r0/target_hydrophobic_fraction_e675.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/target_promoter_cpg_e406.py](norman_f_corrected_top/r0/target_promoter_cpg_e406.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r0/target_promoter_gc_e80_e81.py](norman_f_corrected_top/r0/target_promoter_gc_e80_e81.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r2/tf_binding_motif_score_e192.py](norman_f_corrected_top/r2/tf_binding_motif_score_e192.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/additive_response_x_gene_span_e128.py](norman_f_corrected_top/r3/additive_response_x_gene_span_e128.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/additive_response_x_mean_target_gene_spa_e303.py](norman_f_corrected_top/r3/additive_response_x_mean_target_gene_spa_e303.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/additive_response_x_mean_target_span_e296.py](norman_f_corrected_top/r3/additive_response_x_mean_target_span_e296.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/additive_response_x_target_promoter_cpg_e412.py](norman_f_corrected_top/r3/additive_response_x_target_promoter_cpg_e412.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/additive_response_x_target_promoter_cpg_e509.py](norman_f_corrected_top/r3/additive_response_x_target_promoter_cpg_e509.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/bidirectional_partner_coexpression_with__e531.py](norman_f_corrected_top/r3/bidirectional_partner_coexpression_with__e531.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/cpg_oe_promoter_x_additive_e129.py](norman_f_corrected_top/r3/cpg_oe_promoter_x_additive_e129.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/cpg_promoter_x_additive_response_e142.py](norman_f_corrected_top/r3/cpg_promoter_x_additive_response_e142.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/gene_annotation_random_projection_e567.py](norman_f_corrected_top/r3/gene_annotation_random_projection_e567.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/gene_span_x_additive_response_e143.py](norman_f_corrected_top/r3/gene_span_x_additive_response_e143.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/mean_target_promoter_gc_e295.py](norman_f_corrected_top/r3/mean_target_promoter_gc_e295.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/promoter_similarity_target_g_e564.py](norman_f_corrected_top/r3/promoter_similarity_target_g_e564.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_mean_target_span_e31_e310.py](norman_f_corrected_top/r3/replogle_additive_x_mean_target_span_e31_e310.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_promoter_cpg_island_e507.py](norman_f_corrected_top/r3/replogle_additive_x_promoter_cpg_island_e507.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_promoter_cpg_oe_e391.py](norman_f_corrected_top/r3/replogle_additive_x_promoter_cpg_oe_e391.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_promoter_cpg_oe_e441.py](norman_f_corrected_top/r3/replogle_additive_x_promoter_cpg_oe_e441.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_target_promoter_cpg__e558.py](norman_f_corrected_top/r3/replogle_additive_x_target_promoter_cpg__e558.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_target_promoter_cpg__e590.py](norman_f_corrected_top/r3/replogle_additive_x_target_promoter_cpg__e590.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_target_promoter_cpg_e460.py](norman_f_corrected_top/r3/replogle_additive_x_target_promoter_cpg_e460.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/replogle_additive_x_target_promoter_gc_e328.py](norman_f_corrected_top/r3/replogle_additive_x_target_promoter_gc_e328.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/target_annotation_random_projection_e575.py](norman_f_corrected_top/r3/target_annotation_random_projection_e575.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/target_chromatin_accessibility_e242.py](norman_f_corrected_top/r3/target_chromatin_accessibility_e242.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/target_mean_cpg_oe_promoter_e402_e350.py](norman_f_corrected_top/r3/target_mean_cpg_oe_promoter_e402_e350.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/target_promoter_cpg_mean_e521.py](norman_f_corrected_top/r3/target_promoter_cpg_mean_e521.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/r3/target_promoter_cpg_x_gene_control_varia_e594.py](norman_f_corrected_top/r3/target_promoter_cpg_x_gene_control_varia_e594.py) | Unchanged corrected F stage2 candidate snapshot. |
| [norman_f_corrected_top/selection.json](norman_f_corrected_top/selection.json) | Complete fixed stage2 family-selection manifest. |

### Lead H8 — exact new files

| File | Record |
|---|---|
| [adamson_cf_lead_h8.command.txt](adamson_cf_lead_h8.command.txt) | Exact command receipt. |
| [adamson_cf_lead_h8.exit](adamson_cf_lead_h8.exit) | Explicit terminal exit receipt. |
| [adamson_cf_lead_h8.log](adamson_cf_lead_h8.log) | Captured tool output. |
| [adamson_cf_lead_h8/feature_compare.json](adamson_cf_lead_h8/feature_compare.json) | Lead's unchanged H8 OOF/null result. |
| [adamson_cf_lead_h8/feature_compare.md](adamson_cf_lead_h8/feature_compare.md) | Lead's unchanged H8 OOF/null result. |
| [adamson_cf_lead_h8_audit.json](adamson_cf_lead_h8_audit.json) | Independent fixed H8 criterion/null audit. |
| [adamson_cf_lead_h8_audit.md](adamson_cf_lead_h8_audit.md) | Independent fixed H8 criterion/null audit. |
| [adamson_cf_lead_h8_prerun.command.txt](adamson_cf_lead_h8_prerun.command.txt) | Exact command receipt. |
| [adamson_cf_lead_h8_prerun.exit](adamson_cf_lead_h8_prerun.exit) | Explicit terminal exit receipt. |
| [adamson_cf_lead_h8_prerun.json](adamson_cf_lead_h8_prerun.json) | Fixed public-knowledge pre-run lists/counts. |
| [adamson_cf_lead_h8_prerun.log](adamson_cf_lead_h8_prerun.log) | Captured tool output. |
| [adamson_cf_lead_h8_prerun.md](adamson_cf_lead_h8_prerun.md) | Fixed public-knowledge pre-run lists/counts. |
| [adamson_cf_lead_h8_summary.json](adamson_cf_lead_h8_summary.json) | Fixed H8 result and all emitted metrics. |
| [adamson_cf_lead_h8_summary.md](adamson_cf_lead_h8_summary.md) | Fixed H8 result and all emitted metrics. |
| [adamson_h8_norman_launch_issue51.json](adamson_h8_norman_launch_issue51.json) | Issue51 publication body or exact publication receipt. |
| [adamson_h8_norman_launch_issue51.md](adamson_h8_norman_launch_issue51.md) | Issue51 publication body or exact publication receipt. |
| [lead_h8_prescore_protocol.json](lead_h8_prescore_protocol.json) | H8 protocol, clarification and hashes fixed before scoring. |
| [lead_h8_prescore_protocol.md](lead_h8_prescore_protocol.md) | H8 protocol, clarification and hashes fixed before scoring. |
| [norman_h8_complete_pytest_launch_issue51.json](norman_h8_complete_pytest_launch_issue51.json) | Issue51 publication body or exact publication receipt. |
| [norman_h8_complete_pytest_launch_issue51.md](norman_h8_complete_pytest_launch_issue51.md) | Issue51 publication body or exact publication receipt. |
| [norman_lead_h8.command.txt](norman_lead_h8.command.txt) | Exact command receipt. |
| [norman_lead_h8.exit](norman_lead_h8.exit) | Explicit terminal exit receipt. |
| [norman_lead_h8.log](norman_lead_h8.log) | Captured tool output. |
| [norman_lead_h8/feature_compare.json](norman_lead_h8/feature_compare.json) | Lead's unchanged H8 OOF/null result. |
| [norman_lead_h8/feature_compare.md](norman_lead_h8/feature_compare.md) | Lead's unchanged H8 OOF/null result. |
| [norman_lead_h8_audit.json](norman_lead_h8_audit.json) | Independent fixed H8 criterion/null audit. |
| [norman_lead_h8_audit.md](norman_lead_h8_audit.md) | Independent fixed H8 criterion/null audit. |
| [norman_lead_h8_prerun.command.txt](norman_lead_h8_prerun.command.txt) | Exact command receipt. |
| [norman_lead_h8_prerun.exit](norman_lead_h8_prerun.exit) | Explicit terminal exit receipt. |
| [norman_lead_h8_prerun.json](norman_lead_h8_prerun.json) | Fixed public-knowledge pre-run lists/counts. |
| [norman_lead_h8_prerun.log](norman_lead_h8_prerun.log) | Captured tool output. |
| [norman_lead_h8_prerun.md](norman_lead_h8_prerun.md) | Fixed public-knowledge pre-run lists/counts. |
| [norman_lead_h8_summary.json](norman_lead_h8_summary.json) | Fixed H8 result and all emitted metrics. |
| [norman_lead_h8_summary.md](norman_lead_h8_summary.md) | Fixed H8 result and all emitted metrics. |

### Consolidated publication receipts — exact new files

| File | Record |
|---|---|
| [g_f_h8_preservation_audit.json](g_f_h8_preservation_audit.json) | Preserved reading, provenance or audit receipt. |
| [g_f_h8_preservation_audit.md](g_f_h8_preservation_audit.md) | Preserved reading, provenance or audit receipt. |
| [g_f_h8_publication_manifest.json](g_f_h8_publication_manifest.json) | Preservation and provenance hash manifest. |
| [g_f_h8_publication_manifest.md](g_f_h8_publication_manifest.md) | Preservation and provenance hash manifest. |
| [g_f_h8_publication_pytest.command.txt](g_f_h8_publication_pytest.command.txt) | Exact command receipt. |
| [g_f_h8_publication_pytest.exit](g_f_h8_publication_pytest.exit) | Explicit terminal exit receipt. |
| [g_f_h8_publication_pytest.log](g_f_h8_publication_pytest.log) | Captured tool output. |
| [g_f_h8_publication_verification.json](g_f_h8_publication_verification.json) | Preserved reading, provenance or audit receipt. |
| [g_f_h8_publication_verification.md](g_f_h8_publication_verification.md) | Preserved reading, provenance or audit receipt. |
| [g_f_h8_readings.json](g_f_h8_readings.json) | Consolidated scientific reading and source references. |
| [g_f_h8_readings.md](g_f_h8_readings.md) | Consolidated scientific reading and source references. |
| [g_f_h8_report_audit.json](g_f_h8_report_audit.json) | Preserved reading, provenance or audit receipt. |
| [g_f_h8_report_audit.md](g_f_h8_report_audit.md) | Preserved reading, provenance or audit receipt. |

## Archived from here

`feature_audit.{md,json}`, `feature_audit_feature_box.json`, `feature_audit_v2.{md,json}`, `feature_audit_v2_feature_box.json`
(audit versions 1 and 2, superseded by v3): [`docs/archive/results/`](../archive/README.md).
