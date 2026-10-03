# Architecture and design notes

## Scientific framing

* **Task.** Predict the pseudobulk expression profile of cells under an *unseen*
  perturbation, given control cells (unpaired) and the perturbation's identity.
* **Model.** One linear model over (perturbation, gene) rows predicting the expression
  change. Ridge/lasso/elastic-net/OLS only. The alpha grid is scored on visible
  validation by the controller, never by the experiment.
* **Primary metric.** `pearson_delta`: per held-out perturbation, Pearson correlation of
  predicted vs true change across genes, averaged. Also recorded: RMSE, MAE, MSE,
  Pearson on the top-20 DE genes, direction accuracy on top-20 DE genes, raw-expression
  Pearson, per-perturbation scores, error by expression quartile, delta-scale ratio,
  plus feature/train/inference CPU time, peak RAM and model size.
* **Baselines** (always first): unchanged (control mean), mean training response,
  and OLS / ridge / lasso on {control mean, leave-one-out mean response, target indicator}.
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
  the `.h5ad` ingestor is written for the GEARS layout but has not been exercised on
  Adamson yet.
* `cell-eval` compatibility: metrics are computed in-house on pseudobulk profiles;
  exporting predictions to cell-eval's AnnData format is the next step.
* Prices are configuration, not fetched; Claude CLI calls report their own cost.
