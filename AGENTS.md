# AGENTS.md: read this before you change anything

This file is for every coding agent that works in this repository, whatever model or product it
runs on. It holds the rules. [`HANDOFF.md`](HANDOFF.md) holds the current state, the paths and
commands, and the open work. Read both, then `README.md`, `docs/ARCHITECTURE.md` and
`configs/default.toml`.

## The project

Gene-Mila is an autonomous laboratory. LLM research agents discover features for deliberately
simple CPU models (ridge, lasso, OLS) that predict how gene expression changes under a genetic
perturbation the model has never seen. A Python controller, never an LLM, owns the deadline,
scheduling, spend caps and persistence, and stops everything at the wall-clock budget. The
benchmark is CellForge's (arXiv 2508.02276): its datasets and splits (Adamson first, then Norman
and Srivatsan), its metrics (MSE, PCC and R² on all genes and on the top-20 DE genes), VCWorld's
DE and direction metrics, and Arc Institute's cell-eval for finalists.

The owner is Andres (GitHub `andresloak100`). He wants a paper-grade result: every number must
be reproducible from a run directory and comparable with the others.

## Who else works here

Several Claude sessions work on this project at the same time, coordinated in Andres's Claude
project. You cannot message them. They read this repository (branches, pull requests, issues,
commits), and Andres relays between you and them.

| Owner | Owns | Branch |
|---|---|---|
| Claude, "Autonomous research system" | the lab code, the runs on Andres's Mac, `docs/results/` | `claude/autonomous-research-system-3k435s`, the integration branch (there is no `main` yet) |
| Claude, "Repo description design" | `README.md`, `docs/assets/`, the GitHub About box, `CLAUDE.md`, `tools/readme_check.py` | `claude/repo-description-design-bro3vo` (draft PR #1) |
| You | the tasks Andres gives you | `<your-name>/<topic>`, branched from the integration branch |

## Hard rules

### Secrets

- The DeepSeek key exists only as the environment variable `DEEPSEEK_API_KEY`. Never print,
  echo, log, commit or paste it, never write it to a file, never put it on a command line, and
  never ask anyone to send it to you. The code reads it from the environment
  (`genemila/providers/openai_compat.py`). The same goes for every other API key and GitHub token.
- Never commit `data/`, `runs/`, `*.h5ad` or `.env` (all are in `.gitignore`; never `git add -f`).

### Money and usage

- Every paid API call comes out of Andres's money. DeepSeek has a cumulative cap of **$15 for
  the whole project**, enforced through the shared spend ledger, and runs stop at **$14**.
  A paid run needs Andres's approval in his own words, with an amount. Runs with
  `--planner-provider scripted --worker-provider mock` cost nothing and need no approval.
- Always pass `--planner-provider` explicitly. The default planner is the Claude CLI (Opus),
  which uses Andres's Claude subscription, the thing this handoff is meant to save. If the
  Claude CLI is not available, the lab falls back to the scripted planner with only a warning,
  so the run would be mislabelled.
- Every paid run points at the shared ledger and carries its own caps:
  `--set budget.ledger=<absolute path to the shared ledger> --set budget.cumulative_usd.deepseek=<cap>
  --set budget.max_total_usd=<worker cap> --set budget.max_planner_usd=<planner cap>`.
  Never change the $0.25 defaults in `configs/default.toml`, and never edit or reprice the ledger.
- Never run two paid runs at once. Each run reads the ledger only when it starts, so runs that
  overlap can overshoot the cap together.

### Andres's Mac (the only machine with the real data and the key)

- A detached driver there is running the worker-scaling comparison. Don't kill it, don't create
  its `STOP` file, and don't touch `runs/scale_*`, `runs/newcode_*` or
  `~/Documents/Loak-documents/genemila_scale_logs/` (read them, nothing more) unless Andres asks.
- Never edit files, commit, pull, check out or switch branches in the main checkout
  `~/Documents/Loak-documents/gene-mila`. The driver's next run uses whatever code is there.
  Work in your own clone (HANDOFF.md, section 4).
- While the driver is running, start no lab runs on the Mac: CPU contention would corrupt the
  comparison's timing measurements. Reading, editing and `nice -n 19 python -m pytest -q` are fine.

### Git

- Branch from `claude/autonomous-research-system-3k435s` and open a draft pull request into it.
  Never push to a `claude/*` branch, never force-push, rebase or amend a shared branch, and never
  merge your own pull request: Andres merges.
- One topic per pull request. The description says what changed, the commands you ran, and
  every number together with the run directory it came from.
- `python -m pytest -q` must pass before every push.

### Scientific integrity

- Don't change these without Andres's explicit agreement: `genemila/benchmark/` (evaluator,
  metrics, query-only oracle, DE reference, results table), the split logic, the guard
  (`genemila/guard.py`), `docs/results/cellforge_table1.json`, and existing data bundles under
  `data/`. If you find a bug there, describe it in an issue and stop.
- Never read `data/*/private/` or `data/*/splits.json`, and never use held-out (val2 or test)
  labels or sealed scores to choose features, models or hyperparameters. Only the lab's capped
  `QueryOracle` scores the sealed set, at the end of a run. Selecting on it would turn every
  reported number into a test-set-tuned one.
- Compare runs only within the same bundle and split (`split_id` in `summary.json`). Warm starts
  (`--continue-from`) only on the same split.
- Report each arm as mean ± sd over its repeats, never one lucky run, and claim no difference
  that sits inside run-to-run noise. Numbers decide, never an LLM's judgement.
- Every number you report comes from a run with a `summary.json`; cite the run directory. Never
  delete or overwrite a run directory. A broken run is renamed with the suffix `_contaminated`
  and left out of tables.
- CellForge's published numbers cannot be reproduced under any metric definition tried, so
  their rows stay in our tables marked not comparable.

## How to coordinate

1. **Look first.** Read open pull requests, open issues and recent commits on the integration
   branch, and `progress.md` on the Mac, so you don't redo or collide with work in flight.
2. **Claim the task.** Open a GitHub issue titled `Claim: <task>` naming the files you will
   touch, before you start. If another owner's files are on the list, say so there.
3. **Keep progress where others can read it.** Update the issue as you go, then the pull
   request description. The Claude sessions read GitHub; they cannot read your chat.
4. **Ask Andres for decisions** about spend, scope or protected code, and wait for his answer.
   Don't decide them for him.
5. **Hand back.** When a task is done, the pull request carries the result, and you send Andres
   three lines he can pass on to the Claude project: what changed, the numbers with their run
   directories, and what is next.
6. **Keep this file and HANDOFF.md true.** They are the memory shared between agents. When you
   change the state they describe, update them in the same pull request and re-date the snapshot.
