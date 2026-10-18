# Mac checks of 17 October 2026 (claim #68)

The four free checks the lab-code owner ("Autonomous research system") ran on Andres's Mac through its Remote Control
arm, claim [#68](https://github.com/andresloak100/Gene-Mila/issues/68), announced on
[#51](https://github.com/andresloak100/Gene-Mila/issues/51). All ran at `nice -n 19` from the dedicated clone
`~/Documents/Mila/Gene-Mila/gene-mila-macchecks` (branch `claude/mac-checks-20261017` at `cfa8034`, the integration
head). The main checkout and its data were read-only. The `STOP` file was untouched; there was no lab run, no image
build, no probe, no download other than the git clones from GitHub (this clone and `gene-mila-h`), and no paid call
beyond the balance read. Times are UTC, 18 October 02:29 to about 03:30 (the evening of 17 October on the Mac). The
checks were run by the session that started at 02:27 UTC; the session that took over at 02:48 UTC checked every number
against its file, compared the extra diagnostic of step 4 once its run had ended, and published them. The commands that are not in a committed
script are in [`commands_as_run.txt`](commands_as_run.txt), copied from the first session's record. The interpreter was the main checkout's venv, read-only: Python 3.13.7,
NumPy 2.5.3, SciPy 1.18.1, scikit-learn 1.9.1, which are the frozen export's pins. Every command ran with
`PYTHONPATH=<clone> PYTHONHASHSEED=0`.

## 1. Key check (the D12 console reading)

[`balance_reading.txt`](balance_reading.txt): `GET https://api.deepseek.com/user/balance` returned **HTTP 200**,
`is_available: true`, **USD total 36.55 (topped-up 28.19, granted 8.35)** (02:29:22 UTC; the three fields as the API returned them, each
rounded on its own, so the parts sum to 36.54). The key was read from
`~/.zshenv` as `API_KEY` inside one `zsh -c` and handed to curl on stdin (`-H @-`). It never reached a command line, a
file or a log, and the response file was deleted after reading. This was the checks' only API call.

## 2. Docker and the block H tool check

| | Before | After `open -a Docker` |
|---|---|---|
| daemon | not running (`failed to connect to the docker API`, exit 1; [`docker_info_before.txt`](docker_info_before.txt)) | **running**, up at the first poll (polls every 15 s, at most 16), 16 s after the start ([`docker_start_poll.txt`](docker_start_poll.txt)) |
| Docker Desktop | 4.63.0 (`/Applications/Docker.app`, its `Info.plist` `CFBundleShortVersionString`; [`commands_as_run.txt`](commands_as_run.txt)) | engine 29.2.1, `docker-desktop` VM: linuxkit 6.12.72, aarch64, 8 CPUs, 7.653 GiB; 0 containers, 10 images |
| free disk (`df -h ~`) | 24 GiB of 926 GiB, 98% used ([`df_before.txt`](df_before.txt)) | 23 GiB ([`df_after.txt`](df_after.txt)) |

`check_tools.sh` expects the runner clone at `~/Documents/Mila/Gene-Mila/gene-mila-h` or `H_CLONE`. Neither existed,
so I created `gene-mila-h` as a plain clone from `github.com/andresloak100/gene-mila` of the integration branch
`claude/autonomous-research-system-3k435s` at `cfa8034` (02:31:01 UTC), with nothing else in it. Then, from this
clone, with the no-download shim described below first on `PATH`:
`PATH=$SP/dockershim:$PATH SHIM_LOG=$PWD/docs/mac/mac_checks_20261017/docker_shim_refusals.txt nice -n 19 bash docs/mac/block_h/check_tools.sh > docs/mac/mac_checks_20261017/check_tools.txt 2>&1`,
where `$SP` is the first session's scratchpad; exit 0 as printed by the shell (the file itself records no exit status; [`commands_as_run.txt`](commands_as_run.txt),
[`check_tools.txt`](check_tools.txt)). The script's report:

- `gtimeout` MISSING; `claude` at `~/.local/bin/claude`; `codex` not on PATH, but the ChatGPT app's bundled
  codex-cli **0.160.0** was found (Responses API, the default `H_CODEX_WIRE_API=responses`); `sqlite3`, `screen` and
  `caffeinate` present; Python 3.13.7.
- runner clone `gene-mila-h` at `cfa8034`, 0 changed files; `ledger_proxy.py`, `run_biomni.py`,
  `run_autoresearch.sh`, `run_codex.sh` and `collect_handback.py` present. The A2 checkout `gene-mila-baa7dfd` is at
  `baa7dfd`.
- package `~/gm_packages/adamson_cf_clean_tables`: `NOT STARTED: tier.txt must read 'harness' or 'none'`. `tier.txt` is
  not written, so the package check cannot run.
- ledger $60.232225 (deepseek); nothing running.
- image `genemila-h` MISSING (not built, as instructed); network `genemila_h` **created** (internal, local, free; the
  only thing the script creates).
- **The egress test did not run.** It needs the `alpine/socat` image, which is not on the Mac. I ran the script with a
  pass-through `docker` ([`docker_pull_never_shim.sh`](docker_pull_never_shim.sh)) that adds `--pull=never` to every
  `docker run`, so nothing was downloaded without Andres's approval. The three `docker run`s refused with exit 125
  ([`docker_shim_refusals.txt`](docker_shim_refusals.txt)). The report's line "api.deepseek.com unreachable: good;
  relay UNREACHABLE" is therefore **void**: it comes from the missing image, not from the network. This is also why
  the report's `docker` line (its line 2) shows the shim's path. To run the test, Andres says yes to pulling
  `alpine/socat` from Docker Hub, and `check_tools.sh` is rerun without the shim.
- the report's isolation line (second to last), "isolation available: docker (write 'docker' into … isolation.txt once Andres has said so)",
  only means the daemon answered. `isolation.txt` and `tier.txt` were not written.

## 3. Replogle eligibility manifest

In [`docs/results/replogle_k562_gwps_manifest_20261017/`](../../results/replogle_k562_gwps_manifest_20261017/README.md):
file sha256 `d3269d9c863d96555eba768b42ab330cc1b57493cd33b4ac8fe7fbab8278f104` (md5 matches the Zenodo record;
[`replogle_sha256.txt`](replogle_sha256.txt), [`replogle_md5.txt`](replogle_md5.txt)), provisional universe of 2,055
genes, **1,820 eligible, 1,331 in-distribution** before any R1 exclusion (≥ 30). There is no HGNC file and no
essential-gene library file under `~/Documents/Mila/Gene-Mila/data_downloads` (`find -iname '*hgnc*'` and
`find -iname '*essential*'` found nothing); nothing was downloaded.

## 4. Frozen adapter check

In [`docs/results/frozen_adapter_check_20261017/`](../../results/frozen_adapter_check_20261017/README.md): the PLAN_R
section 6 gate **passes** on the B1 Norman export. Every member is bit-exact. The ensemble is bit-exact against the
export's saved predictions and within 5.96e-08 of the original members' float64 mean cast to float32 (the verification
driver's reading). A full replay reproduced the export's
`query_sha256` and `predictions_sha256`. The commands are [`adapter_check.sh`](adapter_check.sh) (the gate's three
runs), [`adapter_newbranch.sh`](adapter_newbranch.sh) with [`adapter_newbranch_queries.py`](adapter_newbranch_queries.py)
and [`adapter_compare_newbranch.py`](adapter_compare_newbranch.py) (the extra new-condition-branch diagnostic, outside
the gate: bit-exact on all 31 renamed anchors; [`adapter_newbranch_processes.txt`](adapter_newbranch_processes.txt) records a duplicate launch and why its
log header shows 02:55:14 UTC), [`adapter_build_queries.py`](adapter_build_queries.py) and
[`adapter_compare.py`](adapter_compare.py). The runtime-receipt command is in [`commands_as_run.txt`](commands_as_run.txt).

## Files

| File | What it is |
|---|---|
| `balance_reading.txt` | step 1: the HTTP code and the balance fields, with the command as run |
| `docker_info_before.txt`, `docker_start_poll.txt`, `df_before.txt`, `df_after.txt` | step 2: `docker info` before; `open -a Docker`, the polls and `docker info` after; free disk before and after |
| `check_tools.txt`, `docker_pull_never_shim.sh`, `docker_shim_refusals.txt` | step 2: the tool check's full output, the no-download shim it ran with, the three refused `docker run`s |
| `replogle_sha256.txt`, `replogle_md5.txt` | step 3: the file's hashes with start and end times |
| `adapter_build_queries.py`, `adapter_check.sh`, `adapter_compare.py` | step 4: the gate's inputs, runs and comparison, exactly as run |
| `adapter_newbranch_queries.py`, `adapter_newbranch.sh`, `adapter_compare_newbranch.py`, `adapter_newbranch_processes.txt` | step 4, extra diagnostic (not the gate): the renamed queries (the inline code, saved verbatim), the run, its comparison, and the process record of a duplicate launch |
| `commands_as_run.txt` | steps 2 and 4: the commands not in a committed script (disk and `docker info`, the poll loop, the shimmed tool check, the runtime receipt), with the outputs the README cites |
