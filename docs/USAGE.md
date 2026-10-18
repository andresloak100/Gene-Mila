# Using Gene-Mila: operational reference

The [README](../README.md) carries what a reader of the paper needs. This page holds the rest: how to
run the lab, prepare data, configure it and read a run's outputs, the synthetic worked example in
detail, the commands for the feature-comparison tools, and how the lab relates to CellForge and
VCWorld. It was split from the README on 16 October 2026; the text is the README's, moved here.

Sections: [Quick start](#quick-start) · [Scaling](#scaling) · [Data](#data) · [cell-eval](#cell-eval) ·
[Configuration](#configuration) · [Providers](#providers) · [Outputs of a run](#outputs-of-a-run-runsid) ·
[Architecture](#architecture) · [The synthetic example in detail](#the-synthetic-example-in-detail) ·
[Tools for the feature comparison](#tools-for-the-feature-comparison) ·
[Relation to CellForge and VCWorld](#relation-to-cellforge-and-vcworld)

## Quick start

Needs Python 3.11 or newer.

```bash
pip install -r requirements.txt
python -m pytest -q                                   # allow roughly 15 minutes on the Mac

# offline dry run: mock workers + scripted planner, synthetic data, no API keys
# (the no-LLM control in docs/example_run/control_scripted_summary.md)
python run_research.py --minutes 2 --workers 4 --worker-provider mock --planner-provider scripted
```

The command above uses synthetic data and makes no API calls. For paid work on the shared lab,
read [AGENTS.md](../AGENTS.md) and the current approved block in
[HANDOFF section 1](../HANDOFF.md#1-current-state-whoever-is-working-keeps-this-true) first. Every run
states its planner provider explicitly; the configuration default is Claude CLI. Paid runs also state
the shared ledger, cumulative cap, and separate worker and planner caps. Credentials enter through
the environment only. `python tools/deepseek_check.py` makes a paid API call, so it needs spend
authorization too.

Watch a run, then take it apart:

```bash
python status.py                     # live state (add --watch 5)
python leaderboard.py                # ranked experiments; --all includes failures
python leaderboard.py --lineage EXP_0012
python summarize.py --state          # the compressed research state the planner sees
python summarize.py                  # regenerate the run summary (keeps stored query-only scores)
python reproduce.py --experiment EXP_0012
python analyze_run.py                # worker independence, tokens, cost, bottlenecks, projections
```

The reporting commands default to the most recent run under `runs/`; pass `--run runs/<id>` to pick one.
Warm starts use `--continue-from runs/<earlier run>` on the same dataset and split, with the
explicit providers and budgets from the approved run plan.
`summarize.py` keeps the sealed-set scores a finished run already stored and makes no new
query; `--query-only` also scores any top candidate that has no stored sealed-set score yet.

## Scaling

```bash
# rehearsal with no API calls: 44 mock workers and an endless stream of distinct hypotheses
python run_research.py --minutes 5 --workers 44 --worker-provider mock --planner-provider loadtest
```

Experiments fork from a warm server process and reuse cached feature blocks within a run, which
on the mock benchmark cut CPU per experiment from 1.42 s to 0.07 s with bit-identical predictions
(see "CPU efficiency" in [`ARCHITECTURE.md`](ARCHITECTURE.md)); set `--set experiment.executor="subprocess"`
to use a fresh interpreter per experiment instead. `--workers` sets LLM worker slots;
`--cpu-slots` (default: number of cores) caps simultaneous CPU experiments independently, so 44
workers on an 8-core machine queue politely for CPU while the others are writing code. Planner
calls are unlimited unless `--max-planner-calls` is set. The planner's own cap scales with
workers and hours (`budget.planner_usd_per_worker_hour`) and is paced over the run, so a long
run never spends it all at the start; new LLM calls are refused once any dollar cap is reached.
For paid scaling, use the exact commands and authorized caps from the current pre-specified
block in HANDOFF. The cumulative cap includes earlier runs' ledger spend; it is separate from
the cash balance reported by DeepSeek. A run can halt partway through if that cap is left at its
development default. Do not increase a cap or reprice the shared ledger without Andres's decision.

A second synthetic test ([report](archive/records/deepseek_test_2026-10-03.md)) kept Claude Opus as planner and
used DeepSeek workers. From its measurements the report projects the next limit: at 44 workers, one
planner call every ~30 s with at most 20 hypotheses would cap supply near 40 experiments a minute,
so the planner, not CPU or DeepSeek, would set the pace. The lab has since been changed to run
several planner rounds at once as the worker count grows (`schedule.planner_concurrency`).

## Data

`python prepare_data.py synthetic` builds a small synthetic knockout screen with known
biology (gene modules → co-expression, a sparse regulatory network, a shared stress
response) plus prior knowledge (`gene_sets`, `prior_network`, `transcription_factors`; the
gene sets and the network are deliberately noisy). It is the fixture used for tests and
development.

Real data. The ingestor reads both layouts CellForge uses: scPerturb files (raw counts,
`obs['perturbation']`, e.g. `AdamsonWeissman2016_GSM2406681_10X010.h5ad` from
https://zenodo.org/records/13350497) and GEARS files (`perturb_processed.h5ad`,
`obs['condition']` with `GENE+ctrl`). It normalises raw counts (counts per 10k, log1p),
parses target genes out of labels (guides for the same gene are merged; `GENEA+GENEB`
doubles are kept), keeps highly variable genes plus every target gene, and splits by
perturbation. `--control` takes one or more control labels when none has a standard name.
`--splits` takes an external split instead of ours: train/val1/val2 or train/val/test lists,
or CellForge's train/test, whose test set becomes the query-only set while visible
validation is drawn from their training perturbations (`--val-frac`, default 0.25).

Prior knowledge for real screens: `python prepare_data.py knowledge` downloads curated
resources once (Reactome, GO Biological Process and MSigDB Hallmark gene sets, CollecTRI
signed TF-to-target regulation, STRING v12 physical interactions), and `--knowledge` filters
them to a bundle's genes. This general-purpose download excludes perturbation screens and
expression atlases. The real-data campaigns separately added the audited Replogle 2022 CRISPRi
screen as external knowledge, recorded in each run's configuration; see the Adamson results in
the README and [the external-screen control definitions](PROMPTS.md).
A source used as model knowledge cannot also serve as an untouched test.

```bash
pip install anndata cell-eval
python prepare_data.py describe AdamsonWeissman2016_GSM2406681_10X010.h5ad
python prepare_data.py knowledge                       # once; needs network access
python prepare_data.py h5ad --name adamson --knowledge data/raw/knowledge \
    --h5ad AdamsonWeissman2016_GSM2406681_10X010.h5ad --hvg 2000
python run_research.py --dataset adamson --minutes 20 --workers 4 \
    --worker-provider mock --planner-provider scripted
```

## cell-eval

Each bundle also keeps, privately, the cells of held-out perturbations and a separate
sample of control cells. At the end of a run the finalists (and the best baseline) are
scored with Arc Institute's [cell-eval](https://github.com/ArcInstitute/cell-eval) on the
visible validation set, and on the query-only set as part of the same capped oracle query.
A prediction becomes (held-out control mean + predicted delta) repeated for each real
cell, as cell-eval's own mean baseline does, so pseudobulk metrics (pearson_delta, mse,
DE overlap/precision, discrimination score) are comparable with other methods while
distribution metrics treat the prediction as a point mass. Results land in
`summary.md` / `summary.json` and `runs/<run>/celleval/`. Turn it off with
`--set final.celleval=false`; `final.celleval_profile` picks the metric set.
Every experiment is also scored with CellForge's and VCWorld's published metrics
(see [`ARCHITECTURE.md`](ARCHITECTURE.md)), and the summary has a table for each.

## Configuration

`configs/default.toml` holds every knob (workers, CPU slots, timeouts, RAM, retries,
exploration mix, providers and models, budgets, prices). Override with `--config my.toml`
or `--set section.key=value`. Model selection uses every visible perturbation: each experiment
also predicts the training perturbations out of fold (`experiment.cv_folds`, fixed folds per run,
set by the lab and not by agents) and the primary score averages those with the visible
validation set, so the search signal rests on 60-70 perturbations instead of 15-20.
`experiment.selection` names the selection score: `pearson_delta` (the default: correlation of the
predicted change, blind to its size) or `pearson_delta+r2_top`, which adds R² on each perturbation's
twenty most changed genes so a model that shrinks every change loses; `tools/replay_selection.py`
replays both rules over finished runs for free, on visible data only (select on one visible part,
score on the other), never on the sealed set. While the
planner thinks, `schedule.python_exploit` queues deterministic follow-ups around the best model
(add a helpful feature, ablate, refine alpha, swap the model family) so workers never idle; and
`final.ensemble` tries the average of the finalists as one more candidate for the sealed set, kept
only when it wins on the visible perturbations. `schedule.discovery` (off by default; reported as its own arm,
[DISCOVERY_MODE.md](DISCOVERY_MODE.md)) shows the planner where the best model fails, from the training
folds only, and which bundle inputs no feature has read, instead of the fixed idea list; each new
feature names the unread input it brings and is scored for how far the parent's columns already
explain it (`derived_r2`), and the planner stops after `schedule.discovery_dry_rounds` rounds that
bring no unread input. `--continue-from runs/<earlier run>` warm-starts a
run on the same split from that run's useful features and best model, with a PRIOR CAMPAIGN
section in the planner's state. DeepSeek's models reason before answering by default and the
hidden reasoning counts against `worker.max_output_tokens`; the default `worker.thinking = "disabled"`
keeps the whole limit for code (set `"enabled"` plus `worker.reasoning_effort` to try it). DeepSeek prices are set to the
published peak-hour rates for `deepseek-flash` (the configured legacy `deepseek-chat` alias)
and `deepseek-v4-pro`, as checked on the date recorded in the configuration. Prices are a dated
snapshot. `python tools/reprice_ledger.py` previews discrepancies without changing anything; changing
prices or applying a ledger rewrite requires an explicit reviewed decision under [AGENTS.md](../AGENTS.md).

## Providers

`genemila/providers/` hides every model behind `AgentProvider` (`propose`, `implement`,
`diagnose`, `summarize`; a backend only needs `complete()`):
`claude_cli`, `anthropic`, `deepseek`, `openai_compat` (OpenAI, Grok, vLLM/Ollama/OpenCode
servers via `[providers.openai_compat] base_url / api_key_env`), and three that make no API
call: `mock` workers, the `scripted` planner, and the `loadtest` planner (an endless stream of
distinct hypotheses, for rehearsing many workers).
Escalation: set `worker.escalation_provider`/`escalation_model` and a failing cheap-model
implementation (after `llm_retries` fixes) is handed to the stronger model once.

## Outputs of a run (`runs/<id>/`)

`lab.db` (everything, failures included), `artifacts/EXP_xxxx/` (spec, every LLM attempt,
smoke reports, plugin file, predictions, fitted models, metrics, logs), `feature_store/`,
`planner/` (state given to the planner and its raw plans), `celleval/`, `controller.log`,
`summary.md`, `summary.json`, and `warm_start.json` when continued from an earlier run.
Experiment code is pinned at `refs/genemila/<run>/<experiment>`. Only the chosen alpha's
predictions are kept per experiment (`predictions.npz` for the held-out sets, `cv.npz` out of
fold for the training perturbations) and the feature cache is bounded
(`experiment.feature_cache_max_mb`); a run stops early when free disk drops below
`run.min_free_disk_mb`.

`python results_table.py build --runs runs/<...>` turns run summaries into a results table in
CellForge's Table 1 layout ([`results/`](results/)), and `results_table.py calibrate` checks which metric
definition reproduces the paper's simple-baseline rows.

## Architecture

| Role | Who | Sees |
|---|---|---|
| Planner | Claude or DeepSeek, through the selected provider | A compressed research state of at most 20,000 characters (2,500 per section, 8,000 for the knowledge section), however long the run. Called when the queue runs low; with many workers, several rounds run at once. |
| Workers | DeepSeek, Claude Haiku, or any OpenAI-compatible model | The spec, a 30-line API reference, one example plugin, short summaries of the data and the prior-knowledge files, and the names of the model's other features. Never the repository or the experiment history. |
| Controller | Python | Everything: deadline, queue, retries, concurrency, evaluation, the query-only oracle, SQLite. |

Beyond the six rules in the README's Methods, the controller enforces:

| Guard | Mechanism |
|---|---|
| Compute | Per-experiment wall timeout, `RLIMIT_CPU` and `RLIMIT_AS` (Linux) plus RSS polling; one CPU-slot semaphore shared by all workers (`--cpu-slots`). |
| Spend | The worst-case cost of every LLM call is reserved before the call. A call that could cross a per-run cap or the cumulative per-provider cap in `runs/spend_ledger.sqlite` is refused before it reaches the provider. A circuit breaker pauses a provider after repeated API failures, for 60 s at first and up to 10 minutes. |
| Spec hygiene | Every experiment states a hypothesis and a rationale; at most 3 changes from its parent (more than 1 is flagged); no hidden-label, evaluator or split language; duplicate configurations are skipped. |
| Integrity | Dataset file hashes and the split id are verified at start. Each experiment's code is committed and pinned at `refs/genemila/<run>/<experiment>`. |
| Validation labels | Experiment subprocesses receive only `public.npz` (control cells, training labels, perturbation metadata) and predict every non-training perturbation; the controller scores them. |

Process tree: who owns what.

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
    └── Final: query-only evaluation of top candidates and the best baseline,
           cell-eval when held-out cells exist, summary.md + summary.json
```

Module map, token and CPU budgets, failure handling and current limitations are in
[`ARCHITECTURE.md`](ARCHITECTURE.md). The README figures are drawn from the run reports by
[`assets/build_figures.py`](assets/build_figures.py); see [`assets/DESIGN.md`](assets/DESIGN.md).

## The synthetic example in detail

The README's Fig. 2 shows this run. Summary, planner batch, research state and analysis are in
[`example_run/`](example_run/). Before the real screens, the lab was checked on a synthetic
screen whose biology is known. Claude Opus planned and four Claude Haiku workers wrote code
against a synthetic knockout screen: 300 genes, 1,000 control cells and 80 single-gene knockouts
(48 for training, 16 for visible validation, 16 sealed), generated from gene modules and a sparse
regulatory network. The agents could read prior knowledge: module gene sets and a regulatory
network, both partly wrong on purpose, and the exact list of transcription factors. The budget was
10 minutes. The run ended itself at 5.6, when its four planner rounds were used up.

One worker-written feature did most of the work. `target_coexpression_e7`, the knocked-out
gene's co-expression row in control cells, took pearson_delta on visible validation from
0.6054 to 0.7633 (+0.1579). Two more steps added `target_knockdown_scaled_e24` (+0.0136), which
predicts the knocked-out gene's own drop, and `tf_gated_coexpression_e26` (+0.0007), reaching
0.7775. After the run, the sealed query-only set scored the top three models and the baseline,
one logged query each: the winner scored 0.7764 and the baseline 0.5942, so the gain held on 16
perturbations no agent was ever scored on. The last step is too small to separate from noise
on 16 perturbations.

### The no-LLM control on the same split

The same split, run with no LLM at all, does as well. The offline dry run in [Quick
start](#quick-start) uses a scripted planner (seven fixed hypotheses, then combinations of
those that helped, an alpha sweep and one lasso fit) and hand-written template features from
`genemila/providers/mock.py`. In 2 minutes and for $0 it reached 0.7702 on visible validation
and 0.7776 on the sealed set ([summary](example_run/control_scripted_summary.md)), against
the agents' 0.7775 and 0.7764 for about $1.25 of recorded API cost. The control is
timing-sensitive, because its planner combines only results that have finished: three of four
runs of the same command gave 0.7702 and 0.7776, and one stopped a step earlier at 0.7683 and
0.7744. The agents, who never saw the templates, re-derived them: target co-expression adds
+0.1579 in the agent run and in the control. So this run shows that the machinery works and
that the agents reach a hand-written reference; it does not show what agents add beyond one.
That is the first question for real screens. CellForge's PCC, which correlates whole expression
profiles rather than changes, is 0.975 for the linear baseline and 0.980 for the best model on this
run's visible validation: it barely separates them, which is why the search uses pearson_delta.

### A feature a worker wrote

Worker W000 wrote `tf_gated_coexpression`, the last and smallest step of the lineage, in one LLM
call, in its own git worktree, from a 30-line API reference and one example plugin. It takes
the knocked-out gene's co-expression row from control cells and splits it into two columns, one
used when the target is a transcription factor and one when it is not (excerpt;
[full file](example_run/tf_gated_coexpression_e26.py)):

```python
@register
class TFGatedCoexpressionE26(Feature):
    name = "tf_gated_coexpression_e26"
    ...
    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        out = np.zeros((len(perts), ctx.n_genes, 2))
        tf_list = ctx.knowledge('transcription_factors')
        ...
        corr_matrix = ctx.gene_corr
        for i, p in enumerate(perts):
            ...
            target_corr = corr_matrix[target_idx, :].copy()
            ...
            is_tf = 1.0 if target_gene in tf_set else 0.0
            tf_part = target_corr * is_tf
            nontf_part = target_corr * (1.0 - is_tf)
            out[i, :, 0] = tf_part
            out[i, :, 1] = nontf_part
        return out
```

The synthetic run's final model is ridge (alpha = 100) on standardised features, so the
coefficients share one scale. This is the whole model:

| Feature | Written by | Coefficient |
|---|---|--:|
| `mean_response` | built in | +0.1040 |
| `target_knockdown_scaled_e24` | worker W000, EXP_0024 | +0.0948 |
| `target_coexpression_e7` | worker W002, EXP_0007 | +0.0404 |
| `tf_gated_coexpression_e26[0]` | worker W000, EXP_0026 | −0.0305 |
| `tf_gated_coexpression_e26[1]` | worker W000, EXP_0026 | −0.0254 |
| `is_target` | built in | +0.0121 |
| `control_mean` | built in | +0.0012 |

Read the co-expression rows together. `target_coexpression_e7` is the target's co-expression row
with its sign flipped, and `tf_gated_coexpression_e26` splits the same row (target entry zeroed)
by whether the target is a transcription factor. The three columns sum to zero on every row, so
the data cannot separate their weights and ridge's penalty divides them. Read together, they say
the same thing for both kinds of target: the more a gene is co-expressed with the knocked-out
gene in control cells, the lower its predicted change, slightly more so when the target is a
transcription factor. The signs differ only because e7 is negated. Only the transcription-factor
split is new information, and it added +0.0007.

### What the lab threw out

In the same synthetic run, EXP_0027 never reached a model. Its smoke test replaced training
perturbation G0000_KO's label with noise and the feature's rows for G0000_KO changed: the
feature was reading its own answer. The error went back to the worker, after one fix attempt
the feature still failed the same test, and the experiment was recorded as failed with the hint
`use ctx.train_delta(exclude=p)`. Twelve alpha settings that the planner proposed and the
controller expanded without another LLM call changed nothing at four decimals, and two worker
features made the model slightly worse (−0.0002 and −0.0030). All of it stays in `lab.db` next
to the wins.

### Cheaper workers, same rules

A second synthetic test ([report](archive/records/deepseek_test_2026-10-03.md)) kept Claude Opus as
planner and used DeepSeek workers. Four workers ran 11 experiments, each in its own worktree
commit, and none failed. The best feature, `net_diffusion_signed` (the knockout's signed
propagation through the prior regulatory network), reached 0.7980 on visible validation against
the same 0.6054 baseline, above the scripted control's 0.7702; the report records no sealed-set
score for that run. Recomputed from the recorded tokens at DeepSeek's peak rates, the workers
cost about $0.022 across the test's runs, or $0.0015 per experiment in the four-worker run; the
Claude planner reported $0.225.

## Tools for the feature comparison

The README's section "Can the agents find new biology?" describes these tools; the plans are
[`NOVEL_FEATURE_NEEDS.md`](NOVEL_FEATURE_NEEDS.md), [`FEATURE_COMPARISON_PROTOCOL.md`](FEATURE_COMPARISON_PROTOCOL.md)
and [`PLAN_F_GENOME_ANNOTATION.md`](PLAN_F_GENOME_ANNOTATION.md). Block F ran on 16 October (`results/norman_f_readings.md`);
the tool gained a perturbation-level null, a family-wise max-gain correction and the saved coefficient sign on
17 October (`docs/ROADMAP.md` D2), and `tools/build_gene_constraint.py` and `tools/build_protein_annotation.py`
build the two further per-gene tables block G uses.

```bash
# the genome annotation file for the Norman genes
python tools/build_gene_annotation.py --gtf gencode.v27.primary_assembly.annotation.gtf \
    --fasta Homo_sapiens_assembly38.fasta --genes-from data/norman --out gene_annotation.json
# the task package for an outside system; once it has worked there, score the features it kept
python tools/export_task_package.py --data data/norman --out pkg_norman
python tools/feature_compare.py --data data/norman --out fc_norman \
    --source ar=pkg_norman/runs/kept/features
```

`tools/knowledge_coverage.py` counts, per target, which genes the bundle's knowledge files cover
once it runs on the Mac's data. `tools/feature_compare.py --with-val1` reads the visible-validation
labels and is used only when Andres approves it.

## Relation to CellForge and VCWorld

Gene-Mila stays a separate lab rather than a fork of CellForge or VCWorld, built to be compared
with both:

1. **CellForge's datasets.** Adamson is done. Norman has its bundle, a split that keeps
   held-out single genes out of training, the additive baseline, a recorded modality (CRISPRa)
   with sign-aware external features, and reading rules fixed before any run. Srivatsan
   (sci-Plex 3) needs drug and dose ingestion.
2. **The same game.** `results_table.py` lays every arm out like CellForge's Table 1
   ([`results_table.md`](results/results_table.md)), with Unperturbed, Random Forest and
   Linear Regression refitted on the same split and the paper's rows quoted from
   `results/cellforge_table1.json`. Its calibration finds no metric definition that
   reproduces the paper's simple-baseline rows, so those rows stay marked as reported, not
   comparable. A real comparison needs CellForge's model run through this evaluation on the same
   split, which needs a GPU. VCWorld's benchmark is drug perturbations only, so until Gene-Mila
   has drug features the VCWorld comparison uses its DE and direction metrics on Adamson and
   Norman, not its data.

Drug perturbations (Srivatsan in CellForge's set, and all of VCWorld's GeneTAK) wait on drug
metadata: every feature today assumes a gene target, and the ingestor drops labels that name no
measured gene.

| | [CellForge](https://arxiv.org/abs/2508.02276) | [VCWorld](https://proceedings.iclr.cc/paper_files/paper/2026/file/767ff070c27c8954babe74eccf3fbe91-Paper-Conference.pdf) (ICLR 2026) | Gene-Mila |
|---|---|---|---|
| Agents produce | a trained perturbation-response model | differential-expression and direction-of-change predictions | features for a ridge, lasso, elastic net or OLS model |
| Data | six datasets spanning gene knockouts, drug treatments and cytokine stimulations (scRNA-seq, scATAC-seq, CITE-seq), including Adamson, Norman and Srivatsan | GeneTAK: 348 drugs in five Tahoe-100M cell lines (C32, HepG2C3A, HOP62, Hs 766T, PANC-1) | Adamson and Norman from CellForge's set; synthetic screens to check the machinery |
| Scored by | MSE, PCC and R² on mean expression, all genes and top-20 DE genes | DE and direction classification: accuracy, precision, recall, F1, AUROC, AUPRC | `pearson_delta` for the search; both of theirs on every experiment; cell-eval for finalists |
