#!/bin/bash
# B4 end to end: seeds 0, 2, 3 one at a time, each only if the one before passed. No key in it; start it from a login
# zsh as  DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i bash norman_b4_chain.sh > block_b4_chain.log 2>&1 &
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
had=0; [ -e "$L/STOP" ] && had=1
trap '[ "$had" = 1 ] && touch "$L/STOP"; unset DEEPSEEK_API_KEY' EXIT
rm -f "$L/STOP"
echo "$(date -u +%FT%TZ) B4 started"
for s in 0 2 3; do bash "$L/norman_b4_run.sh" "$s" || { echo "$(date -u +%FT%TZ) B4 stopped at seed $s"; exit 3; }; done
echo "$(date -u +%FT%TZ) B4 finished: seeds 0, 2, 3 passed"
