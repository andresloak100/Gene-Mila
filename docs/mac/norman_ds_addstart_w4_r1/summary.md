# RUN SUMMARY

Run `norman_ds_addstart_w4_r1` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `ce1b530431`)

- Duration: 20.1 min
- Workers: 4
- Experiments proposed: 897
- Experiments completed: 636 (plus baselines; deepseek:deepseek-v4-pro: 338, python:exploit: 141, sweep(deepseek:deepseek-v4-pro): 157)
- Experiments failed / rejected / killed / not started: 132 / 6 / 1 / 7
- Unique hypotheses: 877 (replicated: 19); duplicate configurations skipped: 115
- CPU hours: 0.1157
- LLM (worker): 683 calls, 1111746 in / 502245 out / 556544 cached tokens, $0.7726
- LLM (planner): 70 calls, 322839 in / 140388 out / 82560 cached tokens, $0.8767

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6197

## BEST PERFORMANCE
EXP_0875: pearson_delta = 0.6408 (ridge, alpha=120000.0)

## IMPROVEMENT
0.0210 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_response: coefficient +0.0438
- target_delta_times_cv_control_e569: coefficient -0.0282
- is_target: coefficient +0.0037
- target_delta_squared_sum_e168: coefficient +0.0026
- target_delta_times_abs_coexpression_e117: coefficient +0.0022
- replogle_delta_e15: coefficient +0.0017
- target_gene_set_coverage_e587: coefficient -0.0016
- target_specific_replogle_delta_e73: coefficient +0.0006
- pair_target_delta_product_e675: coefficient +0.0006
- is_pair_e58: coefficient +0.0002

## DISCOVERY LINEAGE
EXP_0007 [baseline] score 0.6261
    ↳ EXP_0015 [replogle_delta_e15] score 0.6296
        ↳ EXP_0037 [config] score 0.6305
            ↳ EXP_0055 [config] score 0.6322
                ↳ EXP_0073 [target_specific_replogle_delta_e73] score 0.6325
                    ↳ EXP_0092 [abs_target_coexpression_e92] score 0.6326
                        ↳ EXP_0105 [config] score 0.6326
                            ↳ EXP_0117 [target_delta_times_abs_coexpression_e117] score 0.6334
                                ↳ EXP_0132 [config] score 0.6338
                                    ↳ EXP_0149 [config] score 0.6338
                                        ↳ EXP_0168 [target_delta_squared_sum_e168] score 0.6338
                                            ↳ EXP_0187 [config] score 0.6339
                                                ↳ EXP_0219 [config] score 0.6339
                                                    ↳ EXP_0238 [config] score 0.6340
                                                        ↳ EXP_0247 [config] score 0.6341
                                                            ↳ EXP_0256 [config] score 0.6344
                                                                ↳ EXP_0286 [config] score 0.6351
                                                                    ↳ EXP_0295 [config] score 0.6357
                                                                        ↳ EXP_0314 [config] score 0.6358
                                                                            ↳ EXP_0387 [config] score 0.6359
                                                                                ↳ EXP_0401 [config] score 0.6359
                                                                                    ↳ EXP_0421 [config] score 0.6360
                                                                                        ↳ EXP_0523 [config] score 0.6360
                                                                                            ↳ EXP_0566 [config] score 0.6360
                                                                                                ↳ EXP_0569 [target_delta_times_cv_control_e569] score 0.6385
                                                                                                    ↳ EXP_0587 [target_gene_set_coverage_e587] score 0.6385
                                                                                                        ↳ EXP_0601 [config] score 0.6387
                                                                                                            ↳ EXP_0611 [config] score 0.6388
                                                                                                                ↳ EXP_0633 [target_delta_times_coexpression_sq_e633] score 0.6390
                                                                                                                    ↳ EXP_0648 [config] score 0.6390
                                                                                                                        ↳ EXP_0664 [config] score 0.6391
                                                                                                                            ↳ EXP_0675 [pair_target_delta_product_e675] score 0.6395
                                                                                                                                ↳ EXP_0686 [config] score 0.6395
                                                                                                                                    ↳ EXP_0698 [config] score 0.6396
                                                                                                                                        ↳ EXP_0708 [config] score 0.6397
                                                                                                                                            ↳ EXP_0742 [config] score 0.6399
                                                                                                                                                ↳ EXP_0753 [config] score 0.6402
                                                                                                                                                    ↳ EXP_0762 [config] score 0.6402
                                                                                                                                                        ↳ EXP_0786 [config] score 0.6407
                                                                                                                                                            ↳ EXP_0822 [config] score 0.6407
                                                                                                                                                                ↳ EXP_0831 [config] score 0.6407
                                                                                                                                                                    ↳ EXP_0875 [config] score 0.6408

## MOST USEFUL FEATURES
- replogle_delta_e15 (EXP_0015): +0.0035. Sign-flipped CRISPRi screen delta of p's target genes as a prediction of CRISPRa delta.
- target_delta_times_cv_control_e569 (EXP_0569): +0.0025. Per-target sign-flipped CRISPRi delta(t) * CV(control expression of t), broadcast per gene.
- target_delta_times_abs_coexpression_e117 (EXP_0117): +0.0008. For each target gene t of p, multiply the sign-flipped CRISPRi screen delta of t by the absolute Pearson coexpression between gene g and t, then average over the targets of p.
- pair_target_delta_product_e675 (EXP_0675): +0.0004. Product of sign-flipped training deltas of the two target genes of a pair perturbation, broadcast to both target columns; 0 for singles.
- target_delta_times_gene_set_overlap_e263 (EXP_0263): +0.0003. Sum over targets of sign-flipped delta times Jaccard overlap of gene sets containing target and gene g.
- target_specific_replogle_delta_e73 (EXP_0073): +0.0003. Sign-flipped CRISPRi delta for target genes only, zero elsewhere.
- target_delta_times_coexpression_sq_e633 (EXP_0633): +0.0002. For each target t of p, multiply sign-flipped CRISPRi delta_t by (abs Pearson correlation between t and g)^2; sum over targets.
- target_delta_times_signed_coexpression_s_e665 (EXP_0665): +0.0002. Sum over targets t of sign-flipped CRISPRi delta_t times sign(cor(g,t))*cor(g,t)^2.
- squared_abs_target_coexpression_e111 (EXP_0111): +0.0002. Square of the mean absolute Pearson correlation between gene g and each target gene of p.
- target_coexpression_e16 (EXP_0016): +0.0002. Average Pearson correlation in control cells between gene g and the perturbation's target genes.

## FEATURES THAT DID NOT HELP
- prior_network_target_similarity_e12: -0.0000
- ppi_network_proximity_e13: -0.0001
- gene_set_overlap_e14: -0.0001
- ppi_closeness_to_targets_e20: -0.0001
- gene_set_overlap_with_targets_e21: -0.0001
- target_control_expression_e23: -0.0000
- random_embedding_similarity_e70: -0.0000
- loo_additive_response_e76: -0.0022
- random_embedding_similarity_e84: -0.0092
- replogle_target_magnitude_norm_e89: -0.0001
- pair_replogle_product_e90: -0.0002
- target_ppi_degree_e91: -0.0000
- target_abs_replogle_magnitude_e97: -0.0001
- additive_response_x_target_count_e98: -0.0025
- loo_additive_response_improved_e99: -0.0022
- mean_abs_ppi_weight_to_targets_e101: -0.0000
- random_proj_target_delta_tanh_e104: -0.0001
- target_l1_replogle_delta_e109: -0.0000
- target_count_times_additive_response_e110: -0.0005
- pair_target_delta_ratio_e115: -0.0000
- pair_coexpression_sign_product_e116: -0.0003
- ppi_weighted_proximity_e120: -0.0004
- random_proj_target_coexpression_e129: -0.0043
- pair_coexpression_asymmetry_e134: -0.0002
- pair_coexpression_product_e135: -0.0002
- pair_target_control_product_e138: -0.0000
- pair_target_control_ratio_e139: -0.0000
- pair_target_delta_abs_diff_e155: -0.0002
- pair_coexpression_weighted_delta_e164: -0.0001
- pair_delta_product_e166: -0.0002
- additive_response_times_control_mean_e167: -0.0003
- target_delta_times_ppi_degree_e172: -0.0001
- target_delta_over_control_expr_e174: -0.0000
- pair_delta_product_times_coexpression_si_e175: -0.0001
- target_delta_variance_e180_e190: -0.0000
- target_delta_entropy_e181_e191: -0.0000
- target_delta_cv_e182_e192: -0.0000
- target_delta_weighted_control_e183_e193: -0.0000
- target_magnitude_times_count_e184_e194: -0.0000
- target_delta_entropy_e199: -0.0000
- target_delta_cv_e200: -0.0000
- target_delta_sq_times_coexpr_e202: -0.0021
- target_delta_times_inv_coexpression_var_e209: -0.0000
- pair_target_delta_product_e222: -0.0002
- sum_abs_target_delta_e224: -0.0000
- target_mean_signed_coexpression_e225: -0.0000
- random_projection_target_delta_powers_e228: -0.0001
- target_delta_times_signed_coexpression_e231: -0.0005
- target_delta_times_rank_abs_coexpression_e232: -0.0007
- target_delta_times_gene_set_overlap_e236: -0.0001
- random_projection_delta_coexpression_e237: -0.0002
- target_delta_squared_times_abs_coexpress_e239: -0.0009
- sum_target_delta_over_control_e241: -0.0001
- pair_target_delta_product_e242: -0.0003
- sum_target_delta_times_rank_abs_coexpres_e243: -0.0002
- target_delta_times_abs_coexpression_rank_e248: -0.0003
- target_delta_times_ppi_confidence_e250: -0.0001
- target_delta_times_shared_gene_sets_e251: -0.0002
- target_delta_times_prior_similarity_e252: -0.0002
- random_projection_target_coexpression_e255: -0.0001
- target_delta_times_signed_coexpression_e258: -0.0003
- target_delta_product_e259: -0.0004
- target_delta_normalized_by_control_e261: -0.0002
- rank_target_delta_times_signed_coexpress_e278: -0.0018
- pair_target_coexpression_product_e280: -0.0006
- target_delta_times_signed_coexpression_s_e282: -0.0008
- target_delta_times_coexpression_rank_per_e287: -0.0005
- target_delta_normalized_by_control_expr_e288: -0.0006
- pair_target_coexpression_product_e289: -0.0005
- signed_coexpression_weighted_by_target_d_e292: -0.0011
- target_delta_times_coexpression_squared_e293: -0.0006
- target_delta_times_rank_abs_coexpression_e297: -0.0021
- target_delta_normalized_by_control_expre_e299: -0.0012
- target_delta_signed_squared_sum_e300: -0.0012
- target_delta_times_abs_coexpression_squa_e301: -0.0007
- target_delta_times_essentiality_e303: -0.0013
- target_delta_times_essentiality_e304: -0.0032
- target_pair_abs_coexpression_e307: -0.0019
- max_abs_coexpression_to_target_e308: -0.0017
- target_delta_abs_sum_e309: -0.0019
- pair_delta_product_weighted_e310: -0.0018
- target_delta_times_rank_abs_coexpression_e311: -0.0019
- target_delta_times_essentiality_e312: -0.0018
- pair_target_abs_coexpression_e315: -0.0018
- pair_target_delta_product_e316: -0.0021
- pair_target_delta_product_e317: -0.0021
- pair_target_delta_abs_diff_e318: -0.0019
- essentiality_weighted_target_delta_e320: -0.0017
- target_delta_times_control_mean_e321: -0.0019
- target_delta_abs_sum_e323: -0.0019
- target_control_percentile_e313_e327: -0.0018
- target_mean_abs_coexpression_all_e314_e328: -0.0019
- target_ppi_degree_e315_e329: -0.0019
- target_gene_set_count_e316_e330: -0.0018
- target_is_tf_e317_e331: -0.0018
- target_delta_sqrt_e318_e341: -0.0019
- target_delta_over_control_expr_e343: -0.0020
- target_delta_times_coexpression_rank_e344: -0.0032
- target_delta_times_pos_coexpression_e345: -0.0027
- target_delta_times_ppi_confidence_e346: -0.0020
- target_delta_times_tf_activity_e349: -0.0020
- target_delta_times_rank_abs_coexpression_e353: -0.0025
- target_delta_over_control_expression_e354: -0.0020
- target_delta_times_squared_abs_coexpress_e356: -0.0020
- random_projection_target_coexpression_e359: -0.0009
- target_delta_weighted_by_ppi_confidence_e362: -0.0020
- target_delta_normalized_by_control_e363: -0.0020
- target_delta_weighted_by_gene_set_overla_e364: -0.0027
- target_delta_times_signed_coexpression_s_e365: -0.0026
- tf_target_weighted_delta_e368: -0.0020
- random_projection_target_coexpression_e369: -0.0021
- target_gene_set_activity_e371: -0.0020
- ppi_neighbor_confidence_e372: -0.0021
- tf_binding_overlap_e373: -0.0020
- random_projection_target_coexpr_e376: -0.0021
- target_delta_times_ppi_confidence_e389: -0.0020
- target_delta_times_gene_set_overlap_e390: -0.0020
- target_delta_times_signed_coexpression_e405: -0.0022
- target_delta_weighted_by_geneset_comembe_e407: -0.0018
- target_delta_normalized_by_control_expre_e408: -0.0023
- target_delta_times_is_target_e409: -0.0024
- target_delta_squared_sum_signed_e410: -0.0023
- random_projection_target_delta_coexpress_e412: -0.0020
- target_delta_times_signed_coexpression_e415: -0.0023
- target_delta_weighted_ppi_threshold_e416: -0.0024
- target_delta_times_coexpression_rank_e417: -0.0025
- ppi_degree_e428: -0.0027
- target_ppi_degree_e429: -0.0023
- target_gene_set_count_e430: -0.0023
- target_gene_set_overlap_count_e431: -0.0023
- target_delta_sign_e432: -0.0023
- target_coexpression_rank_e433: -0.0023
- gene_set_overlap_loo_e441: -0.0024
- target_ppi_degree_sum_e442: -0.0024
- target_coexpression_rank_loo_e443: -0.0024
- target_delta_squared_times_abs_coexpress_e445: -0.0028
- random_projection_target_delta_coexp_e448: -0.0024
- target_delta_coexpression_rank_weighted_e451: -0.0029
- target_delta_signed_coexpression_weighte_e452: -0.0023
- target_replogle_delta_variability_e453: -0.0023
- perturbation_target_count_e454: -0.0024
- target_pair_coexpression_e455: -0.0024
- target_delta_coexpression_random_project_e458: -0.0131
- pair_target_coexpression_e460: -0.0024
- pair_target_coexpression_e461: -0.0024
- pair_avg_coexpression_to_gene_e462: -0.0023
- pair_avg_coexpression_to_gene_e463: -0.0023
- is_pair_perturbation_e464: -0.0024
- is_pair_perturbation_e465: -0.0024
- pair_target_delta_product_e466: -0.0026
- pair_target_delta_product_e467: -0.0026
- abs_target_delta_sum_e468: -0.0024
- mean_target_delta_e470: -0.0027
- target_delta_weighted_by_abs_coexpressio_e482: -0.0026
- target_delta_weighted_by_gene_set_overla_e484: -0.0026
- target_delta_weighted_by_tf_coregulation_e485: -0.0025
- pair_target_delta_product_e487: -0.0026
- random_projection_target_delta_e493: -0.0024
- ppi_weighted_target_delta_sum_e497: -0.0023
- coexpression_weighted_target_delta_sum_e498: -0.0025
- geneset_similarity_weighted_target_delta_e499: -0.0028
- perturbation_type_indicator_e501: -0.0024
- normalized_target_delta_sum_e509: -0.0023
- target_delta_over_control_expr_e514: -0.0195
- mean_abs_coexpr_non_targets_e516: -0.0048
- target_delta_weighted_abs_coexpr_e518: -0.0015
- pair_target_delta_product_e519: -0.0023
- target_delta_times_target_control_e530_e533: -0.0024
- target_delta_over_target_control_e531_e534: -0.0023
- target_delta_ppi_max_e534_e537: -0.0024
- random_projection_target_control_interac_e540: -0.0058
- target_delta_weighted_by_ppi_confidence_e549: -0.0024
- pair_target_delta_product_e550: -0.0026
- random_projection_target_delta_vector_e552: -0.0025
- target_delta_times_log_control_mean_g_e557: -0.0024
- target_delta_norm_by_target_control_e558: -0.0195
- max_abs_target_delta_e559: -0.0023
- target_delta_weighted_coexpression_e560: -0.0027
- target_delta_weighted_ppi_e561: -0.0024
- target_delta_weighted_by_essentiality_e585: -0.0003
- target_ppi_degree_sum_e586: -0.0000
- target_is_tf_e589: -0.0000
- target_delta_random_projection_e597: -0.0001
- target_pair_coexpression_sum_e600_e602: -0.0001
- target_delta_times_ppi_degree_e601_e603: -0.0000
- pair_abs_coexpression_sum_e613: -0.0001
- gene_set_coverage_times_is_pair_e614: -0.0000
- shortest_path_to_target_e616: -0.0005
- target_delta_times_control_cv_e617: -0.0006
- target_gene_set_jaccard_e626: -0.0000
- ppi_weighted_distance_e628: -0.0005
- pair_delta_product_e632: -0.0000
- gene_set_random_projection_e645: -0.0002
- gene_set_random_projection_e646: -0.0003
- target_delta_times_control_rank_e653: -0.0000
- target_delta_sum_times_g_cv_e660: -0.0000
- additive_response_squared_e662: -0.0000
- target_delta_times_abs_coexpression_rank_e666: -0.0002
- target_gene_set_overlap_weighted_e667: -0.0001
- pair_delta_product_times_coexpression_e668: -0.0007
- target_gene_set_random_projection_e672: -0.0000
- target_delta_times_signed_coexpression_e673: -0.0001
- pair_target_coexpression_e674: -0.0001
- target_delta_times_signed_coexpression_s_e676: -0.0002
- target_delta_times_rank_abs_coexpression_e677: -0.0006
- target_delta_times_gene_set_similarity_e678: -0.0004
- target_delta_times_abs_coexpression_rank_e689: -0.0002
- target_delta_times_signed_coexpression_t_e690: -0.0001
- target_delta_times_gene_set_specificity__e691: -0.0001
- target_delta_times_ppi_degree_e670_e693: -0.0000
- random_projection_target_gene_sets_e671_e696: -0.0000
- target_delta_times_inverse_ppi_distance_e701: -0.0003
- target_delta_times_gene_set_jaccard_e702: -0.0003
- target_delta_times_random_projection_gen_e706: -0.0000
- target_delta_times_pathway_overlap_e709: -0.0008
- target_delta_times_coexpression_percenti_e710: -0.0002
- pair_target_delta_product_times_coexpres_e711: -0.0000
- target_delta_times_gene_cv_e713: -0.0002
- target_downstream_coexpression_e728: -0.0003
- target_downstream_coexpression_e729: -0.0003
- pair_delta_product_times_target_coexp_e730: -0.0002
- target_delta_times_coexpression_rank_exx_e746: -0.0003
- target_delta_times_control_quantile_exxx_e747: -0.0004
- target_delta_times_tf_indicator_exxx_e748: -0.0003
- target_delta_times_is_tf_e757: -0.0004
- loo_additive_response_e759: -0.0013
- random_projection_target_delta_expr_e761: -0.0004
- target_delta_times_ppi_edge_sum_e765: -0.0007
- target_delta_over_ppi_distance_e766: -0.0007
- target_delta_times_gene_set_specificity_e767: -0.0008
- random_projection_target_delta_outer_e771: -0.0007
- random_projection_target_delta_outer_e772: -0.0006
- loo_additive_response_e773: -0.0006
- target_delta_times_control_rank_e776: -0.0011
- target_delta_weighted_gene_set_coverage_e777: -0.0012
- target_delta_coexpression_outer_projecti_e779: -0.0011
- target_tf_regulation_score_e791: -0.0009
- target_gene_set_jaccard_e793: -0.0008
- target_delta_ppi_distance_decay_e794: -0.0010
- target_control_expr_product_e795: -0.0012
- target_gene_random_projection_e804: -0.0009
- target_delta_times_target_control_expr_e806: -0.0013
- target_delta_times_target_cv_e807: -0.0014
- target_delta_times_coexpression_squared_e809: -0.0015
- target_delta_times_ppi_proximity_e811: -0.0015
- target_delta_times_log_control_mean_e823: -0.0013
- pair_target_delta_abs_sum_e824: -0.0013
- target_delta_times_gene_set_specificity_e825: -0.0013
- pair_target_delta_max_min_ratio_e826: -0.0013
- target_delta_times_control_variance_rank_e827: -0.0014
- target_delta_times_ppi_degree_e837: -0.0015
- target_delta_times_gene_set_specificity_e838: -0.0015
- target_delta_times_tf_score_e842: -0.0015
- target_delta_times_signed_coexpression_e846: -0.0019
- target_delta_times_inverse_cv_e848: -0.0020
- target_delta_times_ppi_weight_e850: -0.0015
- target_delta_times_mean_control_e856_e855: -0.0017
- target_delta_times_inv_cv_control_e857_e856: -0.0019
- target_delta_times_signed_coexpression_e_e857: -0.0017
- target_delta_times_ppi_degree_e860_e859: -0.0017
- target_delta_times_gene_set_count_e861_e860: -0.0015
- tf_coregulation_score_e868: -0.0015
- target_ppi_degree_e869: -0.0015
- target_gene_set_specificity_e870: -0.0015
- target_control_variance_e871: -0.0015
- pair_target_ppi_distance_e872: -0.0015
- target_delta_times_gene_set_specificity__e883: -0.0015
- pair_target_delta_diff_times_coexpressio_e884: -0.0015
- target_delta_weighted_by_ppi_closeness_e_e885: -0.0019
- target_delta_times_tf_overlap_e904_e886: -0.0017

## FAILED FEATURES
- EXP_0019 pair_additivity_departure_e19 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0022 crispri_screen_delta_e22 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0052 partial_corr_to_targets_e52 [test]: feature failed after 2 attempts: timeout after 90s
- EXP_0059 target_replogle_variance_e59 [test]: feature failed after 2 attempts: py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- EXP_0072 target_activation_magnitude_e72 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0075 sum_target_activation_magnitude_e75 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0085 random_embedding_similarity_e85 [test]: feature failed after 2 attempts: s.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman
- EXP_0095 replogle_target_random_projection_e95 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0096 depmap_target_effect_e96 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0100 target_specific_replogle_delta_squared_e100 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0106 target_squared_replogle_delta_e106 [test]: feature failed after 2 attempts: _ds_addstart_w4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Pat
- EXP_0107 target_abs_replogle_delta_sum_e107 [test]: feature failed after 2 attempts: cuments/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public)
- EXP_0108 target_max_replogle_delta_e108 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0113 random_projection_target_replogle_e113 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0118 target_delta_rank_percentile_e118 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0136 pair_replogle_delta_product_e136 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0137 max_target_replogle_delta_e137 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0153 target_delta_magnitude_percentile_e153 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0156 target_delta_times_signed_coexpression_e156 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0160 random_proj_target_coexpression_e160 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0165 target_delta_over_control_e165 [test]: feature failed after 2 attempts: r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if
- EXP_0170 random_proj_target_delta_vector_e170 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0176 target_delta_times_gene_set_overlap_e176 [test]: feature failed after 2 attempts: (args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/no
- EXP_0179 random_proj_target_delta_tanh_e179 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0197 random_proj_target_delta_powers_e185_e197 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0198 target_delta_quantile_rank_e198 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0201 target_delta_sum_times_count_e201 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0205 random_proj_target_delta_powers_e205 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0208 target_delta_times_signed_coexpression_e208 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0210 pair_delta_product_times_coexpression_e210 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0211 primary_target_delta_times_coexpression_e211 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p)); output depends on the order of a pair's target 
- EXP_0220 random_proj_global_target_delta_e220 [test]: feature failed after 2 attempts:  Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addsta
- EXP_0221 target_delta_times_signed_coexpression_e221 [guard]: global/nonlocal statements not allowed
- EXP_0223 target_delta_over_control_e223 [test]: feature failed after 2 attempts: in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Do
- EXP_0233 target_delta_squared_times_signed_coexpr_e233 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0234 target_delta_over_control_expression_e234 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0235 pair_target_delta_product_e235 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0240 max_target_delta_times_abs_coexpression_e240 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0246 random_projection_target_delta_coexpress_e246 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0249 target_delta_times_abs_coexpression_sq_e249 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0260 target_delta_times_abs_coexpression_rank_e260 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0262 target_delta_times_ppi_weight_e262 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0265 random_projection_target_coexpression_in_e265 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p)); output depends on the order of a pair's target 
- EXP_0266 signed_coexpression_rank_weighted_target_e266 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0267 normalized_target_delta_by_control_e267 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0268 target_delta_times_signed_coexpression_s_e268 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0269 gene_set_overlap_weighted_target_delta_e269 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0270 ppi_confidence_weighted_target_delta_e270 [test]: feature failed after 2 attempts: ila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
- EXP_0277 random_projection_target_delta_coexpress_e277 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0279 pair_target_delta_product_e279 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0281 target_delta_times_abs_coexpression_rank_e281 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0285 random_projection_target_delta_coexpress_e285 [test]: feature failed after 2 attempts: , in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/
- EXP_0290 pair_target_delta_product_e290 [test]: feature failed after 2 attempts: t_w4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cach
- EXP_0291 target_delta_sum_squared_e291 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0296 target_delta_weighted_by_ppi_confidence_e296 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0298 pair_target_delta_product_times_coexpres_e298 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0319 target_delta_times_abs_coexpression_rank_e319 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0342 target_delta_times_abs_coexpression_squa_e342 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0352 target_delta_times_positive_coexpression_e352 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0355 target_delta_times_ppi_confidence_e355 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0370 target_coexpression_pca_e370 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0391 sqrt_target_delta_e391 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0392 target_delta_times_control_expression_e392 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0400 random_projection_target_coexpression_e400 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0406 target_delta_weighted_by_ppi_confidence_e406 [experiment]: ValueError: feature target_delta_weighted_by_ppi_confidence_e406 produced NaN/inf values
- EXP_0425 target_delta_normalized_by_control_e425 [test]: feature failed after 2 attempts: /Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.
- EXP_0426 random_projection_target_delta_coexpress_e426 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0427 random_projection_target_delta_coexpress_e427 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0444 target_delta_times_ppi_degree_e444 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0469 abs_target_delta_sum_e469 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0471 mean_target_delta_e471 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0483 target_delta_weighted_by_ppi_confidence__e483 [experiment]: ValueError: feature target_delta_weighted_by_ppi_confidence__e483 produced NaN/inf values
- EXP_0486 signed_target_delta_squared_sum_e486 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0500 target_delta_product_for_pairs_e500 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0515 target_delta_times_log_control_e515 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0517 target_delta_weighted_ppi_confidence_e517 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0528 random_projection_target_delta_e528 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0535 pair_target_delta_product_e532_e535 [test]: feature failed after 2 attempts: aga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r1/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, 
- EXP_0536 target_delta_abs_coexpression_mean_e533_e536 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0545 target_delta_times_abs_coexpression_weig_e545 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0546 target_delta_normalized_by_control_e546 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0547 pair_target_delta_product_e547 [test]: feature failed after 2 attempts: n main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Doc
- EXP_0548 target_delta_abs_squared_sum_e548 [test]: feature failed after 2 attempts: 4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) 
- EXP_0564 random_projection_target_delta_coexpress_e564 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p)); output depends on the order of a pair's tar
- EXP_0570 target_delta_times_ppi_degree_e570 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0571 target_delta_times_essentiality_e571 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0572 pair_delta_product_e572 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0581 random_projection_target_delta_pair_e581 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0605 target_delta_times_essentiality_e603_e605 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0609 target_delta_product_pair_e605_e609 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0612 target_delta_times_ppi_degree_e612 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0615 target_delta_times_coexpression_sq_e615 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0624 random_projection_target_delta_e624 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0625 random_projection_target_delta_e625 [test]: feature failed after 2 attempts: trees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.c
- EXP_0627 target_gene_set_jaccard_e627 [test]: feature failed after 2 attempts: e else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r1/worktrees/_server/genemila/pipeline.py", line 313, in smoke

- EXP_0629 ppi_weighted_distance_e629 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0630 pair_delta_product_e630 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0631 pair_delta_product_e631 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0634 target_delta_times_coexpression_sq_e634 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0652 target_delta_times_control_sq_e652 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0654 target_delta_times_cv_control_sq_e654 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0661 target_delta_times_max_abs_coexpression_e661 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0669 target_delta_times_control_percentile_e669 [test]: feature failed after 2 attempts: , in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/
- EXP_0692 pair_target_coexpression_times_delta_sum_e692 [test]: feature failed after 2 attempts: a/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r1/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.p
- EXP_0699 target_delta_times_shared_tf_count_e699 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0700 target_delta_times_abs_coexpression_rank_e700 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0703 pair_target_delta_product_times_target_c_e703 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0704 target_delta_times_target_control_expres_e704 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0712 target_delta_times_ppi_inverse_distance_e712 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0731 target_delta_times_gene_set_specificity_e731 [test]: feature failed after 2 attempts: ila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
- EXP_0732 target_delta_times_tf_regulation_e732 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0743 random_projection_target_coexp_e743 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0744 target_delta_times_gene_set_specificity__e744 [guard]: iteration over a set of objects (line 96) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0745 target_delta_times_ppi_neighbor_count_ex_e745 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0749 target_delta_times_prior_network_strengt_e749 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0751 random_projection_target_delta_outer_exx_e751 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0755 target_delta_times_abs_coexpression_rank_e755 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0756 target_delta_times_ppi_degree_e756 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0758 target_delta_times_gene_set_count_e758 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0760 target_delta_sq_times_abs_coexpression_e760 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0764 target_delta_times_coexpression_times_ta_e764 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0768 target_delta_times_tf_target_similarity_e768 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0775 target_delta_times_signed_coexpression_e775 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0792 pair_target_delta_sum_squared_e792 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0808 pair_target_delta_product_times_target_c_e808 [test]: feature failed after 2 attempts: erver/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache els
- EXP_0810 target_delta_times_gene_set_similarity_e810 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0830 random_projection_target_delta_outer_pro_e830 [test]: feature failed after 2 attempts: e(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mi
- EXP_0835 target_delta_times_coexpression_rank_e835 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0836 pair_target_delta_ratio_e836 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0839 target_delta_times_cv_control_squared_e839 [test]: feature failed after 2 attempts: art_w4_r1/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.ca
- EXP_0840 pair_target_delta_product_abs_e840 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0847 target_delta_times_control_mean_e847 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0849 target_delta_times_gene_set_shared_fract_e849 [test]: feature failed after 2 attempts: ila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  F
- EXP_0853 random_projection_pair_delta_outer_e853 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0858 pair_target_delta_sum_times_coexpression_e858 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0879 random_projection_target_gene_outer_e879 [test]: feature failed after 2 attempts: output depends on the order of a pair's target genes: a perturbation's targets are an unordered set (use every target, never only the first, and never match two pertur
- EXP_0882 target_delta_times_ppi_degree_e900_e882 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)

## SURPRISING RESULTS
- target_delta_coexpression_random_project_e458 made the model worse (-0.0131) despite a linear model being able to ignore it (overfitting or scale issue)
- target_delta_over_control_expr_e514 made the model worse (-0.0195) despite a linear model being able to ignore it (overfitting or scale issue)
- target_delta_norm_by_target_control_e558 made the model worse (-0.0195) despite a linear model being able to ignore it (overfitting or scale issue)

## ENSEMBLE FINALIST
EXP_0899: average of EXP_0890, EXP_0818, EXP_0844 scores 0.6408 on the visible perturbations (query-only 0.7275). It is a finalist, not the best single model; the union of its members' features is listed in summary.json.

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0899 | ensemble | 0.6408 | 0.7275 | -0.0867 |
| EXP_0890 | config | 0.6408 | 0.7274 | -0.0866 |
| EXP_0818 | config | 0.6407 | 0.7274 | -0.0867 |
| EXP_0844 | config | 0.6407 | 0.7276 | -0.0869 |
| EXP_0003 | baseline | 0.6197 | 0.7126 | -0.0929 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0899 | 0.009 / 0.006 | 0.981 / 0.987 | 0.959 / 0.972 | 0.210 / 0.138 | 0.887 / 0.923 | 0.705 / 0.806 |
| EXP_0890 | 0.009 / 0.006 | 0.981 / 0.987 | 0.959 / 0.972 | 0.211 / 0.138 | 0.887 / 0.923 | 0.705 / 0.805 |
| EXP_0818 | 0.008 / 0.006 | 0.982 / 0.987 | 0.960 / 0.972 | 0.205 / 0.134 | 0.890 / 0.925 | 0.712 / 0.811 |
| EXP_0844 | 0.009 / 0.006 | 0.981 / 0.987 | 0.958 / 0.971 | 0.215 / 0.141 | 0.885 / 0.922 | 0.699 / 0.802 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0899 | 0.474 / 0.480 | 0.718 / 0.744 | 0.532 / 0.490 | 0.931 / 0.945 | 0.804 / 0.850 | 0.961 / 0.974 |
| EXP_0890 | 0.473 / 0.479 | 0.717 / 0.743 | 0.532 / 0.490 | 0.931 / 0.945 | 0.804 / 0.849 | 0.960 / 0.974 |
| EXP_0818 | 0.484 / 0.490 | 0.721 / 0.747 | 0.538 / 0.497 | 0.932 / 0.947 | 0.810 / 0.858 | 0.962 / 0.974 |
| EXP_0844 | 0.465 / 0.471 | 0.714 / 0.740 | 0.527 / 0.485 | 0.929 / 0.944 | 0.797 / 0.844 | 0.960 / 0.973 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0899 | 0.713 / 0.691 | 0.010 / 0.007 | 0.703 / 0.681 | 0.533 / 0.472 | 0.886 / 0.893 |
| EXP_0890 | 0.713 / 0.691 | 0.010 / 0.007 | 0.703 / 0.680 | 0.533 / 0.471 | 0.886 / 0.893 |
| EXP_0818 | 0.713 / 0.691 | 0.009 / 0.007 | 0.707 / 0.688 | 0.535 / 0.476 | 0.889 / 0.898 |
| EXP_0844 | 0.713 / 0.691 | 0.010 / 0.007 | 0.696 / 0.673 | 0.530 / 0.465 | 0.884 / 0.891 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1902.17
- Mean CPU s/experiment: 0.65
- Gain per CPU-hour: 0.1818
- Gain per USD: 0.0127
- LLM cost per completed experiment: $0.00259

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r1 --experiment EXP_0875`
