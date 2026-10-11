#!/bin/bash
# B2 end to end (docs/PLAN_AFTER_N4.md, B2), so the block finishes even if nobody is watching: the free control, then
# the paid seeds 0, 1 and 2, one at a time, each started only if the step before passed its checks (each script
# exits non-zero on a refusal or a stop, and the chain ends there). Contains no key. Start it detached, with the Mac
# kept awake, from the main checkout:
#   cd ~/Documents/Mila/Gene-Mila/gene-mila && DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i \
#     bash docs/mac/block_after_n4/block_b2_chain.sh > ../genemila_scale_logs/block_b2_chain.log 2>&1 &
# It lifts the scaling driver's STOP file for the block's runs and puts it back when it ends, however it ends.
M="$HOME/Documents/Mila/Gene-Mila/gene-mila"; L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
D="$M/docs/mac/block_after_n4"
say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; echo "- $(date -u +%Y-%m-%dT%H:%MZ) block_b2_chain: $*" >> "$L/progress.md"; }
[ -n "$DEEPSEEK_API_KEY" ] || { echo "no DEEPSEEK_API_KEY in the environment; nothing started"; exit 1; }
pgrep -f scale_seq.sh > /dev/null && { echo "the scaling driver is running; nothing started"; exit 2; }
had_stop=0; [ -e "$L/STOP" ] && had_stop=1
trap '[ "$had_stop" = 1 ] && touch "$L/STOP"; unset DEEPSEEK_API_KEY' EXIT
rm -f "$L/STOP"
say "started (the control, then seeds 0, 1, 2)"
# the control is free: it runs with no key in its environment
env -u DEEPSEEK_API_KEY -u API_KEY bash "$D/block_b2_control.sh" || { say "stopped after the control (exit $?)"; exit 3; }
for seed in 0 1 2; do
  bash "$D/block_b2_run.sh" "$seed" || { say "stopped at seed $seed (exit $?)"; exit 3; }
done
say "finished: the control and seeds 0, 1, 2 passed; B2's readings are next"
