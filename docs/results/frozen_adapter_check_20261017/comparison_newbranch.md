# Frozen adapter check, EXTRA diagnostic: the new-condition branch (not part of the gate)

Run D: the 31 single-gene anchors under renamed ids `<SYMBOL>__new` (same targets), so `predict_ensemble` freezes the 119 anchors and computes each condition in its own feature batch, the branch a new cohort target takes. Compared with the export's saved anchor predictions and with run A (the anchor branch). Export manifest sha256 `225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45`.

Members bit-exact vs the export's saved predictions: **True**; ensemble bit-exact: **True**; everything within rtol = atol = 1e-6: **True**.

| array | vs export saved: bit-exact | max abs diff | values differing | over 1e-6 rule | vs run A: bit-exact | max abs diff |
|---|---|---:|---:|---:|---|---:|
| EXP_0681 | True | 0 | 0 | 0 | True | 0 |
| EXP_0729 | True | 0 | 0 | 0 | True | 0 |
| EXP_0519 | True | 0 | 0 | 0 | True | 0 |
| ensemble | True | 0 | 0 | 0 | True | 0 |

Largest per-condition member difference vs the export: BPGM 0, CDKN1C 0, CEBPB 0, ETS2 0, FOSB 0

Receipt: query_sha256 `ce35250ca71330be19ad9ff10162119dc3fdf5a20d5036e5847571e65e637706` (equals the queries file: True); predictions_sha256 `f3b00d12ad534f284f418699b570bd0f72934c60373748bbf454d7bc3f102db7` (equals the predictions.npz beside it: True). The predictions.npz is not committed (`.gitignore`).
