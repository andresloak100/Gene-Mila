# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ds_from_n2_w4_r2:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code d0fb635.

## norman_ds_from_n2_w4_r2: selected model against the additive baseline

Selected EXP_0729 (ridge, 23 features, visible 0.669); additive baseline EXP_0003 (visible 0.631). External knowledge: replogle2022_k562. Code 076282c; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.726 | 0.713 | +0.013 ± 0.006 | 38/18 | selected better |
| sealed, pair_seen0 | 8 | 0.650 | 0.613 | +0.037 ± 0.017 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.851 | 0.835 | +0.016 ± 0.005 | 20/7 | selected better |
| sealed, pair_seen2 | 5 | 0.876 | 0.879 | -0.003 ± 0.013 | 3/2 | reported, not read |
| sealed, single | 16 | 0.506 | 0.504 | +0.002 ± 0.015 | 8/8 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.038 ± 0.008 | 120/55 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | +0.042 ± 0.012 | 9/2 | selected better |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.034 ± 0.008 | 56/17 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.001 ± 0.005 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.043 ± 0.015 | 52/34 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.717 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.34 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.50; the arm reading inflates the sealed SE by the first when above 1.

## norman_ds_from_n2_w4_r2: selected model against its starting model

The run continued norman_control_replogle_w4_r0 (whose selected model EXP_0198 had alpha 6e-05); its starting model, re-fitted under this run's seed (alpha 6e-05), is EXP_0007 (6 features, visible 0.665); selected EXP_0729. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.726 | 0.719 | +0.007 ± 0.003 | 36/20 | selected better |
| sealed, pair_seen0 | 8 | 0.650 | 0.643 | +0.007 ± 0.006 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.851 | 0.847 | +0.00410 ± 0.00344 | 15/12 | no difference established |
| sealed, pair_seen2 | 5 | 0.876 | 0.849 | +0.026 ± 0.010 | 5/0 | reported, not read |
| sealed, single | 16 | 0.506 | 0.499 | +0.006 ± 0.009 | 10/6 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.00398 ± 0.00269 | 100/75 | no difference established |
| visible and out-of-fold, pair_seen0 | 11 | | | +0.00297 ± 0.00492 | 6/5 | no difference established |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.006 ± 0.005 | 47/26 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.004 ± 0.005 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.00271 ± 0.00308 | 44/42 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.717 against 0.708. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 0.93 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.35; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ds_from_n2_w4_r2, sealed pooled: selected minus additive +0.013 ± 0.006 paired SE, selected better on 38 and worse on 18 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.016 ± 0.005 paired SE, selected better on 20 and worse on 7 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive +0.002 ± 0.015 paired SE, selected better on 8 and worse on 8 of 16: no difference established. norman_ds_from_n2_w4_r2 against its starting model, sealed pooled: selected minus start +0.007 ± 0.003 paired SE, selected better on 36 and worse on 20 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00410 ± 0.00344 paired SE, selected better on 15 and worse on 12 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.006 ± 0.009 paired SE, selected better on 10 and worse on 6 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
