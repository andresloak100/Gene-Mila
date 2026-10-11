# Noise ceiling of pearson_delta on adamson_cf

Visible data only: the 17 visible-validation perturbations' held-out cells and the 2000 public control cells (their mean is the lab's control_mean); the sealed set is never read. For each perturbation its cells are split at random into two halves 50 times (seed 0); r_half is the Pearson correlation across the 2055 genes between the two half-sample mean deltas from control_mean, averaged over the splits. Spearman-Brown gives the reliability of the recorded target's mean delta, r_full = k r_half / (1 + (k - 1) r_half) with k = 2 N / n_stored, where N is the number of cells the target averages (the stored cells themselves when their mean reproduces the target, else the count given with --ncells, here ../genemila_scale_logs/adamson_cf_ncells.json; unknown without it, in which case k = 2 and the ceiling is a lower bound). sqrt(r_full) is the correlation a perfect predictor of the true expected delta would reach against the recorded target: the ceiling of pearson_delta for that perturbation (clipped to [0, 1]). The ceiling of the averaged metric is the mean over perturbations. Perturbations with fewer than 4 cells are skipped.

## Per perturbation (visible validation set)

| perturbation | stored cells | target cells | r_half (mean ± sd over 50 splits) | r_full (Spearman-Brown) | ceiling |
|---|---|---|---|---|---|
| AARS | 300 | 447 | 0.945 ± 0.003 | 0.981 | 0.990 |
| ARHGAP22 | 300 | 490 | 0.695 ± 0.013 | 0.882 | 0.939 |
| ATP5B | 300 | 644 | 0.864 ± 0.007 | 0.965 | 0.982 |
| DARS | 300 | 664 | 0.831 ± 0.010 | 0.956 | 0.978 |
| DNAJC19 | 300 | 1525 | 0.915 ± 0.004 | 0.991 | 0.995 |
| EIF2B4 | 300 | 625 | 0.882 ± 0.006 | 0.969 | 0.984 |
| IDH3A | 300 | 663 | 0.608 ± 0.019 | 0.873 | 0.934 |
| MARS | 300 | 523 | 0.938 ± 0.004 | 0.981 | 0.991 |
| MRPL39 | 300 | 683 | 0.701 ± 0.016 | 0.914 | 0.956 |
| PSMD4 | 300 | 625 | 0.934 ± 0.004 | 0.983 | 0.992 |
| PTDSS1 | 300 | 534 | 0.195 ± 0.037 | 0.463 | 0.681 |
| SEC61B | 300 | 1668 | 0.607 ± 0.023 | 0.945 | 0.972 |
| SEC61G | 300 | 650 | 0.752 ± 0.015 | 0.929 | 0.964 |
| SOCS1 | 300 | 450 | 0.542 ± 0.028 | 0.781 | 0.883 |
| TIMM23 | 300 | 757 | 0.768 ± 0.013 | 0.944 | 0.971 |
| UFL1 | 300 | 585 | 0.500 ± 0.029 | 0.796 | 0.892 |
| XRN1 | 300 | 788 | 0.629 ± 0.023 | 0.899 | 0.948 |

## Overall

- Mean ceiling over the 17 visible-validation perturbations: **0.944** (the ceiling of the averaged metric); median 0.971; range 0.681 to 0.995.
- Mean r_half 0.724, mean r_full 0.897; 300 stored cells per perturbation on average.
- The stored cells are the whole population behind the recorded target mean for 0 of 17 perturbations; for the other 17 the recorded target averages more cells than were stored and its sampling noise is smaller. The Spearman-Brown step was carried to the cell count behind the target (--ncells) for 17 of them.

## Control-noise caveat

- Both halves subtract the same control_mean (the mean of 2000 public control cells), so its sampling noise is common to A and B and inflates r_half slightly, most for weak effects.
- Splitting the 300 held-out control cells the same way, the correlation between the two half control means' deviations from control_mean is 0.063 ± 0.032 (r_full 0.118, null ceiling 0.344): the r_half a perturbation with no effect would show from the shared control mean alone, plus any systematic difference between the held-out and the public control cells. r_half values near it are not evidence of a reproducible response.

## Achieved vs ceiling

The run's selected model re-scored on the visible validation set (pearson_delta per perturbation from its predictions at its chosen alpha, against the recorded target means) next to the ceiling. The gap is ceiling minus achieved; cells are the stored cells.

| run | arm | selected | mean achieved | headroom | r(achieved, ceiling) |
|---|---|---|---|---|---|
| newcode_derule_opus_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top) | EXP_0363, alpha 17000.0 | 0.609 | +0.335 | 0.488 |
| scale_w1_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0096, alpha 0.01 | 0.627 | +0.318 | 0.569 |
| scale_w1_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0110, alpha 100.0 | 0.619 | +0.326 | 0.595 |
| scale_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0197, alpha 100.0 | 0.628 | +0.316 | 0.641 |
| scale_w4_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0121, alpha 100.0 | 0.609 | +0.335 | 0.581 |
| scale_w8_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0316, alpha 0.01 | 0.636 | +0.308 | 0.575 |
| scale_w8_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0334, alpha 10.0 | 0.651 | +0.293 | 0.681 |
| scale_w16_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0780, alpha 100.0 | 0.648 | +0.297 | 0.615 |
| scale_w16_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0889, alpha 0.001 | 0.664 | +0.280 | 0.546 |
| newcode_opus_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0441, alpha 300.0 | 0.612 | +0.332 | 0.512 |
| newcode_opus_w4_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers | EXP_0393, alpha 8000.0 | 0.611 | +0.333 | 0.609 |
| newcode_ds_w4_r0 | deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers | EXP_0776, alpha 5600.0 | 0.563 | +0.382 | 0.640 |
| newcode_ds_w4_r1 | deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers | EXP_0725, alpha 30000.0 | 0.625 | +0.319 | 0.574 |
| control_components_from_opus_r0 | no-LLM continuation of newcode_opus_w4_r0 | EXP_0053, alpha 4590.0 | 0.613 | +0.331 | 0.509 |
| scale_control_r0 | scripted control (no LLM) | EXP_0010, alpha 0.01 | 0.571 | +0.373 | 0.667 |
| scale_control_r1 | scripted control (no LLM) | EXP_0010, alpha 0.01 | 0.571 | +0.373 | 0.667 |
| scale_control_r2 | scripted control (no LLM) | EXP_0010, alpha 0.01 | 0.571 | +0.373 | 0.667 |
| scale_control_r3 | scripted control (no LLM) | EXP_0010, alpha 0.01 | 0.571 | +0.373 | 0.667 |
| scale_control_r4 | scripted control (no LLM) | EXP_0010, alpha 0.01 | 0.571 | +0.373 | 0.667 |
| scale_control_r5 | scripted control (no LLM) | EXP_0010, alpha 0.01 | 0.571 | +0.373 | 0.667 |
| newcode2_control_r0 | scripted control (no LLM) | EXP_0041, alpha 41310.0 | 0.571 | +0.373 | 0.661 |
| newcode_control_r0 | scripted control (no LLM) | EXP_0028, alpha 41310.0 | 0.571 | +0.373 | 0.661 |
| newcode_control_r1 | scripted control (no LLM) | EXP_0028, alpha 72900.0 | 0.571 | +0.373 | 0.660 |
| newcode_control_r2 | scripted control (no LLM) | EXP_0028, alpha 41310.0 | 0.571 | +0.373 | 0.661 |
| newcode_control_r3 | scripted control (no LLM) | EXP_0028, alpha 72900.0 | 0.571 | +0.373 | 0.660 |
| newcode_control_r4 | scripted control (no LLM) | EXP_0028, alpha 72900.0 | 0.571 | +0.373 | 0.660 |
| newcode_control_r5 | scripted control (no LLM) | EXP_0028, alpha 72900.0 | 0.571 | +0.373 | 0.660 |
| control_components_w4_r0 | scripted control (no LLM) | EXP_0046, alpha 41310.0 | 0.587 | +0.358 | 0.648 |

### Per perturbation, for the run with the highest mean achieved: scale_w16_r1

Selected model EXP_0889 (best visible score among the experiments scored on the sealed set): ridge on control_mean, mean_response, symbol_family_response_e139, loo_sign_consensus_e175, target_knockdown_depth_e76, geneset_name_token_response_e200, ..., alpha 0.001; claude_cli:opus planner, deepseek:deepseek-flash workers, code 2492e11. Every run's per-perturbation values are in the JSON twin.

| perturbation | cells | ceiling | achieved | gap |
|---|---|---|---|---|
| AARS | 300 | 0.990 | 0.898 | +0.092 |
| ARHGAP22 | 300 | 0.939 | 0.689 | +0.250 |
| ATP5B | 300 | 0.982 | 0.734 | +0.248 |
| DARS | 300 | 0.978 | 0.746 | +0.232 |
| DNAJC19 | 300 | 0.995 | 0.943 | +0.053 |
| EIF2B4 | 300 | 0.984 | 0.901 | +0.084 |
| IDH3A | 300 | 0.934 | 0.634 | +0.300 |
| MARS | 300 | 0.991 | 0.652 | +0.339 |
| MRPL39 | 300 | 0.956 | 0.641 | +0.315 |
| PSMD4 | 300 | 0.992 | 0.408 | +0.583 |
| PTDSS1 | 300 | 0.681 | 0.277 | +0.403 |
| SEC61B | 300 | 0.972 | 0.679 | +0.293 |
| SEC61G | 300 | 0.964 | 0.864 | +0.100 |
| SOCS1 | 300 | 0.883 | 0.478 | +0.405 |
| TIMM23 | 300 | 0.971 | 0.836 | +0.135 |
| UFL1 | 300 | 0.892 | 0.733 | +0.159 |
| XRN1 | 300 | 0.948 | 0.181 | +0.767 |

## Reading

Under cell-sampling noise alone, pearson_delta on this visible validation set cannot exceed about 0.944 on average (median 0.971, range 0.681 to 0.995 across perturbations). For 17 perturbations the target averages more cells than were stored and the Spearman-Brown step was carried to that count. The 28 runs' selected models reach 0.563 to 0.664 on these perturbations, leaving +0.280 to +0.382 between them and the noise ceiling. That gap bounds what a predictor that knew each target's true response could add; a predictor limited to the information in the bundle (the other perturbations' responses and the knowledge files) is bounded by what that information says about a new target, which can lie well below. On the training perturbations, the best hindsight mix of the other perturbations' responses reaches 0.734 (non-negative weights) to 0.780 (any linear weights) (ceiling_analysis.json), so the part of the gap above that needs new information about the targets themselves, not better modelling of the same information. Where achieved tracks the ceiling across perturbations (a high correlation in the table), the perturbations the models miss are also the ones whose response is least reproducible. The ceiling is an estimate under cell-sampling noise alone: it treats the recorded target as the true expected response plus the noise of n cells, it is inflated slightly by the shared control mean (the null ceiling above says by how much a null perturbation would score), and it ignores day and batch effects, which lower what any predictor can reach but do not show in a within-sample split. It is an upper bound on the visible validation set, not a prediction for the sealed set.
