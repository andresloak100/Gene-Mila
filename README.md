# Gene-Mila: an autonomous laboratory for interpretable perturbation prediction

Gene-Mila runs a population of AI research agents against a hard wall-clock budget
(e.g. six hours). The agents discover **features** for deliberately simple, CPU-only
linear models (ridge / lasso / OLS) that predict post-perturbation gene expression of
**unseen perturbations** from unpaired control and perturbed populations. Because the
model is constrained, every gain is attributable to an explicit, inspectable
biological or statistical signal.

```
HYPOTHESIS → CONTROLLED FEATURE CHANGE → CPU MODEL → EVALUATION → EVIDENCE → SHARED MEMORY → NEXT HYPOTHESIS
```

## Architecture

```
run_research.py  (external watchdog: hard-kills the lab if it overruns, then writes the summary)
└── Controller  (owns deadline, scheduling, concurrency, retries, persistence; never an LLM)
    ├── Planner / PI ── LLMGateway ── Claude (claude CLI or Anthropic API)
    │      reads compressed research state, proposes hypotheses (JSON)
    │      Python expands sweeps, replicates, parents, explore/exploit/risky priorities
    ├── SQLite lab.db: queue, experiments (incl. failures), features, LLM calls, planner rounds
    ├── N worker slots (threads; 4 → 8 → 16 → 44 → 64 by --workers)
    │      claim → git worktree → [LLM writes ONE plugin file] → static guard → smoke test
    │      (shape, NaN, determinism, label-leakage) → diff guard → commit + pinned ref
    │      → CPU experiment subprocess (timeout, RAM, CPU limits; capped by --cpu-slots)
    │      → controller-side evaluation → record → feature store
    ├── LLMGateway: spend caps (per run, per role, cumulative per provider), token caps,
    │      bounded retries, circuit breaker, token/cost accounting for every call
    └── Final: query-only evaluation of top candidates, summary.md + summary.json
```

**The unit of prediction.** For perturbation *p* and gene *g* a single linear model
predicts `delta[p,g] = mean expression of g in cells perturbed by p − control mean of g`.
Each feature maps (p, g) to one or a few numbers (`genemila/features/api.py`), so the
model's coefficients say directly how much each discovered signal matters. Splits are
by perturbation: train / visible validation (val1) / query-only validation (val2).

**What agents can and cannot touch.**

| Protection | How it is enforced |
|---|---|
| Validation labels | Experiment subprocesses receive only `public.npz` (control cells, training labels, perturbation metadata). They predict all non-training perturbations without knowing which are val1 vs val2; the controller scores them with its own evaluator. |
| Query-only labels | Read only by `QueryOracle`, only at the end, for at most `final.max_queries` candidates, every query logged. |
| Evaluator, splits, benchmark | Worktree diff must be a subset of the experiment's allowed files (one plugin file); protected paths are rejected; dataset file hashes and split id are verified at start. |
| Feature code | AST guard: numeric imports only; no I/O, reflection, `os`/`subprocess`/network, or FeatureContext internals. |
| Label leakage | Smoke test replaces a training perturbation's label with noise and checks its own feature rows do not change. |
| Compute | Per-experiment wall timeout, `RLIMIT_CPU`, `RLIMIT_AS` (Linux) plus RSS polling; global CPU-slot semaphore. |
| Scientific hygiene | Spec guardrails: must state hypothesis + rationale, one new feature per experiment, ≤3 changes vs parent (>1 flagged), no hidden-label/evaluator/split language, duplicate configurations skipped. |
| Deadline | Controller stops new work, gives a grace window, kills subprocesses; the outer watchdog SIGKILLs the whole process group if needed. |
| Spend | Worst-case cost reserved before each call; calls refused once a cap would be crossed; cumulative ledger in `runs/spend_ledger.sqlite` survives runs. |

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q                                   # 68 tests, ~1 min

# offline dry run: mock workers + scripted planner, synthetic data (no API keys)
python run_research.py --minutes 2 --workers 4 --worker-provider mock --planner-provider scripted

# Claude plans, DeepSeek implements (needs DEEPSEEK_API_KEY and the claude CLI)
python deepseek_check.py                              # ONE minimal API call, prints tokens and cost
python run_research.py --minutes 3 --workers 1 --max-planner-calls 1   # one-worker cycle
python run_research.py --minutes 6 --workers 4 --max-planner-calls 2   # four-worker test

python status.py                     # live state (add --watch 5)
python leaderboard.py                # ranked experiments; --all includes failures
python leaderboard.py --lineage EXP_0012
python summarize.py --state          # the compressed research state the planner sees
python summarize.py                  # regenerate the run summary
python reproduce.py --experiment EXP_0012
python analyze_run.py                # worker independence, tokens, cost, bottlenecks, projections
```

Every command defaults to the most recent run under `runs/`; pass `--run runs/<id>` to pick one.

### Scaling (only after the 4-worker test is reviewed)

```bash
python run_research.py --minutes 20 --workers 8  --budget 1.00
python run_research.py --minutes 20 --workers 16 --budget 2.00
python run_research.py --hours 1    --workers 44 --budget 5.00 --set budget.cumulative_usd.deepseek=10
```

Experiments fork from a warm server process and reuse cached feature blocks within a run
(see "CPU efficiency" in `docs/ARCHITECTURE.md`); set `--set experiment.executor="subprocess"`
to use a fresh interpreter per experiment instead. `--workers` sets LLM worker slots; `--cpu-slots` (default: number of cores) caps
simultaneous CPU experiments independently, so 44 workers on an 8-core machine queue
politely for CPU while the others are writing code. Raise `budget.cumulative_usd.deepseek`
deliberately when you want to spend beyond the $0.25 development cap.

## Data

`python prepare_data.py synthetic` builds a small synthetic knockout screen with known
biology (gene modules → co-expression, a sparse regulatory network, a shared stress
response) plus noisy prior knowledge (`gene_sets`, `prior_network`,
`transcription_factors`). It is the fixture used for tests and development.

Real data (CellForge datasets): download the GEARS-processed Adamson set
(`https://dataverse.harvard.edu/api/access/datafile/6154417`, ~70 MB), extract
`adamson/perturb_processed.h5ad`, then:

```bash
pip install anndata
python prepare_data.py h5ad --name adamson --h5ad adamson/perturb_processed.h5ad --hvg 2000
python run_research.py --dataset adamson --minutes 20 --workers 4
```

The same ingestor handles Norman (combinatorial `GENEA+GENEB` targets are supported).

## Configuration

`configs/default.toml` holds every knob (workers, CPU slots, timeouts, RAM, retries,
exploration mix, providers and models, budgets, prices). Override with `--config my.toml`
or `--set section.key=value`. DeepSeek prices default to the published
`deepseek-chat` rates (cache hit $0.028, miss $0.28, output $0.42 per million tokens);
update `[pricing."deepseek-chat"]` if they change.

## Providers

`genemila/providers/` hides every model behind `AgentProvider` (`propose`, `implement`,
`diagnose`, `summarize`; a backend only needs `complete()`):
`claude_cli`, `anthropic`, `deepseek`, `openai_compat` (OpenAI, Grok, vLLM/Ollama/OpenCode
servers via `[providers.openai_compat] base_url / api_key_env`), `mock`, `scripted`.
Escalation: set `worker.escalation_provider`/`escalation_model` and a failing cheap-model
implementation (after `llm_retries` fixes) is handed to the stronger model once.

## Outputs of a run (`runs/<id>/`)

`lab.db` (everything), `artifacts/EXP_xxxx/` (spec, every LLM attempt, smoke reports,
plugin file, predictions, fitted models, metrics, logs), `feature_store/`, `planner/`
(state given to the planner and its raw plans), `controller.log`, `summary.md`,
`summary.json`. Experiment code is pinned at `refs/genemila/<run>/<experiment>`.

See `docs/ARCHITECTURE.md` for design notes and current limitations.
