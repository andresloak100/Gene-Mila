#!/bin/bash
# Codex CLI wrapper for block U: CellForge calls this as its `codex` binary (CODEX_CLI_BIN). It adds the
# provider overrides that point Codex at DeepSeek through the local spend proxy, then execs the real
# Codex with CellForge's own arguments untouched. Codex reads the key from OPENAI_API_KEY (set by
# CellForge from CODEX_API_KEY, in the process environment only).
#   BLOCK_U_PROXY   http://127.0.0.1:8787   (default; Codex appends /responses, which DeepSeek serves)
#   BLOCK_U_CODEX   the real codex binary       (default ~/.npm-global/bin/codex, 0.166.0)
PROXY="${BLOCK_U_PROXY:-http://127.0.0.1:8787}"
REAL="${BLOCK_U_CODEX:-$HOME/.npm-global/bin/codex}"
exec "$REAL" "$1" \
  -c model_provider=deepseek \
  -c "model_providers.deepseek={name=\"DeepSeek via block U proxy\",base_url=\"$PROXY\",env_key=\"OPENAI_API_KEY\",wire_api=\"responses\"}" \
  "${@:2}"
