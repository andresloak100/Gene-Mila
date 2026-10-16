# Block F feature-level reading: pooled Holm over every gene_annotation feature

Family m_total = 66 add-one rows (status ok, stage 1); 20 tested against the null (stage 2); untested rows enter Holm at p = 1. A feature is found when its pooled Holm p <= 0.05 and the tool's other criteria hold; tier 1 only when its source does not read replogle2022_k562.

| source | feature | z (stage 1) | null p | Holm p (pooled) | other failed criteria | reads Replogle | found | tier 1 |
|---|---|---:|---:|---:|---|---|---|---|
| f_r3 | additive_response_x_target_promoter_cpg_e412 | 3.68 | 0.0007576 | 0.05 | - | no | **yes** | **yes** |
| f_r0 | additive_times_target_promoter_cpg_e428 | 3.68 | 0.0007576 | 0.05 | - | no | **yes** | **yes** |
| f_r0 | additive_times_target_promoter_cpg_e666 | 3.68 | 0.0007576 | 0.05 | - | no | **yes** | **yes** |
| f_r0 | additive_times_bidirectional_proximity_e541 | 3.12 | 0.0007576 | 0.05 | - | no | **yes** | **yes** |
| f_r3 | replogle_additive_x_target_promoter_gc_e328 | 2.69 | 0.0007576 | 0.05 | - | yes | **yes** | no |
| f_r3 | replogle_additive_x_promoter_cpg_oe_e441 | 2.50 | 0.0007576 | 0.05 | - | yes | **yes** | no |
| f_r0 | additive_times_target_hydrophobic_fracti_e679 | 2.43 | 1 | 1 | - | no | no | no |
| f_r0 | additive_times_bidirectional_count_e485 | 2.33 | 0.6447 | 1 | - | no | no | no |
| f_r0 | screen_delta_over_transcript_length_e547 | 2.25 | 0.0007576 | 0.05 | - | yes | **yes** | no |
| f_r3 | replogle_additive_x_target_promoter_cpg__e590 | 2.23 | 0.0007576 | 0.05 | - | yes | **yes** | no |
| f_r3 | replogle_additive_x_target_promoter_cpg__e558 | 2.14 | 0.0007576 | 0.05 | - | yes | **yes** | no |
| f_r3 | replogle_additive_x_target_promoter_cpg_e460 | 2.05 | 0.0007576 | 0.05 | - | yes | **yes** | no |
| f_r3 | target_mean_cpg_oe_promoter_e402_e350 | 1.49 | 1 | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain | no | no | no |
| f_r0 | target_promoter_cpg_e406 | 1.49 | 1 | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain | no | no | no |
| f_r3 | target_promoter_cpg_mean_e521 | 1.49 | 1 | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain | no | no | no |
| f_r0 | screen_delta_over_transcript_length_e546 | 1.40 | 1 | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain | yes | no | no |
| f_r3 | bidirectional_partner_coexpression_with__e531 | 1.40 | 0.0007576 | 0.05 | M1 gain not above 2 SE_adj with wins > n/2 | no | no | no |
| f_r0 | additive_times_target_exon_count_e548 | 1.25 | 0.0007576 | 0.05 | M1 gain not above 2 SE_adj with wins > n/2 | no | no | no |
| f_r0 | additive_times_bidirectional_proximity_e542 | 1.04 | 0.0007576 | 0.05 | M1 gain not above 2 SE_adj with wins > n/2 | no | no | no |
| f_r3 | gene_annotation_random_projection_e567 | 0.53 | 0.0007576 | 0.05 | M1 gain not above 2 SE_adj with wins > n/2 | no | no | no |
| f_r3 | additive_response_x_target_promoter_cpg_e509 | 0.20 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain | no | no | no |
| f_r0 | additive_times_cds_length_e445 | 0.16 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_cds_length_e449 | 0.16 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | replogle_additive_x_promoter_cpg_oe_e391 | 0.02 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_exon_count_e415 | -0.13 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_target_transcript_length_e407 | -0.33 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain | no | no | no |
| f_r0 | additive_times_gene_span_e347 | -0.39 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_n_transcripts_e453 | -0.62 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_intron_length_e443 | -0.66 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_transcript_length_e316 | -0.77 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_transcript_length_e310 | -0.77 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | gene_annotation_ppi_random_projection_e721 | -0.94 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_cpg_oe_promoter_e455 | -0.95 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_cpg_promoter_e325 | -0.95 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_promoter_cpg_e420 | -0.95 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | cpg_promoter_x_additive_response_e142 | -0.95 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_cpg_oe_promoter_squared_e473 | -1.01 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | additive_response_x_gene_span_e128 | -1.10 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_gene_span_e331 | -1.10 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | gene_span_x_additive_response_e143 | -1.10 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_gc_cds_e418 | -1.10 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | cpg_oe_promoter_x_additive_e129 | -1.12 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | target_gene_span_times_screen_e717 | -1.13 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | yes | no | no |
| f_r3 | additive_response_x_mean_target_gene_spa_e303 | -1.15 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_target_gene_span_e401 | -1.15 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_target_span_product_e545 | -1.16 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_utr3_length_e451 | -1.16 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | screen_delta_over_transcript_length_e416 | -1.18 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | yes | no | no |
| f_r3 | additive_response_x_mean_target_span_e296 | -1.35 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | gene_annotation_random_projection_e697 | -1.35 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_utr3_length_e441 | -1.38 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | replogle_additive_x_mean_target_span_e31_e310 | -1.46 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | yes | no | no |
| f_r0 | additive_times_bidirectional_partner_e469 | -1.52 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | mean_target_promoter_gc_e295 | -1.63 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | target_chromatin_accessibility_e242 | -1.63 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | target_promoter_gc_e80_e81 | -1.63 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | additive_times_target_cpg_promoter_e489 | -1.68 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | screen_delta_times_cds_length_e446 | -1.78 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | replogle_additive_x_promoter_cpg_island_e507 | -1.83 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | yes | no | no |
| f_r2 | tf_binding_motif_score_e192 | -2.17 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | screen_delta_times_target_promoter_cpg_e694 | -2.26 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | yes | no | no |
| f_r0 | target_hydrophobic_fraction_e675 | -2.32 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | promoter_similarity_target_g_e564 | -2.40 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r3 | target_annotation_random_projection_e575 | -2.65 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | no | no | no |
| f_r0 | screen_delta_times_promoter_cpg_e377 | -2.98 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain | yes | no | no |
| f_r3 | target_promoter_cpg_x_gene_control_varia_e594 | -3.05 |  | 1 | M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain; mse_top significantly worse | no | no | no |
