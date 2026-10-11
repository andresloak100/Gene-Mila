# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 2 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ds_addstart_w4_r1:EXP_0007, norman_ds_addstart_w4_r1:EXP_0875); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code ce1b530.

## norman_ds_addstart_w4_r1: selected model against the additive baseline

Selected EXP_0875 (ridge, 10 features, visible 0.641); additive baseline EXP_0003 (visible 0.620). External knowledge: replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 5 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.727 | 0.713 | +0.015 ± 0.004 | 44/12 | selected better |
| sealed, pair_seen0 | 8 | 0.627 | 0.613 | +0.014 ± 0.005 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.852 | 0.835 | +0.016 ± 0.007 | 21/6 | selected better |
| sealed, pair_seen2 | 5 | 0.884 | 0.879 | +0.005 ± 0.002 | 4/1 | reported, not read |
| sealed, single | 16 | 0.519 | 0.504 | +0.015 ± 0.005 | 11/5 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.021 ± 0.005 | 127/48 | selected better |
| visible and out-of-fold, pair_seen0 | 21 | | | +0.017 ± 0.004 | 18/3 | selected better |
| visible and out-of-fold, pair_seen1 | 63 | | | +0.015 ± 0.009 | 49/14 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.009 ± 0.005 | 4/1 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.027 ± 0.008 | 56/30 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.720 against 0.711. No stored sealed score to check for EXP_0875 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 0.76 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.32; the arm reading inflates the sealed SE by the first when above 1.

## norman_ds_addstart_w4_r1: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.626); selected EXP_0875. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.727 | 0.716 | +0.011 ± 0.004 | 46/10 | selected better |
| sealed, pair_seen0 | 8 | 0.627 | 0.620 | +0.007 ± 0.002 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.852 | 0.834 | +0.017 ± 0.009 | 23/4 | no difference established |
| sealed, pair_seen2 | 5 | 0.884 | 0.890 | -0.006 ± 0.004 | 1/4 | reported, not read |
| sealed, single | 16 | 0.519 | 0.511 | +0.008 ± 0.003 | 14/2 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.015 ± 0.006 | 114/61 | selected better |
| visible and out-of-fold, pair_seen0 | 21 | | | +0.007 ± 0.003 | 15/6 | selected better |
| visible and out-of-fold, pair_seen1 | 63 | | | +0.018 ± 0.013 | 45/18 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00464 ± 0.00401 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.015 ± 0.006 | 51/35 | selected better |

Other sealed metrics, selected against start: pearson_delta without own targets 0.720 against 0.710. No stored sealed score to check for EXP_0875, EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 0.93 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.47; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ds_addstart_w4_r1, sealed pooled: selected minus additive +0.015 ± 0.004 paired SE, selected better on 44 and worse on 12 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.016 ± 0.007 paired SE, selected better on 21 and worse on 6 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive +0.015 ± 0.005 paired SE, selected better on 11 and worse on 5 of 16: selected better. norman_ds_addstart_w4_r1 against its starting model, sealed pooled: selected minus start +0.011 ± 0.004 paired SE, selected better on 46 and worse on 10 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.017 ± 0.009 paired SE, selected better on 23 and worse on 4 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.008 ± 0.003 paired SE, selected better on 14 and worse on 2 of 16: selected better. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
