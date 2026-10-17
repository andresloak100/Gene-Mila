# Norman G selected direct-table audit

Static source text and direct knowledge-call syntax are distinguished; this does not resolve transitive or dynamic runtime dependencies.

|source|selected total|selected direct GA / GC / PA|all-source raw GA / GC / PA|largest planner state|
|---|---:|---|---|---:|
|g0_r0|28|0/0/0|0/0/0|15102|
|g0_r2|18|0/0/0|0/0/0|14045|
|g0_r3|19|0/0/0|0/0/0|13907|
|g1_r0|11|0/1/0|18/26/13|15366|
|g1_r2|26|5/1/1|33/25/30|17111|
|g1_r3|17|1/3/2|29/29/26|16620|

GA=gene_annotation; GC=gene_constraint; PA=protein_annotation. Exact source hashes, direct calls, table/column literal evidence and raw key expressions are preserved in this JSON twin and source_audit twins.

- Counts separate raw table-name text from direct .knowledge calls with literal table arguments; names/comments alone are not direct calls
- Transitive dependencies and dynamically resolved arguments are not silently counted; raw source expressions preserved
- Column strings are literal intersection with public schema only, not inferred numeric/dynamic field mappings
- No import, compute, private/split/labels/DB or old sealed read
- Total experiments not emitted by prescribed .check receipts; never inferred from EXP IDs or plugin files
