# RUN SUMMARY

Run `adamson_cf_d1_ds_w4_r2_discovery` on dataset `adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`, code `23b3b1281f`)

- Duration: 20.3 min
- Workers: 4
- Experiments proposed: 519
- Experiments completed: 513 (plus baselines; deepseek:deepseek-v4-pro: 43, python:exploit: 470)
- Experiments failed / rejected / killed / not started: 1 / 0 / 0 / 1
- Unique hypotheses: 519 (replicated: 0); duplicate configurations skipped: 4
- CPU hours: 0.0434
- LLM (worker): 46 calls, 82106 in / 31361 out / 53760 cached tokens, $0.0465
- LLM (planner): 6 calls, 31031 in / 15380 out / 8448 cached tokens, $0.0911

## BASELINE PERFORMANCE
EXP_0003: OLS on baseline features (control mean, mean response, target indicator). pearson_delta = 0.5013

## BEST PERFORMANCE
EXP_0199: pearson_delta = 0.5056 (ridge, alpha=0.000388)

## IMPROVEMENT
0.0043 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- mean_response: coefficient +0.0431
- target_control_std_interaction_e63: coefficient -0.0110
- is_target: coefficient +0.0035
- ppi_erythroid_neighbor_transfer_e56: coefficient -0.0006
- protein_localization_e24[2]: coefficient +0.0005
- protein_localization_e24[1]: coefficient -0.0004
- protein_localization_e24[4]: coefficient +0.0004
- protein_localization_e24[9]: coefficient +0.0003
- protein_localization_e24[10]: coefficient -0.0003
- protein_localization_e24[11]: coefficient +0.0003
- amino_acid_composition_e68[3]: coefficient -0.0003
- protein_localization_e24[3]: coefficient +0.0003
- amino_acid_composition_e68[1]: coefficient -0.0003
- erythroid_program_score_e67: coefficient -0.0002
- protein_localization_e24[6]: coefficient +0.0002
- protein_localization_e24[0]: coefficient -0.0001
- protein_localization_e24[8]: coefficient +0.0001
- promoter_cpg_gc_e33[1]: coefficient -0.0001
- promoter_cpg_gc_features_e61[1]: coefficient -0.0001
- amino_acid_composition_e68[0]: coefficient +0.0001
- protein_localization_e24[7]: coefficient -0.0001
- promoter_cpg_gc_e33[0]: coefficient +0.0000
- amino_acid_composition_e68[2]: coefficient +0.0000
- promoter_cpg_gc_features_e61[0]: coefficient +0.0000
- protein_localization_e24[5]: coefficient +0.0000

## DISCOVERY LINEAGE
EXP_0003 [baseline] score 0.5013
    ↳ EXP_0014 [protein_compartment_flags_e14] score 0.5018
        ↳ EXP_0024 [protein_localization_e24] score 0.5020
            ↳ EXP_0031 [config] score 0.5025
                ↳ EXP_0040 [config] score 0.5025
                    ↳ EXP_0063 [target_control_std_interaction_e63] score 0.5056
                        ↳ EXP_0075 [config] score 0.5056
                            ↳ EXP_0077 [config] score 0.5056
                                ↳ EXP_0081 [config] score 0.5056
                                    ↳ EXP_0096 [config] score 0.5056
                                        ↳ EXP_0098 [config] score 0.5056
                                            ↳ EXP_0108 [config] score 0.5056
                                                ↳ EXP_0109 [config] score 0.5056
                                                    ↳ EXP_0113 [config] score 0.5056
                                                        ↳ EXP_0117 [config] score 0.5056
                                                            ↳ EXP_0131 [config] score 0.5056
                                                                ↳ EXP_0147 [config] score 0.5056
                                                                    ↳ EXP_0149 [config] score 0.5056
                                                                        ↳ EXP_0157 [config] score 0.5056
                                                                            ↳ EXP_0174 [config] score 0.5056
                                                                                ↳ EXP_0199 [config] score 0.5056

## MOST USEFUL FEATURES
- target_control_std_interaction_e63 (EXP_0063): +0.0031. Product of is_target and control_std for gene g.
- protein_compartment_flags_e14 (EXP_0014): +0.0005. Binary protein localization compartment flags per gene from protein_annotation.
- protein_localization_e24 (EXP_0024): +0.0002. Per-gene numeric protein subcellular localization profile from UniProt protein_annotation: compartment flags plus a few structural localization indicators (signal peptide, transmembrane count, secreted/membrane).
- secretory_pathway_features_e36 (EXP_0036): +0.0001. Per-gene protein annotation features: has_signal_peptide, signal_peptide_length, n_transmembrane.
- promoter_cpg_gc_e33 (EXP_0033): +0.0000. Standardized promoter GC content and CpG observed/expected ratio per gene.
- protein_length_signal_peptide_e46 (EXP_0046): +0.0000. Standardized protein_length and signal_peptide_length per gene from protein_annotation.

## FEATURES THAT DID NOT HELP
- control_std_e8: -0.0000
- coexpression_transfer_e9: -0.0003
- erythroid_membership_e10: -0.0000
- prior_network_neighbor_response_e11: -0.0000
- gene_length_features_e12: -0.0000
- loeuf_e13: -0.0001
- erythroid_program_membership_e20: -0.0001
- control_std_e21: -0.0000
- gene_span_intron_length_e22: -0.0000
- lof_intolerance_e23: -0.0000
- tf_target_membership_e25: -0.0000
- prior_network_transfer_e26: -0.0000
- gene_corr_transfer_e27: -0.0003
- ppi_neighbor_response_e32: -0.0000
- tf_target_membership_e34: -0.0001
- transcript_utr_features_e35: -0.0001
- erythroid_score_e39: -0.0000
- ppi_neighbor_response_transfer_e44: -0.0000
- transcript_complexity_e45: -0.0002
- missense_constraint_e47: -0.0001
- erythroid_tf_target_membership_e48: -0.0000
- gene_annotation_random_projection_e51: -0.0003
- ppi_erythroid_neighbor_transfer_e56: -0.0000
- missense_constraint_features_e57: -0.0001
- transcript_utr_complexity_e58: -0.0002
- amino_acid_composition_features_e59: -0.0002
- protein_length_feature_e60: -0.0000
- promoter_cpg_gc_features_e61: -0.0000
- erythroid_program_score_e67: -0.0000
- amino_acid_composition_e68: -0.0000
- missense_constraint_gene_e69: -0.0000
- ppi_neighbor_response_e70: -0.0000
- target_protein_length_e71: -0.0000
- gene_constraint_random_projection_e74: -0.0002

## FAILED FEATURES
- EXP_0015 tf_target_membership_e15 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)

## SURPRISING RESULTS
- none

## ENSEMBLE FINALIST
EXP_0525: average of EXP_0199, EXP_0211, EXP_0204 scores 0.5056 on the visible perturbations (query-only 0.5313). It is a finalist, not the best single model; the union of its members' features is listed in summary.json.

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0525 | ensemble | 0.5056 | 0.5313 | -0.0257 |
| EXP_0199 | config | 0.5056 | 0.5313 | -0.0257 |
| EXP_0211 | config | 0.5056 | 0.5313 | -0.0257 |
| EXP_0204 | config | 0.5056 | 0.5313 | -0.0257 |
| EXP_0003 | baseline | 0.5013 | 0.5196 | -0.0183 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0525 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.124 / 0.150 | 0.948 / 0.937 | 0.826 / 0.744 |
| EXP_0199 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.124 / 0.150 | 0.948 / 0.937 | 0.826 / 0.744 |
| EXP_0211 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.124 / 0.150 | 0.948 / 0.937 | 0.826 / 0.744 |
| EXP_0204 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.124 / 0.150 | 0.948 / 0.937 | 0.826 / 0.744 |
| EXP_0003 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.127 / 0.154 | 0.944 / 0.932 | 0.821 / 0.734 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0525 | 0.142 / 0.115 | 0.659 / 0.667 | 0.315 / 0.286 | 0.888 / 0.927 | 0.811 / 0.840 | 0.934 / 0.957 |
| EXP_0199 | 0.142 / 0.115 | 0.659 / 0.667 | 0.315 / 0.286 | 0.888 / 0.927 | 0.811 / 0.840 | 0.934 / 0.957 |
| EXP_0211 | 0.142 / 0.115 | 0.659 / 0.667 | 0.315 / 0.286 | 0.888 / 0.927 | 0.811 / 0.840 | 0.934 / 0.957 |
| EXP_0204 | 0.142 / 0.115 | 0.659 / 0.667 | 0.315 / 0.286 | 0.888 / 0.927 | 0.811 / 0.840 | 0.934 / 0.957 |
| EXP_0003 | 0.138 / 0.111 | 0.659 / 0.666 | 0.314 / 0.284 | 0.890 / 0.929 | 0.814 / 0.844 | 0.934 / 0.957 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0525 | 0.509 / 0.487 | 0.007 / 0.008 | 0.536 / 0.524 | 0.331 / 0.290 | 0.866 / 0.903 |
| EXP_0199 | 0.509 / 0.487 | 0.007 / 0.008 | 0.536 / 0.524 | 0.331 / 0.290 | 0.866 / 0.903 |
| EXP_0211 | 0.509 / 0.487 | 0.007 / 0.008 | 0.536 / 0.524 | 0.331 / 0.290 | 0.866 / 0.903 |
| EXP_0204 | 0.509 / 0.487 | 0.007 / 0.008 | 0.536 / 0.524 | 0.331 / 0.290 | 0.866 / 0.903 |
| EXP_0003 | 0.504 / 0.477 | 0.007 / 0.008 | 0.536 / 0.526 | 0.361 / 0.280 | 0.863 / 0.903 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1516.59
- Mean CPU s/experiment: 0.3
- Gain per CPU-hour: 0.0996
- Gain per USD: 0.0314
- LLM cost per completed experiment: $0.00027

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r2_discovery --experiment EXP_0199`
