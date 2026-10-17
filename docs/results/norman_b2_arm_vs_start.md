# Arm reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The arm reading" and its amendment of 20:30 UTC). Each run's selected model against its starting model, metric pearson_delta per sealed perturbation, paired, from each run's own sealed reading (sha256 below). Rule: the arm's gain G (the mean of the runs' paired differences) counts when it exceeds k·SE, SE = sqrt(S² + sd_g²/R) with S the mean of the runs' paired standard errors (each inflated by its gene-clustering ratio when above 1) and sd_g the spread of their differences, k = max(2, t at 0.975 on Welch–Satterthwaite's degrees of freedom); every run's difference has G's sign; and summed over the runs the side G favours wins on more than half the perturbation-run pairs. Each run's SE is inflated by the overlap-robust clustering ratio (plan amendment of 2026-10-11 20:30 UTC) when above 1. A category is read when it holds at least 10 sealed perturbations in every run. The visible and out-of-fold rows are reported, not read. This reading scored nothing on the sealed set. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| run | code | selected | reference | n | difference (paired SE) | SE inflation | wins | per-run verdict |
|---|---|---|---|---|---|---|---|---|
| norman_ds_addstart_w4_r0 | ce1b530 | EXP_0724 | norman_ds_addstart_w4_r0:EXP_0007 | 56 | +0.0055 ± 0.0019 | 1.24 | 41/15 | selected better |
| norman_ds_addstart_w4_r2 | ce1b530 | EXP_0715 | norman_ds_addstart_w4_r2:EXP_0007 | 56 | +0.0039 ± 0.0022 | 1.23 | 33/23 | no difference established |
| norman_ds_addstart_w4_r3 | ce1b530 | EXP_0625 | norman_ds_addstart_w4_r3:EXP_0007 | 56 | +0.0139 ± 0.0065 | 1.35 | 36/20 | selected better |

| set | G | S | sd_g | SE | k | k·SE | same sign | wins (selected/reference of pairs) | arm verdict |
|---|---|---|---|---|---|---|---|---|---|
| sealed, pooled | +0.0078 | 0.0046 | 0.0054 | 0.0056 | 2.11 | 0.0118 | yes | 110/58 of 168 | no difference established |
| sealed, pair_seen0 (n 8, 8, 8) | | | | | | | | | reported, not read |
| sealed, pair_seen1 (n 27, 27, 27) | +0.0105 | 0.0071 | 0.0070 | 0.0082 | 2.09 | 0.0171 | yes | 53/28 of 81 | no difference established |
| sealed, pair_seen2 (n 5, 5, 5) | | | | | | | | | reported, not read |
| sealed, single (n 16, 16, 16) | +0.0069 | 0.0069 | 0.0005 | 0.0069 | 2.13 | 0.0146 | yes | 34/14 of 48 | no difference established |
| sealed, pooled, SE inflated by the jackknife ratio first specified | +0.0078 | 0.0058 | 0.0054 | 0.0066 | 2.05 | 0.0136 | yes | 110/58 of 168 | no difference established (reported, not read) |
| visible and out-of-fold, pooled (SE not inflated) | +0.0189 | 0.0059 | 0.0096 | 0.0081 | 2.26 | 0.0183 | yes | 329/196 of 525 | not read |
| visible and out-of-fold, pair_seen0 | +0.0120 | 0.0129 | 0.0163 | 0.0160 | 2.24 | 0.0358 | yes | 31/16 of 47 | not read |
| visible and out-of-fold, pair_seen1 | +0.0233 | 0.0100 | 0.0174 | 0.0141 | 2.32 | 0.0328 | yes | 138/67 of 205 | not read |
| visible and out-of-fold, pair_seen2 | -0.0101 | 0.0086 | 0.0133 | 0.0115 | 2.48 | 0.0286 | yes | 4/11 of 15 | not read |
| visible and out-of-fold, single | +0.0190 | 0.0088 | 0.0082 | 0.0099 | 2.04 | 0.0203 | yes | 156/102 of 258 | not read |

The arm's selected models on the sealed set (each run's own end-of-run scoring), mean ± sd over its runs:

| metric | mean | sd | runs |
|---|---|---|---|
| pearson_delta | 0.7239 | 0.0054 | 3 |
| MSE_DE | 0.1196 | 0.0217 | 3 |
| PCC_DE | 0.9314 | 0.0109 | 3 |
| R²_DE | 0.8283 | 0.0269 | 3 |

Readings:

- docs/results/norman_b2_r0_sealed_reading.json (sha256 2185aa188cb08775)
- docs/results/norman_b2_r2_sealed_reading.json (sha256 b1a3e1c2a547f5f3)
- docs/results/norman_b2_r3_sealed_reading.json (sha256 e8a69032f93f7525)

## Reading

Over 3 runs, the arm's selected models against its starting model: G +0.0078, SE 0.0056 (S 0.0046, sd_g 0.0054), k 2.11; no difference established.
