# Handoff: the state of the lab and the open work

Read [`AGENTS.md`](AGENTS.md) first; its rules apply to everything here.

## 1. Current state (whoever is working keeps this true)

Update this section when you start, after each milestone, and before you stop or run out of
tokens; commit it straight to the integration branch (AGENTS.md, "Git"). Times are UTC.

**Last updated:** 2026-10-11 16:00, by Claude ("Agent handoff" session), from `docs/LAB_STATE.md`
(13:51) and the build thread up to 15:45. `docs/LAB_STATE.md` on the integration branch is the lab-code
owner's full catch-up document (results, levers tested, work in progress, what waits on Andres) and wins
over this section where they disagree; this section is the short cross-agent view.

**Active agents**

| Agent | Since | Working on | Claim |
|---|---|---|---|
| Claude, "Autonomous research system" (lab-code owner) | 2026-10-03 | Norman 2019 (Andres chose "Claude now", 11 Oct 12:02): the paid Norman run started 15:34; after it, the folder move on the Mac, the push of the Mac-only reports and Astra's branches, then `docs/LAB_STATE.md` and `docs/NORMAN_PLAN.md` | (predates claim issues) |
| Claude, "Repo description design" | 2026-10-04 | PR #1 (README), to be refreshed to today's results before it merges | |
| Astra (ChatGPT) | 2026-10-08 | not active now. Two DeepSeek continuation campaigns on Adamson (8 workers, 2 h each, about $21.50 together): sealed 0.599 to 0.602, +0.003 over the run they continued. Its branches `astra/deepseek-continuation-memory` (6a3e8a8e) and `astra/compact-master-selection` (74114d43, contains the first), both from lab commit 8261c57, exist only on the Mac until the Mac session pushes them | none |

**On the Mac (15:45):** the paid Norman run `runs/norman_ds_replogle_w4_r0` (N3 in `docs/NORMAN_PLAN.md`
section 6: DeepSeek planner `deepseek-v4-pro`, 4 workers, 20 minutes, the Replogle 2022 screen in the
bundle, no warm start, `--set budget.cumulative_usd.deepseek=34 --set budget.max_total_usd=2.2`) started
at 15:34 on Andres's words and ends about 15:55; it spends the last $2.20 of the cap. Its sealed reading
comes from `tools/sealed_reading.py` against the additive baseline. Start nothing else on the Mac while it
runs. After it, the Mac session moves the lab out of `~/Documents/Loak-documents/` into
`~/Documents/Mila/Gene-Mila/` (`gene-mila`, `genemila_scale_logs`, `gene-mila-2492e11`, `data_downloads`;
shortcuts stay at the old names, so paths recorded in past runs keep working), scans everything for
key-shaped strings, and pushes Astra's two branches unchanged plus a branch `claude/mac-reports-2026-10-11`
with the Mac-only reports (noise-ceiling and refit reports, the Replogle build report, the external
leave-one-out JSON, the Replogle control runs' config, summary and analysis log, the feature-audit JSON
and box, the N3 sealed reading, with an md5 list); the lab-code owner merges the reports into the
integration branch. The code at `28a8a37` already names the new folder (`handoff_state.py`,
`tools/scale_seq.sh`); `docs/LAB_STATE.md` (13:51) still names the old one.

**Results on Adamson (CellForge's seed-42 split; read the files):** tables over 28 runs in
`docs/results/results_table.md` and `scaling.md`, the account in `docs/results/summary_for_collaborators.md`,
the full picture in `docs/LAB_STATE.md`. Sealed pearson_delta: start 0.520; no-LLM control 0.553; agent
arms 0.566 / 0.602 / 0.584 / 0.577 for 1 / 4 / 8 / 16 workers; best of any run without an external
screen under 0.604; noise ceiling 0.94 on the visible validation set. Every lever tested since 5 Oct
(more workers, longer runs, a DE-aware selection rule, a hand-written transfer feature, Astra's
continuation campaigns, a learned target similarity, refitting on all visible labels, feature pruning)
is closed: the limit is information about the targets, not search. The one lever with new information
is an external K562 screen, Replogle 2022 (Andres chose it on 11 Oct), read as knowledge in the bundle:
leave-one-out over the 50 training perturbations +0.072 ± 0.020 over gene-set kNN
(`docs/results/external_loo_replogle2022_k562*.md`); no-LLM runs with the screen score 0.621, 0.638 and
0.646 sealed (`control_replogle_w4_r0`, `control_replogle_from_opus_r0`, `control_replogle3_from_opus_r0`,
one run each, their files on the push list). The 0.646 is the fourth look at a sealed set already scored
for dozens of finalists across about 30 runs, so it is not established: Norman, or a fresh split, is the
clean test. Against CellForge's reported Adamson row nothing is comparable (their evaluation code is
unpublished, their split holds out guides rather than genes, their spreads exceed the differences), so
nothing is reported as "beats CellForge" (`docs/LAB_STATE.md`, "Against CellForge"). Two reported models
(in `scale_w8_r0` and `newcode_ds_w4_r0`) use an agent feature built on Python's salted `hash()`; the
guard now refuses it (`3d7c519`) and their table rows need a footnote at the next regeneration
(`docs/results/feature_audit_v3.md`).

**Norman 2019 (free steps done 11 Oct; `docs/NORMAN_PLAN.md` section 8,
`docs/results/norman_sealed_reading.md`):** bundle built (231 perturbations, gene-grouped split
`split_a391fa9e7b4eccb7`); the Replogle gate passes; the pre-specified leave-one-out shows the screen adds
information on Norman too (+0.023 ± 0.006); but on the sealed set the no-LLM control with the screen
scores 0.719 pearson_delta against 0.717 without it and 0.713 for the additive baseline: a null so far,
neither control beats the additive baseline beyond its error, and selection overfits the perturbations it
chooses on (+0.030 over the baseline on visible data). The paid run above is the first agent arm on Norman.

**DeepSeek ledger:** $31.78 before the Norman run (workers $22.85, planner $8.93; Astra's campaigns about
$21.50), cap **$34** (Andres, 11 Oct 02:39: "we have a max of 34 for deep seek spend it as you think is
best but we need to have a very good model"), passed as `--set budget.cumulative_usd.deepseek=34`; no paid
run starts at a $33.50 ledger or above. After the Norman run the cap is spent: further paid work needs a
new amount from Andres. Opus planner dollars are the Claude CLI's estimate of subscription usage, not a
bill.

**Claude usage:** one Claude Max window shared by the Mac's Claude Code session, the cloud Claude threads
and the Opus planner; nearly spent on 11 Oct. When it is out, Opus-planned runs wait; everything else uses
the DeepSeek planner (AGENTS.md, "Money and usage").

**The key:** `DEEPSEEK_API_KEY` is in no file on the Mac; the Claude session there passes it to each paid
run as a process variable. Andres pasted it in chat again at 15:34 for the Norman run, so it must be
rotated afterwards. From now on nobody asks him to paste it anywhere: he stores the rotated key himself in
`~/.zshenv` on the Mac (`export DEEPSEEK_API_KEY=...`), and every agent reads it from the environment.

**Code:** integration branch head `28a8a37` (361 tests pass at `3d7c519`): Norman 2019 (gene-grouped
split, order-independent pair labels, additive baseline, CRISPRa-aware Replogle features, the `norman_v1`
leave-one-out, `tools/sealed_reading.py`), the external-screen arm (`run.external_knowledge` labels the
run; `tools/build_external_screen.py`, `tools/external_loo.py`), `tools/feature_audit.py`,
`tools/refit_visible.py`, `tools/noise_ceiling.py`, `tools/time_to_best.py`, `tools/compact_model_curve.py`,
reproducible feature runs (`PYTHONHASHSEED=0` in every experiment process; the guard refuses `hash()` and
`id()` in new agent plugins), `pytest.ini`, and the Mac paths above. The repository is public since
11 Oct: nothing secret goes into any branch, and every push from the Mac is scanned for key-shaped strings
first.

**Open pull requests:** #1 (README and its checker; needs today's results before it merges) and #2 (this
file, AGENTS.md, CLAUDE.md; brought up to `28a8a37` on 11 Oct). On 11 Oct 15:44 the build thread asked
Andres on a card whether to merge both; the merge waits on his answer. Andres merges, nobody else.

**Next:** (1) the Norman run's sealed reading, recorded in `docs/LAB_STATE.md` and `docs/NORMAN_PLAN.md`;
(2) the folder move, the push of the Mac-only reports and Astra's branches, and the reports' merge into
the integration branch; (3) PR #1 and PR #2 merged on Andres's word; (4) the compact-model rules (Andres's
ask, 11 Oct 00:32): push Astra's branch, review and merge its feature board, failure archive and curator
into the lab, then add the admission threshold, the second fold seed, the redundancy pre-check and the
monitor (`docs/LAB_STATE.md`, "In progress", item 2); (5) Srivatsan sci-Plex 3, which needs drug and dose
ingestion and Andres's design decision first. An arriving agent that is not the lab-code owner starts
nothing on the Mac while the Norman run and the move are in progress; free code work on (4) is open, claimed
with an issue. The timeline given on 5 Oct (three datasets by 10 to 12 Oct) has slipped: Norman started on
11 Oct, Srivatsan has not.

**Decisions to respect.** Andres's own: the $34 DeepSeek cap with spending inside it delegated (11 Oct
02:39); Replogle 2022 as the external screen (11 Oct); the compact-model rules (11 Oct 00:32); Norman to
Claude, "Claude now" (11 Oct 12:02) and "download norman" (12:04); the paid run goes to Norman, not
Adamson (started on his words, 15:34); the lab lives in `~/Documents/Mila/Gene-Mila` and everything goes
up to GitHub (15:34 to 15:41); earlier: $10 for the comparison (4 Oct 00:04), "go, $15 cap" (4 Oct 19:16),
"Fix, then 1 run" (4 Oct 23:21); CellForge's published rows marked not comparable; no 44-worker run.
Claude's, under his delegation: the default selection rule stays; one full paid Norman run rather than two
short ones; the lab-code owner maintains the protected benchmark, split and guard code.

**Only Andres can (the blockers for any other agent):**
- Rotate the DeepSeek key after the Norman run and store it himself in `~/.zshenv` on the Mac. Until
  then only the Mac's Claude session can start a paid run, and after this run the $34 cap is spent, so
  any paid run also needs a new amount from him.
- Answer the merge card for PR #1 and PR #2 (then merge them), and create a `main` branch.
- Give outside agents write access to the repository (Astra's branches go up through the Mac session's
  `gh` login, which is his).
- Keep the Mac on mains power and awake while anything runs.
- Answer the comment in the summary doc.

Sections 7 to 9 below were written on 4 Oct while the comparison was still running; `docs/LAB_STATE.md`
and the files under `docs/results/` on the integration branch supersede their numbers and their plan.

**Live sources** (check them; they beat this section when they disagree):

| Question | Live source |
|---|---|
| The whole state in one file | `docs/LAB_STATE.md` on the integration branch (the lab-code owner updates it at every milestone; newest state wins) |
| Everything below in one command | `python handoff_state.py --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs` from any clone at the integration branch head (read-only; since `28a8a37` it finds `genemila_scale_logs` beside the checkout or under `~/Documents/Mila/Gene-Mila`, else pass `--logs DIR`; `--fetch` compares against the remote first, `--json` for machines; `--ledger FILE` if the shared ledger is elsewhere). Prints how far your clone is ahead of or behind the integration branch; every run directory with arm, workers, seed, code and state (finished; in progress with minutes to its deadline; killed before its summary; excluded `_contaminated` / `_interrupted`; planner changed or lost) and headline numbers; ledger totals per provider and role; a WARNING listing paid runs whose `budget.ledger` is not the shared ledger (their spend does not count toward the cap); live `run_research.py` processes; the STOP file; the head of `STATE.md` and the tail of `progress.md` |
| What is running on the Mac, and what comes next there? | `~/Documents/Mila/Gene-Mila/genemila_scale_logs/STATE.md` (what is running, every run directory and its status, open decisions, exact next commands; written on the Mac by whoever runs there), `tail -n 30 .../progress.md` (the driver's step log), `pgrep -fl run_research.py` |
| How much DeepSeek money is spent? | `sqlite3 ~/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite "SELECT provider, ROUND(SUM(cost_usd),2) FROM spend GROUP BY provider"` |
| What did a run find? | `runs/<run>/summary.md` and `summary.json` (`best`, `generalization_query_only`, `llm_usage`, `completed_by_proposer`, `split_id`) |
| Who holds which task? | open issues titled `Claim:`, open pull requests |
| What changed in the code? | `git log origin/claude/autonomous-research-system-3k435s` |

## 2. Where things are

| What | Where |
|---|---|
| Repository (public since 2026-10-11, so nothing secret in any branch) | `https://github.com/andresloak100/gene-mila` |
| Integration branch (pull requests go here; there is no `main` yet) | `claude/autonomous-research-system-3k435s` |
| Main checkout on Andres's Mac: real data, runs (the key is stored nowhere on the Mac). **Don't touch its files or git state** | `~/Documents/Mila/Gene-Mila/gene-mila` (moved there from `~/Documents/Mila/Gene-Mila/gene-mila` on 2026-10-11 after the paid Norman run; a shortcut stays at the old name) |
| Its Python environment | `~/Documents/Mila/Gene-Mila/gene-mila/.venv` |
| Data bundle in use (gitignored) | `data/adamson_cf/` in the main checkout |
| Runs (gitignored) | `runs/<run>/` in the main checkout |
| Shared spend ledger, cumulative across all runs | `runs/spend_ledger.sqlite` in the main checkout |
| Comparison driver: state, progress, stop switch | `~/Documents/Mila/Gene-Mila/genemila_scale_logs/` (`STATE.md`, `progress.md`; a file named `STOP` halts the driver after its current step; the driver script is `tools/scale_seq.sh` on the lab branch, no key inside) |
| Raw data | scPerturb archive on Zenodo, record 13350497: `https://zenodo.org/records/13350497/files/<file>?download=1` |
| CellForge | paper arXiv 2508.02276; code `https://github.com/gersteinlab/CellForge` (it has no evaluation code; we rebuilt the metrics from the paper) |
| Evaluation package | `https://github.com/ArcInstitute/cell-eval` |

The Claude session on the Mac is refused git pushes by its own permission system; `gh` there is
signed in as `andresloak100` with repo scope, so another agent working on the Mac should try to push.
Until someone there can, results reach the repository when an agent with push access commits the
files the Mac produced, exactly as they are on disk.

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
cd ~/Documents/Mila/Gene-Mila
git clone https://github.com/andresloak100/gene-mila.git gene-mila-<your-name>
cd gene-mila-<your-name>
git checkout -b <your-name>/<topic> origin/claude/autonomous-research-system-3k435s
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
# data: either point every run at the main checkout's bundle, read-only (runs write only into their
# own run directory):   --set run.data_dir=$HOME/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf
# or copy it once:
mkdir -p data && cp -R ../gene-mila/data/adamson_cf data/     # a copy; never modify the original
export LEDGER="$HOME/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite"
nice -n 19 python -m pytest -q
```

Your runs then land in your clone's `runs/`, away from the comparison; `run.data_dir` (since `1479ae9`)
is resolved to an absolute path, so the main checkout's bundle can be used in place. Off the Mac you
can do all code work; real runs need the bundle copied over (it contains private labels, so treat the
copy like the original) and network access to `api.deepseek.com`.

## 5. Run the lab

Every script defaults to the newest run under `runs/`; pass `--run runs/<run>` to choose one.

```bash
# free: scripted planner, mock workers (no LLM, no money); only when the Mac's driver is idle
python run_research.py --dataset adamson_cf --minutes 5 --workers 2 \
  --planner-provider scripted --worker-provider mock --run-dir runs/<your-name>_smoke \
  --set run.data_dir=$HOME/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf   # or omit, with data/ copied

# paid: DeepSeek plans and implements; only with Andres's approval and amount, never next to another paid run
# (a Claude-planned run, Claude sessions only while usage allows, uses --planner-provider claude_cli
#  --planner-model opus --set planner.fallback=deepseek:deepseek-v4-pro instead of the two planner flags below)
python run_research.py --dataset adamson_cf --minutes 20 --workers 4 --set run.seed=0 \
  --planner-provider deepseek --planner-model deepseek-v4-pro \
  --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek=<cap, at most 14> \
  --set budget.max_total_usd=<worker cap> --set budget.max_planner_usd=<planner cap> \
  --run-dir runs/<your-name>_<topic>_r0

# warm start from an earlier run on the same split
python run_research.py ... --continue-from runs/<earlier run>

python handoff_state.py               # the whole checkout: git, runs, ledger, processes, progress.md
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

## 6. Handing over

Starting a session (any agent):
1. `git fetch` and read section 1 of this file on the integration branch, the open `Claim:`
   issues and pull requests, and `progress.md` on the Mac.
2. Pick the next unclaimed task (section 8) or continue a stalled one: comment on its claim issue
   that you are taking it over, and branch from its pull request's head into a branch of your own.
3. Add yourself to "Active agents" in section 1 and push that change.

Stopping, or expecting to run out of tokens soon:
1. Push your branch, even if the work is half done, and say in the pull request description what
   works, what doesn't, and the exact next command.
2. Update section 1: move yourself out of "Active agents" (or mark "stopped at <time>"), update
   "In flight" and "Next", and push.
3. Leave nothing running that nobody owns. A run you started either finishes on its own with
   its `summary.json`, or section 1 says where it is and when it ends.

## 7. Results so far (Adamson, CellForge's split)

Primary metric `pearson_delta`: per held-out perturbation, the Pearson correlation of predicted and
true expression change across genes, averaged. "Visible" is what the agents select on; "held-out"
is the sealed query-only set, CellForge's test perturbations.

Starting model (OLS on three baseline features): 0.556 visible, 0.520 held-out.
Free no-LLM control on the old code: 0.571 / 0.554, identical over six seeds and finished after
about two minutes, so it is a fixed recipe and gives no noise estimate. On the current code
(`runs/newcode_control_r0` to `r5`, 2026-10-04) it scores 0.510 visible / 0.553 held-out, identical
over six runs, 23 experiments per run, still ending after about two minutes and keeping no ensemble.
Visible scores are not comparable across code versions: selection now averages 67 perturbations (the
visible set plus out-of-fold training perturbations) instead of 17, which is why the tables separate
code versions into arms. `schedule.exploit_depth` (`9044ece`)
added deeper deterministic search tiers, but the rerun `runs/newcode2_control_r0` still exhausted its
search in under three minutes (126 experiments, held-out 0.553, no better model), so the other five
reruns were skipped: the control is a fixed-recipe reference arm, and filling 20 minutes needs a source
of new features that only the agents provide.

Worker-scaling comparison, code `2492e11`, Opus planner, DeepSeek workers, 20 minutes each:

| workers | seed | completed experiments | best visible | best held-out | experiments / hour | DeepSeek $ |
|---|---|---|---|---|---|---|
| 1 | 0 | 82 | 0.627 | 0.544 | 261 | 0.19 |
| 1 | 1 | 93 | 0.619 | 0.589 | 291 | 0.17 |
| 4 | 0 | 159 | 0.629 | 0.601 | 486 | 0.46 |
| 4 | 1 | 112 | 0.609 | 0.604 | see note | 0.22 |
| 8 | 0 | 280 | 0.637 | 0.585 | 855 | 0.71 |
| 8 | 1 | 275 | 0.651 | 0.583 | 804 | 0.82 |
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
   session and the Mac's driver (section 1). Don't duplicate it.
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
  `--run-dir ~/Documents/Mila/Gene-Mila/gene-mila/runs/<run name>` so the comparison's runs stay
  together; the main checkout's files and git state stay untouched;
- the seed-1 repeats `scale_w8_r1` and `scale_w16_r1` run on code `2492e11` with the Opus planner,
  `--set run.seed=1`, worker caps $2 and $3 and `budget.cumulative_usd.deepseek=10`. They need the
  Claude CLI, so they wait while Andres's Claude usage is exhausted; that code has no failover, so
  one whose planner falls back to the scripted planner is renamed `_contaminated`;
- the planner check on the current code, 4 workers, seeds 0 and 1: `newcode_ds_w4_r*` with
  `--planner-provider deepseek --planner-model deepseek-v4-pro --set budget.max_total_usd=2.5`, and
  `newcode_opus_w4_r*` with `--set budget.max_total_usd=1.5 --set planner.fallback=deepseek:deepseek-v4-pro`,
  both with `budget.cumulative_usd.deepseek=15`; `python analyze_run.py --run <dir>` after each;
- then `scaling_report.py` and `results_table.py` over every `scale_*` and `newcode_*` directory
  except `_contaminated` and `_interrupted`;
- the driver script is `tools/scale_seq.sh` (`014daeb`, committed verbatim from the Mac's
  `genemila_scale_logs/scale_seq.sh`; no key inside: `DEEPSEEK_API_KEY` must be in the starting process's
  environment or it halts; DeepSeek-only ledger gate at $14; a Claude CLI probe before each Opus-planned
  run, with the DeepSeek-planned runs first when the window is out; a contamination check that renames
  an old-code run whose planner fell back). Start it detached,
  `nohup setsid caffeinate -i -s bash scale_seq.sh > ~/Documents/Mila/Gene-Mila/genemila_scale_logs/driver.log 2>&1 &`,
  with the key as a process variable; it appends to `progress.md`, waits for any other lab run on the
  machine to finish before each start, and stops when a `STOP` file appears. Update `STATE.md` before
  and after.
