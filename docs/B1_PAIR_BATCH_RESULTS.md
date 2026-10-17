# One per-pair feature correction comparison

The fixed development screen failed: Pearson change is effectively zero across partitions and candidate mean MSE/additive MSE is1.044959, above the1.01 limit. This candidate is rejected under its predeclared advancement rule. **Original frozen B1 remains delivered and unchanged.**

Claim [#34](https://github.com/andresloak100/Gene-Mila/issues/34), [PR #35](https://github.com/andresloak100/Gene-Mila/pull/35). Prospective [plan](B1_PAIR_BATCH_PLAN.md) 9920fec and independently reviewed source d3909a1 were published before fitting. One free run: **45 shared fits, 268.524 seconds, $0 API spend**. No retry, extra alpha, additional feature change, scalar calibration or search extension.

## Complete global metrics

| Metric | r1 + corrected r2 | r1 + original r2 | Additive | r1 | Original r2 | Corrected r2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pearson_delta | 0.588816 ± 0.021337 | 0.588819 ± 0.021309 | 0.562024 ± 0.019969 | 0.588730 ± 0.022156 | 0.585778 ± 0.020610 | 0.585772 ± 0.020660 |
| mse | 0.008777 ± 0.001214 | 0.017833 ± 0.016697 | 0.008399 ± 0.000702 | 0.008280 ± 0.000780 | 0.047972 ± 0.067802 | 0.010982 ± 0.003959 |
| pearson_expr | 0.982968 ± 0.001614 | 0.982972 ± 0.001610 | 0.982228 ± 0.001571 | 0.982650 ± 0.001667 | 0.982958 ± 0.001699 | 0.982948 ± 0.001706 |
| cellforge_r2 | 0.958432 ± 0.005580 | 0.916202 ± 0.077742 | 0.960266 ± 0.003242 | 0.960679 ± 0.003654 | 0.775621 ± 0.316072 | 0.948177 ± 0.018307 |
| mse_top | 0.197545 ± 0.023791 | 0.213271 ± 0.043682 | 0.196988 ± 0.022189 | 0.201354 ± 0.022563 | 0.247022 ± 0.107312 | 0.196785 ± 0.027631 |
| cellforge_pcc_de | 0.897073 ± 0.007252 | 0.897094 ± 0.007213 | 0.894024 ± 0.005803 | 0.894931 ± 0.007703 | 0.898560 ± 0.006915 | 0.898517 ± 0.006990 |
| r2_top | 0.696189 ± 0.030059 | 0.683626 ± 0.041024 | 0.683468 ± 0.027225 | 0.693139 ± 0.029897 | 0.655870 ± 0.087809 | 0.696028 ± 0.031852 |
| pearson_delta_top | 0.658903 ± 0.027521 | 0.658922 ± 0.027473 | 0.555730 ± 0.024651 | 0.658425 ± 0.029801 | 0.654319 ± 0.026000 | 0.654277 ± 0.026089 |
| direction_acc_top | 0.817560 ± 0.019912 | 0.815625 ± 0.022047 | 0.793006 ± 0.017361 | 0.810417 ± 0.022017 | 0.818006 ± 0.021271 | 0.820833 ± 0.018688 |
| delta_scale_ratio | 0.686125 ± 0.023598 | 0.750931 ± 0.134954 | 0.792432 ± 0.020610 | 0.624570 ± 0.014690 | 0.899699 ± 0.281162 | 0.767406 ± 0.057247 |

Mean ± sample SD over seeds12/13/14, five gene folds each,112 historically used public-training conditions and2083 genes. Fold assignments are sensitivity repeats on the same cohort, not independent biological replication. Top20 uses largest absolute development deltas, not stored cell-derived DE. The cellforge metric names do not establish matched CellForge evaluation.

## Paired changes and fixed screen

| Candidate minus comparator | pearson_delta | mse | mse_top | direction_acc_top |
| --- | ---: | ---: | ---: | ---: |
| fixed_ensemble | -0.000003 ± 0.000028 | -0.009056 ± 0.015643 | -0.015727 ± 0.027389 | 0.001935 ± 0.003797 |
| additive | 0.026792 ± 0.002859 | 0.000378 ± 0.000842 | 0.000557 ± 0.003201 | 0.024554 ± 0.005838 |

Primary candidate-minus-control Pearson gains: +0.0000299230, -0.0000190494, -0.0000190085. Mean ± sample SD: **-0.000003 ± 0.000028**. The mean must exceed the fixed max(0.002, sampleSD) threshold **0.002**.

| Predeclared check | Pass |
| --- | ---: |
| pearson_gain_each_positive | NO |
| pearson_gain_mean_above_threshold | NO |
| mse_to_fixed_ensemble_within_one_percent | yes |
| mse_top_to_fixed_ensemble_within_one_percent | yes |
| mse_to_additive_within_one_percent | NO |
| mse_top_to_additive_within_one_percent | yes |

| Ratio of across-seed means | Ratio | Pass |
| --- | ---: | ---: |
| mse_to_fixed_ensemble | 0.492180 | yes |
| mse_top_to_fixed_ensemble | 0.926260 | yes |
| mse_to_additive | 1.044959 | NO |
| mse_top_to_additive | 1.002827 | yes |

The lower mean MSE against the control has paired change−0.009056±0.015643, inside partitionSD; top20 change−0.015727±0.027389 is likewise insideSD. Do not call the mean ratios an established stable error reduction. The candidate-minus-additive top20 difference is also inside its partition variation. The source correction passes behavioral checks, but that alone does not qualify this model under its fixed accuracy screen.

Every check must pass. These are practical screening margins, not significance or noninferiority tests. Within1% of additive is not beating it. No claim is made for differences inside partition variation.

## Individual assignments

| Seed | Candidate Pearson | Control Pearson | Additive Pearson | Candidate MSE | Control MSE | Additive MSE | Candidate top20 MSE | Additive top20 MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | 0.613344 | 0.613314 | 0.585073 | 0.007554 | 0.007614 | 0.007610 | 0.170106 | 0.171733 |
| 13 | 0.574537 | 0.574556 | 0.551041 | 0.008795 | 0.008784 | 0.008955 | 0.212423 | 0.213357 |
| 14 | 0.578566 | 0.578585 | 0.549957 | 0.009982 | 0.037101 | 0.008634 | 0.210105 | 0.205873 |

## Metadata strata

| Group | Counts seeds12/13/14 | Candidate − control Pearson | Candidate − additive Pearson | Candidate − additive MSE |
| --- | ---: | ---: | ---: | ---: |
| external_all | 91/91/91 | -0.000010 ± 0.000028 | 0.031312 ± 0.004081 | 0.000387 ± 0.001034 |
| external_none | 12/12/12 | 0.000054 ± 0.000017 | 0.003363 ± 0.002754 | 0.000371 ± 0.000054 |
| external_partial | 9/9/9 | -0.000002 ± 0.000060 | 0.012325 ± 0.004225 | 0.000290 ± 0.000035 |
| known_0 | 75/82/83 | 0.000013 ± 0.000015 | 0.027470 ± 0.003694 | -0.000107 ± 0.000120 |
| known_1 | 37/30/29 | -0.000047 ± 0.000068 | 0.024622 ± 0.004751 | 0.001721 ± 0.003000 |
| pair | 41/41/41 | -0.000028 ± 0.000048 | 0.028918 ± 0.002173 | 0.001139 ± 0.002250 |
| pair_external_all | 31/31/31 | -0.000036 ± 0.000046 | 0.034442 ± 0.003578 | 0.001452 ± 0.002994 |
| pair_external_none | 1/1/1 | 0.000000 ± 0.000006 | 0.007010 ± 0.009336 | -0.000902 ± 0.000281 |
| pair_external_partial | 9/9/9 | -0.000002 ± 0.000060 | 0.012325 ± 0.004225 | 0.000290 ± 0.000035 |
| pair_known_0 | 4/11/12 | 0.000016 ± 0.000047 | 0.040056 ± 0.010442 | -0.000690 ± 0.000891 |
| pair_known_1 | 37/30/29 | -0.000047 ± 0.000068 | 0.024622 ± 0.004751 | 0.001721 ± 0.003000 |
| singleton | 71/71/71 | 0.000012 ± 0.000017 | 0.025564 ± 0.003260 | -0.000062 ± 0.000078 |
| singleton_external_all | 60/60/60 | 0.000003 ± 0.000020 | 0.029696 ± 0.004429 | -0.000163 ± 0.000095 |
| singleton_external_none | 11/11/11 | 0.000059 ± 0.000018 | 0.003031 ± 0.003698 | 0.000487 ± 0.000084 |
| singleton_known_0 | 71/71/71 | 0.000012 ± 0.000017 | 0.025564 ± 0.003260 | -0.000062 ± 0.000078 |

Groups overlap, and fold-dependent known-singleton memberships change with permitted training rows. External coverage is metadata availability, not perturbation exposure or feature completeness. Small groups do not establish mechanisms or define a future cohort. Full ten-metric/arm/seed/stratum findings and memberships are in the [summary](results/b1_pair_batch_20261013/summary.json).

## What changed and what remains uncertain

Only the copied r2 prior-edge e34 source changed. Its fallback now operates per pair, preserving finite nonzero positive or negative prior weights and otherwise using finite control correlation when both targets exist, else zero; singleton rows stay zero. Missing and zero-weight edges use fallback. Version3/input metadata describe that rule. Parsing/caches/finite sanitation remain identical; e401 composes the corrected feature without a source change. The snapshot has exactly one source difference. Original r2 alpha0.00198, model seed2, feature parameters/columns and r1 remain fixed. Training-only scaling, fresh full-hide contexts and original training-then-whole-query-fold batches are preserved.

Synthetic tests establish e34 row invariance across batch composition/order and its e401 product, not whole-model batch invariance or improved accuracy. The defect was identified before the penalty outcomes; metadata confirms mixed training/query batches, without response inspection. Original e14 kernel-not-guaranteed-PSD, k20 neighbor behavior and external-input ordering/measurement assumptions persist. All original package files remain pinned and unchanged.

## Verification and preservation

Full **490 tests passed**, no skips,8 dependency deprecation warnings in648.09s; focused **8 passed in3.59s**. Independent source/method review found no material issue before publication. Independent NumPy/stdlib saved-array verification checked **2,880 metric values and5,138 aggregate/gate values**, six arms,15full-hide folds/45ordered events,21exact shared-mean/additive checks,14published source pins,820package files and all292original plus292copied r2 plugin pins. Only e34 differs and copied e34 matches the published variant; original r2 specification/alpha0.00198 and e401 source are unchanged. Maximum numerical discrepancy7.77e-16; all original result artifacts stayed unchanged. No model fits were replayed. See the [verification receipt](results/b1_pair_batch_20261013/verification.json).

Chat2 independently checked **2,560 global/stratum aggregate and paired mean/sample-SD statistic pairs**, all six report tables,15full-hide folds/stratum memberships,80ordered progress events including45fits, unchanged r2 specification/alpha and292copied-plugin hash metadata with only e34 differing. Every gate and reported limit matches; no discrepancy found. It read no numeric arrays or model code and made no fits, API calls, edits or Git changes. See its [data-free receipt](results/b1_pair_batch_20261013/chat2_review.json). Its wording correction from single-alpha to source-correction block is incorporated.

Run directory: /Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-pair-batch/runs/b1_pair_batch_20261013. Numeric prediction arrays, package/context and responses remain ignored locally. The data-free archive preserves exact config/summary/progress, command/launcher, source/input/runtime pins, independent reviews and SHA256/MD5 lists. No API, oracle query, private/split read, new data, protected-code or main-checkout change. STOP and the shared ledger remain intact.

## Descriptive offset check

An independent post-hoc decomposition of existing corrected-minus-original r2 arrays separates each condition's mean across genes from its centered change. In seed14,99.999931% of change energy is a gene-constant offset (offset RMS0.260324, gene-varying RMS0.000216); seed12 is99.6346%, seed13 is68.7004% with much smaller absolute change. Pearson correlation is insensitive to a constant added across genes. This is consistent with the error movement and almost unchanged Pearson, not a new candidate, unique causal proof or independent efficacy evidence. The mean error decrease is driven chiefly by seed14: candidate-control MSE changes are−0.00006044,+0.00001143,−0.02711887. Do not change objectives or promote after this description.

## Claude continuation

This is same-cohort development evidence after historical feature selection. It does not rescore the delivered frozen B1 or imply its historical0.723 fell. Preserve this closed source-correction block and all negative results. No automatic new full-training fit/export, held-out lookup, alternative fallback/alpha/seeds/margins, paid call or B3 restart. A separate frozen comparison on compatible unseen perturbations with response access, preprocessing and multi-metric rules fixed first is still required; account/host/cohort setup remains deferred. Read current HANDOFF section1 for integration status and the exact next step.
