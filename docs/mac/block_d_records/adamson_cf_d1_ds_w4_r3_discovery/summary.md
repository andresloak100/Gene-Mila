# RUN SUMMARY

Run `adamson_cf_d1_ds_w4_r3_discovery` on dataset `adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`, code `23b3b1281f`)

- Duration: 20.2 min
- Workers: 4
- Experiments proposed: 664
- Experiments completed: 646 (plus baselines; deepseek:deepseek-v4-pro: 97, python:exploit: 543, sweep(deepseek:deepseek-v4-pro): 6)
- Experiments failed / rejected / killed / not started: 10 / 2 / 0 / 0
- Unique hypotheses: 661 (replicated: 3); duplicate configurations skipped: 6
- CPU hours: 0.0502
- LLM (worker): 120 calls, 209931 in / 64228 out / 134400 cached tokens, $0.1005
- LLM (planner): 14 calls, 79988 in / 36379 out / 20352 cached tokens, $0.2237

## BASELINE PERFORMANCE
EXP_0003: OLS on baseline features (control mean, mean response, target indicator). pearson_delta = 0.5014

## BEST PERFORMANCE
EXP_0518: pearson_delta = 0.5507 (ridge, alpha=41310.0)

## IMPROVEMENT
0.0494 over the best baseline

## BEST MODEL / FEATURES INCLUDED
- gene_set_similarity_transfer_e177: coefficient +0.0339
- is_target: coefficient -0.0047
- has_signal_peptide_flag_e55: coefficient +0.0019
- aa_hydrophobic_fraction_gene_e99: coefficient +0.0005
- protein_length_log_e35: coefficient -0.0002
- atf4_atf6_pathway_membership_e112: coefficient +0.0002
- atf4_atf6_pathway_membership_e113: coefficient +0.0002
- is_transcription_factor_e13: coefficient -0.0001
- is_tf_e25: coefficient -0.0001
- n_transmembrane_domains_e56: coefficient -0.0001
- prec_constraint_e173: coefficient +0.0000

## DISCOVERY LINEAGE
EXP_0003 [baseline] score 0.5014
    ↳ EXP_0013 [is_transcription_factor_e13] score 0.5014
        ↳ EXP_0017 [config] score 0.5020
            ↳ EXP_0022 [protein_compartment_e22] score 0.5026
                ↳ EXP_0028 [config] score 0.5026
                    ↳ EXP_0040 [config] score 0.5026
                        ↳ EXP_0052 [config] score 0.5027
                            ↳ EXP_0055 [has_signal_peptide_flag_e55] score 0.5028
                                ↳ EXP_0078 [target_response_gc_interaction_e66_e78] score 0.5031
                                    ↳ EXP_0079 [config] score 0.5031
                                        ↳ EXP_0092 [config] score 0.5031
                                            ↳ EXP_0094 [config] score 0.5032
                                                ↳ EXP_0106 [config] score 0.5034
                                                    ↳ EXP_0121 [config] score 0.5034
                                                        ↳ EXP_0134 [config] score 0.5034
                                                            ↳ EXP_0177 [gene_set_similarity_transfer_e177] score 0.5459
                                                                ↳ EXP_0183 [config] score 0.5462
                                                                    ↳ EXP_0188 [config] score 0.5463
                                                                        ↳ EXP_0193 [config] score 0.5496
                                                                            ↳ EXP_0194 [config] score 0.5496
                                                                                ↳ EXP_0198 [config] score 0.5496
                                                                                    ↳ EXP_0202 [config] score 0.5497
                                                                                        ↳ EXP_0206 [config] score 0.5499
                                                                                            ↳ EXP_0210 [config] score 0.5502
                                                                                                ↳ EXP_0220 [config] score 0.5503
                                                                                                    ↳ EXP_0222 [config] score 0.5503
                                                                                                        ↳ EXP_0236 [config] score 0.5504
                                                                                                            ↳ EXP_0247 [config] score 0.5504
                                                                                                                ↳ EXP_0260 [config] score 0.5504
                                                                                                                    ↳ EXP_0274 [config] score 0.5504
                                                                                                                        ↳ EXP_0300 [config] score 0.5505
                                                                                                                            ↳ EXP_0308 [config] score 0.5506
                                                                                                                                ↳ EXP_0344 [config] score 0.5506
                                                                                                                                    ↳ EXP_0396 [config] score 0.5507
                                                                                                                                        ↳ EXP_0402 [config] score 0.5507
                                                                                                                                            ↳ EXP_0456 [config] score 0.5507
                                                                                                                                                ↳ EXP_0518 [config] score 0.5507

## MOST USEFUL FEATURES
- gene_set_similarity_transfer_e177 (EXP_0177): +0.0425. Similarity-weighted average of training delta responses, where weights are Jaccard similarities between gene sets containing the perturbation's target gene.
- protein_compartment_e22 (EXP_0022): +0.0006. Binary indicators for whether gene g's protein is localized to mitochondrion, nucleus, or endoplasmic reticulum (from protein_annotation).
- target_response_gc_interaction_e66_e78 (EXP_0078): +0.0003. Interaction between the gc_cds of the perturbation target gene and the gc_cds of each response gene (product or absolute difference).
- has_signal_peptide_flag_e55 (EXP_0055): +0.0001. Binary feature: 1 if gene g's protein has a signal peptide, else 0.
- cpg_oe_promoter_e34 (EXP_0034): +0.0000. Observed/expected CpG ratio in promoter for gene g (gene_annotation.cpg_oe_promoter), median-imputed.
- is_transcription_factor_e13 (EXP_0013): +0.0000. Binary feature: 1 if gene g is in the transcription_factors list, else 0.
- atf4_atf6_pathway_membership_e84 (EXP_0084): +0.0000. Binary feature: 1 if gene g is in any gene set whose name contains 'ATF4' or 'ATF6' (or is a neighbor of ATF4 in prior_network), else 0.
- protein_length_log_e35 (EXP_0035): +0.0000. Log10 of protein_length (from protein_annotation) plus 1, per gene.
- control_std_e11 (EXP_0011): +0.0000. Standard deviation of gene expression across control cells.

## FEATURES THAT DID NOT HELP
- lof_constraint_e8: -0.0001
- gene_set_membership_e9: -0.0001
- target_coexpr_abs_e12: -0.0038
- protein_localization_mito_e15: -0.0001
- gene_set_membership_e20: -0.0002
- control_std_e23: -0.0002
- gene_corr_target_e24: -0.0060
- is_tf_e25: -0.0000
- loeuf_constraint_e26: -0.0002
- gene_span_log_e32: -0.0002
- intron_length_log_e33: -0.0002
- is_prior_neighbor_e37: -0.0000
- target_globin_set_similarity_e39: -0.0000
- gene_span_log_e44: -0.0003
- intron_length_log_e45: -0.0003
- ppi_partner_response_transfer_e47: -0.0000
- cpg_oe_promoter_e48: -0.0000
- n_transcripts_log_e49: -0.0001
- globin_set_similarity_e51: -0.0000
- ppi_globin_proximity_e54: -0.0002
- n_transmembrane_domains_e56: -0.0001
- cpg_oe_promoter_value_e57: -0.0001
- n_upstream_atg_count_e58: -0.0001
- n_upstream_atg_e60_e71: -0.0000
- utr5_length_log_e61_e72: -0.0000
- gc_cds_e62_e73: -0.0002
- pli_e63_e74: -0.0000
- signal_peptide_length_e64_e75: -0.0000
- aa_cysteine_fraction_e65_e76: -0.0000
- gata1_nfe2_regulon_membership_e83: -0.0001
- carbon_dioxide_transport_membership_e85: -0.0001
- intron_length_kb_direct_e88: -0.0001
- signal_peptide_length_e89: -0.0000
- gc_cds_direct_e90: -0.0001
- pli_direct_e91: -0.0000
- pli_gene_side_e98: -0.0001
- aa_hydrophobic_fraction_gene_e99: -0.0000
- nearest_tss_distance_gene_e100: -0.0001
- tss_density_gene_e101: -0.0002
- syn_z_gene_e102: -0.0001
- gc_utr3_gene_e103: -0.0004
- residual_pathway_similarity_gene_e105: -0.0000
- globin_family_membership_e110: -0.0005
- globin_family_membership_e111: -0.0005
- atf4_atf6_pathway_membership_e112: -0.0003
- atf4_atf6_pathway_membership_e113: -0.0003
- gata1_nfe2_regulon_membership_e114: -0.0004
- gata1_nfe2_regulon_membership_e115: -0.0004
- gc_utr3_direct_e116: -0.0006
- n_exons_direct_e117: -0.0005
- oe_mis_direct_e118: -0.0004
- syn_z_direct_e119: -0.0003
- gc_promoter_gene_e110_e125: -0.0003
- n_exons_gene_e111_e126: -0.0006
- cds_length_gene_e112_e127: -0.0004
- utr3_length_gene_e113_e128: -0.0006
- obs_lof_gene_e114_e129: -0.0003
- mis_z_gene_e115_e130: -0.0004
- cpg_island_promoter_gene_e116_e132: -0.0003
- aa_composition_gene_e125_e137: -0.0005
- promoter_gc_gene_e126_e138: -0.0004
- transcript_length_gene_e127_e139: -0.0006
- cds_length_gene_e128_e140: -0.0004
- utr3_length_gene_e129_e141: -0.0005
- obs_lof_gene_e130_e142: -0.0004
- mis_z_gene_e131_e143: -0.0005
- gata1_nfe2_prior_neighbor_gene_e145: -0.0004
- aa_d_fraction_gene_e146: -0.0004
- exp_lof_gene_e147: -0.0006
- globin_coexpression_gene_e148: -0.0006
- target_aars_globin_neighbor_interaction_e149: -0.0058
- residual_pathway_jaccard_gene_e152: -0.0004
- target_aa_composition_interaction_e159: -0.0004
- gene_prec_target_loeuf_interaction_e161: -0.0004
- target_tf_neighbor_regulon_interaction_e162: -0.0006
- globin_corr_target_ars_interaction_e165: -0.0077
- globin_family_membership_e170: -0.0005
- tf_neighbor_interaction_e171: -0.0004
- prec_constraint_e173: -0.0004
- aa_fraction_charged_e175: -0.0004

## FAILED FEATURES
- EXP_0010 prior_network_neighbor_e10 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0021 prior_network_neighbor_e21 [guard]: iteration over a set of objects (line 50) not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects
- EXP_0036 target_degree_prior_e36 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0046 target_prior_degree_e46 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AMIGO3 depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0066 target_ppi_degree_e66 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0120 ppi_degree_target_e120 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0144 ppi_neighbor_response_transfer_e132_e144 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0150 protein_length_mito_target_interaction_e150 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0158 target_globin_neighbor_similarity_e158 [test]: feature failed after 2 attempts: LEAKAGE label leakage: features for training perturbation AMIGO3 depend on its own label (use ctx.train_delta(exclude=p))
- EXP_0160 target_ppi_degree_interaction_e160 [test]: feature failed after 2 attempts: feature is constant across all rows (no information)
- EXP_0172 control_std_tf_interaction_e172 [guard]: use of 'hash' not allowed: hash() and id() differ between processes (str hashes are salted per process, id() is a memory address), and so does the order of a set of objects other than strings and numb
- EXP_0174 ppi_degree_interaction_e174 [test]: feature failed after 2 attempts: or: PPIDegreeInteraction.compute() takes 3 positional arguments but 4 were given
Traceback (most recent call last):
  File "/Users/andresarriaga/Documents/Mila/Gene-Mi

## SURPRISING RESULTS
- none

## ENSEMBLE FINALIST
- none kept (the average of the finalists did not beat the best single model, or ensembles are off)

## GENERALIZATION TO QUERY-ONLY VALIDATION
| experiment | kind | visible | query-only | gap |
|---|---|---|---|---|
| EXP_0518 | config | 0.5507 | 0.5793 | -0.0286 |
| EXP_0540 | config | 0.5507 | 0.5793 | -0.0286 |
| EXP_0526 | config | 0.5507 | 0.5793 | -0.0286 |
| EXP_0003 | baseline | 0.5014 | 0.5196 | -0.0182 |

## CELLFORGE METRICS (visible / query-only)
Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1).

| experiment | mse | pcc | r2 | mse_de | pcc_de | r2_de |
|---|---|---|---|---|---|---|
| EXP_0518 | 0.005 / 0.007 | 0.988 / 0.986 | 0.975 / 0.968 | 0.121 / 0.148 | 0.944 / 0.934 | 0.827 / 0.744 |
| EXP_0540 | 0.005 / 0.007 | 0.988 / 0.986 | 0.975 / 0.968 | 0.121 / 0.148 | 0.944 / 0.934 | 0.827 / 0.744 |
| EXP_0526 | 0.005 / 0.007 | 0.988 / 0.986 | 0.975 / 0.968 | 0.121 / 0.148 | 0.944 / 0.934 | 0.827 / 0.744 |
| EXP_0003 | 0.006 / 0.007 | 0.987 / 0.985 | 0.973 / 0.966 | 0.127 / 0.154 | 0.944 / 0.932 | 0.821 / 0.734 |

## VCWORLD METRICS (visible / query-only)
DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on true DE genes; a prediction's log2FC decides both (VCWorld).

| experiment | de_f1 | de_auroc | de_auprc | dir_accuracy | dir_f1 | dir_auroc |
|---|---|---|---|---|---|---|
| EXP_0518 | 0.191 / 0.157 | 0.681 / 0.711 | 0.368 / 0.387 | 0.896 / 0.941 | 0.818 / 0.866 | 0.943 / 0.968 |
| EXP_0540 | 0.191 / 0.157 | 0.680 / 0.711 | 0.368 / 0.387 | 0.896 / 0.941 | 0.818 / 0.866 | 0.943 / 0.968 |
| EXP_0526 | 0.191 / 0.157 | 0.681 / 0.711 | 0.368 / 0.387 | 0.896 / 0.941 | 0.818 / 0.866 | 0.943 / 0.968 |
| EXP_0003 | 0.138 / 0.111 | 0.659 / 0.666 | 0.314 / 0.284 | 0.890 / 0.929 | 0.814 / 0.844 | 0.934 / 0.957 |

## CELL-EVAL (visible / query-only)
Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json and runs/<run>/celleval/.

| experiment | pearson_delta | mse | discrimination_score_l1 | overlap_at_N | de_direction_match |
|---|---|---|---|---|---|
| EXP_0518 | 0.533 / 0.525 | 0.007 / 0.008 | 0.612 / 0.544 | 0.382 / 0.314 | 0.871 / 0.933 |
| EXP_0540 | 0.533 / 0.525 | 0.007 / 0.008 | 0.612 / 0.544 | 0.382 / 0.314 | 0.871 / 0.933 |
| EXP_0526 | 0.533 / 0.525 | 0.007 / 0.008 | 0.612 / 0.544 | 0.382 / 0.314 | 0.871 / 0.933 |
| EXP_0003 | 0.504 / 0.477 | 0.007 / 0.008 | 0.536 / 0.526 | 0.361 / 0.280 | 0.863 / 0.903 |

## COMPUTE EFFICIENCY
- Experiments/hour: 1917.47
- Mean CPU s/experiment: 0.28
- Gain per CPU-hour: 0.9830
- Gain per USD: 0.1523
- LLM cost per completed experiment: $0.00050

## REPRODUCTION COMMAND
`python reproduce.py --run /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r3_discovery --experiment EXP_0518`
