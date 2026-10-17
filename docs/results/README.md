# Results index

Every file here is a record produced by a run or a tool on Andres's Mac and committed as it was on disk: never edited,
never deleted; a new check gets a new file. Every number in the README traces to one of these files
(`tools/readme_check.py`). A `.md` and `.json` pair is one result (the `.md` is the reading, the `.json` the numbers).

Convention from block G on: each block's readings go in their own directory, `docs/results/block_<x>/`. The files
below predate it and stay where the manifests and records that cite them say they are.

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
| B1 and B2 run records (PLAN_AFTER_N4) | in draft PRs [#6](https://github.com/andresloak100/Gene-Mila/pull/6) and [#7](https://github.com/andresloak100/Gene-Mila/pull/7); the B2 verification in [#10](https://github.com/andresloak100/Gene-Mila/pull/10); listed here once merged | `tools/arm_reading.py`, `tools/sealed_reading.py` |
| `norman_b1_frozen_test_review_20261013.{md,json}` | frozen B1: the saved held-out evaluation, model and source hashes (PR #13) | saved evaluation, 13 October |
| `norman_frozen_export_20261013/` | the frozen B1 export and its independent verification (PR #19); read `report.md` first | `tools/frozen_model.py`, `verification_driver.py` |
| `b1_development_diagnostic_20261013/` | the fixed B1 recipe diagnosis on training gene folds; reading [`docs/B1_DIAGNOSTIC_RESULTS.md`](../B1_DIAGNOSTIC_RESULTS.md) | `tools/b1_development_diagnostic.py` |
| `b1_two_member_test_20261013/` | the fixed two-member screen; reading [`docs/B1_TWO_MEMBER_RESULTS.md`](../B1_TWO_MEMBER_RESULTS.md); `run_with_deadline.py` is executed by `tests/test_b1_two_member_test.py` | `tools/b1_two_member_test.py` |
| `external_cohort_metadata_20261013.json` | the data behind [`docs/EXTERNAL_COHORT_METADATA.md`](../EXTERNAL_COHORT_METADATA.md) | metadata audit |
| `b4_existing_readings_20261017.{md,json}` | B4, the existing one-worker readings (PLAN_B4), 17 October | the lead, from the stored run summaries |

## Block F (16 October 2026; [`docs/PLAN_F_GENOME_ANNOTATION.md`](../PLAN_F_GENOME_ANNOTATION.md))

Read first: [norman_f_readings.md](norman_f_readings.md).

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
| readings | not yet written; they go in `docs/results/block_g/` when the chain ends |

## Archived from here

`feature_audit.{md,json}`, `feature_audit_feature_box.json`, `feature_audit_v2.{md,json}`, `feature_audit_v2_feature_box.json`
(audit versions 1 and 2, superseded by v3): [`docs/archive/results/`](../archive/README.md).
