# Block D run records (18 October 2026)

Copies, unchanged, of what block D's chain wrote on the Mac (`~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_d/`
and `progress.md`) and of each run's `config.json`, `summary.json` and `summary.md`
(`~/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r{0,2,3}_discovery/`). The scripts that wrote them are
`docs/mac/block_d/` on PR #75 (sha256 `0c8fd12f…` cap, `5a76a846…` run, `18639548…` chain; byte-identical copies ran).
The readings are in [`docs/results/adamson_cf_d1_readings.md`](../../results/adamson_cf_d1_readings.md).

| File | What |
|---|---|
| `block_d_cap.txt` | the cap, written once: `70.23 60.232225 2026-10-18T17:53Z` (cap, ledger at the start, UTC) |
| `block_d_chain.log` | the chain's log: bundle check, "ok: all checks", each run's check, "block D finished: adamson_cf d1 seeds 0, 2, 3 passed" |
| `adamson_cf_d1_ds_w4_r{0,2,3}_discovery.check.txt` | each run's post-run check (code, planner, cost, discovery record, features reading each input, largest planner state) |
| `progress_lines.txt` | the block's lines of `progress.md` (cap, start, finish with ledger, passed) |
| `adamson_cf_d1_ds_w4_r{0,2,3}_discovery/` | each run's `config.json`, `summary.json`, `summary.md` |
