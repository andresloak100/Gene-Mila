# RUN SUMMARY

Run `demo_claude_w4` on dataset `synthetic` (split `split_3ad9ac2956087b2f`, code `7389e25c60`)

- Duration: 5.6 min
- Workers: 4
- Experiments proposed: 29
- Experiments completed: 28 (plus baselines)
- Experiments failed / rejected / killed / not started: 1 / 0 / 0 / 0
- Unique hypotheses: 26 (replicated: 3); duplicate configurations skipped: 0
- CPU hours: 0.0119
- LLM (worker): 17 calls, 103308 in / 126258 out / 0 cached tokens, $0.8753
- LLM (planner): 4 calls, 25351 in / 10713 out / 6651 cached tokens, $0.3787

## BASELINE PERFORMANCE
EXP_0004: RIDGE on baseline features (control mean, mean response, target indicator). pearson_delta = 0.6054

## BEST PERFORMANCE
EXP_0026: pearson_delta = 0.7775 (ridge, alpha=100.0)

## IMPROVEMENT
0.1721 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- mean_response: coefficient +0.1040
- target_knockdown_scaled_e24: coefficient +0.0948
- target_coexpression_e7: coefficient +0.0404
- tf_gated_coexpression_e26[0]: coefficient -0.0305
- tf_gated_coexpression_e26[1]: coefficient -0.0254
- is_target: coefficient +0.0121
- control_mean: coefficient +0.0012

## DISCOVERY LINEAGE
EXP_0004 [baseline] score 0.6054
    ↳ EXP_0007 [target_coexpression_e7] score 0.7633
        ↳ EXP_0024 [target_knockdown_scaled_e24] score 0.7769
            ↳ EXP_0026 [tf_gated_coexpression_e26] score 0.7775

## MOST USEFUL FEATURES
- target_coexpression_e6 (EXP_0006): +0.1579. Pearson correlation between target gene and gene g in control cells, negated for KO
- target_coexpression_e7 (EXP_0007): +0.1579. Pearson correlation across control cells between expression of p's target gene and gene g, multiplied by -1 to reflect a KO (0 if the target is not measured)
- knockdown_regression_effect_e13 (EXP_0013): +0.1566. Knockdown regression effect: slope of gene g on target t, multiplied by expected loss of t's expression
- knockdown_regression_effect_e12 (EXP_0012): +0.1566. Control-cell regression slope of gene g on target t, multiplied by expected loss of t's expression.
- knn_response_transfer_e8 (EXP_0008): +0.1240. Weighted mean of delta from k most similar training perturbations by target co-expression
- knn_response_transfer_e9 (EXP_0009): +0.1240. Weighted mean of deltas from k training perturbations whose targets are most co-expressed with p's target
- same_module_x_mean_response_e11 (EXP_0011): +0.0679. Indicator that gene g shares a module with p's target, and its interaction with mean_response.
- network_diffusion_effect_e10 (EXP_0010): +0.0535. Signed propagated effect of perturbation through prior regulatory network
- glasso_partial_corr_target_e21 (EXP_0021): +0.0141. Partial correlation between target t and gene g from graphical-lasso precision matrix on control cells, times -control_mean(t)
- target_knockdown_scaled_e24 (EXP_0024): +0.0136. Scaled knockdown effect: -control_mean[g] if g is a target of p, else 0.

## FEATURES THAT DID NOT HELP
- control_logvar_x_mean_response_e14: -0.0002
- coresponse_propagated_coexp_e25: -0.0030

## FAILED FEATURES
- EXP_0027 dropout_x_coexpression_e27 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation G0000_KO depend on its own label (use ctx.train_delta(exclude=p))

## SURPRISING RESULTS
- none

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0026 | new_feature | 0.7775 | 0.7764 | +0.0011 |
| EXP_0034 | new_feature | 0.7774 | 0.7757 | +0.0017 |
| EXP_0024 | new_feature | 0.7769 | 0.7750 | +0.0019 |
| EXP_0004 | baseline | 0.6054 | 0.5942 | +0.0112 |

## COMPUTE EFFICIENCY
- Experiments/hour: 353.53
- Mean CPU s/experiment: 1.3
- Gain per CPU-hour: 14.4302
- Gain per USD: 0.1373
- LLM cost per completed experiment: $0.03800

## REPRODUCTION COMMAND
`python reproduce.py --run /home/claude/gene-mila/runs/demo_claude_w4 --experiment EXP_0026`
