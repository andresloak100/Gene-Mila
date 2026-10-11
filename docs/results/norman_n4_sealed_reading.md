# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ds_from_n2_w4_r0:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code 076282c.

## norman_ds_from_n2_w4_r0: selected model against the additive baseline

Selected EXP_0790 (ridge, 11 features, visible 0.646); additive baseline EXP_0003 (visible 0.611). External knowledge: replogle2022_k562. Code 076282c; hash seed recorded: 0; the run's own sealed queries: 5 of 5.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.726 | 0.713 | +0.014 ± 0.008 | 37/19 | no difference established |
| sealed, pair_seen0 | 8 | 0.646 | 0.613 | +0.033 ± 0.020 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.856 | 0.835 | +0.021 ± 0.006 | 22/5 | selected better |
| sealed, pair_seen2 | 5 | 0.875 | 0.879 | -0.004 ± 0.019 | 2/3 | reported, not read |
| sealed, single | 16 | 0.502 | 0.504 | -0.002 ± 0.023 | 7/9 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.036 ± 0.010 | 113/62 | selected better |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.037 ± 0.011 | 15/4 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.033 ± 0.015 | 48/17 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.009 ± 0.007 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.039 ± 0.016 | 47/39 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.716 against 0.711.

## norman_ds_from_n2_w4_r0: selected model against its starting model

The run continued norman_control_replogle_w4_r0; its starting model EXP_0007 (6 features, visible 0.642), selected EXP_0790. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.726 | 0.719 | +0.008 ± 0.004 | 40/16 | no difference established |
| sealed, pair_seen0 | 8 | 0.646 | 0.643 | +0.00288 ± 0.00341 | 5/3 | reported, not read |
| sealed, pair_seen1 | 27 | 0.856 | 0.847 | +0.009 ± 0.007 | 21/6 | no difference established |
| sealed, pair_seen2 | 5 | 0.875 | 0.849 | +0.026 ± 0.007 | 5/0 | reported, not read |
| sealed, single | 16 | 0.502 | 0.499 | +0.00245 ± 0.00437 | 9/7 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.00419 ± 0.00278 | 93/82 | no difference established |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.00351 ± 0.00171 | 13/6 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.006 ± 0.007 | 38/27 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.015 ± 0.011 | 4/1 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.00254 ± 0.00268 | 38/48 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.716 against 0.708. No stored sealed score to check for EXP_0007 (scored on the sealed set here first).

## Reading

norman_ds_from_n2_w4_r0, sealed pooled: selected minus additive +0.014 ± 0.008 paired SE, selected better on 37 and worse on 19 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.021 ± 0.006 paired SE, selected better on 22 and worse on 5 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.002 ± 0.023 paired SE, selected better on 7 and worse on 9 of 16: no difference established. norman_ds_from_n2_w4_r0 against its starting model, sealed pooled: selected minus start +0.008 ± 0.004 paired SE, selected better on 40 and worse on 16 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.009 ± 0.007 paired SE, selected better on 21 and worse on 6 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.00245 ± 0.00437 paired SE, selected better on 9 and worse on 7 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
