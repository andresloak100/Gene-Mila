# Missing-singleton transfer: negative development result

The fixed candidate **failed its primary screen**. Pearson delta was lower in all three fold seeds: candidate minus matched control **−0.003245 ± 0.001620** (sample SD). Stage B was automatically skipped. Claude’s delivered B1 model is unchanged; this experiment does not measure an effect on B1.

Claim [#24](https://github.com/andresloak100/Gene-Mila/issues/24), draft [PR #25](https://github.com/andresloak100/Gene-Mila/pull/25). The [prospective plan](SINGLETON_TRANSFER_PLAN.md) was published as `c8c1358`; reviewed code `7606c04` was published before fitting. One run completed, with no retries, extra seeds, grid changes or API calls. Do not merge this unused feature/tool into the lab merely because it was implemented. Preserve this branch and evidence for Claude.

## Comparison

Both ridge panels used five columns and included ordinary external transfer; the candidate replaced mean-fallback additive response with singleton-transfer additive response. Three outer gene-fold seeds (0/1/2), five folds each, nested three-fold alpha selection. Full gene hide sets and fresh features/scalers were applied at each level. All labels were permitted public training data: 112 conditions (71 singles, 41 pairs), 2,083 genes.

**These numbers are not comparable to B1’s historical held-out 0.723.** The panel, folds and training availability differ. Seed SD is sensitivity to partitions of one cohort, not biological replication or statistical significance. The top-20 panel uses absolute development delta, not the cell-derived DE reference. No matched CellForge result or fresh test claim follows.

## Primary results

| Metric | Matched control | Candidate | Paired candidate − control |
|---|---:|---:|---:|
| Pearson delta ↑ | 0.573512 ± 0.015021 | 0.570267 ± 0.013404 | -0.003245 ± 0.001620 |
| MSE ↓ | 0.008086 ± 0.000372 | 0.008132 ± 0.000304 | 0.000047 ± 0.000075 |
| Expression PCC ↑ | 0.982922 ± 0.000947 | 0.982846 ± 0.000826 | -0.000076 ± 0.000129 |
| Expression R² ↑ | 0.961668 ± 0.001914 | 0.961447 ± 0.001585 | -0.000221 ± 0.000366 |
| Top-20 MSE ↓ | 0.194277 ± 0.013439 | 0.193232 ± 0.012043 | -0.001046 ± 0.001435 |
| Top-20 expression PCC ↑ | 0.896357 ± 0.003321 | 0.896755 ± 0.002833 | 0.000398 ± 0.000500 |
| Top-20 R² ↑ | 0.696880 ± 0.013874 | 0.697797 ± 0.012061 | 0.000917 ± 0.001818 |
| Top-20 Pearson delta ↑ | 0.626103 ± 0.024506 | 0.626285 ± 0.023299 | 0.000182 ± 0.002530 |
| Top-20 direction accuracy ↑ | 0.819048 ± 0.016878 | 0.820833 ± 0.015115 | 0.001786 ± 0.002046 |
| Absolute-delta scale ratio | 0.685163 ± 0.009049 | 0.688718 ± 0.007608 | 0.003555 ± 0.001851 |

All entries are mean ± sample SD over the same three seeds. The small top-20 MSE improvement is smaller than its paired SD; do not present it as an established benefit.

| Seed | Control Pearson delta | Candidate Pearson delta | Paired gain |
|---:|---:|---:|---:|
| 0 | 0.559551 | 0.557740 | -0.001812 |
| 1 | 0.571579 | 0.568660 | -0.002920 |
| 2 | 0.589406 | 0.584403 | -0.005003 |

Fixed gate: positive gain in every seed **failed**; mean gain greater than max(0.002, paired SD) **failed** (threshold 0.002000). Ratio-of-across-seed-mean errors passed their ≤1.01 guards: MSE 1.005794, top-20 MSE 0.994618. Error guards alone cannot override the primary failure. Stage B: **0 fits, skipped**.

## Diagnostic controls

| Fixed analytic rule | Pearson delta ↑ | MSE ↓ | Top-20 MSE ↓ |
|---|---:|---:|---:|
| Original additive | 0.561398 ± 0.016064 | 0.008236 ± 0.000350 | 0.193711 ± 0.013308 |
| Direct signed external additive | 0.296014 ± 0.026842 | 0.012310 ± 0.000759 | 0.214362 ± 0.011342 |
| Uncalibrated singleton-transfer additive | 0.564112 ± 0.013258 | 0.008190 ± 0.000254 | 0.189538 ± 0.010199 |

These diagnostics were predeclared and do not decide continuation. All ten metrics for all five rules, every selected alpha and singleton/pair stratum are in the [complete summary](results/singleton_transfer_development_20261013/summary.json). Do not use a favorable diagnostic to reopen this failed screen.

## Feature coverage

| Seed | Known target contributions | Missing contributions | Transferred | Mean fallback: missing external profile | Pairs with zero / one known singleton |
|---:|---:|---:|---:|---:|---:|
| 0 | 30 | 123 | 108 | 15 | 11 / 30 |
| 1 | 28 | 125 | 103 | 22 | 13 / 28 |
| 2 | 38 | 115 | 97 | 18 | 3 / 38 |

Counts are contributions, not independent conditions. Each seed covers 153 named target contributions across 112 conditions. No scored contribution fell back for too few donors, unknown target annotation or an unusable profile. Existing missing external rows were kept in the comparison with the fixed fallback; nothing was excluded by its outcome.

## Reproduction and verification

Run directory: `/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-singleton-transfer/runs/singleton_transfer_development_20261013`. `summary.json` reports 57.771 seconds and 480 Stage A ridge fits. Numeric predictions remain in this ignored directory and are not committed. Source, plan and public input hashes were written before fitting.

The [archived parent launcher](results/singleton_transfer_development_20261013/run_with_deadline.py) enforces 7,200 seconds. Use the Python environment in the untouched main checkout with `PYTHONHASHSEED=0`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1` and niceness 19. See [execution receipt](results/singleton_transfer_development_20261013/execution.json) for the exact command. Never reuse this output directory or rerun the closed grid to chase its result.

- Full final-source suite: **529 passed**, no skips, eight dependency deprecation warnings, 653.50 seconds. Focused suite: **62 passed**, 2.19 seconds. An early full-suite attempt was stopped for the last checkpoint fix and is not counted as a pass.
- Independent methodology/source reviews covered full gene hiding, fresh label-dependent features, duplicate self-exclusion, member snapshots/batch behavior and deadline preservation; see the [review record](results/singleton_transfer_development_20261013/review.md).
- Independent NumPy arithmetic reproduced all **150 metric values** from the saved arrays with maximum absolute difference **8.882e−16**. Seed aggregation, input/source hashes, prediction order, fit counts and skipped Stage B passed; see [verification receipt](results/singleton_transfer_development_20261013/verification.json).
- Chat 2 independently verified all 90 aggregate/paired statistic pairs, fold/fit counts, inner alpha choices, coverage arithmetic, gate and progress history from data-free records; no discrepancies.
- Data-free config, full summary and progress log are copied byte-for-byte into this archive. SHA256 and MD5 lists cover the publication files; numeric-array hashes are in the execution/verification receipts. Secret-pattern scans precede publication.

## Exact handoff to Claude

This block is complete and negative. Keep delivered B1, the main checkout, protected code, existing data and STOP unchanged. Keep PR #25 as an unmerged research record. Do not run conditional Stage B, change lambda/alpha grid, discard a seed, restart B3 or spend API funds under this closed plan. No account setup was approved; that work remains deferred.

The next model experiment needs a distinct, prospectively specified hypothesis and a matched development control; this result supplies no supported replacement model. A fresh generalization claim still requires an eligible independent cohort and an evaluator boundary, but creating an account is not the current model-improvement task. Read the newest integration HANDOFF section 1 before claiming new work. Shared ledger remains $43.599822392 of its $48 cap; this experiment cost $0 in API usage.
