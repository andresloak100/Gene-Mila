# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 10 sealed scorings on oracles of its own, outside the runs' caps; 2 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_control_addstart_w4_r0:EXP_0007, norman_ds_addstart_w4_r2:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code ce1b530.

## norman_ds_addstart_w4_r2: selected model against the additive baseline

Selected EXP_0715 (ridge, 16 features, visible 0.651); additive baseline EXP_0003 (visible 0.631). External knowledge: replogle2022_k562. Code ce1b530; hash seed recorded: 0; the run's own sealed queries: 5 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.713 | +0.007 ± 0.002 | 38/18 | selected better |
| sealed, pair_seen0 | 8 | 0.625 | 0.613 | +0.012 ± 0.003 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.840 | 0.835 | +0.00464 ± 0.00184 | 17/10 | selected better |
| sealed, pair_seen2 | 5 | 0.872 | 0.879 | -0.007 ± 0.005 | 0/5 | reported, not read |
| sealed, single | 16 | 0.518 | 0.504 | +0.014 ± 0.004 | 14/2 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.019 ± 0.004 | 131/44 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | +0.040 ± 0.018 | 11/0 | selected better |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.008 ± 0.003 | 52/21 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.00185 ± 0.00270 | 3/2 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.027 ± 0.007 | 65/21 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.712 against 0.711. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.29 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.46; the arm reading inflates the sealed SE by the first when above 1.

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

## norman_ds_addstart_w4_r2: selected model against its starting model

The run started fresh; its starting model, the built-in additive start (ridge on the built-ins plus additive_response), is EXP_0007 (4 features, visible 0.636); selected EXP_0715. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.716 | +0.00386 ± 0.00218 | 33/23 | no difference established |
| sealed, pair_seen0 | 8 | 0.625 | 0.620 | +0.00500 ± 0.00187 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.840 | 0.834 | +0.006 ± 0.004 | 16/11 | no difference established |
| sealed, pair_seen2 | 5 | 0.872 | 0.890 | -0.018 ± 0.006 | 0/5 | reported, not read |
| sealed, single | 16 | 0.518 | 0.511 | +0.007 ± 0.002 | 11/5 | selected better |
| visible and out-of-fold, pooled | 175 | | | +0.014 ± 0.004 | 113/62 | selected better |
| visible and out-of-fold, pair_seen0 | 11 | | | +0.031 ± 0.016 | 9/2 | no difference established |
| visible and out-of-fold, pair_seen1 | 73 | | | +0.012 ± 0.007 | 46/27 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00237 ± 0.00313 | 1/4 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.015 ± 0.005 | 57/29 | selected better |

Other sealed metrics, selected against start: pearson_delta without own targets 0.712 against 0.710. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the overlap-robust SE is 1.23 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.71; the arm reading inflates the sealed SE by the first when above 1.

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

## norman_ds_addstart_w4_r2 (A) against norman_control_addstart_w4_r0 (B): selected models

A: EXP_0715 (visible 0.651); B: EXP_0157 (visible 0.642); external knowledge of both: replogle2022_k562; both on code ce1b530. No expected direction was fixed. The two runs drew different cross-validation folds, so the out-of-fold perturbations count in the visible row without their categories.

| set | n | A | B | A − B (SE) | wins A/B | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.720 | 0.719 | +0.001 ± 0.006 | 25/31 | no difference established |
| sealed, pair_seen0 | 8 | 0.625 | 0.643 | -0.018 ± 0.016 | 3/5 | reported, not read |
| sealed, pair_seen1 | 27 | 0.840 | 0.847 | -0.007 ± 0.003 | 8/19 | B better |
| sealed, pair_seen2 | 5 | 0.872 | 0.850 | +0.022 ± 0.015 | 3/2 | reported, not read |
| sealed, single | 16 | 0.518 | 0.499 | +0.019 ± 0.018 | 11/5 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.008 ± 0.010 | 88/87 | not read |
| visible and out-of-fold, pair_seen0 | 8 | | | -0.027 ± 0.022 | 3/5 | not read |
| visible and out-of-fold, pair_seen1 | 35 | | | -0.027 ± 0.017 | 11/24 | not read |
| visible and out-of-fold, pair_seen2 | 5 | | | +0.008 ± 0.005 | 3/2 | not read |
| visible and out-of-fold, single | 15 | | | -0.103 ± 0.067 | 4/11 | not read |

Other sealed metrics, A against B: pearson_delta without own targets 0.712 against 0.708. Shared genes: on the visible validation perturbations the overlap-robust SE is 1.47 times the plain paired SE (63 perturbations, 42 genes, 416 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.68; the arm reading inflates the sealed SE by the first when above 1.

## Reading

norman_ds_addstart_w4_r2, sealed pooled: selected minus additive +0.007 ± 0.002 paired SE, selected better on 38 and worse on 18 of 56: selected better; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.00464 ± 0.00184 paired SE, selected better on 17 and worse on 10 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive +0.014 ± 0.004 paired SE, selected better on 14 and worse on 2 of 16: selected better. norman_ds_addstart_w4_r2 against its starting model, sealed pooled: selected minus start +0.00386 ± 0.00218 paired SE, selected better on 33 and worse on 23 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.006 ± 0.004 paired SE, selected better on 16 and worse on 11 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start +0.007 ± 0.002 paired SE, selected better on 11 and worse on 5 of 16: selected better. norman_control_addstart_w4_r0, sealed pooled: selected minus additive +0.006 ± 0.007 paired SE, selected better on 32 and worse on 24 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.012 ± 0.004 paired SE, selected better on 17 and worse on 10 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.005 ± 0.020 paired SE, selected better on 7 and worse on 9 of 16: no difference established. norman_control_addstart_w4_r0 against its starting model, sealed pooled: selected minus start +0.003 ± 0.007 paired SE, selected better on 31 and worse on 25 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.013 ± 0.006 paired SE, selected better on 18 and worse on 9 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus start -0.011 ± 0.018 paired SE, selected better on 6 and worse on 10 of 16: no difference established. norman_ds_addstart_w4_r2 (A) against norman_control_addstart_w4_r0 (B), sealed pooled: A minus B +0.001 ± 0.006 paired SE, A better on 25 and worse on 31 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 A minus B -0.007 ± 0.003 paired SE, A better on 8 and worse on 19 of 27: B better; pair_seen2 (n 5) reported, not read; single A minus B +0.019 ± 0.018 paired SE, A better on 11 and worse on 5 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
