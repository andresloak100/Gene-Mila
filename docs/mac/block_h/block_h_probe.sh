#!/bin/bash
# Block H, the probe (docs/PLAN_H_COMPARISON.md, step 6): two proxy sessions of $0.05 each (ROADMAP D6's cap per
# round). One Biomni --probe round and one one-turn claude -p call, both through the ledger proxy, to check the two
# routes ROADMAP section 8 lists as unverified. No key in it: DEEPSEEK_API_KEY must be in the environment (the
# chain's). Every check comes before any spend.
. "$(dirname "$0")/block_h_common.sh"
name=h_probe
[ -e "$H/$name.passed" ] && { echo "probe passed before"; exit 0; }
[ -e "$H/$name.log" ] && no "$H/$name.log exists; not overwriting"
h_checks; pkg_checks
session_dirs "$name"
echo "- $(utc) $name started (DeepSeek ledger \$$spent, block H cap \$$CAP from a start of \$$START at $CAPDATE, isolation $MODE)" >> "$L/progress.md"
# 1. Biomni: one execute-to-observation round against deepseek-v4-pro (consecutive assistant messages); its run.json
#    lands in $O, where collect_handback.py reads it
proxy_up "$name" 0.05
agent_run "$name" "$TOOLS_PY" "$TOOLS/run_biomni.py" --package "$PKG_IN" --proxy "$PROXY_URL" --model deepseek-v4-pro \
  --minutes 2 --seed 0 --out "$OUT_IN" --probe
biomni_rc=$AGENT_RC
proxy_down
# 2. Claude Code: one turn on DeepSeek's Anthropic-format route (the proxy forwards /anthropic/v1/messages), the model
#    alias on a custom base URL, web tools off, as run_autoresearch.sh starts it
proxy_up "${name}_claude" 0.05
agent_run "${name}_claude" env ANTHROPIC_BASE_URL="$PROXY_URL/anthropic" ANTHROPIC_MODEL=deepseek-v4-pro \
  claude -p "Reply with the single word ok." --model deepseek-v4-pro --disallowedTools WebFetch,WebSearch \
  --strict-mcp-config --no-session-persistence
claude_rc=$AGENT_RC
proxy_down
AGENT_RC=0; [ "$biomni_rc" = 0 ] && [ "$claude_rc" = 0 ] || AGENT_RC="biomni=$biomni_rc,claude=$claude_rc"
session_after "$name" probe deepseek-v4-pro 0.10 || exit 3
echo "probe: biomni rc $biomni_rc, claude rc $claude_rc; served models, tokens and the other statuses (402 is the proxy's cap, 404 a wrong route, 502 the upstream) are in $H/$name.check.txt and $H/proxy/$name*.jsonl: record them in the plan's dated note before any fallback is disclosed"
