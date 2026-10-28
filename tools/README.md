# tools/

One line per file. Everything here runs offline on visible data unless the line says otherwise; nothing reads
`data/*/private/` or `splits.json` (the guard and the tests check it). Run from the repository root.
CI checks only the README (`readme_check.py`); run `python -m pytest -q` (about 13 minutes) before pushing code.

## Current instruments

| File | What it does |
|---|---|
| `feature_compare.py` | the comparison's instrument: what each system's feature set, and each single feature, adds to one fixed linear model, against a matched null (`docs/FEATURE_COMPARISON_PROTOCOL.md`) |
| `feature_audit.py` | audit of finished runs: redundancy, which features earn their place, compact models, the failed-feature box (imported by `feature_compare.py` and `docs/results/norman_f_collect_metadata.py`) |
| `block_f_readings.py` | the two-stage feature-level reading of block F (`docs/PLAN_F_GENOME_ANNOTATION.md`, ROADMAP D2) |
| `arm_reading.py` | the arm reading and the combined model of `docs/PLAN_AFTER_N4.md` |
| `sealed_reading.py` | the pre-specified sealed readings of `docs/NORMAN_PLAN.md` section 5 |
| `build_clean_bundle.py` | a tier-1-only copy of a bundle with its knowledge rebuilt from clean sources (block G) |
| `build_gene_annotation.py`, `build_gene_constraint.py`, `build_protein_annotation.py` | knowledge files from the genome sequence and GENCODE, gnomAD constraint, UniProt protein features |
| `build_paralogs.py`, `build_protein_similarity.py` | the two tier-1 similarity sources: Ensembl Compara paralog pairs and counts, and nearest sequence neighbours from UniProt's per-protein embeddings (`docs/SIMILARITY_SOURCES.md`; inputs fetched on the Mac) |
| `build_external_screen.py` | a knowledge file from an external Perturb-seq screen (the audited exception) |
| `knowledge_coverage.py` | how much prior knowledge each target has in a bundle, and what a symbol loses |
| `residual_mining.py` | training-only residual mining: hypothesis generation, never evidence (ROADMAP M1) |
| `export_task_package.py`, `task_package/` (`evaluate.py`, `literal.py`, `program.md`) | the lab's problem as a self-contained task for other systems (autoresearch-style agents, Biomni) |
| `baselines/` (`run_codex.sh`, `run_autoresearch.sh`, `run_biomni.py`, `collect_handback.py`, `ledger_proxy.py`) | the comparison's other systems and the hand-back collector (block H) |
| `frozen_model.py` | export a pinned frozen ensemble, or predict target-only queries without fitting (`docs/FROZEN_EXPORT.md`) |
| `replogle_slice_manifest.py` | eligibility manifest of a candidate fresh-test cohort from its obs and var tables (ROADMAP D7) |
| `wetlab_candidates.py` | the wet-lab prediction package for pre-registration: where the model with a feature and its parent disagree on perturbations in no dataset, matched negatives, power (`docs/WETLAB_CANDIDATES.md`, ROADMAP D13) |
| `noise_ceiling.py`, `count_target_cells.py` | the noise ceiling of pearson_delta from cell-sampling noise, and the cell counts it needs |
| `external_loo.py` | does an external screen carry information the transfer features lack (leave-one-out on visible data) |
| `readme_check.py` | deterministic checks on the public face (README links, numbers, commands, figures, About box) |

## Dated one-off readings (each produced one record; kept so the record can be reproduced)

| File | Record |
|---|---|
| `refit_visible.py` | `docs/results/refit_visible.md` (11 October) |
| `ceiling_analysis.py` | `docs/results/ceiling_analysis.md` (as-run original: `docs/archive/mac/as_run/`) |
| `learned_kernel_experiment.py` | `docs/results/learned_kernel_experiment.json` (as-run original: `docs/archive/mac/as_run/`) |
| `compact_model_curve.py` | `docs/results/compact_model_curve.md` (as-run original: `docs/archive/mac/as_run/`) |
| `nondeterminism_scan.py` | `docs/results/nondeterminism_scan.md` (11 October; as-run original: `docs/archive/mac/as_run/`) |
| `time_to_best.py` | `docs/results/time_to_best.md` (5 October) |
| `replay_selection.py` | `docs/results/selection_replay.md` (4 October) |
| `b1_development_diagnostic.py` | `docs/B1_DIAGNOSTIC_RESULTS.md` (hashes `docs/B1_DIAGNOSTIC_PLAN.md` by path) |
| `b1_two_member_test.py` | `docs/B1_TWO_MEMBER_RESULTS.md` (hashes `docs/B1_TWO_MEMBER_PLAN.md` by path) |
| `shrinkage_diagnostic.py` | `docs/results/norman_development_shrinkage_20261013/report.md` (13 October; hashes `docs/NORMAN_SHRINKAGE_PLAN.md` by path) |
| `b1_nested_blend.py` | `docs/B1_NESTED_BLEND_RESULTS.md` (13 to 14 October; hashes `docs/B1_NESTED_BLEND_PLAN.md` by path; imports `b1_development_diagnostic.py`) |
| `b1_r2_regularization.py` | `docs/B1_R2_REGULARIZATION_RESULTS.md` (13 to 14 October; hashes `docs/B1_R2_REGULARIZATION_PLAN.md` by path; imports `b1_development_diagnostic.py`) |
| `b1_pair_batch_correction.py`, `feature_variants/pair_target_prior_edge_e34.py` | `docs/B1_PAIR_BATCH_RESULTS.md` (13 to 14 October; hashes `docs/B1_PAIR_BATCH_PLAN.md` and the variant by path; imports `b1_development_diagnostic.py`). The variant is the copied e34 plugin, version 3, with a per-pair fallback; it is installed in no bundle |

## Drivers and checks

| File | What it does |
|---|---|
| `scale_seq.sh` | the finished worker-scaling comparison's driver (HANDOFF section 9 names it; the Mac guards `pgrep` for it) |
| `deepseek_check.py` | one minimal paid DeepSeek call to verify connectivity and pricing; needs spend authorization (AGENTS.md) |
| `reprice_ledger.py` | preview the ledger against the current price table; `--apply` rewrites it and needs Andres (used once, 4 October) |

The comparison arms' feature plugins are not here: they live beside their protocol in `docs/comparison/` because they
are pre-registered records (`tests/test_cellforge_c2.py`, `tests/test_lead_h8_constraint.py`).
