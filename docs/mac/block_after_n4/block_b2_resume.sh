#!/bin/bash
# B2 after its stop at seed 1 (docs/PLAN_AFTER_N4.md, note of 2026-10-11 22:50 UTC): seed 2, then seed 3 in place of
# seed 1, one at a time, each started only if the step before passed its checks (block_b2_run.sh exits non-zero on a
# refusal or a stop, and this script ends there). Contains no key. The main checkout stays on the pinned commit, so
# this script and block_b2_run.sh are brought into genemila_scale_logs/b2_resume/ with git show and run from there.
# Start it detached, with the Mac kept awake, from the main checkout:
#   cd ~/Documents/Mila/Gene-Mila/gene-mila && DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i \
#     bash ../genemila_scale_logs/b2_resume/block_b2_resume.sh > ../genemila_scale_logs/block_b2_resume.log 2>&1 &
# It lifts the scaling driver's STOP file for the block's runs and puts it back when it ends, however it ends.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
D=$(cd "$(dirname "$0")" && pwd)
say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; echo "- $(date -u +%Y-%m-%dT%H:%MZ) block_b2_resume: $*" >> "$L/progress.md"; }
[ -n "$DEEPSEEK_API_KEY" ] || { echo "no DEEPSEEK_API_KEY in the environment; nothing started"; exit 1; }
pgrep -f scale_seq.sh > /dev/null && { echo "the scaling driver is running; nothing started"; exit 2; }
[ -e "$L/block_after_n4_stopped.txt" ] && { echo "the block is stopped ($L/block_after_n4_stopped.txt); nothing started"; exit 2; }
[ -e "$D/block_b2_run.sh" ] || { echo "no block_b2_run.sh beside this script in $D; nothing started"; exit 2; }
had_stop=0; [ -e "$L/STOP" ] && had_stop=1
trap '[ "$had_stop" = 1 ] && touch "$L/STOP"; unset DEEPSEEK_API_KEY' EXIT
rm -f "$L/STOP"
say "started (seed 2, then seed 3 in place of seed 1; block_b2_run.sh md5 $(md5 -q "$D/block_b2_run.sh"))"
for seed in 2 3; do
  bash "$D/block_b2_run.sh" "$seed" || { say "stopped at seed $seed (exit $?)"; exit 3; }
done
say "finished: seeds 2 and 3 passed; B2's readings are next"
