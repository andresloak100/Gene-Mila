#!/bin/bash
# Block H end to end (docs/PLAN_H_COMPARISON.md): the probe, then A4 (Biomni) seeds 0, 2, 3, then A3 (Claude Code)
# seeds 0, 2, 3, then A2 (the one-worker lab) seeds 0, 2, 3, one session at a time, each only if the one before
# passed. No key in it; start it detached from a login zsh (block F's note of 02:05 UTC: never from a tool shell):
#   cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_h
#   screen -dmS blockh zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" caffeinate -i bash block_h_chain.sh > block_h_chain.log 2>&1'
# To halt the chain between sessions: touch $H/STOP (never $L/STOP). A session whose .passed marker exists is skipped, so a chain stopped by a pre-session refusal (ledger, a lab run or
# the driver running, no key, no isolation) resumes by starting it again the same way once the cause is fixed. A
# stopped block (block_h_stopped.txt) does not resume: the scripts refuse until the cause is written up in the plan.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; H="$L/block_h"
# Block H's halt signal is $H/STOP, its own. $L/STOP belongs to the scaling driver (AGENTS.md: nobody creates or
# removes it) and this script no longer touches it: until 2026-11-01 it removed $L/STOP at its start and re-created it
# at its exit, so every short-lived chain (a refusal, a stopped probe) planted the file under the next chain, which
# then stopped between sessions with "STOP file present" (#51, comment 6553039740).
trap 'unset DEEPSEEK_API_KEY' EXIT
echo "$(date -u +%FT%TZ) block H started"
if [ -e "$H/h_probe.passed" ]; then echo "$(date -u +%FT%TZ) probe passed before; skipped"
else bash "$H/block_h_probe.sh" || { echo "$(date -u +%FT%TZ) block H stopped at the probe"; exit 3; }; fi
for arm in a4 a3; do
  for s in 0 2 3; do
    n=h_${arm}_r$s
    [ -e "$H/$n.passed" ] && { echo "$(date -u +%FT%TZ) $n passed before; skipped"; continue; }
    bash "$H/block_h_$arm.sh" "$s" || { echo "$(date -u +%FT%TZ) block H stopped at $n"; exit 3; }
  done
done
for s in 0 2 3; do
  n=adamson_cf_h_a2_ds_w1_r$s
  [ -e "$H/$n.passed" ] && { echo "$(date -u +%FT%TZ) $n passed before; skipped"; continue; }
  bash "$H/block_h_a2.sh" "$s" || { echo "$(date -u +%FT%TZ) block H stopped at $n"; exit 3; }
done
echo "$(date -u +%FT%TZ) block H finished: the probe, A4, A3 and A2, seeds 0, 2, 3 passed"
