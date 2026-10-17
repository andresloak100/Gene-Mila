#!/usr/bin/env bash
# Run the autoresearch-style loop on a task package through the ledger proxy with the Codex CLI (protocol arm A3; the
# Codex twin of run_autoresearch.sh, same interface, same outputs, same refusals).
#
#   tools/baselines/run_codex.sh [--dry-run] [--probe] <package dir> <proxy url> <minutes> <seed> <out dir>
#
# --probe (block_h_probe.sh, ROADMAP D6's $0.05 round): the same CODEX_HOME, provider and environment, but the prompt is
# the one line "Reply with the single word ok.", the sandbox read-only, the limit 2 minutes; run.json carries probe=true
# and the sha256 of that line. It shows whether this Codex starts on the custom provider, reaches the proxy, gets the
# model served and priced, before the arm spends anything.
#
# Codex runs non-interactively (codex exec) with program.md as the prompt on stdin (exactly what the Biomni and Claude
# Code arms get; its sha256 goes into run.json as task_sha256), cwd = the package directory, and an environment built
# from an allowlist (env -i: PATH, HOME, LANG, LC_ALL, TMPDIR, TZ, USER, TERM, SHELL when set) plus CODEX_HOME=<out
# dir>/codex_home and LEDGER_PROXY_TOKEN=proxy-token-<seed> (a dummy; the proxy drops it and adds the key); no other
# variable of this shell reaches codex or the commands it runs. The private CODEX_HOME holds the one config.toml below:
# one model provider "ledger_proxy" at <proxy>/v1 with env_key LEDGER_PROXY_TOKEN, the model $BASELINE_CODEX_MODEL
# (default below), web search disabled, no [mcp_servers] table (so no MCP server is loaded), approval never, sandbox
# workspace-write. The Mac's own ~/.codex (the ChatGPT desktop app's login and config) is never read or written.
# A python watchdog enforces the wall clock (Codex has no wall-clock flag; gtimeout is not stock macOS): SIGTERM to
# codex's process group at <minutes>, SIGKILL 20 s later, exit 124. The transcript (codex --json, one JSONL event per
# line on stdout) goes to <out>/transcript.txt, codex's progress on stderr to <out>/codex_stderr.txt, the final
# message to <out>/last_message.txt; run.json records the exit reason (ended_by: solution|timeout|cap|error), and
# results.tsv, features/ and runs/kept/features/ are copied into <out>/.
#
# The binary: $CODEX_BIN, default `codex` on PATH. The Mac has no standalone install; the Codex CLI bundled with the
# ChatGPT desktop app is at
#   /Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex
# (Astra, 2026-10-17, #41 comment 6228055333; version unknown). Pass it as CODEX_BIN=<that path>.
#
# Wire format: $CODEX_WIRE_API, default "chat". With "chat" Codex speaks OpenAI chat completions, which the proxy's
# existing /v1/chat/completions route serves and prices (stream_options.include_usage injected). UNVERIFIED on the Mac:
# Codex builds from about February 2026 on removed `wire_api = "chat"` (they refuse the config with 'no longer
# supported', github.com/openai/codex/discussions/7782) and speak the Responses API only, POST <base_url>/responses,
# which the proxy does not serve today (a 404 row, no served model, so this script aborts the session). `codex
# --version` on the Mac decides: an older build takes "chat"; a newer one needs a /v1/responses proxy route first and
# CODEX_WIRE_API=responses. The Dockerfile installs a current npm build, so Docker mode needs that route.
#
# Isolation is the caller's job (Docker or a second macOS account holding only the package, ROADMAP D6): the Codex
# sandbox (macOS Seatbelt under workspace-write: the package copy, /tmp and $TMPDIR writable, no network for the
# commands it runs) is a second layer, not the isolation. In Docker the Linux sandbox (bwrap) commonly cannot start in
# an unprivileged container: CODEX_SANDBOX=none replaces --sandbox with --dangerously-bypass-approvals-and-sandbox and
# the container is the isolation.
#
# Refusals: the proxy's /healthz must answer, and the proxy's jsonl log must be at $PROXY_LOG (default
# <out dir>/../proxy.jsonl). After the start, the first new proxy log line must show a served model (printed here)
# within $BASELINE_FIRST_CALL_S seconds (default 180); otherwise codex is killed and the run is recorded as an error.
# That catches a Codex that ignores the provider (no line), a wire format the proxy does not serve (a 404 row) and a
# model name the endpoint rejects (a non-200 row with no model).
#
# Flags (codex-rs sources and developers.openai.com/codex, read 2026-10-17, current main; none run against the Mac's
# binary yet): `codex exec` (non-interactive; approval policy never is hard-coded there), a prompt argument of `-`
# reads the prompt from stdin, -C/--cd <dir>, --sandbox read-only|workspace-write|danger-full-access,
# --dangerously-bypass-approvals-and-sandbox, -m/--model, --json (JSONL events on stdout, usage in turn.completed),
# -o/--output-last-message <file>, --skip-git-repo-check (the package copy is not a git repository; required),
# --ephemeral (no session files). UNVERIFIED: that the Mac's bundled binary is a build that accepts these flags (an old
# build may lack --ephemeral or --json; `codex exec --help` on the Mac settles it); that `codex exec` starts with no
# auth.json in a fresh CODEX_HOME when the provider is custom with env_key and forced_login_method = "api" (if it
# refuses, `codex login --with-api-key` into the scratch CODEX_HOME with the dummy token is the fix); that an old build
# ignores the config keys it does not know (web_search as a string) rather than refusing them.
set -euo pipefail

DRY_RUN=0; PROBE=0
ARGS=()
for a in "$@"; do
  case "$a" in --dry-run) DRY_RUN=1 ;; --probe) PROBE=1 ;; *) ARGS+=("$a") ;; esac
done
if [ "${#ARGS[@]}" -ne 5 ]; then
  echo "usage: $0 [--dry-run] [--probe] <package dir> <proxy url> <minutes> <seed> <out dir>" >&2
  exit 2
fi
PKG="${ARGS[0]}"; PROXY="${ARGS[1]%/}"; MINUTES="${ARGS[2]}"; SEED="${ARGS[3]}"; OUT="${ARGS[4]}"
PROBE_PROMPT="Reply with the single word ok."
[ "$PROBE" = 1 ] && MINUTES=2
BASELINE_CODEX_MODEL="${BASELINE_CODEX_MODEL:-deepseek-v4-pro}"   # DeepSeek's current name; unverified through Codex
CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_WIRE_API="${CODEX_WIRE_API:-chat}"                           # chat | responses (see the header)
CODEX_SANDBOX="${CODEX_SANDBOX:-workspace-write}"                  # workspace-write | read-only | none (Docker)
BASELINE_FIRST_CALL_S="${BASELINE_FIRST_CALL_S:-180}"
PROXY_LOG="${PROXY_LOG:-$OUT/../proxy.jsonl}"
SECS=$(python3 -c "import sys; print(int(float(sys.argv[1]) * 60))" "$MINUTES")

case "$PROXY" in
  http://127.0.0.1*|http://localhost*|http://\[::1\]*|http://host.docker.internal*) ;;
  *) echo "refusing: proxy url must be the local ledger proxy, got $PROXY" >&2; exit 2 ;;
esac
case "$CODEX_WIRE_API" in chat|responses) ;; *) echo "refusing: CODEX_WIRE_API must be chat or responses" >&2; exit 2 ;; esac
case "$CODEX_SANDBOX" in workspace-write|read-only|none) ;; *) echo "refusing: CODEX_SANDBOX must be workspace-write, read-only or none" >&2; exit 2 ;; esac
[ "$PROBE" = 1 ] && [ "$CODEX_SANDBOX" = workspace-write ] && CODEX_SANDBOX=read-only   # the probe writes nothing
if [ ! -f "$PKG/program.md" ] || [ ! -f "$PKG/evaluate.py" ]; then
  echo "refusing: $PKG is not a task package (no program.md or evaluate.py)" >&2; exit 2
fi
if [ -n "${DEEPSEEK_API_KEY:-}" ] || [ -n "${API_KEY:-}" ]; then
  echo "refusing: DEEPSEEK_API_KEY or API_KEY is set in this shell; only the proxy may hold the key" >&2; exit 2
fi
# Absolute paths: -C and -o are read by codex after the watchdog has changed into the package directory.
mkdir -p "$OUT"
PKG=$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$PKG")
OUT=$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$OUT")
PROMPT_FILE="$PKG/program.md"
if [ "$PROBE" = 1 ]; then PROMPT_FILE="$OUT/probe_prompt.txt"; printf '%s\n' "$PROBE_PROMPT" > "$PROMPT_FILE"; fi
TASK_SHA=$(python3 -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$PROMPT_FILE")

# The private CODEX_HOME: config.toml only (plus DeepSeek's model catalog when $BASELINE_CODEX_MODELS_JSON names a copy
# of it; without one Codex logs 'Unknown model ... fallback model metadata' and runs). Never ~/.codex.
CODEX_HOME="$OUT/codex_home"
mkdir -p "$CODEX_HOME"
CATALOG_LINE="# no model_catalog_json: Codex uses its fallback model metadata for $BASELINE_CODEX_MODEL"
if [ -n "${BASELINE_CODEX_MODELS_JSON:-}" ]; then
  cp "$BASELINE_CODEX_MODELS_JSON" "$CODEX_HOME/models.json"
  CATALOG_LINE="model_catalog_json = \"$CODEX_HOME/models.json\""
fi
cat > "$CODEX_HOME/config.toml" <<EOF
# Written by tools/baselines/run_codex.sh for one block H A3 session (seed $SEED). Private to this session's CODEX_HOME.
model = "$BASELINE_CODEX_MODEL"
model_provider = "ledger_proxy"
preferred_auth_method = "apikey"
forced_login_method = "api"
approval_policy = "never"
sandbox_mode = "workspace-write"
# web search off, both spellings: the current key (a string) and the deprecated toggle older builds read
web_search = "disabled"
web_search_request = false
$CATALOG_LINE
# no [mcp_servers.*] table: no MCP server is loaded

[sandbox_workspace_write]
network_access = false

[model_providers.ledger_proxy]
name = "DeepSeek through the ledger proxy"
base_url = "$PROXY/v1"
env_key = "LEDGER_PROXY_TOKEN"
wire_api = "$CODEX_WIRE_API"
request_max_retries = 2
stream_max_retries = 2
stream_idle_timeout_ms = 300000
EOF

case "$CODEX_SANDBOX" in
  none) SANDBOX_FLAGS=(--dangerously-bypass-approvals-and-sandbox) ;;
  *) SANDBOX_FLAGS=(--sandbox "$CODEX_SANDBOX") ;;
esac
CMD=("$CODEX_BIN" exec --skip-git-repo-check --ephemeral -C "$PKG" "${SANDBOX_FLAGS[@]}" -m "$BASELINE_CODEX_MODEL"
     --json -o "$OUT/last_message.txt" -)
# The whole environment codex gets (env -i), the dummy token included; nothing else of this shell.
CHILD_ENV=(CODEX_HOME="$CODEX_HOME" LEDGER_PROXY_TOKEN="proxy-token-$SEED")
for v in PATH HOME LANG LC_ALL TMPDIR TZ USER TERM SHELL; do
  if [ -n "${!v:-}" ]; then CHILD_ENV+=("$v=${!v}"); fi
done
ENV_LINE="env -i ${CHILD_ENV[*]} (OPENAI_API_KEY and DEEPSEEK_API_KEY unset; task_sha256 $TASK_SHA)"

if [ "$DRY_RUN" = 1 ]; then
  echo "dry run; would run in $PKG for $SECS s (seed $SEED), transcript to $OUT/transcript.txt, proxy log $PROXY_LOG:"
  echo "  $ENV_LINE"
  printf '  '; printf '%q ' "${CMD[@]}"; echo "< $PROMPT_FILE"
  echo "  with $CODEX_HOME/config.toml:"
  sed 's/^/    /' "$CODEX_HOME/config.toml"
  exit 0
fi

command -v "$CODEX_BIN" >/dev/null || { echo "refusing: $CODEX_BIN is not on PATH (set CODEX_BIN)" >&2; exit 2; }
HEALTH=$(curl -fsS --max-time 5 "$PROXY/healthz") || { echo "refusing: $PROXY/healthz does not answer" >&2; exit 2; }
echo "proxy: $HEALTH"
[ -f "$PROXY_LOG" ] || { echo "refusing: proxy log $PROXY_LOG not found (set PROXY_LOG)" >&2; exit 2; }
LINES_BEFORE=$(wc -l < "$PROXY_LOG")
STARTED=$(date -u +%s)

# The watchdog: codex in its own process group in the package directory; SIGTERM to the group at the limit (or when
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
env -i "${CHILD_ENV[@]}" python3 -c "$WATCHDOG" "$SECS" "$PKG" "${CMD[@]}" \
  < "$PROMPT_FILE" > "$OUT/transcript.txt" 2> "$OUT/codex_stderr.txt" &
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
  ABORT="no proxy call within $BASELINE_FIRST_CALL_S s (is Codex talking to the proxy?)"
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
# arm stays "autoresearch": collect_handback.py names the hand-back <arm>_r<seed> and the plan's readings read
# autoresearch_r$S for A3 whichever client ran it; "client" says which one did.
python3 - "$OUT" "$SEED" "$MINUTES" "$STARTED" "$BASELINE_CODEX_MODEL" "$SERVED" "$PKG" "$CODE" "$ENDED_BY" "$PROXY" "$ABORT" "$TASK_SHA" "$CODEX_BIN" "$CODEX_WIRE_API" "$CODEX_SANDBOX" "$PROBE" <<'EOF'
import json, sys, time
(out, seed, minutes, started, model, served, pkg, code, ended_by, proxy, abort, task_sha, codex_bin, wire_api,
 sandbox, probe) = sys.argv[1:]
json.dump({"arm": "autoresearch", "client": "codex", "seed": int(seed), "model": model, "model_served": served or None,
           "minutes": float(minutes), "probe": probe == "1", "package": pkg, "out": out, "proxy": proxy,
           "task_sha256": task_sha,
           "codex_bin": codex_bin, "wire_api": wire_api, "sandbox": sandbox, "codex_home": f"{out}/codex_home",
           "started": float(started), "ended": time.time(), "wall_s": round(time.time() - float(started), 1),
           "exit_code": int(code), "ended_by": ended_by, "error": abort or None}, open(f"{out}/run.json", "w"), indent=1)
EOF
echo "codex session ended_by=$ENDED_BY exit=$CODE; see $OUT"
[ "$ENDED_BY" = "timeout" ] || [ "$ENDED_BY" = "solution" ]
