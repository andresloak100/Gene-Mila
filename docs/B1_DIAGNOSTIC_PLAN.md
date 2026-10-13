# Fixed B1 development diagnosis

Prospective plan, 13 October 2026. Claim [#26](https://github.com/andresloak100/Gene-Mila/issues/26),
branch `astra/b1-development-diagnosis`. Andres said “go” to diagnosing Claude's fixed B1 recipes
against the additive rule on public gene-hidden development folds. Publish this plan before fitting.

## Question

Where does the current B1 ensemble improve on the additive rule, and where do its errors concentrate?
The previous shrinkage and singleton-transfer experiments used small panels; neither diagnosed B1's
larger recipes. Claim #24 failed and its conditional Stage B remains closed. This is a separate,
baseline-only diagnosis: no singleton-transfer feature, hyperparameter search or model promotion.

## Fixed inputs and recipes

Use the verified frozen package read-only:

```
gene-mila-export/runs/norman_frozen_export_20261013/package
manifest SHA256: 225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45
```

The manifest pins all public inputs, three member snapshots, features, feature parameters, column
order, original seeds and alphas. Public training: 112 conditions (71 singles/41 pairs), 2,083 genes.
Only permitted public training responses, controls and existing public knowledge are used. No new
data, private response/split files, oracle queries, held-out selection or paid calls.

| Member | Selected experiment | Ridge alpha | Original seed |
|---|---|---:|---:|
| r1 | `norman_ds_from_n2_w4_r1:EXP_0681` | 20000 | 1 |
| r2 | `norman_ds_from_n2_w4_r2:EXP_0729` | 0.00198 | 2 |
| r3 | `norman_ds_from_n2_w4_r3:EXP_0519` | 300 | 3 |

These are refits of historically selected recipes. Their stored full-training predictions/coefficients
are not development-fold predictions. Do not score those stored arrays against training responses.

## Folds and fitting

Use unchanged `cv_folds_of` with gene grouping: **seeds 0, 1, 2; five outer folds**. Each view hides
the entire returned `hide` union, including every training condition involving a withheld gene;
its `predict` sets partition the public training conditions. A predicted pair retains zero or one
known singleton, not universally two unseen targets.

For each member/fold, load fresh snapshot plugin/module state and a fresh restricted training view.
Set its original NumPy seed, compute training-batch features first and then the entire predicted-fold
batch. Preserve this historical batch behavior. Verify feature/column order against the manifest;
use its exact parameters. No inherited label-dependent caches or shared disk cache. Do not use
`frozen._matrix`, which reopens the full training context. Previously reviewed snapshot source uses
the supplied restricted context; reuse that source audit unless a new gap appears.

Standardize columns by that member's permitted training rows only; a zero standard deviation becomes
one. Refit ridge at its original fixed alpha and predict deltas. **No inner CV, tuning, calibration,
extra features or member selection.** The B1 prediction is the equal average of all three members.
The analytic additive comparator is the existing unchanged `AdditiveResponse`, computed from the
same restricted view. It uses known singleton means and the existing mean-response fallback.

## Metrics and error map

For each seed pool all outer predictions across all 112 conditions, then score ensemble, all three
members and additive using the unchanged evaluator definitions: **Pearson delta, MSE, expression PCC,
expression R², top-20 MSE, top-20 expression PCC, top-20 R², top-20 Pearson delta, top-20 direction
accuracy**, plus predicted/true mean absolute delta ratio. Top-20 is largest absolute true
*development* delta per condition, not cell-derived DE or a matched CellForge panel.

Report all metrics as mean ± sample SD across the three seeds, and paired ensemble/member minus
additive differences using each seed's same conditions. Retain per-seed values and fold membership.
This SD measures partition sensitivity on one cohort, not biological replication or significance.
Historical B1 recipe selection also used this cohort: a refit does not erase that exposure.
Do not compare the resulting scores numerically with B1's historical held-out 0.723.

Define strata from metadata and each fold's permitted singleton availability **before scoring**:

- Singles and pairs.
- Singles/pairs with 0 or 1 known training singleton contributions. Report any unexpected category
  explicitly rather than changing the splits or discarding it.
- Existing `replogle2022_k562` target-profile coverage: all, partial or none. A profile is available
  when its record is valid, has positive `n_cells` if provided, and has at least three finite values
  among measured genes aligned to the bundle. This is raw-profile coverage; no norm or KRR gate,
  no claim of complete B1 feature coverage or perturbation exposure. Unannotated targets are unknown.

These strata overlap. Report membership/counts per seed and all recipes/metrics for each nonempty
group. If membership changes with folds, keep that visible; do not treat its aggregate as a fixed
independent population. Empty groups are absent/missing, not measured zero. Small groups are
descriptive and cannot justify a model decision. Do not filter any condition by its response/error.

The diagnostic produces an error map, **not a performance gate or automatic winner change**. Describe
consistent paired weaknesses with their SD/counts. Feature-coverage/error associations are descriptive,
not proof that missing profiles caused the errors. Use the result to propose one distinct hypothesis;
publish its own comparison and acceptance rule before any later model fitting. Do not expand or tune
this diagnostic after outcomes.

## Execution and verification

One free CPU process in the own clone; `PYTHONHASHSEED=0`, single-thread BLAS variables, niceness 19.
Exactly **45 ridge fits** maximum (3 seeds × 5 folds × 3 members); additive has no fit. **7,200-second
wall deadline**, checked by the runner and enforced by a parent launcher. No retries or extra seeds.
Create the run directory exclusively and write config/source/plan/input hashes before fitting.
Atomic summary/progress checkpoints preserve partial/failed/timed-out runs; incomplete results never
support a conclusion. Numeric predictions stay ignored locally. No concurrent lab/model experiment.

Before real outcomes: independent plan/source review and focused synthetic tests (full hidden-label
poisoning, batch/module freshness, original seeds/parameters, training-only scaling, equal average,
actual gene-fold partitions, metadata coverage/membership, exclusive output and error preservation).
Run full `nice -n 19 python -m pytest -q` before every code push; publish reviewed code before fits.
Secret-scan all publication files. Keep protected code/data, main checkout, STOP and ledger unchanged.

```
python docs/results/b1_development_diagnostic_20261013/run_with_deadline.py \
  --package <absolute frozen package path above> \
  --out runs/b1_development_diagnostic_20261013
```

Root owns plan/publication/results, HANDOFF section 1 and live Mac STATE. Implementation subagent owns
only the new runner/tests; independent reviewer is read-only. Archive all outcomes, config/progress,
exact command, source/input pins, SHA256/MD5 and a dated Mac-state snapshot on a draft PR for Claude.
Independently verify consequential metrics from the saved arrays and arithmetic from the summary.
No model change or useful-gain claim follows from implementation/tests alone.
