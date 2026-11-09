#!/bin/bash
# block_u_chain_limits.sh: block U's rerun on Andres's "Rerun, state limits" of 2026-11-09 (docs/PLAN_U_CELLFORGE.md,
# notes). The same CellForge pipeline and the same $15 block cap at the proxy ($9.20 already spent); the only change
# is the task text, which now ends with docs/mac/block_u/machine_limits.md (the Mac's memory, its devices and the
# watchdog's 12 GB and 6-hour limits). Norman first (its table row is empty), then Adamson, one run at a time. A run
# starts only if the ledger plus a per-run estimate stays at or below the cap (AGENTS.md); a failed run is a result
# and the chain goes on; it stops when the proxy has refused a call or a run could not start.
#   python3 -c 'import subprocess; subprocess.Popen(["caffeinate","-i","bash","docs/mac/block_u/block_u_chain_limits.sh"], start_new_session=True)'
set -u
CLONE="$HOME/Documents/Mila/Gene-Mila/gene-mila-norman"; B="$CLONE/docs/mac/block_u"
RUNS="$HOME/Documents/Mila/Gene-Mila/cellforge_runs"; P="$RUNS/progress.md"; LEDGER="$RUNS/proxy/block_u_ledger.jsonl"; touch "$P"
read -r CAP _ < "$B/block_u_cap.txt"
EST=2.40   # per run: block U's dearest run so far ($1.89 for every phase up to autorun) plus the held-out agent and margin
cd "$CLONE"
for spec in "norman cf_norman_lim_s42 42" "norman cf_norman_lim_s0 0" "adamson_cf cf_adamson_lim_s0 0"; do
  set -- $spec; DS="$1"; NAME="$2"; SEED="$3"
  if [ -f "$CLONE/docs/results/cellforge_ours/$NAME/run.done" ]; then echo "- $(date -u +%FT%TZ) chain-limits: $NAME already done" >> "$P"; continue; fi
  refused=$(curl -s -m 2 http://127.0.0.1:8787/__status | python3 -c "import json,sys; print(json.load(sys.stdin).get('refused',0))" 2>/dev/null || echo 0)
  if [ "${refused:-0}" != "0" ]; then echo "- $(date -u +%FT%TZ) chain-limits STOPPED before $NAME: proxy has refused $refused calls (cap)" >> "$P"; touch "$RUNS/block_u_chain_limits.stopped"; exit 2; fi
  total=$(python3 -c "import json,sys; rows=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]; print(rows[-1]['total_usd'] if rows else 0)" "$LEDGER" 2>/dev/null || echo 0)
  if ! python3 -c "import sys; sys.exit(0 if float(sys.argv[1]) + float(sys.argv[2]) <= float(sys.argv[3]) else 1)" "$total" "$EST" "$CAP"; then
    echo "- $(date -u +%FT%TZ) chain-limits STOPPED before $NAME: ledger \$$total plus the \$$EST per-run estimate would pass the \$$CAP cap" >> "$P"; touch "$RUNS/block_u_chain_limits.stopped"; exit 2
  fi
  echo "- $(date -u +%FT%TZ) chain-limits: starting $NAME ($DS, seed $SEED, variant limits, ledger \$$total)" >> "$P"
  bash "$B/block_u_run.sh" "$DS" "$NAME" "$SEED" limits > "$RUNS/launch_$NAME.log" 2>&1; rc=$?
  echo "- $(date -u +%FT%TZ) chain-limits: $NAME ended rc=$rc" >> "$P"
  if [ $rc -eq 3 ]; then echo "- $(date -u +%FT%TZ) chain-limits STOPPED: $NAME not started ($(head -1 "$RUNS/launch_$NAME.log"))" >> "$P"; touch "$RUNS/block_u_chain_limits.stopped"; exit 3; fi
done
echo "- $(date -u +%FT%TZ) chain-limits: all runs attempted" >> "$P"; touch "$RUNS/block_u_chain_limits.done"
