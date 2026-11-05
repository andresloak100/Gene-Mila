# Block U: CellForge's own agent pipeline, run by us on our data, with DeepSeek

Written 2026-11-04 by the claude-mac session (claim [#111](https://github.com/andresloak100/Gene-Mila/issues/111)),
on Andres's words of 4 November: "why dont you copy cell forge and run it compare which agentic flow is better if
theirs or ours" and "run it with the deepseek agents". The cap below still waits for his written confirmation of
the amount (AGENTS.md, Money).

## What and why

Our CellForge Table 1 (`docs/results/cellforge_table1_ours/table.md`) has every row for Adamson and Norman except
CellForge itself: its paper numbers are on a split and preprocessing nobody can reproduce, so they sit beside ours
marked not comparable. Block U removes that gap the only honest way: run CellForge's published pipeline
(gersteinlab/CellForge, commit `6585ff9`, the one `docs/comparison/cellforge_notes.md` describes) on the same
exported training data our GEARS and linear baselines used, let it design, write and train its model, have that
model predict our sealed held-out perturbations, and score the predictions once with `tools/cellforge_bridge.py`,
exactly as GEARS was scored. The comparison is then agent flow against agent flow on one split: CellForge's
multi-agent design-and-code pipeline producing a deep model, against Gene-Mila's planner-and-workers producing
features for a ridge model. Both are driven by the same LLM, DeepSeek v4-pro, so the LLM is not the difference.

CellForge's code is not changed. Two things of ours sit around it:

- **A spend proxy** (`docs/mac/block_u/deepseek_proxy.py`): a local pass-through in front of `api.deepseek.com`.
  CellForge's own DeepSeek client (`DEEPSEEK_BASE_URL`) and the Codex coding agent (provider `base_url`) both point
  at it. It forwards every request unchanged, reads the `usage` block of every reply, prices it with the lab's peak
  rates (`configs/default.toml`, `[pricing."deepseek-v4-pro"]`), appends one line per call to a JSONL ledger, and
  answers HTTP 402 to everything once the block cap is reached. It never logs headers or bodies. CellForge does not
  write to the shared `spend_ledger.sqlite`, so `handoff_state.py` will show block U as spend that bypasses the
  ledger; the proxy ledger is its record, and `block_u_cap.txt` says how much it may spend.
- **A Codex wrapper** (`docs/mac/block_u/codex_deepseek.sh`): CellForge generates code only through OpenAI's Codex
  CLI. Codex 0.166 speaks OpenAI's Responses API; DeepSeek serves that API natively (`POST /responses`, models
  `deepseek-v4-pro` and `deepseek-flash`). The wrapper adds the provider override that points Codex at the proxy and
  passes CellForge's own arguments through untouched. Codex's user config is ignored by CellForge's own flag.

## Design

| | |
|---|---|
| Code | CellForge `6585ff9` at `~/Documents/Mila/Gene-Mila/cellforge-6585ff9`, env `~/cellforge_env` (Python 3.12, torch 2.15, MPS available); Codex CLI 0.166.0 at `~/.npm-global/bin/codex` |
| LLM | `MODEL_NAME=deepseek-v4-pro` for task analysis, method design and the expert discussion; `CODEX_MODEL=deepseek-v4-pro` for code generation and repair. CellForge's defaults otherwise (3 refinement rounds, 6 discussion rounds, 4 experts, 120k-token design budget, up to 5 repair rounds) |
| Data | the exports the baselines used: Adamson `~/cellforge_adamson_export_corrected_20261028` (40,890 training cells, 2,055 genes), Norman `~/cellforge_norman_export`. Each holds training cells only, the held-out perturbation names and `TASK.md`, the contract CellForge is given as its task |
| Split | CellForge makes its own development split of our *training* perturbations (`--split-seed`, default 42, 20% OOD, 10% val). It never sees a sealed label: the sealed set is scored only by the bridge, once per run |
| Compute | the Mac, `--executor local`, one worker, `nice -n 19`, under `caffeinate`. The generated model trains on CPU or MPS. Each phase has a wall-clock limit (code generation 3 h, autorun 6 h, the rest 1 h) |
| Held-out predictions | CellForge's autorun stops at validation metrics on its own split. Step 5 asks the same Codex agent, with a fixed prompt (`docs/mac/block_u/heldout_prompt.md`), to add `predict_heldout.py` to the generated code: fit the final model on all training cells and write `predictions.npz` as `TASK.md` specifies. The prompt, transcript and script are receipts. This is still CellForge's agent writing CellForge's model; nothing is hand-fixed |
| Scoring | `tools/cellforge_bridge.py score` from the lab venv, `--versus` the same matched lab runs the GEARS readings used (`newcode_opus_w4_r0` for Adamson, `norman_ds_from_n2_w4_r1` for Norman), once per run |
| Runs | run 1: Adamson, CellForge split seed 42. Further runs (Norman; seeds 0, 2, 3 for mean ± sd) only after run 1's cost is known, each on Andres's words |

Order of operations for one run (`docs/mac/block_u/block_u_run.sh DATASET NAME SEED`):
probe (one tiny Codex call through the proxy, proving the Responses path) → task_analysis → method_design →
code_generation → autorun (local) → predict_heldout → score. Every step writes `NAME.command.txt`, `.log`, `.exit`
and `.runtime.json` under `docs/results/cellforge_ours/<run>/`, plus the proxy ledger slice for the run and the
generated code and plans copied from the workspace.

## Money

- Cap for run 1: **$15 at the proxy** (peak v4-pro rates, so an over-estimate of what DeepSeek bills). CellForge's
  own figures are 40–80k prompt and 200–400k completion tokens per end-to-end run; Codex's agent loop resends its
  context every turn, mostly as cache hits at $0.044 per million. Expected $2–8; the cap is the hard stop, enforced
  by the proxy, not by any agent.
- `docs/mac/block_u/block_u_cap.txt` holds `CAP_USD START_TIME`; the run script refuses to start unless it exists.
- No other paid run on the Mac while block U runs (AGENTS.md: never two paid runs at once). The lab's ledger is not
  touched; the proxy ledger `~/Documents/Mila/Gene-Mila/cellforge_runs/proxy/block_u_ledger.jsonl` is the spend
  record, copied into the receipts. Andres is asked to read the DeepSeek console before and after.
- The key comes from `$API_KEY` in Andres's shell into the run's process environment only, as `DEEPSEEK_API_KEY`
  and `CODEX_API_KEY`. Nothing writes a `.env` file. Logs are scanned for key-like strings before they are committed.

## Readings, fixed now

1. Sealed pearson_delta and CellForge's six metrics for the CellForge-built model, one row
   "CellForge pipeline, run by us, DeepSeek v4-pro (block U)" in `docs/results/cellforge_table1_ours/table.md`, with
   n = 1 until more seeds exist, and the paired reading against the matched lab run, as for GEARS.
2. Cost and wall time of the CellForge run from the proxy ledger and the receipts, beside the lab's $0.42–1.07 per
   20-minute run in block T.
3. What CellForge built: the research plan, the architecture, parameter count, epochs, and whether its code ran
   first time or needed repair rounds, all from its own workspace files.

## What this does not claim

- One run is one run. No "CellForge beats" or "loses to" claim from n = 1; seeds 0, 2, 3 come later if the cost
  allows.
- CellForge's paper numbers stay not comparable. Block U compares pipelines on our split; it does not reproduce
  their table.
- If CellForge's agent cannot produce `predictions.npz` within the repair rounds and the limits, the run is reported
  as failed with its receipts, not patched by hand into a result.

## Notes after the start

- 2026-11-05: the first Norman run (`cf_norman_s42`) finished analysis, design and code generation ($0.78 by the
  proxy), then CellForge's autorun trained the agent's script on the CPU (a 4-layer transformer over 512 gene
  tokens; the script looks only for CUDA) and the process reached 46.9 GB of memory on the 24 GB Mac (macOS
  JetsamEvent reports of 03:10:57 and 03:13:15 UTC name pid 21314, `python3.12`, as the largest process). At
  03:13:27 UTC the session that had launched the chain ended and every block U process received SIGTERM with it;
  the proxy ledger stood at $2.91. Andres (05 Nov, "Restart, 12 GB cap"): the chain restarts with a resource cap
  beside the wall-clock one: a step whose process tree exceeds 12 GB resident is killed, the run is marked
  failed with the snapshot in `<step>.memkill.txt`, and the chain goes on. A run that needs more memory than the
  machine has is an outcome of the comparison and is reported as such, never patched. The chain is relaunched in
  its own process session so a session ending cannot kill it again. The first attempt's autorun receipts are
  kept as `autorun_attempt1_killed.*` in `docs/results/cellforge_ours/cf_norman_s42/`.
