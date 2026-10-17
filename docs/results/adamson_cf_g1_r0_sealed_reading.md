# Sealed reading

Pre-specified (docs/NORMAN_PLAN.md section 5). Metric pearson_delta per sealed perturbation, paired. Reading rule, pooled and in every category: a gain counts when it exceeds twice its paired standard error and the better side wins on more than half the perturbations; a category with fewer than 10 sealed perturbations is reported, not read. The tool made 2 sealed scorings on oracles of its own, outside the runs' caps; every compared model was already scored on the sealed set when its run ended. Wins are counted per perturbation; the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, the training ones. Tool code 2f2e683.

## adamson_cf_g1_ds_w4_r0: selected model against the additive baseline

Selected EXP_0777 (ridge, 23 features, visible 0.512); additive baseline none. External knowledge: none. Code baa7dfd; hash seed recorded: 0; the run's own sealed queries: 5 of 5. Planner: deepseek:deepseek-v4-pro, unchanged.

no additive baseline in this run (a bundle without pairs records none)

## adamson_cf_g1_ds_w4_r0: selected model against its starting model

The run started fresh; its starting model, the starting model the run reports (its best baseline by visible score), is EXP_0003 (3 features, visible 0.501); selected EXP_0777. The difference is what the run's own search added.

| set | n | selected | start | selected − start (SE) | wins selected/start | verdict |
|---|---|---|---|---|---|---|
| sealed, pooled | 21 | 0.412 | 0.520 | -0.108 ± 0.063 | 11/10 | no difference established |
| visible and out-of-fold, pooled | 67 | | | +0.011 ± 0.005 | 39/28 | no difference established |

Shared genes: on the visible validation perturbations the overlap-robust SE is 1.00 times the plain paired SE (17 perturbations, 17 genes, 0 ordered pairs sharing a gene); the leave-one-gene-out jackknife first specified, which exceeds 1 even for independent pairs, gives 1.00; the arm reading inflates the sealed SE by the first when above 1.

## Reading

adamson_cf_g1_ds_w4_r0 against its starting model, sealed pooled: selected minus start -0.108 ± 0.063 paired SE, selected better on 11 and worse on 10 of 21: no difference established; by category: . Each verdict follows the rule as stated, pooled and in every category of at least 10 sealed perturbations; smaller categories are reported, not read.
