# RUN SUMMARY

Run `norman_ds_addstart_w4_r2` on dataset `norman` (split `split_a391fa9e7b4eccb7`, code `ce1b530431`)

- Duration: 20.0 min
- Workers: 4
- Experiments proposed: 729
- Experiments completed: 559 (plus baselines; deepseek:deepseek-v4-pro: 331, python:exploit: 112, sweep(deepseek:deepseek-v4-pro): 116)
- Experiments failed / rejected / killed / not started: 110 / 4 / 0 / 0
- Unique hypotheses: 721 (replicated: 7); duplicate configurations skipped: 49
- CPU hours: 0.3377
- LLM (worker): 525 calls, 899213 in / 378756 out / 449024 cached tokens, $0.5923
- LLM (planner): 62 calls, 297997 in / 121223 out / 75392 cached tokens, $0.7772

## BASELINE PERFORMANCE
EXP_0003: A perturbation changes expression by the sum of its genes' single-gene changes in training (additive model). pearson_delta = 0.6313

## BEST PERFORMANCE
EXP_0715: pearson_delta = 0.6506 (ridge, alpha=100.0)

## IMPROVEMENT
0.0193 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- additive_response: coefficient +0.0809
- random_fourier_additive_replogle_e348: coefficient -0.0439
- additive_response_squared_e78: coefficient -0.0423
- is_target: coefficient +0.0053
- pair_replogle_delta_sum_e432_e441: coefficient +0.0038
- ppi_additive_propagation_e276: coefficient +0.0037
- signed_replogle_coexpression_e89: coefficient +0.0031
- additive_times_ppi_distance_e462: coefficient -0.0028
- additive_times_target_expression_e148_e157: coefficient -0.0026
- pair_ppi_path_confidence_e715: coefficient -0.0024
- additive_times_pair_replogle_delta_produ_e420: coefficient +0.0023
- additive_times_pair_replogle_product_e560: coefficient +0.0018
- ppi_replogle_propagation_e235: coefficient -0.0012
- pair_target_coexpression_product_e250: coefficient -0.0005
- additive_response_clipped_e212_e219: coefficient +0.0004
- normalized_geneset_overlap_e394: coefficient -0.0002

## DISCOVERY LINEAGE
EXP_0007 [baseline] score 0.6365
    ↳ EXP_0014 [target_coexpression_e14] score 0.6367
        ↳ EXP_0024 [config] score 0.6381
            ↳ EXP_0036 [config] score 0.6395
                ↳ EXP_0058 [weighted_target_coexpression_e58] score 0.6402
                    ↳ EXP_0072 [config] score 0.6413
                        ↳ EXP_0089 [signed_replogle_coexpression_e89] score 0.6421
                            ↳ EXP_0101 [config] score 0.6421
                                ↳ EXP_0113 [config] score 0.6421
                                    ↳ EXP_0121 [additive_times_coexpression_e121] score 0.6425
                                        ↳ EXP_0138 [config] score 0.6426
                                            ↳ EXP_0157 [additive_times_target_expression_e148_e157] score 0.6431
                                                ↳ EXP_0167 [target_control_expression_mean_e167] score 0.6432
                                                    ↳ EXP_0183 [config] score 0.6434
                                                        ↳ EXP_0219 [additive_response_clipped_e212_e219] score 0.6435
                                                            ↳ EXP_0235 [ppi_replogle_propagation_e235] score 0.6435
                                                                ↳ EXP_0250 [pair_target_coexpression_product_e250] score 0.6435
                                                                    ↳ EXP_0258 [config] score 0.6435
                                                                        ↳ EXP_0276 [ppi_additive_propagation_e276] score 0.6436
                                                                            ↳ EXP_0296 [additive_times_signed_replogle_coexpress_e296] score 0.6439
                                                                                ↳ EXP_0311 [config] score 0.6439
                                                                                    ↳ EXP_0322 [config] score 0.6440
                                                                                        ↳ EXP_0348 [random_fourier_additive_replogle_e348] score 0.6441
                                                                                            ↳ EXP_0361 [pair_replogle_delta_product_e361] score 0.6464
                                                                                                ↳ EXP_0370 [config] score 0.6464
                                                                                                    ↳ EXP_0394 [normalized_geneset_overlap_e394] score 0.6464
                                                                                                        ↳ EXP_0420 [additive_times_pair_replogle_delta_produ_e420] score 0.6478
                                                                                                            ↳ EXP_0441 [pair_replogle_delta_sum_e432_e441] score 0.6481
                                                                                                                ↳ EXP_0462 [additive_times_ppi_distance_e462] score 0.6484
                                                                                                                    ↳ EXP_0518 [config] score 0.6484
                                                                                                                        ↳ EXP_0560 [additive_times_pair_replogle_product_e560] score 0.6485
                                                                                                                            ↳ EXP_0593 [config] score 0.6492
                                                                                                                                ↳ EXP_0606 [config] score 0.6496
                                                                                                                                    ↳ EXP_0643 [config] score 0.6502
                                                                                                                                        ↳ EXP_0671 [config] score 0.6503
                                                                                                                                            ↳ EXP_0715 [pair_ppi_path_confidence_e715] score 0.6506

## MOST USEFUL FEATURES
- pair_replogle_delta_product_e361 (EXP_0361): +0.0023. Product of sign-corrected Replogle deltas of the target genes for each gene g.
- additive_times_pair_replogle_delta_produ_e420 (EXP_0420): +0.0014. Elementwise product of additive_response and pair_replogle_delta_product_e361 for each (perturbation, gene).
- signed_replogle_coexpression_e89 (EXP_0089): +0.0008. Average over p's targets t of sign-corrected replogle delta of t times control Pearson correlation between gene g and t.
- weighted_target_coexpression_e58 (EXP_0058): +0.0007. Average over p's targets of (control Pearson corr of g with target) times sign-corrected replogle delta of the target.
- additive_times_target_expression_e148_e157 (EXP_0157): +0.0006. Elementwise product of additive_response and the mean control expression of p's target genes.
- additive_times_coexpression_e121 (EXP_0121): +0.0005. Elementwise product of additive_response and weighted_target_coexpression_e58.
- additive_times_signed_replogle_coexpress_e296 (EXP_0296): +0.0004. Elementwise product of additive_response and signed_replogle_coexpression_e89.
- pair_target_coexpression_product_e76 (EXP_0076): +0.0003. Product of control-cell coexpression of gene g with each of p's targets (squared for singles).
- pair_ppi_path_confidence_e715 (EXP_0715): +0.0003. For pair perturbations A+B, product of PPI edge confidences along the shortest path between A and B; 1 for singles, 0 if disconnected.
- pair_replogle_delta_sum_e432_e441 (EXP_0441): +0.0003. For pair perturbations, sum of sign-corrected Replogle deltas of the two target genes; for single-gene perturbations, equal to the target's delta.

## FEATURES THAT DID NOT HELP
- nn_response_e15: -0.0119
- prior_regulation_score_e16: -0.0000
- target_centrality_e18: -0.0000
- additivity_departure_e19: -0.0011
- ppi_proximity_e27: -0.0002
- replogle_target_magnitude_e29: -0.0000
- target_ppi_degree_e32: -0.0000
- ppi_shortest_path_e38: -0.0001
- pca_projection_score_e40: -0.0000
- pair_coexpression_product_e41: -0.0000
- random_target_projection_e51: -0.0002
- random_target_projection_e52: -0.0002
- partial_corr_targets_e59: -0.0004
- coexpression_x_control_mean_e77: -0.0003
- tanh_weighted_coexpression_e87: -0.0003
- target_coexpression_rank_e90: -0.0005
- geneset_coexpression_product_e92: -0.0001
- weighted_target_coexpression_rank_e91_e105: -0.0004
- pair_target_coexpression_mean_e93_e107: -0.0000
- geneset_similarity_x_coexpression_e95_e109: -0.0011
- replogle_x_coexpression_e96_e110: -0.0001
- tanh_random_projection_e97_e111: -0.0001
- pair_coexpression_times_additive_e117: -0.0002
- normalized_additive_response_e118: -0.0002
- ppi_neighbor_coexpression_e119: -0.0012
- replogle_profile_correlation_e120: -0.0005
- additive_response_squared_e122: -0.0000
- pair_coexpression_product_x_additive_e130: -0.0012
- replogle_self_x_coexpression_e131: -0.0001
- random_tanh_combo_replogle_coexpr_e135: -0.0004
- ppi_proximity_x_coexpression_e136: -0.0001
- ppi_neighbor_replogle_delta_e141: -0.0005
- target_coexpression_asymmetry_e142: -0.0001
- target_coexpression_rank_product_e144: -0.0000
- random_nonlinear_coexpression_projection_e153: -0.0015
- pair_coexpression_asymmetry_e145_e154: -0.0001
- geneset_shared_count_e149_e158: -0.0000
- pair_ppi_distance_asymmetry_e150_e159: -0.0002
- random_projection_all_features_e151_e161: -0.0040
- random_projection_all_features_e151_e162: -0.0036
- pair_shared_geneset_overlap_with_g_e163: -0.0000
- pair_coexpression_asymmetry_squared_e165: -0.0002
- ppi_distance_asymmetry_e166: -0.0000
- additive_response_residual_replogle_e171: -0.0003
- signed_replogle_coexpression_squared_e172: -0.0049
- random_nonlinear_replogle_coexpression_p_e178: -0.0008
- pair_coexpression_asymmetry_e179: -0.0001
- replogle_target_product_e180: -0.0000
- target_expression_range_e181: -0.0000
- additive_times_squared_replogle_coexpres_e190: -0.0003
- pair_coexpression_rank_asymmetry_e192: -0.0004
- random_projection_coexpression_e200: -0.0004
- additive_times_inverse_ppi_distance_e201: -0.0039
- pair_coexpression_dispersion_e192_e202: -0.0000
- target_expression_dispersion_e193_e203: -0.0000
- additive_times_target_count_e194_e204: -0.0000
- additive_times_coexpression_rank_e195_e205: -0.0050
- ppi_shortest_path_sum_e196_e206: -0.0009
- pair_coexpression_asymmetry_e209_e216: -0.0000
- additive_times_target_expression_varianc_e217: -0.0194
- signed_replogle_coexpression_squared_e21_e218: -0.0042
- random_projection_coexpression_e214_e221: -0.0066
- random_projection_coexpression_e214_e222: -0.0066
- rank_coexpression_times_additive_e227: -0.0050
- target_expression_entropy_e228: -0.0001
- clipped_additive_response_e230: -0.0001
- pair_coexpression_asymmetry_e231: -0.0000
- signed_replogle_coexpression_squared_e232: -0.0003
- random_projection_coexpression_e233: -0.0000
- coexpression_replogle_projection_e237: -0.0000
- target_coexpression_rank_sum_e238: -0.0012
- random_coexpression_projection_e241: -0.0019
- target_coexpression_std_e242: -0.0000
- pair_coexpression_product_e243: -0.0001
- pair_target_expression_product_e244: -0.0001
- pair_replogle_delta_product_e245: -0.0006
- pair_geneset_jaccard_e247: -0.0000
- random_coexpression_projection_e249: -0.0025
- pair_target_control_expr_product_e252: -0.0000
- pair_target_ppi_distance_e253: -0.0000
- pair_target_geneset_jaccard_e254: -0.0000
- target_coexpression_std_e255: -0.0000
- random_target_coexpression_projection_e257: -0.0020
- additive_times_coexpression_rank_e263: -0.0045
- weighted_geneset_overlap_e264: -0.0001
- random_projection_target_coexpression_e269: -0.0037
- replogle_additive_correlation_e272: -0.0000
- pair_target_expression_product_e274: -0.0000
- target_gene_set_overlap_e275: -0.0001
- random_ppi_projection_e286: -0.0002
- ppi_neighbor_additive_response_distance__e287: -0.0001
- pair_target_coexpression_asymmetry_e288: -0.0000
- additive_response_times_ppi_degree_e290: -0.0011
- random_fourier_additive_coexpression_e294: -0.0038
- pair_coexpression_times_additive_respons_e299: -0.0000
- random_fourier_additive_coexpression_e302: -0.0029
- ppi_shortest_path_additive_propagation_e303: -0.0014
- pair_target_coexpression_times_additive_e304: -0.0001
- additive_times_target_expression_rank_e306: -0.0031
- geneset_jaccard_additive_propagation_e307: -0.0028
- random_fourier_additive_coexpression_e308: -0.0066
- signed_replogle_coexpression_squared_e29_e313: -0.0035
- pair_coexpression_times_replogle_coexpre_e316: -0.0002
- ppi_neighbor_replogle_abs_mean_e336: -0.0000
- target_ppi_neighbor_coexpression_mean_e338: -0.0012
- additive_times_ppi_neighbor_replogle_mea_e339: -0.0001
- pair_target_coexpression_asymmetry_e349: -0.0000
- min_ppi_shortest_path_to_target_e350: -0.0006
- target_control_expression_dispersion_e352: -0.0000
- shared_geneset_count_e353: -0.0000
- random_fourier_additive_response_e356: -0.0002
- shared_geneset_count_weighted_e363: -0.0002
- target_control_expression_variance_e365: -0.0000
- min_ppi_distance_to_target_e366: -0.0006
- pair_target_expression_product_e367: -0.0001
- random_fourier_ppi_additive_e369: -0.0001
- ppi_target_distance_replogle_e373: -0.0000
- normalized_geneset_overlap_e375: -0.0001
- shared_neighbor_replogle_e376: -0.0001
- ppi_neighbor_replogle_weighted_e390: -0.0000
- target_ppi_neighbor_replogle_sum_e391: -0.0000
- rank_additive_response_e407: -0.0031
- min_ppi_distance_to_target_e409: -0.0006
- random_fourier_combined_e348_plus_e410: -0.0005
- replogle_delta_product_weighted_coexpres_e415: -0.0002
- geneset_overlap_replogle_weighted_e417: -0.0001
- target_expression_times_replogle_delta_e418: -0.0000
- random_fourier_ppi_replogle_e419: -0.0022
- replogle_coexpression_times_geneset_over_e421: -0.0006
- target_coexpression_squared_e424: -0.0004
- additive_response_rank_within_p_e425: -0.0031
- random_ppi_projection_to_targets_e426: -0.0011
- ppi_weighted_shortest_path_to_target_e432: -0.0004
- ppi_neighbor_geneset_overlap_e433: -0.0000
- pair_replogle_correlation_e434: -0.0000
- additive_response_times_inverse_ppi_dist_e436: -0.0039
- random_fourier_ppi_adjacency_to_targets_e439: -0.0002
- signed_replogle_coexpression_squared_e43_e444: -0.0032
- additive_times_target_ppi_degree_e436_e445: -0.0010
- ppi_propagation_scaled_by_target_degree_e457: -0.0000
- coexpression_replogle_interaction_e458: -0.0010
- geneset_replogle_enrichment_e460: -0.0001
- pair_replogle_delta_difference_e461: -0.0001
- target_expression_cv_e456_e468: -0.0000
- pair_replogle_delta_abs_diff_e457_e469: -0.0002
- weighted_geneset_overlap_e458_e470: -0.0002
- additive_times_target_centrality_e459_e471: -0.0010
- pair_target_expression_ratio_e475: -0.0000
- ppi_min_distance_to_target_e476: -0.0007
- pair_replogle_product_times_ppi_proximit_e477: -0.0006
- pair_replogle_delta_sum_squared_e479: -0.0000
- random_fourier_all_features_e488: -0.0092
- additive_times_ppi_decay_e493: -0.0011
- signed_replogle_coexpression_squared_e497: -0.0035
- ppi_additive_prop_times_target_expr_e498: -0.0155
- ppi_additive_propagation_target_decay_e505: -0.0001
- signed_replogle_times_target_coexpressio_e506: -0.0042
- target_expression_times_replogle_product_e507: -0.0001
- additive_response_over_target_expression_e508: -0.0001
- additive_times_ppi_additive_propagation_e520: -0.0001
- signed_replogle_times_ppi_additive_e521: -0.0002
- pair_replogle_product_times_ppi_distance_e522: -0.0003
- additive_times_pair_coexpression_product_e523: -0.0028
- replogle_product_times_ppi_distance_e536: -0.0009
- pair_gene_target_coexpression_product_e539: -0.0009
- ppi_additive_squared_propagation_e540: -0.0004
- target_control_expression_var_e555_e554: -0.0000
- pair_target_ppi_distance_e556_e556: -0.0001
- additive_times_target_coexpression_e557: -0.0003
- signed_replogle_coexpression_squared_e563: -0.0031
- random_fourier_additive_target_expr_e564: -0.0034
- additive_times_pair_replogle_delta_produ_e566: -0.0047
- target_control_expression_variance_e567: -0.0006
- additive_response_times_pair_ppi_distanc_e569: -0.0057
- signed_replogle_coexpression_squared_e576: -0.0035
- target_control_expression_variance_e578: -0.0006
- random_fourier_top3_e580: -0.0006
- pair_ppi_shortest_path_e581: -0.0004
- pair_target_coexpression_e582: -0.0006
- additive_times_ppi_distance_squared_e585: -0.0014
- weighted_geneset_overlap_replogle_e586: -0.0005
- random_projection_top_features_e587: -0.0020
- geneset_jaccard_target_gene_e597: -0.0006
- ppi_additive_propagation_decay_e598: -0.0005
- pair_target_gene_coexpression_product_e599: -0.0002
- pair_replogle_delta_sum_product_combined_e600: -0.0008
- random_projection_ppi_replogle_e603: -0.0026
- pair_target_expression_variance_e604: -0.0005
- additive_times_target_coexpression_e610: -0.0008
- ppi_shortest_path_inverse_e611: -0.0014
- pair_target_expression_product_e612: -0.0007
- replogle_target_sum_squared_e613: -0.0010
- geneset_overlap_target_expression_weight_e614: -0.0006
- pair_target_expression_diff_e621: -0.0014
- mean_inv_ppi_distance_to_targets_e623: -0.0024
- pair_replogle_delta_sum_squared_e625: -0.0013
- additive_response_over_target_variance_e626: -0.0079
- pair_replogle_delta_ratio_e700_e633: -0.0017
- additive_times_pair_replogle_ratio_e703_e636: -0.0017
- ppi_replogle_propagation_pair_weighted_e_e637: -0.0017
- additive_times_pair_replogle_delta_produ_e645: -0.0020
- min_ppi_distance_to_targets_e646: -0.0026
- replogle_weighted_geneset_overlap_e647: -0.0020
- pair_target_coexpression_difference_e648: -0.0010
- random_ppi_projection_e652: -0.0018
- pair_target_coexpression_difference_e660: -0.0011
- replogle_sum_times_ppi_propagation_e661: -0.0020
- random_projection_replogle_ppi_e662: -0.0017
- ppi_replogle_coexpression_interaction_e675: -0.0005
- pair_target_coexpression_asymmetry_e676: -0.0003
- target_control_expression_variance_e679: -0.0005
- ppi_replogle_propagation_squared_e680: -0.0005
- additive_response_target_count_penalty_e688: -0.0062
- replogle_delta_mean_targets_e698: -0.0015
- pair_geneset_union_overlap_e700: -0.0006
- pair_replogle_product_times_additive_squ_e705: -0.0003
- pair_replogle_product_clipped_e706: -0.0015
- ppi_weighted_pair_replogle_product_e707: -0.0015
- pair_target_coexpression_difference_e708: -0.0003
- random_fourier_additive_pair_product_e710: -0.0021
- ppi_neighbor_target_replogle_sum_e714: -0.0002
- additive_times_target_coexpression_e717: -0.0012
- random_fourier_additive_replogle_product_e728: -0.0005

## FAILED FEATURES
- EXP_0021 coexpr_times_additive_e21 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0030 pair_interaction_deviation_e30 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0057 replogle_target_magnitude_pair_e57 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0060 pair_additivity_departure_residual_e60 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0070 random_target_projection_e70 [test]: feature failed after 2 attempts: rt_w4_r2/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cac
- EXP_0091 ppi_replogle_weighted_distance_e91 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0108 signed_ppi_proximity_e94_e108 [guard]: iteration over a set of objects (line 52) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0129 replogle_coexpression_residual_e129 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0132 coexpression_rank_x_additive_e132 [test]: feature failed after 2 attempts: line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andres
- EXP_0143 replogle_additive_profile_correlation_e143 [test]: feature failed after 2 attempts: ns), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r2/worktre
- EXP_0155 replogle_profile_similarity_e146_e155 [test]: feature failed after 2 attempts: _r2/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) i
- EXP_0156 ppi_neighbor_replogle_magnitude_e147_e156 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0168 additive_x_coexpression_rank_e168 [test]: feature failed after 2 attempts: y", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/an
- EXP_0170 random_tanh_replogle_profile_projection_e170 [experiment]: IndexError: index 112 is out of bounds for axis 0 with size 112
- EXP_0174 additive_response_rank_e174 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0185 random_nonlinear_projection_current_e185 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0193 additive_response_normalized_e193 [test]: feature failed after 2 attempts: server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache el
- EXP_0234 replogle_weighted_coexpression_e234 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0236 geneset_replogle_enrichment_e236 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0262 additive_times_ppi_distance_e262 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0265 replogle_profile_corr_with_additive_e265 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0266 ppi_neighbor_replogle_abs_mean_e266 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0289 replogle_coexpression_ppi_weighted_e289 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0291 target_expression_times_replogle_coexpre_e291 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0295 ppi_additive_propagation_times_coexpress_e295 [test]: feature failed after 2 attempts:           Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r2/worktrees/_server/gen
- EXP_0297 additive_response_rank_e297 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0298 target_control_expression_mean_rank_e298 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0305 signed_replogle_coexpression_squared_e305 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0312 additive_times_target_expr_times_replogl_e312 [test]: feature failed after 2 attempts: e 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarr
- EXP_0314 signed_replogle_coexpression_rank_e296_e314 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0315 ppi_shortest_path_additive_propagation_e_e315 [experiment]: KeyError: 'weighted_target_coexpression_e58'
- EXP_0317 random_projection_additive_replogle_e317 [experiment]: KeyError: 'weighted_target_coexpression_e58'
- EXP_0318 abs_additive_response_sqrt_e318 [experiment]: ValueError: could not broadcast input array from shape (112,2083) into shape (119,2083)
- EXP_0324 pair_target_coexpression_difference_e324 [experiment]: KeyError: 'weighted_target_coexpression_e58'
- EXP_0325 additive_times_target_pair_coexpression_e325 [test]: feature failed after 2 attempts: ine.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Use
- EXP_0326 min_ppi_shortest_path_to_target_e326 [experiment]: KeyError: 'weighted_target_coexpression_e58'
- EXP_0327 neighbor_replogle_delta_mean_e327 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0328 ppi_neighbor_geneset_overlap_fraction_e328 [experiment]: KeyError: 'weighted_target_coexpression_e58'
- EXP_0331 random_fourier_additive_targetexpr_e331 [experiment]: KeyError: 'weighted_target_coexpression_e58'
- EXP_0337 ppi_neighbor_weighted_replogle_count_e337 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0368 additive_response_rank_e368 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0372 target_signed_replogle_weighted_coexpres_e372 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0385 random_fourier_network_features_e385 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0392 coexpression_replogle_product_e392 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0393 target_expression_replogle_product_e393 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0395 additive_response_rank_e395 [test]: feature failed after 2 attempts: enemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
- EXP_0403 random_fourier_all_features_e403 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0404 target_ppi_neighbor_replogle_mean_e404 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0405 target_coexpr_times_replogle_e405 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0406 weighted_geneset_similarity_e406 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0408 target_expr_times_replogle_e408 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0416 ppi_neighbor_replogle_coexpression_e416 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0422 ppi_neighbor_count_high_replogle_e422 [test]: feature failed after 2 attempts: ees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cac
- EXP_0423 target_geneset_high_replogle_enrichment_e423 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0435 ppi_replogle_propagation_squared_e435 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0440 additive_times_replogle_target_sum_e431_e440 [test]: feature failed after 2 attempts: ila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  F
- EXP_0443 target_expression_times_replogle_delta_e_e443 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0459 additive_response_binned_by_replogle_e459 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0474 random_projection_all_features_e460_e474 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0478 additive_times_target_coexpression_e478 [test]: feature failed after 2 attempts: .py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/
- EXP_0487 random_fourier_all_features_e487 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0494 replogle_ppi_propagation_times_target_su_e494 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0496 additive_times_pair_target_coexpression_e496 [test]: feature failed after 2 attempts: emila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
 
- EXP_0509 ppi_neighbor_high_replogle_count_e509 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0519 random_fourier_all_features_e519 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0537 coexpression_replogle_propagation_e537 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0538 additive_response_binned_by_replogle_mag_e538 [test]: feature failed after 2 attempts: orman_ds_addstart_w4_r2/worktrees/_server/genemila/pipeline.py", line 313, in smoke
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
 
- EXP_0548 random_fourier_all_features_e548 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0549 ppi_replogle_sum_e550_e549 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0550 gene_replogle_delta_e551_e550 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0551 pair_replogle_delta_max_e552_e551 [test]: feature failed after 2 attempts:  in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/D
- EXP_0552 pair_replogle_delta_min_e553_e552 [test]: feature failed after 2 attempts: r2/worktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if
- EXP_0553 additive_times_gene_replogle_e554_e553 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0558 ppi_neighbor_replogle_sum_e558 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0559 pair_replogle_delta_minmax_e559 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0568 additive_response_normalized_by_target_v_e568 [test]: feature failed after 2 attempts: eline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/U
- EXP_0572 random_fourier_all_features_e572 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0575 additive_times_replogle_product_e575 [test]: feature failed after 2 attempts: orktrees/_server/genemila/pipeline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if arg
- EXP_0577 pair_ppi_distance_e577 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR+FEV depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0579 ppi_replogle_propagation_decay_e579 [guard]: top-level Try statement not allowed
- EXP_0615 random_projection_additive_ppi_e615 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0622 additive_times_target_coexpression_e622 [test]: feature failed after 2 attempts: peline.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/
- EXP_0624 weighted_geneset_overlap_e624 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0628 ppi_graph_embedding_e628 [test]: feature failed after 2 attempts: LEAKAGE non-deterministic output; label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p)); output depends on the
- EXP_0634 pair_replogle_delta_geomean_e701_e634 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0635 pair_replogle_delta_diff_e702_e635 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0640 random_fourier_top_features_e705_e640 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0649 additive_response_per_target_e649 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0658 additive_times_pair_replogle_delta_produ_e658 [test]: feature failed after 2 attempts: ne.py", line 393, in main
    r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/User
- EXP_0659 pair_target_ppi_shortest_path_e659 [guard]: iteration over a set of objects (line 59) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0677 signed_geneset_overlap_replogle_e677 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0678 pair_replogle_product_ppi_distance_e678 [guard]: iteration over a set of objects (line 74) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0682 random_fourier_ppi_additive_e682 [experiment]: KeyError: 'pair_replogle_delta_product_e361'
- EXP_0687 ppi_weighted_pair_replogle_product_e687 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0689 pair_signed_replogle_coexpression_produc_e689 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0690 ppi_propagated_pair_replogle_product_e690 [experiment]: KeyError: 'pair_replogle_delta_product_e361'
- EXP_0691 replogle_weighted_pair_geneset_overlap_e691 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0694 random_fourier_additive_pair_product_e694 [experiment]: KeyError: 'pair_replogle_delta_product_e361'
- EXP_0695 random_fourier_additive_pair_product_e695 [test]: feature failed after 2 attempts: s.plugins), out,
              Path(args.cache) if args.cache else None)
  File "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r2/
- EXP_0696 pair_coexpression_asymmetry_e696 [experiment]: KeyError: 'pair_replogle_delta_product_e361'
- EXP_0697 pair_target_ppi_distance_e697 [experiment]: KeyError: 'pair_replogle_delta_product_e361'
- EXP_0701 ppi_pair_replogle_product_propagation_e701 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0702 random_fourier_additive_pair_product_e702 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AHR depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0709 replogle_sum_times_additive_e709 [test]: feature failed after 2 attempts: NaN/inf values
- EXP_0716 pair_replogle_product_ppi_neighbor_jacca_e716 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)

## SURPRISING RESULTS
- nn_response_e15 made the model worse (-0.0119) despite a linear model being able to ignore it (overfitting or scale issue)
- additive_times_target_expression_varianc_e217 made the model worse (-0.0194) despite a linear model being able to ignore it (overfitting or scale issue)
- ppi_additive_prop_times_target_expr_e498 made the model worse (-0.0155) despite a linear model being able to ignore it (overfitting or scale issue)

## ENSEMBLE FINALIST
EXP_0729: average of EXP_0715, EXP_0724, EXP_0643 scores 0.6507 on the visible perturbations (query-only 0.7201). It is a finalist, not the best single model; the union of its members' features is listed in summary.json.

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0729 | ensemble | 0.6507 | 0.7201 | -0.0694 |
| EXP_0715 | new_feature | 0.6506 | 0.7200 | -0.0694 |
| EXP_0724 | config | 0.6506 | 0.7201 | -0.0695 |
| EXP_0643 | config | 0.6502 | 0.7203 | -0.0701 |
| EXP_0003 | baseline | 0.6313 | 0.7126 | -0.0813 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0729 | 0.008 / 0.005 | 0.983 / 0.989 | 0.963 / 0.974 | 0.173 / 0.108 | 0.903 / 0.937 | 0.753 / 0.843 |
| EXP_0715 | 0.008 / 0.005 | 0.983 / 0.989 | 0.963 / 0.974 | 0.173 / 0.108 | 0.904 / 0.937 | 0.754 / 0.844 |
| EXP_0724 | 0.008 / 0.005 | 0.983 / 0.989 | 0.963 / 0.974 | 0.174 / 0.109 | 0.903 / 0.937 | 0.753 / 0.843 |
| EXP_0643 | 0.008 / 0.005 | 0.983 / 0.989 | 0.963 / 0.974 | 0.174 / 0.109 | 0.903 / 0.937 | 0.753 / 0.843 |
| EXP_0003 | 0.008 / 0.006 | 0.983 / 0.988 | 0.961 / 0.972 | 0.163 / 0.102 | 0.909 / 0.941 | 0.764 / 0.846 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0729 | 0.552 / 0.551 | 0.733 / 0.758 | 0.558 / 0.524 | 0.936 / 0.948 | 0.828 / 0.867 | 0.964 / 0.973 |
| EXP_0715 | 0.551 / 0.550 | 0.732 / 0.757 | 0.556 / 0.521 | 0.936 / 0.948 | 0.828 / 0.867 | 0.964 / 0.973 |
| EXP_0724 | 0.553 / 0.553 | 0.734 / 0.759 | 0.558 / 0.523 | 0.936 / 0.949 | 0.828 / 0.868 | 0.964 / 0.973 |
| EXP_0643 | 0.554 / 0.553 | 0.734 / 0.759 | 0.557 / 0.523 | 0.936 / 0.949 | 0.828 / 0.867 | 0.964 / 0.973 |
| EXP_0003 | 0.578 / 0.562 | 0.732 / 0.760 | 0.558 / 0.527 | 0.935 / 0.946 | 0.831 / 0.864 | 0.963 / 0.970 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0729 | 0.706 / 0.684 | 0.009 / 0.006 | 0.744 / 0.763 | 0.559 / 0.489 | 0.893 / 0.903 |
| EXP_0715 | 0.706 / 0.684 | 0.009 / 0.006 | 0.745 / 0.760 | 0.557 / 0.488 | 0.893 / 0.902 |
| EXP_0724 | 0.706 / 0.684 | 0.009 / 0.006 | 0.744 / 0.765 | 0.558 / 0.488 | 0.893 / 0.908 |
| EXP_0643 | 0.706 / 0.684 | 0.009 / 0.006 | 0.743 / 0.765 | 0.558 / 0.488 | 0.893 / 0.903 |
| EXP_0003 | 0.699 / 0.677 | 0.009 / 0.007 | 0.779 / 0.813 | 0.557 / 0.480 | 0.892 / 0.902 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1673.27
- Mean CPU s/experiment: 2.17
- Gain per CPU-hour: 0.0571
- Gain per USD: 0.0141
- LLM cost per completed experiment: $0.00245

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r2 --experiment EXP_0715`
