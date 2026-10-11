# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. Expected direction, fixed before any run: the run with the external screen above the one without, pooled and on singles. The tool made 6 sealed scorings on oracles of its own, outside the runs' caps; every compared model was already scored on the sealed set when its run ended. Wins are counted per perturbation; the visible rows pair the same models on the visible validation (and out-of-fold training) perturbations. Tool code 5fe6e76.

## norman_control_w4_r0: selected model against the additive baseline

Selected EXP_0076 (ridge, 5 features, visible 0.641); additive baseline EXP_0003 (visible 0.611). External knowledge: none. Code 02e7021; hash seed recorded: 0; the run's own sealed queries: 5 of 5.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.717 | 0.713 | +0.004 ± 0.008 | 28/28 | no difference established |
| sealed, pair_seen0 | 8 | 0.642 | 0.613 | +0.030 ± 0.019 | 5/3 | reported, not read |
| sealed, pair_seen1 | 27 | 0.847 | 0.835 | +0.012 ± 0.005 | 16/11 | selected better |
| sealed, pair_seen2 | 5 | 0.845 | 0.879 | -0.033 ± 0.022 | 1/4 | reported, not read |
| sealed, single | 16 | 0.495 | 0.504 | -0.009 ± 0.022 | 6/10 | no difference established |
| visible, pooled | 175 | | | +0.030 ± 0.009 | 109/66 | selected better |
| visible, pair_seen0 | 19 | | | +0.033 ± 0.010 | 15/4 | selected better |
| visible, pair_seen1 | 65 | | | +0.026 ± 0.011 | 45/20 | selected better |
| visible, pair_seen2 | 5 | | | -0.007 ± 0.008 | 2/3 | no difference established |
| visible, single | 86 | | | +0.034 ± 0.015 | 47/39 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.706 against 0.711.

## norman_control_replogle_w4_r0: selected model against the additive baseline

Selected EXP_0198 (ridge, 6 features, visible 0.642); additive baseline EXP_0003 (visible 0.611). External knowledge: replogle2022_k562. Code 02e7021; hash seed recorded: 0; the run's own sealed queries: 4 of 5.

| set | n | selected | additive | selected − additive (SE) | wins selected/additive | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.713 | +0.006 ± 0.007 | 32/24 | no difference established |
| sealed, pair_seen0 | 8 | 0.643 | 0.613 | +0.030 ± 0.017 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.847 | 0.835 | +0.012 ± 0.004 | 17/10 | selected better |
| sealed, pair_seen2 | 5 | 0.849 | 0.879 | -0.029 ± 0.019 | 2/3 | reported, not read |
| sealed, single | 16 | 0.499 | 0.504 | -0.005 ± 0.020 | 7/9 | no difference established |
| visible, pooled | 175 | | | +0.031 ± 0.008 | 114/61 | selected better |
| visible, pair_seen0 | 19 | | | +0.034 ± 0.010 | 15/4 | selected better |
| visible, pair_seen1 | 65 | | | +0.028 ± 0.011 | 45/20 | selected better |
| visible, pair_seen2 | 5 | | | -0.006 ± 0.007 | 2/3 | no difference established |
| visible, single | 86 | | | +0.036 ± 0.014 | 52/34 | selected better |

Other sealed metrics, selected against additive: pearson_delta without own targets 0.708 against 0.711.

## norman_control_replogle_w4_r0 (with replogle2022_k562) against norman_control_w4_r0 (without): selected models

With the screen: EXP_0198 (visible 0.642); without: EXP_0076 (visible 0.641); both on code 02e7021. Expected: the run with the external screen above the one without, pooled and on singles.

| set | n | with screen | without | with screen − without (SE) | wins with screen/without | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 56 | 0.719 | 0.717 | +0.002 ± 0.001 | 40/16 | with screen better |
| sealed, pair_seen0 | 8 | 0.643 | 0.642 | +0.001 ± 0.002 | 6/2 | reported, not read |
| sealed, pair_seen1 | 27 | 0.847 | 0.847 | +0.000 ± 0.000 | 18/9 | no difference established |
| sealed, pair_seen2 | 5 | 0.849 | 0.845 | +0.004 ± 0.003 | 4/1 | reported, not read |
| sealed, single | 16 | 0.499 | 0.495 | +0.004 ± 0.002 | 12/4 | no difference established |

Other sealed metrics, with screen against without: pearson_delta without own targets 0.708 against 0.706.

## Reading

norman_control_w4_r0, sealed pooled: selected minus additive +0.004 ± 0.008 paired SE, selected better on 28 and worse on 28 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.012 ± 0.005 paired SE, selected better on 16 and worse on 11 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.009 ± 0.022 paired SE, selected better on 6 and worse on 10 of 16: no difference established. norman_control_replogle_w4_r0, sealed pooled: selected minus additive +0.006 ± 0.007 paired SE, selected better on 32 and worse on 24 of 56: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 selected minus additive +0.012 ± 0.004 paired SE, selected better on 17 and worse on 10 of 27: selected better; pair_seen2 (n 5) reported, not read; single selected minus additive -0.005 ± 0.020 paired SE, selected better on 7 and worse on 9 of 16: no difference established. norman_control_replogle_w4_r0 against norman_control_w4_r0, sealed pooled: with screen minus without +0.002 ± 0.001 paired SE, with screen better on 40 and worse on 16 of 56: with screen better; on singles: with screen minus without +0.004 ± 0.002 paired SE, with screen better on 12 and worse on 4 of 16: no difference established; by category: pair_seen0 (n 8) reported, not read; pair_seen1 with screen minus without +0.000 ± 0.000 paired SE, with screen better on 18 and worse on 9 of 27: no difference established; pair_seen2 (n 5) reported, not read; single with screen minus without +0.004 ± 0.002 paired SE, with screen better on 12 and worse on 4 of 16: no difference established. Expected: the run with the external screen above the one without, pooled and on singles. Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
