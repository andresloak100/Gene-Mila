# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_g0_ds_w4_r0:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code 2f2e683.

## norman_g0_ds_w4_r0: selected model against the additive baseline

Selected EXP_0697 (ridge, 28 features, visible 0.629); additive baseline EXP_0003 (visible 0.611). External knowledge: none. Code baa7dfd; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.721 | 0.713 | +0.008 ± 0.007 | 39/17 | no difference established |
| sealed, pair_seen0 | 8 | 0.619 | 0.613 | +0.006 ± 0.002 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.852 | 0.835 | +0.016 ± 0.011 | 21/6 | no difference established |
| sealed, pair_seen2 | 5 | 0.841 | 0.879 | -0.037 ± 0.044 | 2/3 | reported, not read |
| sealed, single | 16 | 0.513 | 0.504 | +0.009 ± 0.005 | 9/7 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.018 ± 0.006 | 114/61 | selected better |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.005 ± 0.001 | 17/2 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.029 ± 0.016 | 44/21 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.002 ± 0.006 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.013 ± 0.003 | 50/36 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.712 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 0.69 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.30; the arm reading inflates the sealed SE by the first when above 1.

## norman_g0_ds_w4_r0: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.615); selected EXP_0697. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.721 | 0.716 | +0.004 ± 0.008 | 39/17 | no difference established |
| sealed, pair_seen0 | 8 | 0.619 | 0.620 | -0.00115 ± 0.00074 | 3/5 | reported, not read |
| sealed, pair_seen1 | 27 | 0.852 | 0.834 | +0.017 ± 0.013 | 23/4 | no difference established |
| sealed, pair_seen2 | 5 | 0.841 | 0.890 | -0.049 ± 0.044 | 2/3 | reported, not read |
| sealed, single | 16 | 0.513 | 0.511 | +0.00192 ± 0.00090 | 11/5 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.014 ± 0.008 | 94/81 | no difference established |
| visible and out-of-fold, pair_seen0 | 19 | | | -0.00094 ± 0.00123 | 6/13 | no difference established |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.034 ± 0.020 | 40/25 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.002 ± 0.005 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.00224 ± 0.00158 | 46/40 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.712 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 0.85 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.41; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_g0_ds_w4_r0, sealed pooled: selected minus additive +0.008 ± 0.007 paired SE, selected better on 39 and worse on 17 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.016 ± 0.011 paired SE, selected better on 21 and worse on 6 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus additive +0.009 ± 0.005 paired SE, selected better on 9 and worse on 7 of 16: no difference established. norman_g0_ds_w4_r0 against its starting model, sealed pooled: selected minus start +0.004 ± 0.008 paired SE, selected better on 39 and worse on 17 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.017 ± 0.013 paired SE, selected better on 23 and worse on 4 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.00192 ± 0.00090 paired SE, selected better on 11 and worse on 5 of 16: selected better. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
