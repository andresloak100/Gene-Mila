#!/bin/bash
# block_u_run.sh DATASET NAME [SEED]      DATASET: adamson_cf | norman      (docs/PLAN_U_CELLFORGE.md)
# One CellForge run on our exported training data, DeepSeek v4-pro for every agent, every call through the spend
# proxy, every step with receipts under docs/results/cellforge_ours/NAME/. Start it detached:
#   nohup caffeinate -i bash docs/mac/block_u/block_u_run.sh adamson_cf cf_adamson_s42 42 > /dev/null 2>&1 &
set -u
DS="${1:?dataset}"; NAME="${2:?run name}"; SEED="${3:-42}"
CLONE="$HOME/Documents/Mila/Gene-Mila/gene-mila-norman"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"
CF="$HOME/Documents/Mila/Gene-Mila/cellforge-6585ff9"; CFENV="$HOME/cellforge_env"
RUNS="$HOME/Documents/Mila/Gene-Mila/cellforge_runs"; WS="$RUNS/$NAME"; PROXYDIR="$RUNS/proxy"
B="$CLONE/docs/mac/block_u"; R="$CLONE/docs/results/cellforge_ours/$NAME"; PORT=8787; PROXY="http://127.0.0.1:$PORT"
case "$DS" in
  adamson_cf) EXPORT="$HOME/cellforge_adamson_export_corrected_20261028"; BUNDLE="$MAIN/data/adamson_cf"; VERSUS="$MAIN/runs/newcode_opus_w4_r0";;
  norman)     EXPORT="$HOME/cellforge_norman_export";                   BUNDLE="$MAIN/data/norman";     VERSUS="$MAIN/runs/norman_ds_from_n2_w4_r1";;
  *) echo "unknown dataset $DS"; exit 2;;
esac
mkdir -p "$R" "$PROXYDIR" "$WS/data/datasets"; rm -f "$R/run.failed"
P="$RUNS/progress.md"; touch "$P"
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { echo "- $(now) $NAME: $*" >> "$P"; echo "$*"; }
fail() { say "FAILED: $*"; touch "$R/run.failed"; rmdir "$RUNS/.lock" 2>/dev/null; exit 1; }

# ---- guards -------------------------------------------------------------------------------------------------
[ -f "$B/block_u_cap.txt" ] || { echo "NOT STARTED: $B/block_u_cap.txt missing (Andres's cap, see the plan)"; exit 3; }
read -r CAP CAPSTART < "$B/block_u_cap.txt"
[ -n "${API_KEY:-}" ] || { echo "NOT STARTED: API_KEY is not in the environment"; exit 3; }
pgrep -f "run_research\.py" > /dev/null && { echo "NOT STARTED: a lab run is running"; exit 3; }
mkdir "$RUNS/.lock" 2>/dev/null || { echo "NOT STARTED: another block U run holds $RUNS/.lock"; exit 3; }
trap 'rmdir "$RUNS/.lock" 2>/dev/null' EXIT
[ -f "$EXPORT/cellforge_input.h5ad" ] && [ -f "$EXPORT/heldout_perturbations.json" ] && [ -f "$EXPORT/TASK.md" ] || fail "export incomplete at $EXPORT"
[ -x "$CFENV/bin/cellforge" ] || fail "no cellforge entry point in $CFENV"

# ---- proxy (one per block; its cap is the block cap, carried across restarts by the ledger) ------------------
if ! curl -s -m 2 "$PROXY/__status" > /dev/null; then
  nohup python3 "$B/deepseek_proxy.py" --port $PORT --ledger "$PROXYDIR/block_u_ledger.jsonl" --cap-usd "$CAP" >> "$PROXYDIR/proxy.log" 2>&1 &
  for i in $(seq 1 20); do sleep 0.5; curl -s -m 2 "$PROXY/__status" > /dev/null && break; done
fi
curl -s -m 2 "$PROXY/__status" > "$R/proxy_status_start.json" || fail "proxy did not start"
START="$(now)"; say "started (dataset $DS, seed $SEED, cap \$$CAP from $CAPSTART, proxy $(cat "$R/proxy_status_start.json"))"

# ---- environment for CellForge and Codex: the key lives only here ------------------------------------------
export CELLFORGE_WORKSPACE_DIR="$WS" DEEPSEEK_API_KEY="$API_KEY" DEEPSEEK_BASE_URL="$PROXY" MODEL_NAME="deepseek-v4-pro"
export CODEGEN_BACKEND="codex" CODEX_AUTH_MODE="api" CODEX_API_KEY="$API_KEY" CODEX_CLI_BIN="$B/codex_deepseek.sh" CODEX_MODEL="deepseek-v4-pro"
export BLOCK_U_PROXY="$PROXY" PATH="$CFENV/bin:$PATH" PYTHONUNBUFFERED=1
unset OPENAI_API_KEY ANTHROPIC_API_KEY OPENAI_BASE_URL
H5="$WS/data/datasets/$DS.h5ad"; ln -sfn "$EXPORT/cellforge_input.h5ad" "$H5"; cp "$EXPORT/TASK.md" "$WS/task.md"

# ---- receipts: NAME.command.txt / .log / .exit / .runtime.json, a wall-clock limit, key-like strings redacted ---
step() {  # step NAME LIMIT_SECONDS WORKDIR -- COMMAND...   (a step whose .exit is already 0 is skipped: resume)
  local name="$1" limit="$2" wd="$3"; shift 3; [ "${1:-}" = "--" ] && shift
  if [ -f "$R/$name.exit" ] && [ "$(cat "$R/$name.exit")" = "0" ]; then say "$name skipped: already done (exit 0 on record)"; return 0; fi
  printf '%s\n' "$*" > "$R/$name.command.txt"
  local s0 start end rc pid; s0=$(date +%s); start=$(now)
  ( cd "$wd" && nice -n 19 "$@" ) > "$R/$name.log" 2>&1 & pid=$!
  while kill -0 $pid 2>/dev/null; do
    sleep 20
    if [ $(( $(date +%s) - s0 )) -gt "$limit" ]; then pkill -TERM -P $pid; sleep 5; pkill -KILL -P $pid; kill -KILL $pid 2>/dev/null; echo "KILLED: wall-clock limit ${limit}s" >> "$R/$name.log"; fi
  done
  wait $pid; rc=$?; end=$(now)
  LC_ALL=C sed -i '' -E 's/sk-[A-Za-z0-9]{16,}/[REDACTED]/g' "$R/$name.log"
  echo "$rc" > "$R/$name.exit"
  python3 -c "import json,sys,platform; json.dump({'start_utc':sys.argv[2],'end_utc':sys.argv[3],'wall_seconds':int(sys.argv[4]),'exit':int(sys.argv[5]),'cwd':sys.argv[6],'machine':platform.platform()},open(sys.argv[1],'w'),indent=1)" "$R/$name.runtime.json" "$start" "$end" $(( $(date +%s) - s0 )) "$rc" "$wd"
  say "$name exit $rc after $(( $(date +%s) - s0 ))s, proxy $(curl -s -m 2 "$PROXY/__status")"
  return $rc
}
CFARGS=(--workspace "$WS" --dataset-path "$H5" --task-file "$WS/task.md")

# 0. probe: one tiny Codex call through the proxy, proving the Responses path to DeepSeek
OPENAI_API_KEY="$API_KEY" step probe 300 "$WS" -- "$B/codex_deepseek.sh" exec --ignore-user-config --ignore-rules --ephemeral --skip-git-repo-check -s read-only -C "$WS" -m deepseek-v4-pro -o "$R/probe.last.md" 'Reply with exactly the text PROBE_OK and nothing else.' || fail "probe"
grep -q "PROBE_OK" "$R/probe.last.md" || fail "probe did not answer PROBE_OK"
# 1-4. CellForge's own phases, unchanged
step task_analysis   3600  "$WS" -- cellforge "${CFARGS[@]}" --phase task_analysis   || fail "task_analysis"
step method_design   3600  "$WS" -- cellforge "${CFARGS[@]}" --phase method_design   || fail "method_design"
step code_generation 10800 "$WS" -- cellforge "${CFARGS[@]}" --phase code_generation --codegen-backend codex || fail "code_generation"
# CellForge resolves its --codex-prompt-file default against the workspace, not its package, so the package path is passed
step autorun         21600 "$WS" -- cellforge "${CFARGS[@]}" --phase autorun --executor local --workers 1 --split-seed "$SEED" --codex-prompt-file "$CF/cellforge/autorun/autoresearch_prompt.md" || fail "autorun"
# 5. held-out predictions by the same coding agent, then the full run of its script
CODEDIR="$(ls -d "$WS"/data/codes/*/ 2>/dev/null | head -1)"; [ -n "$CODEDIR" ] || fail "no generated code dir"
cp "$EXPORT/heldout_perturbations.json" "$EXPORT/TASK.md" "$CODEDIR"; ln -sfn "$EXPORT/cellforge_input.h5ad" "$CODEDIR/training.h5ad"
OPENAI_API_KEY="$API_KEY" step predict_heldout_agent 10800 "$CODEDIR" -- "$B/codex_deepseek.sh" exec --ignore-user-config --ignore-rules --ephemeral --skip-git-repo-check -s workspace-write -C "$CODEDIR" -m deepseek-v4-pro -o "$R/predict_heldout_agent.last.md" "$(cat "$B/heldout_prompt.md")" || fail "predict_heldout agent"
[ -f "$CODEDIR/predict_heldout.py" ] || fail "agent wrote no predict_heldout.py"
step predict_heldout 21600 "$CODEDIR" -- python predict_heldout.py --data training.h5ad --heldout heldout_perturbations.json --out predictions.npz || fail "predict_heldout"
[ -f "$CODEDIR/predictions.npz" ] || fail "no predictions.npz"
# 6. score once, sealed, with the bridge from the lab venv (no DeepSeek key in this step)
DEEPSEEK_API_KEY= CODEX_API_KEY= API_KEY= step score 3600 "$CLONE" -- "$MAIN/.venv/bin/python" tools/cellforge_bridge.py score --bundle "$BUNDLE" --pred "$CODEDIR/predictions.npz" --name "$NAME" --versus "$VERSUS" --out "docs/results/cellforge_ours/$NAME.md" || fail "score"
# 7. collect: workspace files (no data, no checkpoints over 5 MB), the proxy ledger slice, status
mkdir -p "$R/workspace"; for d in analyses plans codes; do [ -d "$WS/data/$d" ] && rsync -a --exclude '*.h5ad' --exclude '*.npz' --max-size=5m "$WS/data/$d" "$R/workspace/"; done
python3 - "$PROXYDIR/block_u_ledger.jsonl" "$START" "$R/proxy_ledger.jsonl" "$R/cost.json" <<'PY'
import json, sys
src, start, dst, summ = sys.argv[1:]
rows = [json.loads(l) for l in open(src)]; mine = [r for r in rows if r["t"] >= start]
open(dst, "w").write("".join(json.dumps(r) + "\n" for r in mine))
json.dump({"calls": len(mine), "usd_peak_rates": round(sum(r["usd"] for r in mine), 4), "prompt_tokens": sum(r["prompt_tokens"] for r in mine),
           "cache_hit_tokens": sum(r["cache_hit_tokens"] for r in mine), "completion_tokens": sum(r["completion_tokens"] for r in mine),
           "calls_without_usage": sum(1 for r in mine if not r["usage_seen"]), "block_total_usd": rows[-1]["total_usd"] if rows else 0}, open(summ, "w"), indent=1)
PY
curl -s -m 2 "$PROXY/__status" > "$R/proxy_status_end.json"
grep -rlE "sk-[A-Za-z0-9]{16,}" "$R" && fail "key-like string in receipts" || true
say "DONE: cost $(cat "$R/cost.json" | tr -d '\n ')"; touch "$R/run.done"
