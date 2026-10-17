# RUN SUMMARY

Run `norman_ds_from_n2_w4_r3` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `076282c71b`)

- Duration: 20.0 min
- Workers: 4
- Experiments proposed: 591
- Experiments completed: 447 (plus baselines; deepseek:deepseek-v4-pro: 279, python:exploit: 81, python:warm_start: 1, sweep(deepseek:deepseek-v4-pro): 86)
- Experiments failed / rejected / killed / not started: 74 / 9 / 0 / 0
- Unique hypotheses: 580 (replicated: 11); duplicate configurations skipped: 54
- CPU hours: 0.3409
- LLM (worker): 455 calls, 807281 in / 360850 out / 379648 cached tokens, $0.5636
- LLM (planner): 52 calls, 273266 in / 108430 out / 78208 cached tokens, $0.6903

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6148

## BEST PERFORMANCE
EXP_0519: pearson_delta = 0.6484 (ridge, alpha=300.0)

## IMPROVEMENT
0.0336 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- response_components_e14[0]: coefficient +0.0220
- response_components_e14[1]: coefficient +0.0173
- additive_singles_random_fourier_e449[6]: coefficient +0.0142
- best_model_residual_e213_e247: coefficient -0.0136
- additive_singles_random_fourier_e449[0]: coefficient -0.0123
- additive_singles_random_fourier_e449[4]: coefficient +0.0114
- response_components_e14[3]: coefficient +0.0079
- pair_shared_tf_count_e312: coefficient +0.0073
- response_components_e14[2]: coefficient +0.0071
- additive_singles_random_fourier_e449[2]: coefficient -0.0069
- additive_singles_random_fourier_e449[9]: coefficient -0.0065
- additive_singles_random_fourier_e449[7]: coefficient -0.0065
- additive_singles_random_fourier_e449[1]: coefficient +0.0064
- additive_singles_random_fourier_e449[5]: coefficient -0.0062
- is_target: coefficient +0.0061
- additive_singles_e15: coefficient +0.0061
- target_random_projection_e377_e390: coefficient +0.0054
- additive_singles_random_fourier_e449[3]: coefficient -0.0052
- pair_shared_ppi_neighbor_replogle_mean_e492: coefficient +0.0046
- ppi_weighted_replogle_delta_e361: coefficient +0.0039
- additive_singles_random_fourier_e449[8]: coefficient -0.0035
- external_direct_replogle2022_k562_e16: coefficient +0.0034
- replogle_weighted_target_delta_e130_e145: coefficient +0.0030
- replogle_pair_interaction_e43_e57: coefficient -0.0029
- replogle_target_delta_ratio_e76_e110: coefficient -0.0029
- replogle_delta_times_ppi_distance_e507: coefficient -0.0024
- pair_target_ppi_distance_e282: coefficient +0.0019
- replogle_delta_random_fourier_e421[3]: coefficient +0.0017
- additive_singles_times_target_level_e334: coefficient -0.0016
- replogle_delta_random_fourier_e421[2]: coefficient +0.0016
- replogle_delta_random_fourier_e421[4]: coefficient -0.0012
- pair_shared_pathway_count_e138: coefficient -0.0010
- replogle_delta_random_fourier_e421[1]: coefficient +0.0007
- replogle_delta_random_fourier_e421[0]: coefficient -0.0006
- pair_shared_ppi_neighbor_mean_control_e484: coefficient +0.0006
- ppi_adjacency_random_projection_e473[9]: coefficient +0.0003
- ppi_adjacency_random_projection_e473[6]: coefficient +0.0003
- prior_network_max_edge_e32: coefficient -0.0002
- ppi_adjacency_random_projection_e473[8]: coefficient -0.0002
- ppi_adjacency_random_projection_e473[2]: coefficient -0.0001
- ppi_adjacency_random_projection_e473[4]: coefficient +0.0001
- ppi_adjacency_random_projection_e473[7]: coefficient -0.0001
- ppi_adjacency_random_projection_e473[5]: coefficient -0.0001
- ppi_adjacency_random_projection_e473[3]: coefficient +0.0001
- ppi_adjacency_random_projection_e473[1]: coefficient -0.0001
- ppi_adjacency_random_projection_e473[0]: coefficient -0.0000

## DISCOVERY LINEAGE
EXP_0007 [config] score 0.6452
    ↳ EXP_0032 [prior_network_max_edge_e32] score 0.6452
        ↳ EXP_0039 [config] score 0.6452
            ↳ EXP_0057 [replogle_pair_interaction_e43_e57] score 0.6460
                ↳ EXP_0106 [config] score 0.6460
                    ↳ EXP_0110 [replogle_target_delta_ratio_e76_e110] score 0.6462
                        ↳ EXP_0138 [pair_shared_pathway_count_e138] score 0.6462
                            ↳ EXP_0145 [replogle_weighted_target_delta_e130_e145] score 0.6462
                                ↳ EXP_0156 [config] score 0.6463
                                    ↳ EXP_0178 [config] score 0.6463
                                        ↳ EXP_0183 [config] score 0.6464
                                            ↳ EXP_0211 [config] score 0.6468
                                                ↳ EXP_0213 [config] score 0.6469
                                                    ↳ EXP_0247 [best_model_residual_e213_e247] score 0.6469
                                                        ↳ EXP_0279 [config] score 0.6470
                                                            ↳ EXP_0282 [pair_target_ppi_distance_e282] score 0.6470
                                                                ↳ EXP_0294 [config] score 0.6471
                                                                    ↳ EXP_0312 [pair_shared_tf_count_e312] score 0.6471
                                                                        ↳ EXP_0334 [additive_singles_times_target_level_e334] score 0.6475
                                                                            ↳ EXP_0361 [ppi_weighted_replogle_delta_e361] score 0.6477
                                                                                ↳ EXP_0390 [target_random_projection_e377_e390] score 0.6477
                                                                                    ↳ EXP_0413 [config] score 0.6478
                                                                                        ↳ EXP_0421 [replogle_delta_random_fourier_e421] score 0.6479
                                                                                            ↳ EXP_0449 [additive_singles_random_fourier_e449] score 0.6481
                                                                                                ↳ EXP_0473 [ppi_adjacency_random_projection_e473] score 0.6481
                                                                                                    ↳ EXP_0484 [pair_shared_ppi_neighbor_mean_control_e484] score 0.6481
                                                                                                        ↳ EXP_0492 [pair_shared_ppi_neighbor_replogle_mean_e492] score 0.6482
                                                                                                            ↳ EXP_0507 [replogle_delta_times_ppi_distance_e507] score 0.6483
                                                                                                                ↳ EXP_0519 [config] score 0.6484

## MOST USEFUL FEATURES
- pair_additivity_residual_e16 (EXP_0016): +0.0067. For a pair perturbation A+B, the deviation of the observed mean pair delta from the additive sum of the single-gene mean deltas of A and B; 0 for single perturbations.
- replogle_target_delta_sum_e19 (EXP_0019): +0.0063. Sum of sign-flipped Replogle CRISPRi deltas for the perturbation's target genes, broadcast to all genes.
- replogle_pair_interaction_e43_e57 (EXP_0057): +0.0008. Difference between Replogle pair delta and sum of single deltas (sign-flipped).
- pca_projection_score_e15 (EXP_0015): +0.0003. Gene-specific loading on top control-expression PCs, scaled by the perturbation's delta projection onto those PCs.
- additive_singles_times_target_level_e334 (EXP_0334): +0.0003. Element-wise product of additive_singles_e15 and target_level_e11.
- additive_singles_random_fourier_e449 (EXP_0449): +0.0002. Random Fourier feature mapping of additive_singles_e15 values.
- ppi_weighted_replogle_delta_e361 (EXP_0361): +0.0002. PPI-proximity-weighted sum of sign-flipped Replogle2022_K562 deltas over a perturbation's target genes, weighting each target by 1/(1+distance_power*shortest_path_length(g,t)) in the PPI network.
- pair_additivity_residual_abs_e329 (EXP_0329): +0.0002. Absolute value of the pair additivity residual (observed pair delta minus sum of single-gene deltas), broadcast to all genes.
- replogle_target_delta_ratio_e76_e110 (EXP_0110): +0.0002. For a pair perturbation A+B, ratio of the sum of sign-flipped Replogle deltas for A and B to the sum of their absolute values; for singles, the sign of the sign-flipped delta.
- replogle_delta_times_ppi_distance_e507 (EXP_0507): +0.0002. Product of sign-flipped Replogle delta of p's target(s) and shortest PPI distance from target to gene g.

## FEATURES THAT DID NOT HELP
- pair_interaction_coexpr_pathway_e8: -0.0000
- coexpr_with_target_e9: -0.0002
- pathway_similarity_knn_e10: -0.0008
- ppi_diffusion_score_e11: -0.0006
- tf_target_indicator_e12: -0.0001
- target_perturbation_magnitude_e17: -0.0000
- ppi_distance_to_targets_e18: -0.0008
- tf_target_indicator_e20: -0.0002
- random_gene_set_overlap_e23: -0.0001
- replogle_direct_signed_e28: -0.0003
- replogle_knn_signed_e29: -0.0001
- perturbation_complexity_e30: -0.0001
- pathway_overlap_count_e31: -0.0001
- target_control_expr_mean_e33: -0.0000
- control_expr_rank_e34: -0.0030
- control_dropout_rate_e35: -0.0026
- replogle_pair_additivity_residual_e25_e40: -0.0003
- pair_residual_times_coexpr_e26_e41: -0.0034
- replogle_target_delta_prior_weighted_e28_e43: -0.0000
- target_level_pair_interaction_e29_e44: -0.0001
- partial_corr_to_target_e42_e56: -0.0003
- pair_additivity_residual_sym_e44_e58: -0.0001
- pair_residual_times_coexpr_e45_e65: -0.0026
- pair_shared_pathway_count_e47_e67: -0.0000
- replogle_pair_delta_product_e48_e68: -0.0001
- replogle_target_delta_product_e72_e79: -0.0001
- pair_shared_pathway_count_e73_e80: -0.0001
- pair_target_coexpr_abs_e75_e82: -0.0001
- replogle_target_delta_ratio_e76_e85: -0.0000
- pair_ppi_shortest_path_weighted_e79_e89: -0.0001
- pair_shared_tf_targets_e80_e90: -0.0001
- pair_target_coexpr_rank_product_e81_e91: -0.0000
- pair_target_expr_quantile_product_e83_e93: -0.0000
- pair_target_expr_quantile_product_e83_e94: -0.0000
- replogle_single_delta_product_sign_e87_e96: -0.0000
- pair_ppi_shortest_path_weighted_e89_e107: -0.0001
- pair_target_expr_quantile_product_e83_e109: -0.0000
- pair_target_coexpr_rank_product_e81_e111: -0.0003
- pair_ppi_edge_confidence_product_e90_e118: -0.0001
- replogle_target_delta_prior_weighted_e28_e123: -0.0000
- target_level_pair_interaction_e29_e44_e125: -0.0021
- pair_target_control_product_e132: -0.0000
- pair_target_control_product_e133: -0.0000
- pair_replogle_delta_product_e134: -0.0001
- pair_replogle_delta_product_e135: -0.0001
- pair_ppi_edge_product_e137: -0.0000
- pair_ppi_diffusion_score_e140: -0.0006
- gene_set_overlap_count_e132_e147: -0.0001
- pair_additivity_residual_abs_e133_e148: -0.0002
- replogle_target_delta_range_e134_e149: -0.0002
- ppi_diffusion_pair_product_e135_e152: -0.0000
- replogle_individual_target_deltas_e146_e157: -0.0006
- replogle_prior_edge_interaction_e147_e158: -0.0000
- replogle_ppi_distance_weighted_e148_e159: -0.0002
- replogle_pathway_overlap_weighted_e149_e160: -0.0001
- replogle_pair_interaction_refined_e150_e161: -0.0008
- ppi_dist_scaled_replogle_product_e166: -0.0002
- replogle_delta_over_control_var_e167: -0.0002
- shared_tf_count_e168: -0.0000
- replogle_delta_product_pair_e169: -0.0001
- target_gene_pathway_jaccard_e170: -0.0001
- pathway_topology_distance_e184: -0.0001
- coexpr_module_response_score_e185: -0.0011
- tf_regulon_overlap_score_e186: -0.0000
- replogle_delta_sign_consistency_e187: -0.0001
- random_projection_context_e198: -0.0001
- coexpr_with_target_e9_e199: -0.0004
- shared_pathway_count_e10_e200: -0.0003
- ppi_distance_to_targets_e11_e201: -0.0003
- target_control_mean_e14_e204: -0.0002
- pair_target_coexpr_e15_e205: -0.0002
- additive_external_interaction_e217: -0.0000
- response_component_target_interaction_e218: -0.0002
- pair_target_control_coexpr_e219: -0.0002
- replogle_ppi_neighbor_delta_e220: -0.0002
- gene_set_comembership_count_e221: -0.0003
- target_control_variance_mean_e222: -0.0002
- target_weighted_random_projection_e223: -0.0002
- replogle_ppi_distance_weighted_delta_e224: -0.0012
- replogle_ppi_neighbor_avg_delta_e225: -0.0011
- target_expr_times_replogle_delta_e226: -0.0011
- replogle_delta_over_control_variance_e227: -0.0012
- pair_replogle_delta_product_e228: -0.0010
- replogle_pair_interaction_abs_e43_e57_e242: -0.0013
- replogle_target_delta_norm_by_control_va_e243: -0.0093
- pathway_response_component_similarity_e244: -0.0022
- ppi_neighbor_replogle_weighted_e245: -0.0012
- prior_network_reverse_edge_to_target_e246: -0.0011
- replogle_pair_interaction_abs_e229_e249: -0.0011
- ppi_shortest_path_count_e230_e250: -0.0011
- replogle_target_delta_sum_sq_e232_e252: -0.0013
- ppi_neighbor_replogle_sum_e234_e254: -0.0013
- pair_target_pathway_jaccard_e257: -0.0011
- replogle_pair_delta_product_e258: -0.0012
- response_component_cosine_similarity_e261: -0.0016
- target_control_mean_ratio_e267: -0.0011
- similar_pert_replogle_avg_e268: -0.0011
- max_jaccard_gene_set_overlap_e269: -0.0011
- prior_network_sum_edge_e270: -0.0011
- rf_residual_simple_e271: -0.0046
- target_gene_set_overlap_e_e274: -0.0002
- prior_network_target_sum_e_e275: -0.0000
- pair_target_control_ratio_e_e277: -0.0000
- ppi_rwr_score_e_e278: -0.0004
- pair_target_control_ratio_e281: -0.0000
- ppi_pair_rwr_score_e287: -0.0004
- gene_pair_pathway_overlap_count_e291: -0.0001
- replogle_target_delta_product_e292: -0.0001
- pair_target_rwr_score_e295: -0.0004
- pair_target_control_imbalance_e290_e296: -0.0001
- target_gene_set_overlap_count_e292_e298: -0.0002
- ppi_weighted_proximity_e293_e299: -0.0000
- replogle_gene_residual_after_target_sum_e304: -0.0005
- pair_shared_pathway_count_weighted_e313: -0.0000
- replogle_pair_delta_product_e314: -0.0001
- ppi_shared_neighbor_count_e_e339: -0.0000
- coexpr_module_overlap_e_e340: -0.0002
- gene_set_cosine_similarity_e_e341: -0.0000
- ppi_embedding_cosine_e_e344: -0.0001
- pathway_overlap_with_targets_e357: -0.0003
- tf_coregulation_with_targets_e358: -0.0000
- ppi_embedding_similarity_g_targets_e359: -0.0000
- ppi_weighted_additive_singles_e360: -0.0001
- additive_times_replogle_sum_e362: -0.0002
- random_projection_response_e363: -0.0000
- shared_ppi_neighbors_count_e367: -0.0001
- target_gene_pathway_count_e368: -0.0003
- replogle_ppi_weighted_sum_e369: -0.0001
- pair_target_coexpr_corr_e370: -0.0000
- target_coexpr_rank_e373: -0.0001
- pair_shared_pathway_weighted_e372_e383: -0.0000
- target_expression_variance_e374_e385: -0.0001
- additive_times_replogle_sum_e376_e389: -0.0003
- ppi_neighbor_overlap_count_e395: -0.0000
- replogle_pair_target_sign_agreement_e397: -0.0000
- shared_pathway_count_gene_targets_e398: -0.0002
- target_expression_specificity_e399: -0.0000
- target_coexpr_sum_sq_e415: -0.0002
- pair_target_control_mean_product_e416: -0.0000
- pair_additivity_residual_loo_e417: -0.0043
- pathway_jaccard_target_overlap_e418: -0.0000
- additive_replogle_interaction_e430: -0.0000
- pair_target_replogle_ratio_e443: -0.0000
- gene_target_pathway_overlap_count_e444: -0.0002
- ppi_shared_neighbor_count_e445: -0.0000
- replogle_delta_ppi_edge_weighted_e446: -0.0000
- replogle_target_delta_ppi_inverse_path_e452: -0.0004
- gene_target_pathway_overlap_count_e463: -0.0002
- gene_target_shared_tf_count_e464: -0.0000
- pair_shared_gene_set_inverse_size_sum_e475: -0.0000
- pair_ppi_adjacency_random_projection_e481: -0.0016
- pair_targets_gene_set_overlap_e485: -0.0001
- replogle_delta_correlation_with_targets_e487: -0.0001
- pair_target_control_expression_product_e488: -0.0000
- ppi_prior_adjacency_random_projection_e491: -0.0000
- gene_set_jaccard_e506: -0.0000
- tf_target_diffusion_score_e521: -0.0000
- ppi_replogle_coexpr_weighted_e523: -0.0000
- pair_replogle_delta_correlation_e534: -0.0001
- pair_replogle_delta_product_e540: -0.0001
- replogle_delta_times_shared_pathway_coun_e542: -0.0002
- pair_target_replogle_delta_similarity_e543: -0.0001
- ppi_neighbor_replogle_delta_sum_e544: -0.0001
- replogle_delta_over_ppi_distance_e546: -0.0002
- replogle_delta_squared_e549: -0.0001
- pair_shared_pathway_replogle_sum_e552: -0.0001
- ppi_neighbor_replogle_entropy_e554: -0.0000
- replogle_delta_over_ppi_degree_e555: -0.0005
- pair_shared_tf_replogle_weighted_e557: -0.0001
- pair_shared_tf_replogle_weighted_e558: -0.0001
- replogle_delta_times_shared_pathway_e560: -0.0000
- ppi_neighbor_replogle_random_projection_e563: -0.0001
- ppi_neighbor_replogle_random_projection_e564: -0.0001
- regulon_replogle_sum_e567: -0.0002
- ppi_shortest_path_confidence_e569: -0.0002
- ppi_neighbor_delta_random_projection_e573: -0.0002
- ppi_neighbor_replogle_variance_e602_e577: -0.0001
- tf_target_diffusion_e603_e578: -0.0005
- pair_target_ppi_path_confidence_product__e583: -0.0000
- replogle_additive_sign_agreement_e003_e585: -0.0000
- pair_shared_pathway_jaccard_e004_e586: -0.0000
- pair_target_control_corr_e005_e587: -0.0000

## FAILED FEATURES
- EXP_0021 pair_single_departure_e21 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0059 target_expr_times_replogle_e45_e59 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0060 glasso_edge_to_target_e46_e60 [test]: feature failed after 2 attempts: timeout after 90s
- EXP_0066 pair_ppi_edge_strength_e46_e66 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0069 pair_prior_network_distance_e49_e69 [guard]: iteration over a set of objects (line 53) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0078 pair_additivity_residual_abs_e71_e78 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0081 pair_ppi_shortest_path_e74_e81 [guard]: iteration over a set of objects (line 55) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0092 replogle_pair_interaction_abs_e82_e92 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0095 replogle_pair_additivity_abs_e86_e95 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0098 pair_ppi_edge_weight_e89_e98 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0108 pair_shared_tf_targets_e80_e108 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0122 replogle_target_delta_ppi_weighted_e27_e_e122 [test]: feature failed after 2 attempts:  = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/
- EXP_0124 replogle_pair_additivity_residual_e25_e4_e124 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0126 replogle_target_delta_ppi_diffusion_e126 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0136 pair_ppi_edge_product_e136 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0164 rf_residual_e151_e164 [test]: feature failed after 2 attempts: timeout after 90s
- EXP_0179 ppi_rwr_pair_product_seed_e179 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0202 similar_pert_knn_e12_e202 [test]: feature failed after 2 attempts: ne)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_from_n2_w4_r3/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np
- EXP_0203 replogle_ppi_weighted_delta_e13_e203 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0216 best_model_residual_e183_e216 [test]: feature failed after 2 attempts: feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene
- EXP_0229 pair_replogle_delta_abs_diff_e229 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0241 pair_additivity_abs_residual_e16_e241 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0251 pathway_replogle_weighted_e231_e251 [test]: feature failed after 2 attempts: 3/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if 
- EXP_0253 loo_residual_similarity_e233_e253 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0256 replogle_weighted_by_pathway_overlap_e256 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0259 replogle_control_mean_weighted_sum_e259 [test]: feature failed after 2 attempts: rray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/andresarriaga/Documen
- EXP_0260 loo_residual_feature_e260 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0265 replogle_target_delta_sum_squared_e265 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0266 replogle_target_delta_product_e266 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0276 replogle_pair_target_product_e_e276 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0285 replogle_target_delta_product_e285 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0288 pair_shared_tf_count_e288 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0290 pair_target_direct_ppi_weight_e290 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0297 replogle_additive_sign_agreement_e291_e297 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0300 replogle_pair_interaction_scaled_e294_e300 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0303 rf_residual_e295_e303 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0305 pair_replogle_product_ppi_signed_e305 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0306 pair_response_component_interaction_e306 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0307 replogle_delta_ppi_distance_weighted_e307 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0308 pair_additivity_residual_by_coexpr_e308 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0311 rf_residual_on_current_features_e311 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0324 rf_residual_feature_e324 [guard]: top-level Try statement not allowed
- EXP_0333 response_component_interaction_pair_e333 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0343 replogle_pair_product_e_e343 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0396 target_pair_ppi_weight_e396 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0414 ppi_shortest_path_weighted_replogle_delt_e414 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0425 gene_target_jaccard_gene_sets_e425 [guard]: iteration over a set of objects (line 32) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0426 replogle_pair_additivity_residual_e426 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0442 replogle_pair_residual_coexpr_weighted_e442 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0450 pair_replogle_sign_product_magnitude_e450 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0453 replogle_delta_times_control_mean_sum_e453 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0462 ppi_diffusion_replogle_delta_e462 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0465 control_expr_weighted_replogle_delta_e465 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0474 pair_shared_ppi_neighbor_control_mean_e474 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0476 replogle_target_sign_product_e476 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0486 tf_target_network_distance_e486 [guard]: iteration over a set of objects (line 46) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0496 replogle_delta_squared_e496 [test]: feature failed after 2 attempts: ila/gene-mila/runs/norman_ds_from_n2_w4_r3/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins)
- EXP_0508 pair_shared_tf_jaccard_e508 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0509 ppi_neighbor_replogle_delta_e509 [test]: feature failed after 2 attempts: ees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cac
- EXP_0524 pair_target_replogle_product_e524 [guard]: call of id() not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numbe
- EXP_0531 target_gene_set_replogle_sum_e531 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0533 shared_tf_replogle_delta_sum_e533 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0535 pathway_replogle_enrichment_e535 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0536 tf_target_diffusion_replogle_e536 [test]: feature failed after 2 attempts: (args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mil
- EXP_0545 pair_shared_ppi_neighbor_replogle_sum_e545 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0547 pair_target_ppi_neighbor_overlap_count_e547 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0551 pair_shared_pathway_replogle_sum_e551 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0553 ppi_neighbor_replogle_entropy_e553 [test]: feature failed after 2 attempts: rees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.ca
- EXP_0556 replogle_delta_over_ppi_degree_e556 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0559 replogle_delta_times_shared_pathway_e559 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0566 ppi_neighbor_delta_variance_e566 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0568 gene_set_replogle_mean_e568 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0570 target_delta_times_shared_neighbors_e570 [test]: feature failed after 2 attempts: ain
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Docume
- EXP_0575 replogle_pair_delta_log_ratio_e600_e575 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0576 pathway_weighted_replogle_delta_e601_e576 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0579 pair_shared_ppi_neighbor_weighted_e604_e579 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0580 replogle_times_prior_edge_e605_e580 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0581 pair_target_replogle_random_projection_e_e581 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0584 pair_shared_ppi_neighbor_confidence_sum__e584 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0589 ppi_neighbor_replogle_random_projection__e589 [experiment]: ValueError: feature ppi_neighbor_replogle_random_projection__e589 produced NaN/inf values

## SURPRISING RESULTS
- none

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0519 | config | 0.6484 | 0.7113 | -0.0629 |
| EXP_0585 | new_feature | 0.6484 | 0.7112 | -0.0628 |
| EXP_0554 | new_feature | 0.6484 | 0.7113 | -0.0629 |
| EXP_0003 | baseline | 0.6148 | 0.7126 | -0.0978 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0519 | 0.007 / 0.005 | 0.985 / 0.989 | 0.966 / 0.975 | 0.156 / 0.106 | 0.914 / 0.940 | 0.784 / 0.850 |
| EXP_0585 | 0.007 / 0.005 | 0.985 / 0.989 | 0.966 / 0.975 | 0.156 / 0.106 | 0.914 / 0.940 | 0.784 / 0.850 |
| EXP_0554 | 0.007 / 0.005 | 0.985 / 0.989 | 0.966 / 0.975 | 0.156 / 0.106 | 0.914 / 0.940 | 0.784 / 0.850 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0519 | 0.567 / 0.550 | 0.744 / 0.758 | 0.559 / 0.515 | 0.945 / 0.949 | 0.860 / 0.871 | 0.973 / 0.971 |
| EXP_0585 | 0.567 / 0.550 | 0.744 / 0.758 | 0.559 / 0.515 | 0.945 / 0.949 | 0.860 / 0.872 | 0.973 / 0.972 |
| EXP_0554 | 0.567 / 0.550 | 0.744 / 0.758 | 0.559 / 0.514 | 0.945 / 0.949 | 0.860 / 0.871 | 0.973 / 0.971 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0519 | 0.745 / 0.676 | 0.008 / 0.006 | 0.786 / 0.782 | 0.561 / 0.484 | 0.920 / 0.900 |
| EXP_0585 | 0.745 / 0.676 | 0.008 / 0.006 | 0.785 / 0.783 | 0.560 / 0.483 | 0.920 / 0.901 |
| EXP_0554 | 0.745 / 0.676 | 0.008 / 0.006 | 0.786 / 0.783 | 0.560 / 0.483 | 0.920 / 0.900 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1339.33
- Mean CPU s/experiment: 2.75
- Gain per CPU-hour: 0.0986
- Gain per USD: 0.0268
- LLM cost per completed experiment: $0.00281

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_from_n2_w4_r3 --experiment EXP_0519`
