#!/bin/bash
# Block H, arm A4 (docs/PLAN_H_COMPARISON.md): one Biomni session on a fresh copy of the task package, 20 minutes,
# deepseek-v4-pro through the ledger proxy, session cap $2.50. Usage: block_h_a4.sh <seed 0|2|3>. No key in it:
# DEEPSEEK_API_KEY must be in the environment. Every check that can refuse comes before any spend.
. "$(dirname "$0")/block_h_common.sh"
S="$1"; case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
name=h_a4_r$S
[ -e "$H/$name.log" ] && no "$H/$name.log exists; not overwriting"
[ -e "$H/h_probe.passed" ] || no "the probe has not passed (block_h_probe.sh)"
h_checks; pkg_checks
BIOMNI_RATE=$(miss_rate deepseek-v4-pro) || exit 1
session_dirs "$name"
echo "- $(utc) $name started (package copy $W, DeepSeek ledger \$$spent, block H cap \$$CAP from a start of \$$START at $CAPDATE, isolation $MODE$([ "$MODE" = docker ] && echo ", image $H_IMAGE"))" >> "$L/progress.md"
proxy_up "$name" 2.50
agent_run "$name" "$TOOLS_PY" "$TOOLS/run_biomni.py" --package "$PKG_IN" --proxy "$PROXY_URL" --model deepseek-v4-pro \
  --minutes 20 --seed "$S" --out "$OUT_IN" --miss-usd-per-mtok "$BIOMNI_RATE"
proxy_down
session_after "$name" a4 deepseek-v4-pro || exit 3
