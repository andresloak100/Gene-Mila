# Scaling analysis: demo_claude_w4 (4 workers, 5.6 min)

## 1. Independence
- distinct workers used: 4; max concurrent experiments: 4
- every LLM-written feature in its own worktree commit: True; experiments touched by >1 worker: none
- W000: ['EXP_0006', 'EXP_0011', 'EXP_0012', 'EXP_0015', 'EXP_0016', 'EXP_0017', 'EXP_0018', 'EXP_0019', 'EXP_0020', 'EXP_0022', 'EXP_0024', 'EXP_0026', 'EXP_0033'] (5 LLM calls)
- W001: ['EXP_0008', 'EXP_0021', 'EXP_0023', 'EXP_0034'] (4 LLM calls)
- W002: ['EXP_0007', 'EXP_0010', 'EXP_0014', 'EXP_0025', 'EXP_0028', 'EXP_0029', 'EXP_0030', 'EXP_0031', 'EXP_0032'] (4 LLM calls)
- W003: ['EXP_0009', 'EXP_0013', 'EXP_0027'] (4 LLM calls)

## 2-3. Experiments
| id | worker | status | feature / change | score | delta | LLM calls | cost |
|---|---|---|---|---|---|---|---|
| EXP_0006 | W000 | completed | target_coexpression_e6 | 0.7633 | +0.1579 | 1 | $0.03393 |
| EXP_0007 | W002 | completed | target_coexpression_e7 | 0.7633 | +0.1579 | 1 | $0.03127 |
| EXP_0008 | W001 | completed | knn_response_transfer_e8 | 0.7294 | +0.1240 | 1 | $0.06178 |
| EXP_0009 | W003 | completed | knn_response_transfer_e9 | 0.7294 | +0.1240 | 1 | $0.08080 |
| EXP_0010 | W002 | completed | network_diffusion_effect_e10 | 0.6589 | +0.0535 | 1 | $0.05606 |
| EXP_0011 | W000 | completed | same_module_x_mean_response_e11 | 0.6733 | +0.0679 | 1 | $0.04504 |
| EXP_0012 | W000 | completed | knockdown_regression_effect_e12 | 0.7620 | +0.1566 | 1 | $0.04393 |
| EXP_0013 | W003 | completed | knockdown_regression_effect_e13 | 0.7620 | +0.1566 | 1 | $0.06699 |
| EXP_0014 | W002 | completed | control_logvar_x_mean_response_e14 | 0.6053 | -0.0002 | 1 | $0.03760 |
| EXP_0015 | W000 | completed | Ridge alpha = 100 shrinks the coefficients too muc | 0.6054 | -0.0000 | 0 | $0.00000 |
| EXP_0016 | W000 | completed | Ridge alpha = 100 shrinks the coefficients too muc | 0.6054 | -0.0000 | 0 | $0.00000 |
| EXP_0017 | W000 | completed | Ridge alpha = 100 shrinks the coefficients too muc | 0.6054 | -0.0000 | 0 | $0.00000 |
| EXP_0018 | W000 | completed | Ridge alpha = 100 shrinks the coefficients too muc | 0.6054 | -0.0000 | 0 | $0.00000 |
| EXP_0019 | W000 | completed | Ridge alpha = 100 shrinks the coefficients too muc | 0.6054 | +0.0000 | 0 | $0.00000 |
| EXP_0020 | W000 | completed | Ridge alpha = 100 shrinks the coefficients too muc | 0.6054 | +0.0000 | 0 | $0.00000 |
| EXP_0021 | W001 | completed | glasso_partial_corr_target_e21 | 0.6195 | +0.0141 | 1 | $0.05652 |
| EXP_0022 | W000 | completed | Adding knn_response_transfer_e8 to the EXP_0007 fe | 0.7683 | +0.0050 | 0 | $0.00000 |
| EXP_0023 | W001 | completed | pca_program_coupling_e23 | 0.7636 | +0.0003 | 1 | $0.05155 |
| EXP_0024 | W000 | completed | target_knockdown_scaled_e24 | 0.7769 | +0.0136 | 1 | $0.02510 |
| EXP_0025 | W002 | completed | coresponse_propagated_coexp_e25 | 0.7603 | -0.0030 | 1 | $0.06259 |
| EXP_0026 | W000 | completed | tf_gated_coexpression_e26 | 0.7775 | +0.0007 | 1 | $0.04934 |
| EXP_0027 | W003 | failed | dropout_x_coexpression_e27 |  |  | 2 | $0.09674 |
|  |  | ↳ | feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation G0000_KO depend on its own label (use ctx.train_delta(exclude=p)) |  |  |  |  |
| EXP_0028 | W002 | completed | With the EXP_0007 feature set, a different ridge a | 0.7633 | +0.0000 | 0 | $0.00000 |
| EXP_0029 | W002 | completed | With the EXP_0007 feature set, a different ridge a | 0.7633 | +0.0000 | 0 | $0.00000 |
| EXP_0030 | W002 | completed | With the EXP_0007 feature set, a different ridge a | 0.7633 | +0.0000 | 0 | $0.00000 |
| EXP_0031 | W002 | completed | With the EXP_0007 feature set, a different ridge a | 0.7633 | -0.0000 | 0 | $0.00000 |
| EXP_0032 | W002 | completed | With the EXP_0007 feature set, a different ridge a | 0.7633 | -0.0000 | 0 | $0.00000 |
| EXP_0033 | W000 | completed | With the EXP_0007 feature set, a different ridge a | 0.7633 | -0.0000 | 0 | $0.00000 |
| EXP_0034 | W001 | completed | loo_gene_coexp_sensitivity_e34 | 0.7774 | +0.0006 | 1 | $0.07608 |

## 4. Tokens
- workers: 103308 in (0 cached) / 126258 out
- planner: 25351 in (6651 cached) / 10713 out

## 5-7. Cost and throughput
- worker LLM cost: $0.87533; planner: $0.37869
- worker cost per completed experiment: $0.03126
- completed experiments per minute: 4.998

## 8. Bottlenecks and duplicated work
- time: {"worker_llm_latency": 1067.3, "experiment_wall": 1117.3, "experiment_cpu": 38.9, "planner_latency": 120.1, "worker_capacity": 1344.5}
- LLM latency share of experiment time: 96%; worker utilisation: 83%
- replicate group ['EXP_0006', 'EXP_0007']: scores [0.7633, 0.7633] (identical outcome: duplicated work)
- replicate group ['EXP_0008', 'EXP_0009']: scores [0.7294, 0.7294] (identical outcome: duplicated work)
- replicate group ['EXP_0012', 'EXP_0013']: scores [0.762, 0.762]
- no change vs parent: ['EXP_0019', 'EXP_0028', 'EXP_0029', 'EXP_0030']

## 9. Projection (worker LLM cost)
- 8 workers 1h: $18.75
- 8 workers 6h: $112.50
- 16 workers 1h: $37.50
- 16 workers 6h: $225.01
- 44 workers 1h: $103.13
- 44 workers 6h: $618.77
- planner: about $4.06/hour at the measured call rate
- Linear in workers x time from measured worker-LLM spend per worker-minute; the planner is called when the queue runs low, so its cost grows sub-linearly with workers.