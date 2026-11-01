# Block H: the comparison on Adamson, fixed before any run

Written 2026-10-17 by the lead (the Claude session on claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41))
under `docs/ROADMAP.md` D5 and D6, on Andres's delegation of 16 October. The question and the arms are
`docs/FEATURE_COMPARISON_PROTOCOL.md` (sections 2 to 6) and `docs/GOAL_CRITERIA.md` B.1 and B.2; this file fixes
what runs, in what order, under which caps and checks, and how it is read. **Nothing below has run.** From the first
paid call on, a change is a new dated section at the end, never an edit. Every number in the readings comes from a run
or session directory named here. Scripts: `docs/mac/block_h/` (`block_h_common.sh` holds the paths and checks the others source; `Dockerfile` the
agents' image).

## Question

- **B.1** (`GOAL_CRITERIA.md`): do at least three systems run on the identical task package, three search seeds each,
  the same wall time and dollar cap, and does the one-worker lab row and CellForge's translated ideas join them?
- **B.2**: are every system's features scored by `tools/feature_compare.py` with the same parent, fold seeds and null?
- The arm question underneath (protocol section 1): with the model fixed (one ridge), which system's features make it
  predict better, out of fold on the development tier now, on the fresh test later (ROADMAP D7). No arm claim is made
  from a development tier; the development numbers screen and show spread.

## Arms, all on Adamson, bundle `data/adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`: the clean bundle keeps `data/adamson_cf`'s split, `docs/PLAN_G_CLEAN_ARM.md`; `docs/archive/mac/STATE_20261014.md`, Runs on disk)

| arm | what | runs or sessions | cost |
|---|---|---|---|
| A1 | block G's g1 runs, `runs/adamson_cf_g1_ds_w4_r{0,2,3}` (`docs/PLAN_G_CLEAN_ARM.md`): DeepSeek planner `deepseek-v4-pro`, 4 `deepseek-flash` workers, 20 min, code `baa7dfd` | not re-run | paid in G |
| A1-ablation | block G's g0 runs, `runs/adamson_cf_g0_ds_w4_r{0,2,3}`, the same bundle without the three tables | not re-run | paid in G |
| A2 | the one-worker lab: as A1 with `--workers 1`, the settings of `docs/PLAN_B4_SINGLE_WORKER.md` (no `--continue-from`, `--no-watchdog`, caps `budget.max_total_usd=1.0`, `budget.max_planner_usd=1.5`), code `baa7dfd` from the checkout `gene-mila-baa7dfd`, `runs/adamson_cf_h_a2_ds_w1_r{0,2,3}` | 3 | paid here |
| A3 | an autoresearch-style loop: Claude Code (`claude -p`) on the task package, `program.md` as its prompt, web tools off, `deepseek-v4-pro` through DeepSeek's Anthropic-format route behind the ledger proxy, 20 min; `tools/baselines/run_autoresearch.sh` | 3 | paid here |
| A4 | Biomni's A1 agent on the task package, `source="OpenAI"`, `llm="deepseek-v4-pro"`, no data lake, the ledger proxy as its endpoint, 20 min; `tools/baselines/run_biomni.py` | 3 | paid here |
| C0 | the scripted no-LLM control. Existing: the `@2492e11` runs in `docs/results/scaling.md` (6 identical runs on `data/adamson_cf`, sealed M1 0.554; different knowledge files, so context only). Comparable, free, no approval needed (`AGENTS.md`, Money): `runs/adamson_cf_h_c0_scripted_w4_r{0,2,3}`, the command below | 3 free | $0 |
| C2 | CellForge's ideas translated by us, `docs/comparison/cellforge_c2/` (the `cf_pair_interaction` row is constant on Adamson and is rejected there, as its README says) | 0 | $0 |

Seeds 0, 2 and 3 everywhere (B2's and G's). A coding agent has no seed: for A3 and A4 the seed names the session
(a fresh copy of the package, a fresh process, `--seed <s>` passed to the runner for its own record).

**The task package.** Exported once by Astra (ROADMAP section 6, step 7) with the D5 tool at or after this plan's
commit, into `~/gm_packages/adamson_cf_clean_tables` with its record `~/gm_packages/adamson_cf_clean_tables.export.json`
beside it:
```bash
python tools/export_task_package.py --data <MAIN>/data/adamson_cf_clean_tables --out $HOME/gm_packages/adamson_cf_clean_tables
shasum -a 256 $HOME/gm_packages/adamson_cf_clean_tables/MANIFEST.json $HOME/gm_packages/adamson_cf_clean_tables/program.md
```
The two sha256 lines go on #41 before any session (D5). The package carries the harness tier by default:
`harness/val1.npz`, the visible validation labels the lab's own controller scores every experiment on
(`genemila/lab.py:96` loads `private/val1.npz`; `evaluate_artifact`, lines 378 to 424, and `_combine_visible`, lines
426 to 437, select the alpha and the best model on the mean `pearson_delta` over the visible validation and the
out-of-fold training perturbations together; `genemila/db.py:203-206` takes the highest such score). `evaluate.py`
reports `oof_pearson_delta`, `val1_pearson_delta` and `combined_pearson_delta`, decides keep or discard on the
combined vector with the same noise rule, tells the agent the file is readable (`program.md`), rejects a feature file
whose source names the tier, and `MANIFEST.json` records the tier's sha256 and the rule. So every arm gets the feedback
the lab's agents get, and every arm's final scoring is still out of fold on new fold seeds (B.2) and then the fresh
test. The exporter reads that one private file through the lab's accessor and never val2, the cells or
`splits.json`. Andres's word on the tier (keep or veto, ROADMAP section 7, item 3) is written once into
`block_h/tier.txt` as `harness` or `none`, with his words and date in the dated note below; the export waits for it.
On a veto Astra exports with `--no-harness-val1`, `tier.txt` reads `none`, and the scripts require the package to
match the file either way (`pkg_checks`). With the tier shipped, the visible validation is a seen tier for A3 and A4:
the protocol's V-based paste check does not apply to them, their candidates are chosen on out-of-fold seeds only, and
the fresh test is the one unseen tier (protocol, note of 2026-10-17).

**The runners** (`tools/baselines/ledger_proxy.py`, `run_biomni.py`, `run_autoresearch.sh`, `collect_handback.py`)
are a sibling pull request (branch `wip2/baselines`), not this one; `H_CLONE` must hold them. The scripts here assume
the interfaces of that branch at `b70ae10`, checked against those files on 2026-10-17: `run_biomni.py --package
--proxy --model --minutes --seed --out [--probe]`, refusing a `DEEPSEEK_API_KEY` in its environment, a package inside a
lab checkout, and a proxy URL not starting with `http://127.0.0.1`, `http://localhost`, `http://[::1]` or
`http://host.docker.internal`; `run_autoresearch.sh <package> <proxy url> <minutes> <seed> <out>`, the model from
`BASELINE_ANTHROPIC_MODEL`, the same URL and key refusals, and the proxy's log readable at `$PROXY_LOG` (it tails it for
the first served model within 180 s); `collect_handback.py --out --package --dest`, needing `<out>/run.json`, copying
the accepted kept files to `<dest>/<arm>_r<seed>/` (`arm` is `biomni` or `autoresearch`, from `run.json`) and merging
`<dest>/manifest.json`; the proxy's log, one JSON object per line with `status` (200 forwarded; 0 its own start and
stop rows; 402 a cap refusal; 404 no such route; 502 upstream), `model_served`, `input_tokens`, `cached_tokens`,
`output_tokens`, `cost_usd`, `ts`, forwarding `/v1/chat/completions` and `/anthropic/v1/messages` only, any client
token accepted and replaced, `--listen` loopback only. If that branch changes before it lands, the scripts change with
it in a dated note.

**Isolation (precondition; protocol, fairness control 7).** `check_tools.sh` says which of the two holds:
1. *Docker* (if the Mac has it): image `genemila-h` built once from `docs/mac/block_h/Dockerfile` (Python, the
   package's pinned numpy, scipy and scikit-learn, Biomni, Claude Code and `tools/baselines/` copied in; never
   `genemila/`, `configs/` or a prompt of the lab, protocol controls 6 and 7; no data), an internal Docker network
   `genemila_h` with no route to the internet, and one relay container `h_relay` (`alpine/socat`) on that network and
   on the bridge, forwarding port 8787 to the proxy on the Mac (`host.docker.internal:8787`). The agent container
   mounts the session's package copy, its output directory and the proxy's log (read-only) and nothing else; its only
   route out is the relay, which `--add-host` names `host.docker.internal` inside the container (the runners accept
   that name and refuse any other host). The run line (from `block_h_a4.sh`, `RELAY_IP` read from `docker inspect`
   after the relay starts):
   ```bash
   docker run --rm --name h_agent --network genemila_h --memory 8g --add-host host.docker.internal:$RELAY_IP \
     -v "$W:/work/pkg" -v "$W.export.json:/work/pkg.export.json:ro" -v "$O:/work/out" \
     -v "$L/block_h/proxy/h_a4_r$S.jsonl:/work/proxy.jsonl:ro" -e PROXY_LOG=/work/proxy.jsonl \
     -e OPENAI_API_KEY=proxy -e ANTHROPIC_AUTH_TOKEN=proxy -e HOME=/work/out genemila-h \
     python /lab/tools/baselines/run_biomni.py --package /work/pkg --proxy http://host.docker.internal:8787 \
     --model deepseek-v4-pro --minutes 20 --seed $S --out /work/out
   ```
   `check_tools.sh` verifies, with a throwaway listener on the Mac, that a container on `genemila_h` cannot reach
   `https://api.deepseek.com` and can reach the relay. The proxy listens on the loopback only (it refuses any other
   address), so if Docker Desktop's `host.docker.internal` does not reach a `127.0.0.1` listener on this Mac, Docker
   mode is out and the arms wait for the account.
2. *A second macOS account* that Andres creates (ROADMAP section 7, item 3), holding only the package copy, a
   Python venv with Biomni and the package's requirements at `/Users/<account>/genemila_h_venv` (or `H_ACCOUNT_VENV`)
   and Claude Code on that venv's `bin`, `/usr/local/bin` or `/opt/homebrew/bin`; the proxy runs in Andres's account on
   `127.0.0.1:8787` with its log under `/Users/Shared/genemila_h/proxy/` (readable by the account; it holds no body
   and no token), copied back under `$L/block_h/proxy/` after the session; the arm scripts start the agent with
   `sudo -u <account> -H env -i ...`, so no variable of Andres's environment crosses. The filesystem isolation holds
   (the account cannot read Andres's home); the network one does not, so the proxy log and the transcript scan are the
   check, and the paper says so. The venv is the account's own and persists between sessions (Docker's image does not):
   a weakness of this mode, stated.
Without either, A3 and A4 wait; A2 and C0 can run. The answer is written once into `block_h/isolation.txt` as
`docker`, `account <username>` or `none` (A2 only), with Andres's words and date in the dated note below. In account
mode the chain runs in the foreground of the login shell: `sudo` asks for the password at each session's checks
(its ticket expires between 20-minute sessions) unless `Defaults timestamp_timeout` in `sudoers` covers the chain, and
the checks verify the venv and `claude` before any spend; in Docker mode it runs detached as below.

**The key** stays `API_KEY` in Andres's `~/.zshenv` and reaches only the proxy and the A2 lab run, as
`DEEPSEEK_API_KEY` in that process's environment (`DEEPSEEK_API_KEY="$API_KEY" ...` in the login shell that starts the
chain; every script unsets `API_KEY`). The agents receive a dummy token and the proxy's address; the proxy adds the
key upstream. Never on a command line, in a file, in a container or in a log.

## Money

ROADMAP D6 and its table: cap **ledger + $15**, expected $8 to $13 on the ledger (an estimate: no such session has
run; the foreign sessions are guessed at $0.5 to $1.7 each, A2 at about B2's $1.19 to $1.37 per run). The cap is
written once, before anything paid, by `block_h_cap.sh` into `block_h_cap.txt` as `<cap> <ledger at the start> <UTC date>`
(cap = ledger + 15.00; the command refuses if the file exists). Andres's one-line confirmation on #41 (ROADMAP
section 7, item 1) comes first and is copied into the dated note. Per session: the proxy's `--session-cap-usd 2.50`
(the probe 0.05) and `--block-cap-usd <cap>` refuse calls past either; A2 passes
`--set budget.cumulative_usd.deepseek=<cap>` with its two run caps. A session starts only when the ledger plus $2.50
stays within the cap and the console's topped-up balance is at least $8 (D12; Astra reads it before the block).
Every proxy call lands in the shared ledger as provider `deepseek` with the session's run id, so the cap counts it.

## Order and commands (Mac; one session at a time; never beside another paid run or the scaling driver)

From a login zsh, `L=~/Documents/Mila/Gene-Mila/genemila_scale_logs`, the scripts copied to `$L/block_h/`; `H_CLONE`
names the operator's clone of the integration branch at this plan's commit or later (default
`~/Documents/Mila/Gene-Mila/gene-mila-h`), which holds `tools/baselines/`. Start chains outside DeepSeek's peak hours
when the session allows (ROADMAP D1: 01:00 to 04:00 and 06:00 to 10:00 UTC on weekdays).

1. **State.** `python handoff_state.py --fetch`; `pgrep -fl 'run_research.py|scale_seq.sh|feature_compare.py|ledger_proxy.py'`.
   Block G must be read (ROADMAP D4) before H starts.
2. **Tools and isolation** (free): `bash $L/block_h/check_tools.sh`; post its output on #41. It names the missing
   pieces, builds nothing paid, and prints the package hashes. Then write `isolation.txt` as above.
3. **C0** (free, CPU only; not beside a paid run; three runs, seeds 0, 2, 3, from `gene-mila-baa7dfd`):
   ```bash
   .venv/bin/python run_research.py --minutes 20 --workers 4 --dataset adamson_cf --planner-provider scripted \
     --worker-provider mock --no-watchdog --run-dir <MAIN>/runs/adamson_cf_h_c0_scripted_w4_r$S --set run.seed=$S \
     --set run.data_dir=<MAIN>/data/adamson_cf_clean_tables
   ```
4. **The cap**, once: `bash $L/block_h/block_h_cap.sh` (after Andres's line).
5. **The chain**, detached:
   ```bash
   cd $L/block_h; screen -dmS blockh zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" caffeinate -i bash block_h_chain.sh > block_h_chain.log 2>&1'
   ```
   Order: the probe; A4 r0, r2, r3; A3 r0, r2, r3; A2 r0, r2, r3. A session whose `.passed` marker exists is skipped,
   so a pre-session refusal (exit 1 or 2) is fixed and the chain restarted the same way; a stop after a session
   (`block_h_stopped.txt`, exit 3) is not resumed until the cause is written up here. The cap file stays.
6. **The probe** (`block_h_probe.sh`): two proxy sessions of $0.05 each (D6's cap per round; one round of either
   client is estimated at $0.02 to $0.03, so one $0.05 cap for both would sit at the expected cost). First one Biomni
   `--probe` round (execute to observation, run id `h_probe`), then one one-turn `claude -p` call on
   `ANTHROPIC_BASE_URL=<proxy>/anthropic` (run id `h_probe_claude`, the flags `run_autoresearch.sh` uses). It checks
   the two routes ROADMAP section 8 lists as unverified: `deepseek-v4-pro` accepting Biomni's consecutive assistant
   messages, and Claude Code honouring the model alias on a custom base URL with its web tools off
   (`--disallowedTools WebFetch,WebSearch`). The proxy logs must show the served model. The check file counts the
   other statuses: a 402 is the proxy's cap, not a route failure, and is read before any fallback is disclosed. If
   Biomni's route fails with the proxy's message merging, A4 is reported as "could not run on DeepSeek v4-pro"; if
   Claude Code rejects the alias, A3 runs on `deepseek-flash` (`H_A3_MODEL`, passed to the runner as
   `BASELINE_ANTHROPIC_MODEL`) and the difference is disclosed (ROADMAP section 5, B.1): either is a dated note here
   before the arm runs.

**What each session does** (`block_h_a4.sh`, `block_h_a3.sh`, seed `S`, session `h_<arm>_r$S`): checks (below); a
fresh copy `$L/block_h/work/h_<arm>_r$S` of the package with its export record (account mode: under
`/Users/Shared/genemila_h/work/`); the proxy up with run id `h_<arm>_r$S` and its own log
`$L/block_h/proxy/h_<arm>_r$S.jsonl`; the agent for 20 minutes, the runner's own clock (`--minutes 20`), with a hard
stop at 30 minutes from the script; the proxy down; `tools/baselines/collect_handback.py` into
`$L/block_h/handback/h_<arm>_r$S/`, which then holds `biomni_r$S/` or `autoresearch_r$S/` (the kept files that pass
the guard and the literal caps), `rejected/` and `manifest.json`; `results.tsv`, `runs/` and the working `features/`
stay in the work copy, and the runner's own copies with `run.json` and the transcript in `$L/block_h/out/h_<arm>_r$S`
(account mode: `/Users/Shared/genemila_h/out/`); the checks after; one line in `progress.md`. `block_h_a2.sh` is
block G's run script with one worker.

**Checks before any spend, per session:** the key in the environment; the cap file valid (at most $15 over its start);
`isolation.txt` present and its mode available (account mode: the venv imports `biomni` and `claude` is on its path);
`H_CLONE` with the four runners; `tier.txt` present and the package source matching it (`harness_val1` in
`MANIFEST.json` for `harness`, absent for `none`), its record beside it, `MANIFEST.json`'s sha256 equal to the record's; no work
copy, log or hand-back for this session; no `$H/STOP` file (block H's own halt signal since 2026-11-01); no stopped block; no lab run, driver, `feature_compare`,
other proxy or `h_agent` container running; the probe passed (for the arms); the ledger readable, at or above the
block's start, and plus $2.50 within the cap.

**Logged per session, from the proxy log** (`--log`, one JSON line per call; the fields named above): over the
status-200 rows, calls, agent minutes (first to last `ts`), `input_tokens`, `cached_tokens`, `output_tokens`,
`model_served` per call, the priced `cost_usd`; the count of other statuses (402, 404, 502); the ledger's delta over
the session; and the number of files the agent wrote or printed that name `harness/val1.npz` (reading 4). The script
refuses the session as passed when no row has status 200, when the served model is not `deepseek-v4-pro` (or the
disclosed `deepseek-flash` for A3), when the ledger delta exceeds $2.50, or when the runner's exit code is not 0.

**Stop rules** (the session becomes its own arm, the chain stops, the cause goes in a dated note): a session's ledger
delta over $2.50 or the cap reached; a runner error; a transcript, output, work copy, session log or proxy file
containing a credential pattern (`sk-[A-Za-z0-9_-]{16,}` or `Bearer sk-`; the clients' dummy `Bearer proxy` is not
one), checked by the script before anything is kept; an agent that touched anything outside its package copy (Docker:
impossible by construction; account mode: `find -ls` of the account's home compared before and after, with the tools'
own state, `.claude*`, `.cache`, `.npm` and `Library`, left out); `planner.mixed` or a non-empty
`run.external_knowledge` in an A2 run.

## Readings, fixed now, made only after the chain has ended (free; `nice -n 19`; no paid run live)

1. **B.2, one call per bundle** (ROADMAP D8), with `tools/feature_compare.py` at or after the D2 fix: candidate
   hashes first (`shasum -a 256` of every file in every arm's candidate directory, posted on #41), then:
   ```bash
   nice -n 19 python tools/feature_compare.py --data <MAIN>/data/adamson_cf_clean_tables --out docs/results/adamson_cf_h_compare \
     --parent builtin --fold-seeds 101,102,103 --null-reps 999 \
     --source-run A1_r0=<MAIN>/runs/adamson_cf_g1_ds_w4_r0 --source-run A1_r2=... --source-run A1_r3=... \
     --source-run A1abl_r0=<MAIN>/runs/adamson_cf_g0_ds_w4_r0 --source-run A1abl_r2=... --source-run A1abl_r3=... \
     --source-run A2_r0=<MAIN>/runs/adamson_cf_h_a2_ds_w1_r0 --source-run A2_r2=... --source-run A2_r3=... \
     --source-run C0_r0=<MAIN>/runs/adamson_cf_h_c0_scripted_w4_r0 --source-run C0_r2=... --source-run C0_r3=... \
     --source A3_r0=$L/block_h/handback/h_a3_r0/autoresearch_r0 --source A3_r2=$L/block_h/handback/h_a3_r2/autoresearch_r2 --source A3_r3=... \
     --source A4_r0=$L/block_h/handback/h_a4_r0/biomni_r0 --source A4_r2=$L/block_h/handback/h_a4_r2/biomni_r2 --source A4_r3=... \
     --source A5_C2=docs/comparison/cellforge_c2
   ```
   OOF only, no `--with-val1` (D5). The package arms' candidate set is `runs/kept/features/` at the kill, never the
   working `features/` (protocol, section 2), as `collect_handback.py` copied it after the guard and the literal caps;
   a file it rejected is listed from `rejected/` in reading 4 and is not a candidate. A session that handed back no
   kept feature is a row with the parent's score, reported, not dropped.
2. **The metrics table of protocol section 5**, one row per arm: the system row's OOF M1 to M7 and M12 from the call
   above (mean ± sd over the three searches), ΔM1 ± SE_adj against the parent, wins, the number of features and the
   number with a development verdict; per arm also the sessions' minutes, calls, tokens, served model and spend from
   the proxy logs (A2: `summary.json["llm_usage"]`), and each arm's median `evaluate.py` runs per session from
   `results.tsv`. The arm rule (`tools/arm_reading.py`) is read descriptively; no arm is called better from this tier.
3. **The frozen batch for the fresh test** (D8): per arm its three system models, at most three single features with a
   development verdict and the largest OOF gain, plus the additive rule and C0, listed with sha256 on #41 before any
   contact with the holder (`docs/PLAN_R_FRESH_TEST.md`, when it exists).
4. **Descriptive:** per session, the kept features' sources read (which knowledge files), the number of attempts,
   keeps and rejections (literal caps, guard, one-change rule), and whether the agent read `harness/val1.npz`: the
   session script counts the files the agent wrote or printed (the transcript, `features/`, `runs/`, `scratch/`, the
   runner's output) that name `val1.npz` or `harness/val1`, the package's own `MANIFEST.json` and `program.md` left
   out, into `h_<arm>_r$S.val1scan.txt` and the `progress.md` line; a read is allowed, recorded and changes nothing.
   The paste check on the kept files is the guard and the literal caps (`collect_handback.py`, the hand-back
   `manifest.json`), read by hand before the frozen batch is listed.

## To be filled in before the chain (dated notes go below this line)

- Andres's cap line on #41 (ledger + $15), with its date; the isolation answer (Docker, or the account's name), with
  its date; his word on the harness tier (keep or veto), written into `tier.txt` as `harness` or `none`, with its
  date; the export runs after it.
- `check_tools.sh`'s output on #41: docker, gtimeout, claude, codex, the image, the network test.
- The package's `MANIFEST.json` and `program.md` sha256 on #41 (step 7 of ROADMAP section 6).
- The console reading before the block (topped-up balance, granted credit) and after it; the cap record line and the
  ledger at the start.
- The probe's result: served models, tokens, cost, the other statuses; any route that failed and the disclosed
  fallback.

## 2026-10-17 03:52 UTC: A3 runs through the Codex CLI; Claude Code stays the fallback

**Why.** Astra's check of the Mac (#41, comment 6228055333, 17 October): `docker` at `/usr/local/bin/docker` (daemon
state unknown), `gtimeout` not found, `claude` (Claude Code) not found, `codex` found at
`/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`, the Codex CLI bundled with
the ChatGPT desktop app, version unknown. The lead's decision: arm A3, the autoresearch-style loop, runs through the
Codex CLI pointed at DeepSeek `deepseek-v4-pro` through the ledger proxy, in the OpenAI chat-completions wire format
on the proxy's existing `/v1/chat/completions` route. The LLM, the 20-minute clock, the $2.50 session cap, the task
package, `program.md` as the whole prompt, the env -i environment, the first-proxy-line check, the hand-back and the
proxy-log reading are the same as with Claude Code; the client program differs, and `run.json["client"]` records
which one ran (`codex` or absent for Claude Code). Two differences come with the client and no configuration removes
them, so they are disclosed here, in `run.json` and in the A3 reading: Codex's shell tool cuts a command at 10 s unless
the model itself passes `timeout_ms` (`DEFAULT_EXEC_COMMAND_TIMEOUT_MS` in `codex-rs/core/src/exec.rs`, 10_000 at
rust-v0.80.0, 0.94.0 and main; no configuration key sets it, only the MCP timeouts exist), where `run_autoresearch.sh`
gives Claude Code's Bash `eval_timeout_s` + 30 s so one `python evaluate.py` fits one call; `run.json["shell_timeout"]`
says so, and reading 1 for an A3 session under Codex counts the `command_execution` items in `transcript.txt` whose
`evaluate.py` command ended in the client's timeout, so evaluations the client cut short are reported as such and not
attributed to the LLM. And in account mode Codex's Seatbelt sandbox (`network_access = false`) blocks the agent's shell
commands from the network, which `program.md` forbids anyway and Claude Code's Bash is only told: the Codex arm is the
stricter of the two there, and reading 4 reads both transcripts for network attempts; in Docker mode both arms are
equal (the internal network is the isolation). The hand-back directory stays `autoresearch_r$S`, so reading 1 reads
as written. Row A3 of the arms table is read with this note.

**What changed** (this commit): `tools/baselines/run_codex.sh`, the Codex twin of `run_autoresearch.sh` (same
interface and refusals, plus `--probe`): it writes a private `CODEX_HOME` under the session's output directory with
one `config.toml` (provider `ledger_proxy` at `<proxy>/v1`, `wire_api = "chat"`, `env_key = "LEDGER_PROXY_TOKEN"`
holding the dummy `proxy-token-<seed>`, `model = "deepseek-v4-pro"`, `web_search = "disabled"`, no `[mcp_servers]`
table, `approval_policy = "never"`, `sandbox_mode = "workspace-write"` with `network_access = false`), and runs
`codex exec --skip-git-repo-check -C <package> --sandbox workspace-write -m deepseek-v4-pro --json
-o <out>/last_message.txt -` with `program.md` on stdin, under the python watchdog, the binary from `CODEX_BIN` (no
`--ephemeral`: it first appears at rust-v0.99.0, a build with no chat wire format; the session files land under the
private `CODEX_HOME`). The Mac's `~/.codex` (the ChatGPT app's login and configuration) is never read or written.
`block_h_common.sh` gains `A3_CLIENT` (`codex`, the default, or `claude`), `CODEX_BIN` (on `PATH`, else the bundled
path) and `H_CODEX_WIRE_API` (`chat` in account mode, `responses` in Docker mode unless set; forwarded to the runner as
`CODEX_WIRE_API` by `block_h_a3.sh` and `block_h_probe.sh`, the only way a variable reaches the isolation), requires
`run_codex.sh` as a fifth runner, and in account mode checks the selected client's binary instead of `claude`;
`block_h_a3.sh` selects `run_codex.sh` or `run_autoresearch.sh` by `A3_CLIENT`; `block_h_probe.sh` step 2 exercises
the selected client once (`run_codex.sh --probe`: the one-line prompt "Run the shell command `ls` and then reply with
the single word ok.", one tool round trip, a read-only sandbox, run id `h_probe_codex`, the same $0.05 cap); `check_tools.sh` prints `codex --version`, `codex exec --help` and `docker info` (read-only);
the `Dockerfile` installs `@openai/codex` beside Claude Code. Every earlier check stays. Tests:
`tests/test_baselines.py` dry-runs the script and runs it once with a stub `codex` through the test proxy.

**Unverified, and how the probe settles it** (nothing has run; the research of 2026-10-17 read the current Codex
sources and OpenAI's and DeepSeek's documentation, not the Mac's binary):
1. The bundled binary's version, and that it is the standalone Rust CLI accepting `codex exec` with these flags.
   `check_tools.sh` prints `codex --version` and `codex exec --help`; both go on #41 before the probe.
2. `wire_api = "chat"`. Codex removed it at rust-v0.95.0 (3 February 2026; github.com/openai/codex/discussions/7782;
   `WireApi::Chat` is in `codex-rs/core/src/model_provider_info.rs` through rust-v0.94.0, 2 February 2026, the last
   chat-capable release, and `CHAT_WIRE_API_REMOVED_ERROR` from 0.95.0 on, read from the tagged sources 2026-10-17):
   such a build refuses the configuration ("no longer supported") or speaks the Responses API only, `POST
   <base_url>/responses`, which the proxy does not serve (a 404 row with no served model, so the runner aborts the
   session as an error). The ChatGPT desktop app ships current Codex, so the bundled binary is likely a post-0.95
   build and the `/v1/responses` route the realistic prerequisite; `check_tools.sh` decides. Rule: if `--version` is
   0.94.0 or older and `h_probe_codex.jsonl` shows status-200 rows with `model_served` `deepseek-v4-pro` (item 7), A3
   runs as configured. If the build is newer, one of two disclosed paths, decided before any A3 session: the proxy
   gets a `/v1/responses` route (forwarding to `https://api.deepseek.com/responses`, pricing the `response.completed`
   usage: `input_tokens`, `input_tokens_details.cached_tokens`, `output_tokens`; no `[DONE]` sentinel;
   `response.failed` ends an errored stream; its own pull request with tests) and the arm runs with
   `H_CODEX_WIRE_API=responses` in the chain's environment; or A3 falls back to
   Claude Code (`A3_CLIENT=claude`, Claude Code installed where the agent runs: the image has it, the account would
   need it) and this note gets the fallback line. In both the LLM and the rest are unchanged.
3. That `codex exec` starts with no `auth.json` in a fresh `CODEX_HOME` when the provider is custom with `env_key` and
   `forced_login_method = "api"`. If the probe shows a login refusal, the fix is `codex login --with-api-key` into the
   scratch `CODEX_HOME` with the dummy token (it writes `auth.json` there only), recorded here.
4. Verified from the sources, not yet on the Mac: a build ignores configuration keys it does not know (`ConfigToml`
   carries `schemars(deny_unknown_fields)`, a schema annotation, and no serde one, at rust-v0.94.0 and main), and the
   top-level `web_search = "disabled"` is the key 0.94.0 honours (`WebSearchMode { Disabled, Cached, Live }`) as does
   main. The `web_search_request = false` line of the first version was removed: that toggle lived under `[tools]`
   (alias of `tools.web_search`), never at the top level, and its default is off.
5. Whether DeepSeek's `output_tokens` includes the reasoning tokens (its wording implies so, as OpenAI's does): one
   probe response against the console reading.
6. Other HTTP requests Codex may make at start (model catalog refresh, telemetry, update checks). In Docker the
   internal network blocks them; in account mode they would leave the Mac; one aimed at the proxy before the first
   chat completion shows as a 404 row and the runner then aborts the session as an error (the first-proxy-line rule:
   the first new row must carry `model_served`). The probe's proxy log (`h_probe_codex.jsonl`) and `codex_stderr.txt`
   are read for such requests before any arm; if one exists the runner's rule needs a decision (skip 404 rows, or
   disable the request in the configuration), recorded here.
7. The tool round trip on the chat route. DeepSeek's chat completions in thinking mode want every earlier turn's
   `reasoning_content` passed back when tools are present (api-docs.deepseek.com, thinking mode and tool calls), and
   a 0.94.0 Codex builds its chat request from its own history, which has no such field; the first shell call of a
   real session would then get a 400 after a 200 first row, which the first-line rule does not catch, and the session
   would burn its clock and cap on retries. So the probe's prompt forces one shell command (`ls`): codex is cleared for
   A3 only when `h_probe_codex.jsonl` holds at least two status-200 rows and no 400; otherwise the chat route is unfit
   for the arm and one of item 2's two paths is taken.

**Docker as the isolation route, pending `docker info`.** `check_tools.sh` now prints it. If the daemon runs, Docker
mode: the image installs the current npm Codex build (`@openai/codex` 0.163.0 on 2026-10-17), which is responses-only,
so Docker mode runs with the responses wire format by construction (`H_CODEX_WIRE_API` defaults to `responses` when
`isolation.txt` reads `docker`) and the `/v1/responses` proxy route is a hard prerequisite for it whatever the bundled
binary's version; inside the container the runner gets `CODEX_SANDBOX=none`
(`--dangerously-bypass-approvals-and-sandbox`; the Linux sandbox does not start unprivileged, the container is the
isolation, as the plan's Isolation section says). If no daemon, account mode with the bundled binary under the second
account and the macOS Seatbelt sandbox as a second layer. Either way the probe runs the selected client through the
proxy once, at $0.05, before any arm.

**Review fixes, 2026-10-17.** The first version's command carried `--ephemeral` beside `wire_api = "chat"`, a pair no
Codex release accepts (chat ends at 0.94.0, the flag begins at 0.99.0); it is gone. `CODEX_WIRE_API` could not reach
the runner through `agent_run` (env -i and `docker run` pass fixed variables only), so Docker mode always wrote
`chat`; `H_CODEX_WIRE_API` is now forwarded. The dead `web_search_request` and `preferred_auth_method` keys were
removed, the probe exercises one tool call (item 7), and the two client differences above are disclosed.

**2026-10-17 04:32 UTC: the proxy serves `/v1/responses`; `responses` is the default wire format in both modes.**
`tools/baselines/ledger_proxy.py` forwards `POST /v1/responses` (the OpenAI Responses API, the only format a Codex
build from 0.95.0 on speaks) to the same path under `--upstream` (`https://api.deepseek.com/v1/responses`; DeepSeek
documents its Codex integration at `base_url` `https://api.deepseek.com/`, `/v1` being its OpenAI-compatible alias),
with the same header handling as the chat route, plain JSON and SSE. It prices the usage of the response object (for a
stream, `data.response.usage` of the `response.completed` event): `input_tokens` minus
`input_tokens_details.cached_tokens` at the cache-miss rate, `cached_tokens` at the cache-hit rate, `output_tokens` at
the output rate, the chat route's formula; the ledger row and the log line keep the other routes' schema with route
`/v1/responses`. A stream that ends without `response.completed` is unpriced and halts the proxy like an Anthropic
stream without `message_delta`. `run_codex.sh`'s `CODEX_WIRE_API` and `block_h_common.sh`'s `H_CODEX_WIRE_API`
default to `responses` in both isolation modes (account mode included); `chat` stays selectable as the legacy option
for a bundled build of 0.94.0 or older. DeepSeek's usage field names on this route are UNVERIFIED and the probe
confirms them: a usage without `input_tokens` or `output_tokens` is not priced (502, the keys seen in the log line,
the proxy halted), so a mismatch shows as a 502 row in `h_probe_codex.jsonl`, never as a silent zero; a usage without
`input_tokens_details.cached_tokens` is priced with every prompt token at the miss rate and the log line says
`cached_tokens_absent`. Should DeepSeek answer 404 on `/v1/responses` (the probe's first row), the route needs the
root path instead: one line in the proxy, before any arm. Tests: `tests/test_ledger_proxy.py` (the route plain and
streamed against the mock upstream, the cost from the pricing table, the events relayed unchanged, the cached-absent
case, the unknown shape, the stream without `response.completed`, the token replaced, nothing of a body in the log)
and `tests/test_baselines.py` (the dry run with the new default and a chat-mode run through the variable; the stub
`codex` speaks the configured format).

**2026-10-17, review fixes to the route.** (1) A usage count that is present with the wrong JSON type (an object, a
list, a string such as `"n/a"`) raised `TypeError`/`ValueError` past the proxy's handlers: the handler thread died with
a traceback, the call was neither priced, logged nor halting, and the next call was admitted, the silent unpriced call
the route was built to refuse, on the route whose field shapes are unverified. The conversion now raises the
unpriced-usage error for any non-integer (502, the keys seen in the log line, the proxy halted), and both handlers catch
the whole family; `tests/test_ledger_proxy.py` covers an object as `input_tokens` plain and a string as `cached_tokens`
in a stream. (2) A stream that ends with `response.incomplete` (the Responses API's terminal event when
`max_output_tokens` or a filter stops the response; its response object carries the same final usage as
`response.completed`, and DeepSeek has billed the call) is now priced like a completed one, and its log line carries
`response_status: "incomplete"` (a plain response with `status: "incomplete"` too); before, it halted the proxy
unpriced and the billed call was missing from the ledger. `response.failed` carries no usage and still halts. This
changes what is priced, in the direction of counting a billed call; Andres may veto it before the probe. (3) The probe
and runner comments now tell the two 404 rows apart: the proxy's own (`"refused": "no such route"`, a route other than
`/v1/responses`: Codex posted elsewhere, Claude Code is the fallback) and DeepSeek's (route `/v1/responses`,
`"priced": false`: the path is not served, the proxy maps the route to `/responses` and the probe runs again).

## 2026-10-17 22:00 UTC: the two script gaps of the lead's note of 19:33 UTC are closed (lab-code owner, PR from `claude/block-h-script-gaps`)

1. **A failed probe can be reset.** `block_h_reset_probe.sh '<the dated note that writes the failure up>'` moves what
   a failed probe leaves behind (`h_probe*.log`, `h_probe*.txt`, `proxy/h_probe*`, `work/`, `out/` and `handback/`
   `h_probe*`, in account mode the `$SHARED` copies too, and `block_h_stopped.txt`) into `$H/failed/h_probe_<utc>/`,
   never deleting, lists them in `moved.txt` there, and appends one line to `progress.md` naming the note. It refuses
   when the probe passed, when nothing of a failed probe exists, when a proxy or an `h_agent` container is running, and
   when `block_h_stopped.txt` holds a stop of another session (an arm's stop is written up and reset by hand, never
   here). The chain then reruns the probe, its `.passed` marker being absent (step 5). The cause of the failure goes in
   a dated note here first, as the stopped-block rule says; the reset records which note.
2. **`run_biomni.py` gets its first-call rate from the Mac.** In Docker and account mode only `tools/baselines/` is
   beside the runner (the Dockerfile copies nothing else, fairness controls 6 and 7), so its lookup of
   `configs/default.toml` found nothing and the first-call cost pre-estimate was silently skipped. Now
   `block_h_common.sh`'s `miss_rate <model>` reads `input_cache_miss` from the operator's clone's rate card (`$C`), the
   probe and A4 scripts pass it as `--miss-usd-per-mtok` (a public flag now), `run.json` records `rate_source` (`flag`,
   `config` or `none`), and a runner with no rate from either source warns on stderr instead of staying silent. A
   missing rate stops the script before any spend (`NOT STARTED`).

Tests: `tests/test_block_h_scripts.py` (the reset on a fake Mac under a temporary `HOME`, its refusals, the account
mode copies, `miss_rate` on the real rate card and on a missing one, the runner with the flag, without any source and
beside the checkout). Nothing else in the scripts changed; the plan's commands are unchanged.

## Note, 2026-10-31: the probe's acceptance rule is now enforced by the script

Astra's preflight (#51, comment 6550718051; `docs/results/block_h_preflight_20261031/`) showed that
`block_h_probe.sh` only printed note item 7's rule. The pooled session check in `block_h_common.sh` accepted one codex
200, a 200 followed by a 400, and a Biomni 200 with no codex 200, and the chain then went on to the paid arms. The lead
(owner of these scripts) closed the gap before any paid probe:
- `probe_gate` in `block_h_common.sh` reads each proxy log on its own, never pooled. Biomni's `h_probe.jsonl` needs at
  least one status-200 row. With the codex client, `h_probe_codex.jsonl` needs at least two status-200 rows and no 400.
- `block_h_probe.sh` runs it after `session_after`. On failure it moves `h_probe.passed` aside to `h_probe.gate_failed`
  (never deleted), writes the reasons to `h_probe.gate.txt` and `block_h_stopped.txt`, and exits 3, so the chain stops
  and `block_h_reset_probe.sh` applies as for any failed probe.
- Tests: `tests/test_block_h_scripts.py::test_probe_gate_enforces_the_plans_codex_rule_per_log` covers Astra's three
  fixtures, two more failures and the passing case.

The rule itself is unchanged; only its enforcement is new. Astra's preflight receipts stay as they are.

## Note, 2026-11-01: the image's Biomni dependencies

Astra built the image, isolation passed, and Biomni then failed to load: `No module named 'pandas'`
(`docs/results/block_h_preflight_20261031/image_imports_20261031.log`, PR #97). Biomni 0.0.8 imports pandas, tqdm and
`langchain_openai` on load, and matplotlib for plots, but does not declare them. The lead reproduced the image's
installs on Python 3.12, added those packages, and pinned the langchain family to 0.3: langchain 0.3.30, langchain-core
0.3.86, langchain-openai 0.3.35, langgraph 0.3.18, biomni 0.0.8, openai 2.54.0. The latest langchain-openai pulls a
langchain-core 1.x that langgraph 0.3.18 refuses. With these pins `pip check` is clean, and `A1(...)` builds offline
exactly as `run_biomni.py` builds it (system prompt 156,006 characters, no model call). The Dockerfile now ends its
install with `pip check` and that import, so a missing package fails the build, not a session. Astra rebuilds the
image; nothing else in the plan changes.

## Note, 2026-11-01 (later): Biomni's probe allowance

The rebuilt chain's probe stopped before any call: `run_biomni.py` estimated Biomni's first call at its 156,006-character
system prompt / 4 characters per token × $1.32 per million tokens = $0.0515, which reaches the probe's $0.05 session
cap, so it refused and sent nothing (Astra, #51). One probe round (execute to observation) is two or three such calls,
mostly cache hits after the first. The lead raises Biomni's probe session to $0.25 and the probe's ledger check to $0.30
(`block_h_probe.sh`). The A3 client's probe stays at $0.05, and the arms' $2.50 sessions and the block ceiling are
unchanged. The probe's acceptance rule (note of 2026-10-31) is unchanged. The stop's files are moved aside with
`block_h_reset_probe.sh '2026-11-01'` before the probe runs again.

## Note, 2026-11-01 (later still): the image lookup from the chain's shell

After the probe reset, the restarted chain stopped at `h_checks` with "no image genemila-h" (PR #103), while
`docker image ls` from Astra's shell listed `genemila-h:latest` (sha256 `b15af00e...`). `docker info` had passed in the
chain, so a daemon answered; the likeliest cause is that the chain's login zsh (`screen -dmS blockh zsh -lc ...`) and
Astra's shell use different Docker contexts (Docker Desktop's `desktop-linux` against `default`, or a `DOCKER_HOST`
set only in one of them), so each sees a different image store. The refusal now prints the context, `DOCKER_HOST`,
`DOCKER_CONTEXT` and the images that shell sees. The operator runs `docker context show` and `docker image ls` from a
login zsh (`zsh -lc`) exactly as the chain is launched, compares with its own shell, and either builds the image from
that login shell (`check_tools.sh`) or launches the chain from the shell that built it. No script other than this
diagnostic changes.

## Note, 2026-11-01 (03:43 UTC stop): the STOP file was the chain's own

After Biomni seeds 0 and 2 passed, the chain stopped before seed 3 with "STOP file present" (`$L/STOP`, zero bytes;
#51, comment 6553039740). Nobody created it by hand. `block_h_chain.sh` removed `$L/STOP` at its start and re-created
it at its exit whenever the file had existed before, and `$L/STOP` has existed on the Mac since the scaling driver was
last halted. Each short-lived chain of the day (the stopped probe, the image refusal) therefore planted the file again
at its exit, and a wrapper exiting after the 02:5x chain had started planted it under that chain, whose per-session
check then refused. The chain was also removing the driver's own halt signal, against AGENTS.md. The lead changes both
scripts: block H's halt signal is now `$H/STOP`, `h_checks` reads only that, and the chain never touches `$L/STOP`.
Nothing scientific changes; seeds 0 and 2 stand. The chain resumes the same way, skipping the sessions whose `.passed`
markers exist (the probe, A4 r0 and r2), after `pgrep -fl block_h_chain` shows no stale chain or wrapper.

## Note, 2026-11-01 (13:12 UTC stop): the image is used by its immutable ID

The resumed chain stopped again at the image check, and the diagnostic of the earlier note answered the question: same
context (`desktop-linux`), no `DOCKER_HOST` or `DOCKER_CONTEXT`, `genemila-h:latest` in the listing, and still
`docker image inspect genemila-h` fails by name (#51, comment 6558432512). On the first occurrence (comment
6551896514) the ID `sha256:b15af00e...` resolved and re-tagging it restored the name for a while. Docker Desktop's
name resolution is what fails, intermittently; the ID never did. So the scripts no longer use the name: `h_checks`
reads the image ID from `$H/image_id.txt` (written once by `check_tools.sh` from the listing of the validated build),
or from the listing when the file is absent, requires `docker image inspect <ID>` to succeed, and `agent_run` starts
every container by that ID. Each session's `started` line in `progress.md` records the ID, so the paper cites the exact
image. Operator steps: pull, copy the scripts, run `check_tools.sh` once (it writes `$H/image_id.txt`; confirm it
holds `b15af00e...`, the validated build), then restart the chain. Nothing scientific changes.

## Note, 2026-11-01 (16:29 UTC, after the chain finished): empty hand-backs in `feature_compare.py`

The chain finished, exit 0, every session passed. Before the B.2 call, Astra found that `tools/feature_compare.py`
gave a `--source` with no usable file an error set row with blank metrics (#51, comment 6560683220), while reading 1
requires a row with the parent's score. Biomni seed 3 handed back no kept file, so the call would have dropped that
session. The lead changes the tool: a source with no file, or whose files all failed the checks, has a set row of
status `ok` with `empty: true`, the parent's model and columns, the parent's metrics, a zero paired gain, no null and
the verdict "no candidate: the parent's model"; its reason names which case. Nothing changes for sources with a usable
feature; `tests/test_feature_compare.py` covers both empty cases. The B.2 call is unchanged and runs once the merge is
on the integration branch and the operator's clone is at it.
