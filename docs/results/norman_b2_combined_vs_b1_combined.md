# Combined model reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The combined model of an arm"). A: combined model of norman_ds_addstart_w4_r0:EXP_0724, norman_ds_addstart_w4_r2:EXP_0715, norman_ds_addstart_w4_r3:EXP_0625; B: combined model of norman_ds_from_n2_w4_r1:EXP_0681, norman_ds_from_n2_w4_r2:EXP_0729, norman_ds_from_n2_w4_r3:EXP_0519. Combination: the plain average of the members' predicted changes, equal weights. Metric pearson_delta per sealed perturbation, paired, A minus B; rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. One paired query (2 sealed scorings) on an oracle of the tool's own. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| side | run | role | experiment | model | features | visible | seed | code |
|---|---|---|---|---|---|---|---|---|
| A | norman_ds_addstart_w4_r0 | selected | EXP_0724 | ridge | 24 | 0.628 | 0 | ce1b530 |
| A | norman_ds_addstart_w4_r2 | selected | EXP_0715 | ridge | 16 | 0.651 | 2 | ce1b530 |
| A | norman_ds_addstart_w4_r3 | selected | EXP_0625 | ridge | 11 | 0.650 | 3 | ce1b530 |
| B | norman_ds_from_n2_w4_r1 | selected | EXP_0681 | ridge | 13 | 0.654 | 1 | 076282c |
| B | norman_ds_from_n2_w4_r2 | selected | EXP_0729 | ridge | 23 | 0.669 | 2 | 076282c |
| B | norman_ds_from_n2_w4_r3 | selected | EXP_0519 | ridge | 21 | 0.648 | 3 | 076282c |

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.727 | 0.723 | +0.004 ± 0.006 | 32/24 | no difference established |
| sealed, pair_seen0 | 8 | 0.631 | 0.649 | -0.018 ± 0.014 | 3/5 | reported, not read |
| sealed, pair_seen1 | 27 | 0.848 | 0.850 | -0.00171 ± 0.00401 | 16/11 | no difference established |
| sealed, pair_seen2 | 5 | 0.886 | 0.856 | +0.030 ± 0.020 | 3/2 | reported, not read |
| sealed, single | 16 | 0.520 | 0.504 | +0.017 ± 0.017 | 10/6 | no difference established |
| visible and out-of-fold, pooled | 175 | | | -0.014 ± 0.007 | 83/92 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | -0.022 ± 0.011 | 3/5 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | -0.015 ± 0.010 | 11/24 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.008 ± 0.007 | 4/1 | not read |
| visible and out-of-fold, single | 15 | | | -0.081 ± 0.059 | 5/10 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.720 against 0.713.

The models drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

Pooled pearson_delta on the 63 visible validation perturbations alone (the score that chooses the delivered model, docs/PLAN_AFTER_N4.md): A 0.7505, B 0.7801.

## Reading

Sealed pooled: A minus B +0.004 ± 0.006 paired SE, A better on 32 and worse on 24 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B -0.00171 ± 0.00401 paired SE, A better on 16 and worse on 11 of 27: no difference established; pair_seen2 (n 5) reported, not read; single A minus B +0.017 ± 0.017 paired SE, A better on 10 and worse on 6 of 16: no difference established. The visible row is reported, not read.
