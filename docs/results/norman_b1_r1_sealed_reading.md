# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 4 sealed scorings on oracles of its own, outside the runs' caps; 1 of the compared models had never been scored on the sealed set and are scored here for the first time (norman_ds_from_n2_w4_r1:EXP_0007); every other one was scored when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code 203a1bd.

## norman_ds_from_n2_w4_r1: selected model against the additive baseline

Selected EXP_0681 (ridge, 13 features, visible 0.654); additive baseline EXP_0003 (visible 0.620). External knowledge: replogle2022_k562. Code 076282c; hash seed recorded: 0; the run's own sealed queries: 4 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.713 | +0.007 ± 0.008 | 32/24 | no difference established |
| sealed, pair_seen0 | 8 | 0.647 | 0.613 | +0.034 ± 0.018 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.848 | 0.835 | +0.013 ± 0.005 | 17/10 | selected better |
| sealed, pair_seen2 | 5 | 0.848 | 0.879 | -0.031 ± 0.021 | 2/3 | reported, not read |
| sealed, single | 16 | 0.498 | 0.504 | -0.005 ± 0.022 | 7/9 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.035 ± 0.009 | 117/58 | selected better |
| visible and out-of-fold, pair_seen0 | 21 | | | +0.042 ± 0.010 | 19/2 | selected better |
| visible and out-of-fold, pair_seen1 | 63 | | | +0.027 ± 0.012 | 45/18 | selected better |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.008 ± 0.008 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.041 ± 0.015 | 51/35 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.708 against 0.711. Shared genes: on the visible validation perturbations the leave-one-gene-out jackknife SE is 1.67 times the plain paired SE (63 perturbations, 42 genes); the arm reading inflates the sealed SE by it when above 1.

## norman_ds_from_n2_w4_r1: selected model against its starting model

The run continued norman_control_replogle_w4_r0; its starting model is EXP_0007 (6 features, visible 0.652); selected EXP_0681. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.719 | +0.00038 ± 0.00106 | 27/29 | no difference established |
| sealed, pair_seen0 | 8 | 0.647 | 0.643 | +0.00365 ± 0.00119 | 7/1 | reported, not read |
| sealed, pair_seen1 | 27 | 0.848 | 0.847 | +0.00057 ± 0.00051 | 11/16 | no difference established |
| sealed, pair_seen2 | 5 | 0.848 | 0.849 | -0.00158 ± 0.00193 | 3/2 | reported, not read |
| sealed, single | 16 | 0.498 | 0.499 | -0.00097 ± 0.00351 | 6/10 | no difference established |
| visible and out-of-fold, pooled | 175 | | | +0.00187 ± 0.00101 | 94/81 | no difference established |
| visible and out-of-fold, pair_seen0 | 21 | | | +0.00387 ± 0.00078 | 20/1 | selected better |
| visible and out-of-fold, pair_seen1 | 63 | | | -0.00005 ± 0.00097 | 26/37 | no difference established |
| visible and out-of-fold, pair_seen2 | 5 | | | -0.00191 ± 0.00148 | 2/3 | no difference established |
| visible and out-of-fold, single | 86 | | | +0.00300 ± 0.00191 | 46/40 | no difference established |

Other sealed metrics, selected against start: pearson_delta without own targets 0.708 against 0.708. No stored sealed score to check for EXP_0007 (scored on the sealed set here first). Shared genes: on the visible validation perturbations the leave-one-gene-out jackknife SE is 1.51 times the plain paired SE (63 perturbations, 42 genes); the arm reading inflates the sealed SE by it when above 1.

## Reading

norman_ds_from_n2_w4_r1, sealed pooled: selected minus additive +0.007 ± 0.008 paired SE, selected better on 32 and worse on 24 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.013 ± 0.005 paired SE, selected better on 17 and worse on 10 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.005 ± 0.022 paired SE, selected better on 7 and worse on 9 of 16: no difference established. norman_ds_from_n2_w4_r1 against its starting model, sealed pooled: selected minus start +0.00038 ± 0.00106 paired SE, selected better on 27 and worse on 29 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus start +0.00057 ± 0.00051 paired SE, selected better on 11 and worse on 16 of 27: no difference established; pair_seen2 (n 5) reported, not read; single selected minus start -0.00097 ± 0.00351 paired SE, selected better on 6 and worse on 10 of 16: no difference established. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
