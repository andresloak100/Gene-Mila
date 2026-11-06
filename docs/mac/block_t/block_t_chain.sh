#!/bin/bash
# Block T's chain (docs/PLAN_T_TABLE_AGENTS.md): six runs, one at a time, Adamson then Norman, seeds 0, 2, 3.
# DEEPSEEK_API_KEY must be in this process's environment; it is never printed or written. GEARS (claim #111) is
# paused before the chain and resumed after it by the operator, so nothing runs beside a paid run.
L="$HOME/Documents/Mila/Gene-Mila/genemila_t_logs"; HERE="$(cd "$(dirname "$0")" && pwd)"
for ds in adamson_cf norman; do for s in 0 2 3; do
  bash "$HERE/block_t_run.sh" "$ds" g0 "$s"; rc=$?
  [ "$rc" = 0 ] || { echo "$(date -u +%Y-%m-%dT%H:%MZ) chain stopped at ${ds} seed $s (exit $rc)" >> "$L/progress.md"; exit "$rc"; }
done; done
echo "$(date -u +%Y-%m-%dT%H:%MZ) block T finished: six runs passed" >> "$L/progress.md"; touch "$L/block_t.done"
