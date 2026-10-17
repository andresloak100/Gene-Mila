# Combined model reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The combined model of an arm"). A: combined model of norman_ds_addstart_w4_r0:EXP_0724, norman_ds_addstart_w4_r2:EXP_0715, norman_ds_addstart_w4_r3:EXP_0625; B: norman_ds_addstart_w4_r0:EXP_0003 (additive). Combination: the plain average of the members' predicted changes, equal weights. Metric pearson_delta per sealed perturbation, paired, A minus B; rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. One paired query (2 sealed scorings) on an oracle of the tool's own. Dataset norman, split split_a391fa9e7b4eccb7. Tool code ce1b530.

| side | run | role | experiment | model | features | visible | seed | code |
|---|---|---|---|---|---|---|---|---|
| A | norman_ds_addstart_w4_r0 | selected | EXP_0724 | ridge | 24 | 0.628 | 0 | ce1b530 |
| A | norman_ds_addstart_w4_r2 | selected | EXP_0715 | ridge | 16 | 0.651 | 2 | ce1b530 |
| A | norman_ds_addstart_w4_r3 | selected | EXP_0625 | ridge | 11 | 0.650 | 3 | ce1b530 |
| B | norman_ds_addstart_w4_r0 | additive | EXP_0003 | none | 0 | 0.611 | 0 | ce1b530 |

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.727 | 0.713 | +0.014 ± 0.003 | 45/11 | A better |
| sealed, pair_seen0 | 8 | 0.631 | 0.613 | +0.018 ± 0.006 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.848 | 0.835 | +0.013 ± 0.003 | 22/5 | A better |
| sealed, pair_seen2 | 5 | 0.886 | 0.879 | +0.007 ± 0.002 | 5/0 | reported, not read |
| sealed, single | 16 | 0.520 | 0.504 | +0.016 ± 0.006 | 11/5 | A better |
| visible and out-of-fold, pooled | 175 | | | +0.049 ± 0.007 | 144/31 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | +0.019 ± 0.010 | 6/2 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | +0.020 ± 0.006 | 33/2 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00397 ± 0.00383 | 3/2 | not read |
| visible and out-of-fold, single | 15 | | | +0.045 ± 0.015 | 14/1 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.720 against 0.711.

The models drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

Pooled pearson_delta on the 63 visible validation perturbations alone (the score that chooses the delivered model, docs/PLAN_AFTER_N4.md): A 0.7505, B 0.7259.

## Reading

Sealed pooled: A minus B +0.014 ± 0.003 paired SE, A better on 45 and worse on 11 of 56: A better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B +0.013 ± 0.003 paired SE, A better on 22 and worse on 5 of 27: A better; pair_seen2 (n 5) reported, not read; single A minus B +0.016 ± 0.006 paired SE, A better on 11 and worse on 5 of 16: A better. The visible row is reported, not read.
