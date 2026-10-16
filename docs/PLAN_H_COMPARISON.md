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

## Arms, all on Adamson, bundle `data/adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`, `README.md`)

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
`splits.json`; Andres may veto the tier (ROADMAP section 7, item 3), in which case Astra exports with
`--no-harness-val1` and this file gets a dated note.

**Isolation (precondition; protocol, fairness control 7).** `check_tools.sh` says which of the two holds:
1. *Docker* (if the Mac has it): image `genemila-h` built once from `docs/mac/block_h/Dockerfile` (Python, the
   package's pinned numpy, scipy and scikit-learn, Biomni, Claude Code, `tools/baselines/` and `genemila/` copied in;
   no data), an internal Docker network `genemila_h` with no route to the internet, and one relay container `h_relay`
   (`alpine/socat`) on that network and on the bridge, forwarding port 8787 to the proxy on the Mac
   (`host.docker.internal:8787`). The agent container mounts the session's package copy and its output directory and
   nothing else; its only route out is `http://h_relay:8787`, the proxy. The run line (from `block_h_a4.sh`):
   ```bash
   docker run --rm --name h_agent --network genemila_h --memory 8g -v "$W:/work/pkg" \
     -v "$W.export.json:/work/pkg.export.json:ro" -v "$O:/work/out" genemila-h \
     python /lab/tools/baselines/run_biomni.py --package /work/pkg --proxy http://h_relay:8787 \
     --model deepseek-v4-pro --minutes 20 --seed $S --out /work/out
   ```
   `check_tools.sh` verifies, with a throwaway listener on the Mac, that a container on `genemila_h` cannot reach
   `https://api.deepseek.com` and can reach the relay.
2. *A second macOS account* that Andres creates (ROADMAP section 7, item 3), holding only the package copy, the
   runners' virtual environment and Claude Code; the proxy runs in Andres's account on `127.0.0.1:8787`; the arm
   scripts start the agent with `sudo -u <account> -H env -i ...`, so no variable of Andres's environment crosses.
   The filesystem isolation holds (the account cannot read Andres's home); the network one does not, so the proxy
   log and the transcript scan are the check, and the paper says so.
Without either, A3 and A4 wait; A2 and C0 can run. The answer is written once into `block_h/isolation.txt` as
`docker`, `account <username>` or `none` (A2 only), with Andres's words and date in the dated note below. In account
mode the chain runs in the foreground of the login shell, since `sudo` asks for the password once; in Docker mode it
runs detached as below.

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
6. **The probe** (`block_h_probe.sh`, session cap $0.05): one Biomni `--probe` round (execute to observation) and one
   one-turn `claude -p` call, both through the proxy. It checks the two routes ROADMAP section 8 lists as unverified:
   `deepseek-v4-pro` accepting Biomni's consecutive assistant messages, and Claude Code honouring the model alias on a
   custom base URL with its web tools off (`--disallowedTools WebFetch,WebSearch`). The proxy log must show the served
   model. If Biomni's route fails with the proxy's message merging, A4 is reported as "could not run on DeepSeek
   v4-pro"; if Claude Code rejects the alias, A3 runs on `deepseek-flash` and the difference is disclosed (ROADMAP
   section 5, B.1): either is a dated note here before the arm runs.

**What each session does** (`block_h_a4.sh`, `block_h_a3.sh`, seed `S`): checks (below); a fresh copy
`$L/block_h/work/<arm>_r$S` of the package with its export record; the proxy up with run id `h_<arm>_r$S` and its
own log `$L/block_h/proxy/h_<arm>_r$S.jsonl`; the agent for 20 minutes, the runner's own clock (`--minutes 20`), with a
hard stop at 30 minutes from the script; the proxy down; `tools/baselines/collect_handback.py` into
`$L/block_h/handback/<arm>_r$S` (`runs/kept/features/`, `features/`, `results.tsv`, `runs/`, the transcript); the
checks after; one line in `progress.md`. `block_h_a2.sh` is block G's run script with one worker.

**Checks before any spend, per session:** the key in the environment; the cap file valid (at most $15 over its start);
`isolation.txt` present and its mode available; `H_CLONE` with the four runners; the package source with
`harness_val1` in `MANIFEST.json` and its record beside it, `MANIFEST.json`'s sha256 equal to the record's; no work
copy, log or hand-back for this session; no STOP file; no stopped block; no lab run, driver, `feature_compare`,
other proxy or `h_agent` container running; the probe passed (for the arms); the ledger readable, at or above the
block's start, and plus $2.50 within the cap.

**Logged per session, from the proxy log** (`--log`, one JSON line per call): calls, agent minutes (first to last
call), input, cache-hit and output tokens, the served model per call, the priced cost; and the ledger's delta over
the session. The script refuses the session as passed when the served model is not `deepseek-v4-pro` (or the
disclosed `deepseek-flash` for A3), when the ledger delta exceeds $2.50, or when the runner's exit code is not 0.

**Stop rules** (the session becomes its own arm, the chain stops, the cause goes in a dated note): a session's ledger
delta over $2.50 or the cap reached; a runner error; a transcript, output or hand-back file containing a credential
pattern (`sk-[A-Za-z0-9_-]{16,}` or `Bearer `), checked by the script before anything is kept; an agent that touched
anything outside its package copy (Docker: impossible by construction; account mode: `ls -la` of the account's home
compared before and after); `planner.mixed` or a non-empty `run.external_knowledge` in an A2 run.

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
     --source A3_r0=$L/block_h/handback/a3_r0/runs/kept/features --source A3_r2=... --source A3_r3=... \
     --source A4_r0=$L/block_h/handback/a4_r0/runs/kept/features --source A4_r2=... --source A4_r3=... \
     --source A5_C2=docs/comparison/cellforge_c2
   ```
   OOF only, no `--with-val1` (D5). The package arms' candidate set is `runs/kept/features/` at the kill, never the
   working `features/` (protocol, section 2). A session that handed back no kept feature is a row with the parent's
   score, reported, not dropped.
2. **The metrics table of protocol section 5**, one row per arm: the system row's OOF M1 to M7 and M12 from the call
   above (mean ± sd over the three searches), ΔM1 ± SE_adj against the parent, wins, the number of features and the
   number with a development verdict; per arm also the sessions' minutes, calls, tokens, served model and spend from
   the proxy logs (A2: `summary.json["llm_usage"]`), and each arm's median `evaluate.py` runs per session from
   `results.tsv`. The arm rule (`tools/arm_reading.py`) is read descriptively; no arm is called better from this tier.
3. **The frozen batch for the fresh test** (D8): per arm its three system models, at most three single features with a
   development verdict and the largest OOF gain, plus the additive rule and C0, listed with sha256 on #41 before any
   contact with the holder (`docs/PLAN_R_FRESH_TEST.md`, when it exists).
4. **Descriptive:** per session, the kept features' sources read (which knowledge files), the number of attempts,
   keeps and rejections (literal caps, guard, one-change rule), and whether the agent read `harness/val1.npz`
   (the transcript scan reports it; it is allowed and changes nothing).

## To be filled in before the chain (dated notes go below this line)

- Andres's cap line on #41 (ledger + $15), with its date; the isolation answer (Docker, or the account's name), with
  its date; his word on the harness tier (keep or veto).
- `check_tools.sh`'s output on #41: docker, gtimeout, claude, codex, the image, the network test.
- The package's `MANIFEST.json` and `program.md` sha256 on #41 (step 7 of ROADMAP section 6).
- The console reading before the block (topped-up balance, granted credit) and after it; the cap record line and the
  ledger at the start.
- The probe's result: served models, tokens, cost; any route that failed and the disclosed fallback.
