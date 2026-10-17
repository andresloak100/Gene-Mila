# One nested blend weight for B1 prediction error

Claim [#30](https://github.com/andresloak100/Gene-Mila/issues/30), own `astra/b1-nested-blend` / `gene-mila-nested-blend`.
Andres explicitly requested further model improvement on 13 October local (14 October UTC).
This is a distinct prospective development block. Preserve the completed Claim28 composition screen;
do not calculate this candidate on its seeds or change its acceptance rule.

## Hypothesis and fixed inputs

The fixed r1+r2 average has useful correlation but higher mean MSE/top-20 MSE than additive.
Test one error-calibration parameter, learned without any outer-fold response:

```
E = (r1_prediction + r2_prediction) / 2
C = A + lambda * (E - A)
lambda = clip(sum((E-A)*(Y-A)) / sum((E-A)**2), 0, 1)
```

`A` is analytic additive, `Y` is permitted OUTER-TRAINING truth, and the arrays used to learn lambda
are INNER out-of-fold predictions. If the denominator is exactly zero, set lambda=0. No intercept,
new feature, optimizer, alpha search, weight grid, or separate r1/r2 weighting. One global scalar per
outer fold, shared across its conditions and genes. Fit by pooled all-gene MSE, with equal weight per
condition/gene; no top-20 labels, correlation or outer outcomes choose the weight.

Use the unchanged read-only B1 export:

```
gene-mila-export/runs/norman_frozen_export_20261013/package
manifest SHA256: 225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45
r1 index0 / EXP_0681 / ridge alpha20000 / original model seed1
r2 index1 / EXP_0729 / ridge alpha0.00198 / original model seed2
```

Original snapshot features/parameters/column order unchanged; r3 is not fit or blended. The package
retains its original three members and all file pins, but only indices0/1 participate. Numeric saved
full-training coefficients are not used in development refits; delivered B1 remains unchanged.

## Nested gene folds and fitting

- Outer seeds **6,7,8**, five unchanged `cv_folds_of` gene folds per seed, on the 112 public-training
  conditions / 2,083 genes. These are new partitions of the same historically used cohort.
- For each outer fold, construct the complete outer-hide restricted view before any inner operation.
  Inner folds: **three**, seed `1000 + 100*outer_seed + outer_fold_index`, constructed ONLY among that
  outer view's permitted training conditions. Preserve exact memberships in config before fitting.
- Every inner fit uses the union of outer and inner hide sets, fresh feature context/modules/cache,
  original model seed reset before training features, training-first batch then whole inner predicted
  fold batch, and training-only scaling. Inner predictions partition the outer-training order once.
- Generate inner r1/r2/additive delta arrays. Learn lambda using only these inner OOF arrays and the
  outer view's permitted training responses; freeze it before predicting/scoring the outer fold.
- Refit r1/r2 once on the outer restricted view at their original alphas. Share these exact outer
  arrays between fixed E and candidate C; additive uses the same permitted outer view.
- Exactly **120 member fits**: 2members*(3inner + 1outer)*15outerfolds. No inner alpha selection,
  retries or extra member/subset fits. Budget/parent wall deadline **7200 seconds**.

Reusing the same cohort and historically selected feature recipes limits inference. Nested calibration
prevents outer-response tuning within this block; it cannot undo historical feature/partition selection
or create independent test evidence. Features' prescribed batch behavior remains part of the recipe.

## Metrics, controls and fixed advancement screen

Save candidate, fixed E, additive and both original members. Same ten metrics and metadata strata as
`B1_DIAGNOSTIC_PLAN.md`: full/top-20 errors, correlation, R2, direction and delta scale. Top-20 is
largest absolute development delta, not cell-derived DE or a matched CellForge comparison. Use full
outer-hide metadata for known-singleton/external-coverage groups; no response-defined eligibility.
Report every seed/arm/stratum and paired mean +/- sample SD across seeds6/7/8. These SDs measure
same-cohort partition sensitivity, not independent replication. Small/overlapping groups are descriptive.

All of these gates must pass:

1. Fixed E minus candidate all-gene MSE is positive in every seed, and its mean is greater than its
   sample SD. This is the primary error-improvement reading.
2. Ratio of across-seed mean candidate MSE to mean additive MSE <= **1.01**; likewise for top-20 MSE.
   Candidate mean top-20 MSE / fixed E mean top-20 MSE must also be <= **1.01**.
3. Candidate minus fixed E Pearson delta is >= **-0.01** in every seed and >= **-0.002** on average.

Ratios of means, never means of ratios. Practical screening margins, not significance/noninferiority
claims. Being within1% of additive is not beating it. Preserve all unfavorable metrics and contextual
member readings; do not select another subset from them. Failure closes this block; no changed gates,
extra seeds, alternative weight objective or feature corrections after results. A pass nominates an
error-calibrated candidate for independent validation; no automatic new frozen package/promotion.

## Execution and evidence

Root owns plan/reports/Git/shared HANDOFF/live Mac STATE and requested documentation. Implementation
subagent owns only new `tools/b1_nested_blend.py` and focused tests. Independent reviewer read-only.
Existing helper/core/protected code remains byte-identical. No old-run array reuse or prior-seed candidate
scores; no held-out/oracle/private/split reads, new data, account/permissions/main/STOP changes or paid calls.

Publish this plan before outcomes and reviewed source before fitting. Required synthetic checks:
outer-hidden response poisoning leaves weights/predictions unchanged; inner-hidden response poisoning
leaves that inner fold's predictions unchanged (may legitimately alter the learned weight via inner
scoring truth); all hide unions and condition order; original seeds/params/batch/scaling; closed-form
weight/clipping/zero denominator; shared outer arrays/exact120 fits; gate boundaries; exclusive output,
checkpoint/failure preservation and parent timeout. Full `nice -n19 python -m pytest -q` before code push.

One mainvenv process in the own clone, niceness19, PYTHONHASHSEED0, single-thread BLAS, parent7200s:

```
python docs/results/b1_nested_blend_20261013/run_with_deadline.py \
  --package <absolute pinned B1 package> --out runs/b1_nested_blend_20261013
```

The exclusive run directory retains config/source/input/plan/runtime hashes before fits, every inner/outer
membership, all15 weights/numerators/denominators/objectives, inner and outer numeric predictions,
checkpoints, full summary/progress, status/error/deadline and exact command. Numeric arrays/package/context
stay ignored locally. Independently recompute lambda from saved inner arrays and allowed outer-training
responses, all metrics/strata/gates and hashes. Chat2 can verify data-free arithmetic/counts separately.
Secret-scan before publication; archive data-free config/summary/progress/reviews/receipts with verified
SHA256/MD5 lists. Keep live state and exact Claude continuation current, including failures. Merge only
reviewed useful changes under Andres's standing bounded merge instruction; delivered original B1 and
fresh-test account/cohort work remain unchanged/deferred.
