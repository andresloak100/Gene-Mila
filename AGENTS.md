# AGENTS.md: read this before you change anything

This file is for every agent that works in this repository: the project's Claude sessions,
Astra (a ChatGPT agent), and any other coding agent. Whichever of them still has tokens
picks up the work where another stopped, so all of them follow the same rules and keep the same
state. The rules are here. [`HANDOFF.md`](HANDOFF.md) holds the shared state (section 1, kept
current by whoever is working), the paths and commands, and the open work. Read both, then
`README.md`, `docs/ARCHITECTURE.md` and `configs/default.toml`.

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

## Who works here

The repository is the only place every agent can read, so it is the single source of state.
Claude sessions also talk in Andres's Claude project, which Astra cannot see; Astra talks to
Andres in ChatGPT, which Claude cannot see. Anything another agent needs goes into this
repository: `HANDOFF.md` section 1, GitHub issues and pull requests.

| Agent | Owns | Branches |
|---|---|---|
| Claude, "Autonomous research system" | the lab code, the runs on Andres's Mac, `docs/results/` | `claude/autonomous-research-system-3k435s`, the integration branch (there is no `main` yet) |
| Claude, "Repo description design" | `README.md`, `docs/assets/`, the GitHub About box, `tools/readme_check.py` | `claude/repo-description-design-bro3vo` (draft PR #1) |
| Other Claude sessions | the tasks Andres gives them | `claude/<topic>` |
| Astra (ChatGPT) | the tasks Andres gives it | `astra/<topic>` |

When one agent runs out of tokens, another may take over its task: read its claim issue, its
pull request and `HANDOFF.md` section 1, then continue on a branch of your own.

## Hard rules (for every agent)

### Secrets

- The DeepSeek key exists only as the environment variable `DEEPSEEK_API_KEY`. Never print,
  echo, log, commit or paste it, never write it to a file, never put it on a command line, and
  never ask anyone to send it to you. The code reads it from the environment
  (`genemila/providers/openai_compat.py`). The same goes for every other API key and GitHub token.
  On the Mac the key is stored in no startup file (the write to `~/.zshenv` was refused): the
  Claude session there passes it to each run as a process variable, so any other agent's paid run
  needs Andres to put the rotated key into that agent's environment first.
- Never commit `data/`, `runs/`, `*.h5ad` or `.env` (all are in `.gitignore`; never `git add -f`).

### Money and usage

- Every paid API call comes out of Andres's money. DeepSeek has a cumulative cap of **$15 for
  the whole project**, enforced through the shared spend ledger, and runs stop at **$14**.
  A paid run needs Andres's approval in his own words, with an amount. Runs with
  `--planner-provider scripted --worker-provider mock` cost nothing and need no approval.
- Always pass `--planner-provider` explicitly. The default planner is the Claude CLI (Opus),
  which uses Andres's Claude subscription. Since `9044ece` the lab never falls back to the
  scripted planner on its own: a run whose planner is unusable, with no usable entry in
  `planner.fallback`, refuses to start (exit 2).
  - Astra and other non-Claude agents never use the Claude CLI planner.
  - Claude sessions use it only for runs whose arm needs it (the comparison's Opus-planned runs),
    and every Claude-planned run on the current code carries
    `--set planner.fallback=deepseek:deepseek-v4-pro`.
  - Once Claude usage is out, everyone uses the DeepSeek planner:
    `--planner-provider deepseek --planner-model deepseek-v4-pro`.
  - `planner.fallback` is an ordered chain of `provider:model` entries, empty by default:
    `--set planner.fallback=deepseek:deepseek-v4-pro`, or
    `--set 'planner.fallback=["deepseek:deepseek-v4-pro","scripted"]'` (`scripted` only when written
    out). On a usage limit, an API error, a budget halt or three unparseable plans in a row, the
    run switches to the next entry for the rest of the run and logs a `planner_switch` event; when
    the chain is exhausted it continues without a planner (the queue drains, the exploit engine
    keeps proposing) and logs `planner_exhausted`.
- Every paid run points at the shared ledger and carries its own caps:
  `--set budget.ledger=<absolute path to the shared ledger> --set budget.cumulative_usd.deepseek=<cap>
  --set budget.max_total_usd=<worker cap> --set budget.max_planner_usd=<planner cap>`.
  Never change the $0.25 defaults in `configs/default.toml`, and never edit or reprice the ledger
  (it was repriced once, on 2026-10-04 with Andres's approval, from $0.2579 to $0.0219 after a
  DeepSeek flash pricing correction; backup `runs/spend_ledger.sqlite.bak`).
- Never run two paid runs at once, whoever starts them. Each run reads the ledger only when it
  starts, so runs that overlap can overshoot the cap together.

### Andres's Mac (the only machine with the real data)

- The worker-scaling comparison runs there, when it runs, as a detached driver
  (`python handoff_state.py`, or `STATE.md` and `progress.md` under
  `~/Documents/Loak-documents/genemila_scale_logs/` and `pgrep -fl run_research.py`, say whether one
  is going; HANDOFF.md section 1 says what is planned).
- Whoever runs anything on the Mac updates `STATE.md` there (what is running, every run directory
  and its status, open decisions, the exact next commands); whoever can push mirrors it into
  HANDOFF.md section 1. The Claude session on the Mac is refused git pushes by its own permission
  system; `gh` there is signed in as `andresloak100` with repo scope, so another agent working on
  the Mac should try to push. Don't kill it, don't
  create its `STOP` file, and don't touch `runs/scale_*`, `runs/newcode_*` or that log directory
  (read them, nothing more) unless Andres asks.
- Never edit files, commit, pull, check out or switch branches in the main checkout
  `~/Documents/Loak-documents/gene-mila` unless you own the runs there (the "Autonomous research
  system" session, or whoever Andres hands them to). The driver's next run uses whatever code is
  there. Everyone else works in their own clone (HANDOFF.md, section 4).
- While the driver is running, start no other lab runs on the Mac: CPU contention would corrupt
  the comparison's timing measurements. Reading, editing and `nice -n 19 python -m pytest -q`
  are fine.

### Git

- Push only to your own branches, branched from `claude/autonomous-research-system-3k435s`,
  and open a draft pull request into it. Never push to another agent's branch, never force-push,
  rebase or amend a shared branch, and never merge your own pull request: Andres merges.
- The one exception: a commit that changes only `HANDOFF.md` section 1 may go straight to the
  integration branch (`git pull` first, a plain push, never forced), so the shared state never
  waits on a merge.
- One topic per pull request. The description says what changed, the commands you ran, and
  every number together with the run directory it came from.
- `python -m pytest -q` must pass before every push of code.

### Scientific integrity

- Protected: `genemila/benchmark/` (evaluator, metrics, query-only oracle, DE reference, results
  table), the split logic, the guard (`genemila/guard.py`), `docs/results/cellforge_table1.json`,
  and existing data bundles under `data/`. Other agents don't change them; if you find a bug
  there, describe it in an issue and stop. The lab-code owner (the "Autonomous research system"
  session, under Andres's standing delegation) changes them only with Andres's agreement and says
  so in the pull request.
- Never read `data/*/private/` or `data/*/splits.json`, and never use held-out (val2 or test)
  labels or sealed scores to choose features, models or hyperparameters. Only the lab's capped
  `QueryOracle` scores the sealed set, at the end of a run. Selecting on it would turn every
  reported number into a test-set-tuned one.
- Compare runs only within the same bundle and split (`split_id` in `summary.json`). Warm starts
  (`--continue-from`) only on the same split.
- A run whose planner changed part-way is its own arm in every table, never pooled with the
  clean runs of its configured arm. `summary.json["planner"]` records it (`configured`,
  `fallback`, `used`, `switches`, `mixed`), `summary.md` prints "PLANNER CHANGED DURING THE RUN",
  and the results table, the scaling report and `handoff_state.py` label it by the planners that
  produced its plans, spelled with `->`, for example
  `claude_cli:opus -> deepseek:deepseek-v4-pro planner`; a run that lost every planner gets the
  suffix `(lost its planner)`. Runs on the old code `2492e11` have no failover: one whose Claude
  planner fell back to the scripted planner is renamed `_contaminated` and left out.
- Report each arm as mean ± sd over its repeats, never one lucky run, and claim no difference
  that sits inside run-to-run noise. Numbers decide, never an LLM's judgement.
- Every number you report comes from a run with a `summary.json`; cite the run directory. Never
  delete or overwrite a run directory. A broken run is renamed with the suffix `_contaminated`
  and left out of tables.
- CellForge's published numbers cannot be reproduced under any metric definition tried, so
  their rows stay in our tables marked not comparable.

## How to coordinate (every agent, every session)

1. **When you start, read the state.** `HANDOFF.md` section 1 on the integration branch,
   `python handoff_state.py --fetch` (one command: how far your clone is behind the integration
   branch, every run with its state, the ledger and any paid run that bypasses it, live processes,
   `STATE.md` and the tail of `progress.md`), open `Claim:` issues, open pull requests and recent
   commits. Don't redo or collide with work someone else holds.
2. **Claim the task.** Open a GitHub issue titled `Claim: <task>` naming the agent, the branch and
   the files you will touch, before you start. If another owner's files are on the list, say so
   there. Taking over a stalled task: comment on its claim issue that you are taking it over.
3. **Keep the state current.** Update `HANDOFF.md` section 1 (who is active, what is in flight,
   what comes next), and `STATE.md` on the Mac when you work there, when you start, after each
   milestone, and **before you stop or as soon as you
   expect to run out of tokens**: write the exact next step so the next agent can continue
   without asking. Put task progress in the claim issue and the pull request description.
4. **Ask Andres for decisions** about spend, scope or protected code, and wait for his answer.
   Don't decide them for him. Record his answer in section 1 or the claim issue, with the date,
   so the other agents know it.
5. **Finish cleanly.** The pull request carries the result; close or update the claim issue;
   section 1 says what is next.
6. **Keep this file and HANDOFF.md true.** When you change what they describe, update them in
   the same pull request.
