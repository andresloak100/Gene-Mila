# Picking up on the Mac

Written 2026-10-11 21:35 UTC by the agent that ran the experiments on Andres's Mac. It says what another agent needs
in order to continue from this machine. The protocol and results live in the repository (`docs/LAB_STATE.md`,
`docs/NORMAN_PLAN.md`, `docs/PLAN_AFTER_N4.md`, `HANDOFF.md`); the running log of what happened here is
`docs/mac/STATE.md` (the same file as `genemila_scale_logs/STATE.md` on the Mac).

## Where things are on the Mac

Everything is under `~/Documents/Mila/Gene-Mila/`:

| folder | what |
|---|---|
| `gene-mila` | main checkout of the lab branch `claude/autonomous-research-system-3k435s`, with `.venv`, `data/` (bundles `adamson_cf`, `norman`) and `runs/` (every run and the shared `spend_ledger.sqlite`) |
| `gene-mila-076282c` | worktree pinned to code 076282c, used for the B1 repeats (no `.venv`, no `data/`; commands use the main checkout's interpreter and absolute paths) |
| `gene-mila-2492e11` | worktree of the old code used for the first scaling runs |
| `genemila_scale_logs` | logs, reports, driver scripts, `STATE.md`, this file |
| `data_downloads` | `replogle2022/ReplogleWeissman2022_K562_gwps.h5ad` (8.8 GB) and `NormanWeissman2019_filtered.h5ad` (0.7 GB), both from Zenodo record 13350497, md5s in the reports |

`~/Documents/Mila` itself is a checkout of a different repository (andresloak100/Mila) with uncommitted work of
Andres's; `Gene-Mila/` is listed in its `.git/info/exclude`. Do not touch anything else there. Four symlinks with the
old folder names remain in `~/Documents/Loak-documents`; run configs, bundle manifests and the `.venv`'s `activate`
and console scripts still record that old path and resolve through them. Use `.venv/bin/python -m ...`, which does
not depend on them. Astra's workspace is `~/Documents/Codex/2026-10-08/pl` (read only; its two branches are on GitHub).

## Rules that have bitten

- **Sealed sets.** Never read `data/*/private/` or score on the sealed set outside the lab's own end-of-run queries
  and the pre-specified tools (`tools/sealed_reading.py`, `tools/arm_reading.py`). Report every sealed number whatever
  it shows; choose nothing by it. Adamson's sealed set is worn out; Norman's is the one that still means something.
- **Blinding.** A run's sealed result is opened only after the plan that says how to read it is on GitHub.
- **Money.** Paid runs need Andres's own words. On 2026-10-11 he authorised spending from the $33.01 left in the
  DeepSeek account; the block cap in `docs/PLAN_AFTER_N4.md` is a shared-ledger total of $48. The ledger overstates
  real cost about twofold (ledger $33.97 against DeepSeek's billed $16.98 on 2026-10-11), and is never repriced.
- **Key.** It is in `~/.zshenv` as `API_KEY`. The lab reads `DEEPSEEK_API_KEY`. Start a paid run from a login zsh with
  a shell assignment, `DEEPSEEK_API_KEY="$API_KEY" <command>`, so it never appears on a command line, in a script or
  in a log. Check presence only (`[ -n "$API_KEY" ] && echo set`). Never ask Andres to paste a key; keys pasted in the
  chat earlier should be rotated.
- **STOP file.** `genemila_scale_logs/STOP` makes the drivers refuse to start a paid run. It is in place. Remove it
  only for a run that is approved, and put it back once the run has started.
- **One run at a time.** Timed runs (20 minutes) must not share the CPU with tests, audits or other runs.
- **Power.** The Mac sleeps on battery with the lid closed; start long jobs with `nohup caffeinate -i -s`.
- **Shell.** The default shell is zsh: `sleep` in the foreground may be blocked, `"$VAR:refs"` applies a modifier
  (write `"${VAR}:..."`), and globs that match nothing abort the command.
- **Permissions.** The Mac's permission system sometimes refuses a compound command; run the one command the plan
  names by itself. Pushing to GitHub works from here (new branches, never force, never to the lab branch directly).
- **Determinism.** Every run records `run.hash_seed = 0`; the feature guard refuses `hash()`, `id()` and iteration
  over sets in new plugins. `run.seed` changes the cross-validation folds, so visible scores are comparable only
  within a run.

## How a paid run is started here

`genemila_scale_logs/norman_b1_run.sh <seed>` is the pattern: it refuses to start without a key in its environment,
with the STOP file present, with the run directory existing, with the worktree off its commit, or above the ledger
limit; it writes the run's log next to itself and unsets the key at the end. Start it detached:

    rm ~/Documents/Mila/Gene-Mila/genemila_scale_logs/STOP
    cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs && zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i -s ./norman_b1_run.sh 2 > norman_ds_from_n2_w4_r2.driver.log 2>&1 &'
    touch ~/Documents/Mila/Gene-Mila/genemila_scale_logs/STOP

In the first minute check the warm-start line in the run's log, and in its `config.json` the recorded
`run.external_knowledge`, `run.hash_seed`, seed, providers and caps. When it ends, report exit code, duration, spend
by role from `lab.db` (`llm_calls`), the ledger total, and `summary.json`'s `planner.mixed` and
`planner.exhausted_at_min` before reading anything else.

## How results get to GitHub

A new branch from the lab branch in a temporary worktree, the files copied under `docs/results/` (reports and their
JSON twins) and `docs/mac/<run>/` (`config.json`, `summary.json`, `summary.md`), an md5 list, a scan of every file
for key-shaped strings (`sk-` followed by 16 or more letters or digits) before the push, then a draft pull request
into the lab branch. `push_to_github.sh` in this folder is the first version of that; pull requests 3, 4 and 6 were
made this way. No data, run directories or databases go up.

## Where the science stands (2026-10-11 21:35 UTC)

| dataset | model | sealed pearson_delta |
|---|---|---|
| Adamson | starting baseline | 0.520 |
| Adamson | agent runs without outside data | about 0.60 |
| Adamson | agents' features plus Replogle features, no LLM (`control_replogle3_from_opus_r0`) | 0.646 |
| Norman | additive baseline | 0.713 |
| Norman | scripted control with Replogle (N2) | 0.719 |
| Norman | combined model of the three B1 repeats | 0.723 |

- Adamson's gain came from outside data (the Replogle 2022 K562 screen), not from more agent search.
- On Norman nothing is established above the additive rule pooled; the B1 arm (three DeepSeek repeats continuing N2)
  adds 0.0000 ± 0.0071 to its starting model. The combined model is +0.0041 ± 0.0011 over N2.
- CellForge's published numbers are matched or exceeded on five of six metrics on both datasets under our own
  splits, but their evaluation is not reproducible, so no claim is made.

## What is next

Per `docs/PLAN_AFTER_N4.md`, waiting for the lab-code owner's go:
1. **B2**: a free scripted control on new lab code, then three fresh DeepSeek Norman runs that start from the
   additive rule (seeds 0 to 2), caps `budget.max_total_usd=1.0`, `budget.max_planner_usd=1.5`, cumulative 48, no
   start above a ledger of $45.50.
2. **B3**: a fresh Adamson split (gene mode, gene-frac 0.57 0.19 0.24, seed 20261011, sample-seed 0), a free control,
   then two DeepSeek runs.

The ledger stood at $38.084345 after B1. Nothing is running on the Mac.
