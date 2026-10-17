# RUN SUMMARY

Run `norman_ds_addstart_w4_r3` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `ce1b530431`)

- Duration: 20.5 min
- Workers: 4
- Experiments proposed: 648
- Experiments completed: 490 (plus baselines; deepseek:deepseek-v4-pro: 297, python:exploit: 87, sweep(deepseek:deepseek-v4-pro): 106)
- Experiments failed / rejected / killed / not started: 30 / 15 / 2 / 12
- Unique hypotheses: 626 (replicated: 22); duplicate configurations skipped: 99
- CPU hours: 0.3217
- LLM (worker): 406 calls, 701152 in / 364736 out / 358144 cached tokens, $0.5427
- LLM (planner): 51 calls, 257140 in / 107420 out / 88960 cached tokens, $0.6513

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6148

## BEST PERFORMANCE
EXP_0625: pearson_delta = 0.6496 (ridge, alpha=300000.0)

## IMPROVEMENT
0.0348 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_response: coefficient +0.0249
- ppi_distance_similarity_response_e115: coefficient +0.0181
- similar_perturbation_response_e60_e70: coefficient +0.0163
- ppi_neighbor_average_response_e132: coefficient +0.0094
- target_coexpression_e14: coefficient +0.0026
- is_target: coefficient +0.0021
- replogle_predicted_delta_e25: coefficient +0.0018
- replogle_weighted_coexpression_v2_e101: coefficient +0.0015
- replogle_weighted_by_coexpression_e93: coefficient +0.0014
- replogle_ppi_distance_modulated_exxx_e172: coefficient +0.0011
- ppi_neighbor_replogle_average_e154: coefficient +0.0009

## DISCOVERY LINEAGE
EXP_0007 [baseline] score 0.6197
    ↳ EXP_0014 [target_coexpression_e14] score 0.6200
        ↳ EXP_0025 [replogle_predicted_delta_e25] score 0.6235
            ↳ EXP_0039 [config] score 0.6235
                ↳ EXP_0051 [config] score 0.6267
                    ↳ EXP_0070 [similar_perturbation_response_e60_e70] score 0.6325
                        ↳ EXP_0093 [replogle_weighted_by_coexpression_e93] score 0.6333
                            ↳ EXP_0115 [ppi_distance_similarity_response_e115] score 0.6411
                                ↳ EXP_0132 [ppi_neighbor_average_response_e132] score 0.6429
                                    ↳ EXP_0154 [ppi_neighbor_replogle_average_e154] score 0.6430
                                        ↳ EXP_0172 [replogle_ppi_distance_modulated_exxx_e172] score 0.6432
                                            ↳ EXP_0182 [ppi_inverse_distance_response_e182] score 0.6440
                                                ↳ EXP_0210 [config] score 0.6450
                                                    ↳ EXP_0218 [config] score 0.6460
                                                        ↳ EXP_0235 [config] score 0.6463
                                                            ↳ EXP_0361 [config] score 0.6482
                                                                ↳ EXP_0407 [config] score 0.6488
                                                                    ↳ EXP_0413 [config] score 0.6495
                                                                        ↳ EXP_0439 [config] score 0.6495
                                                                            ↳ EXP_0545 [config] score 0.6495
                                                                                ↳ EXP_0625 [config] score 0.6496

## MOST USEFUL FEATURES
- ppi_distance_similarity_response_e115 (EXP_0115): +0.0078. For perturbation p and gene g, weighted average of delta[q,g] over training perturbations q, where the weight is exp(-decay * min_shortest_path_distance between any target of p and any target of q) computed from the PPI network.
- ppi_distance_similarity_response_e116 (EXP_0116): +0.0062. Weighted average of training deltas by exp(-PPI shortest path distance) between target sets.
- similar_perturbation_response_e60_e70 (EXP_0070): +0.0057. Jaccard-similarity-weighted average of training deltas over perturbations with similar targets.
- similar_perturbation_response_e60_e71 (EXP_0071): +0.0057. For perturbation p and gene g, weighted average of delta[q,g] over training perturbations q (excluding p), with weights equal to the Jaccard similarity between the target gene sets of p and q.
- replogle_predicted_delta_e25 (EXP_0025): +0.0035. Sign-adjusted Replogle CRISPRi screen delta for perturbation p's targets.
- ppi_neighbor_average_response_e132 (EXP_0132): +0.0019. For perturbation p and gene g, average delta[q,g] over training perturbations q whose target set shares at least one PPI neighbor with p's targets.
- ppi_inverse_distance_response_e182 (EXP_0182): +0.0008. For perturbation p and gene g, weighted average of delta[q,g] over training perturbations q, with weight = 1/(1+shortest_path_distance(g, target(q))).
- replogle_weighted_by_coexpression_e93 (EXP_0093): +0.0008. Sum over p's target genes t of sign-adjusted Replogle delta(t) weighted by control co-expression(t, g).
- prior_embedding_similarity_response_e127 (EXP_0127): +0.0006. Weighted average of training deltas over perturbations q, weighted by cosine similarity between node2vec embeddings of p's targets and q's targets.
- ppi_community_similarity_response_e212 (EXP_0212): +0.0006. For perturbation p and gene g, average delta[q,g] over training perturbations q whose targets share a PPI community with p's targets.

## FEATURES THAT DID NOT HELP
- pathway_similarity_e15: -0.0000
- prior_network_proximity_e16: -0.0001
- ppi_diffusion_score_e17: -0.0000
- nearest_neighbor_response_e18: -0.0092
- prior_pagerank_e21: -0.0001
- geneset_overlap_similarity_e24: -0.0000
- target_coexpression_e26: -0.0000
- graph_embedding_similarity_e35: -0.0001
- pca_program_similarity_e41: -0.0000
- partial_corr_to_target_e42: -0.0000
- target_ppi_degree_e44: -0.0001
- geneset_enrichment_score_e47: -0.0000
- replogle_weighted_target_coexpression_e55: -0.0008
- target_ppi_degree_e64: -0.0001
- replogle_target_delta_variance_e65: -0.0000
- weighted_target_coexpression_e57_e67: -0.0003
- target_count_e90: -0.0001
- pair_coexpression_asymmetry_e92: -0.0004
- weighted_geneset_overlap_e95: -0.0001
- replogle_weighted_coexpression_v2_e100: -0.0003
- topk_similar_perturbation_response_e89_e104: -0.0001
- cosine_similar_perturbation_response_e90_e105: -0.0012
- ppi_embedding_similarity_e92_e109: -0.0002
- cosine_expression_similarity_response_e111: -0.0008
- cosine_expression_similarity_response_e112: -0.0008
- replogle_magnitude_weighted_coexpression_e113: -0.0007
- replogle_pair_interaction_product_e125: -0.0001
- replogle_pair_interaction_product_e126: -0.0001
- ppi_min_distance_to_target_e131: -0.0001
- ppi_weighted_target_coexpression_e133: -0.0001
- replogle_ppi_neighbor_delta_e135: -0.0000
- ppi_pagerank_score_e136: -0.0004
- ppi_weighted_path_similarity_response_e140: -0.0003
- ppi_pagerank_diffusion_score_e141: -0.0003
- ppi_weighted_target_coexpression_e142: -0.0001
- ppi_min_shortest_path_to_target_e150: -0.0001
- ppi_shared_neighbor_count_e151: -0.0000
- ppi_weighted_target_coexpression_e152: -0.0001
- ppi_weighted_replogle_delta_e153: -0.0004
- ppi_neighbor_response_weighted_by_coexpr_e161: -0.0028
- target_pathway_overlap_e162: -0.0000
- pair_interaction_ppi_weighted_e164: -0.0001
- ppi_neighbor_coexpression_weighted_exxx_e171: -0.0000
- shared_target_response_similarity_exxx_e175: -0.0000
- node2vec_embedding_distance_exxx_e178: -0.0000
- ppi_min_distance_to_targets_e180: -0.0001
- target_ppi_degree_mean_e181: -0.0003
- max_target_jaccard_similarity_e186: -0.0002
- target_neighbor_coexpression_e187: -0.0010
- replogle_ppi_distance_weighted_e188: -0.0000
- ppi_min_distance_to_target_e194: -0.0001
- ppi_community_similarity_response_e211: -0.0030
- replogle_ppi_coexpression_combined_e213: -0.0000
- replogle_ppi_coexpression_combined_e214: -0.0003
- ppi_neighbor_coexpression_weighted_respo_e219: -0.0003
- replogle_distance_weighted_sum_e213_e220: -0.0001
- pair_target_ppi_distance_e214_e221: -0.0000
- pair_replogle_coexpression_weighted_sum__e223: -0.0006
- ppi_pagerank_target_diffusion_e217_e231: -0.0001
- ppi_distance_weighted_replogle_sum_e236: -0.0020
- target_neighbor_coexpression_e237: -0.0020
- pair_target_ppi_distance_e238: -0.0020
- pair_geneset_jaccard_e239: -0.0020
- target_neighbor_max_coexpression_e246: -0.0019
- replogle_pagerank_diffusion_e247: -0.0022
- ppi_min_mean_distance_to_targets_e252: -0.0023
- coexpression_times_replogle_e253: -0.0024
- geneset_overlap_weighted_by_replogle_e256: -0.0023
- replogle_pagerank_from_targets_e266: -0.0024
- ppi_pair_target_distance_e267: -0.0023
- geneset_target_overlap_count_e268: -0.0022
- replogle_ppi_pair_weighted_e269: -0.0029
- prior_network_influence_e270: -0.0023
- ppi_neighbor_jaccard_e271: -0.0022
- ppi_pagerank_from_targets_e274: -0.0023
- ppi_neighbor_coexpression_count_e276: -0.0022
- pair_target_ppi_distance_e277: -0.0022
- replogle_ppi_distance_weighted_e278: -0.0023
- geneset_overlap_ppi_neighbors_e279: -0.0025
- target_neighbor_coexpression_e280: -0.0027
- ppi_pagerank_replogle_e281: -0.0025
- ppi_distance_bins_e282: -0.0021
- geneset_replogle_weighted_average_e289: -0.0023
- geneset_replogle_weighted_average_e290: -0.0022
- target_coregulation_correlation_e291: -0.0036
- target_coregulation_correlation_e292: -0.0036
- ppi_community_overlap_e294: -0.0022
- target_control_variance_e295: -0.0021
- target_control_variance_e296: -0.0021
- ppi_distance_similarity_sqrt_e297: -0.0026
- target_coexpression_entropy_e298: -0.0024
- ppi_distance_response_entropy_e303: -0.0023
- ppi_distance_response_variance_e304: -0.0022
- target_coexpression_variance_e305: -0.0018
- replogle_delta_sqrt_e306: -0.0020
- ppi_distance_binned_variance_response_e311: -0.0022
- target_coexpression_entropy_e312: -0.0022
- sqrt_ppi_distance_similarity_response_e313: -0.0026
- ppi_distance_response_entropy_e317: -0.0022
- ppi_distance_response_entropy_e318: -0.0023
- ppi_neighbor_delta_variance_e319: -0.0023
- ppi_distance_squared_decay_response_e331: -0.0023
- target_coexpression_entropy_ppi_neighbor_e332: -0.0020
- ppi_sharp_decay_replogle_modulated_respo_e335: -0.0021
- topk_similar_perturbation_response_e336: -0.0078
- ppi_neighbor_coexpression_weighted_respo_e337: -0.0022
- pair_replogle_distance_weighted_e338: -0.0024
- sqrt_ppi_distance_similarity_e339: -0.0024
- ppi_neighbor_weighted_distance_response_e348: -0.0022
- coexpression_weighted_replogle_e349: -0.0022
- topk_similar_perturbation_response_e350: -0.0014
- coexpression_entropy_to_targets_e352: -0.0022
- replogle_ppi_distance_quantile_e363: -0.0024
- target_coexpression_entropy_e364: -0.0022
- pair_target_ppi_distance_asymmetry_e365: -0.0023
- ppi_neighbor_set_jaccard_e366: -0.0022
- replogle_weighted_by_coexpression_sq_e367: -0.0029
- replogle_ppi_gaussian_decay_e370: -0.0026
- geneset_specificity_overlap_e371: -0.0023
- ppi_neighbor_response_variance_e372: -0.0022
- replogle_degree_weighted_delta_e373: -0.0019
- target_coexpression_entropy_e374: -0.0022
- ppi_community_response_e384: -0.0022
- pair_degree_ratio_e385: -0.0022
- ppi_neighbor_response_variance_exxx_e387: -0.0050
- replogle_raw_target_sum_e388: -0.0048
- coexpression_weighted_ppi_response_e389: -0.0052
- pair_coexpression_product_e390: -0.0050
- ppi_path_distance_histogram_e393: -0.0046
- ppi_path_distance_histogram_e394: -0.0052
- ppi_distance_distribution_stats_e395: -0.0052
- pair_target_coexpression_interaction_e396: -0.0050
- ppi_neighbor_response_variance_e397: -0.0051
- ppi_similar_response_interaction_e409: -0.0052
- target_neighbor_coexpression_e415: -0.0060
- similar_perturbation_response_cosine_e417: -0.0050
- ppi_neighbor_delta_entropy_e427: -0.0049
- pair_replogle_ppi_distance_weighted_e420_e428: -0.0066
- coexpression_weighted_response_e421_e429: -0.0049
- gene_response_variance_e424_e432: -0.0063
- gene_mean_abs_delta_e425_e433: -0.0059
- replogle_target_ppi_weighted_average_exx_e447: -0.0063
- ppi_target_distance_weighted_response_ex_e448: -0.0065
- ppi_neighbor_coexpression_weighted_respo_e449: -0.0063
- ppi_neighbor_coexpression_replogle_avera_e450: -0.0064
- pair_replogle_ppi_interaction_exxx_e454: -0.0064
- pair_target_coexpression_similarity_e458: -0.0063
- pathway_jaccard_target_gene_e459: -0.0063
- ppi_neighbor_coexpression_response_e460: -0.0050
- replogle_pair_product_e461: -0.0064
- target_average_coexpression_e462: -0.0063
- similar_perturbation_ppi_weighted_e463: -0.0156
- sqrt_additive_response_e469: -0.0060
- sqrt_additive_response_e476: -0.0048
- ppi_neighbor_abs_delta_average_e477: -0.0062
- cosine_similar_perturbation_response_e478: -0.0063
- replogle_pair_product_e479: -0.0064
- ppi_min_distance_to_target_e485: -0.0064
- target_neighbor_coexpression_mean_e486: -0.0071
- target_ppi_degree_sum_e487: -0.0066
- similar_perturbation_response_cosine_e488: -0.0155
- target_coexpression_ppi_decay_e491: -0.0062
- replogle_ppi_distance_weighted_sum_e492: -0.0064
- ppi_neighbor_confidence_weighted_respons_e496: -0.0062
- ppi_neighbor_confidence_weighted_replogl_e497: -0.0063
- ppi_distance_similarity_cosine_decay_e499: -0.0066
- ppi_path_count_target_to_gene_e502: -0.0063
- target_coexpression_with_ppi_neighbors_e503: -0.0063
- ppi_inverse_distance_similarity_response_e507: -0.0061
- ppi_rank_distance_similarity_response_e508: -0.0040
- ppi_threshold_distance_similarity_respon_e509: -0.0114
- ppi_neighbor_coexpression_weighted_respo_e513: -0.0062
- ppi_log_distance_similarity_response_e514: -0.0051
- tf_target_overlap_response_e518: -0.0060
- geneset_enrichment_similarity_response_e519: -0.0062
- ppi_neighbor_coexpression_weighted_respo_e520: -0.0064
- pair_ppi_distance_interaction_response_e521: -0.0070
- ppi_pagerank_target_response_e530: -0.0065
- ppi_coexpr_weighted_response_e531: -0.0064
- tf_target_score_e532: -0.0063
- geneset_weighted_overlap_e534: -0.0062
- ppi_soft_decay_response_e535: -0.0065
- random_projection_feature_e544: -0.0062
- ppi_neighbor_coexpression_weighted_respo_e546: -0.0059
- ppi_rank_distance_similarity_response_e547: -0.0064
- geneset_overlap_with_targets_e548: -0.0063
- tf_target_overlap_e549: -0.0063
- control_expression_random_projection_e553: -0.0061
- ppi_soft_distance_similarity_response_e562: -0.0062
- ppi_coexpression_weighted_response_e563: -0.0052
- replogle_rank_distance_weighted_e564: -0.0069
- ppi_similarity_times_replogle_e565: -0.0055
- ppi_weighted_random_projection_e566: -0.0062
- ppi_distance_similarity_inverse_e116b_e567: -0.0046
- ppi_distance_rank_similarity_e568: -0.0060
- ppi_neighbor_coexpr_weighted_response_e569: -0.0056
- target_pathway_coherence_e570: -0.0063
- pair_ppi_distance_product_e571: -0.0065
- random_control_projection_e574: -0.0060
- ppi_distance_times_additive_response_e575: -0.0063
- target_coexpression_ppi_weighted_e576: -0.0064
- pair_target_ppi_distance_e577: -0.0062
- replogle_target_ppi_weighted_e578: -0.0063
- ppi_neighbor_coexpression_weighted_e579: -0.0062
- control_expression_random_projection_e582: -0.0059
- replogle_ppi_distance_weighted_target_av_e586: -0.0064
- ppi_distance_coexpression_weighted_respo_e587: -0.0059
- jaccard_ppi_distance_product_response_e588: -0.0063
- signed_min_ppi_distance_to_target_e589: -0.0062
- ppi_similarity_times_replogle_e590: -0.0039
- ppi_distance_similarity_inverse_e_e593: -0.0061
- tf_target_overlap_e594: -0.0062
- pathway_perturbation_similarity_e595: -0.0059
- ppi_neighbor_inverse_distance_average_e596: -0.0048
- replogle_ppi_distance_sum_v2_e599: -0.0063
- ppi_distance_similarity_inverse_e605: -0.0062
- ppi_target_distance_stats_e606: -0.0064
- replogle_ppi_distance_weighted_e607: -0.0063
- ppi_distance_similarity_coexpr_weighted_e608: -0.0075
- geneset_weighted_overlap_e611: -0.0063
- ppi_distance_similarity_coexpression_wei_e617: -0.0074
- pair_target_coexpression_interaction_e618: -0.0063
- replogle_ppi_coexpression_weighted_e619: -0.0064
- replogle_ppi_coexpression_weighted_e620: -0.0064
- geneset_overlap_target_gene_e621: -0.0063
- ppi_distance_similarity_response_inverse_e622: -0.0062
- ppi_random_projection_embedding_e631: -0.0064
- ppi_random_projection_embedding_e632: -0.0063
- response_set_jaccard_similarity_e634: -0.0033
- prior_network_target_regulation_e635: -0.0064
- replogle_delta_times_coexpression_e636: -0.0063
- target_ppi_clustering_coefficient_e637: -0.0064
- ppi_distance_random_fourier_e640: -0.0070
- ppi_distance_similarity_degree_weighted_e644: -0.0064

## FAILED FEATURES
- EXP_0052 replogle_target_self_magnitude_e52 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0053 replogle_gene_delta_e53 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0054 replogle_pair_synergy_e54 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0066 weighted_target_coexpression_e57_e66 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0069 pair_ppi_distance_e59_e69 [guard]: iteration over a set of objects (line 47) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0083 ppi_pagerank_e61_e83 [experiment]: UnboundLocalError: cannot access local variable 'gene_index' where it is not associated with a value
- EXP_0094 filtered_similarity_response_e94 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0103 topk_similar_perturbation_response_e89_e103 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111
- EXP_0106 replogle_pair_interaction_e91_e106 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0143 pair_ppi_interaction_replogle_e143 [guard]: iteration over a set of objects (line 53) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0144 ppi_neighbor_geneset_similarity_e144 [guard]: iteration over a set of objects (line 79) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0160 ppi_embedding_distance_e160 [test]: feature failed after 2 attempts: LEAKAGE non-deterministic output; label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p)); output depends on the
- EXP_0163 replogle_weighted_by_ppi_distance_e163 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0174 pair_target_ppi_distance_exxx_e174 [guard]: iteration over a set of objects (line 38) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0185 pair_target_ppi_distance_e185 [guard]: iteration over a set of objects (line 49) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0190 replogle_coexpression_product_e190 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0200 ppi_distance_weighted_replogle_delta_e200 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0202 ppi_distance_weighted_by_replogle_magnit_e202 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0254 ppi_neighbor_replogle_weighted_by_distan_e254 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0255 pair_interaction_replogle_ppi_e255 [guard]: iteration over a set of objects (line 83) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0293 ppi_community_overlap_e293 [guard]: iteration over a set of objects (line 62) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0310 ppi_distance_weighted_replogle_response_e310 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0316 log_ppi_distance_modulated_replogle_e316 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0330 ppi_distance_replogle_variance_e330 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0351 pair_ppi_distance_modulated_response_e351 [guard]: iteration over a set of objects (line 46) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0353 ppi_neighbor_replogle_distance_weighted_e353 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0386 pair_target_ppi_distance_e386 [guard]: iteration over a set of objects (line 43) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0398 replogle_ppi_coexpression_weighted_e398 [guard]: iteration over a set of objects (line 95) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0414 ppi_neighbor_delta_weighted_by_target_di_e414 [experiment]: IndexError: index 82 is out of bounds for axis 0 with size 82
- EXP_0416 replogle_delta_weighted_by_target_distan_e416 [test]: feature failed after 2 attempts: eline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
- EXP_0430 pair_target_ppi_distance_e422_e430 [guard]: iteration over a set of objects (line 40) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0431 replogle_pair_interaction_e423_e431 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0451 replogle_coexpression_weighted_sum_exxx_e451 [test]: feature failed after 2 attempts: server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache el
- EXP_0475 replogle_ppi_coexpression_modulated_e475 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0498 replogle_target_ppi_distance_weighted_e498 [guard]: iteration over a set of objects (line 45) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0533 pair_synergy_score_e533 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0550 pair_additive_deviation_e550 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0561 ppi_rank_distance_similarity_response_e561 [test]: feature failed after 2 attempts: py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/a
- EXP_0572 replogle_ppi_coexpr_weighted_e572 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0597 random_control_projection_v2_e597 [test]: feature failed after 2 attempts: erver/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache els
- EXP_0598 random_control_projection_v2_e598 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0604 ppi_distance_similarity_squared_exp_e604 [test]: feature failed after 2 attempts: , Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addst
- EXP_0616 ppi_distance_similarity_coexpression_wei_e616 [experiment]: IndexError: index 111 is out of bounds for axis 0 with size 111

## SURPRISING RESULTS
- similar_perturbation_ppi_weighted_e463 made the model worse (-0.0156) despite a linear model being able to ignore it (overfitting or scale issue)
- similar_perturbation_response_cosine_e488 made the model worse (-0.0155) despite a linear model being able to ignore it (overfitting or scale issue)
- ppi_threshold_distance_similarity_respon_e509 made the model worse (-0.0114) despite a linear model being able to ignore it (overfitting or scale issue)

## ENSEMBLE FINALIST
EXP_0656: average of EXP_0625, EXP_0613, EXP_0446 scores 0.6497 on the visible perturbations (query-only 0.7304). It is a finalist, not the best single model; the union of its members' features is listed in summary.json.

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0656 | ensemble | 0.6497 | 0.7304 | -0.0807 |
| EXP_0625 | config | 0.6496 | 0.7301 | -0.0805 |
| EXP_0613 | config | 0.6495 | 0.7308 | -0.0812 |
| EXP_0446 | config | 0.6495 | 0.7300 | -0.0806 |
| EXP_0003 | baseline | 0.6148 | 0.7126 | -0.0978 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0656 | 0.008 / 0.006 | 0.981 / 0.987 | 0.959 / 0.971 | 0.214 / 0.145 | 0.887 / 0.919 | 0.710 / 0.797 |
| EXP_0625 | 0.008 / 0.006 | 0.981 / 0.987 | 0.960 / 0.971 | 0.213 / 0.145 | 0.887 / 0.919 | 0.711 / 0.797 |
| EXP_0613 | 0.008 / 0.006 | 0.982 / 0.988 | 0.961 / 0.973 | 0.201 / 0.135 | 0.893 / 0.924 | 0.727 / 0.809 |
| EXP_0446 | 0.009 / 0.006 | 0.980 / 0.986 | 0.957 / 0.969 | 0.228 / 0.157 | 0.880 / 0.913 | 0.689 / 0.782 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0656 | 0.485 / 0.458 | 0.731 / 0.741 | 0.539 / 0.487 | 0.940 / 0.946 | 0.832 / 0.851 | 0.969 / 0.976 |
| EXP_0625 | 0.489 / 0.457 | 0.732 / 0.741 | 0.540 / 0.486 | 0.940 / 0.946 | 0.834 / 0.852 | 0.970 / 0.976 |
| EXP_0613 | 0.507 / 0.487 | 0.736 / 0.749 | 0.549 / 0.502 | 0.943 / 0.949 | 0.844 / 0.863 | 0.970 / 0.976 |
| EXP_0446 | 0.455 / 0.420 | 0.724 / 0.731 | 0.528 / 0.470 | 0.937 / 0.941 | 0.820 / 0.834 | 0.968 / 0.974 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0656 | 0.745 / 0.696 | 0.009 / 0.007 | 0.702 / 0.653 | 0.544 / 0.469 | 0.907 / 0.894 |
| EXP_0625 | 0.745 / 0.696 | 0.009 / 0.007 | 0.702 / 0.651 | 0.546 / 0.470 | 0.908 / 0.894 |
| EXP_0613 | 0.745 / 0.696 | 0.009 / 0.007 | 0.725 / 0.680 | 0.550 / 0.482 | 0.912 / 0.899 |
| EXP_0446 | 0.744 / 0.695 | 0.010 / 0.007 | 0.666 / 0.635 | 0.537 / 0.460 | 0.902 / 0.887 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1432.94
- Mean CPU s/experiment: 2.36
- Gain per CPU-hour: 0.1082
- Gain per USD: 0.0292
- LLM cost per completed experiment: $0.00244

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r3 --experiment EXP_0625`
