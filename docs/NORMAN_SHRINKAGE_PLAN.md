# Norman development-only shrinkage diagnostic

Prospective protocol, 2026-10-13, claim #15. This file is fixed before any real diagnostic
outcome. The task is a free CPU check of a magnitude-shrinkage hypothesis, using public
training responses only. It does not change the delivered B1 ensemble or query any existing
validation or sealed set.

## Question and scope

Does restricting a ridge penalty, or calibrating the size of its predicted changes using
training-only out-of-fold responses, improve a small additive model's development errors
without sacrificing its response pattern? The earlier Norman report raised shrinkage as a
hypothesis; its used sealed scores do not establish a cause. The negative Adamson DE-aware
selection experiment (`docs/results/selection_replay.md`) and compact-model audit
(`docs/results/compact_model_curve.md`, `docs/LAB_STATE.md`) remain negative evidence. This
check uses nested development folds and a scalar calibration, rather than reopening agent
search, feature pruning, or the old selection-rule comparison.

The feature set is fixed to the four built-ins, in this order: `control_mean`,
`mean_response`, `is_target`, `additive_response`. No agent plugins, external screens,
finished-run model choices, or feature searches are imported. This is a diagnostic of the
additive-ridge family; it cannot establish that B1's many-feature ensemble is shrunk or
that calibrating that ensemble would help.

## Four fixed recipes

1. `additive`: the existing `additive_delta` rule computed from each outer training view.
2. `ridge`: ridge with intercept; alpha selected on inner out-of-fold mean Pearson delta
   from `[0.01, 1, 100, 10000, 1000000]`.
3. `ridge_low_penalty`: the same rule and features, selecting from `[0.01, 1, 100]`.
4. `ridge_calibrated`: the selected `ridge` multiplied by one training-only scalar.
   For its selected-alpha inner out-of-fold deltas P and inner truths D,
   `s = sum(P * D) / sum(P * P)`, clipped to `[0, 4]`. Zero denominator uses s=1.
   There is no intercept, no scored-outer-fold calibration and no scale-grid search.
   Positive uniform scaling preserves Pearson delta (except a zero scale), so
   magnitude/error metrics carry this check; Pearson gain is not its expected mechanism.
   Alpha and scalar share the inner predictions: those predictions are fitting data,
   not a reported independent calibration result. The outer fold is their evaluation.

Alpha ties choose the smaller alpha. Training feature columns are standardized using only
that fit's training mean/std; zero std becomes one. Every training row's own response is
excluded by the built-ins. All feature blocks are recomputed from the restricted context
for each inner/outer fit, without disk or full-training feature caches.

## Folds, metrics and interpretation

Three fixed outer fold seeds, `[0, 1, 2]`, each use five gene-grouped folds through unchanged
`genemila.pipeline.cv_folds_of`. An outer context hides the function's whole `hide` set,
including perturbations that share a fold's held-out target gene. For each outer context,
three inner gene-grouped folds use seed `1000 + 100 * outer_seed + outer_fold_index`.
Each inner context hides its own whole gene-overlap set. A scored perturbation is predicted
once per outer seed. Empty/too-small training views stop with an error; no alternate seed
or split is tried.

Primary metric is mean per-perturbation Pearson delta. Also report mean-expression MSE,
PCC and R² on all genes and on the top 20 genes ranked by absolute true change, top-20
Pearson delta, top-20 direction accuracy and predicted/true mean absolute delta ratio.
These metrics reuse unchanged `evaluate` and `comparable.cellforge`. The top-20 definition
uses development pseudobulk changes, not private cell-derived DE references or a claim of
CellForge comparability. No DE classification metric is possible without an independent
cell-derived reference, so none is invented.

Each recipe's metric is the mean ± sample SD over the three outer-seed evaluations. These
reuse the same training cohort, so the SD measures fold sensitivity, not independent
biological replication or standard error. Paired differences against additive and against
ridge are also summarized as mean ± sample SD over seeds. All four recipes and all seeds
are reported. No significance verdict, winner promotion, exploration-budget change or
fresh-test claim follows from this exploratory diagnostic. A consistent development
benefit would motivate a separately fixed next protocol, not another query on the used
sealed set. A null result closes this small recipe comparison without enlarging its grid.

## Execution and continuation

`tools/shrinkage_diagnostic.py` opens only `public.npz`, `knowledge/targets.json` and
`manifest.json` in the specified public bundle. It has no lab, provider, evaluator-private
loader or oracle object. It does not read `splits.json`, validation labels, reference
bundles, historical summaries or prediction archives. It writes a new exclusive output
directory containing `config.json` before fitting, then `summary.json`; on failure it
preserves `config.json` and a bounded error marker. Existing directories are refused.
The config records the protocol and source hashes, input fingerprints, public train/gene
order fingerprints, versions and exact fixed recipe. Outputs contain development metrics,
fold memberships and chosen training-only parameters, with no response arrays.

Run only after code/methodology review, from the own clone, with no other lab run active:

```sh
nice -n 19 /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python \
  tools/shrinkage_diagnostic.py \
  --public /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/norman \
  --out runs/norman_development_shrinkage_20261013
```

The command is free and uses no API credential. It fits at most 255 four-column ridge
models: 3 seeds × 5 outer folds × (3 inner folds × 5 alphas + 2 final alphas). Inner
matrices are computed once per fold; the lower-penalty/calibration recipes reuse the broad
inner grid and final fits. Budget and model family are fixed before results. Run outputs
stay out of Git; publish the complete non-secret config/summary byte-for-byte under a new
`docs/results/` snapshot with hashes, run directory and an interpretation of every recipe.
Keep claim #15, HANDOFF section 1 and Mac STATE current. Leave the main checkout and all
historical artifacts untouched. This plan grants no paid run or protected-code change.
