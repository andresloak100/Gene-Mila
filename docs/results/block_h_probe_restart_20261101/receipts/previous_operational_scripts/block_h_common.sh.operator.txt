#!/bin/bash
# Sourced by every block H script (docs/PLAN_H_COMPARISON.md): the paths, the ledger reading, the checks that come
# before any spend, the ledger proxy, and the agent launcher for the two isolation modes. Contains no key: the scripts
# that spend need DEEPSEEK_API_KEY in their environment; API_KEY is unset here so no second copy reaches a child. The
# runners' interfaces (flags, refusals, log fields) are those of tools/baselines/ at wip2/baselines b70ae10 (2026-10-17).
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; H="$L/block_h"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"
C="${H_CLONE:-$HOME/Documents/Mila/Gene-Mila/gene-mila-h}"   # the operator's clone at the plan's commit or later: tools/baselines/
PKG_SRC="$HOME/gm_packages/adamson_cf_clean_tables"           # the package Astra exported (plan, "The task package")
LEDGER="$MAIN/runs/spend_ledger.sqlite"; PY="$MAIN/.venv/bin/python"; PORT=8787
SHARED="/Users/Shared/genemila_h"                             # account mode: what the second account may read and write
A3_CLIENT="${A3_CLIENT:-codex}"                               # the A3 coding agent: codex (run_codex.sh) or claude (run_autoresearch.sh); plan, note of 2026-10-17
# the Codex CLI: on PATH if installed, else the one bundled with the ChatGPT desktop app (Astra, #41 comment 6228055333)
CODEX_BIN="${CODEX_BIN:-$(command -v codex || echo /Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex)}"
# the wire format run_codex.sh writes (CODEX_WIRE_API): responses (the proxy's /v1/responses route; every Codex build from
# 0.95.0 on speaks it only, the bundled one and the image's npm build alike) in both modes, or chat (legacy: the proxy's
# /v1/chat/completions route, for a bundled Codex of 0.94.0 or older, which `codex --version` would show).
H_CODEX_WIRE_API="${H_CODEX_WIRE_API:-responses}"
unset API_KEY
num() { case "$1" in ''|*[!0-9.]*|*.*.*) return 1 ;; esac; }
ledger() { sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'"; }
utc() { date -u +%Y-%m-%dT%H:%MZ; }
no() { echo "NOT STARTED: $*"; exit "${RC:-1}"; }

probe_gate() {  # probe_gate <Biomni's proxy log> [<the A3 codex client's proxy log>]: the probe's acceptance rule
  # (docs/PLAN_H_COMPARISON.md, note item 7, enforced since 2026-10-31 after #51 comment 6550718051 showed the pooled
  # session check let it through): Biomni's own log holds at least one status-200 row; the codex log, when given, holds
  # at least two status-200 rows (the shell call's tool round trip) and no 400. Each log is read on its own, never pooled.
  "$PY" - "$@" <<'PY'
import json, sys
from pathlib import Path
def statuses(path):
    p = Path(path)
    return [json.loads(l).get("status") for l in p.read_text().splitlines() if l.strip()] if p.exists() else None
bad = []
b = statuses(sys.argv[1])
if b is None: bad.append(f"no Biomni proxy log {sys.argv[1]}")
elif b.count(200) < 1: bad.append(f"Biomni: no status-200 row in {sys.argv[1]}")
if len(sys.argv) > 2:
    c = statuses(sys.argv[2])
    if c is None: bad.append(f"no codex proxy log {sys.argv[2]}")
    else:
        if c.count(200) < 2: bad.append(f"codex: {c.count(200)} status-200 rows, at least 2 needed (tool round trip)")
        if 400 in c: bad.append(f"codex: {c.count(400)} status-400 rows; the route is unfit for A3 (plan note item 7)")
for m in bad: print("PROBE GATE:", m)
print("probe gate", "FAILED" if bad else "passed")
sys.exit(1 if bad else 0)
PY
}

h_checks() {  # h_checks [lab]: the checks every paid session makes first; sets CAP START CAPDATE MODE ACCOUNT spent.
  # "lab" (A2) accepts isolation.txt reading "none": the lab needs no isolation, the foreign arms wait without it.
  [ -n "$DEEPSEEK_API_KEY" ] || no "no key in the environment"
  read -r CAP START CAPDATE 2> /dev/null < "$H/block_h_cap.txt"
  num "$CAP" && num "$START" && [ "$(echo "$CAP <= $START + 15" | bc)" = 1 ] \
    || no "no valid block cap in $H/block_h_cap.txt (docs/PLAN_H_COMPARISON.md, Money)"
  read -r MODE ACCOUNT 2> /dev/null < "$H/isolation.txt"
  case "$H_CODEX_WIRE_API" in responses|chat) ;; *) no "H_CODEX_WIRE_API must be responses or chat" ;; esac
  case "$MODE" in
    docker) docker info > /dev/null 2>&1 || no "isolation.txt says docker, but the Docker daemon is not running"
            docker image inspect genemila-h > /dev/null 2>&1 || no "no image genemila-h (check_tools.sh)"
            docker network inspect genemila_h > /dev/null 2>&1 || no "no network genemila_h (check_tools.sh)" ;;
    account) [ -n "$ACCOUNT" ] && id "$ACCOUNT" > /dev/null 2>&1 || no "isolation.txt names no existing account"
            # the account's own interpreter (biomni, the package's requirements) and claude; sudo asks for the
            # password here, in the foreground, so the ticket is fresh for the session (plan, Isolation, mode 2)
            H_ACCOUNT_VENV="${H_ACCOUNT_VENV:-/Users/$ACCOUNT/genemila_h_venv}"
            APATH="$H_ACCOUNT_VENV/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"
            if [ "$1" != lab ]; then  # the A3 client: codex at $CODEX_BIN (an absolute path or a name on APATH), or claude
              [ "$A3_CLIENT" = codex ] && a3bin="$CODEX_BIN" || a3bin=claude
              sudo -v && sudo -u "$ACCOUNT" -H env -i PATH="$APATH" HOME="/Users/$ACCOUNT" "$H_ACCOUNT_VENV/bin/python" \
                -c "import biomni, shutil, sys; sys.exit(0 if shutil.which(sys.argv[1]) else 1)" "$a3bin" > /dev/null 2>&1 \
                || no "account $ACCOUNT: no $H_ACCOUNT_VENV/bin/python with biomni, or no $a3bin on $APATH (check_tools.sh)"
            fi ;;
    none) [ "$1" = lab ] || no "isolation.txt reads none: the foreign arms wait (plan, Isolation)" ;;
    *) no "$H/isolation.txt must read 'docker', 'account <name>' or 'none' (plan, Isolation; Andres's answer first)" ;;
  esac
  for f in ledger_proxy.py run_biomni.py run_autoresearch.sh run_codex.sh collect_handback.py; do
    [ -e "$C/tools/baselines/$f" ] || no "$C/tools/baselines/$f is missing (H_CLONE must be at the plan's commit or later)"
  done
  case "$A3_CLIENT" in codex|claude) ;; *) no "A3_CLIENT must be codex or claude" ;; esac
  [ -e "$L/STOP" ] && { RC=3 no "STOP file present"; }
  [ -e "$H/block_h_stopped.txt" ] && { RC=3 no "block stopped (block_h_stopped.txt); write the cause up in the plan first"; }
  pgrep -f '[r]un_research.py' > /dev/null && no "a lab run is running"
  pgrep -f '[s]cale_seq.sh' > /dev/null && no "the scaling driver is running"
  pgrep -f '[f]eature_compare.py' > /dev/null && no "a feature_compare reading is running"
  pgrep -f '[l]edger_proxy.py' > /dev/null && no "another ledger proxy is running"
  [ "$MODE" = docker ] && docker ps --format '{{.Names}}' | grep -qx h_agent && no "an h_agent container is running"
  spent=$(ledger)
  num "$spent" && [ "$(echo "$spent >= $START" | bc)" = 1 ] && [ "$(echo "$spent + 2.50 <= $CAP" | bc)" = 1 ] \
    || { RC=2 no "ledger '$spent' unreadable, below the block's start $START, or plus the session's cap above the block cap $CAP"; }
  echo "ok: checks; ledger \$$spent, block cap \$$CAP (ledger \$$START at $CAPDATE), isolation $MODE $ACCOUNT, A3 client $A3_CLIENT$([ "$A3_CLIENT" = codex ] && echo " (wire format $H_CODEX_WIRE_API)")"
}

miss_rate() {  # miss_rate <model>: input_cache_miss for the model from the operator's clone's configs/default.toml (the
  # lab's rate card), for run_biomni.py's --miss-usd-per-mtok: in Docker and account mode only tools/baselines/ is
  # beside the runner, never configs/, so without this the first-call cost pre-estimate would be skipped. Prints the
  # rate; exit 1 (and NOT STARTED) when the file or the entry is missing. Call as RATE=$(miss_rate <model>) || exit 1.
  "$PY" - "$C/configs/default.toml" "$1" <<'PY' || no "no input_cache_miss rate for $1 in $C/configs/default.toml"
import sys, tomllib
from pathlib import Path
path = Path(sys.argv[1])
pricing = tomllib.loads(path.read_text()).get("pricing", {}) if path.is_file() else {}
entry = pricing.get(sys.argv[2]) or pricing.get("default")
if not entry or "input_cache_miss" not in entry:
    sys.exit(1)
print(float(entry["input_cache_miss"]))
PY
}

pkg_checks() {  # the package source: the tier Andres decided (tier.txt: harness or none), MANIFEST.json equal to the record
  read -r TIER 2> /dev/null < "$H/tier.txt"
  case "$TIER" in harness|none) ;; *) no "$H/tier.txt must read 'harness' or 'none': Andres's word on the harness tier (plan, The task package; ROADMAP section 7, item 3)" ;; esac
  [ -e "$PKG_SRC/MANIFEST.json" ] && [ -e "$PKG_SRC.export.json" ] || no "$PKG_SRC with its .export.json is missing (plan, The task package)"
  "$PY" - "$PKG_SRC" "$TIER" <<'PY' || no "the package at $PKG_SRC is not the plan's (above)"
import hashlib, json, sys
from pathlib import Path
pkg, tier = Path(sys.argv[1]), sys.argv[2]; rec = json.loads(Path(f"{pkg}.export.json").read_text())
m = json.loads((pkg / "MANIFEST.json").read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
has = bool(m.get("harness_val1"))
bad = [x for x, h in [("MANIFEST.json differs from the export record", sha(pkg / "MANIFEST.json") != rec.get("manifest_sha256")),
                      (f"tier.txt reads {tier}, but MANIFEST.json {'has' if has else 'has no'} harness_val1; export "
                       f"{'with the D5 tool' if tier == 'harness' else 'with --no-harness-val1'}", has != (tier == "harness")),
                      ("harness/val1.npz differs from its recorded sha256", has and sha(pkg / "harness" / "val1.npz") != m["harness_val1"]["sha256"]),
                      (f"bundle {m.get('bundle')}, split {m.get('split_id')}: not adamson_cf_clean_tables", (m.get("bundle") or "") not in ("adamson_cf_clean_tables", "adamson_cf"))] if h]
for x in bad: print("PROBLEM:", x)
print(f"package {pkg.name}: bundle {m.get('bundle')} split {m.get('split_id')}; MANIFEST.json {sha(pkg / 'MANIFEST.json')}; program.md {sha(pkg / 'program.md')}; harness tier {m['harness_val1']['n_perts'] if has else 'none'} perturbations (tier.txt: {tier})")
sys.exit(1 if bad else 0)
PY
}

proxy_up() {  # proxy_up <run id> <session cap>: the ledger proxy on the Mac, the key in its environment only; in Docker
  # mode also the relay container, the agent container's one route out (plan, Isolation). Sets PROXY_LOG_FILE RELAY_IP.
  # The log is created here, empty, so Docker can mount it and the agent can read it (run_autoresearch.sh tails it for
  # the first served model); the proxy appends to it and writes no body and no token into it.
  PROXY_LOG_FILE="$H/proxy/$1.jsonl"; [ "$MODE" = account ] && PROXY_LOG_FILE="$SHARED/proxy/$1.jsonl"
  mkdir -p "$H/proxy" "$(dirname "$PROXY_LOG_FILE")"
  [ -e "$H/proxy/$1.jsonl" ] || [ -e "$PROXY_LOG_FILE" ] && no "$H/proxy/$1.jsonl exists; not overwriting"
  : > "$PROXY_LOG_FILE" && chmod a+r "$PROXY_LOG_FILE" || no "cannot create $PROXY_LOG_FILE"
  if [ "$MODE" = docker ]; then
    docker rm -f h_relay > /dev/null 2>&1
    docker run -d --rm --name h_relay --network genemila_h alpine/socat TCP-LISTEN:$PORT,fork,reuseaddr TCP:host.docker.internal:$PORT > /dev/null \
      && docker network connect bridge h_relay || no "the relay container did not start"
    RELAY_IP=$(docker inspect -f '{{(index .NetworkSettings.Networks "genemila_h").IPAddress}}' h_relay)
    [ -n "$RELAY_IP" ] || no "the relay has no address on genemila_h"
  fi
  "$PY" "$C/tools/baselines/ledger_proxy.py" --listen 127.0.0.1:$PORT --upstream https://api.deepseek.com \
    --ledger "$LEDGER" --run-id "$1" --session-cap-usd "$2" --block-cap-usd "$CAP" --log "$PROXY_LOG_FILE" \
    > "$H/proxy/$1.proxy.log" 2>&1 &
  PROXY_PID=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    "$PY" -c "import socket,sys; s=socket.socket(); s.settimeout(1); sys.exit(0 if s.connect_ex(('127.0.0.1',$PORT))==0 else 1)" && return 0
    sleep 1
  done
  kill "$PROXY_PID" 2> /dev/null; no "the ledger proxy did not listen on 127.0.0.1:$PORT ($H/proxy/$1.proxy.log)"
}
proxy_down() {  # account mode: the log is copied back beside the other records under $H/proxy
  kill "$PROXY_PID" 2> /dev/null; wait "$PROXY_PID" 2> /dev/null
  [ "$MODE" = docker ] && docker rm -f h_relay > /dev/null 2>&1
  [ "$MODE" = account ] && cp "$PROXY_LOG_FILE" "$H/proxy/"
  true
}

home_listing() {  # account mode: the account's home as the agent's user sees it, without the tools' own state
  sudo -u "$ACCOUNT" -H find "/Users/$ACCOUNT" \( -name '.claude*' -o -name .cache -o -name .npm -o -name Library \) -prune -o -ls 2> /dev/null
}

session_dirs() {  # session_dirs <session, h_...>: W (the package copy), O (the runner's output), PKG_IN OUT_IN PROXY_URL TOOLS TOOLS_PY
  if [ "$MODE" = docker ]; then  # the agent reaches the proxy as host.docker.internal, which agent_run points at the relay
    W="$H/work/$1"; O="$H/out/$1"; PKG_IN=/work/pkg; OUT_IN=/work/out; PROXY_URL="http://host.docker.internal:$PORT"
    TOOLS=/lab/tools/baselines; TOOLS_PY=python
  else
    W="$SHARED/work/$1"; O="$SHARED/out/$1"; PKG_IN="$W"; OUT_IN="$O"; PROXY_URL="http://127.0.0.1:$PORT"
    TOOLS="$SHARED/tools/baselines"; TOOLS_PY="$H_ACCOUNT_VENV/bin/python"
  fi
  [ -e "$W" ] || [ -e "$O" ] || [ -e "$H/handback/$1" ] && no "$W, $O or $H/handback/$1 exists: a session is never repeated under its name"
  mkdir -p "$(dirname "$W")" "$O" || no "cannot make $W or $O"
  cp -R "$PKG_SRC" "$W" && cp "$PKG_SRC.export.json" "$W.export.json" || no "copy of the package failed"
  if [ "$MODE" = account ]; then
    mkdir -p "$SHARED/tools" && rm -rf "$SHARED/tools/baselines" && cp -R "$C/tools/baselines" "$SHARED/tools/baselines" || no "copy of the runners failed"
    chmod -R a+rwX "$SHARED" || no "chmod of $SHARED failed"
    home_listing > "$O.home_before.txt"
  fi
}

agent_run() {  # agent_run <log name> <command inside the isolation...>: the agent gets dummy tokens only (the runners set
  # their own and refuse a DEEPSEEK_API_KEY, so none is passed); a hard stop at 30 minutes (the runner's own clock is 20)
  # ends a session the runner did not end
  local name="$1" i; shift
  if [ "$MODE" = docker ]; then
    docker run --rm --name h_agent --network genemila_h --memory 8g --add-host "host.docker.internal:$RELAY_IP" \
      -v "$W:/work/pkg" -v "$W.export.json:/work/pkg.export.json:ro" -v "$O:/work/out" \
      -v "$PROXY_LOG_FILE:/work/proxy.jsonl:ro" -e PROXY_LOG=/work/proxy.jsonl \
      -e OPENAI_API_KEY=proxy -e ANTHROPIC_AUTH_TOKEN=proxy -e HOME=/work/out \
      genemila-h "$@" > "$H/$name.log" 2>&1 &
  else  # the ticket from h_checks is refreshed in the foreground (a backgrounded sudo cannot ask for the password)
    sudo -v
    sudo -u "$ACCOUNT" -H env -i PATH="$APATH" HOME="/Users/$ACCOUNT" PROXY_LOG="$PROXY_LOG_FILE" \
      OPENAI_API_KEY=proxy ANTHROPIC_AUTH_TOKEN=proxy "$@" > "$H/$name.log" 2>&1 &
  fi
  AGENT_PID=$!
  for i in $(seq 1 1800); do kill -0 "$AGENT_PID" 2> /dev/null || break; sleep 1; done
  if kill -0 "$AGENT_PID" 2> /dev/null; then
    echo "$(utc) hard stop at 30 minutes" >> "$H/$name.log"
    [ "$MODE" = docker ] && docker kill h_agent > /dev/null 2>&1
    kill "$AGENT_PID" 2> /dev/null   # sudo relays the signal to the agent's process
  fi
  wait "$AGENT_PID"; AGENT_RC=$?
}

session_after() {  # session_after <session> <arm> <expected model> [<session cap, 2.50>]: hand-back, the proxy-log summary, the scans
  local name="$1" arm="$2" model="$3" scap="${4:-2.50}"
  stop=""
  [ "$AGENT_RC" = 0 ] || stop="$stop runner exit code $AGENT_RC;"
  after=$(ledger)
  if num "$after" && [ "$(echo "$after >= $spent" | bc)" = 1 ]; then cost=$(echo "$after - $spent" | bc)
  else cost="?"; stop="$stop ledger unreadable or below its start after the session ('$after');"; fi
  [ "$cost" = "?" ] || [ "$(echo "$cost <= $scap" | bc)" = 1 ] || stop="$stop ledger delta \$$cost over \$$scap;"
  # a credential pattern anywhere the agent wrote (never under harness/, data/ or the feature cache), in the session's
  # logs or in the proxy's own files stops the block ("Bearer sk-", not the dummy "Bearer proxy" the clients send)
  if grep -rElI --exclude-dir=harness --exclude-dir=data --exclude-dir=cache -e 'sk-[A-Za-z0-9_-]{16,}' -e 'Bearer sk-' \
      "$O" "$W" "$H/$name"*.log "$H/proxy/$name"* > "$H/$name.credscan.txt" 2> /dev/null; then
    stop="$stop credential pattern in $(tr '\n' ' ' < "$H/$name.credscan.txt");"
  fi
  # reads of the harness tier are allowed and recorded (plan, reading 4): files the agent wrote or printed that name
  # harness/val1.npz, the package's own MANIFEST.json and program.md left out
  grep -rIl --exclude-dir=harness --exclude-dir=data --exclude-dir=cache --exclude=MANIFEST.json --exclude=program.md \
    -e 'val1\.npz' -e 'harness/val1' "$O" "$W/features" "$W/runs" "$W/scratch" "$H/$name"*.log > "$H/$name.val1scan.txt" 2> /dev/null
  val1n=$(wc -l < "$H/$name.val1scan.txt" | tr -d ' ')
  if [ "$MODE" = account ]; then
    home_listing > "$O.home_after.txt"
    cmp -s "$O.home_before.txt" "$O.home_after.txt" || stop="$stop the account's home changed (diff $O.home_before.txt $O.home_after.txt);"
  fi
  mkdir -p "$H/handback"
  "$PY" "$C/tools/baselines/collect_handback.py" --out "$O" --package "$W" --dest "$H/handback/$name" > "$H/$name.handback.log" 2>&1 \
    || stop="$stop collect_handback failed (see $H/$name.handback.log);"
  "$PY" - "$model" "$H/proxy/$name"*.jsonl <<'PY' > "$H/$name.check.txt" || stop="$stop $(grep PROBLEM "$H/$name.check.txt" | tr '\n' ';')"
import collections, json, sys
from pathlib import Path
# the proxy's log (tools/baselines/ledger_proxy.py, one JSON object per line): a forwarded call has status 200 with
# model_served, input_tokens, cached_tokens, output_tokens, cost_usd and ts; the proxy's own start and stop rows have
# status 0; a refusal (402 cap, 404 no such route) or an upstream error (502) has its status and no served model
want, paths = sys.argv[1], [Path(p) for p in sys.argv[2:]]
rows = [json.loads(l) for p in paths if p.exists() for l in p.read_text().splitlines() if l.strip()]
calls = [r for r in rows if r.get("status") == 200]
def pick(r, *names, default=0):
    for n in names:
        if n in r: return r[n]
    return default
tin = sum(float(pick(r, "input_tokens") or 0) for r in calls)
tcache = sum(float(pick(r, "cached_tokens") or 0) for r in calls)
tout = sum(float(pick(r, "output_tokens") or 0) for r in calls)
cost = sum(float(pick(r, "cost_usd") or 0) for r in calls)
models = sorted({str(r.get("model_served") or "?") for r in calls})
times = [float(r["ts"]) for r in calls if "ts" in r]
minutes = (max(times) - min(times)) / 60 if len(times) > 1 else 0.0
other = dict(sorted(collections.Counter(str(r.get("status")) for r in rows if r.get("status") not in (200, 0)).items()))
print(f"calls {len(calls)}, agent minutes {minutes:.1f}, tokens in {tin:.0f} cache {tcache:.0f} out {tout:.0f}, proxy cost ${cost:.4f}, served {models}, other statuses {other or 'none'}")
bad = [m for m, h in [("no call reached the proxy", not calls), (f"served model {models}, not {want}", bool(calls) and models != [want])] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
  echo "files naming harness/val1.npz: $val1n ($H/$name.val1scan.txt; allowed, recorded)" >> "$H/$name.check.txt"
  cat "$H/$name.check.txt"
  echo "- $(utc) $name finished rc=$AGENT_RC DeepSeek ledger \$$after (session \$$cost): $(head -1 "$H/$name.check.txt"); files naming harness/val1.npz: $val1n" >> "$L/progress.md"
  if [ -n "$stop" ]; then echo "$(utc) $name:$stop" >> "$H/block_h_stopped.txt"; echo "STOPPED:$stop"; return 3; fi
  touch "$H/$name.passed"; echo "SESSION_DONE $name rc=0"
}
