# Compact feature search

This policy adds an active curation lane to the master/worker laboratory. It is
opt-in through `configs/compact_search.toml`; the legacy default stays disabled.
Changing a file does not change a campaign already running on a pinned commit.

The requested Pearson target is 0.99. This implementation does not claim that
target, or any biological benchmark improvement, has been achieved. The relevant
metric is Pearson correlation of the expression change, averaged over
perturbations; a high correlation of absolute expression is a different metric.

## Work allocation

With eight workers, two prefer deterministic curation and six prefer discovery.
Each lane can take the other's work when its preferred queue is empty. The master
queues bounded rounds around a frozen parent even when the discovery queue is
busy. A round tests training-constant removal, Lasso/ElasticNet column screening,
and conditional single-module or small-block removals. These configuration
experiments need no implementation LLM call. Compute limits and the campaign
deadline still apply.

The master compares completed models using the actual fitted numeric column
count, not the number of source modules. It retains the raw accuracy champion
for audit, and selects the smallest candidate passing the configured visible
score guard and every visible constituent check. The default permits no
intentional score regression. Missing or conflicting protocol/count metadata
falls back to the raw champion. Final selection is frozen before final scoring;
held-out results cannot select a different model.

## Training and reproduction

Column screening standardizes only the current training rows and fits Lasso or
ElasticNet there, then refits ridge on the surviving columns. Every CV fold
learns its own screen. The full-training mask is never reused to score a fold.
Empty, nonfinite or unconverged selectors fail explicitly and enter the normal
failure records.

Artifacts record raw columns, selected columns and mask, normalization, selector
settings, per-fold supports and fitted models. Predictor modules and required
source dependencies are recorded separately. Selecting fewer columns does not
yet guarantee a proportional reduction in feature-computation time: whole
source modules may still be needed to produce retained columns. Duplicate
columns are not automatically merged; removing duplicate ridge inputs can
change the effective regularization and must be validated.

`requirements-compact-tested.txt` records the tested numerical/runtime versions
(Python 3.13.7). It pins the direct dependencies and numerical Python dependencies;
it does not claim to lock the operating system or optional cell-eval installation.

Follow-up proposals, penalty sweeps and warm starts preserve a parent's column
screen. Dependency-only parameter overrides remain attached to their sources.
The shared archive distinguishes execution identity from exact configuration
identity, deduplicates repeated prompt lessons, and summarizes failure classes
over its latest 1,000 records. It does not claim differently named programs are
scientifically equivalent or permanently blacklist a weak feature.

## Validation limits and release

Software tests use generated fixtures and stored synthetic metadata; no paid
campaign or biological query-only evaluation is required. Passing them establishes
queue fairness, leakage boundaries, reproducible predictions and conservative
selection behavior. It does not establish higher Pearson on the real task.

Public CV and visible validation remain adaptive search signals. A final model
needs a frozen comparison against the prior single winner; ensembles must be
reported separately. Do not recycle an already-inspected audit partition as a
fresh independent check. More independent perturbations, informative external
data and a well-defined noise/reproducibility ceiling may be necessary for a
large biological accuracy gain.

Use a new run directory, a fresh protocol-bound board and the committed source
revision for a subsequent authorized run. Preserve the existing duration and
spending constraints. To roll back this policy for a future run, set
`curation.enabled = false`; prior results and the raw winner remain available.
