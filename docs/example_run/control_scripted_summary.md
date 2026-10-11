# RUN SUMMARY

Run `20261004_010043_synthetic_w4` on dataset `synthetic` (split `split_3ad9ac2956087b2f`, code `dee5bb55b0`)

- Duration: 2.0 min
- Workers: 4
- Experiments proposed: 15
- Experiments completed: 13 (plus baselines)
- Experiments failed / rejected / killed / not started: 0 / 0 / 0 / 0
- Unique hypotheses: 12 (replicated: 2); duplicate configurations skipped: 2
- CPU hours: 0.0006
- LLM (worker): 7 calls, 2009 in / 1509 out / 0 cached tokens, $0.0000
- LLM (planner): 8 calls, 0 in / 0 out / 0 cached tokens, $0.0000

## BASELINE PERFORMANCE
EXP_0004: RIDGE on baseline features (control mean, mean response, target indicator). pearson_delta = 0.6054

## BEST PERFORMANCE
EXP_0017: pearson_delta = 0.7702 (ridge, alpha=100.0)

## IMPROVEMENT
0.1648 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- mean_response: coefficient +0.0794
- coexpr_target_e6: coefficient -0.0567
- is_target: coefficient -0.0509
- similar_pert_knn_e9: coefficient +0.0358
- shared_module_e8: coefficient -0.0115
- control_mean: coefficient +0.0008

## DISCOVERY LINEAGE
EXP_0004 [baseline] score 0.6054
    ↳ EXP_0006 [coexpr_target_e6] score 0.7633
        ↳ EXP_0016 [config] score 0.7683
            ↳ EXP_0017 [config] score 0.7702

## MOST USEFUL FEATURES
- coexpr_target_e6 (EXP_0006): +0.1579. Control-cell correlation between the perturbed target gene and gene g.
- similar_pert_knn_e9 (EXP_0009): +0.1240. Response of g averaged over the k training perturbations whose targets are most co-expressed with p's target (leave-one-out).
- pca_alignment_e11 (EXP_0011): +0.1071. Product of target-gene and gene-g loadings on the top control PCs (one column per PC).
- shared_module_e8 (EXP_0008): +0.0679. Fraction of gene sets containing the target that also contain gene g, times control mean of g.
- prior_network_edge_e7 (EXP_0007): +0.0428. Signed prior-network edge from the perturbed gene to gene g, scaled by target expression.
- target_level_e10 (EXP_0010): +0.0336. Control mean expression of g if g is the perturbed target, else 0.
- control_variance_e12 (EXP_0012): +0.0000. Control-cell standard deviation of gene g.

## FEATURES THAT DID NOT HELP
- none

## FAILED FEATURES
- none

## SURPRISING RESULTS
- none

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0017 | config | 0.7702 | 0.7776 | -0.0074 |
| EXP_0016 | config | 0.7683 | 0.7744 | -0.0061 |
| EXP_0015 | config | 0.7666 | 0.7718 | -0.0052 |
| EXP_0004 | baseline | 0.6054 | 0.5942 | +0.0112 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0017 | 0.049 / 0.049 | 0.980 / 0.980 | 0.960 / 0.960 | 0.564 / 0.558 | 0.833 / 0.846 | 0.580 / 0.593 |
| EXP_0016 | 0.049 / 0.050 | 0.980 / 0.980 | 0.959 / 0.960 | 0.571 / 0.565 | 0.833 / 0.846 | 0.574 / 0.587 |
| EXP_0015 | 0.049 / 0.050 | 0.980 / 0.980 | 0.959 / 0.960 | 0.567 / 0.566 | 0.833 / 0.844 | 0.578 / 0.585 |
| EXP_0004 | 0.062 / 0.067 | 0.975 / 0.973 | 0.949 / 0.946 | 0.682 / 0.703 | 0.823 / 0.833 | 0.481 / 0.459 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0017 | 0.647 / 0.780 | 0.883 / 0.933 | 0.661 / 0.826 | 0.939 / 0.955 | 0.879 / 0.906 | 0.957 / 0.965 |
| EXP_0016 | 0.647 / 0.784 | 0.885 / 0.932 | 0.666 / 0.823 | 0.939 / 0.955 | 0.879 / 0.906 | 0.957 / 0.964 |
| EXP_0015 | 0.646 / 0.785 | 0.883 / 0.931 | 0.662 / 0.821 | 0.937 / 0.950 | 0.875 / 0.896 | 0.958 / 0.966 |
| EXP_0004 | 0.436 / 0.518 | 0.712 / 0.714 | 0.439 / 0.528 | 0.863 / 0.880 | 0.742 / 0.773 | 0.912 / 0.919 |

## COMPUTE EFFICIENCY
- Experiments/hour: 538.5
- Mean CPU s/experiment: 0.11
- Gain per CPU-hour: 287.9099
- Gain per USD: n/a
- LLM cost per completed experiment: $0.00000

## REPRODUCTION COMMAND
`python reproduce.py --run runs/20261004_010043_synthetic_w4 --experiment EXP_0017`
