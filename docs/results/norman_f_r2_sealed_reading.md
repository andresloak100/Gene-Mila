# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ga_ds_addstart_w4_r2:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code ce1b530.

## norman_ga_ds_addstart_w4_r2: selected model against the additive baseline

Selected EXP_0260 (ridge, 11 features, visible 0.646); additive baseline EXP_0003 (visible 0.631). External knowledge: gene_annotation, replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.718 | 0.713 | +0.006 ± 0.002 | 33/23 | selected better |
| sealed, pair_seen0 | 8 | 0.620 | 0.613 | +0.007 ± 0.002 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.837 | 0.835 | +0.00178 ± 0.00163 | 13/14 | no difference established |
| sealed, pair_seen2 | 5 | 0.880 | 0.879 | +0.00115 ± 0.00170 | 3/2 | reported, not read |
| sealed, single | 16 | 0.517 | 0.504 | +0.013 ± 0.006 | 9/7 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.014 ± 0.003 | 113/62 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | +0.009 ± 0.003 | 10/1 | selected better |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.00468 ± 0.00196 | 45/28 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00162 ± 0.00204 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.024 ± 0.006 | 55/31 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.711 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.07 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.17; the arm reading inflates the sealed SE by the first when above 1.

## norman_ga_ds_addstart_w4_r2: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.636); selected EXP_0260. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.718 | 0.716 | +0.00207 ± 0.00179 | 30/26 | no difference established |
| sealed, pair_seen0 | 8 | 0.620 | 0.620 | -0.00002 ± 0.00106 | 4/4 | reported, not read |
| sealed, pair_seen1 | 27 | 0.837 | 0.834 | +0.00279 ± 0.00326 | 15/12 | no difference established |
| sealed, pair_seen2 | 5 | 0.880 | 0.890 | -0.011 ± 0.002 | 0/5 | reported, not read |
| sealed, single | 16 | 0.517 | 0.511 | +0.006 ± 0.002 | 11/5 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.009 ± 0.003 | 106/69 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | -0.00002 ± 0.00182 | 8/3 | no difference established |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.008 ± 0.005 | 41/32 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00261 ± 0.00306 | 1/4 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.012 ± 0.004 | 56/30 | selected better |

Other sealed metrics, selected against start: pearson_delta without own targets 0.711 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.16 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.63; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ga_ds_addstart_w4_r2, sealed pooled: selected minus additive +0.006 ± 0.002 paired SE, selected better on 33 and worse on 23 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.00178 ± 0.00163 paired SE, selected better on 13 and worse on 14 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus additive +0.013 ± 0.006 paired SE, selected better on 9 and worse on 7 of 16: selected better. norman_ga_ds_addstart_w4_r2 against its starting model, sealed pooled: selected minus start +0.00207 ± 0.00179 paired SE, selected better on 30 and worse on 26 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00279 ± 0.00326 paired SE, selected better on 15 and worse on 12 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.006 ± 0.002 paired SE, selected better on 11 and worse on 5 of 16: selected better. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
