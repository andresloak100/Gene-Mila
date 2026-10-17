# DeepSeek worker validation, 2026-10-03

Run on Andres's Mac at commit `f4e3480`, Python 3.13. Claude Opus (claude CLI) was the
planner and DeepSeek the worker, on the synthetic dataset. 68/68 tests passed before the runs.

**Cost correction.** The API serves `deepseek-chat` requests with `deepseek-flash` and reports
that name. `deepseek-flash` was missing from the price table, so the runs priced it at the
pessimistic fallback ($3 in / $15 out per million tokens). The figures below are recomputed
from the recorded tokens at DeepSeek's published **peak** flash rates ($0.30 input, $0.006
cached input, $1.20 output per million). Off-peak is half of that. This is fixed in commit
`7787cb7`.

## 1. Did the 4 workers operate independently?

Yes. All 4 worker slots ran experiments, with up to 4 at the same time. Every LLM-written feature
has its own git worktree commit, and no experiment was touched by more than one worker.
W000 ran 4 experiments, W001 2, W002 2 and W003 3.

## 2–3. Experiments and outcomes

**One worker:** 11 experiments, all completed. The best was 0.7563 pearson_delta
(target co-expression), against a 0.6054 baseline; on the query-only set it scored 0.7718.

**Four workers:** 11 proposed, 11 completed, 0 failed, rejected or killed.

| id | worker | feature | score | Δ vs parent |
|---|---|---|---|---|
| EXP_0006 | W003 | prior_net_target_edge | 0.6613 | +0.0559 |
| EXP_0007 | W002 | prior_net_target_edge (replicate) | 0.6611 | +0.0557 |
| EXP_0008 | W000 | target_coexpr_corr | 0.7654 | +0.1600 |
| EXP_0009 | W001 | knn_pert_response | 0.6019 | −0.0035 |
| EXP_0010 | W000 | knn_pert_response (replicate) | 0.7134 | +0.1080 |
| EXP_0011 | W003 | module_pair_response (needed one fix call) | 0.6698 | +0.0644 |
| EXP_0012 | W003 | net_diffusion_signed | **0.7980** | +0.0326 |
| EXP_0013 | W001 | net_diffusion_signed (replicate) | 0.7980 | +0.0326 |
| EXP_0014 | W000 | partial_corr_target | 0.7655 | +0.0000 |
| EXP_0015 | W000 | target_knockdown_magnitude | 0.6390 | +0.0336 |
| EXP_0016 | W002 | linear_response_ko | 0.7610 | −0.0044 |

The best model, EXP_0012, scored 0.7980 against the 0.6054 baseline.

## 4. Tokens (DeepSeek)

| run | input | cached | output |
|---|---|---|---|
| check | 13 | 0 | 1 |
| 1 worker | 5,453 | 0 | 2,840 |
| 4 workers | 15,726 | 0 | 10,114 |

The planner (Claude Opus via the CLI) used 3,367 in / 1,590 out in the one-worker run and
6,768 in / 5,603 out in the four-worker run.

## 5. Total estimated cost

| | recorded (fallback price) | corrected (peak flash) |
|---|---|---|
| check | $0.00005 | $0.000005 |
| 1 worker | $0.0590 | $0.0050 |
| 4 workers | $0.1989 | $0.0169 |
| **DeepSeek total** | **$0.2579** | **≈ $0.022** (≈ $0.011 off-peak) |
| Claude planner (CLI-reported) | $0.225 | $0.225 |

## 6. Cost per completed experiment (4 workers)

About $0.0015 of DeepSeek per experiment at peak rates. The recorded figure was $0.018.

## 7. Throughput

9.1 completed experiments per minute with 4 workers, from a 1.2-minute run, so this is a noisy
figure.

## 8. Bottlenecks and duplicated work

* **The planner starved the workers.** Worker utilisation was 22%. One planner round took
  about 30 s, and workers sat idle until it returned. Both runs stopped early once
  `--max-planner-calls` was used up, so the deadline path was not exercised.
  **Fixed:** the planner now refills when fewer than 2× workers experiments are queued, and
  asks for 2× workers hypotheses per round (capped at 20).
* **No prompt-cache hits.** The task-specific text came first in the worker prompt.
  **Fixed:** the static API reference and example now come first, so repeated calls can be billed
  at the cache-hit rate ($0.006 instead of $0.30 per million).
* **Duplicated work.** EXP_0012 and EXP_0013 are identical (0.7980). EXP_0006 and EXP_0007 are
  nearly identical. EXP_0009 and EXP_0010 diverged widely (0.60 vs 0.71), which shows that
  replicates are worth having for some ideas but not others.
* CPU was not a bottleneck: 13 s in total. It has since dropped about 20× (warm fork server and
  feature cache).

## 9. Projected DeepSeek cost (corrected, peak rates)

These scale linearly from the measured spend per worker-minute at the measured 22% utilisation.
If the planner keeps workers fully busy, multiply by up to ~4.5. Off-peak hours halve them.

| workers | 1 hour | 6 hours |
|---|---|---|
| 8 | $1.68 | $10.08 |
| 16 | $3.36 | $20.17 |
| 44 | $9.24 | $55.45 |

The Claude Opus planner cost about $8/hour at the measured call rate. At 44 workers, one planner
call producing ≤20 hypotheses every ~30 s caps supply at about 40 experiments/minute.
**The planner, not CPU or DeepSeek, is what limits a 44-worker run.**

## 10. Commands (require explicit approval to scale)

The cumulative ledger currently records $0.2579 under the old pricing, which blocks further
DeepSeek runs at the $0.25 cap. First pull and reprice:

```bash
git pull
python reprice_ledger.py            # shows recorded vs corrected totals, changes nothing
python reprice_ledger.py --apply    # rewrites the ledger costs (backup kept)
```

Then:

```bash
python run_research.py --minutes 20 --workers 8  --budget 0.50 --set budget.cumulative_usd.deepseek=1.0
python run_research.py --minutes 20 --workers 16 --budget 1.00 --set budget.cumulative_usd.deepseek=2.0
python run_research.py --hours 1    --workers 44 --budget 10   --set budget.cumulative_usd.deepseek=12 \
    --set budget.cumulative_usd.deepseek=<approved total>   # the planner cap scales with workers and hours
python analyze_run.py               # after each run
```
