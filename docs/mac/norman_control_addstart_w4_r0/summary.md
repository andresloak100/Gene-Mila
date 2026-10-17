# RUN SUMMARY

Run `norman_control_addstart_w4_r0` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `ce1b530431`)

- Duration: 16.7 min
- Workers: 4
- Experiments proposed: 1008
- Experiments completed: 991 (plus baselines; python:exploit: 974, scripted:scripted: 15, sweep(scripted:scripted): 2)
- Experiments failed / rejected / killed / not started: 0 / 0 / 0 / 0
- Unique hypotheses: 990 (replicated: 1); duplicate configurations skipped: 17
- CPU hours: 0.2091
- LLM (worker): 12 calls, 7787 in / 5993 out / 0 cached tokens, $0.0000
- LLM (planner): 0 calls, 0 in / 0 out / 0 cached tokens, $0.0000

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6108

## BEST PERFORMANCE
EXP_0157: pearson_delta = 0.6423 (ridge, alpha=0.0)

## IMPROVEMENT
0.0314 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_singles_e20: coefficient +11755418364.9839
- additive_response: coefficient -11755418364.9126
- response_components_e19[0]: coefficient +0.0192
- response_components_e19[1]: coefficient +0.0158
- response_components_e19[3]: coefficient +0.0074
- response_components_e19[2]: coefficient +0.0066
- is_target: coefficient +0.0056
- target_level_e16: coefficient +0.0026
- external_direct_replogle2022_k562_e21: coefficient +0.0018
- prior_network_edge_e13: coefficient +0.0006

## DISCOVERY LINEAGE
EXP_0007 [baseline] score 0.6154
    ↳ EXP_0019 [response_components_e19] score 0.6353
        ↳ EXP_0037 [config] score 0.6377
            ↳ EXP_0045 [config] score 0.6382
                ↳ EXP_0047 [config] score 0.6382
                    ↳ EXP_0051 [config] score 0.6382
                        ↳ EXP_0055 [config] score 0.6382
                            ↳ EXP_0060 [config] score 0.6382
                                ↳ EXP_0064 [config] score 0.6382
                                    ↳ EXP_0068 [config] score 0.6382
                                        ↳ EXP_0072 [config] score 0.6382
                                            ↳ EXP_0079 [config] score 0.6413
                                                ↳ EXP_0091 [config] score 0.6422
                                                    ↳ EXP_0096 [config] score 0.6422
                                                        ↳ EXP_0110 [config] score 0.6422
                                                            ↳ EXP_0121 [config] score 0.6423
                                                                ↳ EXP_0157 [config] score 0.6423

## MOST USEFUL FEATURES
- response_components_e19 (EXP_0019): +0.0199. Low-rank response components of the training perturbations (leave-one-out SVD of their centred delta profiles); p's weight on each component is predicted by kernel ridge from its target's annotations (gene-set memberships, protein interactions, TF-network partners). One column per component.
- external_direct_replogle2022_k562_e21 (EXP_0021): +0.0037. External screen response of p's target (knowledge file replogle2022_k562): the change of gene g measured for the same target gene in another screen of the cell line (for a pair, the sum of its genes' rows), times the file's sign; 0 where unmeasured or without a row.
- external_krr_replogle2022_k562_e23 (EXP_0023): +0.0029. Kernel transfer through an external screen (knowledge file replogle2022_k562): kernel ridge regression over the other training perturbations' responses, kernel = Pearson correlation between the external responses of their targets, so p's response is the mean training response plus a signed mix of the others' deviations from it; lambda chosen by leave-one-out over those training perturbations; the mean training response when p's target has no external row or fewer than 3 training perturbations have one.
- target_level_e16 (EXP_0016): +0.0011. Control mean expression of g if g is the perturbed target, else 0.
- coexpr_target_e12 (EXP_0012): +0.0002. Control-cell correlation between the perturbed target gene and gene g.
- control_variance_e18 (EXP_0018): +0.0001. Control-cell standard deviation of gene g.
- additive_singles_e20 (EXP_0020): +0.0000. Additive model of single-gene responses: the sum over p's target genes of each gene's single-gene training response (the mean response of the other training perturbations whose one target is that gene), with the mean single-gene training response for a gene without one.

## FEATURES THAT DID NOT HELP
- prior_network_edge_e13: -0.0000
- shared_module_e14: -0.0001
- similar_pert_knn_e15: -0.0081
- pca_alignment_e17: -0.0009
- external_knn_replogle2022_k562_e22: -0.0123

## FAILED FEATURES
- none

## SURPRISING RESULTS
- external_knn_replogle2022_k562_e22 made the model worse (-0.0123) despite a linear model being able to ignore it (overfitting or scale issue)

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0157 | config | 0.6423 | 0.7188 | -0.0766 |
| EXP_0190 | config | 0.6423 | 0.7188 | -0.0765 |
| EXP_0202 | config | 0.6423 | 0.7188 | -0.0765 |
| EXP_0003 | baseline | 0.6108 | 0.7126 | -0.1018 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0157 | 0.007 / 0.005 | 0.984 / 0.989 | 0.966 / 0.975 | 0.166 / 0.110 | 0.909 / 0.937 | 0.770 / 0.842 |
| EXP_0190 | 0.007 / 0.005 | 0.984 / 0.989 | 0.966 / 0.975 | 0.166 / 0.110 | 0.909 / 0.937 | 0.770 / 0.842 |
| EXP_0202 | 0.007 / 0.005 | 0.984 / 0.989 | 0.966 / 0.975 | 0.166 / 0.110 | 0.909 / 0.937 | 0.770 / 0.842 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0157 | 0.566 / 0.542 | 0.751 / 0.759 | 0.570 / 0.519 | 0.947 / 0.949 | 0.860 / 0.868 | 0.974 / 0.972 |
| EXP_0190 | 0.565 / 0.542 | 0.751 / 0.759 | 0.570 / 0.519 | 0.947 / 0.949 | 0.860 / 0.868 | 0.974 / 0.972 |
| EXP_0202 | 0.565 / 0.542 | 0.751 / 0.759 | 0.570 / 0.519 | 0.947 / 0.949 | 0.860 / 0.868 | 0.974 / 0.972 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0157 | 0.742 / 0.682 | 0.008 / 0.006 | 0.774 / 0.744 | 0.566 / 0.484 | 0.920 / 0.897 |
| EXP_0190 | 0.742 / 0.682 | 0.008 / 0.006 | 0.774 / 0.744 | 0.566 / 0.484 | 0.920 / 0.897 |
| EXP_0202 | 0.742 / 0.682 | 0.008 / 0.006 | 0.774 / 0.744 | 0.566 / 0.484 | 0.920 / 0.897 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 3558.13
- Mean CPU s/experiment: 0.76
- Gain per CPU-hour: 0.1503
- Gain per USD: n/a
- LLM cost per completed experiment: $0.00000

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_control_addstart_w4_r0 --experiment EXP_0157`
