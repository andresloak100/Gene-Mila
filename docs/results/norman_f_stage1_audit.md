# Block F stage-1 audit

Evaluation source: `b6638c3450710c7dcc4579c0b0afd73611a7952b` (PR #44).
The amended stage-1 command and `block_f_readings.py select --k 20` both exited 0.
This audit used the completed stage-1 report, selection record, copied plugins and checksum manifest;
it made no new fit, selection or sealed reading.

| Run | Copied annotation plugins | Status-ok family rows | Unusable rows | Selected for stage 2 |
|---|---:|---:|---:|---:|
| r0 | 60 | 40 | 20 | 10 |
| r2 | 1 | 1 | 0 | 0 |
| r3 | 33 | 25 | 8 | 10 |
| Total | 94 | 66 | 28 | 20 |

Run directories:

- r0: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0`
- r2: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r2`
- r3: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3`

The helper records `m_total=66`, `k=20`, `null_reps=1319=20*66-1`.
Its ordering matches descending paired OOF gain / overlap-adjusted SE, with the prescribed name tie break.
All 20 selected files match the copied source bytes. All 94 manifest MD5/SHA256 values and stage-1
source SHA256 values match the unchanged copied files. No extra copied plugin is present.
The stage-1 protocol records a built-in parent, gene-grouped five-fold partitions, seeds 101/102/103,
OOF only and zero null replicates.

## Unusable rows reported by stage 1

| Run | Count | Status | Recorded reason |
|---|---:|---|---|
| r0 | 15 | error | `KeyError: 'replogle_delta_signed_e35'` |
| r0 | 2 | error | `KeyError: 'additive_response_squared_e242'` |
| r0 | 3 | smoke | `feature is constant across all rows (no information)` |
| r3 | 7 | error | `KeyError: 'replogle_additive_response_signed_e104'` |
| r3 | 1 | error | `KeyError: 'target_coexpression_e14'` |

The three constant rows are `pair_screen_delta_abs_diff_e361`,
`screen_delta_times_intron_length_e444` and `screen_delta_times_target_gc_cds_e550`.
The squared-additive missing-key rows are `additive_sq_times_promoter_cpg_e400` and
`target_promoter_cpg_times_additive_sq_e718`. The coexpression missing-key row is
`mean_target_span_x_target_coexpression_e323`.

These 28 rows are not in the amended status-ok family. They were not repaired, substituted or rerun.
A negative primary result cannot establish that the unassessed features add nothing.
The remaining 46 usable but untested rows enter the pooled correction at p=1 under the amendment.
Selection for stage 2 is a processing step, not evidence of a useful feature. No feature-level
finding is established by stage 1 alone; the null test, pooled correction and other fixed gates remain required.
