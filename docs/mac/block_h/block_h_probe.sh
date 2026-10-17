#!/bin/bash
# Block H, the probe (docs/PLAN_H_COMPARISON.md, step 6): two proxy sessions of $0.05 each (ROADMAP D6's cap per
# round). One Biomni --probe round and one one-turn call of the A3 client (A3_CLIENT in block_h_common.sh: codex, the
# default, through run_codex.sh --probe; or claude -p), both through the ledger proxy, to check the routes ROADMAP
# section 8 and the plan's note of 2026-10-17 list as unverified. No key in it: DEEPSEEK_API_KEY must be in the
# environment (the chain's). Every check comes before any spend.
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
# 2. The A3 client, one short turn as the arm starts it:
#    codex: run_codex.sh --probe, the prompt "Run the shell command `ls` and then reply with the single word ok." (one
#    tool round trip: a shell call, its result, a second completion), the private CODEX_HOME with the provider at
#    <proxy>/v1 in the wire format H_CODEX_WIRE_API (responses, the proxy's /v1/responses route, in both modes; chat,
#    the /v1/chat/completions route, only for a build before 0.95.0), the model alias, web search off, a read-only
#    sandbox; its run.json lands in $O/codex_probe, beside Biomni's. It settles what the plan's note of 2026-10-17
#    lists as unverified: that this Codex starts on a custom provider with no login, posts to the route the wire format
#    names (two 404 rows look alike only at a glance: one with "refused": "no such route" and a route other than
#    /v1/responses is the proxy's own, Codex posted elsewhere, Claude Code is the fallback; one with route
#    /v1/responses and "priced": false is DeepSeek's, it does not serve /v1/responses, the proxy maps the route to
#    /responses and the probe runs again), that the proxy prices the call (a 502 row
#    means DeepSeek's usage fields on the route are not the ones the proxy prices; it halts rather than count zero),
#    and that the tool round trip completes (at least two status-200 rows in h_probe_codex.jsonl; a 400 after the
#    first 200 means the route is unfit for the arm, plan note item 7).
#    claude: one claude -p turn ("Reply with the single word ok.") on DeepSeek's Anthropic-format route (the proxy
#    forwards /anthropic/v1/messages), the model alias on a custom base URL, web tools off, as run_autoresearch.sh
#    starts it.
if [ "$A3_CLIENT" = codex ]; then
  proxy_up "${name}_codex" 0.05
  if [ "$MODE" = docker ]; then cbin=codex; sbx=none; else cbin="$CODEX_BIN"; sbx=read-only; fi
  agent_run "${name}_codex" env CODEX_BIN="$cbin" CODEX_SANDBOX="$sbx" CODEX_WIRE_API="$H_CODEX_WIRE_API" \
    bash "$TOOLS/run_codex.sh" --probe "$PKG_IN" "$PROXY_URL" 2 0 "$OUT_IN/codex_probe"
else
  proxy_up "${name}_claude" 0.05
  agent_run "${name}_claude" env ANTHROPIC_BASE_URL="$PROXY_URL/anthropic" ANTHROPIC_MODEL=deepseek-v4-pro \
    claude -p "Reply with the single word ok." --model deepseek-v4-pro --disallowedTools WebFetch,WebSearch \
    --strict-mcp-config --no-session-persistence
fi
client_rc=$AGENT_RC
proxy_down
AGENT_RC=0; [ "$biomni_rc" = 0 ] && [ "$client_rc" = 0 ] || AGENT_RC="biomni=$biomni_rc,$A3_CLIENT=$client_rc"
session_after "$name" probe deepseek-v4-pro 0.10 || exit 3
echo "probe: biomni rc $biomni_rc, $A3_CLIENT rc $client_rc; served models, tokens and the other statuses (402 is the proxy's cap, 404 a wrong route, 502 the upstream) are in $H/$name.check.txt and $H/proxy/$name*.jsonl: record them in the plan's dated note before any fallback is disclosed$([ "$A3_CLIENT" = codex ] && echo "; codex is cleared for A3 only with at least two status-200 rows in $H/proxy/${name}_codex.jsonl and no 400 (plan note item 7)")"
