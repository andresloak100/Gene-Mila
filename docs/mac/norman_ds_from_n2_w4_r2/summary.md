# RUN SUMMARY

Run `norman_ds_from_n2_w4_r2` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `076282c71b`)

- Duration: 20.1 min
- Workers: 4
- Experiments proposed: 752
- Experiments completed: 616 (plus baselines; deepseek:deepseek-v4-pro: 328, python:exploit: 162, python:warm_start: 1, sweep(deepseek:deepseek-v4-pro): 125)
- Experiments failed / rejected / killed / not started: 79 / 15 / 1 / 1
- Unique hypotheses: 742 (replicated: 10); duplicate configurations skipped: 33
- CPU hours: 0.2524
- LLM (worker): 492 calls, 890004 in / 364089 out / 429824 cached tokens, $0.5775
- LLM (planner): 60 calls, 312796 in / 131936 out / 69120 cached tokens, $0.8472

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6313

## BEST PERFORMANCE
EXP_0729: pearson_delta = 0.6693 (ridge, alpha=0.00198)

## IMPROVEMENT
0.0379 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_singles_e15: coefficient +0.0629
- pair_target_shared_tf_count_e83_e92: coefficient +0.0271
- response_components_e14[0]: coefficient +0.0204
- response_components_e14[1]: coefficient +0.0176
- pair_target_shared_tf_pathway_interactio_e222: coefficient -0.0168
- similar_pert_external_response_knn_e52: coefficient +0.0167
- pair_target_prior_edge_e34: coefficient -0.0083
- response_components_e14[3]: coefficient +0.0070
- additive_singles_times_pair_prior_edge_e401: coefficient -0.0067
- response_components_e14[2]: coefficient +0.0066
- is_target: coefficient +0.0062
- target_expression_random_projection_e510[4]: coefficient +0.0060
- pair_shared_tf_times_pathway_entropy_exx_e681: coefficient -0.0046
- external_response_times_control_expr_e279: coefficient +0.0027
- target_level_e11: coefficient +0.0025
- pair_target_shortest_path_e15_e234: coefficient -0.0023
- target_expression_random_projection_e510[2]: coefficient -0.0023
- additive_external_response_interaction_e605: coefficient +0.0022
- pair_target_gene_set_asymmetry_e281_e289: coefficient +0.0019
- target_specificity_times_external_delta_e620: coefficient -0.0018
- external_response_random_projection_targ_e325: coefficient +0.0016
- target_set_pathway_entropy_e642: coefficient -0.0013
- target_expression_random_projection_e510[1]: coefficient +0.0012
- external_replogle_random_projection_gene_e439[1]: coefficient +0.0012
- target_set_functional_coherence_e74: coefficient -0.0010
- target_expression_random_projection_e510[3]: coefficient +0.0010
- additive_singles_squared_pair_e456: coefficient +0.0009
- target_expression_random_projection_e510[0]: coefficient +0.0008
- ppi_neighbor_overlap_with_targets_e567: coefficient -0.0007
- control_expr_rank_perturbation_e163_e176: coefficient -0.0007
- external_replogle_random_projection_gene_e439[3]: coefficient -0.0005
- external_replogle_random_projection_gene_e439[2]: coefficient -0.0004
- external_replogle_random_projection_gene_e439[0]: coefficient +0.0004
- external_replogle_random_projection_gene_e439[4]: coefficient +0.0001

## DISCOVERY LINEAGE
EXP_0007 [config] score 0.6653
    ↳ EXP_0034 [pair_target_prior_edge_e34] score 0.6654
        ↳ EXP_0052 [similar_pert_external_response_knn_e52] score 0.6664
            ↳ EXP_0074 [target_set_functional_coherence_e74] score 0.6665
                ↳ EXP_0092 [pair_target_shared_tf_count_e83_e92] score 0.6665
                    ↳ EXP_0104 [config] score 0.6665
                        ↳ EXP_0126 [pair_target_shared_pathway_count_e126] score 0.6665
                            ↳ EXP_0134 [config] score 0.6665
                                ↳ EXP_0146 [config] score 0.6665
                                    ↳ EXP_0170 [config] score 0.6676
                                        ↳ EXP_0173 [config] score 0.6676
                                            ↳ EXP_0176 [control_expr_rank_perturbation_e163_e176] score 0.6678
                                                ↳ EXP_0192 [config] score 0.6678
                                                    ↳ EXP_0222 [pair_target_shared_tf_pathway_interactio_e222] score 0.6679
                                                        ↳ EXP_0234 [pair_target_shortest_path_e15_e234] score 0.6679
                                                            ↳ EXP_0243 [target_gene_set_specificity_e243] score 0.6679
                                                                ↳ EXP_0253 [config] score 0.6679
                                                                    ↳ EXP_0279 [external_response_times_control_expr_e279] score 0.6680
                                                                        ↳ EXP_0289 [pair_target_gene_set_asymmetry_e281_e289] score 0.6680
                                                                            ↳ EXP_0305 [config] score 0.6680
                                                                                ↳ EXP_0325 [external_response_random_projection_targ_e325] score 0.6682
                                                                                    ↳ EXP_0352 [target_response_pathway_overlap_e352] score 0.6682
                                                                                        ↳ EXP_0358 [config] score 0.6682
                                                                                            ↳ EXP_0385 [config] score 0.6682
                                                                                                ↳ EXP_0401 [additive_singles_times_pair_prior_edge_e401] score 0.6686
                                                                                                    ↳ EXP_0439 [external_replogle_random_projection_gene_e439] score 0.6687
                                                                                                        ↳ EXP_0456 [additive_singles_squared_pair_e456] score 0.6688
                                                                                                            ↳ EXP_0463 [config] score 0.6688
                                                                                                                ↳ EXP_0481 [config] score 0.6688
                                                                                                                    ↳ EXP_0488 [config] score 0.6688
                                                                                                                        ↳ EXP_0500 [config] score 0.6688
                                                                                                                            ↳ EXP_0510 [target_expression_random_projection_e510] score 0.6688
                                                                                                                                ↳ EXP_0537 [config] score 0.6688
                                                                                                                                    ↳ EXP_0544 [config] score 0.6688
                                                                                                                                        ↳ EXP_0556 [config] score 0.6688
                                                                                                                                            ↳ EXP_0567 [ppi_neighbor_overlap_with_targets_e567] score 0.6688
                                                                                                                                                ↳ EXP_0584 [config] score 0.6688
                                                                                                                                                    ↳ EXP_0588 [config] score 0.6688
                                                                                                                                                        ↳ EXP_0592 [config] score 0.6688
                                                                                                                                                            ↳ EXP_0605 [additive_external_response_interaction_e605] score 0.6691
                                                                                                                                                                ↳ EXP_0620 [target_specificity_times_external_delta_e620] score 0.6692
                                                                                                                                                                    ↳ EXP_0642 [target_set_pathway_entropy_e642] score 0.6692
                                                                                                                                                                        ↳ EXP_0648 [config] score 0.6692
                                                                                                                                                                            ↳ EXP_0681 [pair_shared_tf_times_pathway_entropy_exx_e681] score 0.6693
                                                                                                                                                                                ↳ EXP_0694 [config] score 0.6693
                                                                                                                                                                                    ↳ EXP_0717 [config] score 0.6693
                                                                                                                                                                                        ↳ EXP_0729 [config] score 0.6693

## MOST USEFUL FEATURES
- similar_pert_knn_e20_e9 (EXP_0009): +0.0607. Average training delta of the k perturbations whose target gene sets are most Jaccard-similar to p's targets.
- similar_pert_external_response_knn_e52 (EXP_0052): +0.0011. Average training delta of the k perturbations whose external Replogle target response vectors are closest (Euclidean) to p's external response vector.
- pca_alignment_e24_e13 (EXP_0013): +0.0005. Dot product between target loading vectors and gene loading vectors on top control PCs, weighted by PC variance explained.
- target_coexpression_e19_e8 (EXP_0008): +0.0004. Mean control-expression correlation between gene g and the target gene(s) of perturbation p.
- additive_external_response_interaction_e605 (EXP_0605): +0.0003. Element-wise product of additive_singles_e15 and external_response_times_control_expr_e279.
- additive_singles_times_pair_prior_edge_e401 (EXP_0401): +0.0003. Product of additive_singles_e15 and pair_target_prior_edge_e34.
- control_expr_rank_perturbation_e163_e176 (EXP_0176): +0.0002. Percentile rank of gene g's control mean expression, interacted with target membership.
- external_response_random_projection_targ_e325 (EXP_0325): +0.0002. Dot product between a fixed random projection of gene g's sign-corrected external Replogle delta and the average projected vector of the perturbation's target genes.
- target_level_external_direct_interaction_e57 (EXP_0057): +0.0002. Element-wise product of target_level_e11 and external_direct_replogle2022_k562_e16.
- target_neighborhood_expression_projectio_e604 (EXP_0604): +0.0001. Mean control expression of PPI neighbors of perturbation targets (excluding the targets), projected through a fixed random Gaussian matrix to k dimensions.

## FEATURES THAT DID NOT HELP
- prior_network_diffusion_e22_e11: -0.0002
- pathway_overlap_e23_e12: -0.0001
- target_magnitude_e25_e15: -0.0001
- partial_corr_to_targets_e17: -0.0002
- network_propagation_score_e22: -0.0002
- pathway_overlap_with_targets_e23: -0.0001
- target_mean_control_log_e29: -0.0001
- target_mean_control_rank_e30: -0.0001
- target_dropout_rate_e31: -0.0001
- interaction_target_expr_additive_e32: -0.0005
- similar_pert_knn_cosine_e33: -0.0035
- target_hub_degree_e27_e36: -0.0000
- tf_target_regulation_e29_e38: -0.0000
- random_target_projection_e30_e46: -0.0001
- pair_shared_neighbors_prior_e51: -0.0000
- target_control_variance_e53: -0.0001
- pair_additive_residual_pred_e54: -0.0005
- pair_target_expr_product_e61: -0.0000
- pair_target_expr_sum_e62: -0.0001
- pair_target_coexpr_similarity_e63: -0.0000
- random_fourier_target_expr_e68: -0.0003
- pair_external_response_corr_e75: -0.0002
- target_control_expression_rank_e76: -0.0001
- min_network_distance_to_target_e77: -0.0000
- pair_additive_external_direct_e78: -0.0004
- target_prior_network_degree_centrality_e_e82: -0.0001
- target_mean_external_response_magnitude__e84: -0.0001
- pair_target_expression_product_log_e77_e85: -0.0000
- random_fourier_target_expr_risky_e78_e88: -0.0004
- pair_target_shared_pathway_count_e81_e90: -0.0000
- target_set_avg_abs_external_response_e82_e91: -0.0003
- random_network_propagation_e84_e101: -0.0001
- external_replogle_corr_to_targets_e103_e107: -0.0001
- target_external_response_magnitude_e104_e108: -0.0001
- ppi_shared_neighbor_score_e105_e109: -0.0001
- gene_set_jaccard_to_targets_e106_e110: -0.0000
- prior_network_shortest_path_to_target_e1_e111: -0.0001
- target_ppi_degree_e127: -0.0000
- target_prior_out_degree_e128: -0.0002
- target_avg_control_corr_e129: -0.0007
- target_control_variance_e130: -0.0002
- target_random_projection_e132: -0.0001
- target_prior_network_degree_e94_e138: -0.0001
- gene_ppi_distance_to_pair_targets_e95_e139: -0.0001
- pair_target_external_response_similarity_e141: -0.0001
- target_control_variance_e98_e142: -0.0002
- prior_network_shortest_path_to_target_e151: -0.0000
- pair_target_gene_set_jaccard_e152: -0.0000
- target_gene_control_correlation_e153: -0.0005
- target_set_jaccard_to_g_e148_e160: -0.0000
- ppi_distance_to_targets_e150_e162: -0.0001
- pair_shared_tf_count_refined_e151_e163: -0.0000
- pair_target_expr_diff_e164_e177: -0.0001
- external_response_norm_e165_e178: -0.0001
- pair_target_expr_rank_sum_e195: -0.0001
- pair_target_shared_pathway_weighted_e197: -0.0000
- pair_target_expr_product_e198: -0.0000
- similar_pert_hybrid_knn_e199: -0.0082
- pair_target_external_response_corr_e208: -0.0001
- pair_target_shared_pathway_weighted_e209: -0.0000
- pair_target_control_expr_product_e211: -0.0000
- target_control_expr_random_projection_e221: -0.0000
- similar_pert_knn_cosine_e10_e227: -0.0030
- external_response_similarity_to_targets__e230: -0.0000
- target_control_expr_random_proj_poly_e14_e233: -0.0002
- external_replogle_neighbor_response_e241: -0.0002
- pair_target_control_coexpression_e242: -0.0000
- weighted_target_set_functional_coherence_e256: -0.0000
- pair_target_shared_tf_count_expr_weighte_e257: -0.0000
- external_response_target_avg_cosine_e258: -0.0000
- prior_network_min_distance_to_pair_targe_e259: -0.0001
- target_expr_rank_external_response_inter_e260: -0.0001
- pair_target_shared_pathway_coherence_int_e261: -0.0001
- pair_target_external_response_product_e275: -0.0001
- target_geneset_external_top_overlap_e277: -0.0002
- similar_pert_external_response_cosine_kn_e280: -0.0004
- pair_target_weighted_shortest_path_produ_e288: -0.0000
- target_control_expr_random_projection_no_e299: -0.0000
- target_control_expr_random_projection_no_e300: -0.0000
- pair_target_shared_upstream_tf_count_e28_e301: -0.0000
- pair_target_external_delta_product_e306: -0.0001
- pair_target_external_response_corr_e308: -0.0001
- target_count_times_external_response_e309: -0.0001
- external_response_rank_gene_e310: -0.0000
- pair_target_shared_pathway_specificity_e311: -0.0001
- pair_target_external_response_asymmetry_e318: -0.0001
- target_gene_set_overlap_rank_e319: -0.0000
- pair_target_shared_pathway_specificity_e320: -0.0001
- additive_singles_scaled_by_target_count_e322: -0.0022
- external_response_random_projection_targ_e324: -0.0001
- pair_target_jaccard_gene_sets_e340: -0.0000
- ppi_shortest_path_to_target_e341: -0.0003
- tf_regulation_score_e342: -0.0000
- external_response_random_projection_e343: -0.0001
- target_ppi_degree_sum_e350: -0.0001
- max_abs_control_corr_to_targets_e351: -0.0001
- pair_target_control_expr_product_e353: -0.0000
- target_control_expr_random_projection_e356: -0.0004
- target_ppi_degree_e361: -0.0001
- target_component_overlap_e362: -0.0001
- pair_shared_tf_weighted_e363: -0.0000
- target_essentiality_e367: -0.0000
- pair_target_external_rank_product_e380: -0.0001
- pair_target_ppi_weighted_shortest_path_e381: -0.0000
- target_ppi_degree_centrality_e382: -0.0001
- external_response_target_cosine_e383: -0.0000
- pair_shared_tf_external_magnitude_produc_e384: -0.0000
- target_ppi_degree_sum_e388: -0.0001
- target_tf_regulator_overlap_e389: -0.0000
- target_gene_set_count_inverse_e391: -0.0000
- target_gene_shortest_path_e392: -0.0003
- pair_target_control_corr_e393: -0.0000
- control_expr_pca_residual_e395: -0.0001
- target_to_gene_ppi_shortest_path_e398: -0.0002
- normalized_gene_set_overlap_target_gene_e399: -0.0000
- target_tf_binding_sites_in_gene_promoter_e400: -0.0000
- sigmoid_additive_singles_e403: -0.0001
- ppr_target_to_gene_e404: -0.0005
- ppi_weighted_shortest_path_to_target_e409: -0.0003
- target_pathway_response_enrichment_e411: -0.0001
- target_tf_binding_potential_e412: -0.0001
- ppi_confidence_pagerank_to_gene_e416: -0.0003
- target_coexpr_module_similarity_e451_e419: -0.0001
- external_separate_target_deltas_sum_e452_e420: -0.0001
- prior_edge_times_target_expr_e454_e422: -0.0001
- target_gene_set_embedding_similarity_e45_e425: -0.0001
- pair_target_shared_tf_motif_score_e428: -0.0000
- target_control_covariance_with_g_e429: -0.0006
- prior_network_two_step_weight_e430: -0.0000
- external_replogle_delta_of_g_for_targets_e431: -0.0001
- pair_target_weighted_shared_pathways_e432: -0.0001
- additive_singles_times_functional_cohere_e433: -0.0001
- external_replogle_random_projection_gene_e440: -0.0002
- external_response_network_weighted_e443: -0.0000
- target_set_weighted_coherence_e445: -0.0000
- external_target_delta_times_coexpr_e446: -0.0009
- target_set_coherence_weighted_external_e457: -0.0000
- external_coexpr_random_projection_e460: -0.0006
- external_response_of_target_ppi_neighbor_e470: -0.0000
- random_projection_target_gene_external_c_e473: -0.0010
- gene_set_overlap_with_pair_union_e474_e479: -0.0001
- pair_target_control_correlation_e491: -0.0000
- mean_positive_correlation_to_targets_e492: -0.0004
- pair_target_shared_pathway_with_others_e493: -0.0000
- weighted_external_response_ppi_neighbors_e494: -0.0000
- random_projection_coexpression_to_target_e498: -0.0019
- pair_target_shared_ppi_neighbor_weighted_e506: -0.0000
- target_gene_functional_similarity_e507: -0.0000
- target_external_delta_dispersion_e515: -0.0000
- pair_target_mean_external_delta_e516: -0.0000
- target_gene_set_overlap_count_e519: -0.0000
- similar_pert_knn_softmax_e520_e530: -0.0094
- pair_target_external_sign_agreement_e522_e532: -0.0000
- additive_singles_times_target_expr_rp_e5_e533: -0.0001
- gene_target_pathway_jaccard_e525_e535: -0.0000
- pair_target_gene_set_similarity_to_g_e551: -0.0000
- pair_ppi_shortest_path_weighted_e552: -0.0000
- additive_singles_times_pair_external_pro_e553: -0.0000
- pair_external_random_projection_concat_e554: -0.0002
- pair_shortest_path_times_additive_single_e560: -0.0011
- pair_target_expr_diff_random_projection__e564: -0.0000
- pair_external_delta_signed_product_e556_e565: -0.0000
- gene_set_cooccurrence_count_e568: -0.0000
- external_response_ppi_neighbors_targets_e569: -0.0000
- control_coexpression_with_targets_e570: -0.0006
- prior_network_diffusion_score_e571: -0.0002
- pair_target_shared_tf_motifs_e572: -0.0000
- target_expr_external_delta_random_projec_e573: -0.0000
- target_ppi_module_overlap_e576: -0.0003
- pair_target_external_delta_asymmetry_e578: -0.0000
- target_count_times_control_expr_e579: -0.0004
- tf_regulatory_potential_sum_e580: -0.0000
- weighted_gene_set_comembership_e582: -0.0001
- ppi_distance_to_targets_e599: -0.0003
- shared_tf_expression_weighted_e600: -0.0001
- ppi_shortest_path_target_to_gene_e607: -0.0003
- target_expression_specificity_e608: -0.0001
- additive_singles_times_ppi_distance_e609: -0.0000
- shared_tf_motif_score_e610: -0.0000
- go_semantic_similarity_target_gene_e611: -0.0000
- control_expression_covariance_target_gen_e612: -0.0003
- ppr_target_to_gene_e613: -0.0002
- external_response_ppi_distance_weighted_e616: -0.0001
- pair_external_delta_asymmetry_e617: -0.0000
- shared_pathway_weighted_external_delta_e618: -0.0004
- ppi_neighbor_expression_corr_e619: -0.0011
- ppi_neighbor_expression_random_projectio_e622: -0.0000
- shared_ppi_neighbor_expr_corr_e629: -0.0001
- pair_external_delta_abs_sum_e630: -0.0002
- target_ppi_neighbor_expr_random_projecti_e634: -0.0000
- ppi_neighbor_expression_corr_with_target_e639: -0.0004
- target_ppi_neighbor_pathway_overlap_e640: -0.0001
- control_expr_diff_to_target_ppi_neighbor_e643: -0.0001
- external_response_times_ppi_neighbor_ove_e644: -0.0002
- ppi_neighbor_expression_random_projectio_e646: -0.0001
- coherence_times_additive_e653: -0.0001
- ppi_overlap_times_external_response_e654: -0.0002
- normalized_target_set_pathway_entropy_e663: -0.0001
- additive_singles_times_target_ppi_degree_e665: -0.0000
- pair_shared_pathway_times_target_expr_e666: -0.0000
- target_gene_set_membership_random_projec_e669: -0.0002
- additive_singles_times_target_coherence__e670: -0.0001
- external_response_times_ppi_overlap_exxx_e671: -0.0003
- additive_singles_squared_exxx_e682: -0.0000
- pair_shared_tf_motif_count_e689: -0.0000
- pair_target_external_delta_corr_e690: -0.0001
- ppi_shortest_path_to_target_e691: -0.0002
- ppi_adjacency_random_projection_e696: -0.0001
- ppi_gene_target_shortest_path_e700_e698: -0.0004
- ppi_gene_target_shortest_path_e700_e699: -0.0004
- pair_target_shared_tf_count_squared_e702_e703: -0.0000
- ppi_neighbor_expression_random_projectio_e704: -0.0001
- ppi_neighbor_expression_random_projectio_e705: -0.0001
- pair_shared_pathway_times_ppi_density_e7_e706: -0.0000
- ppi_neighbor_external_response_weighted_e720: -0.0000
- target_external_times_ppi_overlap_e721: -0.0001
- pair_target_gene_set_entropy_difference_e723: -0.0000
- pair_target_shared_tf_weighted_e800_e732: -0.0000
- target_spearman_coexpr_control_e801_e733: -0.0003
- target_ppi_degree_sum_e802_e734: -0.0001
- external_response_cosine_to_targets_e803_e735: -0.0010
- weighted_pathway_overlap_with_targets_e8_e736: -0.0001
- pair_target_expression_random_projection_e738: -0.0001
- weighted_pathway_overlap_e743: -0.0001
- target_ppi_neighbor_external_delta_e744: -0.0000
- max_target_coexpression_e745: -0.0001
- pair_weighted_shared_pathway_count_e746: -0.0000

## FAILED FEATURES
- EXP_0010 additivity_residual_e21_e10 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0016 target_self_response_magnitude_e16 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0021 pair_departure_from_additive_e21 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0058 target_control_expression_random_project_e58 [test]: feature failed after 2 attempts: public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_d
- EXP_0065 external_replogle_cosine_sim_e65 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0073 pair_shared_tf_count_e73 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0081 pair_target_external_response_similarity_e81 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0125 pair_target_external_response_diff_norm_e125 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0143 pair_additive_residual_e99_e143 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0149 pair_target_shared_downstream_count_e149 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0155 pair_external_replogle_residual_e155 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0159 pair_target_coexpr_residual_e147_e159 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0161 external_replogle_target_similarity_e149_e161 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0179 similar_pert_external_cosine_knn_e166_e179 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0196 external_additive_pair_cosine_e196 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0207 target_control_expr_random_proj_e207 [test]: feature failed after 2 attempts: oke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-
- EXP_0210 similar_pert_external_response_knn_cosin_e210 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0228 pair_target_expr_product_external_e11_e228 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0229 pair_target_shared_downstream_e12_e229 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0239 target_network_gene_set_overlap_e239 [guard]: iteration over a set of objects (line 27) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0240 pair_target_shared_downstream_prior_e240 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0270 target_expr_random_projection_e270 [test]: feature failed after 2 attempts: c), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_fro
- EXP_0276 pair_target_shortest_path_external_sign_e276 [guard]: iteration over a set of objects (line 69) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0278 pair_additive_residual_e278 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0290 external_response_target_gene_similarity_e290 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0307 pair_target_external_delta_ratio_e307 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0321 external_response_percentile_target_inte_e321 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0326 pair_target_signed_shortest_path_e326 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0339 external_response_magnitude_times_contro_e339 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0349 shared_protein_domains_count_e349 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0364 external_response_projection_target_e364 [test]: feature failed after 2 attempts: _w4_r2/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
                  
- EXP_0387 target_external_random_projection_e387 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0397 target_external_delta_times_target_contr_e397 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0410 external_response_corr_with_target_neigh_e410 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0418 pair_target_shared_ppi_neighbors_e450_e418 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0444 pair_shared_coexpr_module_size_e444 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0449 target_coexpr_random_projection_e449 [test]: feature failed after 2 attempts: .py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/
- EXP_0453 control_expr_rank_times_pair_prior_edge_e453 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0461 external_coexpr_random_projection_e461 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0466 pair_target_shared_ppi_neighbor_count_e466 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0467 pair_target_shared_ppi_neighbor_weighted_e467 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0469 pair_target_shared_pathway_external_weig_e469 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0471 target_external_delta_times_ppi_to_g_e471 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0474 random_projection_target_gene_external_c_e474 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0475 pair_target_shared_tf_weighted_external__e475 [test]: feature failed after 2 attempts: ila/runs/norman_ds_from_n2_w4_r2/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.f
- EXP_0476 pair_target_shared_ppi_neighbors_e471_e476 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0477 ppi_diffusion_external_seed_e472_e477 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0478 pair_target_external_delta_product_e473_e478 [test]: feature failed after 2 attempts: rs/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_from_n2_w4_r2/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().c
- EXP_0486 additive_singles_times_shared_tf_e475_e486 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0505 target_ppi_neighbor_external_response_e505 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0508 target_tf_neighbor_count_e508 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0517 external_delta_times_target_control_e517 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0518 pair_target_prior_shortest_path_e518 [guard]: iteration over a set of objects (line 53) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0520 external_delta_projection_interaction_e520 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0531 pair_target_pathway_jaccard_e521_e531 [guard]: iteration over a set of objects (line 30) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0534 pair_target_ppi_weighted_shortest_path_e_e534 [test]: feature failed after 2 attempts: w4_r2/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache)
- EXP_0547 pair_external_delta_product_e547 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0548 pair_external_sum_times_control_expr_e548 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0549 pair_shared_ppi_neighbor_weighted_e549 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0550 pair_external_diff_times_shared_pathways_e550 [test]: feature failed after 2 attempts: , line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andr
- EXP_0558 pair_prior_edge_times_external_sum_e550_e558 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0559 pair_shared_pathway_times_external_produ_e559 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0561 target_coherence_times_external_sum_e553_e561 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0562 pair_shared_tf_times_external_diff_e554_e562 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0575 ppi_neighbor_external_response_sum_e575 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0577 external_delta_rank_gene_e577 [test]: feature failed after 2 attempts: w4_r2/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache)
- EXP_0627 additive_singles_weighted_by_ppi_distanc_e627 [guard]: iteration over a set of objects (line 82) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0650 ppi_neighbor_control_expr_random_project_e650 [test]: feature failed after 2 attempts: ipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "
- EXP_0652 ppi_neighbor_external_response_e652 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0661 external_response_outer_product_random_p_e661 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0662 pair_coherence_times_external_delta_diff_e662 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0664 ppi_neighbor_external_delta_weighted_sum_e664 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0667 target_set_functional_coherence_squared_e667 [guard]: iteration over a set of objects (line 32) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0668 similar_pert_knn_times_additive_singles_e668 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0683 pair_prior_edge_times_shared_tf_exxx_e683 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0684 external_response_outer_product_random_p_e684 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0692 external_delta_ppi_weighted_sum_e692 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0693 pair_shared_pathway_times_additive_e693 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0701 target_set_ppi_density_e701_e701 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0702 target_set_ppi_density_e701_e702 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0707 pair_shared_pathway_times_ppi_density_e7_e707 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0722 similar_pert_knn_additive_profile_e722 [test]: feature failed after 2 attempts: rs/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_from_n2_w4_r2/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().c
- EXP_0726 target_ppi_external_random_projection_e726 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0727 pair_target_shared_tf_count_squared_e727 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0742 loo_additive_pair_response_e742 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111

## SURPRISING RESULTS
- none

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0729 | config | 0.6693 | 0.7259 | -0.0566 |
| EXP_0709 | config | 0.6693 | 0.7259 | -0.0566 |
| EXP_0747 | config | 0.6693 | 0.7259 | -0.0566 |
| EXP_0003 | baseline | 0.6313 | 0.7126 | -0.0813 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0729 | 0.015 / 0.005 | 0.985 / 0.989 | 0.927 / 0.976 | 0.158 / 0.102 | 0.916 / 0.942 | 0.769 / 0.853 |
| EXP_0709 | 0.015 / 0.005 | 0.985 / 0.989 | 0.927 / 0.976 | 0.158 / 0.102 | 0.916 / 0.942 | 0.769 / 0.853 |
| EXP_0747 | 0.009 / 0.005 | 0.985 / 0.989 | 0.958 / 0.976 | 0.153 / 0.102 | 0.916 / 0.941 | 0.783 / 0.852 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0729 | 0.581 / 0.563 | 0.735 / 0.767 | 0.533 / 0.520 | 0.944 / 0.949 | 0.851 / 0.871 | 0.962 / 0.972 |
| EXP_0709 | 0.581 / 0.563 | 0.736 / 0.767 | 0.534 / 0.520 | 0.945 / 0.949 | 0.851 / 0.871 | 0.962 / 0.972 |
| EXP_0747 | 0.588 / 0.563 | 0.745 / 0.767 | 0.546 / 0.524 | 0.947 / 0.950 | 0.859 / 0.873 | 0.967 / 0.972 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0729 | 0.745 / 0.690 | 0.013 / 0.006 | 0.798 / 0.790 | 0.555 / 0.486 | 0.916 / 0.895 |
| EXP_0709 | 0.745 / 0.690 | 0.013 / 0.006 | 0.798 / 0.790 | 0.555 / 0.486 | 0.917 / 0.895 |
| EXP_0747 | 0.748 / 0.690 | 0.009 / 0.006 | 0.794 / 0.785 | 0.561 / 0.489 | 0.919 / 0.896 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1841.44
- Mean CPU s/experiment: 1.47
- Gain per CPU-hour: 0.1503
- Gain per USD: 0.0266
- LLM cost per completed experiment: $0.00231

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_from_n2_w4_r2 --experiment EXP_0729`
