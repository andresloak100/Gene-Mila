#!/bin/bash
# One B4 run (docs/PLAN_B4_SINGLE_WORKER.md): Norman, DeepSeek planner + 1 worker, fresh additive start, code ce1b530.
# Usage: norman_b4_run.sh <seed 0|2|3>. Contains no key: DEEPSEEK_API_KEY must be in the environment of the process.
S="$1"; case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"; WT="$HOME/Documents/Mila/Gene-Mila/gene-mila-ce1b530"
n=norman_ds_addstart_w1_r$S; d="$MAIN/runs/$n"; LEDGER="$MAIN/runs/spend_ledger.sqlite"
[ -n "$DEEPSEEK_API_KEY" ] || { echo "NOT STARTED: no key in the environment"; exit 1; }
[ "$(git -C "$WT" rev-parse --short=7 HEAD)" = "ce1b530" ] || { echo "NOT STARTED: worktree is not at ce1b530"; exit 1; }
[ -z "$(git -C "$WT" status --porcelain --untracked-files=no)" ] || { echo "NOT STARTED: worktree has changes"; exit 1; }
[ -e "$d" ] && { echo "NOT STARTED: $d exists"; exit 1; }
[ -e "$L/STOP" ] && { echo "NOT STARTED: STOP file present"; exit 3; }
[ -e "$L/block_b4_stopped.txt" ] && { echo "NOT STARTED: block stopped"; exit 3; }
pgrep -f '[r]un_research.py' > /dev/null && { echo "NOT STARTED: a lab run is running"; exit 1; }
[ "$(md5 -q "$MAIN/data/norman/knowledge/replogle2022_k562.json")" = d9eff528143dcd4d72c87393df724084 ] || { echo "NOT STARTED: knowledge file changed"; exit 1; }
spent=$(sqlite3 "$LEDGER" "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'")
[ "$(echo "$spent <= 49.50" | bc)" = 1 ] || { echo "NOT STARTED: ledger $spent above 49.50"; exit 2; }
echo "ok: all checks; ledger \$$spent"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (worktree ce1b530, DeepSeek ledger \$$spent)" >> "$L/progress.md"
cd "$WT" || exit 1
"$MAIN/.venv/bin/python" run_research.py --minutes 20 --workers 1 --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro \
  --worker-provider deepseek --worker-model deepseek-flash --run-dir "$d" --set run.seed=$S \
  --set run.data_dir="$MAIN/data/norman" --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek=52 \
  --set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5 --no-watchdog > "$L/$n.log" 2>&1
rc=$?
unset DEEPSEEK_API_KEY
after=$(sqlite3 "$LEDGER" "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'"); cost=$(echo "$after - $spent" | bc)
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$after (run \$$cost)" >> "$L/progress.md"
stop=""
[ "$rc" = 0 ] || stop="$stop exit code $rc;"
[ "$(echo "$cost <= 2.00" | bc)" = 1 ] || stop="$stop cost \$$cost over \$2.00;"
"$MAIN/.venv/bin/python" - "$d" <<'PY' > "$L/$n.check.txt" || stop="$stop $(grep PROBLEM "$L/$n.check.txt" | tr '\n' ';')"
import json, sys
from pathlib import Path
d = Path(sys.argv[1]); s = json.loads((d / "summary.json").read_text()); c = json.loads((d / "config.json").read_text())
pl, b, u = s.get("planner") or {}, s.get("best") or {}, s["llm_usage"]
print(f"run: code {s['base_commit'][:10]}, {s['duration_s']} s, seed {c['run']['seed']}, workers {c['run']['workers']}, knowledge {c['run'].get('external_knowledge')}, planner {pl.get('configured')} mixed {pl.get('mixed')} exhausted_at_min {pl.get('exhausted_at_min')}")
print(f"cost by the run: workers ${u['worker']['cost_usd']:.3f}, planner ${u['planner']['cost_usd']:.3f}")
print(f"selected {b.get('experiment_id')} ({b.get('model')}, {len(b.get('features') or [])} features) visible {b.get('score')}")
bad = [m for m, h in [("planner.mixed not false", pl.get("mixed") is not False), (f"duration_note {s.get('duration_note')}", bool(s.get("duration_note"))),
                      ("not code ce1b530", not s["base_commit"].startswith("ce1b530")), ("knowledge differs", c["run"].get("external_knowledge") != ["replogle2022_k562"])] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
cat "$L/$n.check.txt"
if [ -n "$stop" ]; then echo "$(date -u +%Y-%m-%dT%H:%MZ) $n:$stop" >> "$L/block_b4_stopped.txt"; echo "STOPPED:$stop"; exit 3; fi
touch "$L/$n.passed"; echo "RUN_DONE $n rc=0"
