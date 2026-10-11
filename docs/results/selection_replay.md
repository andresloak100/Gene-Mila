# Selection-rule replay on visible data

Offline and free, and the sealed (query-only) labels are never read: comparing rules by their sealed outcome would tune the rule on the test set. Each run that cross-validated has two disjoint visible parts, the visible validation set and the out-of-fold predictions of the training perturbations; a rule picks the run's best experiment on one part and the pick is scored on the other, both ways. Scores on the validation part include CellForge's top-20 DE metrics (its DE reference exists there); the out-of-fold part has pearson_delta, R² and MSE on each perturbation's 20 most changed genes. Only the chosen alpha of each experiment survives on disk, so a rule is replayed across experiments, not inside one alpha grid. Runs without out-of-fold predictions are skipped.

## newcode_opus_w4_r0: claude_cli:opus planner, deepseek:deepseek-flash workers, 4 workers, code 537344f

411 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0339 | ridge on is_target, is_target_x_control_mean_e35, knn_response_symbol_family_e58, knn_residual_response_e59, knn_response_geneset_e12, normalized_mean_response_e56, … | 0.5839 | 0.5921 | 0.8502 | 0.1109 | 0.0993 | 0.9628 | 0.8708 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0339 | ridge on is_target, is_target_x_control_mean_e35, knn_response_symbol_family_e58, knn_residual_response_e59, knn_response_geneset_e12, normalized_mean_response_e56, … | 0.7093 | 0.5921 | 0.8502 | 0.1109 | 0.0993 | 0.9628 | 0.8708 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0081 | ridge on is_target, knn_response_geneset_e11, shared_geneset_score_e15, is_target_x_control_mean_e35, knn_response_symbol_family_e58, knn_residual_response_e59, … | 0.6169 | 0.5603 | 0.8208 | 0.1097 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0390 | ridge on is_target, is_target_x_control_mean_e35, knn_response_symbol_family_e58, knn_residual_response_e59, knn_response_geneset_e12, normalized_mean_response_e56, … | 0.7455 | 0.5735 | 0.8364 | 0.1006 | – | – | – |

## newcode_opus_w4_r1: claude_cli:opus planner, deepseek:deepseek-flash workers, 4 workers, code 537344f

351 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0380 | ridge on mean_response, is_target, target_knockdown_scaled_e18, geneset_knn_response_e14, ppi_kernel_weighted_response_e40, symbol_family_knn_response_e70, … | 0.5784 | 0.6036 | 0.8479 | 0.1098 | 0.0985 | 0.9622 | 0.8694 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0295 | ridge on control_mean, mean_response, is_target, target_knockdown_scaled_e18, geneset_knn_response_e14, ppi_kernel_weighted_response_e40, … | 0.7052 | 0.6058 | 0.8632 | 0.1015 | 0.0893 | 0.9669 | 0.8840 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0060 | ridge on control_mean, mean_response, is_target, target_knockdown_scaled_e18, geneset_knn_response_e14, ppi_kernel_weighted_response_e40, … | 0.6266 | 0.5450 | 0.8239 | 0.1025 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0056 | ridge on control_mean, mean_response, is_target, target_knockdown_scaled_e18, geneset_knn_response_e14, learned_metric_knn_response_e56 | 0.7427 | 0.5275 | 0.8075 | 0.1094 | – | – | – |

## newcode_ds_w4_r0: deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers, 4 workers, code 537344f

672 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0800 | ridge on mean_response, is_target, ppi_adjacency_e9, target_mean_abs_response_e61_e69, log_target_mean_abs_response_e105, shared_pathway_mean_abs_response_e123, … | 0.4927 | 0.5624 | 0.8028 | 0.1440 | 0.1302 | 0.9501 | 0.8240 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0079 | ridge on mean_response, is_target, ppi_adjacency_e9, target_expression_variance_e37, target_mean_expression_all_e56, target_mean_abs_response_e61_e69, … | 0.6318 | 0.5572 | 0.8176 | 0.1280 | 0.1166 | 0.9498 | 0.8319 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0722 | ridge on mean_response, is_target, ppi_adjacency_e9, target_mean_abs_response_e61_e69, log_target_mean_abs_response_e105, shared_pathway_mean_abs_response_e123, … | 0.5684 | 0.4891 | 0.7676 | 0.1375 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0380 | ridge on mean_response, is_target, ppi_adjacency_e9, target_mean_abs_response_e61_e69, log_target_mean_abs_response_e105, shared_pathway_mean_abs_response_e123, … | 0.6928 | 0.4713 | 0.7731 | 0.1336 | – | – | – |

## newcode_ds_w4_r1: deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers, 4 workers, code 537344f

559 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0667 | ridge on is_target, knn_perturbation_response_target_pathway_e125, prior_network_random_walk_influence_e79, knn_perturbation_response_sequence_weigh_e451, target_expression_stability_ratio_e438, target_ppi_neighbor_expression_variance_e481, … | 0.5740 | 0.6150 | 0.8691 | 0.0949 | 0.0874 | 0.9640 | 0.8813 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0506 | ridge on is_target, knn_perturbation_response_ppi_weighted_e54, knn_perturbation_response_target_pathway_e125, prior_network_random_walk_influence_e79, knn_perturbation_response_sequence_weigh_e451, target_expression_stability_ratio_e438, … | 0.7084 | 0.6267 | 0.8725 | 0.0963 | 0.0884 | 0.9658 | 0.8826 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0519 | ridge on is_target, knn_perturbation_response_ppi_weighted_e54, knn_perturbation_response_target_pathway_e125, prior_network_random_walk_influence_e79, knn_perturbation_response_sequence_weigh_e451, target_expression_stability_ratio_e438, … | 0.6281 | 0.5602 | 0.8300 | 0.1001 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0497 | ridge on is_target, knn_perturbation_response_ppi_weighted_e54, knn_perturbation_response_target_pathway_e125, prior_network_random_walk_influence_e79, knn_perturbation_response_sequence_weigh_e451, target_expression_stability_ratio_e438, … | 0.7542 | 0.5649 | 0.8376 | 0.0941 | – | – | – |

## newcode_control_r0: scripted control (no LLM), 4 workers, code 72a53c5

22 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0028 | ridge on mean_response, is_target, target_level_e11 | 0.4862 | 0.5714 | 0.7970 | 0.1426 | 0.1296 | 0.9494 | 0.8173 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0017 | ridge on control_mean, mean_response, is_target, target_level_e11 | 0.6291 | 0.5710 | 0.8231 | 0.1274 | 0.1154 | 0.9565 | 0.8410 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0018 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4856 | 0.7724 | 0.1356 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4856 | 0.7725 | 0.1355 | – | – | – |

## newcode_control_r1: scripted control (no LLM), 4 workers, code 72a53c5

23 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0028 | ridge on mean_response, is_target, target_level_e11 | 0.4891 | 0.5713 | 0.7831 | 0.1509 | 0.1372 | 0.9456 | 0.8048 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0010 | ridge on control_mean, mean_response, is_target, similar_pert_knn_e10 | 0.6349 | 0.5152 | 0.8237 | 0.1307 | 0.1205 | 0.9466 | 0.8321 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0019 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4885 | 0.7763 | 0.1322 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4885 | 0.7764 | 0.1322 | – | – | – |

## newcode_control_r2: scripted control (no LLM), 4 workers, code 72a53c5

23 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0028 | ridge on mean_response, is_target, target_level_e11 | 0.4868 | 0.5714 | 0.7970 | 0.1426 | 0.1296 | 0.9494 | 0.8173 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0017 | ridge on control_mean, mean_response, is_target, target_level_e11 | 0.6297 | 0.5710 | 0.8231 | 0.1274 | 0.1154 | 0.9565 | 0.8410 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0019 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4861 | 0.7732 | 0.1344 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4861 | 0.7732 | 0.1343 | – | – | – |

## newcode_control_r3: scripted control (no LLM), 4 workers, code 72a53c5

23 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0028 | ridge on mean_response, is_target, target_level_e11 | 0.4884 | 0.5713 | 0.7831 | 0.1509 | 0.1372 | 0.9456 | 0.8048 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0017 | ridge on control_mean, mean_response, is_target, target_level_e11 | 0.6318 | 0.5710 | 0.8231 | 0.1274 | 0.1154 | 0.9565 | 0.8410 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0019 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4875 | 0.7759 | 0.1325 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4875 | 0.7759 | 0.1325 | – | – | – |

## newcode_control_r4: scripted control (no LLM), 4 workers, code 72a53c5

23 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0028 | ridge on mean_response, is_target, target_level_e11 | 0.4897 | 0.5713 | 0.7831 | 0.1509 | 0.1372 | 0.9456 | 0.8048 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0017 | ridge on control_mean, mean_response, is_target, target_level_e11 | 0.6333 | 0.5710 | 0.8231 | 0.1274 | 0.1154 | 0.9565 | 0.8410 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0019 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4890 | 0.7774 | 0.1315 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4890 | 0.7774 | 0.1315 | – | – | – |

## newcode_control_r5: scripted control (no LLM), 4 workers, code 72a53c5

23 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0028 | ridge on mean_response, is_target, target_level_e11 | 0.4914 | 0.5713 | 0.7831 | 0.1509 | 0.1372 | 0.9456 | 0.8048 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0017 | ridge on control_mean, mean_response, is_target, target_level_e11 | 0.6351 | 0.5710 | 0.8231 | 0.1274 | 0.1154 | 0.9565 | 0.8410 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0019 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4907 | 0.7793 | 0.1308 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4907 | 0.7794 | 0.1308 | – | – | – |

## newcode2_control_r0: scripted control (no LLM), 4 workers, code 537344f

126 candidate experiments (17 validation and 50 out-of-fold training perturbations); the run itself selected by pearson_delta on both parts together.

| direction | rule | picked | model | selection score | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|---|---|---|
| select on out-of-fold training, score on validation | pearson_delta | EXP_0041 | ridge on mean_response, is_target, target_level_e11 | 0.4862 | 0.5714 | 0.7970 | 0.1426 | 0.1296 | 0.9494 | 0.8173 |
| select on out-of-fold training, score on validation | pearson_delta+r2_top | EXP_0017 | ridge on control_mean, mean_response, is_target, target_level_e11 | 0.6291 | 0.5710 | 0.8231 | 0.1274 | 0.1154 | 0.9565 | 0.8410 |
| select on validation, score on out-of-fold training | pearson_delta | EXP_0018 | ridge on mean_response, is_target, target_level_e11 | 0.5717 | 0.4856 | 0.7724 | 0.1356 | – | – | – |
| select on validation, score on out-of-fold training | pearson_delta+r2_top | EXP_0022 | lasso on mean_response, is_target, target_level_e11 | 0.6973 | 0.4856 | 0.7725 | 0.1355 | – | – | – |

## Across the 11 usable runs

**select on out-of-fold training, score on validation**

| rule | pick differs from pearson_delta in | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|
| pearson_delta | 0 of 11 runs | 0.5793 ± 0.0166 | 0.8085 ± 0.0316 | 0.1356 ± 0.0202 | 0.1230 ± 0.0185 | 0.9518 ± 0.0074 | 0.8288 ± 0.0298 |
| pearson_delta+r2_top | 10 of 11 runs | 0.5748 ± 0.0281 | 0.8333 ± 0.0192 | 0.1211 ± 0.0122 | 0.1097 ± 0.0116 | 0.9573 ± 0.0061 | 0.8498 ± 0.0195 |

- pearson_delta+r2_top minus pearson_delta, pearson_delta: -0.0045 ± 0.0176 over 11 runs; better in 2 of 11.
- pearson_delta+r2_top minus pearson_delta, R²_top: +0.0248 ± 0.0149 over 11 runs; better in 10 of 11.
- pearson_delta+r2_top minus pearson_delta, MSE_top: -0.0145 ± 0.0088 over 11 runs; better in 9 of 11.
- pearson_delta+r2_top minus pearson_delta, MSE_DE: -0.0133 ± 0.0079 over 11 runs; better in 9 of 11.
- pearson_delta+r2_top minus pearson_delta, PCC_DE: +0.0056 ± 0.0044 over 11 runs; better in 9 of 11.
- pearson_delta+r2_top minus pearson_delta, R²_DE: +0.0210 ± 0.0134 over 11 runs; better in 10 of 11.

**select on validation, score on out-of-fold training**

| rule | pick differs from pearson_delta in | pearson_delta | R²_top | MSE_top | MSE_DE | PCC_DE | R²_DE |
|---|---|---|---|---|---|---|---|
| pearson_delta | 0 of 11 runs | 0.5061 ± 0.0318 | 0.7881 ± 0.0239 | 0.1257 ± 0.0142 | – | – | – |
| pearson_delta+r2_top | 11 of 11 runs | 0.5045 ± 0.0348 | 0.7893 ± 0.0256 | 0.1245 ± 0.0154 | – | – | – |

- pearson_delta+r2_top minus pearson_delta, pearson_delta: -0.0016 ± 0.0089 over 11 runs; better in 2 of 11.
- pearson_delta+r2_top minus pearson_delta, R²_top: +0.0011 ± 0.0077 over 11 runs; better in 10 of 11.
- pearson_delta+r2_top minus pearson_delta, MSE_top: -0.0011 ± 0.0041 over 11 runs; better in 10 of 11.
