#!/bin/bash
# Block H, arm A2 (docs/PLAN_H_COMPARISON.md): block G's run script with one worker. The settings of
# docs/PLAN_B4_SINGLE_WORKER.md on data/adamson_cf_clean_tables, DeepSeek planner + 1 worker, fresh start, code
# baa7dfd (the checkout gene-mila-baa7dfd, as G1, so A2 differs from A1 in the worker count only).
# Usage: block_h_a2.sh <seed 0|2|3>. No key in it: DEEPSEEK_API_KEY must be in the environment. Every check that can
# refuse comes before the run, so a refusal costs nothing.
G_COMMIT="baa7dfd"  # block G's code (docs/PLAN_G_CLEAN_ARM.md, note of 2026-10-16 23:40 UTC)
. "$(dirname "$0")/block_h_common.sh"
S="$1"; case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
WT="${G_WT:-$HOME/Documents/Mila/Gene-Mila/gene-mila-$G_COMMIT}"  # never the main checkout
n=adamson_cf_h_a2_ds_w1_r$S; d="$MAIN/runs/$n"; DATA="$MAIN/data/adamson_cf_clean_tables"
WANT="gene_annotation.json gene_constraint.json gene_sets.json ppi_network.json prior_network.json protein_annotation.json targets.json transcription_factors.json"
[ -e "$H/$n.log" ] && no "$H/$n.log exists; not overwriting"
[ -e "$d" ] && no "$d exists"
h_checks lab   # the key, the cap, isolation.txt (none is enough for the lab), STOP, a stopped block, other runs and proxies, the ledger gate
[ "$(git -C "$WT" rev-parse --short=7 HEAD)" = "$G_COMMIT" ] || no "$WT is not at $G_COMMIT"
[ -z "$(git -C "$WT" status --porcelain --untracked-files=no)" ] || no "$WT has changes"
# the bundle, as block G checks it: verify_bundle clean, added_knowledge empty, exactly the g1 files, the existing
# bundle's split_id, the knowledge summary within the knowledge-section budget of the code at $WT
[ -e "$DATA/manifest.json" ] || no "$DATA is not a bundle (docs/mac/block_g/prepare_clean_bundles.sh)"
PYTHONPATH="$WT" "$PY" - "$DATA" "$MAIN/data/adamson_cf" "$WANT" <<'PY' || no "$DATA is not the plan's bundle (above)"
import json, sys
from pathlib import Path
from genemila import research_state
from genemila.data.bundle import added_knowledge, verify_bundle
data, src, want = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].split()
m, ms = json.loads((data / "manifest.json").read_text()), json.loads((src / "manifest.json").read_text())
problems, added = verify_bundle(data), added_knowledge(data)
got = sorted(f.name for f in (data / "knowledge").iterdir() if f.is_file())
parts = []
for p in sorted((data / "knowledge").glob("*.json")):  # genemila.lab.Lab.knowledge_summary
    o = json.loads(p.read_text())
    if isinstance(o, dict) and isinstance(o.get("description"), str):
        parts.append(f"{p.stem}: {o['description'][:900]} (a dict with keys {', '.join(map(str, o))})")
    elif isinstance(o, dict):
        k = next(iter(o), None); parts.append(f"{p.stem}: dict of {len(o)} entries, e.g. {k!r}: {str(o[k])[:60]}")
    else:
        parts.append(f"{p.stem}: list of {len(o)}, e.g. {str(o[0])[:60] if o else ''}")
n, limit = len("; ".join(parts)), getattr(research_state, "KNOWLEDGE_SECTION_CHARS", research_state.SECTION_CHARS)
bad = [x for x, h in [(f"verify_bundle: {problems}", bool(problems)), (f"added knowledge {added}, not none", bool(added)),
                      (f"knowledge files {got}, not {want}", got != want),
                      (f"split_id {m.get('split_id')} is not {src.name}'s {ms.get('split_id')}", m.get("split_id") != ms.get("split_id")),
                      (f"knowledge summary {n} characters over the planner's knowledge-section budget {limit} of the code in use", n > limit)] if h]
for x in bad: print("PROBLEM:", x)
print(f"bundle {data.name}: split_id {m['split_id']}, knowledge {' '.join(got)}; knowledge summary {n} characters (section budget {limit})")
sys.exit(1 if bad else 0)
PY
echo "- $(utc) $n started (code $G_COMMIT in $WT, data $(basename "$DATA"), 1 worker, DeepSeek ledger \$$spent, block H cap \$$CAP from a start of \$$START at $CAPDATE)" >> "$L/progress.md"
cd "$WT" || exit 1
"$PY" run_research.py --minutes 20 --workers 1 --dataset adamson_cf --planner-provider deepseek --planner-model deepseek-v4-pro \
  --worker-provider deepseek --worker-model deepseek-flash --run-dir "$d" --set run.seed=$S \
  --set run.data_dir="$DATA" --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek="$CAP" \
  --set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5 --no-watchdog > "$H/$n.log" 2>&1
rc=$?
unset DEEPSEEK_API_KEY
after=$(ledger)
stop=""
if num "$after" && [ "$(echo "$after >= $spent" | bc)" = 1 ]; then cost=$(echo "$after - $spent" | bc)
else cost="?"; stop="$stop ledger unreadable or below its start after the run ('$after');"; fi
echo "- $(utc) $n finished rc=$rc DeepSeek ledger \$$after (run \$$cost)" >> "$L/progress.md"
[ "$rc" = 0 ] || stop="$stop exit code $rc;"
[ "$cost" = "?" ] || [ "$(echo "$cost <= 2.50" | bc)" = 1 ] || stop="$stop cost \$$cost over \$2.50;"
"$PY" - "$d" "$G_COMMIT" <<'PY' > "$H/$n.check.txt" || stop="$stop $(grep PROBLEM "$H/$n.check.txt" | tr '\n' ';')"
import json, sys
from pathlib import Path
d, commit = Path(sys.argv[1]), sys.argv[2]
if not (d / "summary.json").exists():
    print("PROBLEM: no summary.json"); sys.exit(1)
s = json.loads((d / "summary.json").read_text()); c = json.loads((d / "config.json").read_text())
pl, b, u = s.get("planner") or {}, s.get("best") or {}, s["llm_usage"]
print(f"run: code {s['base_commit'][:10]}, {s['duration_s']} s, seed {c['run']['seed']}, workers {c['run']['workers']}, data {Path(c['run']['data_dir']).name}, external knowledge {c['run'].get('external_knowledge')}, planner {pl.get('configured')} mixed {pl.get('mixed')} exhausted_at_min {pl.get('exhausted_at_min')}")
print(f"cost by the run: workers ${u['worker']['cost_usd']:.3f}, planner ${u['planner']['cost_usd']:.3f}")
print(f"selected {b.get('experiment_id')} ({b.get('model')}, {len(b.get('features') or [])} features) visible {b.get('score')}")
bad = [m for m, h in [("planner.mixed not false", pl.get("mixed") is not False), (f"duration_note {s.get('duration_note')}", bool(s.get("duration_note"))),
                      (f"not code {commit}", not s["base_commit"].startswith(commit)), ("not 1 worker", int(c["run"]["workers"]) != 1),
                      ("knowledge list other than the bundle's own", bool(c["run"].get("external_knowledge")))] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
cat "$H/$n.check.txt"
if [ -n "$stop" ]; then echo "$(utc) $n:$stop" >> "$H/block_h_stopped.txt"; echo "STOPPED:$stop"; exit 3; fi
touch "$H/$n.passed"; echo "RUN_DONE $n rc=0"
