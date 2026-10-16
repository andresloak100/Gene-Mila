#!/bin/bash
# Block F end to end: seeds 0, 2, 3 one at a time, each only if the one before passed. No key in it; start it from a
# login zsh as  DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i bash norman_f_chain.sh > block_f_chain.log 2>&1 &
# A seed whose .passed marker exists is skipped, so a chain stopped by a pre-run refusal (ledger, a lab run or the
# driver running, no key) resumes by starting it again the same way once the cause is fixed. A stopped block
# (block_f_stopped.txt) does not resume: norman_f_run.sh refuses until the cause is written up in the plan.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
had=0; [ -e "$L/STOP" ] && had=1
trap '[ "$had" = 1 ] && touch "$L/STOP"; unset DEEPSEEK_API_KEY' EXIT
rm -f "$L/STOP"
echo "$(date -u +%FT%TZ) block F started"
for s in 0 2 3; do
  [ -e "$L/norman_ga_ds_addstart_w4_r$s.passed" ] && { echo "$(date -u +%FT%TZ) seed $s passed before; skipped"; continue; }
  bash "$L/norman_f_run.sh" "$s" || { echo "$(date -u +%FT%TZ) block F stopped at seed $s"; exit 3; }
done
echo "$(date -u +%FT%TZ) block F finished: seeds 0, 2, 3 passed"
