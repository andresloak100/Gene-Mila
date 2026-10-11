# Feature audit: redundancy, compact model and the failed-feature box

Protocol, fixed before any result under it was read. Per run: the selected single model (highest visible score among completed non-ensemble, non-baseline experiments); a pool adds the features that raised their parent's score by more than 0.0005, and the built-ins. Scores are pearson_delta per visible perturbation: out of fold for the 50 training perturbations (5 folds; features that read training labels, detected per feature on a fresh view, recomputed without each fold) and, from a fit on all of them, for the 17 visible validation perturbations; every fit is ridge on columns standardised by its training rows. With two fold seeds (the run's own and the next), each subset's penalty is chosen on the training perturbations' out-of-fold scores under one fold partition and reported under the other (both ways averaged), so only the validation perturbations are independent of it. The greedy paths and the compact model (smallest set on the backward path within max(paired SE, 0.001) of its best) are chosen on the training perturbations alone; compact and full are compared, paired, on the validation perturbations, untouched by any choice of this tool (the lab chose the selected model partly on them). A difference within max(SE, 0.001) is either not established or below 0.001, a margin of practical equivalence. Lasso: penalty by cross-validation over the fold-recomputed designs, then 50 half-samples; stable = selected in at least 80%. Verdicts, in order: kept, required_input, unstable (changes with the hash seed), harmful, redundant (|r| ≥ 0.9 with a kept feature), substitutable (established drop-one gain the compact set does without), no_gain, unrecomputable. A composite (a feature computing others through ctx.feature) is one feature; what a kept one computes is a required input (+k), never boxed.

## Runs

| run | arm | feat. | cols | rank | dup. | r≥0.9 | compact f/c | full | compact | Δ val (SE) | Lasso |
|---|---|---|---|---|---|---|---|---|---|---|---|
| newcode_derule_opus_w4_r0 | A1 | 12 | 16 | 16 | 1 | 1 | 4/6 | 0.5809 | 0.5862 | -0.0009 (0.0042) | 8/12 |
| scale_w1_r0 | A2 | 12 | 17 | 16 | 1 | 3 | 5/7 | 0.5703 | 0.5740 | -0.0010 (0.0053) | 6/12 |
| scale_w1_r1 | A2 | 11 | 15 | 14 | 2 | 2 | 3/6 | 0.5654 | 0.5649 | -0.0094 (0.0132) | 5/11 |
| scale_w4_r0 | A2 | 18 | 28 | 25 | 2 | 7 | 5/8 | 0.5694 | 0.5867 | -0.0024 (0.0066) | 3/18 |
| scale_w4_r1 | A2 | 12 | 15 | 14 | 0 | 0 | 3/4 | 0.5615 | 0.5709 | -0.0046 (0.0077) | 7/12 |
| scale_w8_r0 † | A2 | 24 | 33 | 33 | 0 | 15 | 4/5 | 0.5766 | 0.5812 | -0.0112 (0.0062) | 1/24 |
| scale_w8_r1 | A2 | 22 | 29 | 28 | 0 | 3 | 4/5 | 0.5436 | 0.5683 | +0.0042 (0.0059) | 5/22 |
| scale_w16_r0 | A2 | 28 | 44 | 39 | 0 | 15 | 5/8 | 0.5660 | 0.5729 | -0.0329 (0.0124) | 3/28 |
| scale_w16_r1 | A2 | 25 (+1) | 33 | 32 | 1 | 9 | 6/8 | 0.5748 | 0.5830 | -0.0239 (0.0126) | 4/25 |
| newcode_opus_w4_r0 | A2 | 12 | 17 | 17 | 0 | 1 | 5/7 | 0.5897 | 0.5886 | +0.0005 (0.0022) | 12/12 |
| newcode_opus_w4_r1 | A2 | 10 | 13 | 11 | 0 | 2 | 5/7 | 0.5841 | 0.5864 | -0.0143 (0.0081) | 4/10 |
| newcode_ds_w4_r0 † | A3 | 15 | 19 | 19 | 0 | 2 | 3/3 | 0.5102 | 0.5091 | -0.0018 (0.0017) | 15/15 |
| newcode_ds_w4_r1 | A3 | 9 | 9 | 8 | 1 | 1 | 3/3 | 0.5886 | 0.5863 | -0.0087 (0.0054) | 9/9 |
| control_components_from_opus_r0 | A4 | 12 | 17 | 16 | 1 | 2 | 5/7 | 0.5900 | 0.5888 | +0.0000 (0.0022) | 12/12 |
| scale_control_r0 | A5 | 4 | 4 | 4 | 0 | 0 | 2/2 | 0.5080 | 0.5084 | +0.0007 (0.0003) | 4/4 |
| scale_control_r1 | A5 | 4 | 4 | 4 | 0 | 0 | 2/2 | 0.5082 | 0.5086 | +0.0006 (0.0003) | 4/4 |
| scale_control_r2 | A5 | 4 | 4 | 4 | 0 | 0 | 2/2 | 0.5078 | 0.5082 | +0.0006 (0.0003) | 4/4 |
| scale_control_r3 | A5 | 4 | 4 | 4 | 0 | 0 | 2/2 | 0.5089 | 0.5094 | +0.0007 (0.0003) | 4/4 |
| scale_control_r4 | A5 | 4 | 4 | 4 | 0 | 0 | 2/2 | 0.5101 | 0.5106 | +0.0007 (0.0003) | 4/4 |
| scale_control_r5 | A5 | 4 | 4 | 4 | 0 | 0 | 2/2 | 0.5066 | 0.5071 | +0.0007 (0.0003) | 4/4 |
| newcode2_control_r0 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5089 | 0.5084 | +0.0004 (0.0009) | 3/3 |
| newcode_control_r0 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5089 | 0.5084 | +0.0004 (0.0009) | 3/3 |
| newcode_control_r1 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5091 | 0.5086 | +0.0003 (0.0008) | 3/3 |
| newcode_control_r2 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5087 | 0.5082 | +0.0003 (0.0009) | 3/3 |
| newcode_control_r3 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5099 | 0.5094 | +0.0004 (0.0010) | 3/3 |
| newcode_control_r4 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5110 | 0.5106 | +0.0004 (0.0009) | 3/3 |
| newcode_control_r5 | A5 | 3 | 3 | 3 | 0 | 0 | 2/2 | 0.5073 | 0.5071 | +0.0003 (0.0008) | 3/3 |
| control_components_w4_r0 | A5 | 4 | 7 | 7 | 0 | 0 | 3/6 | 0.5352 | 0.5348 | -0.0002 (0.0006) | 3/4 |
| astra_ds_w8_2h_20261008T165933Z | A6 | 48 (+8) | 99 | 53 | 4 | 83 | 1 (+30)/50 | 0.5971 | 0.5982 | -0.0005 (0.0011) | 20/48 |
| astra_ds_w8_2h_20261010T135041Z | A7 | 87 (+16) | 176 | 91 | 11 | 178 | 20 (+29)/88 | 0.5983 | 0.5994 | -0.0045 (0.0022) | 17/87 |

Arms: A1 = claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top); A2 = claude_cli:opus planner, deepseek:deepseek-flash workers; A3 = deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers; A4 = no-LLM continuation of newcode_opus_w4_r0; A5 = scripted control (no LLM); A6 = deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers (continued from newcode_opus_w4_r0); A7 = deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers (continued from previous-run-repaired).
feat./cols: the selected model; dup.: exact duplicate columns; r≥0.9: column pairs with |r| ≥ 0.9; compact f/c: the compact set; full, compact: visible scores (the compact set was chosen on the training perturbations, which flatter it); Δ val: compact − full on the validation perturbations, paired; Lasso: Lasso-stable features. (+k): k required inputs, computed through ctx.feature. †: the audited model is not exactly the run's (selected features unrecomputable or unstable, or the lab's visible score not reproduced within 0.002).

Compact sets (agent runs):

- newcode_derule_opus_w4_r0: target_knockdown_level_e16, gene_transferability_weighted_knn_e129 +2
- scale_w1_r0: mean_response, geneset_knn_response_e8, target_knockdown_scaled_e12 +2
- scale_w1_r1: geneset_knn_response_e7, ppi_knn_response_e22, target_knockdown_magnitude_e38
- scale_w4_r0: mean_response, geneset_matched_response_e15, idf_geneset_knn_residual_e25 +2
- scale_w4_r1: geneset_knn_response_e6, ppi_knn_response_e27, self_knockdown_magnitude_e60
- scale_w8_r0: knn_pert_response_e23, target_expr_knockdown_e40, functional_category_response_e49 +1
- scale_w8_r1: mean_response, residual_softmax_knn_e63, expected_knockdown_delta_e65 +1
- scale_w16_r0: is_target, er_stress_gate_e121, specific_geneset_mate_response_e154 +2
- scale_w16_r1: mean_response, target_knockdown_depth_e76, per_component_score_transfer_e508 +3
- … 6 more runs

## Verdicts

| verdict | agent: selected | agent: pools | no-LLM: selected | no-LLM: pools |
|---|---|---|---|---|
| kept | 76 | 69 | 34 | 34 |
| required_input | 35 | 35 | 0 | 0 |
| unstable | 2 | 2 | 0 | 0 |
| redundant | 22 | 55 | 1 | 2 |
| substitutable | 14 | 12 | 0 | 0 |
| harmful | 17 | 24 | 0 | 2 |
| no_gain | 181 | 298 | 26 | 34 |
| unrecomputable | 0 | 1 | 0 | 0 |

Feature families of the agent runs (name without its _e<experiment> suffix, built-ins left out; one verdict per run and feature, kept in either scope counts as kept), most often kept: geneset_knn_response 6/20, symbol_family_knn_response 3/4, ppi_knn_response 3/6, consensus_knn_response 2/2. Most often boxed: geneset_knn_response 14/20 (11 redundant, 3 no_gain), coexpr_knn_response 3/3 (3 no_gain), geneset_idf_knn_response 3/3 (3 redundant), response_cluster_centroid 3/3 (3 no_gain).

## Detail: astra_ds_w8_2h_20261010T135041Z (highest visible full score)

Selected model EXP_2761: ridge, best alpha 75, 87 features, 176 columns; 5 folds, seeds 0, 1; alpha grid 1, 10, 75, 100, 1000, 10000, 30000, 100000. Full model 0.5983 (alphas 75/75), compact 0.5994 (alphas 75/75). Compact − full on the 17 validation perturbations -0.0045 (0.0022), 5 wins; on the 50 training perturbations that chose it +0.0029 (0.0023). With its 29 required inputs the compact set computes 49 features and 120 columns (full model: 103, 193). Lab's visible scores recomputed at alpha 75: validation 0.6176 vs stored 0.6176; out-of-fold 0.6058 vs stored 0.6058.

Backward path (each step drops the feature whose removal leaves the highest training score; ← compact set, * best; train: out-of-fold training score, val: validation score):

| feat. | cols | removed | train | best − this (SE) | val | alpha |
|---|---|---|---|---|---|---|
| 87 | 176 | (full model) | 0.5918 | +0.0040 (0.0019) | 0.6176 | 75/75 |
| … | | (steps omitted, in the JSON) | | | | |
| 54 * | 124 | phylogenetic_profile_similarity_e3036 | 0.5957 | +0.0000 (0.0000) | 0.6156 | 75/75 |
| … | | (steps omitted, in the JSON) | | | | |
| 20 ← | 88 | signaling_propagated_tf_motif_score_e1331 | 0.5947 | +0.0010 (0.0011) | 0.6131 | 75/75 |
| … | | (steps omitted, in the JSON) | | | | |
| 4 | 72 | geneset_jaccard_similarity_e1827 | 0.5917 | +0.0040 (0.0016) | 0.6114 | 75/75 |
| 3 | 71 | target_knockdown_magnitude_e44 | 0.5887 | +0.0070 (0.0029) | 0.6102 | 75/75 |
| 2 | 70 | half_life_modulated_pathway_response_e926 | 0.5879 | +0.0079 (0.0030) | 0.6098 | 1/1 |
| 1 | 50 | random_projection_all_features_v2_e1079 | 0.5879 | +0.0079 (0.0036) | 0.6109 | 1/1 |

Forward path (add the feature that raises the training score most):

| feat. | cols | added | train | val | alpha |
|---|---|---|---|---|---|
| 1 | 50 | random_projection_all_features_e2763 | 0.5879 | 0.6109 | 1/1 |
| 2 | 51 | target_expression_breadth_response_e3053 | 0.5889 | 0.6105 | 1/1 |
| 3 | 52 | is_target | 0.5896 | 0.6107 | 1/1 |
| … | | 83 steps in the JSON | | | |
| 87 | 176 | coexpression_module_response_e3109 | 0.5918 | 0.6176 | 75/75 |

Drop-one (full − without, paired over all visible perturbations; wins = perturbations where the full model is higher) and single-feature scores:

| feature | cols | single | full − without (SE) | wins | Lasso | verdict |
|---|---|---|---|---|---|---|
| random_projection_all_features_e2763 | 50 | 0.5937 | +0.0288 (0.0104) | 47/67 | 0.92 | kept |
| half_life_modulated_pathway_response_e926 | 1 | 0.4897 | +0.0043 (0.0028) | 44/67 | 0.28 | kept |
| target_knockdown_magnitude_e44 | 1 | 0.0109 | +0.0021 (0.0011) | 44/67 | 0.84 | kept |
| … 81 features in the JSON | | | | | | |
| half_life_x_ppi_diffusion_interaction_e322 | 1 | 0.1488 | -0.0004 (0.0003) | 27/67 | 0.68 | no_gain |
| splicing_factor_x_intron_count_e1848 | 1 | 0.0694 | -0.0004 (0.0004) | 32/67 | 0.54 | no_gain |
| coexpression_module_response_e3109 | 1 | 0.0595 | -0.0005 (0.0002) | 23/67 | 0.86 | no_gain |

Redundancy of the 176 columns: rank 91, effective rank 11.2, condition number singular; 16 constant, 11 exact duplicates, 178 pairs with |r| ≥ 0.9, 642 with |r| ≥ 0.7; most correlated: tf_motif_binding_response_e1303 ~ signaling_propagated_tf_motif_score_e1331 +1.000. Lasso penalty 0.000338; 17 stable features: shared_geneset_score_e15, target_knockdown_magnitude_e44 +15.

Merge test (a cluster at |r| ≥ 0.9 spanning two or more features replaced by its first principal component, fitted on each fit's training rows only; weakest link: the smallest |r| joining it, ≥ 0.9; its ends may correlate less (min_pair_abs_r in the JSON)):

| cluster features | weakest link \|r\| | cols | merged score | merged − full (SE) |
|---|---|---|---|---|
| is_target, combined_network_rwr_response_e840 +6 | 0.945 | 169 | 0.5982 | -0.0001 (0.0002) |
| normalized_mean_response_e56 +1 | 0.907 | 161 | 0.5984 | +0.0000 (0.0005) |
| … 7 more in the JSON | | | | |

## Reading

15 agent runs audited, 15 no-LLM runs as a reference. The compact model keeps a median of 4 of 15 features (7 of 19 columns) and is smaller than the full model in 15 of 15 runs. With its composites' required inputs (2 of 15 runs), it computes a median of 5 of 15 features (7 of 19 columns), the full model's counted alike. It was chosen on the training perturbations' out-of-fold scores, which flatter it (mean compact − full there +0.0096). On the 17 validation perturbations of each run, which no choice of this tool touched, compact − full is within one paired SE in 8 of 15 runs, lower by more than max(SE, 0.001) in 7 (mean -0.0074, median paired SE 0.0059); the lab chose each selected model partly on them, which if anything favours the full model. In 7 runs the dropped features carry signal on perturbations outside the choice that the compact set does not. Of the 269 features of the selected models outside their compact sets, 35 are required inputs of kept features (not boxed); of the other 234, 22 redundant (|r| ≥ 0.9 with a kept feature), 14 substitutable (an established drop-one gain that kept features take over), 181 no_gain and 17 harmful; near-duplication explains a minority of those 234: most are not copies of kept ones; a no_gain feature's drop-one effect is within max(paired SE, 0.001), which is not proof of zero effect. 2 feature(s) of the selected models are unstable (boxed). The engine reproduces the lab's stored visible scores within 0.002 for 28 of 28 selected models. No-LLM runs (reference): the compact model keeps a median of 2 of 4 features; on the validation perturbations it is lower than full by more than max(SE, 0.001) in 0 of the 15 runs where it is smaller. Single fold-seed differences below about 0.02 never were established.
