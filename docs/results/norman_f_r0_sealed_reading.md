# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ga_ds_addstart_w4_r0:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code ce1b530.

## norman_ga_ds_addstart_w4_r0: selected model against the additive baseline

Selected EXP_0715 (ridge, 28 features, visible 0.628); additive baseline EXP_0003 (visible 0.611). External knowledge: gene_annotation, replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.713 | +0.008 ± 0.002 | 39/17 | selected better |
| sealed, pair_seen0 | 8 | 0.633 | 0.613 | +0.020 ± 0.004 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.836 | 0.835 | +0.00133 ± 0.00310 | 15/12 | no difference established |
| sealed, pair_seen2 | 5 | 0.883 | 0.879 | +0.00392 ± 0.00357 | 4/1 | reported, not read |
| sealed, single | 16 | 0.517 | 0.504 | +0.014 ± 0.005 | 12/4 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.017 ± 0.004 | 108/67 | selected better |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.019 ± 0.003 | 19/0 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.001 ± 0.005 | 30/35 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00059 ± 0.00334 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.029 ± 0.008 | 57/29 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.715 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.10 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.54; the arm reading inflates the sealed SE by the first when above 1.

## norman_ga_ds_addstart_w4_r0: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.615); selected EXP_0715. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.716 | +0.00430 ± 0.00161 | 38/18 | selected better |
| sealed, pair_seen0 | 8 | 0.633 | 0.620 | +0.014 ± 0.002 | 8/0 | reported, not read |
| sealed, pair_seen1 | 27 | 0.836 | 0.834 | +0.00234 ± 0.00195 | 18/9 | no difference established |
| sealed, pair_seen2 | 5 | 0.883 | 0.890 | -0.008 ± 0.003 | 0/5 | reported, not read |
| sealed, single | 16 | 0.517 | 0.511 | +0.007 ± 0.004 | 12/4 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.012 ± 0.003 | 116/59 | selected better |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.013 ± 0.003 | 17/2 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.006 ± 0.003 | 42/23 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00482 ± 0.00266 | 0/5 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.018 ± 0.006 | 57/29 | selected better |

Other sealed metrics, selected against start: pearson_delta without own targets 0.715 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.46 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.85; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ga_ds_addstart_w4_r0, sealed pooled: selected minus additive +0.008 ± 0.002 paired SE, selected better on 39 and worse on 17 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.00133 ± 0.00310 paired SE, selected better on 15 and worse on 12 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus additive +0.014 ± 0.005 paired SE, selected better on 12 and worse on 4 of 16: selected better. norman_ga_ds_addstart_w4_r0 against its starting model, sealed pooled: selected minus start +0.00430 ± 0.00161 paired SE, selected better on 38 and worse on 18 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00234 ± 0.00195 paired SE, selected better on 18 and worse on 9 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.007 ± 0.004 paired SE, selected better on 12 and worse on 4 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
