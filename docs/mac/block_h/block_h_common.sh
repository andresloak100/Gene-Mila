#!/bin/bash
# Sourced by every block H script (docs/PLAN_H_COMPARISON.md): the paths, the ledger reading, the checks that come
# before any spend, the ledger proxy, and the agent launcher for the two isolation modes. Contains no key: the scripts
# that spend need DEEPSEEK_API_KEY in their environment; API_KEY is unset here so no second copy reaches a child.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; H="$L/block_h"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"
C="${H_CLONE:-$HOME/Documents/Mila/Gene-Mila/gene-mila-h}"   # the operator's clone at the plan's commit or later: tools/baselines/
PKG_SRC="$HOME/gm_packages/adamson_cf_clean_tables"           # the package Astra exported (plan, "The task package")
LEDGER="$MAIN/runs/spend_ledger.sqlite"; PY="$MAIN/.venv/bin/python"; PORT=8787
SHARED="/Users/Shared/genemila_h"                             # account mode: what the second account may read and write
unset API_KEY
num() { case "$1" in ''|*[!0-9.]*|*.*.*) return 1 ;; esac; }
ledger() { sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'"; }
utc() { date -u +%Y-%m-%dT%H:%MZ; }
no() { echo "NOT STARTED: $*"; exit "${RC:-1}"; }

h_checks() {  # h_checks [lab]: the checks every paid session makes first; sets CAP START CAPDATE MODE ACCOUNT spent.
  # "lab" (A2) accepts isolation.txt reading "none": the lab needs no isolation, the foreign arms wait without it.
  [ -n "$DEEPSEEK_API_KEY" ] || no "no key in the environment"
  read -r CAP START CAPDATE 2> /dev/null < "$H/block_h_cap.txt"
  num "$CAP" && num "$START" && [ "$(echo "$CAP <= $START + 15" | bc)" = 1 ] \
    || no "no valid block cap in $H/block_h_cap.txt (docs/PLAN_H_COMPARISON.md, Money)"
  read -r MODE ACCOUNT 2> /dev/null < "$H/isolation.txt"
  case "$MODE" in
    docker) docker info > /dev/null 2>&1 || no "isolation.txt says docker, but the Docker daemon is not running"
            docker image inspect genemila-h > /dev/null 2>&1 || no "no image genemila-h (check_tools.sh)"
            docker network inspect genemila_h > /dev/null 2>&1 || no "no network genemila_h (check_tools.sh)" ;;
    account) [ -n "$ACCOUNT" ] && id "$ACCOUNT" > /dev/null 2>&1 || no "isolation.txt names no existing account" ;;
    none) [ "$1" = lab ] || no "isolation.txt reads none: the foreign arms wait (plan, Isolation)" ;;
    *) no "$H/isolation.txt must read 'docker', 'account <name>' or 'none' (plan, Isolation; Andres's answer first)" ;;
  esac
  for f in ledger_proxy.py run_biomni.py run_autoresearch.sh collect_handback.py; do
    [ -e "$C/tools/baselines/$f" ] || no "$C/tools/baselines/$f is missing (H_CLONE must be at the plan's commit or later)"
  done
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
  echo "ok: checks; ledger \$$spent, block cap \$$CAP (ledger \$$START at $CAPDATE), isolation $MODE $ACCOUNT"
}

pkg_checks() {  # the package source: the harness tier, and MANIFEST.json equal to the record beside it
  [ -e "$PKG_SRC/MANIFEST.json" ] && [ -e "$PKG_SRC.export.json" ] || no "$PKG_SRC with its .export.json is missing (plan, The task package)"
  "$PY" - "$PKG_SRC" <<'PY' || no "the package at $PKG_SRC is not the plan's (above)"
import hashlib, json, sys
from pathlib import Path
pkg = Path(sys.argv[1]); rec = json.loads(Path(f"{pkg}.export.json").read_text())
m = json.loads((pkg / "MANIFEST.json").read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
bad = [x for x, h in [("MANIFEST.json differs from the export record", sha(pkg / "MANIFEST.json") != rec.get("manifest_sha256")),
                      ("no harness tier (harness_val1) in MANIFEST.json; export with the D5 tool", not m.get("harness_val1")),
                      ("harness/val1.npz differs from its recorded sha256", bool(m.get("harness_val1")) and sha(pkg / "harness" / "val1.npz") != m["harness_val1"]["sha256"]),
                      (f"bundle {m.get('bundle')}, split {m.get('split_id')}: not adamson_cf_clean_tables", (m.get("bundle") or "") not in ("adamson_cf_clean_tables", "adamson_cf"))] if h]
for x in bad: print("PROBLEM:", x)
print(f"package {pkg.name}: bundle {m.get('bundle')} split {m.get('split_id')}; MANIFEST.json {sha(pkg / 'MANIFEST.json')}; program.md {sha(pkg / 'program.md')}; harness tier {m['harness_val1']['n_perts'] if m.get('harness_val1') else 'none'} perturbations")
sys.exit(1 if bad else 0)
PY
}

proxy_up() {  # proxy_up <run id> <session cap>: the ledger proxy on the Mac, the key in its environment only; in Docker
  # mode also the relay container, the agent container's one route out (plan, Isolation)
  mkdir -p "$H/proxy"
  [ -e "$H/proxy/$1.jsonl" ] && no "$H/proxy/$1.jsonl exists; not overwriting"
  if [ "$MODE" = docker ]; then
    docker rm -f h_relay > /dev/null 2>&1
    docker run -d --rm --name h_relay --network genemila_h alpine/socat TCP-LISTEN:$PORT,fork,reuseaddr TCP:host.docker.internal:$PORT > /dev/null \
      && docker network connect bridge h_relay || no "the relay container did not start"
  fi
  "$PY" "$C/tools/baselines/ledger_proxy.py" --listen 127.0.0.1:$PORT --upstream https://api.deepseek.com \
    --ledger "$LEDGER" --run-id "$1" --session-cap-usd "$2" --block-cap-usd "$CAP" --log "$H/proxy/$1.jsonl" \
    > "$H/proxy/$1.proxy.log" 2>&1 &
  PROXY_PID=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    "$PY" -c "import socket,sys; s=socket.socket(); s.settimeout(1); sys.exit(0 if s.connect_ex(('127.0.0.1',$PORT))==0 else 1)" && return 0
    sleep 1
  done
  kill "$PROXY_PID" 2> /dev/null; no "the ledger proxy did not listen on 127.0.0.1:$PORT ($H/proxy/$1.proxy.log)"
}
proxy_down() { kill "$PROXY_PID" 2> /dev/null; wait "$PROXY_PID" 2> /dev/null; [ "$MODE" = docker ] && docker rm -f h_relay > /dev/null 2>&1; true; }

session_dirs() {  # session_dirs <arm>_r<S>: W (the package copy), O (the runner's output), PKG_IN OUT_IN PROXY_URL TOOLS
  if [ "$MODE" = docker ]; then
    W="$H/work/$1"; O="$H/out/$1"; PKG_IN=/work/pkg; OUT_IN=/work/out; PROXY_URL="http://h_relay:$PORT"; TOOLS=/lab/tools/baselines
  else
    W="$SHARED/work/$1"; O="$SHARED/out/$1"; PKG_IN="$W"; OUT_IN="$O"; PROXY_URL="http://127.0.0.1:$PORT"; TOOLS="$SHARED/tools/baselines"
  fi
  [ -e "$W" ] || [ -e "$O" ] || [ -e "$H/handback/$1" ] && no "$W, $O or $H/handback/$1 exists: a session is never repeated under its name"
  mkdir -p "$(dirname "$W")" "$O" || no "cannot make $W or $O"
  cp -R "$PKG_SRC" "$W" && cp "$PKG_SRC.export.json" "$W.export.json" || no "copy of the package failed"
  if [ "$MODE" = account ]; then
    mkdir -p "$SHARED/tools" && rm -rf "$SHARED/tools/baselines" && cp -R "$C/tools/baselines" "$SHARED/tools/baselines" || no "copy of the runners failed"
    chmod -R a+rwX "$SHARED" || no "chmod of $SHARED failed"
    ls -laR "/Users/$ACCOUNT" > "$O.home_before.txt" 2> /dev/null
  fi
}

agent_run() {  # agent_run <session> <command inside the isolation...>: the agent gets dummy tokens only; a hard stop
  # at 30 minutes (the runner's own clock is 20) ends a session the runner did not end
  local name="$1" i; shift
  if [ "$MODE" = docker ]; then
    docker run --rm --name h_agent --network genemila_h --memory 8g -v "$W:/work/pkg" \
      -v "$W.export.json:/work/pkg.export.json:ro" -v "$O:/work/out" \
      -e OPENAI_API_KEY=proxy -e ANTHROPIC_AUTH_TOKEN=proxy -e DEEPSEEK_API_KEY=proxy -e HOME=/work/out \
      genemila-h "$@" > "$H/$name.log" 2>&1 &
  else  # sudo asks for the password once: account mode runs the chain in the foreground of a login shell
    sudo -u "$ACCOUNT" -H env -i PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin HOME="/Users/$ACCOUNT" \
      OPENAI_API_KEY=proxy ANTHROPIC_AUTH_TOKEN=proxy DEEPSEEK_API_KEY=proxy "$@" > "$H/$name.log" 2>&1 &
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
  # a credential pattern anywhere the agent wrote (never under harness/, data/ or the feature cache) stops the block
  if grep -rElI --exclude-dir=harness --exclude-dir=data --exclude-dir=cache -e 'sk-[A-Za-z0-9_-]{16,}' -e 'Bearer ' "$O" "$W" "$H/$name.log" > "$H/$name.credscan.txt"; then
    stop="$stop credential pattern in $(tr '\n' ' ' < "$H/$name.credscan.txt");"
  fi
  if [ "$MODE" = account ]; then
    ls -laR "/Users/$ACCOUNT" > "$O.home_after.txt" 2> /dev/null
    cmp -s "$O.home_before.txt" "$O.home_after.txt" || stop="$stop the account's home changed (diff $O.home_before.txt $O.home_after.txt);"
  fi
  mkdir -p "$H/handback"
  "$PY" "$C/tools/baselines/collect_handback.py" --out "$O" --package "$W" --dest "$H/handback/$name" > "$H/$name.handback.log" 2>&1 \
    || stop="$stop collect_handback failed (see $H/$name.handback.log);"
  "$PY" - "$H/proxy/$name.jsonl" "$model" <<'PY' > "$H/$name.check.txt" || stop="$stop $(grep PROBLEM "$H/$name.check.txt" | tr '\n' ';')"
import json, sys
from pathlib import Path
# the proxy's log: one JSON object per call; the field names are the proxy's own (tools/baselines/ledger_proxy.py), so
# each quantity is read from the first name that exists in a record
path, want = Path(sys.argv[1]), sys.argv[2]
rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []
def pick(r, *names, default=0):
    for n in names:
        if n in r: return r[n]
        u = r.get("usage") or {}
        if n in u: return u[n]
    return default
tin = sum(float(pick(r, "input_tokens", "prompt_tokens") or 0) for r in rows)
tcache = sum(float(pick(r, "cache_hit_tokens", "prompt_cache_hit_tokens", "cache_read_input_tokens") or 0) for r in rows)
tout = sum(float(pick(r, "output_tokens", "completion_tokens") or 0) for r in rows)
cost = sum(float(pick(r, "cost_usd", "cost") or 0) for r in rows)
models = sorted({str(pick(r, "served_model", "model", default="?")) for r in rows})
times = [float(t) for t in (pick(r, "time", "ts", "timestamp", default=None) for r in rows) if t is not None]
minutes = (max(times) - min(times)) / 60 if len(times) > 1 else 0.0
print(f"calls {len(rows)}, agent minutes {minutes:.1f}, tokens in {tin:.0f} cache {tcache:.0f} out {tout:.0f}, proxy cost ${cost:.4f}, served {models}")
bad = [m for m, h in [("no call reached the proxy", not rows), (f"served model {models}, not {want}", bool(rows) and models != [want])] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
  cat "$H/$name.check.txt"
  echo "- $(utc) $name finished rc=$AGENT_RC DeepSeek ledger \$$after (session \$$cost): $(head -1 "$H/$name.check.txt")" >> "$L/progress.md"
  if [ -n "$stop" ]; then echo "$(utc) $name:$stop" >> "$H/block_h_stopped.txt"; echo "STOPPED:$stop"; return 3; fi
  touch "$H/$name.passed"; echo "SESSION_DONE $name rc=0"
}
