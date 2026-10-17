#!/usr/bin/env bash
# Run the autoresearch-style Claude Code loop on a task package through the ledger proxy (protocol arm A3).
#
#   tools/baselines/run_autoresearch.sh [--dry-run] <package dir> <proxy url> <minutes> <seed> <out dir>
#
# Claude Code runs non-interactively (claude -p) with program.md as the prompt (exactly what the Biomni arm gets; its
# sha256 goes into run.json as task_sha256), cwd = the package directory, and an environment built from an allowlist
# (env -i: PATH, HOME, LANG, LC_ALL, TMPDIR, TZ, USER, TERM, SHELL when set) plus ANTHROPIC_BASE_URL=<proxy>/anthropic and
# ANTHROPIC_AUTH_TOKEN=proxy-token-<seed> (a dummy; the proxy adds the key); no other variable of this shell reaches
# claude or its Bash tool. The model is $BASELINE_ANTHROPIC_MODEL (default below), also passed as --model. Web tools
# are denied and no MCP server is loaded. BASH_DEFAULT_TIMEOUT_MS and BASH_MAX_TIMEOUT_MS are set to MANIFEST.json's
# eval_timeout_s plus 30 s, so one `python evaluate.py` fits in one Bash call, as it does in the Biomni arm. A python
# watchdog enforces the wall clock (gtimeout is not stock macOS): SIGTERM to claude's process group at <minutes>,
# SIGKILL 20 s later, exit 124. The transcript (stream-json, one event per line) goes to <out>/transcript.txt, run.json
# records the exit reason (ended_by: solution|timeout|cap|error), and results.tsv, features/ and runs/kept/features/
# are copied into <out>/.
#
# Isolation is the caller's job (Docker or a second macOS account holding only the package, ROADMAP D6): claude runs
# shell commands with the rights of whoever starts this script.
#
# Refusals: the proxy's /healthz must answer, and the proxy's jsonl log must be at $PROXY_LOG (default
# <out dir>/../proxy.jsonl). After the start, the first new proxy log line must show a served model (printed here)
# within $BASELINE_FIRST_CALL_S seconds (default 180); otherwise claude is killed and the run is recorded as an error.
# That catches a Claude Code that ignores the base URL (it would talk to Anthropic with the Mac's own login, and no
# line would appear) and a model name the endpoint rejects (the line would carry a non-200 status and no model).
#
# Flags verified against `claude --help` of Claude Code 2.1.301 in the build container (2026-10-16): -p/--print,
# --model, --permission-mode (choices acceptEdits, auto, bypassPermissions, manual, dontAsk, plan), --allowedTools,
# --disallowedTools, --output-format (text|json|stream-json), --verbose, --no-session-persistence, --strict-mcp-config.
# Unverified: that the Mac's Claude Code honours ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN over its own login; that
# DeepSeek's Anthropic-format endpoint accepts the model name below (its documentation could not be fetched from the
# build container; the lab's model names are deepseek-v4-pro and deepseek-flash, legacy alias deepseek-chat); the
# usage fields of that endpoint (the proxy refuses to price an unknown shape and halts).
set -euo pipefail

DRY_RUN=0
ARGS=()
for a in "$@"; do
  if [ "$a" = "--dry-run" ]; then DRY_RUN=1; else ARGS+=("$a"); fi
done
if [ "${#ARGS[@]}" -ne 5 ]; then
  echo "usage: $0 [--dry-run] <package dir> <proxy url> <minutes> <seed> <out dir>" >&2
  exit 2
fi
PKG="${ARGS[0]}"; PROXY="${ARGS[1]%/}"; MINUTES="${ARGS[2]}"; SEED="${ARGS[3]}"; OUT="${ARGS[4]}"
BASELINE_ANTHROPIC_MODEL="${BASELINE_ANTHROPIC_MODEL:-deepseek-v4-pro}"   # unverified against DeepSeek's endpoint
BASELINE_FIRST_CALL_S="${BASELINE_FIRST_CALL_S:-180}"
PROXY_LOG="${PROXY_LOG:-$OUT/../proxy.jsonl}"
SECS=$(python3 -c "import sys; print(int(float(sys.argv[1]) * 60))" "$MINUTES")

case "$PROXY" in
  http://127.0.0.1*|http://localhost*|http://\[::1\]*|http://host.docker.internal*) ;;
  *) echo "refusing: proxy url must be the local ledger proxy, got $PROXY" >&2; exit 2 ;;
esac
if [ ! -f "$PKG/program.md" ] || [ ! -f "$PKG/evaluate.py" ]; then
  echo "refusing: $PKG is not a task package (no program.md or evaluate.py)" >&2; exit 2
fi
if [ -n "${DEEPSEEK_API_KEY:-}" ] || [ -n "${API_KEY:-}" ]; then
  echo "refusing: DEEPSEEK_API_KEY or API_KEY is set in this shell; only the proxy may hold the key" >&2; exit 2
fi
# One evaluation must fit in one Bash call: MANIFEST.json's eval_timeout_s (export_task_package.py default 600) + 30 s.
EVAL_MS=$(python3 -c 'import json, sys
try: t = float(json.load(open(sys.argv[1]))["eval_timeout_s"])
except Exception: t = 600.0
print(int((t + 30) * 1000))' "$PKG/MANIFEST.json")
TASK_SHA=$(python3 -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$PKG/program.md")

# The tools Claude Code may use without a prompt: file edits (acceptEdits) and the shell commands program.md needs.
# One rule per word: a Bash rule holds a space, so the list is an array, never an unquoted string.
ALLOWED=(Read Edit Write Glob Grep "Bash(python evaluate.py*)" "Bash(python3 evaluate.py*)" "Bash(grep *)"
         "Bash(tail *)" "Bash(head *)" "Bash(cat *)" "Bash(ls *)" "Bash(wc *)" "Bash(mkdir *)" "Bash(python *)"
         "Bash(python3 *)")
DENIED=(WebSearch WebFetch Task)
CMD=(claude -p --model "$BASELINE_ANTHROPIC_MODEL" --permission-mode acceptEdits
     --allowedTools "${ALLOWED[@]}" --disallowedTools "${DENIED[@]}" --strict-mcp-config --no-session-persistence
     --output-format stream-json --verbose)
# The whole environment claude gets (env -i), the dummy token included; nothing else of this shell.
CHILD_ENV=(ANTHROPIC_BASE_URL="$PROXY/anthropic" ANTHROPIC_AUTH_TOKEN="proxy-token-$SEED"
           ANTHROPIC_MODEL="$BASELINE_ANTHROPIC_MODEL" ANTHROPIC_SMALL_FAST_MODEL="$BASELINE_ANTHROPIC_MODEL"
           BASH_DEFAULT_TIMEOUT_MS="$EVAL_MS" BASH_MAX_TIMEOUT_MS="$EVAL_MS")
for v in PATH HOME LANG LC_ALL TMPDIR TZ USER TERM SHELL; do
  if [ -n "${!v:-}" ]; then CHILD_ENV+=("$v=${!v}"); fi
done
ENV_LINE="env -i ${CHILD_ENV[*]} (ANTHROPIC_API_KEY unset; task_sha256 $TASK_SHA)"

if [ "$DRY_RUN" = 1 ]; then
  echo "dry run; would run in $PKG for $SECS s (seed $SEED), transcript to $OUT/transcript.txt, proxy log $PROXY_LOG:"
  echo "  $ENV_LINE"
  printf '  '; printf '%q ' "${CMD[@]}"; echo '"$(cat program.md)"'
  exit 0
fi

command -v claude >/dev/null || { echo "refusing: claude is not on PATH" >&2; exit 2; }
HEALTH=$(curl -fsS --max-time 5 "$PROXY/healthz") || { echo "refusing: $PROXY/healthz does not answer" >&2; exit 2; }
echo "proxy: $HEALTH"
[ -f "$PROXY_LOG" ] || { echo "refusing: proxy log $PROXY_LOG not found (set PROXY_LOG)" >&2; exit 2; }
mkdir -p "$OUT"
LINES_BEFORE=$(wc -l < "$PROXY_LOG")
STARTED=$(date -u +%s)
PROMPT="$(cat "$PKG/program.md")"

# The watchdog: claude in its own process group in the package directory; SIGTERM to the group at the limit (or when
# this script sends the watchdog SIGTERM), SIGKILL 20 s later; exit 124 on the limit, 125 when stopped from outside.
WATCHDOG='import os, signal, subprocess, sys
secs, cwd = float(sys.argv[1]), sys.argv[2]
p = subprocess.Popen(sys.argv[3:], cwd=cwd, start_new_session=True)
def stop(code):
    for sig, grace in ((signal.SIGTERM, 20), (signal.SIGKILL, 10)):
        try: os.killpg(p.pid, sig)
        except ProcessLookupError: break
        try: p.wait(timeout=grace); break
        except subprocess.TimeoutExpired: continue
    sys.exit(code)
signal.signal(signal.SIGTERM, lambda *a: stop(125))
try:
    sys.exit(p.wait(timeout=secs))
except subprocess.TimeoutExpired:
    stop(124)'
env -i "${CHILD_ENV[@]}" python3 -c "$WATCHDOG" "$SECS" "$PKG" "${CMD[@]}" "$PROMPT" > "$OUT/transcript.txt" 2>&1 &
LOOP=$!

# The first proxy log line after the start must show the served model.
SERVED=""; ABORT=""
for _ in $(seq 1 "$BASELINE_FIRST_CALL_S"); do
  sleep 1
  FIRST=$(tail -n +"$((LINES_BEFORE + 1))" "$PROXY_LOG" | head -n 1)
  if [ -n "$FIRST" ]; then
    SERVED=$(python3 -c 'import json, sys; d = json.loads(sys.argv[1]); print(d.get("model_served") or "")' "$FIRST")
    if [ -z "$SERVED" ]; then
      ABORT="the first proxy log line after the start shows no served model: $FIRST"
    else
      echo "served model: $SERVED"
    fi
    break
  fi
  kill -0 "$LOOP" 2>/dev/null || break
done
if [ -z "$SERVED" ] && [ -z "$ABORT" ] && kill -0 "$LOOP" 2>/dev/null; then
  ABORT="no proxy call within $BASELINE_FIRST_CALL_S s (is Claude Code talking to the proxy?)"
fi
if [ -n "$ABORT" ]; then
  echo "refusing to continue: $ABORT" >&2
  kill -TERM "$LOOP" 2>/dev/null || true
fi

set +e
wait "$LOOP"; CODE=$?
set -e
ENDED_BY="error"
if [ "$CODE" = 124 ]; then ENDED_BY="timeout"; elif [ "$CODE" = 0 ]; then ENDED_BY="solution"; fi
if tail -n +"$((LINES_BEFORE + 1))" "$PROXY_LOG" | grep -q '"status": 402'; then ENDED_BY="cap"; fi
if [ -n "$ABORT" ] || [ -z "$SERVED" ]; then ENDED_BY="error"; fi

[ -f "$PKG/results.tsv" ] && cp "$PKG/results.tsv" "$OUT/"
[ -f "$PKG/MANIFEST.json" ] && cp "$PKG/MANIFEST.json" "$OUT/"
[ -d "$PKG/features" ] && { rm -rf "$OUT/features"; cp -R "$PKG/features" "$OUT/features"; }
[ -d "$PKG/runs/kept/features" ] && { rm -rf "$OUT/kept_features"; cp -R "$PKG/runs/kept/features" "$OUT/kept_features"; }
python3 - "$OUT" "$SEED" "$MINUTES" "$STARTED" "$BASELINE_ANTHROPIC_MODEL" "$SERVED" "$PKG" "$CODE" "$ENDED_BY" "$PROXY" "$ABORT" "$TASK_SHA" "$EVAL_MS" <<'EOF'
import json, sys, time
out, seed, minutes, started, model, served, pkg, code, ended_by, proxy, abort, task_sha, eval_ms = sys.argv[1:]
json.dump({"arm": "autoresearch", "seed": int(seed), "model": model, "model_served": served or None,
           "minutes": float(minutes), "package": pkg, "out": out, "proxy": proxy, "task_sha256": task_sha,
           "bash_timeout_ms": int(eval_ms), "started": float(started),
           "ended": time.time(), "wall_s": round(time.time() - float(started), 1), "exit_code": int(code),
           "ended_by": ended_by, "error": abort or None}, open(f"{out}/run.json", "w"), indent=1)
EOF
echo "autoresearch session ended_by=$ENDED_BY exit=$CODE; see $OUT"
[ "$ENDED_BY" = "timeout" ] || [ "$ENDED_BY" = "solution" ]
