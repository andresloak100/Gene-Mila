# Fixed two-member B1 development screen

The r1+r2 equal average passed the predeclared development screen against the original three-member refit average. Pearson delta increased in all three fold assignments, with a paired gain of **+0.125342 ± 0.015775** and lower overall/top-20 MSE. The candidate has higher correlation than additive, but higher mean errors. **Original frozen B1 remains delivered and unchanged.**

Claim [#28](https://github.com/andresloak100/Gene-Mila/issues/28), [PR #29](https://github.com/andresloak100/Gene-Mila/pull/29); diagnostic dependency [PR #27](https://github.com/andresloak100/Gene-Mila/pull/27). Prospective [plan](B1_TWO_MEMBER_PLAN.md) `2fc1ab1` and reviewed source `5467687` were published before fitting. One free run: **45 shared original-recipe fits, 307.875 seconds total, $0 API spend**, no retry or search extension.

## Complete global metrics

| Metric | r1+r2 candidate | Three-member control | Additive |
|---|---:|---:|---:|
| `pearson_delta` | 0.584325 ± 0.011274 | 0.458983 ± 0.020521 | 0.561655 ± 0.008879 |
| `mse` | 0.009420 ± 0.001651 | 0.013530 ± 0.001790 | 0.008515 ± 0.000225 |
| `pearson_expr` | 0.982641 ± 0.000154 | 0.982669 ± 0.000079 | 0.982120 ± 0.000392 |
| `cellforge_r2` | 0.955488 ± 0.007664 | 0.935745 ± 0.008438 | 0.959829 ± 0.000990 |
| `mse_top` | 0.200563 ± 0.008383 | 0.212396 ± 0.006466 | 0.192678 ± 0.002571 |
| `cellforge_pcc_de` | 0.899062 ± 0.001805 | 0.899125 ± 0.001337 | 0.898574 ± 0.002664 |
| `r2_top` | 0.698475 ± 0.010054 | 0.673190 ± 0.014784 | 0.693618 ± 0.004252 |
| `pearson_delta_top` | 0.650645 ± 0.019029 | 0.556982 ± 0.023486 | 0.559596 ± 0.012785 |
| `direction_acc_top` | 0.810714 ± 0.010092 | 0.725893 ± 0.003370 | 0.796280 ± 0.008403 |
| `delta_scale_ratio` | 0.714085 ± 0.053263 | 0.773290 ± 0.091161 | 0.800406 ± 0.010107 |

Every entry is mean ± sample SD over fixed gene-fold seeds **3/4/5**, five folds each, the same 112 public-training conditions and 2,083 genes. Original features, parameters, alphas and model seeds are unchanged. Both ensembles use identical member predictions; this tests composition without additional candidate fits. All gene-sharing response rows are hidden for the predicted fold, and scaling uses training rows only. Top-20 is the largest absolute development delta, not a cell-derived DE reference. The `cellforge_*` metric names do not establish a matched CellForge comparison.

## Paired changes and fixed gate

| Candidate minus comparator | Pearson delta | MSE | Top-20 MSE | Top-20 direction |
|---|---:|---:|---:|---:|
| baseline | 0.125342 ± 0.015775 | -0.004111 ± 0.001469 | -0.011833 ± 0.005500 | 0.084821 ± 0.013333 |
| additive | 0.022670 ± 0.002693 | 0.000905 ± 0.001471 | 0.007885 ± 0.006483 | 0.014435 ± 0.001690 |

The three primary gains are **+0.122298, +0.142416, +0.111311**. Their mean 0.125342 exceeds the fixed threshold `max(0.002, sample SD)` = 0.015775. Ratios of across-seed mean candidate/control errors are **0.696179 MSE** and **0.944288 top-20 MSE**, both below the 1.01 limits. All four gate checks pass. This gate is a screening heuristic, not a significance test.

Against additive, mean candidate MSE is about 10.6% higher and top-20 MSE about 4.1% higher. The MSE difference is inside its partition SD; top-20 error is higher in all three assignments. Higher correlation is therefore not a general multi-metric win. All differences and individual assignments are preserved in the [comparison summary](results/b1_two_member_test_20261013/comparison.json).

## Individual assignments

| Fold seed | Candidate Pearson delta | Control | Additive | Candidate MSE | Control MSE | Additive MSE |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 0.571870 | 0.449572 | 0.552287 | 0.011312 | 0.014645 | 0.008710 |
| 4 | 0.587272 | 0.444856 | 0.562731 | 0.008675 | 0.014480 | 0.008566 |
| 5 | 0.593832 | 0.482521 | 0.569947 | 0.008271 | 0.011466 | 0.008269 |

## Original members, context only

| Member | Pearson delta | MSE | Top-20 MSE | Top-20 direction |
|---|---:|---:|---:|---:|
| r1 / EXP_0681 | 0.584277 ± 0.009812 | 0.008408 ± 0.000125 | 0.199090 ± 0.002929 | 0.808333 ± 0.011306 |
| r2 / EXP_0729 | 0.580829 ± 0.013337 | 0.013301 ± 0.006768 | 0.206468 ± 0.018923 | 0.811012 ± 0.011948 |
| r3 / EXP_0519 | 0.317044 ± 0.016921 | 0.051128 ± 0.012757 | 0.339234 ± 0.044113 | 0.671131 ± 0.025452 |

r1 alone has nearly the same correlation as the two-member candidate and lower mean errors here. These member readings are descriptive context; no additional subset was selected or tested as a new candidate. r2 still has variable MSE. Do not reopen this block to optimize weights, choose a singleton member or add seeds after seeing the outcomes.

## Metadata strata

| Group | Counts, seeds3/4/5 | Candidate − control Pearson delta | Candidate − additive Pearson delta |
|---|---:|---:|---:|
| external_all | 91/91/91 | 0.121701 ± 0.017953 | 0.027706 ± 0.002760 |
| external_none | 12/12/12 | 0.197569 ± 0.076801 | -0.002557 ± 0.008681 |
| external_partial | 9/9/9 | 0.065850 ± 0.036076 | 0.005387 ± 0.006185 |
| known_0 | 80/76/76 | 0.160833 ± 0.018591 | 0.021960 ± 0.002667 |
| known_1 | 32/36/36 | 0.045994 ± 0.012645 | 0.024197 ± 0.004084 |
| pair | 41/41/41 | 0.051068 ± 0.014200 | 0.025449 ± 0.002992 |
| pair_external_all | 31/31/31 | 0.041382 ± 0.018446 | 0.031983 ± 0.005075 |
| pair_external_none | 1/1/1 | 0.218289 ± 0.122274 | 0.003434 ± 0.003348 |
| pair_external_partial | 9/9/9 | 0.065850 ± 0.036076 | 0.005387 ± 0.006185 |
| pair_known_0 | 9/5/5 | 0.075981 ± 0.040343 | 0.031833 ± 0.005293 |
| pair_known_1 | 32/36/36 | 0.045994 ± 0.012645 | 0.024197 ± 0.004084 |
| singleton | 71/71/71 | 0.168232 ± 0.016755 | 0.021066 ± 0.002886 |
| singleton_external_all | 60/60/60 | 0.163199 ± 0.017823 | 0.025496 ± 0.001987 |
| singleton_external_none | 11/11/11 | 0.195685 ± 0.073830 | -0.003102 ± 0.009301 |
| singleton_known_0 | 71/71/71 | 0.168232 ± 0.016755 | 0.021066 ± 0.002886 |

Groups overlap; known-singleton membership changes with folds. External availability is metadata coverage, not perturbation exposure or feature completeness. The no-profile group shows no consistent gain over additive; pair-with-no-profile has one condition and pair-known0 has only 5–9. These groups cannot establish a mechanism or choose a cohort. All ten metrics, memberships and member readings are archived.

## Validation and preservation

Full **482 tests passed**, no skips, 8 dependency deprecation warnings, 654.28 seconds; focused **15 passed in 1.39 seconds**. Independent source/method review resolved the parent-timeout finding before publication. Independent NumPy/stdlib arithmetic verified **3,840 metric values and 4,492 aggregate/gate values**, all 15 folds/45 fit events, exact candidate/control/additive arrays and source/package pins (maximum metric difference 8.88e-16). Baseline artifacts remain unchanged. See the [verification receipt](results/b1_two_member_test_20261013/verification.json). Chat 2 independently verified **2,240 global/stratum mean/sample-SD statistic pairs**, folds/counts/progress and summary hashes (maximum rounding difference 4.44e-16); see its [data-free review](results/b1_two_member_test_20261013/chat2_review.json). A separate report review verified table mappings and interpretation. No discrepancies were found.

Run directory: `/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-b1-two-member/runs/b1_two_member_test_20261013`. Original `summary.json`/`predictions.npz` remain separate and unchanged; candidate arrays and `comparison.json` are separate. Numeric arrays and package/context remain ignored locally. The archive preserves byte-identical config, both summaries and progress, exact command, source/input pins, reviews and verified SHA256/MD5 lists.

## Claude continuation

This is a promising simpler composition for independent validation, not a newly delivered frozen coefficient model. These folds reuse the historically selected cohort after r3 removal was chosen from diagnosis seeds0/1/2. No candidate was calculated on those diagnosis seeds. Repartitioning is not an untouched test, and these refits do not rescore the original frozen B1 or imply its historical 0.723 fell. No CellForge superiority is established.

Preserve the closed block and the original B1 package. The next model milestone is a separately specified, frozen r1+r2 candidate and additive comparison on compatible unseen perturbations, with the response-access boundary, preprocessing and multi-metric rule fixed before outcomes. Account/host isolation and a new cohort are still deferred/unapproved; do not read private/split files, restart B3, launch paid agents or silently extend this grid. Read current HANDOFF section1 before further work.
