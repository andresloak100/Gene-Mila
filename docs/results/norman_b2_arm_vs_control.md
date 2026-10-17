# Arm reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The arm reading" and its amendment of 20:30 UTC). Each run's selected model against the other run of its --versus reading, metric pearson_delta per sealed perturbation, paired, from each run's own sealed reading (sha256 below). Rule: the arm's gain G (the mean of the runs' paired differences) counts when it exceeds k·SE, SE = sqrt(S² + sd_g²/R) with S the mean of the runs' paired standard errors (each inflated by its gene-clustering ratio when above 1) and sd_g the spread of their differences, k = max(2, t at 0.975 on Welch–Satterthwaite's degrees of freedom); every run's difference has G's sign; and summed over the runs the side G favours wins on more than half the perturbation-run pairs. Each run's SE is inflated by the overlap-robust clustering ratio (plan amendment of 2026-10-11 20:30 UTC) when above 1. A category is read when it holds at least 10 sealed perturbations in every run. The visible and out-of-fold rows are reported, not read. This reading scored nothing on the sealed set. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| run | code | selected | reference | n | difference (paired SE) | SE inflation | wins | per-run verdict |
|---|---|---|---|---|---|---|---|---|
| norman_ds_addstart_w4_r0 | ce1b530 | EXP_0724 | norman_control_addstart_w4_r0:EXP_0157 | 56 | +0.0028 ± 0.0064 | 1.47 | 27/29 | no difference established |
| norman_ds_addstart_w4_r2 | ce1b530 | EXP_0715 | norman_control_addstart_w4_r0:EXP_0157 | 56 | +0.0012 ± 0.0062 | 1.47 | 25/31 | no difference established |
| norman_ds_addstart_w4_r3 | ce1b530 | EXP_0625 | norman_control_addstart_w4_r0:EXP_0157 | 56 | +0.0113 ± 0.0085 | 1.00 | 34/22 | no difference established |

| set | G | S | sd_g | SE | k | k·SE | same sign | wins (selected/reference of pairs) | arm verdict |
|---|---|---|---|---|---|---|---|---|---|
| sealed, pooled | +0.0051 | 0.0090 | 0.0054 | 0.0095 | 2.01 | 0.0191 | yes | 86/82 of 168 | no difference established |
| sealed, pair_seen0 (n 8, 8, 8) | | | | | | | | | reported, not read |
| sealed, pair_seen1 (n 27, 27, 27) | -0.0025 | 0.0066 | 0.0070 | 0.0077 | 2.11 | 0.0162 | no | 34/47 of 81 | no difference established |
| sealed, pair_seen2 (n 5, 5, 5) | | | | | | | | | reported, not read |
| sealed, single (n 16, 16, 16) | +0.0184 | 0.0246 | 0.0005 | 0.0246 | 2.13 | 0.0524 | yes | 30/18 of 48 | no difference established |
| sealed, pooled, SE inflated by the jackknife ratio first specified | +0.0051 | 0.0099 | 0.0054 | 0.0104 | 2.01 | 0.0208 | yes | 86/82 of 168 | no difference established (reported, not read) |
| visible and out-of-fold, pooled (SE not inflated) | +0.0005 | 0.0088 | 0.0128 | 0.0115 | 2.19 | 0.0252 | no | 250/275 of 525 | not read |
| visible and out-of-fold, pair_seen0 | -0.0309 | 0.0197 | 0.0108 | 0.0207 | 2.30 | 0.0475 | yes | 9/26 of 35 | not read |
| visible and out-of-fold, pair_seen1 | -0.0122 | 0.0118 | 0.0176 | 0.0156 | 2.23 | 0.0347 | no | 59/76 of 135 | not read |
| visible and out-of-fold, pair_seen2 | -0.0001 | 0.0126 | 0.0133 | 0.0148 | 2.46 | 0.0364 | no | 9/6 of 15 | not read |
| visible and out-of-fold, single | -0.0358 | 0.0345 | 0.0585 | 0.0483 | 2.35 | 0.1134 | no | 52/64 of 116 | not read |

The arm's selected models on the sealed set (each run's own end-of-run scoring), mean ± sd over its runs:

| metric | mean | sd | runs |
|---|---|---|---|
| pearson_delta | 0.7239 | 0.0054 | 3 |
| MSE_DE | 0.1196 | 0.0217 | 3 |
| PCC_DE | 0.9314 | 0.0109 | 3 |
| R²_DE | 0.8283 | 0.0269 | 3 |

Readings:

- docs/results/norman_b2_r0_versus_control.json (sha256 0ef3b9fc0cb1eac5)
- docs/results/norman_b2_r2_versus_control.json (sha256 c3fd36a58f959bbf)
- docs/results/norman_b2_r3_versus_control.json (sha256 041a1be68fb45168)

## Reading

Over 3 runs, the arm's selected models against the other run of its --versus reading: G +0.0051, SE 0.0095 (S 0.0090, sd_g 0.0054), k 2.01; no difference established.
