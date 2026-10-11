# Arm reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The arm reading" and its amendment of 20:30 UTC). Each run's selected model against its starting model, metric pearson_delta per sealed perturbation, paired, from each run's own sealed reading (sha256 below). Rule: the arm's gain G (the mean of the runs' paired differences) counts when it exceeds k·SE, SE = sqrt(S² + sd_g²/R) with S the mean of the runs' paired standard errors (each inflated by its gene-clustering ratio when above 1) and sd_g the spread of their differences, k = max(2, t at 0.975 on Welch–Satterthwaite's degrees of freedom); every run's difference has G's sign; and summed over the runs the side G favours wins on more than half the perturbation-run pairs. Each run's SE is inflated by the overlap-robust clustering ratio (plan amendment of 2026-10-11 20:30 UTC) when above 1. A category is read when it holds at least 10 sealed perturbations in every run. The visible and out-of-fold rows are reported, not read. This reading scored nothing on the sealed set. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| run | code | selected | reference | n | difference (paired SE) | SE inflation | wins | per-run verdict |
|---|---|---|---|---|---|---|---|---|
| norman_ds_addstart_w4_r0 | ce1b530 | EXP_0724 | norman_ds_addstart_w4_r0:EXP_0007 | 56 | +0.0055 ± 0.0019 | 1.24 | 41/15 | selected better |
| norman_ds_addstart_w4_r2 | ce1b530 | EXP_0715 | norman_ds_addstart_w4_r2:EXP_0007 | 56 | +0.0039 ± 0.0022 | 1.23 | 33/23 | no difference established |

| set | G | S | sd_g | SE | k | k·SE | same sign | wins (selected/reference of pairs) | arm verdict |
|---|---|---|---|---|---|---|---|---|---|
| sealed, pooled | +0.0047 | 0.0025 | 0.0011 | 0.0027 | 2.02 | 0.0054 | yes | 74/38 of 112 | no difference established |
| sealed, pair_seen0 (n 8, 8) | | | | | | | | | reported, not read |
| sealed, pair_seen1 (n 27, 27) | +0.0065 | 0.0046 | 0.0012 | 0.0047 | 2.05 | 0.0096 | yes | 34/20 of 54 | no difference established |
| sealed, pair_seen2 (n 5, 5) | | | | | | | | | reported, not read |
| sealed, single (n 16, 16) | +0.0072 | 0.0025 | 0.0000 | 0.0025 | 2.13 | 0.0053 | yes | 26/6 of 32 | arm better |
| sealed, pooled, SE inflated by the jackknife ratio first specified | +0.0047 | 0.0035 | 0.0011 | 0.0036 | 2.01 | 0.0072 | yes | 74/38 of 112 | no difference established (reported, not read) |
| visible and out-of-fold, pooled (SE not inflated) | +0.0134 | 0.0036 | 0.0011 | 0.0037 | 2.00 | 0.0074 | yes | 229/121 of 350 | not read |
| visible and out-of-fold, pair_seen0 | +0.0174 | 0.0086 | 0.0189 | 0.0159 | 4.35 | 0.0691 | yes | 23/7 of 30 | not read |
| visible and out-of-fold, pair_seen1 | +0.0133 | 0.0062 | 0.0024 | 0.0065 | 2.00 | 0.0130 | yes | 88/50 of 138 | not read |
| visible and out-of-fold, pair_seen2 | -0.0024 | 0.0027 | 0.0000 | 0.0027 | 2.78 | 0.0074 | yes | 2/8 of 10 | not read |
| visible and out-of-fold, single | +0.0143 | 0.0052 | 0.0011 | 0.0053 | 2.00 | 0.0105 | yes | 116/56 of 172 | not read |

The arm's selected models on the sealed set (each run's own end-of-run scoring), mean ± sd over its runs:

| metric | mean | sd | runs |
|---|---|---|---|
| pearson_delta | 0.7208 | 0.0011 | 2 |
| MSE_DE | 0.1070 | 0.0010 | 2 |
| PCC_DE | 0.9377 | 0.0004 | 2 |
| R²_DE | 0.8438 | 0.0004 | 2 |

Readings:

- docs/results/norman_b2_r0_sealed_reading.json (sha256 2185aa188cb08775)
- docs/results/norman_b2_r2_sealed_reading.json (sha256 b1a3e1c2a547f5f3)

## Reading

Over 2 runs, the arm's selected models against its starting model: G +0.0047, SE 0.0027 (S 0.0025, sd_g 0.0011), k 2.02; no difference established.

Reported, not read (docs/PLAN_AFTER_N4.md, addendum of 23:00 UTC): the arm as first specified, seeds 0 and 2.
