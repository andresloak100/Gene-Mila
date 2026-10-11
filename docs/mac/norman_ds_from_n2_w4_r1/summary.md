# RUN SUMMARY

Run `norman_ds_from_n2_w4_r1` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `076282c71b`)

- Duration: 20.1 min
- Workers: 4
- Experiments proposed: 786
- Experiments completed: 565 (plus baselines; deepseek:deepseek-v4-pro: 317, python:exploit: 128, python:warm_start: 1, sweep(deepseek:deepseek-v4-pro): 119)
- Experiments failed / rejected / killed / not started: 76 / 26 / 3 / 5
- Unique hypotheses: 778 (replicated: 8); duplicate configurations skipped: 101
- CPU hours: 0.2655
- LLM (worker): 521 calls, 903710 in / 393416 out / 439168 cached tokens, $0.6141
- LLM (planner): 62 calls, 325467 in / 132729 out / 104576 cached tokens, $0.8218

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6197

## BEST PERFORMANCE
EXP_0681: pearson_delta = 0.6543 (ridge, alpha=20000.0)

## IMPROVEMENT
0.0346 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_singles_e15: coefficient +0.0657
- response_components_e14[0]: coefficient +0.0201
- response_components_e14[1]: coefficient +0.0149
- response_components_e14[3]: coefficient +0.0072
- response_components_e14[2]: coefficient +0.0067
- is_target: coefficient +0.0050
- external_random_projection_multicomp_e15_e161[1]: coefficient +0.0032
- external_random_projection_multicomp_e15_e161[0]: coefficient -0.0029
- additive_singles_external_product_e198: coefficient +0.0029
- external_random_projection_multicomp_e15_e161[2]: coefficient +0.0023
- external_random_projection_multicomp_e15_e161[4]: coefficient +0.0021
- target_level_e11: coefficient +0.0020
- external_direct_squared_e39: coefficient +0.0013
- external_direct_replogle2022_k562_e16_e20: coefficient +0.0013
- control_mean_times_external_direct_e282: coefficient +0.0013
- partial_corr_target_output_e28: coefficient +0.0011
- external_random_projection_multicomp_e15_e161[3]: coefficient +0.0011
- pair_external_delta_product_e184: coefficient -0.0006
- shared_gene_set_count_e168: coefficient -0.0004
- external_random_projection_seed2_e252[4]: coefficient -0.0004
- external_random_projection_seed2_e252[2]: coefficient -0.0004
- external_random_projection_seed2_e252[3]: coefficient +0.0003
- external_random_projection_seed2_e252[0]: coefficient +0.0001
- external_random_projection_seed2_e252[1]: coefficient -0.0001

## DISCOVERY LINEAGE
EXP_0007 [config] score 0.6525
    ↳ EXP_0039 [external_direct_squared_e39] score 0.6526
        ↳ EXP_0065 [external_direct_sin_transform_e65] score 0.6530
            ↳ EXP_0070 [config] score 0.6530
                ↳ EXP_0085 [pair_external_rank_product_e85] score 0.6532
                    ↳ EXP_0110 [config] score 0.6532
                        ↳ EXP_0120 [config] score 0.6532
                            ↳ EXP_0161 [external_random_projection_multicomp_e15_e161] score 0.6533
                                ↳ EXP_0165 [config] score 0.6533
                                    ↳ EXP_0168 [shared_gene_set_count_e168] score 0.6533
                                        ↳ EXP_0184 [pair_external_delta_product_e184] score 0.6533
                                            ↳ EXP_0198 [additive_singles_external_product_e198] score 0.6538
                                                ↳ EXP_0209 [config] score 0.6538
                                                    ↳ EXP_0221 [config] score 0.6538
                                                        ↳ EXP_0252 [external_random_projection_seed2_e252] score 0.6539
                                                            ↳ EXP_0282 [control_mean_times_external_direct_e282] score 0.6540
                                                                ↳ EXP_0309 [config] score 0.6540
                                                                    ↳ EXP_0314 [config] score 0.6541
                                                                        ↳ EXP_0333 [config] score 0.6541
                                                                            ↳ EXP_0368 [config] score 0.6542
                                                                                ↳ EXP_0386 [config] score 0.6542
                                                                                    ↳ EXP_0434 [config] score 0.6542
                                                                                        ↳ EXP_0453 [config] score 0.6542
                                                                                            ↳ EXP_0463 [config] score 0.6542
                                                                                                ↳ EXP_0506 [config] score 0.6542
                                                                                                    ↳ EXP_0630 [config] score 0.6543
                                                                                                        ↳ EXP_0681 [config] score 0.6543

## MOST USEFUL FEATURES
- additive_singles_e15_e21 (EXP_0021): +0.0724. Sum over the perturbation's target genes of the mean training delta of each target's single-gene perturbation, excluding the current perturbation from training data.
- external_direct_replogle2022_k562_e16_e20 (EXP_0020): +0.0067. Sum of sign-flipped Replogle 2022 K562 CRISPRi screen deltas of the perturbation's target gene(s), broadcast to all genes.
- target_coexpression_e8 (EXP_0008): +0.0008. Control-cell Pearson co-expression of the perturbation target(s) with each gene g.
- additive_singles_external_product_e198 (EXP_0198): +0.0005. Product of the additive single-gene response and the sign-flipped external Replogle2022_K562 delta: for pairs, the product with the pairwise external delta product; for singles, the product with the external direct delta.
- external_direct_sin_transform_e65 (EXP_0065): +0.0004. Sine of the scaled external direct delta feature.
- external_direct_sin_transform_e66 (EXP_0066): +0.0004. Sine transform of the external direct Replogle2022 K562 delta feature.
- external_direct_squared_e39 (EXP_0039): +0.0002. Square of the sum of sign-flipped external direct deltas of the perturbation's targets.
- pair_external_rank_product_e85 (EXP_0085): +0.0002. Product of ranks (by absolute value) of the sign-flipped external Replogle2022_K562 deltas of the two targets in a pair perturbation; 0 for single-gene perturbations.
- control_mean_times_external_direct_e282 (EXP_0282): +0.0001. Product of gene g's control mean expression and the sum of sign-flipped external Replogle2022_K562 deltas of perturbation p's targets.
- external_random_projection_seed2_e252 (EXP_0252): +0.0001. A low-dimensional random projection of the sign-flipped external Replogle delta vector for the perturbation's target(s), using a different random seed.

## FEATURES THAT DID NOT HELP
- similar_target_knn_response_e9: -0.0221
- pair_additivity_departure_e10: -0.0071
- pathway_shared_membership_e11: -0.0002
- ppi_network_diffusion_e14: -0.0002
- target_expression_level_e15: -0.0001
- ppi_propagation_score_e16: -0.0001
- target_expression_level_e17: -0.0000
- shared_pathway_score_e18: -0.0002
- pca_program_alignment_e19: -0.0003
- target_perturbation_magnitude_e26: -0.0001
- control_mean_rank_e27: -0.0039
- dropout_rate_e30: -0.0034
- weighted_additive_singles_e31: -0.0004
- pair_external_concordance_e38: -0.0002
- shared_tf_regulation_e57: -0.0000
- target_activation_strength_e55_e71: -0.0002
- pair_external_delta_product_e56_e72: -0.0000
- target_self_response_magnitude_e57_e73: -0.0002
- pair_shared_tf_count_e58_e74: -0.0001
- pair_target_expression_rank_product_e59_e75: -0.0001
- external_delta_correlation_with_target_e_e76: -0.0001
- pair_external_delta_product_e84: -0.0000
- pair_shared_pathway_count_e87: -0.0000
- external_direct_squared_target_e88: -0.0008
- pair_target_expression_product_e89: -0.0000
- shared_tf_regulation_score_e96: -0.0000
- target_output_expression_ratio_e97: -0.0002
- pair_target_sum_times_output_mean_e98: -0.0008
- external_delta_rank_product_signed_e99: -0.0001
- pair_ppi_shortest_path_length_e100: -0.0000
- external_delta_random_projection_e104: -0.0000
- pair_external_sum_squared_e105: -0.0001
- pair_external_delta_abs_product_e106: -0.0000
- pair_external_min_abs_e107: -0.0001
- pair_external_max_abs_e108: -0.0003
- pair_external_delta_abs_diff_e122: -0.0001
- pair_shared_pathway_count_e123: -0.0000
- target_coexpr_weighted_by_response_e125: -0.0007
- pair_shared_gene_set_count_e137: -0.0000
- pair_ppi_shortest_path_e138: -0.0000
- pair_external_rank_corr_e139: -0.0003
- pair_target_expression_product_e140: -0.0000
- pair_target_coexpression_e146_e147: -0.0011
- jaccard_pathway_overlap_e149_e150: -0.0002
- ppi_shortest_distance_e150_e151: -0.0001
- ppi_shortest_path_to_target_e166: -0.0001
- target_coexpression_control_e167: -0.0002
- additive_singles_interaction_e170: -0.0000
- external_random_projection_per_perturbat_e181: -0.0000
- external_delta_magnitude_e182: -0.0000
- external_delta_rank_percentile_e183: -0.0001
- shared_gene_set_jaccard_e185: -0.0003
- external_internal_sign_consistency_e187: -0.0000
- ppi_neighbor_sign_agreement_e192: -0.0001
- pair_external_delta_product_e193: -0.0000
- external_delta_target_l2norm_e194: -0.0000
- external_delta_ppi_neighbor_agreement_e200: -0.0000
- external_delta_random_fourier_e205: -0.0002
- pair_gene_set_both_targets_count_e210: -0.0000
- ppi_pair_gene_shortest_path_e211: -0.0001
- ppi_pair_pagerank_score_e212: -0.0004
- pair_external_product_times_additive_e214: -0.0001
- similar_pert_knn_external_direct_e215: -0.0002
- external_direct_rff_multiscale_e216: -0.0015
- pair_shared_tf_count_e223: -0.0001
- pair_target_coexpression_e224: -0.0000
- pair_external_delta_similarity_e225: -0.0002
- additive_singles_shared_gene_set_product_e226: -0.0001
- ppi_neighbor_external_delta_mean_e240: -0.0001
- shared_pathway_weighted_count_e241: -0.0001
- additive_singles_external_rank_weighted_e244: -0.0000
- rank_weighted_additive_singles_e254: -0.0014
- pair_external_cosine_similarity_e257: -0.0000
- pair_shared_tf_count_e263: -0.0001
- additive_singles_rank_product_interactio_e264: -0.0006
- shared_gene_set_external_weighted_e267: -0.0003
- additive_external_poly2_e268: -0.0015
- ppi_shortest_path_to_target_e278: -0.0001
- weighted_shared_gene_set_count_e279: -0.0001
- tf_coregulation_count_e280: -0.0000
- external_delta_corr_with_target_e281: -0.0006
- pair_ppi_shortest_path_external_weighted_e289: -0.0000
- shared_tf_regulation_count_e291: -0.0000
- external_delta_rank_corr_target_vs_g_e292: -0.0001
- additive_singles_sqrt_abs_e293: -0.0000
- external_additive_random_projection_seed_e295: -0.0000
- shared_gene_set_count_external_weighted_e296: -0.0001
- shared_gene_set_count_inverse_size_e300: -0.0001
- cosine_external_delta_target_indicator_e301: -0.0000
- pair_shared_tf_count_e315: -0.0001
- gene_external_delta_rank_pct_e316: -0.0003
- pair_ppi_weighted_shortest_path_e318: -0.0001
- covariance_random_projection_target_e329: -0.0000
- weighted_ppi_shortest_path_to_target_e334: -0.0001
- tf_regulon_overlap_score_e335: -0.0007
- target_expression_percentile_in_pathway_e337: -0.0002
- ppi_adjacency_random_projection_e341: -0.0001
- pair_shared_tf_count_e344: -0.0001
- pair_target_control_coexpression_e346: -0.0001
- weighted_shared_gene_set_count_e347: -0.0001
- target_ppi_degree_e348: -0.0001
- target_external_delta_norm_e349: -0.0000
- ppi_adjacency_random_projection_e351: -0.0001
- ppi_neighbor_corr_e300_e355: -0.0001
- ppi_degree_external_delta_e301_e356: -0.0001
- shared_tf_targets_e302_e357: -0.0002
- control_mean_times_additive_singles_e304_e359: -0.0049
- random_projection_external_additive_e305_e367: -0.0002
- pair_tf_overlap_score_e369: -0.0002
- weighted_shared_gene_set_count_e370: -0.0002
- external_delta_rank_percentile_e371: -0.0002
- target_level_times_additive_response_e372: -0.0015
- ppi_shortest_path_to_target_e373: -0.0002
- ppi_adjacency_target_mask_random_proj_e376: -0.0003
- ppi_shortest_path_to_target_e378: -0.0002
- target_gene_set_overlap_norm_e379: -0.0002
- target_mean_coexpression_signed_e381: -0.0013
- ppi_degree_times_external_delta_e382: -0.0001
- target_gene_set_jaccard_e385: -0.0005
- ppi_shortest_path_to_target_e387: -0.0006
- target_gene_set_enrichment_e389: -0.0005
- target_coexpression_signed_e391: -0.0015
- external_delta_random_fourier_e394: -0.0011
- ppi_distance_weighted_external_delta_e395: -0.0006
- pair_shared_pathway_count_with_g_e396: -0.0005
- additive_external_abs_difference_e398: -0.0008
- target_gene_set_enrichment_e399: -0.0005
- ppi_degree_times_external_delta_e400: -0.0004
- ppi_adjacency_random_projection_e401: -0.0014
- additive_singles_squared_e403_e407: -0.0005
- additive_times_external_sum_e404_e408: -0.0004
- additive_singles_rff_e405_e411: -0.0013
- additive_singles_times_pair_rank_product_e418: -0.0006
- weighted_shared_gene_set_count_e419: -0.0004
- ppi_shortest_path_length_e421: -0.0006
- ppi_adjacency_random_projection_e423: -0.0009
- shared_gene_set_count_pair_union_e427: -0.0005
- target_coexpression_with_g_e428: -0.0015
- external_delta_of_gene_g_e429: -0.0005
- additive_singles_times_external_direct_e431: -0.0006
- random_fourier_additive_singles_e433: -0.0015
- target_coexpr_ppi_neighborhood_e437: -0.0007
- external_delta_rank_in_shared_sets_e438: -0.0011
- target_ppi_adjacency_random_projection_e448: -0.0006
- pair_shared_tf_count_e449: -0.0005
- ppi_pair_distance_e300_e454: -0.0006
- shared_tf_regulation_e301_e455: -0.0006
- max_gene_set_jaccard_e302_e456: -0.0007
- ppi_weighted_external_delta_e303_e457: -0.0007
- additive_singles_times_target_level_e304_e458: -0.0002
- ppi_min_shortest_path_e466: -0.0003
- shared_tf_target_score_e467: -0.0002
- max_jaccard_target_gene_sets_e469: -0.0002
- ppi_shortest_path_to_target_e477: -0.0003
- gene_set_overlap_target_gene_e478: -0.0002
- gene_external_delta_replogle_e479: -0.0002
- is_transcription_factor_gene_e481: -0.0004
- ppi_adjacency_random_projection_gene_e484: -0.0003
- max_jaccard_gene_set_similarity_e485: -0.0002
- idf_weighted_gene_set_overlap_e486: -0.0003
- pair_target_sum_times_gene_external_delt_e487: -0.0002
- triple_external_delta_product_e488: -0.0001
- target_expression_times_external_sum_e489: -0.0002
- ppi_random_projection_target_gene_e492: -0.0003
- ppi_random_projection_target_gene_e493: -0.0003
- ppi_heat_kernel_score_e494: -0.0002
- weighted_shared_gene_set_score_e495: -0.0003
- coexpression_shift_target_gene_e496: -0.0005
- rank_product_times_additive_singles_e497: -0.0001
- random_fourier_external_direct_e500: -0.0002
- weighted_shared_gene_set_count_e517: -0.0003
- ppi_row_random_projection_e518: -0.0003
- ppi_shortest_path_count_e300_e530: -0.0003
- shared_gene_set_size_weighted_e301_e531: -0.0003
- external_delta_times_ppi_degree_e302_e532: -0.0002
- target_control_correlation_e304_e534: -0.0004
- ppi_random_projection_target_gene_e305_e543: -0.0007
- ppi_shortest_path_length_to_gene_e548: -0.0003
- ppi_shared_neighbor_count_e549: -0.0002
- gene_set_jaccard_targets_gene_e550: -0.0006
- pair_external_rank_sum_e565: -0.0003
- control_mean_times_gene_external_direct_e566: -0.0002
- external_direct_normalized_by_variance_e569: -0.0002
- ppi_min_dist_times_external_delta_e577: -0.0002
- ppi_neighbor_external_sum_e578: -0.0002
- pair_external_sum_squared_e579: -0.0005
- external_delta_times_target_rank_e580: -0.0002
- shared_gene_set_external_weighted_e581: -0.0005
- ppi_adjacency_random_projection_e582: -0.0006
- pair_external_product_over_ppi_distance_e583: -0.0002
- additive_singles_times_external_direct_e586: -0.0004
- pair_target_expression_product_e587: -0.0002
- ppi_weighted_external_delta_e588: -0.0004
- external_delta_over_control_e590: -0.0003
- pair_shared_gene_set_count_e591: -0.0002
- ppi_adjacency_random_projection_e592: -0.0011
- external_ppi_neighbor_weighted_e590_e593: -0.0004
- ppi_external_random_projection_e593_e604: -0.0008
- shared_gene_set_ppi_neighbor_e594_e605: -0.0005
- pair_external_rank_ratio_e608: -0.0002
- additive_singles_times_control_mean_e609: -0.0049
- ppi_edge_count_times_external_sum_e610: -0.0003
- ppi_random_projection_seed3_e619: -0.0010
- ppi_min_shortest_path_to_target_e622: -0.0003
- shared_gene_set_count_external_weighted_e623: -0.0005
- pair_external_sum_times_additive_e625: -0.0004
- random_projection_ppi_external_e626: -0.0007
- random_projection_ppi_external_e627: -0.0007
- normalized_shared_gene_set_count_e638: -0.0003
- min_ppi_shortest_path_to_target_e640: -0.0003
- ppi_adjacency_random_projection_e642: -0.0007
- ppi_min_shortest_path_pair_e647: -0.0003
- shared_gene_set_specificity_weighted_e648: -0.0003
- additive_singles_times_ppi_inv_distance_e649: -0.0000
- pair_external_delta_percentile_product_e650: -0.0003
- ppi_random_projection_seed3_e657: -0.0010
- external_direct_squared_times_additive_s_e658: -0.0004
- ppi_min_shortest_path_to_output_e659: -0.0003
- shared_gene_set_specificity_weighted_e660: -0.0003
- pair_external_percentile_rank_product_e661: -0.0003
- shared_tf_target_count_e662: -0.0003
- additive_singles_x_target_level_e663: -0.0000
- pair_external_sign_disagreement_e674: -0.0002
- pair_additive_singles_product_e675: -0.0003
- shared_gene_set_specificity_weighted_e676: -0.0004
- ppi_min_shortest_path_e677: -0.0003
- shared_tf_regulation_count_e688: -0.0003
- pair_target_expression_product_e689: -0.0002
- shared_gene_set_specificity_score_e691: -0.0003
- shared_tf_regulators_count_e705: -0.0003
- target_output_coexpr_percentile_e706: -0.0004
- pair_gene_set_specificity_overlap_e707: -0.0004
- additive_singles_loo_times_external_dire_e720: -0.0003
- target_output_external_rank_product_e721: -0.0004
- pair_target_shared_gene_sets_e722: -0.0003
- target_output_external_cosine_e723: -0.0004
- external_random_projection_seed3_e731: -0.0003
- additive_singles_loo_e735: -0.0003
- shared_gene_set_jaccard_e737: -0.0006
- target_expression_random_projection_e740: -0.0003
- pair_target_coexpression_product_e743: -0.0005
- shared_gene_set_rank_e744: -0.0004
- external_delta_squared_times_target_coun_e745: -0.0010
- pair_external_rank_product_e758: -0.0003

## FAILED FEATURES
- EXP_0023 pair_target_ppi_edge_e23 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0033 target_gene_set_enrichment_e33 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0037 external_direct_x_is_target_e37 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0040 external_direct_rank_e40 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0049 external_direct_sin_transform_e49 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0055 pair_external_delta_product_e55 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0056 target_external_magnitude_e56 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0124 pair_ppi_shortest_path_e124 [guard]: iteration over a set of objects (line 64) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0132 external_random_projection_e132 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0136 pair_ppi_edge_exists_e136 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0143 external_random_projection_e143 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0149 target_external_rank_sum_e148_e149 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0169 ppi_neighbor_external_response_e169 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0180 external_random_projection_per_perturbat_e180 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0186 ppi_neighbor_external_delta_avg_e186 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0190 ppi_neighbor_external_delta_mean_e190 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0191 external_delta_rank_percentile_e191 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0197 external_delta_random_fourier_e197 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0199 ppi_shortest_path_length_pair_e199 [guard]: iteration over a set of objects (line 71) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0202 pair_shared_tf_count_e202 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0213 additive_singles_times_external_direct_e213 [test]: feature failed after 2 attempts: ver/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else 
- EXP_0222 pair_ppi_shortest_path_length_e222 [guard]: iteration over a set of objects (line 41) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0242 target_expr_external_product_e242 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0243 pair_external_delta_ratio_e243 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0245 pair_coexpr_additivity_product_e245 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0253 external_norm_corr_interaction_e253 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0255 target_external_entropy_e255 [test]: feature failed after 2 attempts:  393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarri
- EXP_0256 pair_external_harmonic_mean_e256 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0260 external_random_fourier_expansion_e260 [test]: feature failed after 2 attempts: rees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.ca
- EXP_0285 random_projection_external_additive_e285 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0290 pair_external_delta_product_times_coexpr_e290 [guard]: use of 'getattr' not allowed
- EXP_0299 pair_external_delta_abs_diff_e299 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0310 nonlinear_random_projection_external_add_e310 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0317 pair_external_sum_times_shared_sets_e317 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0336 pair_target_regulon_similarity_e336 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0338 additive_response_residual_e338 [guard]: access to ._targets not allowed
- EXP_0345 control_expr_corr_with_external_delta_e345 [test]: feature failed after 2 attempts: gs.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norma
- EXP_0358 pair_external_delta_ratio_e303_e358 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0374 pair_external_delta_sum_squared_e374 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0380 pair_external_rank_sum_e380 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0388 pair_target_ppi_distance_e388 [guard]: iteration over a set of objects (line 46) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0390 external_delta_times_ppi_degree_e390 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0397 external_train_response_rank_correlation_e397 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0404 pair_external_log_ratio_e400_e404 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0405 external_sum_times_control_mean_e401_e405 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0406 external_sum_rank_e402_e406 [test]: feature failed after 2 attempts: la/runs/norman_ds_from_n2_w4_r1/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.fl
- EXP_0420 additive_external_ratio_e420 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0422 gene_external_delta_e422 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0426 ppi_shortest_path_between_targets_e426 [guard]: iteration over a set of objects (line 44) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0430 target_gene_external_delta_product_e430 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0439 pair_external_product_ppi_weighted_e439 [guard]: iteration over a set of objects (line 81) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0461 external_direct_rff_e305_e461 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0468 pair_ppi_dist_times_external_product_e468 [guard]: iteration over a set of objects (line 56) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0470 external_delta_rank_gene_g_e470 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0473 random_fourier_external_direct_e473 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0480 pair_ppi_distance_external_weighted_e480 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0514 external_delta_rank_gene_e514 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0515 external_rank_product_gene_pert_e515 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0516 ppi_min_distance_to_gene_e516 [guard]: top-level Try statement not allowed
- EXP_0533 pair_ppi_distance_external_product_e303_e533 [guard]: iteration over a set of objects (line 83) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0560 ppi_distance_times_external_direct_e560 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0561 external_direct_rank_gene_e561 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0567 pair_external_abs_sum_e567 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0568 pair_external_sign_agreement_e568 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0572 external_direct_decile_e572 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0589 additive_singles_rank_e589 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111
- EXP_0594 pair_ppi_dist_times_external_product_e59_e594 [guard]: iteration over a set of objects (line 91) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0595 external_delta_rank_among_targets_e592_e595 [test]: feature failed after 2 attempts: ds_from_n2_w4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(
- EXP_0607 pair_shared_genesets_times_external_sum_e607 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0611 pair_external_correlation_e611 [test]: feature failed after 2 attempts: s_from_n2_w4_r1/worktrees/EXP_0611/genemila/features/plugins/pair_external_correlation_e611.py", line 111, in compute
    v1 = get_vec(tg[0])
  File "/Users/andresarri
- EXP_0621 additive_external_direct_product_g_e621 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0624 external_delta_rank_percentile_g_e624 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0639 external_delta_abs_percentile_e639 [test]: feature failed after 2 attempts: line.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Us
- EXP_0641 additive_external_direct_product_e641 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0643 pair_external_sum_squared_e643 [guard]: use of 'getattr' not allowed
- EXP_0672 external_random_projection_seed3_e672 [test]: feature failed after 2 attempts: rktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args
- EXP_0673 tf_target_overlap_pair_e673 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0680 external_random_projection_seed3_e680 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0687 pair_ppi_shortest_distance_e687 [guard]: iteration over a set of objects (line 36) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0690 external_delta_abs_rank_percentile_e690 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0698 external_random_projection_seed3_e698 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0704 pair_ppi_shortest_path_distance_e704 [guard]: iteration over a set of objects (line 44) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0708 external_rank_product_e708 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0714 external_random_projection_target_output_e714 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0733 pair_ppi_shortest_path_e733 [guard]: iteration over a set of objects (line 41) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0734 pair_external_rank_product_e734 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0736 pair_external_sign_agreement_e736 [test]: feature failed after 2 attempts: ds_from_n2_w4_r1/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
        
- EXP_0741 target_expression_random_projection_e741 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0742 external_delta_times_target_expression_e742 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0746 pair_ppi_shortest_path_e746 [guard]: iteration over a set of objects (line 62) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0754 external_random_projection_seed3_e754 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0757 loo_additive_singles_external_product_e757 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0759 shared_gene_set_weighted_external_e759 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0760 pair_external_delta_diff_squared_e760 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0768 external_random_projection_pert_seed_e768 [test]: feature failed after 2 attempts: s/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache

## SURPRISING RESULTS
- similar_target_knn_response_e9 made the model worse (-0.0221) despite a linear model being able to ignore it (overfitting or scale issue)

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0681 | config | 0.6543 | 0.7192 | -0.0649 |
| EXP_0702 | config | 0.6543 | 0.7192 | -0.0649 |
| EXP_0630 | config | 0.6543 | 0.7192 | -0.0649 |
| EXP_0003 | baseline | 0.6197 | 0.7126 | -0.0929 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0681 | 0.007 / 0.005 | 0.984 / 0.988 | 0.965 / 0.974 | 0.171 / 0.115 | 0.907 / 0.935 | 0.764 / 0.837 |
| EXP_0702 | 0.007 / 0.005 | 0.984 / 0.988 | 0.965 / 0.974 | 0.171 / 0.115 | 0.907 / 0.935 | 0.764 / 0.837 |
| EXP_0630 | 0.007 / 0.005 | 0.984 / 0.988 | 0.965 / 0.974 | 0.171 / 0.116 | 0.907 / 0.935 | 0.764 / 0.837 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0681 | 0.546 / 0.530 | 0.748 / 0.757 | 0.561 / 0.512 | 0.947 / 0.947 | 0.858 / 0.862 | 0.973 / 0.971 |
| EXP_0702 | 0.547 / 0.530 | 0.748 / 0.757 | 0.562 / 0.512 | 0.947 / 0.947 | 0.858 / 0.862 | 0.973 / 0.971 |
| EXP_0630 | 0.551 / 0.534 | 0.747 / 0.758 | 0.560 / 0.512 | 0.946 / 0.948 | 0.855 / 0.862 | 0.972 / 0.971 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0681 | 0.745 / 0.683 | 0.008 / 0.006 | 0.759 / 0.722 | 0.563 / 0.481 | 0.919 / 0.894 |
| EXP_0702 | 0.744 / 0.683 | 0.008 / 0.006 | 0.759 / 0.723 | 0.563 / 0.481 | 0.920 / 0.893 |
| EXP_0630 | 0.745 / 0.683 | 0.008 / 0.006 | 0.764 / 0.724 | 0.562 / 0.478 | 0.919 / 0.895 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1689.88
- Mean CPU s/experiment: 1.69
- Gain per CPU-hour: 0.1303
- Gain per USD: 0.0241
- LLM cost per completed experiment: $0.00254

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_from_n2_w4_r1 --experiment EXP_0681`
