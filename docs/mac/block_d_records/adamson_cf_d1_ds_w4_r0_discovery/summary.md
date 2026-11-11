# RUN SUMMARY

Run `adamson_cf_d1_ds_w4_r0_discovery` on dataset `adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`, code `23b3b1281f`)

- Duration: 20.1 min
- Workers: 4
- Experiments proposed: 1016
- Experiments completed: 982 (plus baselines; deepseek:deepseek-v4-pro: 158, python:exploit: 803, sweep(deepseek:deepseek-v4-pro): 21)
- Experiments failed / rejected / killed / not started: 21 / 0 / 0 / 0
- Unique hypotheses: 1012 (replicated: 4); duplicate configurations skipped: 13
- CPU hours: 0.0973
- LLM (worker): 194 calls, 345466 in / 107633 out / 216192 cached tokens, $0.1692
- LLM (planner): 25 calls, 150023 in / 57357 out / 37504 cached tokens, $0.3773

## BASELINE PERFORMANCE
EXP_0003: OLS on baseline features (control mean, mean response, target indicator). pearson_delta = 0.5010

## BEST PERFORMANCE
EXP_0974: pearson_delta = 0.5524 (ridge, alpha=3.3e-05)

## IMPROVEMENT
0.0514 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- train_delta_transfer_similarity_e267: coefficient +0.0617
- mean_response: coefficient -0.0131
- is_target: coefficient -0.0070
- target_er_flag_e11: coefficient +0.0067
- target_gata1_nfe2_x_gene_globin_corr_e211: coefficient -0.0043
- target_aa_k_fraction_e234: coefficient -0.0042
- target_pli_e67: coefficient -0.0041
- gata1_nfe2_network_proximity_e21: coefficient +0.0032
- gata1_nfe2_network_proximity_e113: coefficient -0.0030
- target_gene_constraint_interaction_e54: coefficient +0.0015
- target_globin_sets_similarity_e242: coefficient +0.0014
- cpg_oe_promoter_globin_interaction_e275: coefficient -0.0011
- train_delta_transfer_similarity_weighted_e293: coefficient -0.0010
- target_globin_coexpression_interaction_e255: coefficient -0.0009
- target_g_gene_set_jaccard_e239: coefficient +0.0007
- protein_length_log_e31: coefficient -0.0004
- gene_methionine_fraction_e241: coefficient +0.0003
- target_tf_x_gene_histone_e277: coefficient +0.0001
- aa_cysteine_fraction_e119: coefficient -0.0001
- has_signal_peptide_e70: coefficient +0.0001
- has_signal_peptide_e59: coefficient +0.0001
- protein_length_e42: coefficient +0.0001
- gene_proline_fraction_rank_e248: coefficient -0.0000

## DISCOVERY LINEAGE
EXP_0003 [baseline] score 0.5010
    ↳ EXP_0008 [control_std_e8] score 0.5010
        ↳ EXP_0017 [config] score 0.5014
            ↳ EXP_0033 [config] score 0.5015
                ↳ EXP_0059 [has_signal_peptide_e59] score 0.5020
                    ↳ EXP_0065 [config] score 0.5020
                        ↳ EXP_0079 [gene_target_pli_interaction_e79] score 0.5023
                            ↳ EXP_0089 [aa_l_e87_e89] score 0.5023
                                ↳ EXP_0103 [obs_lof_e98_e103] score 0.5023
                                    ↳ EXP_0108 [config] score 0.5023
                                        ↳ EXP_0120 [config] score 0.5024
                                            ↳ EXP_0124 [config] score 0.5025
                                                ↳ EXP_0128 [config] score 0.5027
                                                    ↳ EXP_0132 [config] score 0.5031
                                                        ↳ EXP_0174 [config] score 0.5031
                                                            ↳ EXP_0211 [target_gata1_nfe2_x_gene_globin_corr_e211] score 0.5041
                                                                ↳ EXP_0218 [config] score 0.5041
                                                                    ↳ EXP_0239 [target_g_gene_set_jaccard_e239] score 0.5044
                                                                        ↳ EXP_0242 [target_globin_sets_similarity_e242] score 0.5044
                                                                            ↳ EXP_0267 [train_delta_transfer_similarity_e267] score 0.5510
                                                                                ↳ EXP_0281 [config] score 0.5510
                                                                                    ↳ EXP_0293 [train_delta_transfer_similarity_weighted_e293] score 0.5514
                                                                                        ↳ EXP_0296 [config] score 0.5516
                                                                                            ↳ EXP_0300 [config] score 0.5516
                                                                                                ↳ EXP_0305 [config] score 0.5516
                                                                                                    ↳ EXP_0306 [config] score 0.5516
                                                                                                        ↳ EXP_0310 [config] score 0.5516
                                                                                                            ↳ EXP_0314 [config] score 0.5516
                                                                                                                ↳ EXP_0318 [config] score 0.5516
                                                                                                                    ↳ EXP_0322 [config] score 0.5516
                                                                                                                        ↳ EXP_0326 [config] score 0.5516
                                                                                                                            ↳ EXP_0330 [config] score 0.5516
                                                                                                                                ↳ EXP_0334 [config] score 0.5516
                                                                                                                                    ↳ EXP_0352 [config] score 0.5517
                                                                                                                                        ↳ EXP_0369 [config] score 0.5518
                                                                                                                                            ↳ EXP_0370 [config] score 0.5518
                                                                                                                                                ↳ EXP_0394 [config] score 0.5518
                                                                                                                                                    ↳ EXP_0420 [config] score 0.5518
                                                                                                                                                        ↳ EXP_0445 [config] score 0.5519
                                                                                                                                                            ↳ EXP_0449 [config] score 0.5519
                                                                                                                                                                ↳ EXP_0451 [config] score 0.5521
                                                                                                                                                                    ↳ EXP_0464 [config] score 0.5521
                                                                                                                                                                        ↳ EXP_0466 [config] score 0.5521
                                                                                                                                                                            ↳ EXP_0470 [config] score 0.5521
                                                                                                                                                                                ↳ EXP_0501 [config] score 0.5521
                                                                                                                                                                                    ↳ EXP_0529 [config] score 0.5521
                                                                                                                                                                                        ↳ EXP_0530 [config] score 0.5521
                                                                                                                                                                                            ↳ EXP_0564 [config] score 0.5522
                                                                                                                                                                                                ↳ EXP_0593 [config] score 0.5522
                                                                                                                                                                                                    ↳ EXP_0618 [config] score 0.5522
                                                                                                                                                                                                        ↳ EXP_0622 [config] score 0.5522
                                                                                                                                                                                                            ↳ EXP_0660 [config] score 0.5522
                                                                                                                                                                                                                ↳ EXP_0704 [config] score 0.5522
                                                                                                                                                                                                                    ↳ EXP_0747 [config] score 0.5522
                                                                                                                                                                                                                        ↳ EXP_0809 [config] score 0.5522
                                                                                                                                                                                                                            ↳ EXP_0810 [config] score 0.5522
                                                                                                                                                                                                                                ↳ EXP_0815 [config] score 0.5522
                                                                                                                                                                                                                                    ↳ EXP_0852 [config] score 0.5522
                                                                                                                                                                                                                                        ↳ EXP_0941 [config] score 0.5524
                                                                                                                                                                                                                                            ↳ EXP_0942 [config] score 0.5524
                                                                                                                                                                                                                                                ↳ EXP_0971 [config] score 0.5524
                                                                                                                                                                                                                                                    ↳ EXP_0974 [config] score 0.5524

## MOST USEFUL FEATURES
- train_delta_transfer_similarity_e267 (EXP_0267): +0.0465. Cosine-similarity weighted average of training deltas for gene g, where weights are cosine similarities between the target gene of p and the target genes of training perturbations in gene-set space.
- target_gata1_nfe2_x_gene_globin_corr_e211 (EXP_0211): +0.0010. Product of an indicator that the target of perturbation p is a neighbor of GATA1 or NFE2 in prior_network and the gene's correlation with globin genes.
- has_signal_peptide_e59 (EXP_0059): +0.0004. Indicator that gene g's protein has a signal peptide (protein_annotation).
- train_delta_transfer_similarity_weighted_e293 (EXP_0293): +0.0004. Cosine-similarity weighted average of training deltas, scaled by the target protein's length from protein_annotation.
- gene_target_pli_interaction_e79 (EXP_0079): +0.0003. Interaction between gene g's LoF constraint (pLI) and the target gene t's pLI: product of the two, with median imputation of missing values.
- target_g_gene_set_jaccard_e239 (EXP_0239): +0.0002. Jaccard similarity between gene set memberships of perturbation target and response gene g.
- target_globin_coexpression_interaction_e255 (EXP_0255): +0.0001. For each (p,g), if gene g is a globin gene (HBZ, HBG2, HBA1, HBG1), the control-cell correlation between the perturbation target gene and g; else 0.
- aa_leucine_fraction_e82 (EXP_0082): +0.0001. Fraction of leucine (aa_L) in the protein sequence of gene g.
- target_gene_shared_compartment_e23 (EXP_0023): +0.0001. Binary indicator: 1 if the target of perturbation p and gene g share at least one subcellular localization flag from protein_annotation, else 0.
- target_globin_sets_similarity_e242 (EXP_0242): +0.0001. Jaccard similarity between the target gene's gene-set memberships and the union of globin-gene gene sets, broadcast to all genes.

## FEATURES THAT DID NOT HELP
- gene_intron_length_e10: -0.0000
- globin_set_membership_e12: -0.0001
- target_gc_x_control_mean_e15: -0.0001
- co2_transport_membership_e22: -0.0001
- intron_length_kb_e25: -0.0000
- coexpr_with_target_e28: -0.0037
- is_prior_neighbor_of_target_e29: -0.0001
- target_n_transcripts_e39: -0.0000
- gene_span_kb_e40: -0.0001
- n_transcripts_e41: -0.0001
- loeuf_e44: -0.0001
- target_gene_constraint_interaction_e54: -0.0003
- transcript_length_log_e55: -0.0002
- utr3_length_e56: -0.0001
- n_exons_e57: -0.0001
- protein_length_log_e58: -0.0000
- cds_length_e68: -0.0000
- utr3_length_e69: -0.0001
- control_coexpr_with_target_e73: -0.0065
- cds_length_log_e80: -0.0001
- gc_utr3_e81: -0.0001
- target_mis_z_interaction_e83: -0.0001
- target_n_upstream_atg_interaction_e85: -0.0005
- n_upstream_atg_e85_e87: -0.0000
- gc_utr3_e86_e88: -0.0000
- oe_lof_e88_e90: -0.0005
- mis_z_e89_e91: -0.0004
- utr5_length_e94_e99: -0.0000
- cpg_oe_promoter_e95_e100: -0.0000
- oe_mis_e96_e101: -0.0002
- syn_z_e97_e102: -0.0000
- co2_transport_membership_e112: -0.0001
- gata1_nfe2_network_proximity_e113: -0.0000
- syn_z_e115: -0.0000
- utr5_length_e116: -0.0000
- nearest_tss_kb_e117: -0.0000
- n_tss_within_100kb_e118: -0.0001
- gene_corr_with_residual_genes_e141: -0.0042
- gene_set_overlap_with_target_e143: -0.0007
- aa_histidine_fraction_e144: -0.0008
- gene_constraint_oe_lof_upper_bin_e145: -0.0013
- control_std_x_target_loeuf_e147: -0.0012
- globin_histone_corr_similarity_e152: -0.0010
- target_set_count_x_control_std_e153: -0.0008
- ppi_distance_to_residual_genes_e154: -0.0008
- aa_cysteine_x_target_loeuf_e155: -0.0017
- target_pli_x_control_mean_e156: -0.0016
- gene_exp_lof_x_target_pli_e165: -0.0008
- gene_oe_lof_lower_x_target_loeuf_e166: -0.0006
- gene_pnull_x_target_pli_e167: -0.0012
- gene_oe_mis_upper_x_target_oe_mis_e168: -0.0008
- gene_lof_z_x_target_pli_e169: -0.0009
- target_lof_z_x_control_std_e175: -0.0013
- target_exp_lof_x_intron_length_e176: -0.0008
- aa_d_fraction_e177: -0.0008
- aa_g_fraction_e178: -0.0008
- aa_f_fraction_e179: -0.0007
- target_pnull_x_control_mean_e180: -0.0032
- target_residual_gene_set_overlap_e182: -0.0007
- gene_corr_with_residual_set_e182_e184: -0.0011
- signal_peptide_length_e183_e185: -0.0007
- aa_aspartic_fraction_e184_e186: -0.0008
- aa_glutamic_fraction_e185_e187: -0.0007
- target_residual_set_overlap_e186_e188: -0.0007
- ppi_distance_to_residual_genes_e187_e189: -0.0007
- aa_q_fraction_e192_e193: -0.0008
- signal_peptide_length_e193_e194: -0.0007
- gene_corr_with_globin_e194_e195: -0.0009
- target_gata1_nfe2_neighbor_e195_e196: -0.0008
- aa_i_fraction_e196_e197: -0.0007
- gene_corr_with_globin_e210: -0.0035
- gene_in_co2_transport_e212: -0.0009
- gene_is_histone_e213: -0.0007
- target_residual_set_overlap_e214: -0.0007
- target_is_gata1_nfe2_neighbor_e217: -0.0008
- target_gene_shared_prior_neighbors_e222: -0.0009
- gene_corr_with_globin_set_e224: -0.0009
- gene_corr_with_globin_set_e225: -0.0009
- target_aa_k_fraction_e228: -0.0008
- gene_aa_r_fraction_e229: -0.0008
- target_cpg_promoter_x_gene_intron_length_e232: -0.0009
- target_aa_r_fraction_e233: -0.0000
- target_aa_k_fraction_e234: -0.0001
- target_aa_p_fraction_e235: -0.0001
- target_aa_t_fraction_e237: -0.0001
- gene_tryptophan_fraction_e243: -0.0001
- target_loeuf_x_gene_globin_corr_e244: -0.0001
- gene_asparagine_fraction_e245: -0.0001
- gene_proline_fraction_rank_e248: -0.0000
- target_gene_aa_w_interaction_e249: -0.0000
- target_gene_aa_n_interaction_e250: -0.0000
- target_gene_aa_m_interaction_e251: -0.0003
- target_gene_aa_v_interaction_e252: -0.0008
- target_gene_aa_a_interaction_e253: -0.0000
- target_gene_aa_y_interaction_e254: -0.0001
- target_gene_control_corr_e261: -0.0035
- target_tf_gene_corr_e262: -0.0035
- target_gene_aa_a_interaction_e263: -0.0000
- target_gene_aa_v_interaction_e264: -0.0008
- target_gene_aa_y_interaction_e265: -0.0001
- target_gene_control_dist_sim_e266: -0.0002
- target_gene_ppi_shortest_path_e268: -0.0004
- target_globin_corr_gene_corr_e273: -0.0002
- target_globin_train_delta_similarity_e274: -0.0006
- target_cpg_oe_promoter_x_globin_gene_e276: -0.0001
- target_gene_control_corr_e286: -0.0046
- target_protein_length_x_gene_length_e287: -0.0000
- target_control_std_x_gene_control_std_e291: -0.0004

## FAILED FEATURES
- EXP_0014 prior_network_similarity_e14 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0026 target_ppi_degree_e26 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AMIGO3 depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0027 tf_target_network_similarity_e27 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0030 target_is_tf_e30 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0045 target_is_tf_e45 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AMIGO3 depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0060 target_tf_response_neighbor_e60 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0071 target_gata1_nfe2_neighbor_e71 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0078 tf_target_interaction_e78 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0106 co2_target_gata1_interaction_e99_e106 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0107 co2_target_gata1_interaction_e99_e107 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0140 gata1_nfe2_target_similarity_e140 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0142 target_gene_ppi_shared_partners_e142 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0172 target_mito_set_similarity_e172 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0223 target_gene_shared_prior_neighbors_e223 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0226 target_gene_shared_residual_sets_count_e226 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0227 target_gene_shared_residual_sets_count_e227 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0230 target_gene_shared_domain_sets_e230 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0238 target_g_shared_prior_neighbors_e238 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0280 target_mitochondrial_set_x_globin_gene_e280 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0289 target_residual_gene_network_proximity_e289 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0290 target_er_stress_set_similarity_e290 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)

## SURPRISING RESULTS
- none

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0974 | config | 0.5524 | 0.5679 | -0.0156 |
| EXP_0942 | config | 0.5524 | 0.5679 | -0.0156 |
| EXP_0993 | config | 0.5524 | 0.5679 | -0.0156 |
| EXP_0003 | baseline | 0.5010 | 0.5196 | -0.0186 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0974 | 0.005 / 0.006 | 0.988 / 0.987 | 0.975 / 0.971 | 0.102 / 0.122 | 0.952 / 0.944 | 0.856 / 0.786 |
| EXP_0942 | 0.005 / 0.006 | 0.988 / 0.987 | 0.975 / 0.971 | 0.102 / 0.122 | 0.952 / 0.944 | 0.856 / 0.786 |
| EXP_0993 | 0.005 / 0.006 | 0.988 / 0.987 | 0.975 / 0.971 | 0.102 / 0.122 | 0.952 / 0.944 | 0.856 / 0.786 |
| EXP_0003 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.127 / 0.154 | 0.944 / 0.932 | 0.821 / 0.734 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0974 | 0.356 / 0.360 | 0.702 / 0.735 | 0.380 / 0.427 | 0.895 / 0.931 | 0.816 / 0.846 | 0.945 / 0.962 |
| EXP_0942 | 0.356 / 0.360 | 0.702 / 0.735 | 0.380 / 0.427 | 0.895 / 0.931 | 0.816 / 0.846 | 0.945 / 0.962 |
| EXP_0993 | 0.356 / 0.360 | 0.702 / 0.735 | 0.380 / 0.427 | 0.895 / 0.931 | 0.816 / 0.846 | 0.945 / 0.962 |
| EXP_0003 | 0.138 / 0.111 | 0.659 / 0.666 | 0.314 / 0.284 | 0.890 / 0.929 | 0.814 / 0.844 | 0.934 / 0.957 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0974 | 0.530 / 0.510 | 0.007 / 0.007 | 0.664 / 0.599 | 0.405 / 0.310 | 0.872 / 0.933 |
| EXP_0942 | 0.530 / 0.510 | 0.007 / 0.007 | 0.664 / 0.599 | 0.405 / 0.310 | 0.872 / 0.933 |
| EXP_0993 | 0.530 / 0.510 | 0.007 / 0.007 | 0.664 / 0.599 | 0.405 / 0.310 | 0.872 / 0.933 |
| EXP_0003 | 0.504 / 0.477 | 0.007 / 0.008 | 0.536 / 0.526 | 0.361 / 0.280 | 0.863 / 0.903 |

## COMPUTE EFFICIENCY
- Experiments/hour: 2935.95
- Mean CPU s/experiment: 0.36
- Gain per CPU-hour: 0.5276
- Gain per USD: 0.0940
- LLM cost per completed experiment: $0.00056

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r0_discovery --experiment EXP_0974`
