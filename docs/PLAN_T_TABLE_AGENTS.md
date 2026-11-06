# Plan T: fresh DeepSeek agent rows for our CellForge Table 1

Written 2026-11-03 by a Claude session on the Mac (claim [#111](https://github.com/andresloak100/Gene-Mila/issues/111)),
before any run of the block, on Andres's own words in that session: "Run a clean benchmark in our setting. For the
agents inside run deepseek for cheaper purpose", and, asked whether to reuse block G's runs or pay for a new block,
his choice "Run new paid block" (2026-11-03). A change after the first run is a dated note at the end, never an edit.

## What and why

`docs/results/cellforge_table1_ours/table.md` lays our models out in CellForge's Table 1 (Adamson and Norman; no
Srivatsan bundle exists). Its agent rows today are block G's runs (code `baa7dfd`). Block T gives the table fresh
agent rows on today's code, with block G0's design unchanged: the clean tier-1 bundles without the three tables
(`data/adamson_cf_clean`, `data/norman_clean`; same splits as `adamson_cf` and `norman`), DeepSeek planner
`deepseek-v4-pro`, four `deepseek-flash` workers, 20 minutes, fresh start, `--no-watchdog`, per-run caps
`budget.max_total_usd=1.0` and `budget.max_planner_usd=1.5`, the shared ledger, one run at a time, seeds 0, 2, 3.
G0 rather than G1 because the tables lowered the agents' score on Adamson in blocks G and H. Six runs:
`<CLONE>/runs/<ds>_t0_ds_w4_r<S>` in the operator's own clone `~/Documents/Mila/Gene-Mila/gene-mila-norman`, never
the main checkout. The code is a dedicated detached worktree at `T_COMMIT` = `d53edff` (the integration head; it
differs from `a2c4cb4` only in HANDOFF.md).

Block T is its own arm in every table (code `d53edff`), never pooled with G0 (code `baa7dfd`).

## Money

- Block G0's six runs cost $5.88 by the ledger ($0.45 to $1.27 each). Block T is expected to cost about $6.
- **Block cap:** the DeepSeek ledger (provider `deepseek`) may rise at most **$10** over its reading when the block
  starts: $66.731337 on 2026-11-03, so the cap is **$76.73**. The cap is written once, before the chain, into
  `~/Documents/Mila/Gene-Mila/genemila_t_logs/block_t_cap.txt`.
- Each run starts only when the ledger plus its two caps ($2.50) stays within the block cap. The block stops when a
  run fails, costs more than $2.00, or the ledger cannot be read.
- The key: each run gets `DEEPSEEK_API_KEY` from Andres's `~/.zshenv` (`API_KEY`) in its own process environment
  only (AGENTS.md). It is never printed, written or put on a command line.

## The Mac

GEARS's free Norman seeds (claim #111) are training on the CPU when the block starts. A paid run never runs beside
another job, so the operator pauses the GEARS process (SIGSTOP) for the whole block and resumes it (SIGCONT) after;
both times go into `progress.md` there and GEARS's receipts, because its wall time includes the pause. Its result
does not depend on wall time.

## Readings, fixed now

1. Each run's selected model scored once on the sealed tier by the run itself (as every run does), plus
   `docs/results/cellforge_table1_ours/score_selected.py` when the run did not store CellForge's metrics for it.
2. The table gains a row "Gene-Mila agents, DeepSeek, clean tier 1 (block T0, code d53edff)", mean ± sample sd over
   the three seeds, beside the G0 and G1 rows. Descriptive only: both sealed sets are worn, and no difference inside
   run-to-run noise is claimed.
