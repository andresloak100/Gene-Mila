# One fixed r2 regularization comparison

The fixed development screen failed: all-gene MSE improved about2.0%, but top20 MSE increased1.0672% against the control, beyond the fixed1% limit. This candidate is rejected under its predeclared advancement rule. **Original frozen B1 remains delivered and unchanged.**

Claim [#32](https://github.com/andresloak100/Gene-Mila/issues/32), [PR #33](https://github.com/andresloak100/Gene-Mila/pull/33). Prospective [plan](B1_R2_REGULARIZATION_PLAN.md) fe64e9e and independently reviewed source 8134cd9 were published before fitting. One free run: **45 shared fits, 266.442 seconds, $0 API spend**. No retry, extra alpha, feature change, scalar calibration or search extension.

## Complete global metrics

| Metric | r1 + regularized r2 | r1 + original r2 | Additive | r1 | Original r2 | Regularized r2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pearson_delta | 0.593702 ± 0.005731 | 0.594151 ± 0.005555 | 0.570125 ± 0.005630 | 0.594226 ± 0.004712 | 0.591500 ± 0.006175 | 0.589569 ± 0.006467 |
| mse | 0.007580 ± 0.000199 | 0.007734 ± 0.000201 | 0.008273 ± 0.000284 | 0.007689 ± 0.000217 | 0.008218 ± 0.000416 | 0.007642 ± 0.000212 |
| pearson_expr | 0.984464 ± 0.000549 | 0.984350 ± 0.000621 | 0.983055 ± 0.000614 | 0.984219 ± 0.000568 | 0.984206 ± 0.000712 | 0.984488 ± 0.000547 |
| cellforge_r2 | 0.964260 ± 0.001084 | 0.963523 ± 0.001112 | 0.961113 ± 0.001400 | 0.963668 ± 0.001166 | 0.961267 ± 0.002118 | 0.964042 ± 0.001161 |
| mse_top | 0.173743 ± 0.003823 | 0.171908 ± 0.003812 | 0.174556 ± 0.001196 | 0.177689 ± 0.003867 | 0.167761 ± 0.003944 | 0.170900 ± 0.003953 |
| cellforge_pcc_de | 0.906049 ± 0.003285 | 0.906505 ± 0.003713 | 0.903099 ± 0.002515 | 0.904784 ± 0.003451 | 0.907549 ± 0.004054 | 0.906748 ± 0.003133 |
| r2_top | 0.733148 ± 0.005281 | 0.734608 ± 0.005496 | 0.718350 ± 0.002229 | 0.730089 ± 0.005145 | 0.736943 ± 0.006105 | 0.734650 ± 0.005472 |
| pearson_delta_top | 0.666745 ± 0.006073 | 0.666712 ± 0.005718 | 0.571900 ± 0.012633 | 0.667314 ± 0.004215 | 0.661792 ± 0.006567 | 0.661264 ± 0.007226 |
| direction_acc_top | 0.824851 ± 0.008545 | 0.824554 ± 0.009502 | 0.802976 ± 0.007814 | 0.817113 ± 0.006505 | 0.830804 ± 0.007016 | 0.830655 ± 0.009032 |
| delta_scale_ratio | 0.702646 ± 0.019303 | 0.722333 ± 0.022608 | 0.867638 ± 0.006214 | 0.678308 ± 0.023200 | 0.785156 ± 0.020388 | 0.735951 ± 0.015200 |

Mean ± sample SD over seeds9/10/11, five gene folds each,112 historically used public-training conditions and2083 genes. Fold assignments are sensitivity repeats on the same cohort, not independent biological replication. Top20 uses largest absolute development deltas, not stored cell-derived DE. The cellforge metric names do not establish matched CellForge evaluation.

## Paired changes and fixed screen

| Candidate minus comparator | pearson_delta | mse | mse_top | direction_acc_top |
| --- | ---: | ---: | ---: | ---: |
| fixed_ensemble | -0.000449 ± 0.000291 | -0.000154 ± 0.000093 | 0.001835 ± 0.000056 | 0.000298 ± 0.001289 |
| additive | 0.023576 ± 0.001551 | -0.000693 ± 0.000139 | -0.000814 ± 0.002837 | 0.021875 ± 0.002362 |

Primary fixed-control minus candidate MSE improvements: 0.0002138739, 0.0002007680, 0.0000474443. Mean ± sample SD: **0.000154 ± 0.000093**.

Pearson changes, candidate minus fixed control: -0.0007824478, -0.0002404268, -0.0003255189. Mean ± sample SD: **-0.000449 ± 0.000291**.

| Predeclared check | Pass |
| --- | ---: |
| mse_gain_each_positive | yes |
| mse_gain_mean_above_sd | yes |
| pearson_each_above_min | yes |
| pearson_mean_above_min | yes |
| mse_to_additive_within_one_percent | yes |
| mse_top_to_additive_within_one_percent | yes |
| mse_top_to_fixed_ensemble_within_one_percent | NO |

| Ratio of across-seed means | Ratio | Pass |
| --- | ---: | ---: |
| mse_to_additive | 0.916183 | yes |
| mse_top_to_additive | 0.995338 | yes |
| mse_top_to_fixed_ensemble | 1.010672 | NO |

Every check must pass. These are practical screening margins, not significance or noninferiority tests. Within1% of additive is not beating it. No claim is made for differences inside partition variation.

## Individual assignments

| Seed | Candidate Pearson | Control Pearson | Additive Pearson | Candidate MSE | Control MSE | Additive MSE | Candidate top20 MSE | Additive top20 MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 0.588892 | 0.589675 | 0.564371 | 0.007367 | 0.007581 | 0.007946 | 0.170238 | 0.173190 |
| 10 | 0.592170 | 0.592410 | 0.570383 | 0.007760 | 0.007961 | 0.008412 | 0.177820 | 0.175415 |
| 11 | 0.600043 | 0.600369 | 0.575622 | 0.007612 | 0.007660 | 0.008461 | 0.173170 | 0.175064 |

## Metadata strata

| Group | Counts seeds9/10/11 | Candidate − control Pearson | Candidate − additive Pearson | Candidate − additive MSE |
| --- | ---: | ---: | ---: | ---: |
| external_all | 91/91/91 | -0.000275 ± 0.000239 | 0.028054 ± 0.001351 | -0.000834 ± 0.000175 |
| external_none | 12/12/12 | -0.003043 ± 0.000405 | -0.001656 ± 0.002784 | 0.000474 ± 0.000213 |
| external_partial | 9/9/9 | 0.001240 ± 0.000945 | 0.011949 ± 0.002802 | -0.000824 ± 0.000350 |
| known_0 | 78/76/76 | -0.000092 ± 0.000087 | 0.025790 ± 0.002101 | -0.000187 ± 0.000103 |
| known_1 | 34/36/36 | -0.001249 ± 0.001067 | 0.018754 ± 0.000257 | -0.001787 ± 0.000253 |
| pair | 41/41/41 | -0.001075 ± 0.000705 | 0.021990 ± 0.001234 | -0.001771 ± 0.000340 |
| pair_external_all | 31/31/31 | -0.001779 ± 0.000662 | 0.025330 ± 0.000889 | -0.002077 ± 0.000525 |
| pair_external_none | 1/1/1 | -0.000070 ± 0.000060 | 0.008806 ± 0.008728 | -0.000825 ± 0.000739 |
| pair_external_partial | 9/9/9 | 0.001240 ± 0.000945 | 0.011949 ± 0.002802 | -0.000824 ± 0.000350 |
| pair_known_0 | 7/5/5 | -0.000264 ± 0.001220 | 0.042141 ± 0.005982 | -0.001714 ± 0.001056 |
| pair_known_1 | 34/36/36 | -0.001249 ± 0.001067 | 0.018754 ± 0.000257 | -0.001787 ± 0.000253 |
| singleton | 71/71/71 | -0.000088 ± 0.000075 | 0.024493 ± 0.001748 | -0.000071 ± 0.000044 |
| singleton_external_all | 60/60/60 | 0.000503 ± 0.000121 | 0.029461 ± 0.001625 | -0.000192 ± 0.000050 |
| singleton_external_none | 11/11/11 | -0.003314 ± 0.000446 | -0.002607 ± 0.002419 | 0.000592 ± 0.000175 |
| singleton_known_0 | 71/71/71 | -0.000088 ± 0.000075 | 0.024493 ± 0.001748 | -0.000071 ± 0.000044 |

Groups overlap, and fold-dependent known-singleton memberships change with permitted training rows. External coverage is metadata availability, not perturbation exposure or feature completeness. Small groups do not establish mechanisms or define a future cohort. Full ten-metric/arm/seed/stratum findings and memberships are in the [summary](results/b1_r2_regularization_20261013/summary.json).

## What changed and what remains uncertain

Only a deep-copied r2 ridge alpha changed from0.00198 to20000, matching original r1. Original feature recipes, parameters, expected columns, model seeds and plugin snapshot stay fixed. Each member receives a fresh full-hide view; scaling uses training rows only. Original train-batch then whole-query-fold batch behavior is preserved. Both equal averages share exactly the same r1 predictions. There is no inner tuning and original package bytes are unchanged.

Source-only audit found batch-dependent prior-edge fallback in e34/e401, an e14 kernel not guaranteed PSD, k20 neighbor behavior and external-input ordering/measurement assumptions. The small original penalty motivates a stability hypothesis; it does not establish exact OLS equivalence or the cause of errors. This alpha-only test cannot repair those features or establish stable standalone inference.

## Verification and preservation

Full **490 tests passed**, no skips,8 dependency deprecation warnings in647.09s; focused **8 passed in1.32s**. Independent source/method review found no material issue before publication. Independent NumPy/stdlib saved-array verification checked **2,880 metric values and5,139 aggregate/gate values**, six arms,15full-hide folds/45ordered fit events,21exact shared-mean/additive-array checks, alpha-only identity,12source pins and820package-file pins. Maximum discrepancies were7.77e-16 for metrics and5.76e-16 for aggregates. All original artifacts stayed unchanged; no model fit was replayed. See the [verification receipt](results/b1_r2_regularization_20261013/verification.json).

Chat2 independently checked **2,560 global/stratum mean/sample-SD statistic pairs**, all six report tables, fold/hide/count/event/variant metadata, plan pin and every gate (maximum rounding difference2.22e-16). It read no numeric arrays, labels or model code and made no fits or API calls; see its [data-free receipt](results/b1_r2_regularization_20261013/chat2_review.json). Both reviews confirm the failed verdict; the exact1.0106722979 ratio cannot be rounded into a pass.

Run directory: /Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-r2-regularization/runs/b1_r2_regularization_20261013. Numeric prediction arrays, package/context and responses remain ignored locally. The data-free archive preserves exact config/summary/progress, command/launcher, source/input/runtime pins, independent reviews and SHA256/MD5 lists. No API, oracle query, private/split read, new data, protected-code or main-checkout change. STOP and the shared ledger remain intact.

## Claude continuation

This is same-cohort development evidence after historical feature selection. It does not rescore the delivered frozen B1 or imply its historical0.723 fell. Preserve this closed single-alpha block and all negative results. No automatic new full-training fit/export, held-out lookup, alternative alpha/seeds/margins, paid call or B3 restart. A separate frozen comparison on compatible unseen perturbations with response access, preprocessing and multi-metric rules fixed first is still required; account/host/cohort setup remains deferred. Read current HANDOFF section1 for integration status and the exact next step.
