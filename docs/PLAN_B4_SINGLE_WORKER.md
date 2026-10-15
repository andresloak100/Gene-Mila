# Block B4: one worker against four (Norman), fixed before any run

Written 2026-10-15 on Andres's messages of 15 October ("we need to find a framework for the agent to build this
feature", "compare ... test our workflow is better", "run the deepseek agents if needed"). It is the first
comparison the paper proposal (`docs/PAPER_FRAMEWORK_PROPOSAL.md`, section 3) needs: does the multi-agent loop beat
a single-agent loop, autoresearch-style, given the same task, start, knowledge and wall time?

## Arms

- **B2 arm (exists, not rerun):** `runs/norman_ds_addstart_w4_r0`, `_r2`, `_r3`: DeepSeek planner deepseek-v4-pro,
  4 deepseek-flash workers, 20 minutes, fresh start from `baseline_ridge_additive`, Norman with the Replogle file,
  code ce1b530. Seed 1 is its own arm (killed while finishing) and is not used.
- **B4 arm (new):** the same with `--workers 1`, seeds 0, 2 and 3, run directories
  `runs/norman_ds_addstart_w1_r0`, `_r2`, `_r3`. Everything else identical: code ce1b530 (from the worktree
  `~/Documents/Mila/Gene-Mila/gene-mila-ce1b530`), bundle `data/norman` with `replogle2022_k562.json` md5
  d9eff528143dcd4d72c87393df724084, 20 minutes, no `--continue-from`, `--no-watchdog`, caps
  `budget.max_total_usd=1.0` and `budget.max_planner_usd=1.5`, shared ledger, `budget.cumulative_usd.deepseek=52`.

One worker at equal wall time also means about a quarter of the worker compute; that is the comparison the paper
cares about (same clock, same money ceiling), and it is stated as such.

## Money

Andres on 15 October: "run the deepseek agents if needed"; on 11 October: spend as needed from the $33 then left
in the DeepSeek account. The block's ledger cap is $52 (the ledger overstates real cost about twofold). A run starts
only when the ledger plus its two caps stays within $52, that is at a ledger of $49.50 or less. Expected cost about
$1 per run on the ledger. A run that fails, is killed, costs more than $2.00, or ends with `planner.mixed` true stops
the block; such a run is its own arm.

## Readings, fixed now, made only after all three B4 runs have ended

All with the tools at ce1b530 (the same tools that read B2), from the worktree, written to
`docs/results/norman_b4_*`:

1. Per run: `tools/sealed_reading.py --runs runs/norman_ds_addstart_w1_r<S>` (selected against start and additive).
2. **Primary:** `tools/arm_reading.py combine --members <the three w1 runs> --reference <B2's w4 runs r0 r2 r3>`:
   B4's combined model against B2's combined model on the sealed perturbations, paired.
3. Secondary: `tools/arm_reading.py rule --against start` and `--against additive` over B4's three readings;
   `combine` of B4 against `runs/norman_ds_addstart_w1_r0:start` and `:additive`.

Reading rule as for B1 and B2: a gain counts only when it exceeds twice its paired standard error and the better side
wins on more than half the perturbations; categories under 10 sealed perturbations are reported, not read. The
expected direction is not assumed: on Adamson, 4 workers beat 1 (`docs/results/scaling.md`); here either outcome is
reported. Nothing is chosen from a sealed score. The Norman sealed set has been read for B1 and B2 already, so this is
one more labelled look at a used set, not the paper's clean test (that waits on a fresh test held outside the
orchestration, `docs/FROZEN_TEST_PLAN.md`).
