# Norman public-training shrinkage diagnostic: fixed comparison completed

The lower-penalty recipe produced exactly the same predictions and metrics as ordinary ridge,
and training-only scalar calibration provided no average improvement over ridge. All 15 outer
fold fits selected alpha 0.01 from both grids. This closes the fixed small comparison for the
four built-in additive-ridge features. It provides no new evidence about the delivered B1
ensemble, external generalization, an untouched test, or superiority over CellForge.

Run directory: `/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-shrinkage/runs/norman_development_shrinkage_20261013`. Completed 2026-10-13 in 4.344 s; API spend $0.
The run scored 112 original public-training perturbations and 2,083 genes. Existing visible
validation and sealed labels, references, splits and oracle were never loaded. The original
main checkout and all historical run artifacts remain unchanged.

The prospective protocol was first published at `fe98ed7eda702bf3d9dd02806f3b387e460b6593`.
Execution used `0fbb8ce392744dcb04cb06674fb5f62cfd7a65b9`; its only protocol clarification says
positive uniform scaling preserves Pearson correlation. The fixed feature/grids/folds/recipes
did not change. Code review, ten synthetic methodology checks and the full **447-test passing**
suite (646.95 s) preceded execution. See [the prospective plan](../../NORMAN_SHRINKAGE_PLAN.md).

## Method and uncertainty

Each of seeds 0, 1 and 2 uses five outer gene-grouped folds; each outer training view uses
three inner gene-grouped folds with seed `1000 + 100 * outer_seed + outer_fold_index`. Each fold
hides its complete gene-overlap set. Label-dependent features and standardization are
recomputed using that fitting view only. Outer responses are used to score completed predictions.
The fixed features are `control_mean`, `mean_response`, `is_target`, `additive_response`.

Broad ridge selects alpha by inner mean Pearson delta from `[0.01, 1, 100, 10000, 1000000]`;
low-penalty ridge selects from `[0.01, 1, 100]`. Calibrated ridge multiplies the broad recipe
by a through-origin least-squares scalar fitted to selected-alpha inner out-of-fold predictions
and training truth, bounded to `[0, 4]`. Analytic additive uses the unchanged additive rule.
No calibration or recipe choice uses scored outer responses.

**Every ± below is sample SD over the three fold seeds.** These evaluations reuse the same
cohort and are not independent biological replicates, paired standard errors or test uncertainty.
Paired differences are computed within seed before averaging. No statistical significance
verdict or winning-recipe promotion is inferred. All raw seed outcomes are retained.

Top-20 genes are ranked by absolute true development change. Expression PCC/R² concern
mean expression, while Pearson delta concerns change from the original public control mean.
These top-20 fields have no private cell-derived DE reference and imply no matched CellForge
comparison. Delta magnitude ratio is mean absolute predicted change divided by mean absolute
measured development change; approaching one alone does not establish improved predictions.

## All four recipes, mean ± sample SD

| Metric | Additive | Ridge | Low-penalty ridge | Calibrated ridge |
|---|---:|---:|---:|---:|
| Pearson delta ↑ | 0.561398 ± 0.016064 | 0.569691 ± 0.016473 | 0.569691 ± 0.016473 | 0.569691 ± 0.016473 |
| MSE ↓ | 0.00823607 ± 0.00034975 | 0.00804452 ± 0.00038737 | 0.00804452 ± 0.00038737 | 0.00806231 ± 0.00039050 |
| Expression PCC ↑ | 0.982595 ± 0.000898 | 0.982999 ± 0.000943 | 0.982999 ± 0.000943 | 0.982951 ± 0.000932 |
| Expression R² ↑ | 0.961145 ± 0.001859 | 0.962002 ± 0.001986 | 0.962002 ± 0.001986 | 0.961898 ± 0.001959 |
| Top-20 MSE ↓ | 0.19371121 ± 0.01330837 | 0.19122482 ± 0.01394271 | 0.19122482 ± 0.01394271 | 0.19243290 ± 0.01285071 |
| Top-20 expression PCC ↑ | 0.894678 ± 0.002818 | 0.896510 ± 0.003997 | 0.896510 ± 0.003997 | 0.896016 ± 0.003978 |
| Top-20 expression R² ↑ | 0.687217 ± 0.013899 | 0.698918 ± 0.015984 | 0.698918 ± 0.015984 | 0.697732 ± 0.015563 |
| Top-20 Pearson delta ↑ | 0.552880 ± 0.025774 | 0.621149 ± 0.026771 | 0.621149 ± 0.026771 | 0.621149 ± 0.026771 |
| Top-20 direction accuracy ↑ | 0.794494 ± 0.018042 | 0.812202 ± 0.018995 | 0.812202 ± 0.018995 | 0.812202 ± 0.018995 |
| Delta magnitude ratio (diagnostic) | 0.787251 ± 0.014466 | 0.707249 ± 0.011074 | 0.707249 ± 0.011074 | 0.698987 ± 0.016130 |

## All raw seed evaluations

All-gene metrics and magnitude ratio:

| Seed | Recipe | Pearson delta | MSE | Expression PCC | Expression R² | Delta magnitude ratio |
|---:|---|---:|---:|---:|---:|---:|
| 0 | `additive` | 0.546074 | 0.00862948 | 0.981647 | 0.959112 | 0.776537 |
| 0 | `ridge` | 0.553107 | 0.00847648 | 0.981990 | 0.959826 | 0.699629 |
| 0 | `ridge_low_penalty` | 0.553107 | 0.00847648 | 0.981990 | 0.959826 | 0.699629 |
| 0 | `ridge_calibrated` | 0.553107 | 0.00850348 | 0.981935 | 0.959708 | 0.701452 |
| 1 | `additive` | 0.560010 | 0.00796031 | 0.983433 | 0.962758 | 0.803707 |
| 1 | `ridge` | 0.569915 | 0.00772796 | 0.983856 | 0.963717 | 0.719951 |
| 1 | `ridge_low_penalty` | 0.569915 | 0.00772796 | 0.983856 | 0.963717 | 0.719951 |
| 1 | `ridge_calibrated` | 0.569915 | 0.00776098 | 0.983766 | 0.963483 | 0.681767 |
| 2 | `additive` | 0.578111 | 0.00811842 | 0.982705 | 0.961565 | 0.781509 |
| 2 | `ridge` | 0.586051 | 0.00792911 | 0.983150 | 0.962462 | 0.702166 |
| 2 | `ridge_low_penalty` | 0.586051 | 0.00792911 | 0.983150 | 0.962462 | 0.702166 |
| 2 | `ridge_calibrated` | 0.586051 | 0.00792248 | 0.983152 | 0.962503 | 0.713743 |

Top-20 metrics:

| Seed | Recipe | MSE | Expression PCC | Expression R² | Pearson delta | Direction accuracy |
|---:|---|---:|---:|---:|---:|---:|
| 0 | `additive` | 0.20779618 | 0.891444 | 0.671238 | 0.526873 | 0.778125 |
| 0 | `ridge` | 0.20640484 | 0.891897 | 0.680549 | 0.592515 | 0.793750 |
| 0 | `ridge_low_penalty` | 0.20640484 | 0.891897 | 0.680549 | 0.592515 | 0.793750 |
| 0 | `ridge_calibrated` | 0.20703659 | 0.891479 | 0.679776 | 0.592515 | 0.793750 |
| 1 | `additive` | 0.18134681 | 0.896602 | 0.696513 | 0.553353 | 0.791518 |
| 1 | `ridge` | 0.17898998 | 0.898948 | 0.709662 | 0.625377 | 0.811161 |
| 1 | `ridge_low_penalty` | 0.17898998 | 0.898948 | 0.709662 | 0.625377 | 0.811161 |
| 1 | `ridge_calibrated` | 0.18285295 | 0.897663 | 0.706070 | 0.625377 | 0.811161 |
| 2 | `additive` | 0.19199064 | 0.895989 | 0.693899 | 0.578414 | 0.813839 |
| 2 | `ridge` | 0.18827963 | 0.898684 | 0.706543 | 0.645554 | 0.831696 |
| 2 | `ridge_low_penalty` | 0.18827963 | 0.898684 | 0.706543 | 0.645554 | 0.831696 |
| 2 | `ridge_calibrated` | 0.18740915 | 0.898906 | 0.707350 | 0.645554 | 0.831696 |

## Paired recipe minus additive: mean ± sample SD

A positive MSE difference is worse; a positive correlation/R²/direction difference is better.
Magnitude-ratio difference is diagnostic and has no monotonic preferred direction.

| Metric | `ridge` | `ridge_low_penalty` | `ridge_calibrated` |
|---|---:|---:|---:|
| Pearson delta ↑ | +0.008293 ± 0.001468 | +0.008293 ± 0.001468 | +0.008293 ± 0.001468 |
| MSE ↓ | -0.00019155 ± 0.00003972 | -0.00019155 ± 0.00003972 | -0.00017376 ± 0.00004139 |
| Expression PCC ↑ | +0.000404 ± 0.000054 | +0.000404 ± 0.000054 | +0.000356 ± 0.000082 |
| Expression R² ↑ | +0.000857 ± 0.000127 | +0.000857 ± 0.000127 | +0.000753 ± 0.000173 |
| Top-20 MSE ↓ | -0.00248639 ± 0.00116525 | -0.00248639 ± 0.00116525 | -0.00127831 ± 0.00307679 |
| Top-20 expression PCC ↑ | +0.001831 ± 0.001207 | +0.001831 ± 0.001207 | +0.001338 ± 0.001461 |
| Top-20 expression R² ↑ | +0.011701 ± 0.002086 | +0.011701 ± 0.002086 | +0.010515 ± 0.002593 |
| Top-20 Pearson delta ↑ | +0.068269 ± 0.003337 | +0.068269 ± 0.003337 | +0.068269 ± 0.003337 |
| Top-20 direction accuracy ↑ | +0.017708 ± 0.002013 | +0.017708 ± 0.002013 | +0.017708 ± 0.002013 |
| Delta magnitude ratio (diagnostic) | -0.080002 ± 0.003471 | -0.080002 ± 0.003471 | -0.088264 ± 0.029393 |

## Paired recipe minus ridge: mean ± sample SD

A positive MSE difference is worse; a positive correlation/R²/direction difference is better.
Magnitude-ratio difference is diagnostic and has no monotonic preferred direction.

| Metric | `additive` | `ridge_low_penalty` | `ridge_calibrated` |
|---|---:|---:|---:|
| Pearson delta ↑ | -0.008293 ± 0.001468 | +0.000000 ± 0.000000 | +0.000000 ± 0.000000 |
| MSE ↓ | +0.00019155 ± 0.00003972 | +0.00000000 ± 0.00000000 | +0.00001779 ± 0.00002137 |
| Expression PCC ↑ | -0.000404 ± 0.000054 | +0.000000 ± 0.000000 | -0.000048 ± 0.000047 |
| Expression R² ↑ | -0.000857 ± 0.000127 | +0.000000 ± 0.000000 | -0.000104 ± 0.000138 |
| Top-20 MSE ↓ | +0.00248639 ± 0.00116525 | +0.00000000 ± 0.00000000 | +0.00120808 ± 0.00241878 |
| Top-20 expression PCC ↑ | -0.001831 ± 0.001207 | +0.000000 ± 0.000000 | -0.000494 ± 0.000757 |
| Top-20 expression R² ↑ | -0.011701 ± 0.002086 | +0.000000 ± 0.000000 | -0.001186 ± 0.002229 |
| Top-20 Pearson delta ↑ | -0.068269 ± 0.003337 | +0.000000 ± 0.000000 | +0.000000 ± 0.000000 |
| Top-20 direction accuracy ↑ | -0.017708 ± 0.002013 | +0.000000 ± 0.000000 | +0.000000 ± 0.000000 |
| Delta magnitude ratio (diagnostic) | +0.080002 ± 0.003471 | +0.000000 ± 0.000000 | -0.008262 ± 0.026369 |

## Every selected alpha and calibration scalar

Both ridge grids selected alpha **0.01 in every outer fold**. None selected a high penalty.
The calibrator was never clipped or assigned the zero-denominator fallback.

| Seed | Outer fold | Broad alpha | Low alpha | Training-only scalar |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0.01 | 0.01 | 0.979508223 |
| 0 | 1 | 0.01 | 0.01 | 0.952928718 |
| 0 | 2 | 0.01 | 0.01 | 1.078585653 |
| 0 | 3 | 0.01 | 0.01 | 1.044941313 |
| 0 | 4 | 0.01 | 0.01 | 0.967243254 |
| 1 | 0 | 0.01 | 0.01 | 0.938569425 |
| 1 | 1 | 0.01 | 0.01 | 0.990836555 |
| 1 | 2 | 0.01 | 0.01 | 0.904573859 |
| 1 | 3 | 0.01 | 0.01 | 0.910879173 |
| 1 | 4 | 0.01 | 0.01 | 0.988036837 |
| 2 | 0 | 0.01 | 0.01 | 1.037728812 |
| 2 | 1 | 0.01 | 0.01 | 0.987631861 |
| 2 | 2 | 0.01 | 0.01 | 1.032210178 |
| 2 | 3 | 0.01 | 0.01 | 0.964029550 |
| 2 | 4 | 0.01 | 0.01 | 1.065937057 |

Scalars span 0.904574 to 1.078586. Ten of fifteen are below one. The exact
fold train/predict/hide memberships and inner fitting scores appear in the unchanged
[summary.json](summary.json), so future agents can audit every exclusion.

## Reading and continuation

- Restricting the alpha grid offered no change: every metric and seed matched broad ridge exactly.
- Calibrated and ordinary ridge have equal Pearson delta and direction accuracy as expected for
  positive uniform scaling. Calibration raises all-gene MSE by **0.00001779 ± 0.00002137** and
  top-20 MSE by **0.00120808 ± 0.00241878**, with top-20 R² difference **−0.001186 ± 0.002229**.
  Two seeds worsen and one improves on these errors; no calibration benefit is established.
- Ordinary ridge minus additive has development Pearson difference **+0.008293 ± 0.001468**.
  Reported as an exploratory result on this fixed cohort and simple feature family; the fold seeds
  supply no independent replication-based significance claim or new generalization claim.
- A lower magnitude ratio does not demonstrate that excessive ridge regularization caused error.
  Here ridge selects the smallest fixed alpha, and the trained scalar is often below one.
  This outcome does not support increasing magnitudes by default. It says nothing causal about
  the historical high-alpha, many-feature B1 members.

Do not enlarge the grids, rerun with selected seeds, promote a recipe, alter exploration budgets
or score another used test based on these outcomes. Preserve all four results. The next useful
work is the independent frozen-inference reproduction and prospectively reviewed compatible
external cohort/evaluator boundary. A future development comparison needs a new dated fixed
protocol that identifies new information or a distinct mechanism.

## Reproducibility receipt

Runtime: Python 3.13.7, NumPy 2.5.3,
scikit-learn 1.9.1. Public bundle manifest split identity
`split_a391fa9e7b4eccb7` is provenance only; no split file was opened.
The raw [config.json](config.json) and [summary.json](summary.json) copies are byte-for-byte
from the run directory. Their hashes and this report are in [MD5SUMS.txt](MD5SUMS.txt) and
[SHA256SUMS.txt](SHA256SUMS.txt). Both checksum lists exclude themselves.

An independent archive check recomputed all **100** recipe-metric and paired-difference
mean/SD pairs from the raw seed metrics, checked all 15 alpha/scalar records, and verified
the summary’s config hash. No second model fit or evaluation was performed.

| Source/input | SHA256 |
|---|---|
| `tools/shrinkage_diagnostic.py` | `c1b65a3aa3ddca66e73afc683c3b5b59674aea812f4ad55693eca9ab43204299` |
| `docs/NORMAN_SHRINKAGE_PLAN.md` | `64022dc11c5962e328e260f47e57586e998bd852071b55e94847f9cd247d4015` |
| `genemila/features/api.py` | `6cded0b6c2105bceed8b08ad10d432cfefa496aa3824c5b31eb518df00f3b0d7` |
| `genemila/features/builtin.py` | `7385a22d565958ddd870297c722452072b1b2701431367dbc95290deba732725` |
| `genemila/pipeline.py` | `afb15b56bbe778d66f051f79db6d6bb47e7e1b1e4eaad080dd08bc90817ba82f` |
| `genemila/benchmark/evaluator.py` | `4cb2a6aa8ec0973b9fe431b9d58d43bbf90105077ffe736cdb64b1cb6b283a25` |
| `genemila/benchmark/comparable.py` | `94be9a12351b1e2e870dae626c9a039bbae043d7764f653607ee477ee57dc9f7` |
| `genemila/benchmark/__init__.py` | `b39b000d6993ef461532198ee506b0e0b287186ee99c048a49f6c42aa3df47b8` |
| `public.npz` | `b2c7eb3d34806a8d05b3a7719670833aa547d235e9d00767acce4126cbdc5411` |
| `knowledge/targets.json` | `f02c03f13588ea93b8a14a7979e9c31b8bc317d6cb18b9c24e38362b3bb7662c` |
| `manifest.json` | `1bdb4f24918792bb7497d5926eb0dac31dbaac48353c2ae7170304005eddec17` |
| Training perturbation order | `9e5f706dd00f69e943234b7341fa69ae8926a8b1c5a7d6e03c9c2564e4366bcc` |
| Gene order | `b21b43e09bd8d89e1877e6acaedb79ed776dbe7d75471f2feee2a14053a185a9` |
