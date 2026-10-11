# When did each run stop improving?

Running best of the visible selection score, by minute of the run (experiments in order of completion, single models; the sealed set is never read). The start is the run's starting model, the best of its baseline fits. "Share of final gain" is how much of the run's final visible gain over the start had been reached at a quarter, half and three quarters of the time budget; the next two columns are the gain that arrived after the midpoint and after three quarters. A run is "still rising" when the last quarter added at least 0.005 (the threshold is a judgement; the column before it shows the amount); a run that ended before its final quarter (the scripted control runs out of hypotheses in minutes) is not counted either way, nor is a warm-started run, whose gain is the model it imported.

| run | arm | workers | budget (min) | start → best (visible) | share at 25% / 50% / 75% | gain after 50% | gain after 75% | last improvement (min) | experiments after it | planner rounds after it | still rising |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scale_w1_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 1 | 20.0 | 0.556 → 0.627 | 87% / 94% / 98% | +0.0044 | +0.0013 | 17.7 | 5 of 82 | 2 | no |
| scale_w1_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 1 | 20.0 | 0.556 → 0.619 | 60% / 94% / 100% | +0.0036 | +0.0002 | 18.8 | 3 of 93 | 1 | no |
| scale_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 4 | 20.0 | 0.556 → 0.628 | 71% / 77% / 99% | +0.0169 | +0.0009 | 19.9 | 4 of 159 | 1 | no |
| scale_w4_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 4 | 20.0 | 0.556 → 0.609 | 61% / 92% / 100% | +0.0042 | +0.0000 | 13.0 | 12 of 112 | 0 | no |
| scale_w8_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 8 | 20.0 | 0.556 → 0.636 | 71% / 84% / 91% | +0.0131 | +0.0070 | 19.7 | 1 of 280 | 1 | yes |
| scale_w8_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 8 | 20.0 | 0.556 → 0.651 | 75% / 84% / 98% | +0.0154 | +0.0022 | 19.0 | 17 of 275 | 2 | no |
| scale_w16_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 16 | 20.0 | 0.556 → 0.648 | 82% / 91% / 96% | +0.0082 | +0.0038 | 19.9 | 16 of 657 | 3 | no |
| scale_w16_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11 | 16 | 20.0 | 0.556 → 0.664 | 68% / 78% / 90% | +0.0239 | +0.0107 | 19.9 | 11 of 722 | 3 | yes |
| scale_control_r0 | scripted control (no LLM) @ 2492e11 | 4 | 20.0 | 0.556 → 0.571 | 100% / 100% / 100% | +0.0000 | +0.0000 | 0.1 | 2 of 8 | 2 | ended early |
| scale_control_r1 | scripted control (no LLM) @ 2492e11 | 4 | 20.0 | 0.556 → 0.571 | 100% / 100% / 100% | +0.0000 | +0.0000 | 0.1 | 3 of 9 | 2 | ended early |
| scale_control_r2 | scripted control (no LLM) @ 2492e11 | 4 | 20.0 | 0.556 → 0.571 | 100% / 100% / 100% | +0.0000 | +0.0000 | 0.1 | 3 of 9 | 2 | ended early |
| scale_control_r3 | scripted control (no LLM) @ 2492e11 | 4 | 20.0 | 0.556 → 0.571 | 100% / 100% / 100% | +0.0000 | +0.0000 | 0.1 | 3 of 9 | 2 | ended early |
| scale_control_r4 | scripted control (no LLM) @ 2492e11 | 4 | 20.0 | 0.556 → 0.571 | 100% / 100% / 100% | +0.0000 | +0.0000 | 0.1 | 3 of 9 | 2 | ended early |
| scale_control_r5 | scripted control (no LLM) @ 2492e11 | 4 | 20.0 | 0.556 → 0.571 | 100% / 100% / 100% | +0.0000 | +0.0000 | 0.1 | 3 of 9 | 2 | ended early |
| newcode_control_r0 | scripted control (no LLM) @ 72a53c5 | 4 | 20.0 | 0.501 → 0.508 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.8 | 1 of 22 | 1 | ended early |
| newcode_control_r1 | scripted control (no LLM) @ 72a53c5 | 4 | 20.0 | 0.502 → 0.510 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.8 | 1 of 23 | 1 | ended early |
| newcode_control_r2 | scripted control (no LLM) @ 72a53c5 | 4 | 20.0 | 0.501 → 0.508 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.8 | 1 of 23 | 1 | ended early |
| newcode_control_r3 | scripted control (no LLM) @ 72a53c5 | 4 | 20.0 | 0.501 → 0.509 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.9 | 1 of 23 | 1 | ended early |
| newcode_control_r4 | scripted control (no LLM) @ 72a53c5 | 4 | 20.0 | 0.502 → 0.510 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.8 | 1 of 23 | 1 | ended early |
| newcode_control_r5 | scripted control (no LLM) @ 72a53c5 | 4 | 20.0 | 0.503 → 0.512 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.8 | 1 of 23 | 1 | ended early |
| newcode2_control_r0 | scripted control (no LLM) @ 537344f | 4 | 20.0 | 0.501 → 0.508 | 100% / 100% / 100% | +0.0000 | +0.0000 | 1.8 | 92 of 126 | 1 | ended early |
| newcode_opus_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f | 4 | 20.0 | 0.501 → 0.590 | 92% / 97% / 98% | +0.0025 | +0.0015 | 19.9 | 4 of 411 | 1 | no |
| newcode_opus_w4_r1 | claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f | 4 | 20.0 | 0.502 → 0.586 | 79% / 94% / 95% | +0.0052 | +0.0038 | 20.0 | 1 of 351 | 1 | no |
| newcode_ds_w4_r0 | deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f | 4 | 20.0 | 0.501 → 0.510 | 75% / 86% / 94% | +0.0014 | +0.0005 | 18.3 | 47 of 672 | 7 | no |
| newcode_ds_w4_r1 | deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f | 4 | 20.0 | 0.502 → 0.587 | 74% / 74% / 98% | +0.0224 | +0.0015 | 19.9 | 1 of 559 | 2 | no |
| newcode_derule_opus_w4_r0 | claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top) @ 7debddd | 4 | 20.0 | 0.638 → 0.713 | 70% / 78% / 94% | +0.0165 | +0.0048 | 18.6 | 10 of 352 | 2 | no |
| control_components_w4_r0 | scripted control (no LLM) @ 74e07ca | 4 | 20.0 | 0.501 → 0.531 | 100% / 100% / 100% | +0.0000 | +0.0000 | 2.1 | 140 of 179 | 0 | ended early |
| control_components_from_opus_r0 | no-LLM continuation of newcode_opus_w4_r0 @ bee2106 | 4 | 20.0 | 0.501 → 0.591 | 100% / 100% / 100% | +0.0000 | +0.0000 | 2.1 | 1271 of 1316 | 19 | continuation (its gain is the warm start) |

## By arm

- claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top) @ 7debddd, 4 workers (1 run): share of the final gain reached by the midpoint 78% (median); gain after three quarters +0.0048 (median); 0 of 1 still rising in the final quarter.
- claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 1 workers (2 runs): share of the final gain reached by the midpoint 94% (median); gain after three quarters +0.0008 (median); 0 of 2 still rising in the final quarter.
- claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 4 workers (2 runs): share of the final gain reached by the midpoint 84% (median); gain after three quarters +0.0004 (median); 0 of 2 still rising in the final quarter.
- claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 8 workers (2 runs): share of the final gain reached by the midpoint 84% (median); gain after three quarters +0.0046 (median); 1 of 2 still rising in the final quarter.
- claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 16 workers (2 runs): share of the final gain reached by the midpoint 85% (median); gain after three quarters +0.0073 (median); 1 of 2 still rising in the final quarter.
- claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f, 4 workers (2 runs): share of the final gain reached by the midpoint 96% (median); gain after three quarters +0.0027 (median); 0 of 2 still rising in the final quarter.
- deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f, 4 workers (2 runs): share of the final gain reached by the midpoint 80% (median); gain after three quarters +0.0010 (median); 0 of 2 still rising in the final quarter.
- no-LLM continuation of newcode_opus_w4_r0 @ bee2106, 4 workers (1 run): warm-started from another campaign, so its gain is the imported model and it is not counted.
- scripted control (no LLM) @ 2492e11, 4 workers (6 runs): ended after 0.1 min (median last improvement) of a 20-min budget, so the budget was not the limit.
- scripted control (no LLM) @ 537344f, 4 workers (1 run): ended after 1.8 min (median last improvement) of a 20-min budget, so the budget was not the limit.
- scripted control (no LLM) @ 72a53c5, 4 workers (6 runs): ended after 1.8 min (median last improvement) of a 20-min budget, so the budget was not the limit.
- scripted control (no LLM) @ 74e07ca, 4 workers (1 run): ended after 2.1 min (median last improvement) of a 20-min budget, so the budget was not the limit.

## Reading

2 of 13 runs that used their budget were still rising in the final quarter (median gain after three quarters +0.0015; median share of the gain reached by the midpoint 86%). If that is a minority and the late gains are small, the runs had plateaued before their deadline and a longer budget alone is unlikely to raise the score; the lever is then a new feature family. If it is a majority, a longer budget is the cheaper next test. Visible scores only: whether a late visible improvement survives on the sealed set is a separate question the runs' summaries answer.
