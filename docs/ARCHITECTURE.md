# Architecture and design notes

## Scientific framing

* **Task.** Predict the pseudobulk expression profile of cells under an *unseen*
  perturbation, given control cells (unpaired) and the perturbation's identity.
* **Model.** One linear model over (perturbation, gene) rows predicting the expression
  change. Ridge/lasso/elastic-net/OLS only. The alpha grid is scored on visible
  validation by the controller, never by the experiment.
* **Primary metric.** `pearson_delta`: per held-out perturbation, Pearson correlation of
  predicted vs true change across genes, averaged. Selection uses every visible perturbation:
  each experiment also predicts the training perturbations out of fold (`experiment.cv_folds`
  fold views of the feature context that hide the fold's labels from feature code; folds fixed
  per run, set by the lab after validation so agents cannot choose them), and the primary score
  is the mean over validation plus out-of-fold perturbations; `pearson_delta` stays the
  validation-set value and `pearson_delta_cv` the out-of-fold value. Fold views are enforced,
  not trusted: the guard refuses plugin code that constructs its own `FeatureContext`, reaches
  a class through `type()`, `__init__` or `__file__`, or routes around the view; plugin modules
  are re-executed before every fold (and between the smoke test's checks), so a module-level
  memo cannot carry full-training aggregates into a fold. Features that never read training
  labels (`FeatureContext.label_reads`, recorded in a `.dep` sidecar next to each cached block)
  are sliced from the full-training block instead of recomputed per fold, so the fold cost is
  paid only by label-dependent features. Also recorded: RMSE, MAE, MSE,
  Pearson on the top-20 DE genes, direction accuracy on top-20 DE genes, raw-expression
  Pearson, per-perturbation scores, error by expression quartile, delta-scale ratio,
  plus feature/train/inference CPU time, peak RAM and model size.
* **Results table** (`genemila/benchmark/table.py`, `results_table.py`): run summaries, the paper's
  simple baselines refitted on the same split, and the paper's reported rows, in CellForge's Table 1
  layout with ranks recomputed from the means; plus a calibration of candidate metric definitions
  against the paper's Unperturbed / Linear Regression / Random Forest rows, because the paper does
  not state its expression scale and its repository has no evaluation code.
* **Comparable metrics** (`genemila/benchmark/comparable.py`), on every experiment's visible
  validation and on every query-only evaluation, so our numbers sit next to published ones:
  CellForge's MSE / PCC / R² on mean expression over all genes and over the top-20 DE genes,
  and VCWorld's DE and direction (DIR) classification metrics (accuracy, precision, recall,
  F1, AUROC, AUPRC over perturbation-gene pairs). Ground-truth DE genes come from the
  held-out cells (`genemila/benchmark/reference.py`: Welch t-test ranking for the top-20,
  Wilcoxon + Benjamini-Hochberg p <= 0.05 and |log2FC| >= 0.25 for DE labels) and are stored
  privately with the bundle. Raw-expression PCC is dominated by baseline expression (the
  "predict control" baseline already scores about 0.97 on the synthetic data), so it is
  reported, never optimised. Finalists are also scored with Arc's cell-eval.
* **Baselines** (always first): unchanged (control mean), mean training response,
  and OLS / ridge / lasso on {control mean, leave-one-out mean response, target indicator}.
* **Exploit engine** (`genemila/exploit.py`, `schedule.python_exploit`): whenever fewer
  experiments are queued than there are workers, Python queues deterministic follow-ups around
  the current best model (add a helpful feature it lacks, add the two best missing ones together,
  drop one of its features, refine the penalty around the chosen alpha, swap the model family).
  Candidates carry the best model's feature parameters and seed, are hashed like any queued
  experiment (a guardrail rejection keeps its hash too) and are never re-proposed, so the engine
  runs dry instead of looping; a run ends as exhausted only after one last exploit pass found
  nothing. `schedule.exploit_depth` adds two deeper tiers once the first is dry: every known
  feature and the best pairs added to the best model, a wider penalty range and follow-ups around
  the next-best distinct models (tier 2), then an exhaustive pass over small feature subsets (tier
  3), so a no-LLM run keeps searching for its whole time budget. It exists because the planner,
  not CPU, bounds throughput. Summaries count completed
  experiments by proposer (`completed_by_proposer`, `experiments_completed_planner`), so the
  scaling report can compare worker counts on planner-proposed work alone.
* **Ensemble finalist** (`genemila/report.py: ensemble_finalist`, `final.ensemble`): the average
  of the finalists' predicted deltas is scored like any experiment on the visible perturbations
  and, only when it beats the best single model there, becomes one more candidate for the sealed
  set (kind `ensemble`, one query-only evaluation). It never becomes the run's "best" experiment
  that the planner or a warm start builds on. Sealed-set queries go singles, starting model,
  ensemble, so a query cap of `top_k + 1` still scores the baseline; a damaged member artifact
  logs `ensemble_error` and leaves no half-built row; `reproduce.py` reproduces an ensemble
  through its members and re-averages them.
* **Warm start** (`run_research.py --continue-from RUN_DIR`, `Lab.warm_start`): a run on the same
  dataset and split imports the earlier run's useful features (code and metadata) into its store,
  queues that run's best model as its starting experiment, and gives the planner a PRIOR CAMPAIGN
  section (its best scores, helpful and unhelpful features, failed ideas). Another split is
  refused, because a model selected on other visible perturbations may have been selected on this
  split's sealed ones.
* **Splits.** By perturbation, 60/20/20, seeded, hashed into a `split_id` that every
  experiment records. `val1` metrics guide the agents; `val2` is query-only.

## Components

| Module | Role |
|---|---|
| `genemila/data/` | Dataset bundles (public vs private files, hashes), synthetic generator, `.h5ad` ingestion |
| `genemila/benchmark/` | **Protected** evaluator and query-only oracle |
| `genemila/features/` | Feature API (`FeatureContext`), built-in features, registry, `plugins/` for agent code |
| `genemila/pipeline.py` | Experiment subprocess: build features, fit, predict, smoke-test new features |
| `genemila/spec.py` | Experiment specification, guardrails, protected paths, config hashing |
| `genemila/guard.py` | AST check of plugins, worktree diff check |
| `genemila/isolation.py` | Git worktrees per experiment, commits pinned under `refs/genemila/` |
| `genemila/sandbox.py` | Limited subprocesses (timeout, CPU, RAM, external kill) |
| `genemila/db.py` | SQLite schema, atomic queue claims, lineage |
| `genemila/llm.py` | LLM gateway: budgets, token caps, retries, breaker, accounting |
| `genemila/providers/` | Provider abstraction and implementations |
| `genemila/prompts.py` | All prompts |
| `genemila/research_state.py` | Compressed research memory from the DB |
| `genemila/planner.py` | Hypotheses → specs; sweeps/replicates/parents/priorities in Python |
| `genemila/worker.py` | Worker slot: implement → test → run → evaluate → record |
| `genemila/controller.py` | Deadline, worker supervision, orphan requeue, shutdown |
| `genemila/report.py` | Final report, query-only evaluation |

## Token efficiency

* Workers get: the spec, a 30-line API reference, one example plugin, a one-line data
  summary, a one-line summary of each prior-knowledge file, and names of features
  already in the model. Never the repository or the experiment history.
* A fix attempt sends only the failing code and the tail of the error.
* The planner gets the compressed state (bounded at 12k characters regardless of run
  length) and returns a batch of hypotheses; it is called only when the queue runs low.
* Sweeps, combinations, ablations, evaluation, duplicate detection, scheduling and
  reporting never call an LLM.
* Planner failover: `planner.fallback` is an ordered chain of `provider:model` entries
  (`--set planner.fallback=deepseek:deepseek-v4-pro`). When the planner fails (a usage
  limit, an API error, a budget halt, or three unparseable plans in a row) the run switches
  to the next entry for good, logs a `planner_switch` event, and its summary (`planner`:
  configured, used, switches, failed rounds) and the results tables label it a
  mixed-planner arm named after the planners that actually produced its plans, never pooled
  with the clean runs. With the chain exhausted (the default: the chain is empty) the run
  goes on without a planner, draining its queue and the exploit follow-ups, under a
  `planner_exhausted` event and a "(lost its planner)" label. An LLM arm never degrades
  silently to the scripted planner; `run_research.py` refuses to start when no planner in
  the chain is usable.

## CPU efficiency

Measured on the example run, 96% of experiment CPU time was starting Python and importing
numpy/scipy/sklearn, not feature computation or fitting. Two mechanisms remove it:

* **Warm fork server** (`genemila/forkserver.py`, `experiment.executor = "forkserver"`): one
  single-threaded process per run imports the numeric stack and loads the public data, then
  forks a child per experiment or smoke test. Children keep their own session, rlimits, working
  directory and logs, so timeouts, kills and isolation are unchanged. If the server cannot start
  or dies, the executor falls back to fresh subprocesses.
* **Feature cache** (`experiment.feature_cache = true`): every computed feature block is stored
  under `runs/<id>/cache/features/`, keyed by the feature's source hash, version, parameters,
  dataset split and perturbation list; shared matrices (gene correlation) under `cache/shared/`.
  An experiment that adds one feature to a model computes only that feature.

Both are bit-identical to the plain path (tested). On the mock benchmark, CPU per experiment fell
from 1.42 s to 0.07 s. The remaining per-experiment overhead is git worktree creation and commits
(~0.5 s wall), which is negligible next to LLM latency.

Further options not yet built: solving ridge for all alphas from one X^T X factorisation,
screening new features on a gene subset before the full evaluation (for Adamson-size data), and
skipping fits whose new feature block is numerically identical to an existing feature.

## Failure handling

| Failure | Outcome |
|---|---|
| Syntax error / bad shape / NaN / non-determinism / leakage | Error tail sent back for `llm_retries` fixes, then optional escalation, then `failed` (stage `test`) |
| Forbidden code (I/O, imports, internals) | One chance to fix, then `rejected` (stage `guard`) |
| Edits outside the allowed file, or to protected paths | `rejected` |
| Timeout / RAM / CPU limit | Subprocess killed, `failed` (stage `timeout` / `resources`) |
| Worker exception | Recorded as `worker_crash` with traceback; the worker continues |
| Worker thread death | Supervisor restarts it; orphaned experiments requeued up to `max_attempts` |
| API errors | Bounded retries (default 1) with backoff; circuit breaker after N consecutive failures |
| Budget reached | Further calls refused before reaching the provider |
| Deadline | `killed` (stage `deadline`); queued work marked `cancelled` |

## Current limitations

* **Isolation is process-level, not a security sandbox.** The AST guard and the absence
  of private data in the experiment's inputs stop accidental or naive leakage, but a
  determined adversarial program running as the same OS user could still find the
  private label files on disk. For untrusted models, run experiment subprocesses as a
  separate user or in a container, or move `QueryOracle` (and val1 scoring) to a remote
  service; both only need the existing `query()` / `evaluate_artifact()` interfaces.
* The model family is one shared linear model over (p, g) rows. Per-gene models or
  perturbation-level embeddings would need a second feature kind.
* Real datasets could not be downloaded in the build environment (network policy);
  the `.h5ad` ingestor (scPerturb and GEARS layouts) is tested on a simulated screen but
  has not been exercised on Adamson yet.
* `cell-eval`: the search optimises in-house pseudobulk metrics; cell-eval scores only the
  finalists at the end. Predictions are perturbation means, so cell-eval's distribution
  metrics see a point mass per perturbation. Cell-level predictions would need a noise or
  sampling model on top of the linear mean model.
* Prices are configuration, not fetched; Claude CLI calls report their own cost.
