# Frozen linear export and target-only inference

Claim [#14](https://github.com/andresloak100/Gene-Mila/issues/14). This adapter exports explicitly frozen
fitted models and computes predictions without calling model fitting, alpha selection, cross-validation,
the lab controller or any evaluator. It is a preparation step for the separate test protocol in
[PR #13](https://github.com/andresloak100/Gene-Mila/pull/13). No model gain or new test score follows from
exporting a model. No new response labels are accepted by the prediction command.

## Frozen identities and original context

The delivered B1 ensemble remains the equal average of these preselected models:

| Original run directory under the Mac main checkout | Experiment | Frozen alpha | Full model-grid index |
|---|---|---:|---:|
| `runs/norman_ds_from_n2_w4_r1` | `EXP_0681` | 20000 | 0 |
| `runs/norman_ds_from_n2_w4_r2` | `EXP_0729` | 0.00198 | 1 |
| `runs/norman_ds_from_n2_w4_r3` | `EXP_0519` | 300 | 4 |

`models.pkl` retains the full alpha grid even when `predictions.npz` contains only the selected alpha.
Export resolves the explicitly supplied alpha against the full `run_spec.json` grid and checks the
estimator's class, alpha and feature count. It never reads a summary, selects a winner, or uses the
pruned prediction index to select an estimator. The original model/scaling arrays are copied into
numeric `numeric.npz` files; prediction never deserializes an estimator.

The pinned model receipt comes from PR #13's
`docs/results/norman_b1_frozen_test_review_20261013.json`. It supplies immutable run, experiment,
alpha, member-weight, model-source, plugin-source and public-context hashes. The receipt may contain
historical results for the human audit; export projects only the identity/provenance fields into the
package and excludes those scores. Verify the source receipt SHA256 independently before using it.

The package preserves original gene, context perturbation, training perturbation and feature-column
order, all original public training means/control cells and all original public knowledge JSON files.
The optional public `train_ncells` count array is allowed. Unexpected NPZ arrays are refused. Members
must share the same public context. Plugin files are the complete pinned original snapshot, including
dependencies; omitted or added source/knowledge files are refused. Caches remain in fresh memory only,
separate for every member and feature batch. Existing run caches and historical outputs are untouched.

The anchor hash explicitly covers original evaluation identities/target order, gene order and public NPZ
and target-source hashes. Core feature/pipeline implementation hashes (including the feature package initializer),
Python, the `PYTHONHASHSEED` environment setting and NumPy/SciPy/scikit-learn versions are recorded
in the package. Prediction requires those same source bytes and versions. This is a runtime identity
receipt, not a complete environment lock: OS/BLAS differences can still cause floating-point changes.
The manifest records declared training commits alongside the current runtime, with an explicit outstanding
audit requirement. Confirm core feature compatibility with the recorded training commit and reproduce saved
predictions before accepting an export for scientific use. For B1 training commit `076282c71b7c54fef47674b8797fda736eff6f01`,
the coordinator's source comparison found unchanged API/pipeline code and three original builtin formulas;
later code adds the additive helper/feature and registry constants. The coordinator archives that exact
comparison and actual reproduction results in the PR rather than claiming all core bytes are identical.

## Batch-dependent features: the explicit prospective recipe

Some saved feature formulas depend on the perturbations computed together. Specifically, the selected
r3 plugin `feature_store/pair_shared_ppi_neighbor_replogle_mean_e492.py`, lines 92–96, adds the original
control mean to the entire output when **all rows of its feature batch are zero**. Calling it on an
arbitrary subset can therefore differ from the original pipeline's full evaluation batch.

The manifest records the following fixed inference recipe:

1. Original evaluation conditions are recomputed together in their original order, using exactly the
   original target metadata and public context. First compute the original training feature batch to
   prime module/context memo exactly as `pipeline.run()` did, without fitting. Requested original rows
   are then retrieved from the original full evaluation batch. This is the saved-prediction reproduction path.
2. Every new condition is computed in a separate feature batch containing the complete original
   evaluation conditions as anchors followed by that one new condition. Its metadata is appended to
   the original context; original context metadata is never replaced. Each batch reloads plugin modules,
   creates a fresh context and primes original training features before evaluation.
3. Only that new condition's prediction is emitted from its batch. Other submitted new conditions
   cannot influence its result. Submission order controls output order alone.

This recipe freezes the adapter's behavior for a future cohort. It does not prove B1's compatibility
with an external cohort, or convert the saved model into a condition-independent formula. The cohort
protocol must prospectively accept the anchor recipe before any outcome is inspected. No original
feature formula is edited. Feature computation may use its existing training-only SVD/kernel solves;
the fitted top-level linear estimator, training context, hyperparameters and feature recipe remain frozen.

## Commands in an own clone

Use the existing Mac venv with the code in your own clone/worktree. Store model packages and predictions
under a new nontracked location; never commit model arrays, public training data, response data or run
artifacts. Output directories must be absent and outside the original run and package roots; both commands
refuse overwrite and publish complete outputs atomically. No API provider or credential is involved.

```sh
PYTHONHASHSEED=0 nice -n 19 /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python tools/frozen_model.py export \
  --receipt /absolute/path/to/norman_b1_frozen_test_review_20261013.json \
  --receipt-sha256 <independently-verified-receipt-sha256> \
  --member EXP_0681=20000 --member EXP_0729=0.00198 --member EXP_0519=300 \
  --trust-archived-pickle --out /absolute/path/to/new/frozen_b1_package
```

Export prints its manifest SHA256. Pin that value externally; a hash listed inside a modified package
cannot authenticate itself. The trust flag acknowledges that historical pickles and feature Python
execute code. Hash verification establishes identity, not safety, so only archived trusted sources
may be exported. Prediction verifies every package file and refuses changed source/context/runtime,
gene order, computed feature order, invalid scales and nonfinite numeric predictions.

The strict query JSON contains identities and target genes only:

```json
{
  "schema_version": 1,
  "queries": [
    {"condition_id": "external-guide-condition-1", "target_genes": ["GENE_A", "GENE_B"]}
  ]
}
```

Query targets must be distinct and within the frozen gene universe. Condition IDs must be distinct,
outside the original training set, and must not change an existing condition's targets or their order.
Outcome/efficacy/control-expression fields and any other fields are rejected. Empty-target controls
are not model queries; control handling belongs in the prospective evaluator protocol.

```sh
PYTHONHASHSEED=0 nice -n 19 /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python tools/frozen_model.py predict \
  --package /absolute/path/to/frozen_b1_package \
  --manifest-sha256 <externally-pinned-manifest-sha256> \
  --queries /absolute/path/to/target_only_queries.json \
  --out /absolute/path/to/new/predictions
```

`predictions.npz` contains mean delta, each member's delta, condition IDs, gene IDs and member IDs.
Predictions use the original public context/control scale; introducing external controls/preprocessing
requires a fixed evaluator protocol and must not silently modify frozen features. `receipt.json` records
manifest/query/prediction hashes, identities, alphas, weights, runtime and anchor recipe. It contains no
new score. The prediction side reads no oracle, response file or split file and creates no query instance.

## Acceptance and exact next step

The synthetic regression suite covers the wrong-alpha indexing failure, exact original-batch reproduction,
no fitting, numeric/source/context/runtime tampering, gene/column order, missing knowledge, nonfinite
parameters/predictions, strict query input, and batch/order independence under a deliberately batch-dependent
feature, training-phase memo priming and multiple weighted members with distinct same-name plugin sources.
Run it with `python -m pytest -q tests/test_frozen_model.py`; the implementation passed
27 cases before coordinator validation. Full-suite and actual artifact validation results are recorded in the claim/PR and HANDOFF.

Before any external inference, independently review the adapter and source pins, then export B1 and
reproduce the three members' saved evaluation predictions from public inputs alone. Use target-only IDs
from the saved prediction artifact; compare predictions without any label/score access. Preserve an
immutable numeric receipt, original and reproduced prediction hashes, tolerances, maximum absolute
differences and runtime. A mismatch blocks use; investigate implementation/runtime without selecting a
different model. Neither this reproduction nor the export is a fresh test.

The data-free [verification driver](results/norman_frozen_export_20261013/verification_driver.py)
fixes this reproduction batch, source receipt pin and **rtol = atol = 1e-6** before execution. It derives
the code worktree from its own archived location and requires an explicit receipt path. Run only after
the full suite passes and any other lab/diagnostic computation has finished:

```sh
PYTHONHASHSEED=0 nice -n 19 /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python \
  docs/results/norman_frozen_export_20261013/verification_driver.py \
  --receipt /absolute/path/to/norman_b1_frozen_test_review_20261013.json \
  --out runs/norman_frozen_export_20261013
```

That output must be a new directory strictly under this own clone's ignored `runs/`; it may not use the
Mac coordination log directory, an original source run or any data bundle. The driver writes `config.json`
before computation, then `summary.json` with success/failure, exact alpha indices, order checks, member
and ensemble differences, source/prediction/runtime hashes and the reviewed core source diff. Archive
only its data-free config/summary/diff in the result folder after execution; leave numeric packages and
public-context copies local and ignored. Run-directory evidence is required before reporting a pass.

Then complete the external target/guide eligibility audit and have the prospective cohort/batch/evaluator
boundary reviewed. Feature/plugin execution remains trusted Python under the current OS user; it is not
the requested inaccessible-test security boundary. A separate evaluator account/host must hold new labels
and reports with orchestration access denied and verified. No new cohort download, protected evaluator
change, API spending, permissions change or merge is implied by this adapter.
