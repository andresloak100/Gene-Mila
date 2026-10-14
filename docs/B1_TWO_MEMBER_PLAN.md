# Fixed two-member B1 comparison

Prospective follow-up to [Claim #26](https://github.com/andresloak100/Gene-Mila/issues/26),
Claim [#28](https://github.com/andresloak100/Gene-Mila/issues/28), `astra/b1-two-member-test`.
Andres's “go” accepted diagnosis followed by one targeted change. Publish before any candidate score.

## Rationale and limits

The diagnosis on partition seeds0/1/2 found r1/r2 much stronger than r3 under fixed gene-hidden refits.
Source review found r3 batch-dependent fallback and training/inference proxy mismatch concerns, but
did not establish their causal role. Test one small composition change: remove r3's contribution.
Do not screen other subsets, optimize weights, modify features or evaluate this candidate on the
diagnosis seeds. Preserve their existing results. This is a separate prospective model comparison.

Seeds3/4/5 create new partitions of the **same cohort**, after this subset was chosen. They are
development robustness checks, not independent confirmation or an untouched test. Original B1
recipes were historically selected using this cohort. A pass does not establish better performance
of new full-training coefficients or a drop in the original frozen B1's historical held-out score.
No CellForge superiority or automatic delivered-model change follows.

## Fixed inputs and arms

Use the same read-only B1 package:

```
gene-mila-export/runs/norman_frozen_export_20261013/package
manifest SHA256: 225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45
```

Exactly the original three feature recipes, parameters, column order, alphas and model seeds:
r1 `EXP_0681` alpha20000 seed1; r2 `EXP_0729` alpha0.00198 seed2;
r3 `EXP_0519` alpha300 seed3. No source or parameter changes.

- Control: mean of r1+r2+r3 predicted delta arrays, weights1/3 each.
- Candidate: mean of r1+r2 predicted delta arrays, weights0.5/0.5/0.
- Context: each member and the unchanged analytic additive rule.

Average **prediction arrays**, not member metric values. Both arms reuse identical member refits;
no extra candidate training. User-approved source/runner from PR #27 is the dependency, unchanged.

## Fits, metrics and acceptance

Fixed gene-fold seeds **3,4,5**, five folds each, unchanged full `cv_folds_of` hide union. Fresh
restricted context and snapshot modules per member/fold; original seed reset before training
features; training batch then whole predicted-fold batch; training-only scaling. No inner CV.
Exactly **45 ridge fits** maximum. Protected split/evaluator/guard code remains unchanged.

Use the same ten metrics and metadata strata as [B1_DIAGNOSTIC_PLAN.md](B1_DIAGNOSTIC_PLAN.md).
Top-20 is absolute development delta, not cell-derived DE. Every seed/global/member/stratum reading
and paired difference is retained. Report mean ± sample SD over the three same-cohort partitions.
Small/overlapping/changing strata remain descriptive. Additive is context, not a substitute control.
In particular r2's diagnosis had variable MSE: good correlation alone is insufficient.

Candidate passes this fixed development screen only if **all** conditions hold:

1. Candidate minus control Pearson delta is positive in every seed.
2. Mean paired gain is greater than `max(0.002, sample SD of paired gains)`.
3. Across-seed mean candidate MSE is ≤1.01 times across-seed mean control MSE; the same bound
   holds for top-20 MSE. These are ratios of means, not means of ratios.

This is a screening heuristic, not a significance test. A failure closes the comparison; no additional
subsets/weights/seeds or altered criterion. A pass identifies a simpler candidate for independent
validation. Record whether it also improves on additive; do not claim that from improvement over
the fragile refitted control. Preserve the delivered original B1 while a new test is unverified.

## Execution and evidence

The thin wrapper temporarily configures the reviewed diagnostic for seeds3/4/5, restoring its globals
afterward. Config/source/plan/input hashes, candidate weights, metrics and gate are written before
any fit. Original diagnostic arrays/summary remain intact; candidate arrays and comparison summary
are separate artifacts. A dated run directory is exclusive; failures are preserved. No paid calls,
downloads, new knowledge, private/split files, oracle or permissions changes.

One own-clone process, mainvenv, niceness19, `PYTHONHASHSEED=0`, single-thread BLAS, **7200s parent
deadline**. Focused composition/gate/global-restoration/provenance tests, source review and full
pytest before code push; publish reviewed source before fitting. Secret-scan publication files.

```
python docs/results/b1_two_member_test_20261013/run_with_deadline.py \
  --package <absolute pinned B1 package path> \
  --out runs/b1_two_member_test_20261013
```

Root owns plan/report/Git/shared HANDOFF/live Mac STATE. Implementation subagent owns wrapper/tests;
independent reviewer is read-only. Preserve all outcomes, exact command, original and candidate array
hashes, config, summaries, progress, reviews and SHA256/MD5 on a draft PR into the lab branch. PR #27
is its diagnostic dependency; no protected/main/data/STOP/ledger changes. Keep Claude's next step exact.
