# Combined model reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The combined model of an arm"). A: combined model of norman_ds_addstart_w4_r0:EXP_0724, norman_ds_addstart_w4_r2:EXP_0715, norman_ds_addstart_w4_r3:EXP_0625; B: norman_control_addstart_w4_r0:EXP_0157 (selected). Combination: the plain average of the members' predicted changes, equal weights. Metric pearson_delta per sealed perturbation, paired, A minus B; rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. One paired query (2 sealed scorings) on an oracle of the tool's own. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| side | run | role | experiment | model | features | visible | seed | code |
|---|---|---|---|---|---|---|---|---|
| A | norman_ds_addstart_w4_r0 | selected | EXP_0724 | ridge | 24 | 0.628 | 0 | ce1b530 |
| A | norman_ds_addstart_w4_r2 | selected | EXP_0715 | ridge | 16 | 0.651 | 2 | ce1b530 |
| A | norman_ds_addstart_w4_r3 | selected | EXP_0625 | ridge | 11 | 0.650 | 3 | ce1b530 |
| B | norman_control_addstart_w4_r0 | selected | EXP_0157 | ridge | 7 | 0.642 | 0 | ce1b530 |

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.727 | 0.719 | +0.008 ± 0.006 | 34/22 | no difference established |
| sealed, pair_seen0 | 8 | 0.631 | 0.643 | -0.012 ± 0.014 | 3/5 | reported, not read |
| sealed, pair_seen1 | 27 | 0.848 | 0.847 | +0.00134 ± 0.00406 | 17/10 | no difference established |
| sealed, pair_seen2 | 5 | 0.886 | 0.850 | +0.036 ± 0.019 | 4/1 | reported, not read |
| sealed, single | 16 | 0.520 | 0.499 | +0.021 ± 0.018 | 10/6 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.018 ± 0.008 | 106/69 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | -0.017 ± 0.013 | 4/4 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | -0.009 ± 0.012 | 14/21 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.010 ± 0.009 | 4/1 | not read |
| visible and out-of-fold, single | 15 | | | -0.074 ± 0.054 | 5/10 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.720 against 0.708.

The models drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

Pooled pearson_delta on the 63 visible validation perturbations alone (the score that chooses the delivered model, docs/PLAN_AFTER_N4.md): A 0.7505, B 0.7746.

## Reading

Sealed pooled: A minus B +0.008 ± 0.006 paired SE, A better on 34 and worse on 22 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B +0.00134 ± 0.00406 paired SE, A better on 17 and worse on 10 of 27: no difference established; pair_seen2 (n 5) reported, not read; single A minus B +0.021 ± 0.018 paired SE, A better on 10 and worse on 6 of 16: no difference established. The visible row is reported, not read.
