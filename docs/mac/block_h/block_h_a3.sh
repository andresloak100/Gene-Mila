#!/bin/bash
# Block H, arm A3 (docs/PLAN_H_COMPARISON.md): one autoresearch-style Claude Code session on a fresh copy of the task
# package, 20 minutes, deepseek-v4-pro on DeepSeek's Anthropic-format route through the ledger proxy, web tools off,
# session cap $2.50. Usage: block_h_a3.sh <seed 0|2|3>. No key in it: DEEPSEEK_API_KEY must be in the environment.
# H_A3_MODEL=deepseek-flash only after the probe showed that Claude Code rejects the alias (a dated note in the plan).
. "$(dirname "$0")/block_h_common.sh"
S="$1"; case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
name=h_a3_r$S; model="${H_A3_MODEL:-deepseek-v4-pro}"
[ -e "$H/$name.log" ] && no "$H/$name.log exists; not overwriting"
[ -e "$H/h_probe.passed" ] || no "the probe has not passed (block_h_probe.sh)"
h_checks; pkg_checks
session_dirs "a3_r$S"
echo "- $(utc) $name started (package copy $W, model $model, DeepSeek ledger \$$spent, block H cap \$$CAP from a start of \$$START at $CAPDATE, isolation $MODE)" >> "$L/progress.md"
proxy_up "$name" 2.50
agent_run "$name" env ANTHROPIC_MODEL="$model" bash "$TOOLS/run_autoresearch.sh" "$PKG_IN" "$PROXY_URL" 20 "$S" "$OUT_IN"
proxy_down
session_after "$name" a3 "$model" || exit 3
