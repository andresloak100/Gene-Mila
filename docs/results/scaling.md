# Efficiency across worker counts

Same dataset, split and time budget for every run; mean ± sd over repeats (n in the header). Gain is best model minus the starting model (best linear model on built-in features); sealed = query-only held-out perturbations. Planner dollars are the Claude CLI's usage estimate. 'best' rows take the headline finalist (an ensemble when one was kept); 'single model' rows the best single model. The selection score is what each run optimised: on code with cross-validated selection it averages the validation set and out-of-fold training perturbations, so it is lower than, and not comparable with, the validation-only score of earlier code; 'validation set only' is comparable across code versions. Counts marked planner-proposed exclude the deterministic exploit engine's follow-ups, which run without an LLM whenever workers would otherwise idle (their share is listed).

| measure | scripted control (no LLM), 4 workers (n=6) | claude_cli:opus planner, deepseek:deepseek-flash workers, 1 workers (n=2) | claude_cli:opus planner, deepseek:deepseek-flash workers, 4 workers (n=2) | claude_cli:opus planner, deepseek:deepseek-flash workers, 8 workers (n=2) | claude_cli:opus planner, deepseek:deepseek-flash workers, 16 workers (n=2) |
|---|---|---|---|---|---|
| best visible (selection score) | 0.571 ± 0.000 | 0.623 ± 0.006 | 0.619 ± 0.014 | 0.644 ± 0.010 | 0.656 ± 0.012 |
| best visible (single model, selection score) | 0.571 ± 0.000 | 0.623 ± 0.006 | 0.619 ± 0.014 | 0.644 ± 0.010 | 0.656 ± 0.012 |
| best visible (validation set only) | 0.571 ± 0.000 | 0.623 ± 0.006 | 0.619 ± 0.014 | 0.644 ± 0.010 | 0.656 ± 0.012 |
| best sealed | 0.554 ± 0.000 | 0.566 ± 0.032 | 0.602 ± 0.002 | 0.584 ± 0.001 | 0.577 ± 0.022 |
| best sealed (single model) | 0.554 ± 0.000 | 0.566 ± 0.032 | 0.602 ± 0.002 | 0.584 ± 0.001 | 0.577 ± 0.022 |
| gain over start (visible) | 0.015 ± 0.000 | 0.067 ± 0.006 | 0.063 ± 0.014 | 0.088 ± 0.010 | 0.100 ± 0.012 |
| gain over start (sealed) | 0.034 ± 0.000 | 0.047 ± 0.032 | 0.083 ± 0.002 | 0.065 ± 0.001 | 0.058 ± 0.022 |
| experiments completed | 9 ± 0 | 88 ± 8 | 136 ± 33 | 278 ± 4 | 690 ± 46 |
| completed, planner-proposed | 9 ± 0 | 88 ± 8 | 136 ± 33 | 278 ± 4 | 690 ± 46 |
| share proposed by the exploit engine | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| failed | 1 ± 0 | 16 ± 0 | 26 ± 13 | 53 ± 20 | 100 ± 37 |
| unique hypotheses | 10 ± 0 | 93 ± 1 | 142 ± 48 | 293 ± 24 | 763 ± 64 |
| unique hypotheses, planner-proposed | 10 ± 0 | 93 ± 1 | 142 ± 48 | 293 ± 24 | 763 ± 64 |
| duplicates skipped | 0 ± 0 | 0 ± 1 | 0 ± 0 | 0 ± 0 | 44 ± 12 |
| CPU hours | 0.001 ± 0.000 | 0.035 ± 0.023 | 0.040 ± 0.012 | 0.140 ± 0.078 | 0.591 ± 0.328 |
| wall minutes | 2.1 ± 0.0 | 20.0 ± 0.0 | 20.4 ± 0.2 | 20.3 ± 0.4 | 20.5 ± 0.0 |
| LLM tokens (k, in+out) | 3.9 ± 0.0 | 405.3 ± 13.8 | 681.4 ± 312.9 | 1564.7 ± 96.6 | 2701.5 ± 279.9 |
| cached input share | 0.000 ± 0.000 | 0.234 ± 0.011 | 0.254 ± 0.023 | 0.273 ± 0.012 | 0.240 ± 0.012 |
| worker $ (DeepSeek) | 0.000 ± 0.000 | 0.182 ± 0.015 | 0.341 ± 0.168 | 0.768 ± 0.076 | 1.287 ± 0.125 |
| planner $ (CLI estimate) | 0.000 ± 0.000 | 1.746 ± 0.034 | 2.453 ± 0.978 | 5.581 ± 0.027 | 9.546 ± 0.809 |
| experiments / hour | 394.7 ± 11.7 | 275.9 ± 21.3 | 406.7 ± 111.6 | 836.9 ± 25.2 | 2031.4 ± 135.2 |
| planner-proposed experiments / hour | 394.7 ± 11.7 | 275.9 ± 21.3 | 406.7 ± 111.6 | 836.9 ± 25.2 | 2031.4 ± 135.2 |
| gain per $ | – | 0.035 ± 0.003 | 0.023 ± 0.005 | 0.014 ± 0.001 | 0.009 ± 0.000 |
| gain per CPU-hour | 11.750 ± 0.374 | 2.371 ± 1.411 | 1.586 ± 0.128 | 0.716 ± 0.327 | 0.207 ± 0.135 |
| worker utilisation | 0.027 ± 0.001 | 0.606 ± 0.097 | 0.257 ± 0.089 | 0.326 ± 0.057 | 0.453 ± 0.107 |
| LLM share of worker time | 0.000 ± 0.000 | 0.655 ± 0.068 | 0.690 ± 0.086 | 0.630 ± 0.083 | 0.372 ± 0.116 |

Runs: scripted control (no LLM), 4 workers: scale_control_r0, scale_control_r1, scale_control_r2, scale_control_r3, scale_control_r4, scale_control_r5; claude_cli:opus planner, deepseek:deepseek-flash workers, 1 workers: scale_w1_r0, scale_w1_r1; claude_cli:opus planner, deepseek:deepseek-flash workers, 4 workers: scale_w4_r0, scale_w4_r1; claude_cli:opus planner, deepseek:deepseek-flash workers, 8 workers: scale_w8_r0, scale_w8_r1; claude_cli:opus planner, deepseek:deepseek-flash workers, 16 workers: scale_w16_r0, scale_w16_r1

## Is the ordering real?

- scripted control (no LLM), 4 workers (6 runs): identical results every time, sealed gain 0.0341, visible gain 0.0150. The scripted recipe is deterministic on this dataset, so this control is a fixed-recipe reference, not a noise reference.
- scripted control (no LLM), 4 workers ended after 2.1 min on average (its hypotheses ran out) against 20.3 min for the agent arms, so it is not an equal-time arm: it shows what the fixed template features give, not what a no-LLM search of the same length gives.
- 1 vs 4 workers (claude_cli:opus planner, deepseek:deepseek-flash workers): sealed gain 0.0467 ± 0.0316 vs 0.0826 ± 0.0021, difference +0.0359; p = 0.35 (Welch), does not exceed run-to-run noise.
- 1 vs 8 workers (claude_cli:opus planner, deepseek:deepseek-flash workers): sealed gain 0.0467 ± 0.0316 vs 0.0646 ± 0.0015, difference +0.0179; p = 0.57 (Welch), does not exceed run-to-run noise.
- 1 vs 16 workers (claude_cli:opus planner, deepseek:deepseek-flash workers): sealed gain 0.0467 ± 0.0316 vs 0.0576 ± 0.0218, difference +0.0109; p = 0.73 (Welch), does not exceed run-to-run noise.
- 4 vs 8 workers (claude_cli:opus planner, deepseek:deepseek-flash workers): sealed gain 0.0826 ± 0.0021 vs 0.0646 ± 0.0015, difference -0.0180; p = 0.01 (Welch), exceeds run-to-run noise.
- 4 vs 16 workers (claude_cli:opus planner, deepseek:deepseek-flash workers): sealed gain 0.0826 ± 0.0021 vs 0.0576 ± 0.0218, difference -0.0250; p = 0.35 (Welch), does not exceed run-to-run noise.
- 8 vs 16 workers (claude_cli:opus planner, deepseek:deepseek-flash workers): sealed gain 0.0646 ± 0.0015 vs 0.0576 ± 0.0218, difference -0.0070; p = 0.73 (Welch), does not exceed run-to-run noise.
- A difference that does not exceed noise with two repeats needs more runs before any ordering is claimed; each extra 20-minute repeat costs about the worker $ shown above in DeepSeek spend.
