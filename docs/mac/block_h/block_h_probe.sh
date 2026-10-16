#!/bin/bash
# Block H, the probe (docs/PLAN_H_COMPARISON.md, step 6): session cap $0.05. One Biomni --probe round and one one-turn
# claude -p call, both through the ledger proxy, to check the two routes ROADMAP section 8 lists as unverified. No key
# in it: DEEPSEEK_API_KEY must be in the environment (the chain's). Every check comes before any spend.
. "$(dirname "$0")/block_h_common.sh"
name=h_probe
[ -e "$H/$name.passed" ] && { echo "probe passed before"; exit 0; }
[ -e "$H/$name.log" ] && no "$H/$name.log exists; not overwriting"
h_checks; pkg_checks
session_dirs "$name"
echo "- $(utc) $name started (DeepSeek ledger \$$spent, block H cap \$$CAP from a start of \$$START at $CAPDATE, isolation $MODE)" >> "$L/progress.md"
proxy_up "$name" 0.05
# 1. Biomni: one execute-to-observation round against deepseek-v4-pro (consecutive assistant messages)
agent_run "$name" python "$TOOLS/run_biomni.py" --package "$PKG_IN" --proxy "$PROXY_URL" --model deepseek-v4-pro \
  --minutes 2 --seed 0 --out "$OUT_IN/biomni" --probe
biomni_rc=$AGENT_RC
# 2. Claude Code: one turn on DeepSeek's Anthropic-format route, the model alias on a custom base URL, web tools off
agent_run "${name}_claude" env ANTHROPIC_BASE_URL="$PROXY_URL" ANTHROPIC_MODEL=deepseek-v4-pro claude -p "Reply with the single word ok." \
  --model deepseek-v4-pro --disallowedTools WebFetch,WebSearch
claude_rc=$AGENT_RC
proxy_down
AGENT_RC=0; [ "$biomni_rc" = 0 ] && [ "$claude_rc" = 0 ] || AGENT_RC="biomni=$biomni_rc,claude=$claude_rc"
cat "$H/${name}_claude.log" >> "$H/$name.log"
session_after "$name" probe deepseek-v4-pro 0.05 || exit 3
echo "probe: biomni rc $biomni_rc, claude rc $claude_rc; the served models and tokens are in $H/$name.check.txt and $H/proxy/$name.jsonl: record them in the plan's dated note"
