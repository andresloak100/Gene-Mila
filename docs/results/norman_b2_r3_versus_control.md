# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 10 sealed scorings on oracles of its own, outside the runs' caps; 2 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_control_addstart_w4_r0:EXP_0007, norman_ds_addstart_w4_r3:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code ce1b530.

## norman_ds_addstart_w4_r3: selected model against the additive baseline

Selected EXP_0625 (ridge, 11 features, visible 0.650); additive baseline EXP_0003 (visible 0.615). External knowledge: replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 5 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.730 | 0.713 | +0.017 ± 0.007 | 38/18 | selected better |
| sealed, pair_seen0 | 8 | 0.643 | 0.613 | +0.030 ± 0.024 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.853 | 0.835 | +0.018 ± 0.010 | 20/7 | no difference established |
| sealed, pair_seen2 | 5 | 0.890 | 0.879 | +0.011 ± 0.009 | 3/2 | reported, not read |
| sealed, single | 16 | 0.517 | 0.504 | +0.013 ± 0.014 | 8/8 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.035 ± 0.010 | 105/70 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.009 ± 0.022 | 9/8 | no difference established |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.037 ± 0.013 | 51/16 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.021 ± 0.022 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.041 ± 0.016 | 43/43 | no difference established |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.723 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.22 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.43; the arm reading inflates the sealed SE by the first when above 1.

## norman_control_addstart_w4_r0: selected model against the additive baseline

Selected EXP_0157 (ridge, 7 features, visible 0.642); additive baseline EXP_0003 (visible 0.611). External knowledge: replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: scripted:opus, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.713 | +0.006 ± 0.007 | 32/24 | no difference established |
| sealed, pair_seen0 | 8 | 0.643 | 0.613 | +0.030 ± 0.017 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.847 | 0.835 | +0.012 ± 0.004 | 17/10 | selected better |
| sealed, pair_seen2 | 5 | 0.850 | 0.879 | -0.029 ± 0.019 | 2/3 | reported, not read |
| sealed, single | 16 | 0.499 | 0.504 | -0.005 ± 0.020 | 7/9 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.031 ± 0.008 | 114/61 | selected better |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.034 ± 0.010 | 15/4 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.028 ± 0.011 | 45/20 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.006 ± 0.007 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.036 ± 0.014 | 52/34 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.708 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.48 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.68; the arm reading inflates the sealed SE by the first when above 1.

## norman_ds_addstart_w4_r3: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.620); selected EXP_0625. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.730 | 0.716 | +0.014 ± 0.007 | 36/20 | selected better |
| sealed, pair_seen0 | 8 | 0.643 | 0.620 | +0.023 ± 0.026 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.853 | 0.834 | +0.019 ± 0.009 | 19/8 | selected better |
| sealed, pair_seen2 | 5 | 0.890 | 0.890 | -0.001 ± 0.010 | 2/3 | reported, not read |
| sealed, single | 16 | 0.517 | 0.511 | +0.006 ± 0.012 | 8/8 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.030 ± 0.010 | 100/75 | selected better |
| visible and out-of-fold, pair_seen0 | 17 | | | +0.001 ± 0.021 | 8/9 | no difference established |
| visible and out-of-fold, pair_seen1 | 67 | | | +0.043 ± 0.017 | 50/17 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.025 ± 0.020 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.028 ± 0.016 | 40/46 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.723 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.35 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.61; the arm reading inflates the sealed SE by the first when above 1.

## norman_control_addstart_w4_r0: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.615); selected EXP_0157. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.716 | +0.003 ± 0.007 | 31/25 | no difference established |
| sealed, pair_seen0 | 8 | 0.643 | 0.620 | +0.023 ± 0.017 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.847 | 0.834 | +0.013 ± 0.006 | 18/9 | selected better |
| sealed, pair_seen2 | 5 | 0.850 | 0.890 | -0.041 ± 0.021 | 1/4 | reported, not read |
| sealed, single | 16 | 0.499 | 0.511 | -0.011 ± 0.018 | 6/10 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.027 ± 0.009 | 110/65 | selected better |
| visible and out-of-fold, pair_seen0 | 19 | | | +0.027 ± 0.009 | 15/4 | selected better |
| visible and out-of-fold, pair_seen1 | 65 | | | +0.032 ± 0.015 | 46/19 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.010 ± 0.008 | 1/4 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.025 ± 0.014 | 48/38 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.708 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.58 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.85; the arm reading inflates the sealed SE by the first when above 1.

## norman_ds_addstart_w4_r3 (A) against norman_control_addstart_w4_r0 (B): selected models

A: EXP_0625 (visible 0.650); B: EXP_0157 (visible 0.642); external knowledge of both: replogle2022_k562; both on code ce1b530. No expected direction was fixed. The two runs drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.730 | 0.719 | +0.011 ± 0.009 | 34/22 | no difference established |
| sealed, pair_seen0 | 8 | 0.643 | 0.643 | -0.001 ± 0.023 | 5/3 | reported, not read |
| sealed, pair_seen1 | 27 | 0.853 | 0.847 | +0.006 ± 0.011 | 16/11 | no difference established |
| sealed, pair_seen2 | 5 | 0.890 | 0.850 | +0.040 ± 0.014 | 5/0 | reported, not read |
| sealed, single | 16 | 0.517 | 0.499 | +0.018 ± 0.021 | 8/8 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.007 ± 0.008 | 85/90 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | -0.043 ± 0.028 | 1/7 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | +0.007 ± 0.007 | 21/14 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.015 ± 0.027 | 3/2 | not read |
| visible and out-of-fold, single | 15 | | | +0.006 ± 0.022 | 6/9 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.723 against 0.708. Shared genes: on the visible validation perturbations the overlap-robust SE is 0.54 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 0.98; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ds_addstart_w4_r3, sealed pooled: selected minus additive +0.017 ± 0.007 paired SE, selected better on 38 and worse on 18 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.018 ± 0.010 paired SE, selected better on 20 and worse on 7 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus additive +0.013 ± 0.014 paired SE, selected better on 8 and worse on 8 of 16: no difference established. norman_ds_addstart_w4_r3 against its starting model, sealed pooled: selected minus start +0.014 ± 0.007 paired SE, selected better on 36 and worse on 20 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.019 ± 0.009 paired SE, selected better on 19 and worse on 8 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus start +0.006 ± 0.012 paired SE, selected better on 8 and worse on 8 of 16: no difference established. norman_control_addstart_w4_r0, sealed pooled: selected minus additive +0.006 ± 0.007 paired SE, selected better on 32 and worse on 24 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.012 ± 0.004 paired SE, selected better on 17 and worse on 10 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.005 ± 0.020 paired SE, selected better on 7 and worse on 9 of 16: no difference established. norman_control_addstart_w4_r0 against its starting model, sealed pooled: selected minus start +0.003 ± 0.007 paired SE, selected better on 31 and worse on 25 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.013 ± 0.006 paired SE, selected better on 18 and worse on 9 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus start -0.011 ± 0.018 paired SE, selected better on 6 and worse on 10 of 16: no difference established. norman_ds_addstart_w4_r3 (A) against norman_control_addstart_w4_r0 (B), sealed pooled: A minus B +0.011 ± 0.009 paired SE, A better on 34 and worse on 22 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B +0.006 ± 0.011 paired SE, A better on 16 and worse on 11 of 27: no difference established; pair_seen2 (n 5) reported, not read; single A minus B +0.018 ± 0.021 paired SE, A better on 8 and worse on 8 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
