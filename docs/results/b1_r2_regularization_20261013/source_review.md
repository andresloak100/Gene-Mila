# Source and method review before real fitting

Reviewed 2026-10-14 01:52 UTC by the read-only model-hypothesis reviewer and root.
No real response arrays, previous candidate predictions, held-out labels or API calls were used.

No material issue found. The original r2 specification is deep-copied and only alpha changes.
Both r2 versions retain the members/1 plugin snapshot, original seed2, feature recipes, parameters,
expected columns, train-only scaling and historical train-then-whole-query-fold batch rule.
Shared r1 predictions feed both exact half-means. Each member is fit on a fresh full-hide context.

Synthetic tests cover the actual fit_outer route, including nonempty hide-minus-predict poisoning;
exact original/variant feature matrices and unmodified specification;45 fits; prefit config/source pins;
sample SD/ratios-of-means and all fixed gates; exclusive outputs; and timeout/failure checkpoints.

Existing base helper and core are unchanged. Base helper SHA256:
d25ce9f184f6bd3b5f6d268f753763ccf6196cb552d1c119457d593603339763.
No dependency on the rejected nested-blend runner. Parent launcher uses the original manifest pin,
exclusive directory and7200s subprocess deadline, preserving existing partial checkpoint/array bytes.

Focused result reported by implementer:8 passed in1.32s. Full repository suite:490 passed, no skips,8 dependency deprecation warnings in647.09s.
Source ownership handed to root; no source edits during the full suite.

## Limits preserved

Prior-edge e34/e401 whole-batch fallback, e14 kernel not guaranteed PSD, k20 neighbor behavior and
external-input ordering/measurement assumptions are unchanged. This alpha-only test cannot establish
or repair those issues. Same historical cohort remains development evidence, not a fresh test or
CellForge comparison. Passing does not alter delivered originalB1 or create a new frozen package.
