#!/bin/bash
# Block D end to end (docs/PLAN_D_DISCOVERY_ADAMSON.md): three discovery-mode runs on Adamson, seeds 0, 2, 3, one at a
# time, each only if the one before passed. No key in it; start it detached from a login zsh (never from a tool shell):
#   cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_d
#   screen -dmS blockd zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" caffeinate -i bash block_d_chain.sh > block_d_chain.log 2>&1'
# A run whose .passed marker exists is skipped, so a chain stopped by a pre-run refusal (ledger, a lab run or a proxy
# running, no key) resumes by starting it again the same way once the cause is fixed. A stopped block
# (block_d_stopped.txt) does not resume: block_d_run.sh refuses until the cause is written up in the plan.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; D="$L/block_d"
had=0; [ -e "$L/STOP" ] && had=1
trap '[ "$had" = 1 ] && touch "$L/STOP"; unset DEEPSEEK_API_KEY' EXIT
rm -f "$L/STOP"
echo "$(date -u +%FT%TZ) block D started"
for s in 0 2 3; do
  n=adamson_cf_d1_ds_w4_r${s}_discovery
  [ -e "$D/$n.passed" ] && { echo "$(date -u +%FT%TZ) $n passed before; skipped"; continue; }
  bash "$D/block_d_run.sh" "$s" || { echo "$(date -u +%FT%TZ) block D stopped at $n"; exit 3; }
done
echo "$(date -u +%FT%TZ) block D finished: adamson_cf d1 seeds 0, 2, 3 passed"
