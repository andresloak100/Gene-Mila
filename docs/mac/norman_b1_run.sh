#!/bin/bash
# One B1 repeat of N4 (docs/PLAN_AFTER_N4.md, B1). Usage: norman_b1_run.sh <seed>. Contains no key: DEEPSEEK_API_KEY must
# be in the environment of the process that starts it (from API_KEY in ~/.zshenv). Runs from the worktree at 076282c.
S="$1"; [ -n "$S" ] || { echo "usage: $0 <seed>"; exit 1; }
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"; WT="$HOME/Documents/Mila/Gene-Mila/gene-mila-076282c"
n=norman_ds_from_n2_w4_r$S; d="$MAIN/runs/$n"
[ -n "$DEEPSEEK_API_KEY" ] || { echo "no key in the environment"; exit 1; }
[ "$(git -C "$WT" rev-parse --short=7 HEAD)" = "076282c" ] || { echo "worktree is not at 076282c"; exit 1; }
[ -e "$d" ] && { echo "$d exists; not overwriting"; exit 1; }
[ -f "$L/STOP" ] && { echo "STOP file present; $n not started"; exit 3; }
spent=$(sqlite3 "$MAIN/runs/spend_ledger.sqlite" "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'")
[ "$(echo "$spent > 41.37" | bc)" = 1 ] && { echo "ledger $spent > 41.37; $n not started"; exit 2; }
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (worktree code $(git -C "$WT" rev-parse --short HEAD), DeepSeek ledger \$$spent)" >> "$L/progress.md"
cd "$WT" || exit 1
"$MAIN/.venv/bin/python" run_research.py --minutes 20 --workers 4 --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro \
  --continue-from "$MAIN/runs/norman_control_replogle_w4_r0" --run-dir "$d" --set run.seed=$S \
  --set run.data_dir="$MAIN/data/norman" --set budget.ledger="$MAIN/runs/spend_ledger.sqlite" \
  --set budget.cumulative_usd.deepseek=48 --set budget.max_total_usd=1.3 > "$L/$n.log" 2>&1
rc=$?
unset DEEPSEEK_API_KEY
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$(sqlite3 "$MAIN/runs/spend_ledger.sqlite" "select round(sum(cost_usd),4) from spend where provider='deepseek'")" >> "$L/progress.md"
echo "RUN_DONE $n rc=$rc"
