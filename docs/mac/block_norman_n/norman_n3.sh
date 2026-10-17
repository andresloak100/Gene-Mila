#!/bin/bash
# Paid Norman arm N3 (NORMAN_PLAN section 6 step 8). Contains no key: DEEPSEEK_API_KEY must be in the environment
# of the process that starts it. Approved by Andres in the thread, 2026-10-11 15:34 UTC; DeepSeek cap $34 total.
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; M="$HOME/Documents/Mila/Gene-Mila/gene-mila"
cd "$M" || exit 1
n=norman_ds_replogle_w4_r0; d="$M/runs/$n"
[ -n "$DEEPSEEK_API_KEY" ] || { echo "no key in the environment"; exit 1; }
[ -e "$d" ] && { echo "$d exists; not overwriting"; exit 1; }
spent=$(sqlite3 runs/spend_ledger.sqlite "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'")
[ "$(echo "$spent >= 33.50" | bc)" = 1 ] && { echo "ledger $spent >= 33.50; not started"; exit 2; }
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (code $(git rev-parse --short HEAD), DeepSeek ledger \$$spent)" >> "$L/progress.md"
.venv/bin/python run_research.py --minutes 20 --workers 4 --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro \
  --run-dir "runs/$n" --set budget.cumulative_usd.deepseek=34 --set budget.max_total_usd=2.2 > "$L/$n.log" 2>&1
rc=$?
unset DEEPSEEK_API_KEY
.venv/bin/python analyze_run.py --run "$d" > "$L/$n.analysis.log" 2>&1
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$(sqlite3 runs/spend_ledger.sqlite "select round(sum(cost_usd),4) from spend where provider='deepseek'")" >> "$L/progress.md"
echo "RUN_DONE rc=$rc"
