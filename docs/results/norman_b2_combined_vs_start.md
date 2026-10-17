# Combined model reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The combined model of an arm"). A: combined model of norman_ds_addstart_w4_r0:EXP_0724, norman_ds_addstart_w4_r2:EXP_0715, norman_ds_addstart_w4_r3:EXP_0625; B: norman_ds_addstart_w4_r0:EXP_0007 (start). Combination: the plain average of the members' predicted changes, equal weights. Metric pearson_delta per sealed perturbation, paired, A minus B; rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. One paired query (2 sealed scorings) on an oracle of the tool's own. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| side | run | role | experiment | model | features | visible | seed | code |
|---|---|---|---|---|---|---|---|---|
| A | norman_ds_addstart_w4_r0 | selected | EXP_0724 | ridge | 24 | 0.628 | 0 | ce1b530 |
| A | norman_ds_addstart_w4_r2 | selected | EXP_0715 | ridge | 16 | 0.651 | 2 | ce1b530 |
| A | norman_ds_addstart_w4_r3 | selected | EXP_0625 | ridge | 11 | 0.650 | 3 | ce1b530 |
| B | norman_ds_addstart_w4_r0 | start | EXP_0007 | ridge | 4 | 0.615 | 0 | ce1b530 |

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.727 | 0.716 | +0.011 ± 0.002 | 44/12 | A better |
| sealed, pair_seen0 | 8 | 0.631 | 0.620 | +0.011 ± 0.007 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.848 | 0.834 | +0.014 ± 0.004 | 23/4 | A better |
| sealed, pair_seen2 | 5 | 0.886 | 0.890 | -0.00464 ± 0.00276 | 2/3 | reported, not read |
| sealed, single | 16 | 0.520 | 0.511 | +0.009 ± 0.004 | 12/4 | A better |
| visible and out-of-fold, pooled | 175 | | | +0.045 ± 0.007 | 135/40 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | +0.016 ± 0.009 | 6/2 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | +0.026 ± 0.015 | 28/7 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00026 ± 0.00246 | 2/3 | not read |
| visible and out-of-fold, single | 15 | | | +0.034 ± 0.013 | 13/2 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.720 against 0.710.

The models drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

Pooled pearson_delta on the 63 visible validation perturbations alone (the score that chooses the delivered model, docs/PLAN_AFTER_N4.md): A 0.7505, B 0.7261.

## Reading

Sealed pooled: A minus B +0.011 ± 0.002 paired SE, A better on 44 and worse on 12 of 56: A better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B +0.014 ± 0.004 paired SE, A better on 23 and worse on 4 of 27: A better; pair_seen2 (n 5) reported, not read; single A minus B +0.009 ± 0.004 paired SE, A better on 12 and worse on 4 of 16: A better. The visible row is reported, not read.
