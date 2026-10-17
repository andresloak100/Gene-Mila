# RUN SUMMARY

Run `norman_ds_addstart_w4_r0` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `ce1b530431`)

- Duration: 20.1 min
- Workers: 4
- Experiments proposed: 730
- Experiments completed: 581 (plus baselines; deepseek:deepseek-v4-pro: 332, python:exploit: 105, sweep(deepseek:deepseek-v4-pro): 144)
- Experiments failed / rejected / killed / not started: 70 / 12 / 0 / 3
- Unique hypotheses: 718 (replicated: 12); duplicate configurations skipped: 56
- CPU hours: 0.2947
- LLM (worker): 498 calls, 825879 in / 352539 out / 436608 cached tokens, $0.5424
- LLM (planner): 59 calls, 278824 in / 117984 out / 66688 cached tokens, $0.7502

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6108

## BEST PERFORMANCE
EXP_0724: pearson_delta = 0.6280 (ridge, alpha=0.01)

## IMPROVEMENT
0.0172 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_response: coefficient +0.0861
- target_mean_x_additive_e20: coefficient -0.0084
- additive_response_sq_e342: coefficient +0.0078
- shared_tf_regulators_pair_e374: coefficient +0.0059
- target_prior_outdegree_sq_x_additive_e291: coefficient +0.0058
- additive_response_squared_e351: coefficient -0.0054
- target_gene_set_specificity_x_additive_e717: coefficient +0.0051
- random_projection_best_features_e108[1]: coefficient -0.0049
- random_projection_best_features_e108[2]: coefficient +0.0048
- pair_target_ppi_distance_x_additive_e580: coefficient +0.0046
- target_variance_x_additive_e412: coefficient -0.0035
- target_ppi_degree_e64: coefficient -0.0034
- random_projection_best_features_e108[0]: coefficient -0.0034
- target_ppi_neighbor_coherence_e643: coefficient +0.0024
- abs_additive_x_target_mean_e662: coefficient -0.0018
- ppi_neighbor_coexpression_e628: coefficient -0.0016
- gene_set_overlap_x_additive_e486: coefficient -0.0015
- target_ppi_prior_degree_product_x_additi_e514: coefficient -0.0014
- prior_network_length2_path_count_e542: coefficient -0.0012
- pair_target_ppi_distance_sq_x_additive_e618: coefficient +0.0009
- pair_target_gene_set_jaccard_e533: coefficient -0.0008
- gene_screen_delta_sq_x_additive_e724: coefficient -0.0004
- target_prior_outdegree_x_additive_e221: coefficient +0.0003
- gene_set_overlap_fraction_g_e692: coefficient -0.0003
- gene_screen_delta_e365: coefficient +0.0002
- gene_screen_delta_x_additive_e459: coefficient +0.0000

## DISCOVERY LINEAGE
EXP_0007 [baseline] score 0.6154
    ↳ EXP_0020 [target_mean_x_additive_e20] score 0.6168
        ↳ EXP_0024 [config] score 0.6194
            ↳ EXP_0036 [config] score 0.6215
                ↳ EXP_0064 [target_ppi_degree_e64] score 0.6222
                    ↳ EXP_0085 [config] score 0.6222
                        ↳ EXP_0090 [config] score 0.6222
                            ↳ EXP_0108 [random_projection_best_features_e108] score 0.6253
                                ↳ EXP_0120 [config] score 0.6255
                                    ↳ EXP_0143 [config] score 0.6258
                                        ↳ EXP_0206 [config] score 0.6263
                                            ↳ EXP_0221 [target_prior_outdegree_x_additive_e221] score 0.6263
                                                ↳ EXP_0249 [config] score 0.6264
                                                    ↳ EXP_0291 [target_prior_outdegree_sq_x_additive_e291] score 0.6267
                                                        ↳ EXP_0311 [config] score 0.6267
                                                            ↳ EXP_0342 [additive_response_sq_e342] score 0.6267
                                                                ↳ EXP_0351 [additive_response_squared_e351] score 0.6268
                                                                    ↳ EXP_0365 [gene_screen_delta_e365] score 0.6268
                                                                        ↳ EXP_0369 [config] score 0.6268
                                                                            ↳ EXP_0374 [shared_tf_regulators_pair_e374] score 0.6268
                                                                                ↳ EXP_0387 [config] score 0.6268
                                                                                    ↳ EXP_0405 [config] score 0.6268
                                                                                        ↳ EXP_0412 [target_variance_x_additive_e412] score 0.6269
                                                                                            ↳ EXP_0459 [gene_screen_delta_x_additive_e459] score 0.6270
                                                                                                ↳ EXP_0463 [config] score 0.6270
                                                                                                    ↳ EXP_0486 [gene_set_overlap_x_additive_e486] score 0.6270
                                                                                                        ↳ EXP_0495 [config] score 0.6270
                                                                                                            ↳ EXP_0514 [target_ppi_prior_degree_product_x_additi_e514] score 0.6274
                                                                                                                ↳ EXP_0533 [pair_target_gene_set_jaccard_e533] score 0.6274
                                                                                                                    ↳ EXP_0542 [prior_network_length2_path_count_e542] score 0.6275
                                                                                                                        ↳ EXP_0580 [pair_target_ppi_distance_x_additive_e580] score 0.6277
                                                                                                                            ↳ EXP_0599 [config] score 0.6277
                                                                                                                                ↳ EXP_0618 [pair_target_ppi_distance_sq_x_additive_e618] score 0.6277
                                                                                                                                    ↳ EXP_0628 [ppi_neighbor_coexpression_e628] score 0.6278
                                                                                                                                        ↳ EXP_0643 [target_ppi_neighbor_coherence_e643] score 0.6278
                                                                                                                                            ↳ EXP_0662 [abs_additive_x_target_mean_e662] score 0.6279
                                                                                                                                                ↳ EXP_0692 [gene_set_overlap_fraction_g_e692] score 0.6279
                                                                                                                                                    ↳ EXP_0717 [target_gene_set_specificity_x_additive_e717] score 0.6280
                                                                                                                                                        ↳ EXP_0724 [gene_screen_delta_sq_x_additive_e724] score 0.6280

## MOST USEFUL FEATURES
- random_projection_best_features_e108 (EXP_0108): +0.0031. Concatenate several base features, standardize, then apply a fixed random Gaussian projection to reduce dimensionality.
- target_mean_x_additive_e20 (EXP_0020): +0.0015. Product of mean control expression of p's targets and the additive response row.
- target_ppi_degree_e64 (EXP_0064): +0.0007. Average PPI network degree of the perturbation's target gene(s), broadcast to all genes.
- target_ppi_prior_degree_product_x_additi_e514 (EXP_0514): +0.0004. Product of average PPI degree and average prior-network out-degree of the perturbation's target genes, multiplied by additive_response.
- ppi_rwr_score_from_targets_e27 (EXP_0027): +0.0004. Random-walk-with-restart stationary probability over the PPI network, seeded uniformly on the target gene(s) of each perturbation.
- target_ppi_degree_e51 (EXP_0051): +0.0004. Average PPI-network degree over the perturbation's target genes.
- target_prior_outdegree_sq_x_additive_e291 (EXP_0291): +0.0003. Squared average prior-network out-degree of p's target gene(s), multiplied row-wise by the additive response.
- pair_target_ppi_distance_x_additive_e580 (EXP_0580): +0.0002. Shortest path length between pair targets in PPI network times additive_response; 0 for singles.
- ppi_heat_diffusion_score_e52 (EXP_0052): +0.0002. Heat kernel diffusion score from perturbation targets over the PPI network.
- additive_response_x_target_percentile_e57 (EXP_0057): +0.0002. Product of additive_response and the percentile rank of the perturbation target's mean control expression (averaged for pairs).

## FEATURES THAT DID NOT HELP
- target_control_mean_e14: -0.0000
- target_control_product_e15: -0.0000
- pathway_overlap_count_e17: -0.0000
- ppi_network_distance_e18: -0.0001
- ppi_shortest_path_to_target_e26: -0.0001
- gene_set_overlap_with_targets_e28: -0.0000
- prior_network_target_to_gene_weight_e31: -0.0000
- additive_response_is_target_interaction_e32: -0.0001
- ppi_shortest_path_distance_e38: -0.0004
- prior_network_target_influence_e40: -0.0000
- target_expression_percentile_e41: -0.0005
- target_dropout_rate_e42: -0.0006
- additive_response_squared_e43: -0.0000
- target_replogle_magnitude_e50: -0.0000
- prior_network_coregulation_score_e53: -0.0001
- additive_response_squared_e56: -0.0008
- target_prior_outdegree_e65: -0.0002
- partial_corr_to_target_e73: -0.0000
- target_activation_magnitude_e78: -0.0007
- target_coexpression_with_gene_e79: -0.0012
- additive_response_x_target_percentile_e80: -0.0001
- additive_response_x_gene_ppi_degree_e81: -0.0020
- target_prior_outgoing_weight_e82: -0.0002
- target_replogle_magnitude_modulated_addi_e93: -0.0013
- additive_response_x_target_count_e94: -0.0049
- target_gene_coexpression_x_additive_e96: -0.0001
- gene_ppi_degree_x_additive_e97: -0.0020
- additive_response_x_target_ppi_degree_e103: -0.0000
- target_gene_coexpression_control_e104: -0.0012
- prior_network_max_weight_to_gene_e105: -0.0000
- target_replogle_magnitude_mean_e112: -0.0001
- additive_response_x_target_replogle_magn_e113: -0.0036
- target_mean_expression_percentile_e114: -0.0013
- additive_response_x_target_expression_pe_e115: -0.0004
- additive_response_x_target_ppi_degree_e116: -0.0000
- target_coexpression_vector_e119: -0.0012
- target_replogle_magnitude_loo_e122: -0.0000
- shared_tf_count_e124: -0.0001
- target_ppi_degree_variance_e126: -0.0000
- target_self_activation_magnitude_e133: -0.0004
- pair_target_synergy_score_e134: -0.0005
- target_control_variance_x_additive_e135: -0.0005
- target_neighbor_mean_expression_e136: -0.0005
- ppi_neighbor_replogle_mean_e145: -0.0005
- pair_target_ppi_path_redundancy_e146: -0.0006
- gene_set_overlap_with_all_targets_e147: -0.0006
- pair_target_coexpression_e148: -0.0006
- additive_x_target_betweenness_e149: -0.0007
- additive_x_target_variance_e150: -0.0015
- rff_target_expression_profile_e153: -0.0009
- pathway_overlap_with_targets_v2_e154: -0.0008
- ppi_distance_degree_weighted_e155: -0.0007
- prior_network_rwr_score_e156: -0.0005
- target_variance_x_additive_e157: -0.0004
- pair_target_coexpression_x_additive_e158: -0.0005
- rbf_ppi_embedding_features_e161: -0.0005
- target_variance_x_additive_e162: -0.0027
- gene_ppi_degree_x_additive_e163: -0.0005
- target_betweenness_x_additive_e164: -0.0016
- pair_coexpression_x_additive_e165: -0.0009
- distance_to_target_x_additive_e166: -0.0006
- prior_rwr_score_e169: -0.0005
- target_variance_x_additive_e170: -0.0004
- gene_variance_x_additive_e171: -0.0004
- target_entropy_x_additive_e172: -0.0006
- coexpression_x_additive_e173: -0.0027
- target_prior_degree_x_additive_e174: -0.0003
- rbf_rff_ppi_embedding_e177: -0.0012
- pair_target_ppi_degree_x_additive_e178: -0.0008
- prior_network_weight_from_targets_to_g_e179: -0.0006
- gene_set_jaccard_targets_g_e180: -0.0006
- target_entropy_x_additive_e181: -0.0006
- target_betweenness_x_additive_e182: -0.0004
- rff_ppi_embedding_similarity_e183: -0.0008
- ppi_neighborhood_similarity_e187: -0.0005
- gene_set_cosine_similarity_e188: -0.0006
- replogle_magnitude_x_additive_e189: -0.0007
- rff_ppi_embedding_x_additive_e199: -0.0047
- target_coresg_score_e200: -0.0006
- tfbs_overlap_count_e201: -0.0005
- prior_signed_influence_e202: -0.0006
- target_expression_specificity_e203: -0.0005
- weighted_pathway_overlap_e204: -0.0005
- rff_ppi_distance_e207: -0.0008
- target_prior_outdegree_e209: -0.0005
- target_mean_ppi_degree_x_additive_e210: -0.0047
- normalized_gene_set_overlap_e211: -0.0006
- tf_binding_similarity_to_targets_e212: -0.0006
- target_ppi_betweenness_e222: -0.0001
- tf_binding_similarity_to_targets_e223: -0.0002
- rff_best_features_no_leakage_e228: -0.0071
- target_control_variance_e229: -0.0005
- target_pair_coexpression_e231: -0.0000
- target_tf_count_e233: -0.0000
- target_shared_tf_count_e238: -0.0001
- pair_target_coexpression_modulation_e239: -0.0004
- target_mean_x_additive_squared_v2_e256: -0.0001
- target_ppi_degree_x_additive_squared_e257: -0.0017
- target_prior_outdegree_x_additive_square_e258: -0.0004
- pair_coexpression_x_additive_e259: -0.0014
- target_mean_x_additive_cubed_e260: -0.0012
- shared_tf_count_weighted_e273: -0.0002
- min_ppi_distance_to_targets_e274: -0.0004
- normalized_gene_set_overlap_e275: -0.0001
- mean_target_coexpression_with_g_e276: -0.0006
- target_prior_outdegree_standalone_e277: -0.0000
- target_ppi_random_projection_e284: -0.0002
- coexpression_profile_distance_e285: -0.0014
- target_pair_coexpression_e292: -0.0001
- target_pair_coexpression_e293: -0.0001
- shared_tf_count_e294: -0.0002
- shared_tf_count_e295: -0.0002
- ppi_rwr_score_v2_e296: -0.0005
- ppi_rwr_score_v2_e297: -0.0004
- ppi_adjacency_random_projection_e305: -0.0005
- ppi_adjacency_random_projection_e306: -0.0005
- target_ppi_adjacency_random_projection_e307: -0.0004
- tf_target_overlap_signature_e308: -0.0005
- additive_response_x_target_percentile_e317: -0.0001
- shared_tf_count_e318: -0.0001
- target_gene_control_projection_e319: -0.0017
- target_pair_shared_tf_count_e323: -0.0000
- additive_x_target_ppi_degree_sq_e324: -0.0033
- target_replogle_abs_mean_e341: -0.0001
- additive_sq_x_target_ppi_degree_e343: -0.0001
- target_gene_set_intersection_size_e353: -0.0000
- target_pair_control_correlation_e354: -0.0000
- shared_tf_count_e361: -0.0002
- mean_prior_weight_target_to_g_e362: -0.0000
- gene_ppi_degree_x_additive_e363: -0.0000
- mean_prior_out_edge_to_g_e373: -0.0000
- target_gene_set_overlap_fraction_e375: -0.0001
- additive_x_target_control_variance_e386: -0.0013
- target_gene_coexpression_x_additive_e391: -0.0002
- ppi_rwr_score_from_targets_v2_e392: -0.0002
- target_mean_variance_e393: -0.0006
- gene_set_jaccard_with_targets_e394: -0.0001
- additive_x_target_ppi_degree_e395: -0.0013
- random_projection_all_features_e404: -0.0039
- ppi_degree_norm_rwr_from_targets_e409: -0.0000
- pair_shared_prior_regulators_e410: -0.0001
- signed_coexpression_with_targets_e411: -0.0003
- target_prior_indegree_x_additive_e424: -0.0002
- target_mean_sq_x_additive_e426: -0.0003
- shared_tf_regulators_target_gene_e427: -0.0002
- random_projection_gene_screen_control_e438: -0.0025
- target_variance_x_ppi_degree_e443: -0.0006
- prior_outdegree_x_additive_sq_e444: -0.0009
- gene_set_jaccard_target_g_e446: -0.0001
- ppi_weighted_rwr_target_g_e447: -0.0002
- target_mean_x_additive_sq_e455: -0.0000
- target_ppi_degree_x_additive_sq_e456: -0.0001
- shared_tf_regulators_x_additive_e458: -0.0217
- target_variance_x_additive_sq_e460: -0.0002
- ppi_pair_intermediate_distance_e467: -0.0002
- weighted_shared_tf_regulators_pair_e468: -0.0002
- gene_set_overlap_both_targets_e469: -0.0000
- additive_x_shared_tf_pair_e471: -0.0342
- gene_ppi_degree_x_additive_e481: -0.0000
- target_mean_sq_x_additive_e485: -0.0016
- gene_ppi_degree_x_additive_e498: -0.0001
- gene_prior_outdegree_x_additive_e499: -0.0000
- pair_ppi_distance_x_additive_e501: -0.0006
- shared_tf_regulators_x_additive_e502: -0.0072
- pair_ppi_degree_x_additive_e505: -0.0040
- random_projection_gene_expr_x_additive_e506: -0.0000
- target_expression_cv_x_additive_e510: -0.0036
- pair_target_coexpression_x_additive_e511: -0.0003
- tf_regulator_overlap_target_gene_x_addit_e512: -0.0001
- pair_target_coexpression_x_additive_e524: -0.0003
- pair_ppi_distance_x_additive_e525: -0.0004
- pair_gene_set_overlap_x_additive_e526: -0.0113
- abs_gene_screen_delta_x_additive_sq_e527: -0.0000
- target_ppi_degree_x_additive_sq_e528: -0.0001
- target_ppi_degree_sq_x_additive_e535: -0.0090
- shared_ppi_neighbors_with_targets_e541: -0.0000
- random_projection_network_features_e549: -0.0005
- shared_ppi_community_with_targets_e550: -0.0001
- shared_ppi_neighbors_count_e552: -0.0000
- gene_set_overlap_x_additive_sq_e556: -0.0000
- target_tf_regulon_overlap_e560: -0.0000
- pair_shared_gene_set_count_e562: -0.0000
- target_ppi_community_overlap_e563: -0.0006
- nonlinear_random_projection_best_feature_e566: -0.0031
- target_ppi_degree_x_gene_screen_delta_e576: -0.0000
- target_variance_x_gene_screen_delta_e579: -0.0000
- shared_tf_regulators_x_additive_e581: -0.0350
- random_projection_all_current_e590: -0.0000
- target_gene_set_specificity_x_additive_e_e592: -0.0046
- prior_network_length3_path_count_e603_e594: -0.0001
- target_ppi_degree_x_gene_screen_delta_e6_e595: -0.0000
- shared_tf_regulators_gene_target_e605_e596: -0.0001
- random_projection_all_current_e606_e598: -0.0001
- ppi_community_comembership_e601: -0.0001
- target_gene_set_specificity_x_additive_e602: -0.0012
- tf_coregulation_g_target_e603: -0.0001
- pair_target_shared_tf_regulators_x_addit_e615: -0.0222
- gene_set_overlap_sq_x_additive_e616: -0.0000
- target_prior_outdegree_x_additive_sq_e617: -0.0000
- target_mean_x_additive_sq_e619: -0.0015
- gene_set_specificity_e621: -0.0000
- log_abs_additive_response_e622: -0.0048
- gene_set_specificity_x_additive_e627: -0.0002
- prior_downstream_abs_expr_x_additive_e629: -0.0005
- shared_tf_regulators_to_g_e630: -0.0001
- ppi_community_overlap_e631: -0.0000
- additive_x_target_ppi_degree_e632: -0.0055
- additive_response_signed_sqrt_e641: -0.0058
- pair_target_specific_gene_set_overlap_e642: -0.0000
- prior_network_length3_path_count_e644: -0.0001
- pair_target_gene_set_cosine_e646: -0.0000
- additive_response_signed_log_e649: -0.0020
- pair_target_prior_embedding_cosine_e650: -0.0001
- additive_response_signed_log_e652: -0.0060
- gene_set_overlap_both_targets_e654: -0.0000
- ppi_neighbor_screen_delta_random_project_e656: -0.0009
- shared_ppi_neighbors_x_additive_e658: -0.0004
- weighted_gene_set_similarity_e659: -0.0002
- shared_tf_regulators_x_additive_e660: -0.0316
- signed_log_additive_response_e673: -0.0000
- gene_screen_delta_x_target_mean_e674: -0.0009
- gene_set_overlap_target_mean_interaction_e676: -0.0001
- shared_tf_target_mean_interaction_e677: -0.0011
- tf_regulator_overlap_g_targets_e690: -0.0001
- ppi_neighbor_target_weighted_outdegree_e691: -0.0000
- prior_network_length3_path_count_e693: -0.0000
- ppi_distance_x_target_outdegree_e694: -0.0002
- gene_coexpression_with_target_average_e695: -0.0004
- random_projection_ppi_neighbor_expressio_e696: -0.0004
- ppi_community_overlap_e700_e702: -0.0000
- additive_x_gene_ppi_degree_e702_e704: -0.0000
- pair_target_coexpression_mean_e703_e705: -0.0006
- additive_sq_x_target_mean_e704_e706: -0.0027
- random_projection_ppi_neighbor_expr_e705_e713: -0.0002
- ppi_neighbor_expression_variance_e715: -0.0001
- pair_target_control_corr_e719: -0.0001
- random_projection_neighbor_screen_deltas_e721: -0.0005
- pair_target_control_corr_x_additive_e722: -0.0005
- pair_target_prior_overlap_x_additive_e723: -0.0016

## FAILED FEATURES
- EXP_0019 additive_response_x_is_target_e19 [test]: feature failed after 2 attempts: a/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  Fil
- EXP_0044 is_target_x_additive_response_e44 [test]: feature failed after 2 attempts: a/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  Fil
- EXP_0062 target_replogle_magnitude_e62 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0063 target_replogle_delta_sum_e63 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0066 additive_response_x_target_ppi_degree_e66 [test]: feature failed after 2 attempts: rees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.ca
- EXP_0095 prior_network_weight_x_additive_e95 [test]: feature failed after 2 attempts: ne-mila/runs/norman_ds_addstart_w4_r0/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out
- EXP_0100 random_feature_combination_projection_e100 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0109 random_projection_best_features_e109 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0110 target_replogle_magnitude_sum_e110 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0129 rff_best_features_e129 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0144 random_fourier_best_features_e144 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0152 rff_target_expression_profile_e152 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0186 target_coexpression_score_e186 [experiment]: IndexError: index 112 is out of bounds for axis 0 with size 112
- EXP_0198 rff_ppi_embedding_x_additive_e198 [test]: feature failed after 2 attempts: LEAKAGE non-deterministic output; label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p)); output depends on the
- EXP_0208 target_pair_ppi_weight_sum_e208 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0219 random_projection_current_plus_rwr_e219 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0220 random_projection_current_plus_rwr_e220 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0224 target_ppi_degree_sq_x_additive_e224 [test]: feature failed after 2 attempts: mila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  
- EXP_0225 random_projection_best_plus_network_stat_e225 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0236 random_projection_extended_e236 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0250 target_expression_random_projection_e250 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0251 target_expression_random_projection_e251 [test]: feature failed after 2 attempts: gins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r0/workt
- EXP_0262 random_projection_best_features_v2_e262 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0290 target_ppi_degree_sq_x_additive_e290 [test]: feature failed after 2 attempts: _r0/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) i
- EXP_0321 target_pair_ppi_distance_e321 [guard]: iteration over a set of objects (line 45) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0337 pair_prior_edge_sum_e337 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0338 pair_ppi_shortest_path_e338 [guard]: iteration over a set of objects (line 42) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0344 random_projection_target_summaries_e344 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0349 target_pair_ppi_shortest_path_norm_degre_e349 [guard]: iteration over a set of objects (line 61) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0350 target_pair_prior_edge_weight_e350 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0352 target_mean_abs_crispri_delta_e352 [test]: feature failed after 2 attempts: rktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args
- EXP_0355 random_projection_target_summaries_rp_e355 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0356 random_projection_target_summaries_rp_e356 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0364 overlap_highvar_genesets_e364 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0368 random_projection_target_summaries_v2_e368 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0376 additive_x_min_ppi_distance_e376 [guard]: iteration over a set of objects (line 44) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0385 random_projection_target_summaries_v2_e385 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0403 random_projection_all_features_e403 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0420 random_projection_all_best_features_e420 [guard]: use of 'getattr' not allowed
- EXP_0425 pair_ppi_distance_x_additive_e425 [guard]: iteration over a set of objects (line 69) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0428 random_projection_target_prior_degrees_e428 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0448 target_mean_abs_screen_delta_e448 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0450 random_projection_current_best_e450 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0457 target_prior_outdegree_x_additive_sq_e457 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111
- EXP_0462 random_projection_all_best_e462 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0470 pair_screen_delta_product_e470 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0472 additive_x_ppi_degree_sq_e472 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0473 random_projection_best_plus_interactions_e473 [test]: feature failed after 2 attempts: shape (4, 5, 1) != (4, 2083, dim)
- EXP_0482 target_ppi_degree_sq_x_additive_e482 [experiment]: IndexError: index 112 is out of bounds for axis 0 with size 112
- EXP_0483 pair_target_ppi_shortest_path_e483 [guard]: iteration over a set of objects (line 40) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0503 gene_variance_x_additive_e503 [test]: feature failed after 2 attempts: ila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  F
- EXP_0504 gene_screen_delta_sq_x_additive_e504 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0523 random_projection_all_current_features_e523 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0529 random_projection_all_best_features_e529 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0534 target_prior_outdegree_x_gene_screen_del_e534 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0539 random_projection_network_features_e539 [guard]: iteration over a set of objects (line 189) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of object
- EXP_0551 ppi_neighbor_mean_screen_delta_x_additiv_e551 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0554 pair_target_prior_downstream_jaccard_e554 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0558 random_projection_current_best_features_e558 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0559 random_projection_current_best_features_e559 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0561 ppi_neighbor_screen_delta_weighted_e561 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0565 additive_response_sq_x_target_mean_e565 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111
- EXP_0578 gene_set_overlap_x_additive_sq_e578 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111
- EXP_0591 ppi_community_overlap_targets_e600_e591 [guard]: iteration over a set of objects (line 93) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0593 ppi_neighbor_screen_delta_weighted_e602_e593 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0604 gene_ppi_neighbor_screen_delta_mean_e604 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0605 random_projection_best_features_v2_e605 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0645 gene_screen_delta_x_ppi_distance_e645 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0653 pair_target_shared_ppi_neighbors_e653 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0655 additive_x_pair_shared_ppi_neighbors_e655 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0672 random_projection_all_features_screen_e672 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0675 pair_target_ppi_distance_x_additive_sq_e675 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0686 random_projection_current_best_e686 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0703 tf_coregulation_weighted_e701_e703 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0714 pair_tf_conflict_count_e714 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0716 pair_ppi_community_jaccard_e716 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0718 target_prior_downstream_count_x_additive_e718 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0725 target_ppi_degree_x_gene_screen_delta_e725 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0726 target_mean_x_gene_screen_delta_e726 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)

## SURPRISING RESULTS
- shared_tf_regulators_x_additive_e458 made the model worse (-0.0217) despite a linear model being able to ignore it (overfitting or scale issue)
- additive_x_shared_tf_pair_e471 made the model worse (-0.0342) despite a linear model being able to ignore it (overfitting or scale issue)
- pair_gene_set_overlap_x_additive_e526 made the model worse (-0.0113) despite a linear model being able to ignore it (overfitting or scale issue)
- shared_tf_regulators_x_additive_e581 made the model worse (-0.0350) despite a linear model being able to ignore it (overfitting or scale issue)
- pair_target_shared_tf_regulators_x_addit_e615 made the model worse (-0.0222) despite a linear model being able to ignore it (overfitting or scale issue)
- shared_tf_regulators_x_additive_e660 made the model worse (-0.0316) despite a linear model being able to ignore it (overfitting or scale issue)

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0724 | new_feature | 0.6280 | 0.7216 | -0.0936 |
| EXP_0717 | new_feature | 0.6280 | 0.7216 | -0.0936 |
| EXP_0720 | config | 0.6279 | 0.7209 | -0.0931 |
| EXP_0003 | baseline | 0.6108 | 0.7126 | -0.1018 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0724 | 0.008 / 0.005 | 0.983 / 0.989 | 0.963 / 0.975 | 0.170 / 0.106 | 0.906 / 0.938 | 0.758 / 0.844 |
| EXP_0717 | 0.008 / 0.005 | 0.983 / 0.989 | 0.963 / 0.975 | 0.170 / 0.106 | 0.906 / 0.938 | 0.758 / 0.844 |
| EXP_0720 | 0.008 / 0.005 | 0.983 / 0.988 | 0.962 / 0.974 | 0.171 / 0.108 | 0.906 / 0.937 | 0.757 / 0.842 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0724 | 0.546 / 0.557 | 0.729 / 0.760 | 0.546 / 0.518 | 0.931 / 0.949 | 0.819 / 0.869 | 0.961 / 0.973 |
| EXP_0717 | 0.546 / 0.557 | 0.729 / 0.760 | 0.547 / 0.519 | 0.931 / 0.949 | 0.819 / 0.870 | 0.961 / 0.974 |
| EXP_0720 | 0.544 / 0.549 | 0.726 / 0.755 | 0.543 / 0.514 | 0.930 / 0.948 | 0.817 / 0.867 | 0.960 / 0.972 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0724 | 0.708 / 0.685 | 0.009 / 0.006 | 0.738 / 0.754 | 0.554 / 0.488 | 0.889 / 0.904 |
| EXP_0717 | 0.707 / 0.685 | 0.009 / 0.006 | 0.738 / 0.754 | 0.553 / 0.488 | 0.889 / 0.905 |
| EXP_0720 | 0.706 / 0.684 | 0.009 / 0.006 | 0.741 / 0.754 | 0.551 / 0.486 | 0.888 / 0.906 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1738.26
- Mean CPU s/experiment: 1.83
- Gain per CPU-hour: 0.0583
- Gain per USD: 0.0133
- LLM cost per completed experiment: $0.00222

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r0 --experiment EXP_0724`
