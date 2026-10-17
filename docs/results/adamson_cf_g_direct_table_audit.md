# Adamson G selected direct table calls

This companion distinguishes literal table mentions from actual static ctx.knowledge calls. Unchanged source hashes/key expressions are in the JSON and original source-audit twin.

|run|selected features|GA / GC / PA direct calls|planner chars|
|---|---:|---|---:|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r0|10|0/0/0|12541|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r2|23|0/0/0|14717|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r3|19|0/0/0|14826|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r0|23|3/5/3|16967|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r2|22|1/3/4|16834|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r3|22|1/2/0|16605|

- g1_r2 target_compartment_x_gene_annotation_e333 mentions gene_annotation only in its feature name; its direct knowledge call is protein_annotation. Raw mentions 2/3/4 therefore differ from direct calls 1/3/4.
- Counts exclude transitive/dynamic dependencies; no runtime use is inferred from static source.
- g1_r0 fields: oe_lof_upper; nucleus; full numeric annotation projections. full_annotation_projection_with_protein_e645 skips protein_length.
- g1_r2 fields: cpg_oe_promoter; oe_lof_upper; protein_length, has_signal_peptide, n_transmembrane, membrane, secreted and a compartment parameter.
- g1_r3 source uses promoter CpG/OE names with fallbacks; oe_lof_upper/pLI/flags. coessentiality_correlation_e725 names source=depmap but reads gnomAD/network proxies, not a DepMap input. Case-sensitive pLI availability was not validated; target_essentiality_score_e284 falls back to indices 0/1.
- Total experiments are not emitted by .check.txt; selected experiment IDs and plugin-file counts are not total experiments. All planner maxima are below 20000.
