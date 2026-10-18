# Frozen adapter check on the B1 Norman export, 17 October 2026

The gate of [`docs/PLAN_R_FRESH_TEST.md`](../../PLAN_R_FRESH_TEST.md) section 6: the adapter reproduces an arm's
saved predictions bit for bit on its own conditions. Run on Andres's Mac by the lab-code owner's Mac session (claim
[#68](https://github.com/andresloak100/Gene-Mila/issues/68)), free, `nice -n 19`, from the clone `gene-mila-macchecks`
at `cfa8034`. Inputs were the export of 13 October ([`../norman_frozen_export_20261013/`](../norman_frozen_export_20261013/report.md)),
read-only, at
`/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-export/runs/norman_frozen_export_20261013`.
No label, score, fitting or selection was involved; only predictions were compared.

**Verdict: the gate passes.** All 119 original evaluation conditions were reproduced. Every member array is bit-exact
(`np.array_equal`) against both the export's saved predictions and the original runs' saved arrays. The ensemble is
bit-exact against the export's saved ensemble and within 5.96e-08 of the float64 mean of the original runs' saved
members cast to float32 (the verification driver's reading; against the uncast float64 mean the largest difference is
7.95e-08), under the export's rule of rtol = atol = 1e-6 (the export's `summary.json` records the same 5.960464477539063e-08).
The full replay's query and predictions files are byte-identical to the export's.

## Identity and runtime

- Package `…/norman_frozen_export_20261013/package`, `manifest.json` sha256
  `225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45`, equal to the export receipt's `manifest_sha256`
  and the summary's.
- The clone's `genemila.frozen.runtime_receipt()` ([`runtime_receipt_clone.json`](runtime_receipt_clone.json)) equals
  the package manifest's `runtime` block: CPython 3.13.7, NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1,
  `PYTHONHASHSEED=0`, and the six pinned source hashes. Those six files are unchanged since `1ec08e6`.
  `load_export` checks this receipt before any prediction.
- Members EXP_0681 (alpha 20000), EXP_0729 (0.00198) and EXP_0519 (300), weight 1/3 each. 119 anchor conditions × 2,083
  genes.

## The runs ([`docs/mac/mac_checks_20261017/adapter_check.sh`](../../mac/mac_checks_20261017/adapter_check.sh); log [`adapter_runs.log`](adapter_runs.log))

The inputs come from the package's metadata only ([`adapter_build_queries.py`](../../mac/mac_checks_20261017/adapter_build_queries.py)):
`manifest.json`'s `anchor_perts` and `context/knowledge/targets.json`, as `verification_driver.py` builds them. Of the
119 anchors, 31 are single-gene and 88 are pairs. `predict-targets` takes one symbol per condition and cannot express
a pair.

| Run | Mode | Conditions | Query | Time |
|---|---|---|---|---:|
| A | `tools/frozen_model.py predict-targets --target SYMBOL …` | the 31 single-gene anchors, in anchor order ([`inputs/single_targets.txt`](inputs/single_targets.txt)) | written by `predict_targets()`: [`predict_targets_out/queries.json`](predict_targets_out/queries.json) | 94 s |
| B | `tools/frozen_model.py predict --queries` | the 88 pair anchors | [`inputs/pairs_queries.json`](inputs/pairs_queries.json), serialised exactly as `predict_targets()` serialises | 100 s |
| C | `tools/frozen_model.py predict --queries` | all 119 anchors, in anchor order | [`inputs/all_anchors_queries.json`](inputs/all_anchors_queries.json), byte-identical to the export's `original_target_only_queries.json` | 79 s |

Each output directory is new, inside this clone, outside the package and run roots. Each receipt is committed
(`predict_*_out/receipt.json`); the `predictions.npz` files are not (`.gitignore` here), and their sha256 are below.

## Comparison ([`comparison.json`](comparison.json), [`comparison.md`](comparison.md); script [`adapter_compare.py`](../../mac/mac_checks_20261017/adapter_compare.py))

Rows were matched by condition id, and the gene and member orders were asserted identical. There are two references:
the export's saved predictions (`reproduced/predictions.npz`, sha256 `5dc71266…`), and the original runs' saved member
predictions at the frozen alpha (`runs/norman_ds_from_n2_w4_r{1,2,3}/artifacts/<EXP>/predictions.npz` in the main
checkout, each sha256 equal to the export's record).

| Run | Members vs export (max abs diff) | Ensemble vs export | Members vs original runs | Ensemble vs the original members' float64 mean cast to float32 |
|---|---|---|---|---|
| A (31) | 0, 0, 0 (bit-exact) | 0 (bit-exact) | 0, 0, 0 (bit-exact) | 1.49e-08 (≤ 1e-6) |
| B (88) | 0, 0, 0 (bit-exact) | 0 (bit-exact) | 0, 0, 0 (bit-exact) | 5.96e-08 (≤ 1e-6) |
| C (119) | 0, 0, 0 (bit-exact) | 0 (bit-exact) | 0, 0, 0 (bit-exact) | 5.96e-08 (≤ 1e-6) |

A and B, reassembled in anchor order, equal the export's saved member and ensemble arrays bit for bit. No value
exceeds the tolerance anywhere.

| | query_sha256 | predictions_sha256 |
|---|---|---|
| export, 13 October | `f0feecfb48fdd94e1cca134713770796de4ba5c4319b07ef859d719c009c3c78` | `5dc712660fa7cd60fc9c201bad8c12410055db47f28d016d9ec8af4d511b485f` |
| A, `predict-targets` | `6a705b5d7cb9c1f77be8004b9c4473078b18f06f0560a29c82c30d4a11eaa802` | `53051db2501e64f170fea8d98cd59c3676e982444eb5006aa69bf77559ed88b4` |
| B, pairs | `0a00456414ad0c6d8e1f5a262c00f0cfc1ab14fe7c98f618e9fee1d83aa204fb` | `8fc996020ecaa7e0d9177240cb0662cb0765707f75ebc557f4f255f3f175e0eb` |
| C, full replay | `f0feecfb48fdd94e1cca134713770796de4ba5c4319b07ef859d719c009c3c78` (equal) | `5dc712660fa7cd60fc9c201bad8c12410055db47f28d016d9ec8af4d511b485f` (equal) |

A's and B's queries name a subset of the anchors, so their hashes differ from the export's by construction. In every
run, the `predictions_sha256` in the receipt equals the sha256 of the `predictions.npz` beside it. A's `queries.json`
hash equals its receipt's `query_sha256`.

## What the gate does and does not cover

Every single-gene anchor's condition id is its own symbol (BPGM, CDKN1C, …). So `predict-targets --target BPGM` names
an original anchor, and `predict_ensemble` serves it from the original evaluation batch (its anchor branch). Run A
therefore verifies the `predict-targets` wrapper, its query serialisation and receipt, the strict query checks, the
runtime pin and the package's integrity. It does not exercise the branch a new cohort target takes: the original
anchors plus that one condition, computed per member in a fresh feature batch. The 13 October report says that
branch "still needs prospective acceptance". The extra diagnostic below exercises it on known answers.

## Extra diagnostic: the new-condition branch (not part of the gate)

Run D ([`adapter_newbranch.sh`](../../mac/mac_checks_20261017/adapter_newbranch.sh)) asks `predict` for the 31
single-gene anchors again, under renamed ids `<SYMBOL>__new` with the same targets
([`inputs/newbranch_queries.json`](inputs/newbranch_queries.json), written by
[`adapter_newbranch_queries.py`](../../mac/mac_checks_20261017/adapter_newbranch_queries.py)). So `predict_ensemble`
freezes the 119 anchors and computes each condition in its own feature batch, once per member: 93 feature builds
against run A's 3. The answers are known (the saved anchor rows), so any difference measures the branch itself.
[`adapter_compare_newbranch.py`](../../mac/mac_checks_20261017/adapter_compare_newbranch.py) compares it with the
export's saved predictions and with run A, and writes `comparison_newbranch.json` and `comparison_newbranch.md` here.

**Status at this commit: running.** Run D started at 02:42:16 UTC (python pid 7513) and had not finished at
03:15 UTC. A duplicate launch at 02:55:14 UTC was stopped before it wrote any output, but it overwrote the header of
[`adapter_newbranch.log`](adapter_newbranch.log)
([`adapter_newbranch_processes.txt`](../../mac/mac_checks_20261017/adapter_newbranch_processes.txt)). The result
follows in a later commit on this branch. The gate's verdict above does not depend on it.
