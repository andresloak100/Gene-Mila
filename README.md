<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/hero-narrow.svg">
    <img src="docs/assets/hero.svg" width="100%" alt="Gene-Mila. Agents write the features. Only a linear model may use them. The clock stops everyone. Example run on synthetic data: Claude Opus planner and Claude Haiku workers, 5.6 of 10 minutes used, 29 experiments, 1 of which failed the label-leakage test. pearson_delta on 16 visible-validation and 16 sealed query-only perturbations: linear baseline 0.6054 and 0.5942, best model 0.7775 and 0.7764.">
  </picture>
</p>

Gene-Mila is a research lab run by LLM agents against a wall clock. Give it a single-cell
perturbation screen and a deadline (`--hours 6`): Claude plans as the principal investigator,
cheap worker models each turn one hypothesis into one feature, and Python fits a ridge, lasso,
elastic net or OLS model, scores it, and kills everything when time is up. The outer model never
gets cleverer, so every gain arrives as a named feature with a coefficient, and every feature is
a committed file of numpy, scipy or scikit-learn code that a person can read.

**The question.** Gene-Mila asks how far LLM agents can take a linear model on perturbations
held out of training, within a fixed time budget, and which signals the gain comes from. The
task is the unpaired one: given control cells and the identity of a held-out genetic
perturbation, predict every gene's change in mean expression. Held out means that none of the
perturbation's cells are used in training; perturbations, not cells, are split. The predictor is
linear on purpose: on this task, simple linear baselines have matched or beaten deep-learning
models (Ahlmann-Eltze, Huber and Anders, *Nature Methods* 2025), and a linear model keeps the
biology in the features, where it can be read.

> [!NOTE]
> Every score on this page comes from a synthetic knockout screen with known biology. No
> real-data run is documented here yet; Adamson on CellForge's splits is next
> ([where this is going](#where-this-is-going)).

## What one run looks like

<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/example-run-narrow.svg">
    <img src="docs/assets/example-run.svg" width="100%" alt="Every experiment of the synthetic example run, plotted in queue order by pearson_delta on 16 visible-validation perturbations. Worker-written features range from 0.6053 to 0.7775. Twelve alpha sweeps sit on the 0.6054 linear baseline or the 0.7633 plateau, and one planner-proposed combination briefly held the best score at 0.7683. The winning lineage adds one feature per step: target_coexpression +0.1579 to 0.7633, target_knockdown_scaled +0.0136 to 0.7769, tf_gated_coexpression +0.0007 to 0.7775. EXP_0027 failed because its feature leaked the label. On 16 sealed query-only perturbations the best model scored 0.7764, a scripted control with no LLM 0.7776, and the linear baseline 0.5942.">
  </picture>
</p>

Claude Opus planned and four Claude Haiku workers wrote code against a synthetic knockout
screen: 300 genes, 1,000 control cells and 80 single-gene knockouts (48 for training, 16 for
visible validation, 16 sealed), generated from gene modules and a sparse regulatory network.
The agents could read prior knowledge: module gene sets and a regulatory network, both partly
wrong on purpose, and the exact list of transcription factors. The budget was 10 minutes. The
run ended itself at 5.6, when its four planner rounds were used up.

One worker-written feature did most of the work. `target_coexpression_e7`, the knocked-out
gene's co-expression row in control cells, took pearson_delta on visible validation from
0.6054 to 0.7633 (+0.1579). Two more steps added `target_knockdown_scaled_e24` (+0.0136), which
predicts the knocked-out gene's own drop, and `tf_gated_coexpression_e26` (+0.0007), reaching
0.7775. After the run, the sealed query-only set scored the top three models and the baseline,
one logged query each: the winner scored 0.7764 and the baseline 0.5942, so the gain held on 16
perturbations no agent was ever scored on. The last step is too small to separate from noise
on 16 perturbations. Summary, planner batch, research state and analysis are in
[`docs/example_run/`](docs/example_run/).

The same split, run with no LLM at all, does as well. The offline dry run in
[Quick start](#quick-start) uses a scripted planner (seven fixed hypotheses, then combinations
of those that helped and an alpha sweep) and hand-written template features from
`genemila/providers/mock.py`. In 2 minutes and for $0 it reached 0.7702 on visible validation
and 0.7776 on the sealed set ([summary](docs/example_run/control_scripted_summary.md)), against
the agents' 0.7775 and 0.7764 for about $1.25 of recorded API cost. The agents, who never saw
the templates, re-derived them: target co-expression adds +0.1579 in both runs. So this run
shows that the machinery works and that the agents reach a hand-written reference; it does not
show what agents add beyond one. That is the first question for real screens.

### A feature a worker wrote

Worker W000 wrote `tf_gated_coexpression`, the last and smallest step of the lineage, in one LLM
call, in its own git worktree, from a 30-line API reference and one example plugin. It takes
the knocked-out gene's co-expression row from control cells and splits it into two columns, one
used when the target is a transcription factor and one when it is not (excerpt;
[full file](docs/example_run/tf_gated_coexpression_e26.py)):

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

A second synthetic test ([report](docs/deepseek_test_2026-10-03.md)) kept Claude Opus as
planner and used DeepSeek workers. Four workers ran 11 experiments, each in its own worktree
commit, and none failed. The best feature, `net_diffusion_signed` (the knockout's signed
propagation through the prior regulatory network), reached 0.7980 on visible validation against
the same 0.6054 baseline, above the scripted control's 0.7702; the report records no sealed-set
score for that run. Recomputed from the recorded tokens at DeepSeek's peak rates, the workers
cost about $0.022 across the test's runs, or $0.0015 per experiment in the four-worker run; the
Claude planner reported $0.225. From the same measurements the report projects the next limit:
at 44 workers, one planner call every ~30 s with at most 20 hypotheses would cap supply near 40
experiments a minute, so the planner, not CPU or DeepSeek, would set the pace. The lab has since
been changed to run several planner rounds at once as the worker count grows
(`schedule.planner_concurrency`).

## How it works

<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/loop-narrow.svg">
    <img src="docs/assets/loop.svg" width="100%" alt="How one experiment moves through the lab, inside a dashed deadline frame. Claude, as planner, reads the research memory and proposes hypotheses as JSON. The Python controller queues them and adds sweeps and replicates. A worker LLM writes a single plugin file in its own git worktree. Python guards check it: AST rules, a smoke and label-leakage test, and a diff limited to that file. Code that fails goes back to the worker for a fix; if it still fails it is recorded as failed, or as rejected when forbidden code remains or the edit reaches outside its file. A ridge, lasso, elastic net or OLS model is fitted on CPU in a limited subprocess, the controller scores it by pearson_delta on visible validation, and the result goes into the research memory the planner reads next round. After the deadline: running fits get 30 seconds and are killed, the top 3 candidates and the best baseline are scored once each on the query-only set, finalists are scored with Arc's cell-eval when held-out cells exist, and a watchdog kills the process group if anything overruns.">
  </picture>
</p>

| Role | Who | Sees |
|---|---|---|
| Planner | Claude, through the `claude` CLI or the Anthropic API | A compressed research state of at most 20,000 characters (2,500 per section), however long the run. Called when the queue runs low; with many workers, several rounds run at once. |
| Workers | DeepSeek, Claude Haiku, or any OpenAI-compatible model | The spec, a 30-line API reference, one example plugin, short summaries of the data and the prior-knowledge files, and the names of the model's other features. Never the repository or the experiment history. |
| Controller | Python | Everything: deadline, queue, retries, concurrency, evaluation, the query-only oracle, SQLite. |

Six rules make a gain mean something. Each is enforced in code, not in a prompt.

| # | Rule | How the code enforces it |
|:-:|---|---|
| **1** | **The clock kills everything.** | A run gets `--minutes` or `--hours`. At the deadline the controller stops new experiments and LLM calls, gives running fits `run.shutdown_grace_s` (30 s), then kills them. `run_research.py` runs the lab as its own process group and SIGKILLs the group if it is still alive 180 s later, then writes the summary from `lab.db`. Completed models are kept. |
| **2** | **Linear models only.** | Ridge, lasso, elastic net or OLS, on CPU; any other model type is refused when the experiment is specified (`ALLOWED_MODELS` in `genemila/spec.py`). Fits run in a limited subprocess with a wall timeout, `RLIMIT_CPU` and `RLIMIT_AS`, and the controller picks alpha on visible validation. The rule binds the model fitted on the features; feature code may use numpy, scipy and scikit-learn, including models fitted on leave-one-out training responses. |
| **3** | **One new feature per experiment.** | A worker may change exactly one file, its plugin under `genemila/features/plugins/`, so a score change has one candidate cause. The diff guard rejects any other edit and any touch of the evaluator, data, splits or guards (`genemila/guard.py`). |
| **4** | **Numbers decide, never an LLM.** | The controller scores every experiment with its own evaluator (`genemila/benchmark/evaluator.py`). Ranking, sweeps, replicates, duplicate detection and scheduling are Python. |
| **5** | **The sealed set is read only after the run.** | Perturbations, not cells, are split 60/20/20 (or by an external split, `--splits`) into train, visible validation and query-only validation, hashed into a `split_id`. Experiments predict both validation sets without knowing which is which. Only `QueryOracle` reads the query-only labels, after the run: one query each for the top `final.top_k` distinct candidates and the best baseline, capped at `final.max_queries`, every query logged. |
| **6** | **Every feature is tested for leakage.** | Before a feature runs, the smoke test swaps one training perturbation's label for noise and checks that the feature's rows for it do not move. It also checks shape, NaN, determinism and constancy. An AST guard allows numeric imports only: no file I/O, network, processes or reflection. |

<details>
<summary>Also enforced: compute, spend, spec hygiene, integrity</summary>

| Guard | Mechanism |
|---|---|
| Compute | Per-experiment wall timeout, `RLIMIT_CPU` and `RLIMIT_AS` (Linux) plus RSS polling; one CPU-slot semaphore shared by all workers (`--cpu-slots`). |
| Spend | The worst-case cost of every LLM call is reserved before the call. A call that could cross a per-run cap or the cumulative per-provider cap in `runs/spend_ledger.sqlite` is refused before it reaches the provider. A circuit breaker pauses a provider after repeated API failures, for 60 s at first and up to 10 minutes. |
| Spec hygiene | Every experiment states a hypothesis and a rationale; at most 3 changes from its parent (more than 1 is flagged); no hidden-label, evaluator or split language; duplicate configurations are skipped. |
| Integrity | Dataset file hashes and the split id are verified at start. Each experiment's code is committed and pinned at `refs/genemila/<run>/<experiment>`. |
| Validation labels | Experiment subprocesses receive only `public.npz` (control cells, training labels, perturbation metadata) and predict every non-training perturbation; the controller scores them. |

</details>

### The prediction

For perturbation $p$ and gene $g$, one linear model shared across all rows predicts the change
in mean expression:

```math
\Delta_{p,g} \;=\; \bar{x}_{g \mid p} \;-\; \bar{x}_{g \mid \text{control}} \;\approx\; w^{\top} f(p, g) + b
```

A feature $f$ maps $(p, g)$ to one or a few numbers (`genemila/features/api.py`), so each
coefficient weighs one named signal for every perturbation and gene, as long as no feature is a
linear combination of others (see the note under the coefficient table). The primary metric is
`pearson_delta`: for each held-out perturbation, the Pearson correlation between predicted and
true change across genes, averaged over perturbations. Baselines run first: no change, the mean
training response, and OLS, ridge and lasso on control mean, leave-one-out mean response and a
target indicator. On the synthetic example run's visible validation they score 0 (a constant
prediction has no correlation), 0.4755 and 0.6054 (the three linear fits tie).

`pearson_delta` has two known soft spots. It correlates over every gene, the knocked-out gene
included, whose own drop is easy to predict. And it is measured against control, so a response
that all perturbations share scores well on its own; that is why the mean training response
reaches 0.4755 (the systematic-variation problem described by Systema, Viñas Torné et al.,
2025).

So that the numbers can sit next to published ones, every experiment is also scored with
CellForge's metrics (MSE, PCC and R² on mean expression, over all genes and over the top-20 DE
genes) and VCWorld's DE and direction classification metrics (`genemila/benchmark/comparable.py`).
They measure different things: CellForge's PCC correlates whole expression profiles, not
changes, so in the scripted control run it is 0.975 for the linear baseline and 0.980 for the
best model on visible validation ([summary](docs/example_run/control_scripted_summary.md)).

## Limitations

- **Synthetic data only, so far.** The synthetic screen was generated from the same mechanisms
  (gene modules, a regulatory network) that the winning features exploit, so it checks the
  machinery, not the science. No real-data run is documented here yet.
- **No evidence yet that agents beat a hand-written list.** On the synthetic screen a scripted
  run with no LLM matches the agents (see [above](#what-one-run-looks-like)).
- **One split, one run.** Every agent number comes from a single run on one random split (seed 0):
  48 training, 16 visible and 16 sealed perturbations. Each score is a mean over 16
  perturbations whose own scores vary widely (from 0.547 to 0.922 for one model), so
  differences of a few thousandths, like the lineage's last step, are not resolved. Repeats,
  other split seeds and confidence intervals are not computed yet.
- **Features may learn.** A feature can fit its own model on training responses, leaving its
  own perturbation out (`knn_response_transfer_e8` was a nearest-neighbour transfer). The
  linear-only rule binds the outer model; reading a gain means reading its feature's code.
- **Recall or discovery.** On real genes, worker LLMs know the literature, so a gain may come
  from recalled biology rather than from the screen. Only a control that hides gene identities,
  for example by scrambling gene names, would separate the two.
- **Comparable metrics, not comparable runs yet.** CellForge's and VCWorld's metrics are
  reimplemented from their papers (`genemila/benchmark/comparable.py`), not run from their code;
  CellForge publishes no evaluation code and defines DE genes differently in its paper and its
  documentation, so both definitions are reported. cell-eval scores only the finalists, and the
  search itself optimises `pearson_delta`. No run documented here has real-data or cell-eval
  numbers yet.
- **Means, not cells.** The lab predicts each perturbation's mean expression change, so
  cell-eval's distribution metrics see a point mass per perturbation. Cell-level predictions
  would need a noise or sampling model on top of the linear mean model.
- **Process-level guards, not a sandbox.** They stop accidental or naive leakage. A determined
  program running as the same OS user could still find the private label files on disk; for
  untrusted models, run experiments as a separate user or in a container, or move
  `QueryOracle` to a remote service.
- **Short runs.** All three documented agent runs lasted minutes and ended when their
  planner-call cap ran out, before their deadline. No multi-hour or many-worker agent run is
  documented yet.

## Where this is going

The paper this lab is built for asks three questions:

- **How far?** On real screens and within hours, how close do agent-discovered features bring a
  linear model to CellForge on the same data and splits, and how far past a scripted planner
  with hand-written features on the same split and clock?
- **Which signals?** Which biology carries the gain, and how much of it comes from the screen
  rather than from what the models already know about these genes? In the synthetic runs most
  of the gain came from control-cell co-expression with the knocked-out gene (+0.1579 in one
  step), and the DeepSeek run's last step added signed propagation through a prior regulatory
  network. The synthetic screen was generated from exactly those mechanisms, so that is a
  sanity check, not a finding.
- **Does it hold?** Does the gain survive a set no agent tuned against, across repeated runs,
  under the same scoring as CellForge and VCWorld?

Gene-Mila stays a separate lab rather than a fork of CellForge or VCWorld, built to be compared
with both:

1. **Real screens on CellForge's splits.** Adamson (CRISPRi knockdown) first, then Norman
   (CRISPRa activation, single and double targets). The ingestor, CellForge-style train/test
   splits (`--splits`) and curated prior knowledge (`prepare_data.py knowledge`) exist. Before
   Norman, the planner has to be told the modality and that a target can be a gene pair: today
   it is told "single-gene targets", and the features that won here model loss of function.
2. **The same game.** Results laid out like CellForge's Table 1: Unperturbed, Random Forest and
   Linear Regression rerun on the same split, the published models quoted as reported, and
   Gene-Mila's best model next to its pre-agent starting point. VCWorld's benchmark is drug
   perturbations only, so until Gene-Mila has drug features the VCWorld comparison uses its DE
   and direction metrics on Adamson and Norman, not its data.

Drug perturbations (Srivatsan in CellForge's set, and all of VCWorld's GeneTAK) wait on drug
metadata: every feature today assumes a gene target, and the ingestor drops labels that name no
measured gene.

| | [CellForge](https://arxiv.org/abs/2508.02276) | [VCWorld](https://proceedings.iclr.cc/paper_files/paper/2026/file/767ff070c27c8954babe74eccf3fbe91-Paper-Conference.pdf) (ICLR 2026) | Gene-Mila |
|---|---|---|---|
| Agents produce | a trained perturbation-response model | differential-expression and direction-of-change predictions | features for a ridge, lasso, elastic net or OLS model |
| Data | six datasets spanning gene knockouts, drug treatments and cytokine stimulations (scRNA-seq, scATAC-seq, CITE-seq), including Adamson, Norman and Srivatsan | GeneTAK: 348 drugs in five Tahoe-100M cell lines (C32, HepG2C3A, HOP62, Hs 766T, PANC-1) | synthetic screens so far; Adamson and Norman next |
| Scored by | MSE, PCC and R² on mean expression, all genes and top-20 DE genes | DE and direction classification: accuracy, precision, recall, F1, AUROC, AUPRC | `pearson_delta` for the search; both of theirs on every experiment; cell-eval for finalists |

---

## Quick start

Needs Python 3.11 or newer.

```bash
pip install -r requirements.txt
python -m pytest -q                                   # about a minute

# offline dry run: mock workers + scripted planner, synthetic data, no API keys
# (the no-LLM control in docs/example_run/control_scripted_summary.md)
python run_research.py --minutes 2 --workers 4 --worker-provider mock --planner-provider scripted

# Claude plans, DeepSeek implements (needs DEEPSEEK_API_KEY and the claude CLI)
python deepseek_check.py                              # one minimal API call; prints tokens and cost
python run_research.py --minutes 3 --workers 1 --max-planner-calls 1   # one-worker cycle
python run_research.py --minutes 6 --workers 4 --max-planner-calls 2   # four-worker test

# the example run on this page (Claude Opus plans, Claude Haiku implements)
python run_research.py --minutes 10 --workers 4 --worker-provider claude_cli --worker-model haiku \
    --planner-provider claude_cli --planner-model opus --budget 1.5 --max-planner-calls 4
```

Watch a run, then take it apart:

```bash
python status.py                     # live state (add --watch 5)
python leaderboard.py                # ranked experiments; --all includes failures
python leaderboard.py --lineage EXP_0012
python summarize.py --state          # the compressed research state the planner sees
python summarize.py --query-only     # rebuild summary.md with the sealed-set tables
python reproduce.py --experiment EXP_0012
python analyze_run.py                # worker independence, tokens, cost, bottlenecks, projections
```

Every command defaults to the most recent run under `runs/`; pass `--run runs/<id>` to pick one.
`summarize.py --query-only` reuses the sealed-set scores a finished run already stored; plain
`summarize.py` rewrites the summary without them.

### Scaling (only after the 4-worker test is reviewed)

```bash
# rehearsal with no API calls: 44 mock workers and an endless stream of distinct hypotheses
python run_research.py --minutes 5 --workers 44 --worker-provider mock --planner-provider loadtest

# paid runs, from the DeepSeek report; each raises the cumulative DeepSeek cap on purpose
python run_research.py --minutes 20 --workers 8  --budget 0.50 \
    --set budget.cumulative_usd.deepseek=1.0
python run_research.py --minutes 20 --workers 16 --budget 1.00 \
    --set budget.cumulative_usd.deepseek=2.0
python run_research.py --hours 1 --workers 44 --budget 10 \
    --set budget.cumulative_usd.deepseek=12
```

Experiments fork from a warm server process and reuse cached feature blocks within a run, which
on the mock benchmark cut CPU per experiment from 1.42 s to 0.07 s with bit-identical predictions
(see "CPU efficiency" in `docs/ARCHITECTURE.md`); set `--set experiment.executor="subprocess"`
to use a fresh interpreter per experiment instead. `--workers` sets LLM worker slots;
`--cpu-slots` (default: number of cores) caps simultaneous CPU experiments independently, so 44
workers on an 8-core machine queue politely for CPU while the others are writing code. Planner
calls are unlimited unless `--max-planner-calls` is set; planner spend is capped at
`budget.planner_usd_per_hour` (15) times the run's hours, and new LLM calls are refused once any
dollar cap is reached. Raise `budget.cumulative_usd.deepseek` deliberately when you want to
spend beyond the $0.25 development cap.

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
them to a bundle's genes. Resources derived from perturbation screens or expression atlases
are left out on purpose, so prior knowledge cannot encode the held-out responses.

```bash
pip install anndata cell-eval
python prepare_data.py describe AdamsonWeissman2016_GSM2406681_10X010.h5ad
python prepare_data.py knowledge                       # once; needs network access
python prepare_data.py h5ad --name adamson --knowledge data/raw/knowledge \
    --h5ad AdamsonWeissman2016_GSM2406681_10X010.h5ad --hvg 2000
python run_research.py --dataset adamson --minutes 20 --workers 4
```

### cell-eval

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
(see `docs/ARCHITECTURE.md`), and the summary has a table for each.

## Configuration

`configs/default.toml` holds every knob (workers, CPU slots, timeouts, RAM, retries,
exploration mix, providers and models, budgets, prices). Override with `--config my.toml`
or `--set section.key=value`. DeepSeek prices are set to the
published peak-hour rates for `deepseek-flash` (what the API serves for `deepseek-chat`)
and `deepseek-v4-pro`; update `[pricing.*]` if they change, and run
`python reprice_ledger.py --apply` to recompute the spend ledger with new prices.

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
`summary.md`, `summary.json`. Experiment code is pinned at `refs/genemila/<run>/<experiment>`.

## Architecture

<details>
<summary>Process tree: who owns what</summary>

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

</details>

Module map, token and CPU budgets, failure handling and current limitations are in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The figures on this page are drawn from the run
reports by [`docs/assets/build_figures.py`](docs/assets/build_figures.py).
