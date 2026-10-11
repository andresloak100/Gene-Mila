# Arm reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The arm reading" and its amendment of 20:30 UTC). Each run's selected model against its additive baseline, metric pearson_delta per sealed perturbation, paired, from each run's own sealed reading (sha256 below). Rule: the arm's gain G (the mean of the runs' paired differences) counts when it exceeds k·SE, SE = sqrt(S² + sd_g²/R) with S the mean of the runs' paired standard errors (each inflated by its gene-clustering ratio when above 1) and sd_g the spread of their differences, k = max(2, t at 0.975 on Welch–Satterthwaite's degrees of freedom); every run's difference has G's sign; and summed over the runs the side G favours wins on more than half the perturbation-run pairs. Each run's SE is inflated by the overlap-robust clustering ratio (plan amendment of 2026-10-11 20:30 UTC) when above 1. A category is read when it holds at least 10 sealed perturbations in every run. The visible and out-of-fold rows are reported, not read. This reading scored nothing on the sealed set. Dataset norman, split split_a391fa9e7b4eccb7. Tool code d0fb635.

| run | code | selected | reference | n | difference (paired SE) | SE inflation | wins | per-run verdict |
|---|---|---|---|---|---|---|---|---|
| norman_ds_from_n2_w4_r1 | 076282c | EXP_0681 | norman_ds_from_n2_w4_r1:EXP_0003 | 56 | +0.0066 ± 0.0076 | 1.47 | 32/24 | no difference established |
| norman_ds_from_n2_w4_r2 | 076282c | EXP_0729 | norman_ds_from_n2_w4_r2:EXP_0003 | 56 | +0.0133 ± 0.0056 | 1.34 | 38/18 | selected better |
| norman_ds_from_n2_w4_r3 | 076282c | EXP_0519 | norman_ds_from_n2_w4_r3:EXP_0003 | 56 | -0.0013 ± 0.0119 | 1.48 | 31/25 | no difference established |

| set | G | S | sd_g | SE | k | k·SE | same sign | wins (selected/reference of pairs) | arm verdict |
|---|---|---|---|---|---|---|---|---|---|
| sealed, pooled | +0.0062 | 0.0121 | 0.0073 | 0.0128 | 2.01 | 0.0257 | no | 101/67 of 168 | no difference established |
| sealed, pair_seen0 (n 8, 8, 8) | | | | | | | | | reported, not read |
| sealed, pair_seen1 (n 27, 27, 27) | +0.0133 | 0.0065 | 0.0025 | 0.0066 | 2.05 | 0.0136 | yes | 54/27 of 81 | no difference established |
| sealed, pair_seen2 (n 5, 5, 5) | | | | | | | | | reported, not read |
| sealed, single (n 16, 16, 16) | -0.0026 | 0.0277 | 0.0038 | 0.0278 | 2.13 | 0.0592 | no | 22/26 of 48 | no difference established |
| sealed, pooled, SE inflated by the jackknife ratio first specified | +0.0062 | 0.0137 | 0.0073 | 0.0144 | 2.01 | 0.0288 | no | 101/67 of 168 | no difference established (reported, not read) |
| visible and out-of-fold, pooled (SE not inflated) | +0.0354 | 0.0085 | 0.0023 | 0.0086 | 2.00 | 0.0172 | yes | 350/175 of 525 | not read |
| visible and out-of-fold, pair_seen0 | +0.0401 | 0.0112 | 0.0037 | 0.0114 | 2.21 | 0.0253 | yes | 42/7 of 49 | not read |
| visible and out-of-fold, pair_seen1 | +0.0301 | 0.0101 | 0.0039 | 0.0104 | 2.00 | 0.0207 | yes | 151/52 of 203 | not read |
| visible and out-of-fold, pair_seen2 | -0.0055 | 0.0064 | 0.0035 | 0.0067 | 2.61 | 0.0176 | yes | 7/8 of 15 | not read |
| visible and out-of-fold, single | +0.0408 | 0.0152 | 0.0019 | 0.0153 | 2.00 | 0.0306 | yes | 150/108 of 258 | not read |

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

Over 3 runs, the arm's selected models against its additive baseline: G +0.0062, SE 0.0128 (S 0.0121, sd_g 0.0073), k 2.01; no difference established.
