# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ga_ds_addstart_w4_r3:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code ce1b530.

## norman_ga_ds_addstart_w4_r3: selected model against the additive baseline

Selected EXP_0603 (ridge, 24 features, visible 0.631); additive baseline EXP_0003 (visible 0.615). External knowledge: gene_annotation, replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.713 | +0.008 ± 0.002 | 37/19 | selected better |
| sealed, pair_seen0 | 8 | 0.622 | 0.613 | +0.009 ± 0.002 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.837 | 0.835 | +0.00162 ± 0.00085 | 18/9 | no difference established |
| sealed, pair_seen2 | 5 | 0.878 | 0.879 | -0.00100 ± 0.00249 | 1/4 | reported, not read |
| sealed, single | 16 | 0.523 | 0.504 | +0.019 ± 0.006 | 10/6 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.016 ± 0.003 | 113/62 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.009 ± 0.003 | 15/2 | selected better |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.00239 ± 0.00156 | 39/28 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00075 ± 0.00149 | 4/1 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.029 ± 0.007 | 55/31 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.714 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.19 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.28; the arm reading inflates the sealed SE by the first when above 1.

## norman_ga_ds_addstart_w4_r3: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.620); selected EXP_0603. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.716 | +0.00399 ± 0.00249 | 36/20 | no difference established |
| sealed, pair_seen0 | 8 | 0.622 | 0.620 | +0.00215 ± 0.00251 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.837 | 0.834 | +0.00263 ± 0.00430 | 17/10 | no difference established |
| sealed, pair_seen2 | 5 | 0.878 | 0.890 | -0.013 ± 0.003 | 0/5 | reported, not read |
| sealed, single | 16 | 0.523 | 0.511 | +0.012 ± 0.004 | 13/3 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.011 ± 0.004 | 100/75 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.00151 ± 0.00237 | 10/7 | no difference established |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.008 ± 0.007 | 37/30 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00348 ± 0.00235 | 1/4 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.016 ± 0.005 | 52/34 | selected better |

Other sealed metrics, selected against start: pearson_delta without own targets 0.714 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.22 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.69; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ga_ds_addstart_w4_r3, sealed pooled: selected minus additive +0.008 ± 0.002 paired SE, selected better on 37 and worse on 19 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.00162 ± 0.00085 paired SE, selected better on 18 and worse on 9 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus additive +0.019 ± 0.006 paired SE, selected better on 10 and worse on 6 of 16: selected better. norman_ga_ds_addstart_w4_r3 against its starting model, sealed pooled: selected minus start +0.00399 ± 0.00249 paired SE, selected better on 36 and worse on 20 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00263 ± 0.00430 paired SE, selected better on 17 and worse on 10 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.012 ± 0.004 paired SE, selected better on 13 and worse on 3 of 16: selected better. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
