# What the Mac produced

Andres's Mac is the only machine with the real data (AGENTS.md, "Andres's Mac"; paths in HANDOFF.md sections 2 to 6).
Everything here was copied from it byte for byte and is a record: the scripts that ran a block are never edited
(a change is a new file), run records are never rewritten. How to work on the Mac: `MAC_HANDOFF.md`, which arrives
with draft PR [#6](https://github.com/andresloak100/Gene-Mila/pull/6).

## Block scripts (the exact scripts that ran each block)

| Directory | Block | Files |
|---|---|---|
| `block_norman_n/` | Norman N3 and N4 ([`docs/NORMAN_PLAN.md`](../NORMAN_PLAN.md)) | `norman_n3.sh`, `norman_n4.sh` |
| `block_after_n4/` | B2 ([`docs/PLAN_AFTER_N4.md`](../PLAN_AFTER_N4.md)) | `block_b2_chain.sh`, `block_b2_run.sh`, `block_b2_control.sh`, `block_b2_resume.sh`, `block_b2_read.sh`; the B1 scripts and the `logs/` directory arrive with PRs #6 and #7 |
| `block_b4/` | B4 ([`docs/PLAN_B4_SINGLE_WORKER.md`](../PLAN_B4_SINGLE_WORKER.md)) | `norman_b4_chain.sh`, `norman_b4_run.sh` |
| `block_f/` | F ([`docs/PLAN_F_GENOME_ANNOTATION.md`](../PLAN_F_GENOME_ANNOTATION.md)) | `prepare_norman_ga.sh`, `norman_f_chain.sh`, `norman_f_run.sh`, and `gene_annotation_norman.json.gz`, the knowledge file the block used |
| `block_g/` | G, running ([`docs/PLAN_G_CLEAN_ARM.md`](../PLAN_G_CLEAN_ARM.md)) | `prepare_clean_bundles.sh`, `block_g_chain.sh`, `block_g_run.sh`; receipts `downloads.md`, `prepare_*.txt`, `archive_*.jsonl`. Nothing here changes while the chain runs |
| `block_h/` | H, not yet run ([`docs/PLAN_H_COMPARISON.md`](../PLAN_H_COMPARISON.md)) | `block_h_chain.sh`, `block_h_a2.sh`, `block_h_a3.sh`, `block_h_a4.sh`, `block_h_cap.sh`, `block_h_common.sh`, `block_h_probe.sh`, `check_tools.sh`, `Dockerfile` |

## Run records (`config.json`, `summary.json` and the analysis log of one run each)

Adamson controls with the external Replogle screen: `control_replogle_w4_r0/`, `control_replogle_from_opus_r0/`,
`control_replogle3_from_opus_r0/`. Norman N1 to N4: `norman_control_w4_r0/`, `norman_control_replogle_w4_r0/`,
`norman_ds_from_n2_w4_r0/`, `norman_ds_replogle_w4_r0/`. The B1 and B2 run records arrive with PRs #6 and #7.
Their readings are in [`docs/results/`](../results/README.md).

## Inputs the runs and tools read

| File | What it is | Used by |
|---|---|---|
| `adamson_cf_ncells.json` | cells behind each of the 90 Adamson target means | `tools/noise_ceiling.py --ncells` (`docs/results/noise_ceiling.md`), PREREG_G |
| `replogle_aliases.json` | 97 gene-symbol aliases joining the Replogle 2022 K562 screen to Adamson | `tools/build_external_screen.py` |
| `norman/norman_replogle_aliases.json` | 84 aliases for Norman (a different file; NORMAN_PLAN section 8, step 5) | `tools/build_external_screen.py` |
| `norman/external_replogle_norman_dryrun.txt` | the dry run of the Norman external-screen build | NORMAN_PLAN section 8 |
| `knowledge/gene_constraint_norman.json.gz` | gnomAD v2.1.1 constraint for 2,018 of Norman's 2,083 genes | `tools/build_gene_constraint.py`; block G's clean bundles |

## Upload checksums

`MD5SUMS.txt` (the 11 October upload, 68 lines) and `MD5SUMS_n4.txt` (the N4 upload, 10 lines) list paths as uploaded.
The `docs/mac/STATE.md` lines fail because the snapshot changed after the upload (`md5sum -c` on 17 October: 67 of
68 and 9 of 10 OK); the files moved on 17 October verify at the paths given in
[`docs/archive/README.md`](../archive/README.md). `MD5SUMS_b1.txt`, `MD5SUMS_b2.txt` and
`MD5SUMS_b2_verification_20261013.txt` arrive with PRs #6, #7 and #10.

Archived from here on 17 October (see [`docs/archive/README.md`](../archive/README.md)): the dated `STATE.md` snapshot
(14 October), `push_to_github.sh`, the as-run copies of four analysis scripts now in `tools/`, `external_stack_control.*`,
`feature_block_hashes.py` and a test log. Moved: `selection_replay.json` and `calibration_adamson_cf_val2.*` to
`docs/results/`, `cellforge_notes.md` to `docs/comparison/`. Deleted: three byte-identical copies of
`docs/results/norman_{splits,manifest}.json` and `norman_check.txt`, and a one-line checksum of a status copy.
