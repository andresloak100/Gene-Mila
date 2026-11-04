#!/bin/bash
# block_u_chain.sh: the rest of block U on Andres's "Yes, run them" of 2026-11-04 (docs/PLAN_U_CELLFORGE.md):
# three CellForge runs on Norman and two more on Adamson, one at a time, each a fresh CellForge pipeline
# (new workspace, new plan, new code) with a different internal split seed. The block cap stays $15 at the
# proxy, which carries the $1.86 run 1 spent. A failed run is a result and the chain goes on; the chain stops
# only when the proxy has refused a call (cap reached) or the Mac has a lab run going.
#   nohup caffeinate -i bash docs/mac/block_u/block_u_chain.sh > /dev/null 2>&1 &
set -u
CLONE="$HOME/Documents/Mila/Gene-Mila/gene-mila-norman"; B="$CLONE/docs/mac/block_u"
RUNS="$HOME/Documents/Mila/Gene-Mila/cellforge_runs"; P="$RUNS/progress.md"; touch "$P"
cd "$CLONE"
for spec in "norman cf_norman_s42 42" "norman cf_norman_s0 0" "norman cf_norman_s2 2" "adamson_cf cf_adamson_s0 0" "adamson_cf cf_adamson_s2 2"; do
  set -- $spec; DS="$1"; NAME="$2"; SEED="$3"
  if [ -f "$CLONE/docs/results/cellforge_ours/$NAME/run.done" ]; then echo "- $(date -u +%FT%TZ) chain: $NAME already done" >> "$P"; continue; fi
  refused=$(curl -s -m 2 http://127.0.0.1:8787/__status | python3 -c "import json,sys; print(json.load(sys.stdin).get('refused',0))" 2>/dev/null || echo 0)
  if [ "${refused:-0}" != "0" ]; then echo "- $(date -u +%FT%TZ) chain STOPPED before $NAME: proxy has refused $refused calls (cap)" >> "$P"; touch "$RUNS/block_u_chain.stopped"; exit 2; fi
  echo "- $(date -u +%FT%TZ) chain: starting $NAME ($DS, seed $SEED)" >> "$P"
  bash "$B/block_u_run.sh" "$DS" "$NAME" "$SEED" > "$RUNS/launch_$NAME.log" 2>&1; rc=$?
  echo "- $(date -u +%FT%TZ) chain: $NAME ended rc=$rc" >> "$P"
  if [ $rc -eq 3 ]; then echo "- $(date -u +%FT%TZ) chain STOPPED: $NAME not started ($(head -1 "$RUNS/launch_$NAME.log"))" >> "$P"; touch "$RUNS/block_u_chain.stopped"; exit 3; fi
done
echo "- $(date -u +%FT%TZ) chain: all runs attempted" >> "$P"; touch "$RUNS/block_u_chain.done"
