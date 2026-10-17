# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_g0_ds_w4_r2:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code 2f2e683.

## norman_g0_ds_w4_r2: selected model against the additive baseline

Selected EXP_0787 (ridge, 18 features, visible 0.643); additive baseline EXP_0003 (visible 0.631). External knowledge: none. Code baa7dfd; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.713 | +0.007 ± 0.002 | 40/16 | selected better |
| sealed, pair_seen0 | 8 | 0.620 | 0.613 | +0.007 ± 0.002 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.839 | 0.835 | +0.00372 ± 0.00177 | 21/6 | selected better |
| sealed, pair_seen2 | 5 | 0.883 | 0.879 | +0.00395 ± 0.00361 | 3/2 | reported, not read |
| sealed, single | 16 | 0.516 | 0.504 | +0.012 ± 0.006 | 9/7 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.012 ± 0.003 | 113/62 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | +0.009 ± 0.004 | 10/1 | selected better |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.00428 ± 0.00099 | 49/24 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00013 ± 0.00098 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.020 ± 0.005 | 52/34 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.712 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.13 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.19; the arm reading inflates the sealed SE by the first when above 1.

## norman_g0_ds_w4_r2: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.636); selected EXP_0787. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.716 | +0.00311 ± 0.00184 | 27/29 | no difference established |
| sealed, pair_seen0 | 8 | 0.620 | 0.620 | +0.00049 ± 0.00162 | 4/4 | reported, not read |
| sealed, pair_seen1 | 27 | 0.839 | 0.834 | +0.00473 ± 0.00333 | 14/13 | no difference established |
| sealed, pair_seen2 | 5 | 0.883 | 0.890 | -0.008 ± 0.003 | 1/4 | reported, not read |
| sealed, single | 16 | 0.516 | 0.511 | +0.005 ± 0.003 | 8/8 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.007 ± 0.003 | 103/72 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | -0.00019 ± 0.00142 | 6/5 | no difference established |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.008 ± 0.005 | 45/28 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00409 ± 0.00090 | 0/5 | start better |
| visible and out-of-fold, single | 86 | | | +0.007 ± 0.003 | 52/34 | selected better |

Other sealed metrics, selected against start: pearson_delta without own targets 0.712 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.28 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.74; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_g0_ds_w4_r2, sealed pooled: selected minus additive +0.007 ± 0.002 paired SE, selected better on 40 and worse on 16 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.00372 ± 0.00177 paired SE, selected better on 21 and worse on 6 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive +0.012 ± 0.006 paired SE, selected better on 9 and worse on 7 of 16: no difference established. norman_g0_ds_w4_r2 against its starting model, sealed pooled: selected minus start +0.00311 ± 0.00184 paired SE, selected better on 27 and worse on 29 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00473 ± 0.00333 paired SE, selected better on 14 and worse on 13 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.005 ± 0.003 paired SE, selected better on 8 and worse on 8 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
