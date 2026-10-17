# Arm reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The arm reading" and its amendment of 20:30 UTC). Each run's selected model against its starting model, metric pearson_delta per sealed perturbation, paired, from each run's own sealed reading (sha256 below). Rule: the arm's gain G (the mean of the runs' paired differences) counts when it exceeds k·SE, SE = sqrt(S² + sd_g²/R) with S the mean of the runs' paired standard errors (each inflated by its gene-clustering ratio when above 1) and sd_g the spread of their differences, k = max(2, t at 0.975 on Welch–Satterthwaite's degrees of freedom); every run's difference has G's sign; and summed over the runs the side G favours wins on more than half the perturbation-run pairs. Each run's SE is inflated by the overlap-robust clustering ratio (plan amendment of 2026-10-11 20:30 UTC) when above 1. A category is read when it holds at least 10 sealed perturbations in every run. The visible and out-of-fold rows are reported, not read. This reading scored nothing on the sealed set. Dataset norman, split split_a391fa9e7b4eccb7. Tool code d0fb635.

| run | code | selected | reference | n | difference (paired SE) | SE inflation | wins | per-run verdict | start alpha / continued run's alpha |
|---|---|---|---|---|---|---|---|---|---|
| norman_ds_from_n2_w4_r1 | 076282c | EXP_0681 | norman_ds_from_n2_w4_r1:EXP_0007 | 56 | +0.0004 ± 0.0011 | 1.35 | 27/29 | no difference established | 0 / 0 |
| norman_ds_from_n2_w4_r2 | 076282c | EXP_0729 | norman_ds_from_n2_w4_r2:EXP_0007 | 56 | +0.0071 ± 0.0033 | 1.00 | 36/20 | selected better | 0 / 0 |
| norman_ds_from_n2_w4_r3 | 076282c | EXP_0519 | norman_ds_from_n2_w4_r3:EXP_0007 | 56 | -0.0075 ± 0.0079 | 1.55 | 25/31 | no difference established | 0 / 0 |

| set | G | S | sd_g | SE | k | k·SE | same sign | wins (selected/reference of pairs) | arm verdict |
|---|---|---|---|---|---|---|---|---|---|
| sealed, pooled | -0.0000 | 0.0057 | 0.0073 | 0.0071 | 2.15 | 0.0152 | no | 88/80 of 168 | no difference established |
| sealed, pair_seen0 (n 8, 8, 8) | | | | | | | | | reported, not read |
| sealed, pair_seen1 (n 27, 27, 27) | +0.0013 | 0.0020 | 0.0025 | 0.0025 | 2.16 | 0.0053 | no | 38/43 of 81 | no difference established |
| sealed, pair_seen2 (n 5, 5, 5) | | | | | | | | | reported, not read |
| sealed, single (n 16, 16, 16) | +0.0019 | 0.0057 | 0.0038 | 0.0061 | 2.11 | 0.0128 | no | 23/25 of 48 | no difference established |
| sealed, pooled, SE inflated by the jackknife ratio first specified | -0.0000 | 0.0069 | 0.0073 | 0.0081 | 2.08 | 0.0168 | no | 88/80 of 168 | no difference established (reported, not read) |
| visible and out-of-fold, pooled (SE not inflated) | +0.0030 | 0.0016 | 0.0011 | 0.0018 | 2.00 | 0.0035 | yes | 288/237 of 525 | not read |
| visible and out-of-fold, pair_seen0 | +0.0038 | 0.0026 | 0.0008 | 0.0027 | 2.21 | 0.0059 | yes | 38/11 of 49 | not read |
| visible and out-of-fold, pair_seen1 | +0.0027 | 0.0025 | 0.0028 | 0.0030 | 2.09 | 0.0062 | no | 108/95 of 203 | not read |
| visible and out-of-fold, pair_seen2 | +0.0003 | 0.0031 | 0.0035 | 0.0037 | 2.45 | 0.0091 | no | 7/8 of 15 | not read |
| visible and out-of-fold, single | +0.0032 | 0.0024 | 0.0005 | 0.0024 | 2.00 | 0.0049 | yes | 135/123 of 258 | not read |

The arm's selected models on the sealed set (each run's own end-of-run scoring), mean ± sd over its runs:

| metric | mean | sd | runs |
|---|---|---|---|
| pearson_delta | 0.7188 | 0.0073 | 3 |
| MSE_DE | 0.1077 | 0.0068 | 3 |
| PCC_DE | 0.9387 | 0.0034 | 3 |
| R²_DE | 0.8465 | 0.0083 | 3 |

Readings:

- docs/results/norman_b1_r1_sealed_reading_amended.json (sha256 5b6d597a2ac5ceb1)
- docs/results/norman_b1_r2_sealed_reading.json (sha256 27b09dc420f17b25)
- docs/results/norman_b1_r3_sealed_reading.json (sha256 7524caaed635a011)

## Reading

Over 3 runs, the arm's selected models against its starting model: G -0.0000, SE 0.0071 (S 0.0057, sd_g 0.0073), k 2.15; no difference established.
