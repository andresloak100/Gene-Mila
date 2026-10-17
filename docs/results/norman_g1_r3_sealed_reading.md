# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_g1_ds_w4_r3:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code 2f2e683.

## norman_g1_ds_w4_r3: selected model against the additive baseline

Selected EXP_0652 (ridge, 17 features, visible 0.627); additive baseline EXP_0003 (visible 0.615). External knowledge: none. Code baa7dfd; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.715 | 0.713 | +0.00213 ± 0.00286 | 28/28 | no difference established |
| sealed, pair_seen0 | 8 | 0.617 | 0.613 | +0.00457 ± 0.00205 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.836 | 0.835 | +0.00100 ± 0.00276 | 11/16 | no difference established |
| sealed, pair_seen2 | 5 | 0.862 | 0.879 | -0.016 ± 0.015 | 0/5 | reported, not read |
| sealed, single | 16 | 0.512 | 0.504 | +0.009 ± 0.007 | 11/5 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.013 ± 0.004 | 102/73 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.007 ± 0.003 | 13/4 | selected better |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.00135 ± 0.00157 | 36/31 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00166 ± 0.00061 | 0/5 | additive better |
| visible and out-of-fold, single | 86 | | | +0.023 ± 0.007 | 53/33 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.711 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.08 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.28; the arm reading inflates the sealed SE by the first when above 1.

## norman_g1_ds_w4_r3: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.620); selected EXP_0652. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.715 | 0.716 | -0.00140 ± 0.00252 | 28/28 | no difference established |
| sealed, pair_seen0 | 8 | 0.617 | 0.620 | -0.00230 ± 0.00155 | 3/5 | reported, not read |
| sealed, pair_seen1 | 27 | 0.836 | 0.834 | +0.00201 ± 0.00290 | 15/12 | no difference established |
| sealed, pair_seen2 | 5 | 0.862 | 0.890 | -0.028 ± 0.015 | 0/5 | reported, not read |
| sealed, single | 16 | 0.512 | 0.511 | +0.00158 ± 0.00446 | 10/6 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.008 ± 0.003 | 92/83 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | -0.00043 ± 0.00158 | 8/9 | no difference established |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.007 ± 0.005 | 41/26 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.006 ± 0.002 | 0/5 | start better |
| visible and out-of-fold, single | 86 | | | +0.010 ± 0.006 | 43/43 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.711 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.17 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.66; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_g1_ds_w4_r3, sealed pooled: selected minus additive +0.00213 ± 0.00286 paired SE, selected better on 28 and worse on 28 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.00100 ± 0.00276 paired SE, selected better on 11 and worse on 16 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus additive +0.009 ± 0.007 paired SE, selected better on 11 and worse on 5 of 16: no difference established. norman_g1_ds_w4_r3 against its starting model, sealed pooled: selected minus start -0.00140 ± 0.00252 paired SE, selected better on 28 and worse on 28 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00201 ± 0.00290 paired SE, selected better on 15 and worse on 12 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.00158 ± 0.00446 paired SE, selected better on 10 and worse on 6 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
