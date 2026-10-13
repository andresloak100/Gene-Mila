# B1 frozen export: saved predictions reproduced

The frozen inference adapter reproduced all three preselected B1 members **bit for bit** from their
original public context and fitted numeric parameters. Their equal ensemble passed the comparison
predeclared before execution (`rtol = 1e-6`, `atol = 1e-6`); its maximum absolute difference from the
saved members' float64 mean cast to float32 was **5.960464477539063e-08**. The ensemble is not bit
identical. No tolerance was changed after viewing a result.

This is a reproducibility check, with no fitting, selection, scoring, oracle query, test-label access or
new model-performance claim. It does not provide a fresh untouched test or establish a gain over
CellForge. The complete old evaluation batch includes all original nontraining condition IDs; only
public target metadata and prediction arrays were used, without opening their response labels.

## Evidence and frozen identities

Executed exactly once in the coordinator's own clone at commit
`1ec08e64204cc3fcb7fa4602ca0308d64b3b72a2`:

`/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-export/runs/norman_frozen_export_20261013`

The run's configuration was written at 2026-10-13 19:43:07 UTC before model export/computation. Prediction
reproduction ran from 19:43:07 to 19:44:06 UTC, **59.0087165 seconds**, covering **119 conditions × 2083
genes**. Condition, gene and member ordering matches exactly. The archived [config](config.json),
[summary](summary.json), [package manifest](manifest.json), and [prediction receipt](prediction_receipt.json)
are byte copies of the run's data-free metadata. The local package, public training-context copy and
prediction arrays are not published.

| Original run under `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/` | Frozen experiment | Alpha | Full fitted-grid index | Maximum absolute difference | Array equal |
|---|---|---:|---:|---:|---|
| `runs/norman_ds_from_n2_w4_r1` | `EXP_0681` | 20000 | 0 | 0 | Yes |
| `runs/norman_ds_from_n2_w4_r2` | `EXP_0729` | 0.00198 | 1 | 0 | Yes |
| `runs/norman_ds_from_n2_w4_r3` | `EXP_0519` | 300 | 4 | 0 | Yes |

The original pickles retain all fitted alpha-grid estimators. Saved prediction files are pruned to
selected alphas. Matching the frozen alpha to the full grid correctly used indices **0, 1, 4** rather
than taking estimator zero for each member. All three weights remain exactly the declared `1/3`.
Each member has zero differing values; the ensemble has zero values exceeding its predeclared tolerance.
Its mean absolute difference is `7.64988671630699e-12`, consistent with the two float32 averaging paths.
These are numerical reproduction differences, not scientific uncertainty or repeated-run performance.

A second agent independently reread the original saved and reproduced prediction arrays, checked their
order and source hashes, and recomputed the comparisons without rerunning inference. The
[independent verification](independent_verification.json) confirms three exact members and the same
ensemble maximum difference. All recorded run-file hashes, helper/config pins and archive-copy hashes
were verified. No original run, main checkout, data bundle, protected evaluator, split, coordination log
or STOP file was edited by this reproduction.

## Pins, runtime and core compatibility

| Pin | SHA256 |
|---|---|
| Source B1 frozen receipt, PR #13 | `f0b2424676b559f9140c656bd8264649fb405144abf3f1c89115277de76341b9` |
| Immutable verification driver | `a1c171df06c1dfa0f8448786be6da583404fc86f5580da44d982d5560cff5d91` |
| Export manifest | `225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45` |
| Original evaluation anchor identity | `2fca0b8c206cb310ea956c97f6f114e513e4ddf7f9f0bab2858bac8929dd8ec5` |
| Reproduced prediction arrays, local only | `5dc712660fa7cd60fc9c201bad8c12410055db47f28d016d9ec8af4d511b485f` |
| Reviewed training-core diff | `a7267e73f6bea54c16de23d63f7fd2a78564f413d34a9adc7950dbb77910fdaf` |

The recorded runtime is **CPython 3.13.7**, **NumPy 2.5.3**, **SciPy 1.18.1**, **scikit-learn 1.9.1**,
with **`PYTHONHASHSEED=0`**. Source hashes cover `frozen.py`, `pipeline.py`, the feature package initializer,
feature API, builtins and registry. Prediction requires those same hashes and runtime settings.
This identifies the used runtime; it is not a complete OS/BLAS environment lock. Reproduction elsewhere
must preserve the receipt and repeat the fixed numerical checks, without relaxing the tolerance.

Training commit was `076282c71b7c54fef47674b8797fda736eff6f01`. The archived
[core compatibility diff](training_core_compatibility.diff) adds the later additive helper/feature to
the end of the builtin file and the pair-feature registry constants. The feature API, pipeline and
empty feature initializer are byte identical to training; the three original builtin formulas remain
an unchanged source prefix. Core bytes are therefore not wholly identical. The driver pins the reviewed
diff and recorded both old/current source hashes; actual prediction equality validates this B1 recipe
under the stated runtime.

Before publication, the repository full suite passed **464 tests** while the code and driver were frozen,
with **eight dependency
deprecation warnings**, no skips, in **652.70 seconds**. The focused frozen-adapter suite passed
27 synthetic cases, including multiple weighted members, training-phase memo priming, batch-dependent
features, exact full-grid alpha resolution and input/hash/order/nonfinite rejection. No source or test
code changed after that full-suite check; the following edits only archive verification evidence.

## Batch semantics and remaining work

The r3 selected plugin `pair_shared_ppi_neighbor_replogle_mean_e492.py` uses an all-batch-zero fallback.
The adapter consequently preserves the original ordered evaluation conditions as anchors. Each fresh
context first computes the original training feature batch to prime module/context memo as the original
pipeline did. Saved conditions are then computed in the original full evaluation batch. For a new
condition, the prospective recipe is original anchors plus that one condition, with each new condition
computed independently of other submitted queries. The manifest pins this recipe and anchor identity.

This check validates original-condition reproduction. The anchor-plus-new-condition recipe still needs
prospective acceptance in a compatible external-cohort protocol; this run did not infer or score an
external cohort. New targets must fit the frozen gene universe, and external-study controls/normalization
must be fixed without replacing the original training context or changing feature formulas after outcomes.

Next agents should review the adapter/result PR and [export instructions](../../FROZEN_EXPORT.md), verify
these pins and use a new own-clone run directory if replay is necessary. The existing run is immutable.
The separate cohort eligibility audit belongs to [claim #18](https://github.com/andresloak100/Gene-Mila/issues/18);
do not duplicate it. A suitable untouched cohort and a separate evaluator account/host with demonstrated
orchestration access denial remain pending. Exported trusted Python feature execution under one OS user
is not that security boundary. No new paid block, data acquisition, permissions change, protected-code
change or merge is authorized by this reproduction.
