#!/bin/bash
# Block H, arm A3 (docs/PLAN_H_COMPARISON.md): one autoresearch-style coding-agent session on a fresh copy of the task
# package, 20 minutes, deepseek-v4-pro through the ledger proxy, web tools off, session cap $2.50. The client is
# A3_CLIENT (block_h_common.sh; default codex, the Mac has codex and not claude, plan note of 2026-10-17): codex runs
# run_codex.sh (the Codex CLI at CODEX_BIN, the wire format H_CODEX_WIRE_API: responses on the proxy's /v1/responses
# route in both modes; chat, the /v1/chat/completions route, only for a build before 0.95.0), claude runs
# run_autoresearch.sh (Claude Code, DeepSeek's
# Anthropic-format route). Usage: block_h_a3.sh <seed 0|2|3>. No key in
# it: DEEPSEEK_API_KEY must be in the environment.
# H_A3_MODEL=deepseek-flash only after the probe showed that the client rejects the alias (a dated note in the plan).
. "$(dirname "$0")/block_h_common.sh"
S="$1"; case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
name=h_a3_r$S; model="${H_A3_MODEL:-deepseek-v4-pro}"
[ -e "$H/$name.log" ] && no "$H/$name.log exists; not overwriting"
[ -e "$H/h_probe.passed" ] || no "the probe has not passed (block_h_probe.sh)"
h_checks; pkg_checks
session_dirs "$name"
echo "- $(utc) $name started (package copy $W, client $A3_CLIENT, model $model, DeepSeek ledger \$$spent, block H cap \$$CAP from a start of \$$START at $CAPDATE, isolation $MODE$([ "$MODE" = docker ] && echo ", image $H_IMAGE"))" >> "$L/progress.md"
proxy_up "$name" 2.50
if [ "$A3_CLIENT" = codex ]; then
  # the runner takes the model from BASELINE_CODEX_MODEL (config.toml and -m) and the binary from CODEX_BIN; in Docker
  # the image's own codex, no sandbox inside the container (CODEX_SANDBOX=none: bwrap does not start unprivileged)
  if [ "$MODE" = docker ]; then cbin=codex; sbx=none; else cbin="$CODEX_BIN"; sbx=workspace-write; fi
  agent_run "$name" env BASELINE_CODEX_MODEL="$model" CODEX_BIN="$cbin" CODEX_SANDBOX="$sbx" CODEX_WIRE_API="$H_CODEX_WIRE_API" \
    bash "$TOOLS/run_codex.sh" "$PKG_IN" "$PROXY_URL" 20 "$S" "$OUT_IN"
else
  # the runner takes the model from BASELINE_ANTHROPIC_MODEL and sets ANTHROPIC_MODEL and --model from it
  agent_run "$name" env BASELINE_ANTHROPIC_MODEL="$model" bash "$TOOLS/run_autoresearch.sh" "$PKG_IN" "$PROXY_URL" 20 "$S" "$OUT_IN"
fi
proxy_down
session_after "$name" a3 "$model" || exit 3
