# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ds_from_n2_w4_r3:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code d0fb635.

## norman_ds_from_n2_w4_r3: selected model against the additive baseline

Selected EXP_0519 (ridge, 21 features, visible 0.648); additive baseline EXP_0003 (visible 0.615). External knowledge: replogle2022_k562. Code 076282c; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.711 | 0.713 | -0.001 ± 0.012 | 31/25 | no difference established |
| sealed, pair_seen0 | 8 | 0.647 | 0.613 | +0.034 ± 0.018 | 5/3 | reported, not read |
| sealed, pair_seen1 | 27 | 0.846 | 0.835 | +0.011 ± 0.004 | 17/10 | selected better |
| sealed, pair_seen2 | 5 | 0.762 | 0.879 | -0.117 ± 0.105 | 2/3 | reported, not read |
| sealed, single | 16 | 0.500 | 0.504 | -0.004 ± 0.021 | 7/9 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.034 ± 0.009 | 113/62 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.036 ± 0.011 | 14/3 | selected better |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.029 ± 0.011 | 50/17 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.007 ± 0.006 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.039 ± 0.015 | 47/39 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.708 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.48 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.68; the arm reading inflates the sealed SE by the first when above 1.

## norman_ds_from_n2_w4_r3: selected model against its starting model

The run continued norman_control_replogle_w4_r0 (whose selected model EXP_0198 had alpha 6e-05); its starting model, re-fitted under this run's seed (alpha 6e-05), is EXP_0007 (6 features, visible 0.645); selected EXP_0519. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.711 | 0.719 | -0.008 ± 0.008 | 25/31 | no difference established |
| sealed, pair_seen0 | 8 | 0.647 | 0.643 | +0.00371 ± 0.00352 | 4/4 | reported, not read |
| sealed, pair_seen1 | 27 | 0.846 | 0.847 | -0.00081 ± 0.00118 | 12/15 | no difference established |
| sealed, pair_seen2 | 5 | 0.762 | 0.849 | -0.088 ± 0.088 | 2/3 | reported, not read |
| sealed, single | 16 | 0.500 | 0.499 | +0.00050 ± 0.00218 | 7/9 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.00322 ± 0.00121 | 94/81 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.00447 ± 0.00214 | 12/5 | selected better |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.00258 ± 0.00120 | 35/32 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00144 ± 0.00269 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.00375 ± 0.00224 | 45/41 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.708 against 0.708. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.55 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.84; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ds_from_n2_w4_r3, sealed pooled: selected minus additive -0.001 ± 0.012 paired SE, selected better on 31 and worse on 25 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.011 ± 0.004 paired SE, selected better on 17 and worse on 10 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.004 ± 0.021 paired SE, selected better on 7 and worse on 9 of 16: no difference established. norman_ds_from_n2_w4_r3 against its starting model, sealed pooled: selected minus start -0.008 ± 0.008 paired SE, selected better on 25 and worse on 31 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start -0.00081 ± 0.00118 paired SE, selected better on 12 and worse on 15 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.00050 ± 0.00218 paired SE, selected better on 7 and worse on 9 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
