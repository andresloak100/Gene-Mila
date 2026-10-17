# Norman G independent audit addendum

Source/count/planner and reading-2 numerical audits: PASS. Static source caveats are recorded without changing any feature, score or criterion.

All mixed=false, exhausted_at_min=null, external knowledge=[]; no maximum reaches20000
Missing from all six permitted checks; never inferred from EXPIDs or plugin counts

- g1_r0/lof_weighted_target_response_similarity_e201: Constraint oe_lof_upper/case-sensitive pLI, missing weight=1. Weight normalization cancels constraint weighting with one usable target.
- g1_r2/target_bidirectional_count_e89: bidirectional field, otherwise adjacent-index/control-expression proxy; not a demonstrated bidirectional promoter count.
- g1_r2/target_neighbor_count_times_additive_e515: Expects neighbours field, otherwise correlation-degree proxy.
- g1_r2/target_expression_variance_mean_e585: Control-cell variance plus n_exons/transcript_length/gene_span_kb proxy; does not read a cell-type atlas.
- g1_r2/other direct fields: cpg_oe_promoter, oe_lof_upper, protein_length; public schema-name literals preserved in source-audit twins.
- g1_r3/promoter_cpg_overlap_with_target_e519: Reads loci[1] and cpg_oe_promoter; compares numeric TSS windows without chromosome-equality check; strand stored but unused.
- g1_r3/other direct fields: LOEUF/pLI constraint branches; protein_length and nucleus protein branches.

- Static direct literal calls, not exhaustive runtime/transitive attribution.
- Dynamic knowledge calls concern network names rather than the three exact tables.
- Literal dependency traversal found no additional table types, but coexpression_weighted_target_similarity_e160 chooses dependency via similarity_feature parameter; active nondefault params were not examined.
- Root companion preserves public schema-name literals and all raw key expressions; no new value-level or runtime branch validation.
- No new jobs, imports, scores, scientific changes or model decisions from this audit.

Exact counts and reviewer scope are in the JSON twin; source/key/hash/check evidence remains in source_audit/direct_table_audit twins.
