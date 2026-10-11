# Combined model reading

Pre-specified (docs/PLAN_AFTER_N4.md, "The combined model of an arm"). A: combined model of norman_ds_from_n2_w4_r1:EXP_0681, norman_ds_from_n2_w4_r2:EXP_0729, norman_ds_from_n2_w4_r3:EXP_0519; B: norman_control_replogle_w4_r0:EXP_0198 (selected). Combination: the plain average of the members' predicted changes, equal weights. Metric pearson_delta per sealed perturbation, paired, A minus B; rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. One paired query (2 sealed scorings) on an oracle of the tool's own. Dataset norman, split split_a391fa9e7b4eccb7. Tool code d0fb635.

| side | run | role | experiment | model | features | visible | seed | code |
|---|---|---|---|---|---|---|---|---|
| A | norman_ds_from_n2_w4_r1 | selected | EXP_0681 | ridge | 13 | 0.654 | 1 | 076282c |
| A | norman_ds_from_n2_w4_r2 | selected | EXP_0729 | ridge | 23 | 0.669 | 2 | 076282c |
| A | norman_ds_from_n2_w4_r3 | selected | EXP_0519 | ridge | 21 | 0.648 | 3 | 076282c |
| B | norman_control_replogle_w4_r0 | selected | EXP_0198 | ridge | 6 | 0.642 | 0 | 02e7021 |

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.723 | 0.719 | +0.00410 ± 0.00113 | 38/18 | A better |
| sealed, pair_seen0 | 8 | 0.649 | 0.643 | +0.006 ± 0.002 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.850 | 0.847 | +0.00305 ± 0.00144 | 15/12 | A better |
| sealed, pair_seen2 | 5 | 0.856 | 0.849 | +0.007 ± 0.002 | 5/0 | reported, not read |
| sealed, single | 16 | 0.504 | 0.499 | +0.00426 ± 0.00300 | 10/6 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.032 ± 0.007 | 116/59 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | +0.00492 ± 0.00279 | 6/2 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | +0.006 ± 0.003 | 23/12 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00182 ± 0.00252 | 3/2 | not read |
| visible and out-of-fold, single | 15 | | | +0.006 ± 0.007 | 7/8 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.713 against 0.708.

The models drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

Pooled pearson_delta on the 63 visible validation perturbations alone (the score that chooses the delivered model, docs/PLAN_AFTER_N4.md): A 0.7801, B 0.7746.

## Reading

Sealed pooled: A minus B +0.00410 ± 0.00113 paired SE, A better on 38 and worse on 18 of 56: A better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B +0.00305 ± 0.00144 paired SE, A better on 15 and worse on 12 of 27: A better; pair_seen2 (n 5) reported, not read; single A minus B +0.00426 ± 0.00300 paired SE, A better on 10 and worse on 6 of 16: no difference established. The visible row is reported, not read.
