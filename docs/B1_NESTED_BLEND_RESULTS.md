# Nested additive-blend development result: rejected

The one-scalar blend failed its predeclared screen. Pearson delta fell in every repeat beyond the permitted margin; the mean MSE improvement was smaller than its partition SD. **Do not merge this unused experimental runner or promote the candidate.** Preserve the original delivered B1 and the prior two-member candidate.

Claim [#30](https://github.com/andresloak100/Gene-Mila/issues/30), [draft PR #31](https://github.com/andresloak100/Gene-Mila/pull/31). Prospective [plan](B1_NESTED_BLEND_PLAN.md)21f50d9 and reviewed source1238dac were published before fitting. One free run: **120 member fits,506.492 seconds,$0 API**, no retry or grid extension.

## All global metrics

| Metric | Learned blend | Fixed r1/r2 mean | Additive |
|---|---:|---:|---:|
| pearson_delta | 0.557795 ± 0.007611 | 0.575703 ± 0.009284 | 0.549573 ± 0.007776 |
| mse | 0.008796 ± 0.000159 | 0.010017 ± 0.001202 | 0.008795 ± 0.000339 |
| pearson_expr | 0.982097 ± 0.000648 | 0.982500 ± 0.000876 | 0.981715 ± 0.000734 |
| cellforge_r2 | 0.958575 ± 0.000782 | 0.952303 ± 0.006098 | 0.958638 ± 0.001688 |
| mse_top | 0.198983 ± 0.008823 | 0.200117 ± 0.006360 | 0.201088 ± 0.009942 |
| cellforge_pcc_de | 0.893962 ± 0.002661 | 0.896371 ± 0.002285 | 0.891998 ± 0.003034 |
| r2_top | 0.686717 ± 0.009643 | 0.695614 ± 0.009641 | 0.679619 ± 0.010518 |
| pearson_delta_top | 0.574647 ± 0.012270 | 0.642266 ± 0.014805 | 0.541525 ± 0.016001 |
| direction_acc_top | 0.797321 ± 0.011633 | 0.808185 ± 0.016228 | 0.778571 ± 0.013213 |
| delta_scale_ratio | 0.779981 ± 0.047674 | 0.731934 ± 0.037260 | 0.795685 ± 0.029345 |

Mean ± sample SD over outer gene-fold seeds6/7/8, five folds each, the same112 public-training conditions/2083genes. Three inner gene folds per outer fold learned one clipped weight by pooled all-gene MSE; original member features/parameters/alphas/seeds were fixed. All outer/inner gene-sharing response rows were hidden appropriately. This is same-cohort partition sensitivity after historical selection, not independent replication. Top-20 uses absolute development delta, not cell-derived DE.

## Paired readings and rejection

| Candidate minus control | Pearson delta | MSE | Top-20 MSE | Top-20 direction |
|---|---:|---:|---:|---:|
| fixed_ensemble | -0.017908 ± 0.004063 | -0.001221 ± 0.001291 | -0.001135 ± 0.003832 | -0.010863 ± 0.006536 |
| additive | 0.008222 ± 0.005372 | 0.000001 ± 0.000183 | -0.002105 ± 0.002019 | 0.018750 ± 0.006202 |

Fixed-ensemble minus candidate MSE gains were **0.002677,0.000216,0.000768**. Their mean **0.001221** did not exceed sample SD **0.001291**. Candidate-minus-ensemble Pearson changes were **−0.021678,−0.013604,−0.018442**; all breach−0.01, and mean **−0.017908 ± 0.004063** breaches−0.002. The error guardrails pass (MSE/additive1.000134,top-20/additive0.989530,top-20/ensemble0.994331), but cannot override failed primary/correlation gates. The candidate essentially matches additive MSE, with slightly higher mean error.

## Learned weights

| Outer seed | Fold0 | Fold1 | Fold2 | Fold3 | Fold4 |
|---|---:|---:|---:|---:|---:|
| 6 | 0.014195 | 0.155804 | 0.302361 | 0.031316 | 0.000000 |
| 7 | 0.599228 | 0.661471 | 0.252302 | 0.095125 | 0.312151 |
| 8 | 0.181866 | 0.242090 | 0.136539 | 0.088942 | 0.000000 |

Two zero weights make the candidate exactly additive in those folds. This does not explain the entire loss: seed7 has positive weights throughout and still loses correlation. The pooled MSE objective did not preserve the pattern signal under this recipe. Do not insert an epsilon weight, alter the objective, add groups or retune the margins after these outcomes.

## Metadata strata

| Group | Counts,seeds6/7/8 | Candidate − fixed Pearson delta | Candidate − fixed MSE |
|---|---:|---:|---:|
| external_all | 91/91/91 | -0.020649 ± 0.004884 | -0.001407 ± 0.001674 |
| external_none | 12/12/12 | -0.005603 ± 0.003096 | -0.000339 ± 0.000237 |
| external_partial | 9/9/9 | -0.006606 ± 0.002426 | -0.000509 ± 0.001202 |
| known_0 | 79/77/83 | -0.018722 ± 0.003075 | 0.000041 ± 0.000179 |
| known_1 | 33/35/29 | -0.015888 ± 0.006439 | -0.004322 ± 0.004661 |
| pair | 41/41/41 | -0.017593 ± 0.006430 | -0.003399 ± 0.003583 |
| pair_external_all | 31/31/31 | -0.021152 ± 0.007556 | -0.004359 ± 0.005034 |
| pair_external_none | 1/1/1 | -0.006149 ± 0.008118 | 0.000351 ± 0.000831 |
| pair_external_partial | 9/9/9 | -0.006606 ± 0.002426 | -0.000509 ± 0.001202 |
| pair_known_0 | 8/6/12 | -0.025347 ± 0.007249 | 0.000319 ± 0.001461 |
| pair_known_1 | 33/35/29 | -0.015888 ± 0.006439 | -0.004322 ± 0.004661 |
| singleton | 71/71/71 | -0.018090 ± 0.003119 | 0.000038 ± 0.000042 |
| singleton_external_all | 60/60/60 | -0.020388 ± 0.003737 | 0.000118 ± 0.000063 |
| singleton_external_none | 11/11/11 | -0.005553 ± 0.003984 | -0.000402 ± 0.000250 |
| singleton_known_0 | 71/71/71 | -0.018090 ± 0.003119 | 0.000038 ± 0.000042 |

All ten metrics for every arm/seed/stratum and all memberships are in the complete summary. Groups overlap and small/changing groups are descriptive, not selection rules or causal proof.

## Validation and preservation

Full490tests passed/no skips/8dependency warnings648.89s; focused8passed3.73s. Source/method review and stronger extra-hidden-row poisoning tests passed before source publication. Independent NumPy/stdlib review reproduced all15 weights/statistics/objectives,93 exact array checks,2400metric values,4179aggregate/gate values,45inner/15outer memberships,120events and source/package pins. Maximum metric discrepancy7.77e-16. Raw review passed; the model screen failed. This verifies saved arithmetic/provenance, not an independent fit replay. Chat2 independently verified2080global/stratum mean/sampleSD pairs (maxrounding2.22e-16), memberships/120ordered events/15weight formulas/gates, with no discrepancies. See the archived reviews/receipts.

Run directory: /Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-nested-blend/runs/b1_nested_blend_20261013. Numeric outer/inner arrays and package/context remain ignored locally. Config,summary,progress,source/input pins,exact command,reviews,verification and SHA256/MD5 lists are archived with this rejected research record. Existing runs were not overwritten.

## Continuation

Close this fixed scalar-calibration block without promotion or merging its unused code. No old-seed candidate scores,held-out/oracle/private/split reads,paid calls,protected/data/main/STOP/account changes occurred. Original B1 remains delivered; no historical-score drop or CellForge win is claimed.

Andres continues to request model improvement. A distinct next hypothesis may investigate r2’s original very weak ridge penalty and source behavior, using a newly published plan and matched nested development control. Do not treat its causality or success as established, reuse these predictions for new selection, reopen this objective or silently retune the old grid. Current HANDOFF carries the exact next owner/plan/state.
