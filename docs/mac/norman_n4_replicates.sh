#!/bin/bash
# Replicates of the paid Norman arm N4 with seeds 1 and 2, one after the other. Contains no key: DEEPSEEK_API_KEY must
# be in the environment of the process that starts it. Approved by Andres in the thread, 2026-10-11 19:10-19:16 UTC.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; M="$HOME/Documents/Mila/Gene-Mila/gene-mila"
cd "$M" || exit 1
[ -n "$DEEPSEEK_API_KEY" ] || { echo "no key in the environment"; exit 1; }
for s in 1 2; do
  n=norman_ds_from_n2_w4_r$s; d="$M/runs/$n"
  [ -e "$d" ] && { echo "$d exists; skipped"; continue; }
  [ -f "$L/STOP" ] && { echo "STOP file present; halted before $n"; break; }
  spent=$(sqlite3 runs/spend_ledger.sqlite "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'")
  [ "$(echo "$spent >= 38.50" | bc)" = 1 ] && { echo "ledger $spent >= 38.50; $n not started"; break; }
  echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (code $(git rev-parse --short HEAD), DeepSeek ledger \$$spent)" >> "$L/progress.md"
  .venv/bin/python run_research.py --minutes 20 --workers 4 --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro \
    --continue-from runs/norman_control_replogle_w4_r0 --run-dir "runs/$n" --set run.seed=$s \
    --set budget.cumulative_usd.deepseek=40 --set budget.max_total_usd=1.3 > "$L/$n.log" 2>&1
  rc=$?
  ( env -u DEEPSEEK_API_KEY .venv/bin/python analyze_run.py --run "$d" > "$L/$n.analysis.log" 2>&1 )
  echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$(sqlite3 runs/spend_ledger.sqlite "select round(sum(cost_usd),4) from spend where provider='deepseek'")" >> "$L/progress.md"
  echo "RUN_DONE $n rc=$rc"
done
unset DEEPSEEK_API_KEY
echo ALL_DONE
