# Missing-singleton transfer: fixed development comparison

Prospective protocol, 13 October 2026. Claim [#24](https://github.com/andresloak100/Gene-Mila/issues/24),
branch `astra/singleton-transfer-development`. Publish this document before any real fitting.
Andres asked for a model improvement building on Claude's work. This is one free CPU experiment;
evaluator-account setup is deferred, and no new API calls, downloads or lab-controller run are authorized.

## Hypothesis and permitted inputs

The additive rule uses the mean available singleton response when a target has no training singleton.
Test whether an existing external perturbation screen can predict that missing response. Preserve
available singleton responses exactly, transfer each missing target separately, and sum contributions.
This differs from the existing whole-condition external KRR feature. No claim is made that no discarded
historical plugin ever attempted a related idea.

Use only the public training/context snapshot of the verified B1 export:

```
gene-mila-export/runs/norman_frozen_export_20261013/package
manifest SHA256: 225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45
```

The manifest fixes all input files and all three B1 member recipes, feature parameters, sources,
alphas and seeds before outcomes. Its training cohort has 112 conditions and 2,083 output genes.
Read the public snapshot and existing `replogle2022_k562` knowledge only. Never read private labels,
split files, the query oracle or historical held-out scores for this experiment. Existing protected
split/evaluator/guard code, bundles and main checkout remain unchanged. STOP stays in place.

## Fixed prediction rules

Align external profiles by gene identifier and their measured mask. Ignore zero-cell, malformed or
unusable rows. Center finite measured values and normalize to unit norm, requiring at least three
finite shared genes and positive norm. Missing measurements become zero only in the normalized kernel
vector, after centering. Sort target identifiers before sums. KRR uses correlation geometry without
an activation/repression sign flip:

```
K = Z @ Z.T
prediction = mean_response + (Z @ query).T @ solve(K + I, Y - mean_response)
```

Penalty is **1.0**, fixed. No penalty search, blending coefficient, calibration or learned gate.

- **Ordinary external transfer:** sum a condition's target external rows before normalization;
  fit to all permitted training conditions with usable profiles. Center/fallback on the mean of all
  permitted training conditions. Require at least three usable condition rows.
- **Singleton transfer additive:** fit only to permitted singleton conditions, grouped by target
  (average duplicate singleton conditions). Center/fallback on the mean over original singleton
  condition rows, or all remaining conditions if no singles exist, or zero if none exist. For each
  query target, preserve the permitted singleton mean when known; otherwise KRR-transfer its profile
  using at least three usable singleton targets, falling back to that same mean when unavailable.
- **Direct external additive control:** preserve known singleton means; otherwise use the raw external
  response with the knowledge file's fixed sign (only +1 or -1 allowed; default +1). Fill unmeasured
  genes with the singleton fallback; missing/zero-cell rows use the whole fallback. No fitted transfer.
- **Singleton transfer correction:** transferred additive minus ordinary additive calculated on the
  same per-query permitted training view. This is one optional feature column, not a default change.

Every feature query excludes its own training response. A query that is itself a training singleton
also excludes every other singleton condition targeting the same gene before means/transfer fitting;
a new query for an actually observed target can use its permitted singleton mean. Pair responses never
enter the singleton transfer fit, except the declared no-singleton fallback. No global or disk caches
carry labels between views. Built-in additive and other existing control features stay unchanged.

## Folds, selection and metrics

Use unchanged `cv_folds_of` with target grouping: **three seeds 0, 1, 2; five outer folds**. Hide the
entire returned `hide` set, not just the `predict` set: all responses involving a withheld gene must
be unavailable. Predictions cover each training condition once per seed. A held pair can retain zero
or one known singleton. Do not describe every pair as having two unseen targets.

Stage A selects ridge alpha separately per arm on **three inner gene folds** inside the outer
training view. Inner seed is `1000 + 100 * outer_seed + outer_fold_index` (zero-based). Fixed grid:
**0.01, 1, 100, 10000, 1000000**. Maximize mean inner out-of-fold Pearson delta; smaller alpha wins an
exact tie. Recompute all label-dependent features, singleton/condition means, transfer fits and
training-only scaling in every inner/outer view. Never reuse a full-cohort learned feature matrix.
Train batch precedes evaluation batch. Standardize using training rows only; zero standard deviation
becomes one. Ridge uses the existing implementation and an intercept.

For each seed pool its outer predictions across all 112 conditions, then report unchanged evaluator
definitions for **Pearson delta, MSE, expression PCC, expression R², top-20 MSE, top-20 expression PCC,
top-20 R², top-20 Pearson delta, top-20 direction accuracy**, plus predicted/true mean absolute delta
ratio. Top-20 means largest absolute true *development* delta per condition, not the cell-derived DE
reference. Consequently this is not a matched CellForge evaluation. Report all metrics and paired
candidate-minus-control differences as mean ± sample SD over the three seeds. This SD measures
partition sensitivity on one cohort, not independent biological replication or a significance test.
Also report metadata-fixed singleton/pair strata, known/missing singleton contributions and fallback
coverage. Do not select conditions by outcomes or discard a seed.

## Stage A: matched component screen

Both arms have five scalar feature columns and the same training/selection procedure:

| Control | Candidate |
|---|---|
| Control mean | Control mean |
| Mean response | Mean response |
| Is target | Is target |
| Additive response | Singleton transfer additive |
| Ordinary external transfer | Ordinary external transfer |

Also score unchanged analytic additive, direct external additive and uncalibrated singleton transfer
additive as diagnostic controls. These controls do not determine the continuation gate.

Continue to Stage B **only if all** of these prospectively fixed conditions hold:

1. Every seed's paired candidate-minus-control Pearson-delta gain is positive.
2. Mean paired gain is greater than `max(0.002, sample SD of the three paired gains)`.
3. Across-seed mean candidate MSE is at most 1.01 times across-seed mean control MSE; the same bound
   holds for top-20 MSE. These are ratios of means, not means of ratios or per-fold thresholds.

This is a conservative development screening heuristic. A pass is not proof of generalization.
A failure ends this fixed experiment: preserve it; do not widen the grid or change the gate.

## Stage B: ablation on Claude's fixed B1 recipes

Run only after Stage A passes. On the **same fixed outer folds**, refit each original B1 recipe versus
the identical recipe plus exactly one `SingletonTransferCorrection` column. Member identities:

| Member | Selected experiment | Fixed ridge alpha |
|---|---|---:|
| r1 | `norman_ds_from_n2_w4_r1:EXP_0681` | 20000 |
| r2 | `norman_ds_from_n2_w4_r2:EXP_0729` | 0.00198 |
| r3 | `norman_ds_from_n2_w4_r3:EXP_0519` | 300 |

The pinned export manifest is authoritative for feature order, parameters, original model seeds and
source hashes. There is no Stage B tuning. Fresh plugin/module/context state per member and fold;
compute original training-batch features then the entire evaluation-fold batch. Both arms reuse the
same base matrices; each scales its own columns from training rows. This explicitly preserves
batch-sensitive historical plugin behavior. Do not call the frozen inference helper that reopens the
full training context, and do not compare held-fold truth with stored full-training B1 predictions.

Score individual members and their fixed equal-weight three-member average. Apply the same gate to
the **ensemble** candidate versus baseline. Stage B uses the Stage A cohort and folds; it is not
independent confirmation. Historical B1 feature selection used this cohort. Even a pass identifies
only a development candidate for future independent validation; no automatic delivered-model change,
new frozen package, fresh-test claim or CellForge superiority claim follows.

## Execution, checks and preservation

Before outcomes: independent methodology review; source review; focused synthetic tests; full
`nice -n 19 python -m pytest -q`; scan all publication files for secret-shaped strings; publish code.
Meaningful tests must poison outer hidden labels and preserve selected inner alpha/predictions, poison
inner hidden labels and preserve fixed-alpha predictions, check target-order/duplicate handling,
known-single preservation, fallbacks, gene alignment, no pair-label transfer and the exact gate.

One standalone CPU process, `PYTHONHASHSEED=0`, niceness 19, no API spending. Deadline **7,200 seconds**
for the full real experiment, checked during the loop and enforced by its driver. Maximum **480
Stage A ridge fits**, then **90 Stage B ridge fits** if eligible (no retries or extra seeds). Partial,
failed or timed-out outcomes are recorded and are not promoted. Do not run concurrently with a lab
controller or another real model experiment. Tests can run before it; no controller restart.

```
python tools/singleton_transfer_diagnostic.py \
  --package <absolute frozen package path above> \
  --manifest-sha256 225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45 \
  --out runs/singleton_transfer_development_20261013
```

Create the run directory exclusively, with config/input/source/plan hashes before any fit. Preserve
fold membership, selected alphas, feature coverage, every seed/metric, paired summaries and gate
components in `summary.json`; retain numeric predictions locally in ignored `runs/`. Publish only
data-free config/summaries/protocol/checksums and interpretation. Never overwrite a run. Root owns
shared HANDOFF section 1 and live Mac STATE, updated at start, milestones and completion. No useful
gain means no model promotion and no merge of unused experimental tooling.
