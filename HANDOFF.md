# Handoff: the state of the lab and the open work

Read [`AGENTS.md`](AGENTS.md) first; its rules apply to everything here.

## 1. Snapshot

Written on 2026-10-04 at 17:15 UTC for an agent joining without access to the Claude project.
Things move fast. Before relying on anything below, check the live sources:

| Question | Live source |
|---|---|
| What is running on the Mac? | `tail -n 30 ~/Documents/Loak-documents/genemila_scale_logs/progress.md`, `pgrep -fl run_research.py` |
| How much DeepSeek money is spent? | `sqlite3 ~/Documents/Loak-documents/gene-mila/runs/spend_ledger.sqlite "SELECT provider, ROUND(SUM(cost_usd),2) FROM spend GROUP BY provider"` |
| What did a run find? | `runs/<run>/summary.md` and `summary.json` (`best`, `generalization_query_only`, `llm_usage`, `completed_by_proposer`, `split_id`) |
| What changed in the code? | `git log origin/claude/autonomous-research-system-3k435s`, open pull requests and issues |

## 2. Where things are

| What | Where |
|---|---|
| Repository (private) | `https://github.com/andresloak100/gene-mila` |
| Integration branch (pull requests go here; there is no `main` yet) | `claude/autonomous-research-system-3k435s` |
| Main checkout on Andres's Mac: real data, key, runs. **Don't touch its files or git state** | `~/Documents/Loak-documents/gene-mila` |
| Its Python environment | `~/Documents/Loak-documents/gene-mila/.venv` |
| Data bundle in use (gitignored) | `data/adamson_cf/` in the main checkout |
| Runs (gitignored) | `runs/<run>/` in the main checkout |
| Shared spend ledger, cumulative across all runs | `runs/spend_ledger.sqlite` in the main checkout |
| Comparison driver: progress, log, stop switch | `~/Documents/Loak-documents/genemila_scale_logs/` (`progress.md`, `driver.log`; a file named `STOP` halts the driver) |
| Raw data | scPerturb archive on Zenodo, record 13350497: `https://zenodo.org/records/13350497/files/<file>?download=1` |
| CellForge | paper arXiv 2508.02276; code `https://github.com/gersteinlab/CellForge` (it has no evaluation code; we rebuilt the metrics from the paper) |
| Evaluation package | `https://github.com/ArcInstitute/cell-eval` |

The Mac cannot push to GitHub. Results reach the repository when an agent with push access
commits the files the Mac produced, exactly as they are on disk.

## 3. The data

`data/adamson_cf` is Adamson et al. 2016 Perturb-seq (CRISPRi in K562 cells), file
`AdamsonWeissman2016_GSM2406681_10X010.h5ad` (the unfolded-protein-response screen):
counts per 10k plus log1p, 2,055 genes (highly variable genes plus every target gene),
88 knockdowns, 3 non-targeting control guides pooled as control, and CellForge's split with
seed 42: 50 training perturbations, 17 visible validation (`val1`) and 21 query-only (`val2`,
CellForge's test perturbations). It also carries prior-knowledge files (gene sets, TF targets,
protein interactions).

Bundle layout: `manifest.json` (source, split id, file hashes; the lab verifies them at the start
of every run), `public.npz` (all that feature code may see), `private/val1.npz` (evaluator only),
`private/val2.npz` (query-only oracle only), `splits.json` (protected). Never read the last three.

Not yet loaded: `NormanWeissman2019_filtered.h5ad` (single and double CRISPRa perturbations) and
`SrivatsanTrapnell2020_sciplex3.h5ad` (drugs; needs drug metadata the lab doesn't model yet).
CellForge's paper states no exact split; it holds out whole perturbations. Its split code (one 20%
hold-out, fixed seed) disagrees with its documentation (five folds), so whatever you do for a new
dataset, record every assumption next to the bundle.

## 4. Set up your own clone

On the Mac, with your own GitHub access:

```bash
cd ~/Documents/Loak-documents
git clone https://github.com/andresloak100/gene-mila.git gene-mila-<your-name>
cd gene-mila-<your-name>
git checkout -b <your-name>/<topic> origin/claude/autonomous-research-system-3k435s
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
mkdir -p data && cp -R ../gene-mila/data/adamson_cf data/     # a copy; never modify the original
export LEDGER="$HOME/Documents/Loak-documents/gene-mila/runs/spend_ledger.sqlite"
nice -n 19 python -m pytest -q
```

Your runs then land in your clone's `runs/`, away from the comparison. Off the Mac you can do
all code work; real runs need the bundle copied over (it contains private labels, so treat the
copy like the original) and network access to `api.deepseek.com`.

## 5. Run the lab

Every script defaults to the newest run under `runs/`; pass `--run runs/<run>` to choose one.

```bash
# free: scripted planner, mock workers (no LLM, no money); only when the Mac's driver is idle
python run_research.py --dataset adamson_cf --minutes 5 --workers 2 \
  --planner-provider scripted --worker-provider mock --run-dir runs/<your-name>_smoke

# paid: DeepSeek plans and implements; only with Andres's approval and amount, never next to another paid run
python run_research.py --dataset adamson_cf --minutes 20 --workers 4 --set run.seed=0 \
  --planner-provider deepseek --planner-model deepseek-v4-pro \
  --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek=<cap, at most 14> \
  --set budget.max_total_usd=<worker cap> --set budget.max_planner_usd=<planner cap> \
  --run-dir runs/<your-name>_<topic>_r0

# warm start from an earlier run on the same split
python run_research.py ... --continue-from runs/<earlier run>

python status.py --watch 5            # live state of a run
python leaderboard.py                 # ranked experiments (--all includes failures)
python summarize.py                   # regenerate summary.md / summary.json (keeps stored sealed scores)
python analyze_run.py                 # utilisation, tokens, cost, bottlenecks (writes analysis.json)
python reproduce.py --experiment EXP_0012
python results_table.py build --runs <run dirs> --dataset-key adamson   # CellForge Table 1 layout, into docs/results/
python results_table.py calibrate --data data/adamson_cf --dataset-key adamson
python scaling_report.py --runs <run dirs>                              # mean ± sd per arm and worker count
```

Measured costs: a 20-minute, 4-worker run spends about $0.20 to $0.50 on DeepSeek workers; a
DeepSeek V4 Pro planner adds about $0.50. List run directories explicitly in the report commands,
and leave out anything ending in `_contaminated` or `_interrupted`.

## 6. In flight on 2026-10-04 at 17:15 UTC

- **On the Mac, free:** a detached driver (started with `nohup setsid caffeinate`, so it survives the
  Claude session disconnecting) runs six control runs on the current code,
  `runs/newcode_control_r0` to `r5` (scripted planner, mock workers, 4 workers, 20 minutes).
- **Waiting on Andres:** whether the remaining paid runs may run unattended. Options: a $15 cap
  (the 8- and 16-worker seed-1 repeats `runs/scale_w8_r1` and `runs/scale_w16_r1`, then the planner
  check: `runs/newcode_ds_w4_r0`/`_r1` planned by DeepSeek V4 Pro and `runs/newcode_opus_w4_r0`/`_r1`
  planned by Opus, about $6 more), a $10 cap (only the two repeats, about $2), or free only.
- **After that:** the final results table, calibration and scaling report over every run, committed
  to `docs/results/` by the Claude "Autonomous research system" session from the Mac's files.
- **Ledger:** DeepSeek $4.66 at 17:02 UTC. The Opus planner's dollar figures are the Claude CLI's
  estimate of subscription usage, not a bill.
- **The Mac** must stay powered on and awake (plugged in, lid open) for any of it.

## 7. Results so far (Adamson, CellForge's split)

Primary metric `pearson_delta`: per held-out perturbation, the Pearson correlation of predicted and
true expression change across genes, averaged. "Visible" is what the agents select on; "held-out"
is the sealed query-only set, CellForge's test perturbations.

Starting model (OLS on three baseline features): 0.556 visible, 0.520 held-out.
Free no-LLM control on the old code: 0.571 / 0.554, identical over six seeds and finished after
about two minutes, so it is a fixed recipe and gives no noise estimate.

Worker-scaling comparison, code `2492e11`, Opus planner, DeepSeek workers, 20 minutes each:

| workers | seed | completed experiments | best visible | best held-out | experiments / hour | DeepSeek $ |
|---|---|---|---|---|---|---|
| 1 | 0 | 82 | 0.627 | 0.544 | 261 | 0.19 |
| 1 | 1 | 93 | 0.619 | 0.589 | 291 | 0.17 |
| 4 | 0 | 159 | 0.629 | 0.601 | 486 | 0.46 |
| 4 | 1 | 112 | 0.609 | 0.604 | see note | 0.22 |
| 8 | 0 | 280 | 0.637 | 0.585 | 855 | 0.71 |
| 16 | 0 | 657 | 0.648 | 0.562 | 1,936 | 1.20 |

Note: the 4-worker seed-1 run was killed at its deadline and its summary rebuilt afterwards; its
stored duration was an artefact (fixed in `2370276`), so read its throughput against 20 minutes.

The honest reading: throughput and the visible score rise with workers, the held-out score does
not. Sixteen workers chose among 657 experiments using 17 visible perturbations and ended with
the best visible and nearly the worst held-out score, which is selection overfitting. The two
1-worker runs differ by 0.045 held-out, as much as the spread across worker counts, so no
ordering is established. The current code selects on 67 perturbations (the visible set plus
5-fold out-of-fold predictions on the training set) to address exactly this; the new-code runs
above are its first test.

Against the simple baselines refitted on CellForge's split, every agent run wins on the top-20 DE
genes: held-out MSE 0.11 to 0.12 against 0.16 for linear regression, R² 0.80 to 0.82 against 0.71.
All-gene PCC is about 0.985 to 0.989 for every model, plain OLS included, so it separates nothing.
CellForge's published Adamson numbers cannot be reproduced under any metric definition tried
(their Unperturbed row reports PCC 0.0001; that baseline scores 0.98 on this data), so their rows
are marked not comparable.

Excluded from every table: `runs/scale_w8_r0_contaminated` (its planner fell back to the scripted
one mid-run), `runs/scale_w1_r1_interrupted`, and the first Adamson run (most experiments failed on
a since-fixed output limit).

## 8. Open work, in Andres's priority order

1. **Raise our model's held-out scores on CellForge's Adamson split.** The top priority. Once the
   planner check shows whether DeepSeek V4 Pro can plan as well as Opus, a campaign of longer
   runs warm-started from the best run (`--continue-from`) with the DeepSeek planner can carry it
   without the Claude subscription. Paid: needs Andres's approval and amount, and the Mac's driver
   must be idle. Unassigned.
2. **Finish the 1/4/8/16-worker comparison with repeats.** The Claude "Autonomous research system"
   session and the Mac's driver (section 6). Don't duplicate it.
3. **Final tables and scaling report, committed to `docs/results/`.** Same owner. If that session
   has gone quiet and Andres asks you to, run the commands of section 5 over the full run list and
   commit the files exactly as produced.
4. **Norman.** Ingest `NormanWeissman2019_filtered.h5ad` with `prepare_data.py h5ad` into a new
   bundle following CellForge's split code, record every assumption, run the free control on it,
   and only then propose paid runs. Free to start and collides with nothing: a good first task.
   Unassigned.
5. **Srivatsan (sci-Plex 3).** Drug perturbations need drug metadata, a new kind of feature input.
   A design question for Andres before any code. Unassigned.
6. **Smaller items** (from `docs/ARCHITECTURE.md`): one factorisation shared by every ridge alpha,
   screening new features on a subset of genes, skipping features numerically identical to existing
   ones. Lab code: claim it first, because the integration branch's owner may be changing the same
   files. Known limits, not bugs: the guard is not an operating-system sandbox, and the lab predicts
   per-perturbation means, so cell-eval's distribution metrics would need cell-level output (a
   design call for Andres).

## 9. Taking over the comparison (only if Andres asks)

The comparison must keep its arms comparable. If Andres hands it to you because no Claude session
is available, keep these settings and check `progress.md` first so nothing runs twice:

- dataset `adamson_cf`, 20 minutes, the shared ledger, one paid run at a time, and the driver
  stopped (`pgrep -fl run_research.py` shows nothing) before you start;
- run from your own clone checked out at the arm's code version, with
  `--run-dir ~/Documents/Loak-documents/gene-mila/runs/<run name>` so the comparison's runs stay
  together; the main checkout's files and git state stay untouched;
- the seed-1 repeats `scale_w8_r1` and `scale_w16_r1` run on code `2492e11` with the Opus planner,
  `--set run.seed=1`, worker caps $2 and $3 and `budget.cumulative_usd.deepseek=10`. They need the
  Claude CLI, so they wait while Andres's Claude usage is exhausted;
- the planner check on the current code, 4 workers, seeds 0 and 1: `newcode_ds_w4_r*` with
  `--planner-provider deepseek --planner-model deepseek-v4-pro --set budget.max_total_usd=2.5`, and
  `newcode_opus_w4_r*` with `--set budget.max_total_usd=1.5`, both with
  `budget.cumulative_usd.deepseek=15`; `python analyze_run.py --run <dir>` after each;
- then `scaling_report.py` and `results_table.py` over every `scale_*` and `newcode_*` directory
  except `_contaminated` and `_interrupted`.
