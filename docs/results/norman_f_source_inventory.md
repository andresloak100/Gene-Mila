# Block F annotation source inventory

Literal key/column references and numeric subscript contexts are source evidence; dynamic access and runtime use are not inferred. Inspect the unchanged copied plugins.

Rows are grouped by the primary rule’s literal `replogle2022_k562` source check. `Selected` refers only to the already recorded visible-selected model. The unchanged full plugin files and metadata JSON retain all numeric subscript contexts and source evidence; a literal mention alone is not proof of runtime use.

Annotation numeric column order: 0=gene_span_kb, 1=n_transcripts, 2=n_exons, 3=transcript_length, 4=cds_length, 5=utr5_length, 6=utr3_length, 7=intron_length_kb, 8=gc_cds, 9=gc_utr3, 10=gc_promoter, 11=cpg_oe_promoter, 12=n_upstream_atg, 13=nearest_tss_kb, 14=n_tss_within_100kb, 15=aa_A, 16=aa_C, 17=aa_D, 18=aa_E, 19=aa_F, 20=aa_G, 21=aa_H, 22=aa_I, 23=aa_K, 24=aa_L, 25=aa_M, 26=aa_N, 27=aa_P, 28=aa_Q, 29=aa_R, 30=aa_S, 31=aa_T, 32=aa_V, 33=aa_W, 34=aa_Y.

## f_r0

Run: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0`.

### Annotation without a literal Replogle read

| Feature | Selected | Literal annotation fields | Literal annotation columns | Numeric subscript contexts |
|---|---|---|---|---:|
| additive_sq_times_promoter_cpg_e400 | no | columns, genes | cpg_oe_promoter | 2 |
| additive_times_bidirectional_count_e485 | no | bidirectional | numeric/dynamic; see source | 1 |
| additive_times_bidirectional_partner_e469 | no | bidirectional | numeric/dynamic; see source | 2 |
| additive_times_bidirectional_proximity_e541 | no | loci | numeric/dynamic; see source | 3 |
| additive_times_bidirectional_proximity_e542 | no | genes, loci | numeric/dynamic; see source | 5 |
| additive_times_cds_length_e445 | no | columns, genes | cds_length | 2 |
| additive_times_cds_length_e449 | no | columns, genes | cds_length | 1 |
| additive_times_cpg_oe_promoter_e455 | no | columns, genes | cpg_oe_promoter | 2 |
| additive_times_cpg_oe_promoter_squared_e473 | no | columns, genes | cpg_oe_promoter | 2 |
| additive_times_cpg_promoter_e325 | no | columns, genes | cpg_oe_promoter | 0 |
| additive_times_exon_count_e415 | no | columns, genes | n_exons | 1 |
| additive_times_gc_cds_e418 | no | columns, genes | gc_cds | 0 |
| additive_times_gene_span_e331 | no | genes | numeric/dynamic; see source | 1 |
| additive_times_gene_span_e347 | yes | columns, genes | gene_span_kb | 1 |
| additive_times_intron_length_e443 | no | columns, genes | intron_length_kb | 2 |
| additive_times_n_transcripts_e453 | no | columns, genes | n_transcripts | 2 |
| additive_times_promoter_cpg_e420 | no | columns, genes | cpg_oe_promoter | 0 |
| additive_times_target_cpg_promoter_e489 | no | columns, genes | cpg_oe_promoter | 2 |
| additive_times_target_exon_count_e548 | yes | columns, genes | n_exons | 2 |
| additive_times_target_gene_span_e401 | no | columns, genes | gene_span_kb | 2 |
| additive_times_target_hydrophobic_fracti_e679 | no | columns, genes | numeric/dynamic; see source | 3 |
| additive_times_target_promoter_cpg_e428 | no | columns, genes | cpg_oe_promoter | 2 |
| additive_times_target_promoter_cpg_e666 | yes | columns, genes | cpg_oe_promoter | 2 |
| additive_times_target_span_product_e545 | no | columns, genes | gene_span_kb | 2 |
| additive_times_target_transcript_length_e407 | no | columns, genes | transcript_length | 1 |
| additive_times_transcript_length_e310 | yes | columns, genes | transcript_length | 3 |
| additive_times_transcript_length_e316 | no | column_units, columns, genes | transcript_length | 3 |
| additive_times_utr3_length_e441 | no | columns, genes | utr3_length | 1 |
| additive_times_utr3_length_e451 | no | columns, genes | utr3_length | 2 |
| gene_annotation_ppi_random_projection_e721 | no | columns, genes | numeric/dynamic; see source | 5 |
| gene_annotation_random_projection_e697 | yes | columns, genes | numeric/dynamic; see source | 6 |
| screen_delta_over_transcript_length_e348 | no | columns, genes | transcript_length | 2 |
| screen_delta_times_bidirectional_flag_e464 | no | bidirectional | numeric/dynamic; see source | 4 |
| screen_delta_times_cds_length_e446 | no | columns, genes | cds_length | 2 |
| screen_delta_times_gc_cds_e452 | no | columns, genes | gc_cds | 2 |
| screen_delta_times_gc_promoter_e472 | no | columns, genes | gc_promoter | 2 |
| screen_delta_times_intron_length_e419 | no | columns, genes | intron_length_kb | 0 |
| screen_delta_times_intron_length_e444 | yes | genes | numeric/dynamic; see source | 5 |
| screen_delta_times_intron_length_e450 | no | columns, genes | intron_length_kb | 2 |
| screen_delta_times_n_exons_e454 | no | columns, genes | n_exons | 2 |
| screen_delta_times_target_exon_count_e490 | no | columns, genes | n_exons | 2 |
| screen_delta_times_target_gc_cds_e549 | no | columns, genes | gc_cds | 2 |
| screen_delta_times_target_gene_span_e488 | no | genes | numeric/dynamic; see source | 3 |
| screen_delta_times_target_gene_span_e667 | no | columns, genes | gene_span_kb | 2 |
| screen_delta_times_transcript_length_e324 | yes | columns, genes | transcript_length | 2 |
| screen_delta_times_utr5_length_e456 | no | columns, genes | utr5_length | 1 |
| screen_times_promoter_cpg_e366 | yes | columns, genes | cpg_oe_promoter | 0 |
| screen_times_promoter_cpg_e367 | no | columns, genes | cpg_oe_promoter | 2 |
| target_hydrophobic_fraction_e675 | no | columns, genes | aa_A, aa_F, aa_I, aa_L, aa_M, aa_V, aa_W, aa_Y | 1 |
| target_promoter_cpg_e406 | no | columns, genes | cpg_oe_promoter | 1 |
| target_promoter_cpg_times_additive_sq_e718 | no | columns, genes | cpg_oe_promoter | 4 |
| target_promoter_gc_e80_e81 | no | columns, genes | gc_promoter | 1 |

### Annotation plus Replogle

| Feature | Selected | Literal annotation fields | Literal annotation columns | Numeric subscript contexts |
|---|---|---|---|---:|
| pair_screen_delta_abs_diff_e361 | no | numeric/dynamic; see source | numeric/dynamic; see source | 6 |
| screen_delta_over_transcript_length_e416 | no | columns, genes | transcript_length | 0 |
| screen_delta_over_transcript_length_e546 | no | columns, genes | transcript_length | 1 |
| screen_delta_over_transcript_length_e547 | no | columns, genes | transcript_length | 2 |
| screen_delta_times_promoter_cpg_e377 | no | columns, genes | cpg_oe_promoter | 1 |
| screen_delta_times_target_gc_cds_e550 | no | columns, genes | gc_cds | 2 |
| screen_delta_times_target_promoter_cpg_e694 | no | columns, genes | cpg_oe_promoter | 2 |
| target_gene_span_times_screen_e717 | no | columns, genes | gene_span_kb | 1 |

## f_r2

Run: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r2`.

### Annotation without a literal Replogle read

| Feature | Selected | Literal annotation fields | Literal annotation columns | Numeric subscript contexts |
|---|---|---|---|---:|
| tf_binding_motif_score_e192 | no | loci | numeric/dynamic; see source | 8 |

### Annotation plus Replogle

| Feature | Selected | Literal annotation fields | Literal annotation columns | Numeric subscript contexts |
|---|---|---|---|---:|

## f_r3

Run: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3`.

### Annotation without a literal Replogle read

| Feature | Selected | Literal annotation fields | Literal annotation columns | Numeric subscript contexts |
|---|---|---|---|---:|
| additive_response_x_gene_span_e128 | no | columns, genes | gene_span_kb | 2 |
| additive_response_x_mean_target_gene_spa_e303 | no | columns, genes | gene_span_kb | 2 |
| additive_response_x_mean_target_span_e296 | no | columns, genes | gene_span_kb | 1 |
| additive_response_x_target_promoter_cpg_e412 | no | columns, genes | cpg_oe_promoter | 2 |
| additive_response_x_target_promoter_cpg_e509 | no | columns, genes | cpg_oe_promoter | 2 |
| bidirectional_partner_coexpression_with__e531 | no | bidirectional | numeric/dynamic; see source | 5 |
| cpg_oe_promoter_x_additive_e129 | no | columns, genes | cpg_oe_promoter | 1 |
| cpg_promoter_x_additive_response_e142 | no | columns, genes | cpg_oe_promoter | 2 |
| gene_annotation_random_projection_e567 | no | columns, genes | numeric/dynamic; see source | 3 |
| gene_span_x_additive_response_e143 | no | columns, genes | gene_span_kb | 2 |
| mean_target_promoter_gc_e295 | no | columns, genes | gc_promoter | 1 |
| mean_target_span_x_target_coexpression_e323 | no | columns, genes | gene_span_kb | 2 |
| promoter_similarity_target_g_e564 | no | columns, genes | gc_promoter, cpg_oe_promoter | 3 |
| replogle_additive_x_gene_promoter_cpg_e5_e540 | yes | columns, genes | cpg_oe_promoter | 2 |
| replogle_additive_x_intron_length_e448 | no | columns, genes | intron_length_kb | 2 |
| replogle_additive_x_mean_target_gene_spa_e337 | no | columns, genes | gene_span_kb | 2 |
| replogle_additive_x_mean_target_promoter_e301 | no | columns, genes | gc_promoter | 2 |
| replogle_additive_x_promoter_cpg_oe_e391 | no | columns, genes | cpg_oe_promoter | 1 |
| replogle_additive_x_promoter_gc_e300_e274 | yes | columns, genes | gc_promoter | 0 |
| replogle_additive_x_target_promoter_cpg_e528 | no | columns, genes | cpg_oe_promoter | 2 |
| replogle_additive_x_target_promoter_gc_e382 | no | columns, genes | gc_promoter | 2 |
| target_annotation_random_projection_e575 | no | columns, genes | numeric/dynamic; see source | 1 |
| target_chromatin_accessibility_e242 | no | columns, genes | gc_promoter | 1 |
| target_mean_cpg_oe_promoter_e402_e350 | no | columns, genes | cpg_oe_promoter | 1 |
| target_promoter_cpg_mean_e521 | yes | columns, genes | cpg_oe_promoter | 1 |
| target_promoter_cpg_x_gene_control_varia_e594 | no | genes | numeric/dynamic; see source | 2 |

### Annotation plus Replogle

| Feature | Selected | Literal annotation fields | Literal annotation columns | Numeric subscript contexts |
|---|---|---|---|---:|
| replogle_additive_x_mean_target_span_e31_e310 | no | columns, genes | gene_span_kb | 1 |
| replogle_additive_x_promoter_cpg_island_e507 | no | columns, genes | cpg_oe_promoter | 2 |
| replogle_additive_x_promoter_cpg_oe_e441 | no | columns, genes | cpg_oe_promoter | 1 |
| replogle_additive_x_target_promoter_cpg__e558 | no | columns, genes | cpg_oe_promoter | 2 |
| replogle_additive_x_target_promoter_cpg__e590 | no | columns, genes | cpg_oe_promoter | 2 |
| replogle_additive_x_target_promoter_cpg_e460 | yes | columns, genes | cpg_oe_promoter | 2 |
| replogle_additive_x_target_promoter_gc_e328 | no | columns, genes | gc_promoter | 1 |
