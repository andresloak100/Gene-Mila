# Refit on all visible labels, scored once on the sealed set

Protocol, fixed before any sealed result under it was read and reported whatever it shows. For each finished run, every model the run already scored on the sealed set (its top single finalists, its ensemble when one was kept, and its starting baseline) is refitted on all visible labels: the 50 training perturbations the run trained on plus the 17 visible validation perturbations it only ever used for selection. The refit keeps exactly the same feature set, feature parameters, model type, chosen alpha and seed, is fitted as the pipeline fits (features for the training rows and the held-out rows, standardised by the training mean and standard deviation, one linear model on the flattened deltas), and is scored once on the sealed perturbations through the lab's oracle; the ensemble's refit is the mean of its members' refits. Nothing is selected, tuned or chosen by a sealed score: the finalists are the ones the run chose under its own protocol, the selected finalist of a run is its highest visible score among them, and every refit is reported. The run directories are read only (own oracle instance, own feature cache, no event and no query charged to the run).

Read the numbers as one more look at a sealed set that is no longer fresh: before this protocol was written, the sealed perturbations had already been scored for dozens of finalists across about thirty runs, and that history shaped which models exist to be refitted. A refit gain here is evidence that the extra labels help, not a clean held-out confirmation; the untouched tests are the Norman bundle and any new split.

## Selected finalist per run

| run | arm | workers | selected | kind | model | alpha | sealed pearson_delta: original | refit | difference | MSE_DE original -> refit | PCC_DE original -> refit | R²_DE original -> refit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| newcode_derule_opus_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top) @ 7debddd | 4 | EXP_0388 | ensemble | ensemble | n/a | 0.5839 | 0.5877 | +0.0038 | 0.1159 -> 0.1209 | 0.9546 -> 0.9521 | 0.8043 -> 0.7957 |
| scale_w1_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 1 | EXP_0096 | config | ridge | 0.01 | 0.5440 | 0.5400 | -0.0039 | 0.1051 -> 0.1102 | 0.9577 -> 0.9559 | 0.8218 -> 0.8126 |
| scale_w1_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 1 | EXP_0110 | new_feature | ridge | 100 | 0.5886 | 0.5869 | -0.0017 | 0.1120 -> 0.1154 | 0.9567 -> 0.9538 | 0.8128 -> 0.8050 |
| scale_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 4 | EXP_0197 | new_feature | ridge | 100 | 0.6007 | 0.5981 | -0.0026 | 0.1150 -> 0.1130 | 0.9559 -> 0.9553 | 0.8050 -> 0.8084 |
| scale_w4_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 4 | EXP_0121 | new_feature | ridge | 100 | 0.6037 | 0.5949 | -0.0088 | 0.1183 -> 0.1210 | 0.9548 -> 0.9533 | 0.8006 -> 0.7956 |
| scale_w8_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 8 | EXP_0316 | new_feature | ridge | 0.01 | 0.5853 | 0.5719 | -0.0133 | 0.1219 -> 0.1188 | 0.9540 -> 0.9543 | 0.8011 -> 0.7997 |
| scale_w8_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 8 | EXP_0334 | new_feature | ridge | 10 | 0.5832 | 0.5662 | -0.0170 | 0.1170 -> 0.1225 | 0.9548 -> 0.9535 | 0.8029 -> 0.7909 |
| scale_w16_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 16 | EXP_0780 | config | ridge | 100 | 0.5618 | 0.5884 | +0.0266 | 0.1172 -> 0.1126 | 0.9550 -> 0.9558 | 0.8015 -> 0.8073 |
| scale_w16_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 16 | EXP_0889 | config | ridge | 0.001 | 0.5926 | 0.5560 | -0.0366 | 0.1041 -> 0.1091 | 0.9606 -> 0.9582 | 0.8298 -> 0.8201 |
| newcode_opus_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f | 4 | EXP_0461 | ensemble | ensemble | n/a | 0.6007 | 0.6030 | +0.0023 | 0.1178 -> 0.1204 | 0.9550 -> 0.9539 | 0.8023 -> 0.7979 |
| newcode_opus_w4_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f | 4 | EXP_0393 | config | ridge | 8000 | 0.5873 | 0.5951 | +0.0079 | 0.1293 -> 0.1323 | 0.9503 -> 0.9501 | 0.7787 -> 0.7766 |
| newcode_ds_w4_r0 | deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f | 4 | EXP_0776 | config | ridge | 5600 | 0.5383 | 0.5407 | +0.0023 | 0.1482 -> 0.1457 | 0.9390 -> 0.9414 | 0.7487 -> 0.7534 |
| newcode_ds_w4_r1 | deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f | 4 | EXP_0725 | config | ridge | 30000 | 0.6007 | 0.5969 | -0.0037 | 0.1169 -> 0.1153 | 0.9533 -> 0.9541 | 0.8030 -> 0.8047 |
| control_components_from_opus_r0 | no-LLM continuation of newcode_opus_w4_r0 @ bee2106 | 4 | EXP_0053 | config | ridge | 4590 | 0.5997 | 0.6037 | +0.0040 | 0.1192 -> 0.1235 | 0.9543 -> 0.9526 | 0.7998 -> 0.7925 |
| scale_control_r0 | scripted control (no LLM) @ 2492e11 | 4 | EXP_0010 | new_feature | ridge | 0.01 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| scale_control_r1 | scripted control (no LLM) @ 2492e11 | 4 | EXP_0010 | new_feature | ridge | 0.01 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| scale_control_r2 | scripted control (no LLM) @ 2492e11 | 4 | EXP_0010 | new_feature | ridge | 0.01 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| scale_control_r3 | scripted control (no LLM) @ 2492e11 | 4 | EXP_0010 | new_feature | ridge | 0.01 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| scale_control_r4 | scripted control (no LLM) @ 2492e11 | 4 | EXP_0010 | new_feature | ridge | 0.01 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| scale_control_r5 | scripted control (no LLM) @ 2492e11 | 4 | EXP_0010 | new_feature | ridge | 0.01 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| newcode2_control_r0 | scripted control (no LLM) @ 537344f | 4 | EXP_0041 | config | ridge | 41310 | 0.5527 | 0.5492 | -0.0035 | 0.1628 -> 0.1580 | 0.9355 -> 0.9378 | 0.7259 -> 0.7335 |
| newcode_control_r0 | scripted control (no LLM) @ 72a53c5 | 4 | EXP_0028 | config | ridge | 41310 | 0.5527 | 0.5492 | -0.0035 | 0.1628 -> 0.1580 | 0.9355 -> 0.9378 | 0.7259 -> 0.7335 |
| newcode_control_r1 | scripted control (no LLM) @ 72a53c5 | 4 | EXP_0028 | config | ridge | 72900 | 0.5530 | 0.5493 | -0.0037 | 0.1718 -> 0.1658 | 0.9312 -> 0.9343 | 0.7100 -> 0.7201 |
| newcode_control_r2 | scripted control (no LLM) @ 72a53c5 | 4 | EXP_0028 | config | ridge | 41310 | 0.5527 | 0.5492 | -0.0035 | 0.1628 -> 0.1580 | 0.9355 -> 0.9378 | 0.7259 -> 0.7335 |
| newcode_control_r3 | scripted control (no LLM) @ 72a53c5 | 4 | EXP_0028 | config | ridge | 72900 | 0.5530 | 0.5493 | -0.0037 | 0.1718 -> 0.1658 | 0.9312 -> 0.9343 | 0.7100 -> 0.7201 |
| newcode_control_r4 | scripted control (no LLM) @ 72a53c5 | 4 | EXP_0028 | config | ridge | 72900 | 0.5530 | 0.5493 | -0.0037 | 0.1718 -> 0.1658 | 0.9312 -> 0.9343 | 0.7100 -> 0.7201 |
| newcode_control_r5 | scripted control (no LLM) @ 72a53c5 | 4 | EXP_0028 | config | ridge | 72900 | 0.5530 | 0.5493 | -0.0037 | 0.1718 -> 0.1658 | 0.9312 -> 0.9343 | 0.7100 -> 0.7201 |
| control_components_w4_r0 | scripted control (no LLM) @ 74e07ca | 4 | EXP_0046 | config | ridge | 41310 | 0.5932 | 0.5890 | -0.0042 | 0.1420 -> 0.1415 | 0.9429 -> 0.9438 | 0.7554 -> 0.7567 |

## Every refit finalist

Singles, the kept ensemble and the starting baseline of each run; the selected finalist is marked with *. Original = the run's own sealed score of the model fitted on the training perturbations; refit = the same model fitted on all visible labels.

| run | finalist | kind | model | alpha | visible score | pearson_delta original | refit | diff | MSE_DE original | refit | diff | PCC_DE original | refit | diff | R²_DE original | refit | diff |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| newcode_derule_opus_w4_r0 | EXP_0363 | config | ridge | 17000 | 0.7131 | 0.5693 | 0.5657 | -0.0036 | 0.1147 | 0.1204 | +0.0056 | 0.9548 | 0.9517 | -0.0031 | 0.8060 | 0.7960 | -0.0100 |
| newcode_derule_opus_w4_r0 | EXP_0365 | config | ridge | 17000 | 0.7127 | 0.5694 | 0.5691 | -0.0003 | 0.1147 | 0.1204 | +0.0057 | 0.9548 | 0.9521 | -0.0028 | 0.8061 | 0.7968 | -0.0094 |
| newcode_derule_opus_w4_r0 | EXP_0364 | config | ridge | 17000 | 0.7126 | 0.5910 | 0.5970 | +0.0060 | 0.1201 | 0.1240 | +0.0039 | 0.9536 | 0.9519 | -0.0016 | 0.7970 | 0.7903 | -0.0067 |
| newcode_derule_opus_w4_r0 | EXP_0388* | ensemble | ensemble | n/a | 0.7155 | 0.5839 | 0.5877 | +0.0038 | 0.1159 | 0.1209 | +0.0050 | 0.9546 | 0.9521 | -0.0025 | 0.8043 | 0.7957 | -0.0086 |
| newcode_derule_opus_w4_r0 | EXP_0003 | baseline | ols | 0 | 0.6383 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w1_r0 | EXP_0096* | config | ridge | 0.01 | 0.6268 | 0.5440 | 0.5400 | -0.0039 | 0.1051 | 0.1102 | +0.0051 | 0.9577 | 0.9559 | -0.0018 | 0.8218 | 0.8126 | -0.0092 |
| scale_w1_r0 | EXP_0102 | new_feature | ridge | 0.01 | 0.6263 | 0.5444 | 0.5379 | -0.0064 | 0.1050 | 0.1101 | +0.0051 | 0.9580 | 0.9562 | -0.0017 | 0.8222 | 0.8131 | -0.0091 |
| scale_w1_r0 | EXP_0091 | new_feature | ridge | 0.01 | 0.6258 | 0.5841 | 0.5914 | +0.0074 | 0.1212 | 0.1221 | +0.0009 | 0.9549 | 0.9546 | -0.0003 | 0.7993 | 0.7966 | -0.0027 |
| scale_w1_r0 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w1_r1 | EXP_0110* | new_feature | ridge | 100 | 0.6188 | 0.5886 | 0.5869 | -0.0017 | 0.1120 | 0.1154 | +0.0034 | 0.9567 | 0.9538 | -0.0029 | 0.8128 | 0.8050 | -0.0078 |
| scale_w1_r1 | EXP_0109 | new_feature | ridge | 100 | 0.6188 | 0.5886 | 0.5869 | -0.0017 | 0.1120 | 0.1154 | +0.0034 | 0.9567 | 0.9538 | -0.0029 | 0.8128 | 0.8050 | -0.0078 |
| scale_w1_r1 | EXP_0105 | new_feature | ridge | 10 | 0.6186 | 0.5894 | 0.5884 | -0.0010 | 0.1115 | 0.1137 | +0.0021 | 0.9567 | 0.9545 | -0.0023 | 0.8135 | 0.8078 | -0.0056 |
| scale_w1_r1 | EXP_0004 | baseline | ridge | 0.01 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w4_r0 | EXP_0197* | new_feature | ridge | 100 | 0.6285 | 0.6007 | 0.5981 | -0.0026 | 0.1150 | 0.1130 | -0.0021 | 0.9559 | 0.9553 | -0.0006 | 0.8050 | 0.8084 | +0.0034 |
| scale_w4_r0 | EXP_0194 | new_feature | ridge | 10 | 0.6283 | 0.6042 | 0.5973 | -0.0068 | 0.1152 | 0.1135 | -0.0017 | 0.9556 | 0.9549 | -0.0007 | 0.8048 | 0.8074 | +0.0026 |
| scale_w4_r0 | EXP_0189 | new_feature | ridge | 100 | 0.6282 | 0.6059 | 0.6048 | -0.0011 | 0.1135 | 0.1083 | -0.0052 | 0.9565 | 0.9570 | +0.0005 | 0.8076 | 0.8154 | +0.0078 |
| scale_w4_r0 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w4_r1 | EXP_0121* | new_feature | ridge | 100 | 0.6091 | 0.6037 | 0.5949 | -0.0088 | 0.1183 | 0.1210 | +0.0026 | 0.9548 | 0.9533 | -0.0015 | 0.8006 | 0.7956 | -0.0050 |
| scale_w4_r1 | EXP_0135 | config | ridge | 3000 | 0.6087 | 0.5990 | 0.5960 | -0.0029 | 0.1207 | 0.1219 | +0.0013 | 0.9539 | 0.9530 | -0.0009 | 0.7971 | 0.7940 | -0.0031 |
| scale_w4_r1 | EXP_0127 | config | ridge | 100 | 0.6087 | 0.5980 | 0.5943 | -0.0036 | 0.1207 | 0.1213 | +0.0007 | 0.9539 | 0.9532 | -0.0007 | 0.7973 | 0.7950 | -0.0023 |
| scale_w4_r1 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w8_r0 | EXP_0316* | new_feature | ridge | 0.01 | 0.6365 | 0.5853 | 0.5719 | -0.0133 | 0.1219 | 0.1188 | -0.0031 | 0.9540 | 0.9543 | +0.0003 | 0.8011 | 0.7997 | -0.0014 |
| scale_w8_r0 | EXP_0311 | new_feature | ridge | 0.01 | 0.6355 | 0.5813 | 0.5739 | -0.0074 | 0.1219 | 0.1197 | -0.0022 | 0.9538 | 0.9538 | +0.0000 | 0.8003 | 0.7977 | -0.0026 |
| scale_w8_r0 | EXP_0319 | new_feature | ridge | 0.01 | 0.6350 | 0.5844 | 0.5759 | -0.0086 | 0.1217 | 0.1191 | -0.0026 | 0.9542 | 0.9544 | +0.0002 | 0.8011 | 0.7990 | -0.0021 |
| scale_w8_r0 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w8_r1 | EXP_0334* | new_feature | ridge | 10 | 0.6509 | 0.5832 | 0.5662 | -0.0170 | 0.1170 | 0.1225 | +0.0055 | 0.9548 | 0.9535 | -0.0013 | 0.8029 | 0.7909 | -0.0120 |
| scale_w8_r1 | EXP_0345 | new_feature | ridge | 10 | 0.6507 | 0.5803 | 0.5667 | -0.0136 | 0.1173 | 0.1221 | +0.0048 | 0.9547 | 0.9536 | -0.0011 | 0.8023 | 0.7916 | -0.0107 |
| scale_w8_r1 | EXP_0335 | new_feature | ridge | 10 | 0.6507 | 0.5811 | 0.5676 | -0.0135 | 0.1165 | 0.1214 | +0.0049 | 0.9548 | 0.9538 | -0.0011 | 0.8035 | 0.7927 | -0.0108 |
| scale_w8_r1 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w16_r0 | EXP_0780* | config | ridge | 100 | 0.6477 | 0.5618 | 0.5884 | +0.0266 | 0.1172 | 0.1126 | -0.0047 | 0.9550 | 0.9558 | +0.0008 | 0.8015 | 0.8073 | +0.0057 |
| scale_w16_r0 | EXP_0781 | config | ridge | 100 | 0.6477 | 0.5599 | 0.5892 | +0.0292 | 0.1169 | 0.1123 | -0.0046 | 0.9553 | 0.9559 | +0.0006 | 0.8009 | 0.8080 | +0.0070 |
| scale_w16_r0 | EXP_0766 | new_feature | ridge | 100 | 0.6475 | 0.5663 | 0.5877 | +0.0215 | 0.1164 | 0.1126 | -0.0038 | 0.9552 | 0.9558 | +0.0006 | 0.8024 | 0.8073 | +0.0050 |
| scale_w16_r0 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_w16_r1 | EXP_0889* | config | ridge | 0.001 | 0.6644 | 0.5926 | 0.5560 | -0.0366 | 0.1041 | 0.1091 | +0.0050 | 0.9606 | 0.9582 | -0.0024 | 0.8298 | 0.8201 | -0.0097 |
| scale_w16_r1 | EXP_0898 | new_feature | ridge | 0.01 | 0.6644 | 0.5923 | 0.5547 | -0.0376 | 0.1041 | 0.1091 | +0.0050 | 0.9606 | 0.9582 | -0.0024 | 0.8298 | 0.8201 | -0.0097 |
| scale_w16_r1 | EXP_0902 | new_feature | ridge | 0.01 | 0.6642 | 0.5928 | 0.5560 | -0.0368 | 0.1040 | 0.1090 | +0.0050 | 0.9606 | 0.9582 | -0.0024 | 0.8298 | 0.8202 | -0.0096 |
| scale_w16_r1 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_opus_w4_r0 | EXP_0441 | config | ridge | 300 | 0.5903 | 0.5987 | 0.6031 | +0.0045 | 0.1172 | 0.1209 | +0.0037 | 0.9551 | 0.9537 | -0.0014 | 0.8029 | 0.7968 | -0.0061 |
| newcode_opus_w4_r0 | EXP_0444 | config | ridge | 100 | 0.5901 | 0.5985 | 0.6020 | +0.0035 | 0.1172 | 0.1176 | +0.0004 | 0.9551 | 0.9548 | -0.0003 | 0.8029 | 0.8023 | -0.0005 |
| newcode_opus_w4_r0 | EXP_0428 | config | ridge | 510 | 0.5896 | 0.6008 | 0.6025 | +0.0018 | 0.1197 | 0.1228 | +0.0031 | 0.9545 | 0.9530 | -0.0015 | 0.8001 | 0.7944 | -0.0058 |
| newcode_opus_w4_r0 | EXP_0461* | ensemble | ensemble | n/a | 0.5907 | 0.6007 | 0.6030 | +0.0023 | 0.1178 | 0.1204 | +0.0025 | 0.9550 | 0.9539 | -0.0012 | 0.8023 | 0.7979 | -0.0044 |
| newcode_opus_w4_r0 | EXP_0003 | baseline | ols | 0 | 0.5010 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_opus_w4_r1 | EXP_0393* | config | ridge | 8000 | 0.5861 | 0.5873 | 0.5951 | +0.0079 | 0.1293 | 0.1323 | +0.0030 | 0.9503 | 0.9501 | -0.0002 | 0.7787 | 0.7766 | -0.0021 |
| newcode_opus_w4_r1 | EXP_0380 | new_feature | ridge | 100 | 0.5848 | 0.5883 | 0.5858 | -0.0025 | 0.1256 | 0.1287 | +0.0031 | 0.9521 | 0.9513 | -0.0008 | 0.7856 | 0.7813 | -0.0043 |
| newcode_opus_w4_r1 | EXP_0381 | new_feature | ridge | 100 | 0.5848 | 0.5883 | 0.5858 | -0.0025 | 0.1256 | 0.1287 | +0.0031 | 0.9521 | 0.9513 | -0.0008 | 0.7856 | 0.7813 | -0.0043 |
| newcode_opus_w4_r1 | EXP_0003 | baseline | ols | 0 | 0.5017 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_ds_w4_r0 | EXP_0776* | config | ridge | 5600 | 0.5104 | 0.5383 | 0.5407 | +0.0023 | 0.1482 | 0.1457 | -0.0025 | 0.9390 | 0.9414 | +0.0025 | 0.7487 | 0.7534 | +0.0047 |
| newcode_ds_w4_r0 | EXP_0724 | config | ridge | 5600 | 0.5104 | 0.5382 | 0.5409 | +0.0027 | 0.1484 | 0.1452 | -0.0032 | 0.9390 | 0.9415 | +0.0025 | 0.7484 | 0.7540 | +0.0055 |
| newcode_ds_w4_r0 | EXP_0800 | config | ridge | 5600 | 0.5104 | 0.5383 | 0.5407 | +0.0024 | 0.1480 | 0.1457 | -0.0022 | 0.9390 | 0.9414 | +0.0025 | 0.7485 | 0.7532 | +0.0047 |
| newcode_ds_w4_r0 | EXP_0003 | baseline | ols | 0 | 0.5010 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_ds_w4_r1 | EXP_0725* | config | ridge | 30000 | 0.5867 | 0.6007 | 0.5969 | -0.0037 | 0.1169 | 0.1153 | -0.0016 | 0.9533 | 0.9541 | +0.0009 | 0.8030 | 0.8047 | +0.0017 |
| newcode_ds_w4_r1 | EXP_0724 | config | ridge | 30000 | 0.5866 | 0.6007 | 0.5972 | -0.0036 | 0.1170 | 0.1155 | -0.0015 | 0.9533 | 0.9542 | +0.0009 | 0.8030 | 0.8046 | +0.0016 |
| newcode_ds_w4_r1 | EXP_0641 | config | ridge | 30000 | 0.5865 | 0.6007 | 0.5971 | -0.0036 | 0.1170 | 0.1155 | -0.0015 | 0.9533 | 0.9542 | +0.0009 | 0.8030 | 0.8046 | +0.0016 |
| newcode_ds_w4_r1 | EXP_0003 | baseline | ols | 0 | 0.5017 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| control_components_from_opus_r0 | EXP_0053* | config | ridge | 4590 | 0.5908 | 0.5997 | 0.6037 | +0.0040 | 0.1192 | 0.1235 | +0.0043 | 0.9543 | 0.9526 | -0.0017 | 0.7998 | 0.7925 | -0.0073 |
| control_components_from_opus_r0 | EXP_0064 | config | ridge | 4590 | 0.5907 | 0.5997 | 0.6038 | +0.0042 | 0.1196 | 0.1243 | +0.0047 | 0.9543 | 0.9526 | -0.0016 | 0.7992 | 0.7914 | -0.0078 |
| control_components_from_opus_r0 | EXP_0076 | config | ridge | 4590 | 0.5907 | 0.5997 | 0.6037 | +0.0040 | 0.1192 | 0.1235 | +0.0043 | 0.9543 | 0.9526 | -0.0017 | 0.7998 | 0.7925 | -0.0073 |
| control_components_from_opus_r0 | EXP_0003 | baseline | ols | 0 | 0.5010 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r0 | EXP_0010* | new_feature | ridge | 0.01 | 0.5710 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| scale_control_r0 | EXP_0013 | config | ridge | 0.001 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r0 | EXP_0012 | new_feature | ridge | 0.01 | 0.5560 | 0.5200 | 0.5182 | -0.0018 | 0.1535 | 0.1517 | -0.0018 | 0.9319 | 0.9334 | +0.0015 | 0.7343 | 0.7369 | +0.0026 |
| scale_control_r0 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r1 | EXP_0010* | new_feature | ridge | 0.01 | 0.5710 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| scale_control_r1 | EXP_0013 | config | ridge | 0.001 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r1 | EXP_0015 | config | lasso | 1e-05 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7340 | 0.7367 | +0.0026 |
| scale_control_r1 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r2 | EXP_0010* | new_feature | ridge | 0.01 | 0.5710 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| scale_control_r2 | EXP_0013 | config | ridge | 0.001 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r2 | EXP_0015 | config | lasso | 1e-05 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7340 | 0.7367 | +0.0026 |
| scale_control_r2 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r3 | EXP_0010* | new_feature | ridge | 0.01 | 0.5710 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| scale_control_r3 | EXP_0013 | config | ridge | 0.001 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r3 | EXP_0015 | config | lasso | 1e-05 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7340 | 0.7367 | +0.0026 |
| scale_control_r3 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r4 | EXP_0010* | new_feature | ridge | 0.01 | 0.5710 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| scale_control_r4 | EXP_0013 | config | ridge | 0.001 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r4 | EXP_0015 | config | lasso | 1e-05 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7340 | 0.7367 | +0.0026 |
| scale_control_r4 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r5 | EXP_0010* | new_feature | ridge | 0.01 | 0.5710 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| scale_control_r5 | EXP_0013 | config | ridge | 0.001 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| scale_control_r5 | EXP_0015 | config | lasso | 1e-05 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7340 | 0.7367 | +0.0026 |
| scale_control_r5 | EXP_0003 | baseline | ols | 0 | 0.5560 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode2_control_r0 | EXP_0041* | config | ridge | 41310 | 0.5078 | 0.5527 | 0.5492 | -0.0035 | 0.1628 | 0.1580 | -0.0048 | 0.9355 | 0.9378 | +0.0023 | 0.7259 | 0.7335 | +0.0076 |
| newcode2_control_r0 | EXP_0047 | config | ridge | 41310 | 0.5075 | 0.5527 | 0.5492 | -0.0035 | 0.1628 | 0.1580 | -0.0048 | 0.9355 | 0.9378 | +0.0023 | 0.7259 | 0.7335 | +0.0076 |
| newcode2_control_r0 | EXP_0022 | config | lasso | 1e-05 | 0.5074 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode2_control_r0 | EXP_0003 | baseline | ols | 0 | 0.5010 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_control_r0 | EXP_0028* | config | ridge | 41310 | 0.5078 | 0.5527 | 0.5492 | -0.0035 | 0.1628 | 0.1580 | -0.0048 | 0.9355 | 0.9378 | +0.0023 | 0.7259 | 0.7335 | +0.0076 |
| newcode_control_r0 | EXP_0022 | config | lasso | 1e-05 | 0.5074 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode_control_r0 | EXP_0017 | config | ridge | 0.006 | 0.5069 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| newcode_control_r0 | EXP_0003 | baseline | ols | 0 | 0.5010 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_control_r1 | EXP_0028* | config | ridge | 72900 | 0.5100 | 0.5530 | 0.5493 | -0.0037 | 0.1718 | 0.1658 | -0.0060 | 0.9312 | 0.9343 | +0.0031 | 0.7100 | 0.7201 | +0.0101 |
| newcode_control_r1 | EXP_0022 | config | lasso | 1e-05 | 0.5096 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode_control_r1 | EXP_0017 | config | ridge | 0.0033 | 0.5091 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| newcode_control_r1 | EXP_0003 | baseline | ols | 0 | 0.5017 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_control_r2 | EXP_0028* | config | ridge | 41310 | 0.5082 | 0.5527 | 0.5492 | -0.0035 | 0.1628 | 0.1580 | -0.0048 | 0.9355 | 0.9378 | +0.0023 | 0.7259 | 0.7335 | +0.0076 |
| newcode_control_r2 | EXP_0022 | config | lasso | 1e-05 | 0.5078 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode_control_r2 | EXP_0017 | config | ridge | 0.0033 | 0.5073 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| newcode_control_r2 | EXP_0003 | baseline | ols | 0 | 0.5013 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_control_r3 | EXP_0028* | config | ridge | 72900 | 0.5094 | 0.5530 | 0.5493 | -0.0037 | 0.1718 | 0.1658 | -0.0060 | 0.9312 | 0.9343 | +0.0031 | 0.7100 | 0.7201 | +0.0101 |
| newcode_control_r3 | EXP_0022 | config | lasso | 1e-05 | 0.5088 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode_control_r3 | EXP_0017 | config | ridge | 0.006 | 0.5083 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| newcode_control_r3 | EXP_0003 | baseline | ols | 0 | 0.5014 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_control_r4 | EXP_0028* | config | ridge | 72900 | 0.5104 | 0.5530 | 0.5493 | -0.0037 | 0.1718 | 0.1658 | -0.0060 | 0.9312 | 0.9343 | +0.0031 | 0.7100 | 0.7201 | +0.0101 |
| newcode_control_r4 | EXP_0022 | config | lasso | 1e-05 | 0.5100 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode_control_r4 | EXP_0017 | config | ridge | 0.0033 | 0.5095 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| newcode_control_r4 | EXP_0003 | baseline | ols | 0 | 0.5025 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| newcode_control_r5 | EXP_0028* | config | ridge | 72900 | 0.5117 | 0.5530 | 0.5493 | -0.0037 | 0.1718 | 0.1658 | -0.0060 | 0.9312 | 0.9343 | +0.0031 | 0.7100 | 0.7201 | +0.0101 |
| newcode_control_r5 | EXP_0022 | config | lasso | 1e-05 | 0.5113 | 0.5539 | 0.5501 | -0.0038 | 0.1451 | 0.1442 | -0.0009 | 0.9429 | 0.9431 | +0.0002 | 0.7558 | 0.7562 | +0.0004 |
| newcode_control_r5 | EXP_0017 | config | ridge | 0.0033 | 0.5107 | 0.5537 | 0.5501 | -0.0036 | 0.1451 | 0.1442 | -0.0009 | 0.9428 | 0.9431 | +0.0002 | 0.7559 | 0.7563 | +0.0003 |
| newcode_control_r5 | EXP_0003 | baseline | ols | 0 | 0.5035 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |
| control_components_w4_r0 | EXP_0046* | config | ridge | 41310 | 0.5313 | 0.5932 | 0.5890 | -0.0042 | 0.1420 | 0.1415 | -0.0006 | 0.9429 | 0.9438 | +0.0010 | 0.7554 | 0.7567 | +0.0012 |
| control_components_w4_r0 | EXP_0058 | config | ridge | 41310 | 0.5311 | 0.5932 | 0.5891 | -0.0042 | 0.1420 | 0.1414 | -0.0006 | 0.9429 | 0.9438 | +0.0009 | 0.7554 | 0.7567 | +0.0013 |
| control_components_w4_r0 | EXP_0054 | config | ridge | 41310 | 0.5308 | 0.5934 | 0.5891 | -0.0043 | 0.1420 | 0.1415 | -0.0005 | 0.9428 | 0.9437 | +0.0008 | 0.7556 | 0.7566 | +0.0011 |
| control_components_w4_r0 | EXP_0003 | baseline | ols | 0 | 0.5010 | 0.5196 | 0.5178 | -0.0018 | 0.1536 | 0.1518 | -0.0018 | 0.9318 | 0.9333 | +0.0015 | 0.7341 | 0.7367 | +0.0026 |

## By arm

Mean ± sd over the arm's runs of the selected finalist's sealed pearson_delta, original and refit, and of their difference (refit minus original).

| arm | workers | n | original | refit | difference | runs improved |
|---|---|---|---|---|---|---|
| claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top) @ 7debddd | 4 | 1 | 0.5839 | 0.5877 | +0.0038 | 1 of 1 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 1 | 2 | 0.5663 ± 0.0316 | 0.5635 ± 0.0332 | -0.0028 ± 0.0016 | 0 of 2 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 4 | 2 | 0.6022 ± 0.0021 | 0.5965 ± 0.0023 | -0.0057 ± 0.0044 | 0 of 2 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 8 | 2 | 0.5842 ± 0.0015 | 0.5691 ± 0.0040 | -0.0152 ± 0.0026 | 0 of 2 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 16 | 2 | 0.5772 ± 0.0218 | 0.5722 ± 0.0229 | -0.0050 ± 0.0447 | 1 of 2 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f | 4 | 2 | 0.5940 ± 0.0095 | 0.5991 ± 0.0055 | +0.0051 ± 0.0039 | 2 of 2 |
| deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f | 4 | 2 | 0.5695 ± 0.0441 | 0.5688 ± 0.0398 | -0.0007 ± 0.0043 | 1 of 2 |
| no-LLM continuation of newcode_opus_w4_r0 @ bee2106 | 4 | 1 | 0.5997 | 0.6037 | +0.0040 | 1 of 1 |
| scripted control (no LLM) @ 2492e11 | 4 | 6 | 0.5537 ± 0.0000 | 0.5501 ± 0.0000 | -0.0036 ± 0.0000 | 0 of 6 |
| scripted control (no LLM) @ 537344f | 4 | 1 | 0.5527 | 0.5492 | -0.0035 | 0 of 1 |
| scripted control (no LLM) @ 72a53c5 | 4 | 6 | 0.5529 ± 0.0002 | 0.5493 ± 0.0001 | -0.0036 ± 0.0001 | 0 of 6 |
| scripted control (no LLM) @ 74e07ca | 4 | 1 | 0.5932 | 0.5890 | -0.0042 | 0 of 1 |

## Arm ensembles

For each arm with at least two runs, the mean of the selected finalists' sealed predictions over all of the arm's runs (no run chosen by score), once from the original predictions and once from the refit predictions, each scored once.

| arm | workers | n | pearson_delta: original ensemble | refit ensemble | difference | MSE_DE original -> refit | PCC_DE original -> refit | R²_DE original -> refit |
|---|---|---|---|---|---|---|---|---|
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 1 | 2 | 0.5789 | 0.5780 | -0.0009 | 0.1081 -> 0.1121 | 0.9575 -> 0.9552 | 0.8183 -> 0.8100 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 4 | 2 | 0.6127 | 0.6062 | -0.0064 | 0.1155 -> 0.1161 | 0.9559 -> 0.9546 | 0.8048 -> 0.8038 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 8 | 2 | 0.5990 | 0.5842 | -0.0149 | 0.1178 -> 0.1195 | 0.9551 -> 0.9545 | 0.8050 -> 0.7978 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 16 | 2 | 0.6032 | 0.5956 | -0.0076 | 0.1067 -> 0.1086 | 0.9590 -> 0.9578 | 0.8227 -> 0.8176 |
| claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f | 4 | 2 | 0.6000 | 0.6038 | +0.0039 | 0.1227 -> 0.1257 | 0.9536 -> 0.9524 | 0.7937 -> 0.7887 |
| deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f | 4 | 2 | 0.5884 | 0.5854 | -0.0030 | 0.1277 -> 0.1264 | 0.9479 -> 0.9494 | 0.7852 -> 0.7873 |
| scripted control (no LLM) @ 2492e11 | 4 | 6 | 0.5537 | 0.5501 | -0.0036 | 0.1451 -> 0.1442 | 0.9428 -> 0.9431 | 0.7559 -> 0.7563 |
| scripted control (no LLM) @ 72a53c5 | 4 | 6 | 0.5529 | 0.5493 | -0.0036 | 0.1687 -> 0.1631 | 0.9327 -> 0.9355 | 0.7155 -> 0.7247 |

## Reading

The refit on all visible labels raised the selected finalist's sealed pearson_delta in 6 of 28 runs and lowered it in 22; the difference (refit minus original) averages -0.0033 ± 0.0098 and ranges from -0.0366 to +0.0266. Caution: this is one split, scored on the same sealed perturbations the original finalists were scored on, under a protocol written after those scores were known, and every run's finalist was chosen under the original protocol (selected on the very perturbations the refit now trains on), so the comparison says what more labels buy for the models the runs found, not which protocol selects better.
