# Norman G source/count/planner audit

Sources: each run directory below, its permitted .check.txt, selected names in the completed six-run OOF report, and unchanged plugin sources. No private, split, old sealed score or manual database read.

|run|plugin files|all-source mentions GA / GC / PA|selected mentions GA / GC / PA|largest planner state|cut reached|experiments|
|---|---:|---|---|---:|---|---|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r0|308|0/0/0|0/0/0|15102|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r2|318|0/0/0|0/0/0|14045|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r3|260|0/0/0|0/0/0|13907|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r0|258|18/26/13|0/1/0|15366|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r2|315|33/25/30|5/1/1|17111|False|not emitted by .check|
|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r3|274|29/29/26|1/3/2|16620|False|not emitted by .check|

GA=gene_annotation; GC=gene_constraint; PA=protein_annotation.

- Source mentions are static direct text matches, as in the prescribed grep/check; they do not measure runtime use or resolve transitive/dynamic dependencies.
- schema_column_literals are column-name strings present in source; numeric/dynamic indexing and flag/get/subscript expressions remain in key_accesses and the unchanged plugin sources. No guessed field mapping.
- Total experiment counts are absent from the permitted .check receipts and are reported missing.
- Every recorded planner is DeepSeek mixed=False, no exhaustion and empty external knowledge in the check receipts.

## g0_r0

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r0

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g0_r2

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r2

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g0_r3

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r3

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g1_r0

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r0

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|
|lof_weighted_target_response_similarity_e201|gene_constraint|gene_constraint: oe_lof_upper, pLI|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g1_r2

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r2

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|
|target_bidirectional_count_e89|gene_annotation|gene_annotation: |
|target_loeuf_times_additive_response_e104|gene_constraint|gene_constraint: oe_lof_upper|
|target_cpg_times_additive_response_e137|gene_annotation|gene_annotation: cpg_oe_promoter|
|target_protein_length_mean_e231|protein_annotation|protein_annotation: protein_length|
|target_weighted_cpg_promoter_e459|gene_annotation|gene_annotation: cpg_oe_promoter|
|target_neighbor_count_times_additive_e515|gene_annotation|gene_annotation: |
|target_expression_variance_mean_e585|gene_annotation|gene_annotation: gene_span_kb, n_exons, transcript_length|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.

## g1_r3

Run: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r3

|selected feature|tables mentioned|schema-column string literals|
|---|---|---|
|target_constraint_interaction_e91|gene_constraint|gene_constraint: oe_lof_upper, pLI|
|pair_target_constraint_interaction_e242|gene_constraint|gene_constraint: oe_lof_upper|
|pair_target_constraint_aggregate_e433|gene_constraint|gene_constraint: oe_lof_upper, pLI|
|additive_response_x_target_protein_lengt_e453|protein_annotation|protein_annotation: protein_length|
|promoter_cpg_overlap_with_target_e519|gene_annotation|gene_annotation: cpg_oe_promoter|
|additive_response_x_target_nuclear_e542|protein_annotation|protein_annotation: nucleus|

Exact static key expressions, source hashes and raw check receipt are in the JSON twin.
