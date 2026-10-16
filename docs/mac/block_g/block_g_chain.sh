#!/bin/bash
# Block G end to end: twelve runs one at a time, each only if the one before passed. Adamson first, then Norman; in
# each dataset the two arms interleave seeds (g0 r0, g1 r0, g0 r2, g1 r2, g0 r3, g1 r3), so a stop leaves the arms
# balanced. No key in it; start it detached from a login zsh (block F's note of 02:05 UTC: never from a tool shell):
#   cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs
#   screen -dmS blockg zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" caffeinate -i bash block_g_chain.sh > block_g_chain.log 2>&1'
# A run whose .passed marker exists is skipped, so a chain stopped by a pre-run refusal (ledger, a lab run or the
# driver running, no key) resumes by starting it again the same way once the cause is fixed. A stopped block
# (block_g_stopped.txt) does not resume: block_g_run.sh refuses until the cause is written up in the plan.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
had=0; [ -e "$L/STOP" ] && had=1
trap '[ "$had" = 1 ] && touch "$L/STOP"; unset DEEPSEEK_API_KEY' EXIT
rm -f "$L/STOP"
echo "$(date -u +%FT%TZ) block G started"
for ds in adamson_cf norman; do
  for s in 0 2 3; do
    for arm in g0 g1; do
      n=${ds}_${arm}_ds_w4_r$s
      [ -e "$L/$n.passed" ] && { echo "$(date -u +%FT%TZ) $n passed before; skipped"; continue; }
      bash "$L/block_g_run.sh" "$ds" "$arm" "$s" || { echo "$(date -u +%FT%TZ) block G stopped at $n"; exit 3; }
    done
  done
done
echo "$(date -u +%FT%TZ) block G finished: adamson_cf and norman, g0 and g1, seeds 0, 2, 3 passed"
