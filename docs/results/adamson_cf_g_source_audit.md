# Adamson G source/count/planner audit

Sources: each run directory below, its permitted .check.txt, selected names in the completed six-run OOF report, and unchanged plugin sources. No private, split, old sealed score or manual database read.

|run|plugin files|all-source mentions GA / GC / PA|selected mentions GA / GC / PA|largest planner state|cut reached|experiments|
|---|---:|---|---|---:|---|---|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r0|99|0/0/0|0/0/0|12541|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r2|264|0/0/0|0/0/0|14717|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r3|249|0/0/0|0/0/0|14826|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r0|280|36/62/22|3/5/3|16967|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r2|282|30/33/37|2/3/4|16834|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r3|296|45/40/32|1/2/0|16605|False|not emitted by .check|

GA=gene_annotation; GC=gene_constraint; PA=protein_annotation.

- Source mentions are static direct text matches, as in the prescribed grep/check; they do not measure runtime use or resolve transitive/dynamic dependencies.
- schema_column_literals are column-name strings present in source; numeric/dynamic indexing and flag/get/subscript expressions remain in key_accesses and the unchanged plugin sources. No guessed field mapping.
- Total experiment counts are absent from the permitted .check receipts and are reported missing.
- Every recorded planner is DeepSeek mixed=False, no exhaustion and empty external knowledge in the check receipts.

## g0_r0

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r0

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g0_r2

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r2

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g0_r3

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r3

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g1_r0

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r0

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|
|essentiality_selfdelta_interaction_e234_e249|gene_constraint|gene_constraint: oe_lof_upper|
|essentiality_response_interaction_e329|gene_constraint|gene_constraint: oe_lof_upper|
|combined_annotation_projection_target_in_e398|gene_annotation, protein_annotation|gene_annotation: ; protein_annotation: |
|full_annotation_projection_target_e459|gene_annotation|gene_annotation: |
|nuclear_gene_x_loeuf_target_e467|gene_constraint, protein_annotation|gene_constraint: oe_lof_upper; protein_annotation: nucleus|
|gene_loeuf_x_target_selfdelta_e569|gene_constraint|gene_constraint: oe_lof_upper|
|target_loeuf_x_ppi_neighbor_response_e62_e628|gene_constraint|gene_constraint: oe_lof_upper|
|full_annotation_projection_with_protein_e645|gene_annotation, protein_annotation|gene_annotation: ; protein_annotation: protein_length|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g1_r2

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r2

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|
|protein_stability_proxy_e81|gene_constraint, protein_annotation|gene_constraint: oe_lof_upper; protein_annotation: has_signal_peptide, n_transmembrane, protein_length|
|target_has_signal_peptide_x_is_target_e247|protein_annotation|protein_annotation: has_signal_peptide|
|target_protein_length_x_gene_membrane_e2_e300|protein_annotation|protein_annotation: membrane, n_transmembrane, protein_length|
|target_cpg_promoter_x_gene_tf_indicator_e321|gene_annotation|gene_annotation: cpg_oe_promoter|
|target_compartment_x_gene_annotation_e333|gene_annotation, protein_annotation|gene_annotation: ; protein_annotation: cytoplasm, endoplasmic_reticulum, golgi, lysosome, membrane, mitochondrion, nucleus, peroxisome, secreted|
|target_loeuf_x_gene_loeuf_e380|gene_constraint|gene_constraint: oe_lof_upper|
|target_loeuf_x_gene_control_expression_e523|gene_constraint|gene_constraint: oe_lof_upper|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g1_r3

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r3

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|
|target_essentiality_score_e284|gene_constraint|gene_constraint: oe_lof_upper|
|target_promoter_cpg_island_e444|gene_annotation|gene_annotation: cpg_oe_promoter|
|coessentiality_correlation_e725|gene_constraint|gene_constraint: oe_lof_upper, pLI|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.
