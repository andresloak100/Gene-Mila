Astra — GEARS complete: all three training runs, validations and prescribed score invocations exit 0. Full seed reports: [0](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6486841104), [2](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6486841324), [3](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6486841557). Shared DeepSeek ledger remains 61.401668232; no paid call. One draft results PR is being prepared; C2 and H have not started.

# GEARS on matched Adamson targets: three fixed CPU seeds

All three training runs and exactly one prescribed bridge invocation per seed completed with exit 0. GEARS sealed pearson_delta is **0.407282874 ± 0.011648347** (mean ± sample SD, seeds 0/2/3). The selected four-worker Opus-planned comparator, `newcode_opus_w4_r0:EXP_0441`, scores **0.598665038** in these same paired queries and meets the predeclared paired reading rule against every GEARS seed. This is a descriptive comparison on the worn sealed cohort, not a fresh-test result or a basis for model selection.

Predictions cover all 38 held-out identities × 2,055 genes; the bridge scores the 21 sealed perturbations. Its other held-out identities belong to the visible validation tier. No held-out cells were supplied to GEARS. The operator did not inspect sealed labels or their membership.

## Metrics

The table uses unrounded JSON values for arithmetic, with sample SD (ddof=1) across the three seeds. Counts and the duplicated primary/CellForge metrics are retained for completeness. No internal repeated oracle query is counted as a replicate.

| Metric | Seed 0 | Seed 2 | Seed 3 | Mean | Sample SD |
|---|---:|---:|---:|---:|---:|
| rmse | 0.0926694591559 | 0.0967147418989 | 0.0908198479766 | 0.0934013496772 | 0.00301482858386 |
| mae | 0.0650769980478 | 0.0701163071361 | 0.0645995436352 | 0.066597616273 | 0.00305661245847 |
| mse | 0.00858762866025 | 0.00935374130058 | 0.0082482447865 | 0.00872987158244 | 0.000566308592857 |
| pearson_delta | 0.397645128805 | 0.403976513843 | 0.420226978031 | 0.40728287356 | 0.0116483470737 |
| pearson_delta_top | 0.510265338112 | 0.506803796512 | 0.52295847878 | 0.513342537801 | 0.00850560451964 |
| direction_acc_top | 0.838095238095 | 0.828571428571 | 0.87380952381 | 0.846825396825 | 0.0238491733354 |
| mse_top | 0.146822827422 | 0.136513718193 | 0.140270708822 | 0.141202418145 | 0.0052173264196 |
| r2_top | 0.774724825013 | 0.78598115314 | 0.785962206705 | 0.782222728286 | 0.00649338162004 |
| pearson_expr | 0.981168255882 | 0.979348079184 | 0.981706415408 | 0.980740916824 | 0.00123588083536 |
| primary | 0.397645128805 | 0.403976513843 | 0.420226978031 | 0.40728287356 | 0.0116483470737 |
| cellforge_mse | 0.00858762866025 | 0.00935374130058 | 0.0082482447865 | 0.00872987158244 | 0.000566308592857 |
| cellforge_pcc | 0.981168255882 | 0.979348079184 | 0.981706415408 | 0.980740916824 | 0.00123588083536 |
| cellforge_r2 | 0.959062327475 | 0.955353095345 | 0.960661658763 | 0.958359027194 | 0.00272326731268 |
| cellforge_mse_de | 0.13723175862 | 0.130127993702 | 0.131636066518 | 0.13299860628 | 0.00374276033889 |
| cellforge_pcc_de | 0.92689962078 | 0.927215446796 | 0.928947720946 | 0.927687596174 | 0.00110266601833 |
| cellforge_r2_de | 0.744216814529 | 0.752351647507 | 0.75793123034 | 0.751499897458 | 0.00689676800189 |
| cellforge_mse_deset | 0.131057513958 | 0.129307295308 | 0.130567813749 | 0.130310874338 | 0.000902956104702 |
| cellforge_pcc_deset | 0.876697639964 | 0.885335693779 | 0.881262267874 | 0.881098533872 | 0.00432135395966 |
| cellforge_r2_deset | 0.632642820977 | 0.632398530183 | 0.636053476044 | 0.633698275734 | 0.00204331736897 |
| cellforge_n_perts_deset | 19 | 19 | 19 | 19 | 0 |
| vcworld_de_accuracy | 0.746796431468 | 0.697161394972 | 0.723021666087 | 0.722326497509 | 0.0248248193652 |
| vcworld_de_precision | 0.320691254929 | 0.289291465378 | 0.309104394586 | 0.306362371631 | 0.0158784669717 |
| vcworld_de_recall | 0.352903637524 | 0.458583280153 | 0.425526483727 | 0.412337800468 | 0.0540601770358 |
| vcworld_de_f1 | 0.336027222459 | 0.354776598371 | 0.358090328124 | 0.349631382984 | 0.0118974824619 |
| vcworld_de_auroc | 0.632474366915 | 0.639107798081 | 0.648392391633 | 0.639991518876 | 0.00799572383016 |
| vcworld_de_auprc | 0.304692644644 | 0.314320871705 | 0.310927648166 | 0.309980388172 | 0.0048835095175 |
| vcworld_dir_accuracy | 0.848117421825 | 0.8486279515 | 0.878111040204 | 0.858285471176 | 0.0171713438786 |
| vcworld_dir_precision | 0.620778110304 | 0.61878914405 | 0.687265917603 | 0.642277723986 | 0.0389736086398 |
| vcworld_dir_recall | 0.82735042735 | 0.844444444444 | 0.836467236467 | 0.836087369421 | 0.00855333732133 |
| vcworld_dir_f1 | 0.709330727894 | 0.71421686747 | 0.754561809304 | 0.726036468223 | 0.0248241798016 |
| vcworld_dir_auroc | 0.908180480582 | 0.91822537112 | 0.928755716749 | 0.918387189484 | 0.0102885725308 |
| vcworld_dir_auprc | 0.794547504452 | 0.822924748181 | 0.841841050933 | 0.819771101189 | 0.0238039702925 |
| vcworld_n_de_pairs | 7835 | 7835 | 7835 | 7835 | 0 |

## Paired reading against the prescribed lab run

Differences below are GEARS minus lab pearson_delta, paired over n=21 sealed perturbations. The rule requires gain above twice its paired SE and wins on more than half the perturbations (at least 11 of 21). The lab satisfies both conditions for each seed. No cross-seed pooled p-value or additional query was computed.

| GEARS seed | GEARS − lab | Paired SE | GEARS wins | Lab wins | Ties | Rule verdict |
|---|---:|---:|---:|---:|---:|---|
| 0 | -0.201019909606 | 0.0406614016483 | 1/21 | 20/21 | 0 | Lab |
| 2 | -0.194688524567 | 0.0414405291013 | 2/21 | 19/21 | 0 | Lab |
| 3 | -0.178438060379 | 0.0414186180553 | 1/21 | 20/21 | 0 | Lab |

The plan’s contextual historical rows are start≈0.520, no-LLM control≈0.554 and four-worker agents≈0.602±0.002 (as quoted in [PLAN_DL_BASELINES](../../PLAN_DL_BASELINES.md)); those arms were not rescored here. The exact prescribed single-run comparator in this result is 0.598665038, not that historical three-run mean.

## Input, fixed settings and limitations

Andres approved reuse of the corrected export `~/cellforge_adamson_export_corrected_20261028`: 40,890 cells, 9,065 controls, 31,825 training cells, all 50 training perturbations, 2,055 genes. It contains control/training cells only, already counts per 10,000 and log1p. Input SHA-256 `ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a`; export receipt SHA-256 `c85d04d964f75b426927855361f7cc7f0fa23532a946b34ecab5fd46688b795c`. The preserved original empty export was not used or rebuilt.

The requested three-source export adds 1,770 controls and 10 training cells relative to the bundle’s original single-source ingest. The evaluation targets, genes and evaluator match; the training cell cohort is not identical to the lab bundle. This caveat prevents interpreting the comparison as a strictly identical-input training experiment.

All seeds use 20 CPU epochs, hidden size 64, batch size 32 and validation fraction 0.1, with fresh work/output folders and no parameter/device/source changes. GEARS uses 41 training conditions and 5 validation conditions; 4 exported conditions are excluded because they lie outside its graph: AMIGO3, KCTD16, SLMO2, SRPR. The runner’s mean-training-response fallback is used for TIMM23 (1/38 prediction identities). It remains in the unchanged prediction artifact; we do not assert its sealed membership. The runner selects its epoch using GEARS validation conditions drawn from training perturbations, not held-out labels.

Training used source `d5e842fed53d883ed615ec766ccd07b35bfa397c`. After training finished, the own clone fast-forwarded to integration `37d991d94b414ca8f8475b066bad5ec4451acc9f` for scoring/publication. Exact diff and hashes confirm GEARS runner/requirements, bridge and genemila/ unchanged. Main checkout, evaluator, split, guard and input files were not modified.

## Runtime and reproducibility

| Seed | Runner wall seconds | Prediction SHA-256 |
|---|---:|---|
| 0 | 5021.1 | `780b0239464f7ea84e2a43d97f774eaad58e99ef49cfec3e0f4cd956ca62f3ee` |
| 2 | 18158.9 | `e0bae73fbfff0cfb6420879d7b65bdfe298c130d0635312540976c16db884632` |
| 3 | 4983.2 | `aea8a91e73cef518abaa61f493c3b6361971c5599f23dde8ab4ca48d663a648f` |

Runner times are wall time, not aggregate CPU-hours. Seed 2 includes the previously disclosed slow-progress interval; its cause is not established. The chain started 2026-10-28T19:13:05.900862 UTC and ended 2026-10-29T03:02:56.758416 UTC, with no retry, restart or timeout. Scoring ran sequentially 03:09:04–03:09:09 UTC, keys unset, nice 19, after all training.

Environment installation/pip-check/imports passed; 7 focused tests passed before training. Actual versions include cell-gears 0.1.2, torch 2.15.0, torch-geometric 2.8.1, pandas 2.3.3, anndata 0.13.4, scanpy 1.12.4, numpy 2.5.4, scipy 1.18.1 and scikit-learn 1.9.1. Exact requirements, pip report/freeze, wheel provenance and commands are retained. All 17 prediction checks pass for each seed. All four downloaded graph artifacts have identical hashes in all three work folders:

| Graph artifact | Bytes | SHA-256 |
|---|---:|---|
| `gears_data/essential_all_data_pert_genes.pkl` | 558811 | `46c3dfe354d8ad5c0da22c69f3d0ca451987b1a61ed9d984279b22b9565ff8d7` |
| `gears_data/gene2go_all.pkl` | 9462558 | `f145c5e84a53048d87942a417d870a4f2d8db50200b96e492b358c13aba8c771` |
| `gears_data/go_essential_all/go_essential_all.csv` | 354733543 | `99622d9215462e7bbea99a5f6c0b1e86febfef9f57226269418053484fcb3f9f` |
| `gears_data/go_essential_all.tar.gz` | 60654049 | `98a14a60e8b76f76fd172570d023a6036775f151604ec01340b3fec7d36693da` |

These are the actual downloaded sizes (including a 354,733,543-byte unpacked CSV), rather than the plan’s approximate 10 MB. No screen dataset downloader was invoked.

Full precision is preserved in [aggregate.json](aggregate.json) and the untouched tool outputs [seed 0](../gears_adamson_s0.json), [seed 2](../gears_adamson_s2.json), [seed 3](../gears_adamson_s3.json). Every command, log, explicit exit, runtime, validation and hash receipt is individually indexed below in this directory’s [README](README.md). Raw predictions, work folders, packages and input remain outside Git. No paid call.
