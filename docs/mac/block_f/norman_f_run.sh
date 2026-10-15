#!/bin/bash
# One block F run (docs/PLAN_F_GENOME_ANNOTATION.md): B2's settings on data/norman_ga (data/norman plus the genome
# annotation file), DeepSeek planner + 4 workers, fresh additive start, code ce1b530.
# Usage: norman_f_run.sh <seed 0|2|3>. Contains no key: DEEPSEEK_API_KEY must be in the environment of the process.
S="$1"; case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"; WT="$HOME/Documents/Mila/Gene-Mila/gene-mila-ce1b530"
n=norman_ga_ds_addstart_w4_r$S; d="$MAIN/runs/$n"; LEDGER="$MAIN/runs/spend_ledger.sqlite"; DATA="$MAIN/data/norman_ga"
[ -n "$DEEPSEEK_API_KEY" ] || { echo "NOT STARTED: no key in the environment"; exit 1; }
[ -s "$L/block_f_cap.txt" ] || { echo "NOT STARTED: no block cap (docs/PLAN_F_GENOME_ANNOTATION.md, Money)"; exit 1; }
CAP="$(cat "$L/block_f_cap.txt")"
[ "$(git -C "$WT" rev-parse --short=7 HEAD)" = "ce1b530" ] || { echo "NOT STARTED: worktree is not at ce1b530"; exit 1; }
[ -z "$(git -C "$WT" status --porcelain --untracked-files=no)" ] || { echo "NOT STARTED: worktree has changes"; exit 1; }
[ -e "$d" ] && { echo "NOT STARTED: $d exists"; exit 1; }
[ -e "$L/STOP" ] && { echo "NOT STARTED: STOP file present"; exit 3; }
[ -e "$L/block_f_stopped.txt" ] && { echo "NOT STARTED: block stopped"; exit 3; }
pgrep -f '[r]un_research.py' > /dev/null && { echo "NOT STARTED: a lab run is running"; exit 1; }
[ "$(md5 -q "$DATA/knowledge/replogle2022_k562.json")" = d9eff528143dcd4d72c87393df724084 ] || { echo "NOT STARTED: Replogle file changed"; exit 1; }
[ "$(md5 -q "$DATA/knowledge/gene_annotation.json")" = 3f6aca1fc91cccdd5b684656d7f54963 ] || { echo "NOT STARTED: annotation file changed"; exit 1; }
# the planner sees every knowledge file in one section cut at 2,500 characters (research_state.SECTION_CHARS at
# ce1b530): the new file must not push the Replogle description out of it, or the arm would differ from B2 twice
"$MAIN/.venv/bin/python" - "$DATA/knowledge" <<'PY' || { echo "NOT STARTED: knowledge summary over 2,500 characters"; exit 1; }
import json, sys
from pathlib import Path
parts = []
for p in sorted(Path(sys.argv[1]).glob("*.json")):  # genemila.lab.Lab.knowledge_summary at ce1b530
    o = json.loads(p.read_text())
    if isinstance(o, dict) and isinstance(o.get("description"), str):
        parts.append(f"{p.stem}: {o['description'][:900]} (a dict with keys {', '.join(map(str, o))})")
    elif isinstance(o, dict):
        k = next(iter(o), None); parts.append(f"{p.stem}: dict of {len(o)} entries, e.g. {k!r}: {str(o[k])[:60]}")
    else:
        parts.append(f"{p.stem}: list of {len(o)}, e.g. {str(o[0])[:60] if o else ''}")
s = "; ".join(parts); print(f"knowledge summary {len(s)} characters"); sys.exit(0 if len(s) <= 2500 else 1)
PY
spent=$(sqlite3 "$LEDGER" "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'")
[ "$(echo "$spent + 2.50 <= $CAP" | bc)" = 1 ] || { echo "NOT STARTED: ledger $spent plus the run's caps above the block cap $CAP"; exit 2; }
echo "ok: all checks; ledger \$$spent, block cap \$$CAP"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (worktree ce1b530, data norman_ga, DeepSeek ledger \$$spent)" >> "$L/progress.md"
cd "$WT" || exit 1
"$MAIN/.venv/bin/python" run_research.py --minutes 20 --workers 4 --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro \
  --worker-provider deepseek --worker-model deepseek-flash --run-dir "$d" --set run.seed=$S \
  --set run.data_dir="$DATA" --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek="$CAP" \
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
store = d / "feature_store"
uses = sorted(p.stem for p in store.glob("*.py") if "gene_annotation" in p.read_text()) if store.exists() else []
print(f"features reading gene_annotation: {len(uses)} {uses[:20]}")
bad = [m for m, h in [("planner.mixed not false", pl.get("mixed") is not False), (f"duration_note {s.get('duration_note')}", bool(s.get("duration_note"))),
                      ("not code ce1b530", not s["base_commit"].startswith("ce1b530")),
                      ("knowledge differs", sorted(c["run"].get("external_knowledge") or []) != ["gene_annotation", "replogle2022_k562"])] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
cat "$L/$n.check.txt"
if [ -n "$stop" ]; then echo "$(date -u +%Y-%m-%dT%H:%MZ) $n:$stop" >> "$L/block_f_stopped.txt"; echo "STOPPED:$stop"; exit 3; fi
touch "$L/$n.passed"; echo "RUN_DONE $n rc=0"
