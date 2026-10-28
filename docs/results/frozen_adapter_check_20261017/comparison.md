# Frozen adapter check: B1 Norman export, 17 October 2026

Export `/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-export/runs/norman_frozen_export_20261013` (package manifest sha256 `225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45`). Rule: members `np.array_equal`; ensemble within rtol = atol = 1e-6 (the verification driver's rule). Rows matched by condition id; gene order identical (asserted).

**Gate: PASSES.**

| run | mode | conditions | members bit-exact vs export saved | ensemble bit-exact vs export saved | members bit-exact vs original runs | ensemble max abs diff vs original runs (≤ 1e-6?) |
|---|---|---:|---|---|---|---|
| A | `predict-targets` | 31 (single-gene anchors (condition id == symbol)) | True | True | True | 1.49012e-08 (True) |
| B | `predict` | 88 (pair anchors, queries serialised as predict_targets() does) | True | True | True | 5.96046e-08 (True) |
| C | `predict` | 119 (all anchors, query bytes = the export's original query) | True | True | True | 5.96046e-08 (True) |

Per member, max abs difference (vs export saved / vs original run):

- A: EXP_0681 0 / 0; EXP_0729 0 / 0; EXP_0519 0 / 0; ensemble 0 / 1.49012e-08
- B: EXP_0681 0 / 0; EXP_0729 0 / 0; EXP_0519 0 / 0; ensemble 0 / 5.96046e-08
- C: EXP_0681 0 / 0; EXP_0729 0 / 0; EXP_0519 0 / 0; ensemble 0 / 5.96046e-08

| run | query_sha256 | predictions_sha256 |
|---|---|---|
| export (13 Oct) | `f0feecfb48fdd94e1cca134713770796de4ba5c4319b07ef859d719c009c3c78` | `5dc712660fa7cd60fc9c201bad8c12410055db47f28d016d9ec8af4d511b485f` |
| A | `6a705b5d7cb9c1f77be8004b9c4473078b18f06f0560a29c82c30d4a11eaa802` | `53051db2501e64f170fea8d98cd59c3676e982444eb5006aa69bf77559ed88b4` |
| B | `0a00456414ad0c6d8e1f5a262c00f0cfc1ab14fe7c98f618e9fee1d83aa204fb` | `8fc996020ecaa7e0d9177240cb0662cb0765707f75ebc557f4f255f3f175e0eb` |
| C | `f0feecfb48fdd94e1cca134713770796de4ba5c4319b07ef859d719c009c3c78` | `5dc712660fa7cd60fc9c201bad8c12410055db47f28d016d9ec8af4d511b485f` |

Run C's query bytes equal the export's (`query_sha256` equal: True); its `predictions_sha256` equals the export's: True (the predictions file is byte-identical to the export's).

Runs A and B have their own query bytes (a subset of the anchors, A's condition ids named by symbol), so their query_sha256 and predictions_sha256 differ from the export's by construction; their arrays are compared above.

Original saved member files: EXP_0681 sha256 matches the export's record: True; EXP_0729 sha256 matches the export's record: True; EXP_0519 sha256 matches the export's record: True

A and B reassembled in anchor order vs the export's saved arrays: members bit-exact True; ensemble bit-exact True.
