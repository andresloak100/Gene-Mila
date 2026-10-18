#!/bin/bash
# One block D run (docs/PLAN_D_DISCOVERY_ADAMSON.md): block G's g1 settings on data/adamson_cf_clean_tables (DeepSeek
# planner deepseek-v4-pro, 4 deepseek-flash workers, 20 minutes, fresh start) with discovery mode on
# (schedule.discovery=true, docs/DISCOVERY_MODE.md), code D_COMMIT (PR #71's head). The run directory carries the
# suffix _discovery (issue #72: the results table does not label the arm until PR #73 lands).
# Usage: block_d_run.sh <seed 0|2|3>. Contains no key: DEEPSEEK_API_KEY must be in the environment of the process.
# Every check that can refuse comes before the run, so a refusal costs nothing.
D_COMMIT="23b3b12"  # 7 characters; PR #71's head on 2026-10-18; the plan's dated note names it before the chain
S="$1"
case "$S" in 0|2|3) ;; *) echo "usage: $0 0|2|3"; exit 1 ;; esac
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; D="$L/block_d"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"
WT="${D_WT:-$HOME/Documents/Mila/Gene-Mila/gene-mila-$D_COMMIT}"  # the dedicated checkout at D_COMMIT; never the main checkout
D_CAP_OVER="${D_CAP_OVER:-10}"  # Andres's amount over the ledger ("go discovery, cap $10", 2026-10-18 02:41 UTC)
n=adamson_cf_d1_ds_w4_r${S}_discovery; d="$MAIN/runs/$n"; LEDGER="$MAIN/runs/spend_ledger.sqlite"
DATA="$MAIN/data/adamson_cf_clean_tables"
WANT="gene_annotation.json gene_constraint.json gene_sets.json ppi_network.json prior_network.json protein_annotation.json targets.json transcription_factors.json"
PY="$MAIN/.venv/bin/python"
unset API_KEY  # as B2 and G: the lab reads DEEPSEEK_API_KEY only, so no second copy reaches it or its experiment processes
num() { case "$1" in ''|*[!0-9.]*|*.*.*) return 1 ;; esac; }
[ -n "$DEEPSEEK_API_KEY" ] || { echo "NOT STARTED: no key in the environment"; exit 1; }
case "$D_COMMIT" in *'<'*|'') echo "NOT STARTED: D_COMMIT is not filled in (plan, dated note before the chain)"; exit 1 ;; esac
# the block cap, written once before the chain (plan, Money) as "<cap> <ledger at the start> <UTC date>"
read -r CAP START CAPDATE 2> /dev/null < "$D/block_d_cap.txt"
num "$CAP" && num "$START" && [ "$(echo "$CAP <= $START + $D_CAP_OVER" | bc)" = 1 ] \
  || { echo "NOT STARTED: no valid block cap in $D/block_d_cap.txt (docs/PLAN_D_DISCOVERY_ADAMSON.md, Money)"; exit 1; }
[ "$(git -C "$WT" rev-parse --short=7 HEAD)" = "$D_COMMIT" ] || { echo "NOT STARTED: $WT is not at $D_COMMIT"; exit 1; }
[ -z "$(git -C "$WT" status --porcelain --untracked-files=no)" ] || { echo "NOT STARTED: $WT has changes"; exit 1; }
[ -e "$WT/genemila/discovery.py" ] || { echo "NOT STARTED: $WT has no genemila/discovery.py (the code must carry discovery mode, PR #71)"; exit 1; }
[ -e "$d" ] && { echo "NOT STARTED: $d exists"; exit 1; }
[ -e "$D/$n.log" ] && { echo "NOT STARTED: $D/$n.log exists; not overwriting"; exit 1; }
[ -e "$L/STOP" ] && { echo "NOT STARTED: STOP file present"; exit 3; }
[ -e "$D/block_d_stopped.txt" ] && { echo "NOT STARTED: block stopped"; exit 3; }
pgrep -f '[r]un_research.py' > /dev/null && { echo "NOT STARTED: a lab run is running"; exit 1; }
pgrep -f '[s]cale_seq.sh' > /dev/null && { echo "NOT STARTED: the scaling driver is running (pgrep -f scale_seq.sh)"; exit 1; }
pgrep -f '[f]eature_compare.py' > /dev/null && { echo "NOT STARTED: a feature_compare reading is running"; exit 1; }
pgrep -f '[l]edger_proxy.py|[b]lock_h_chain.sh' > /dev/null && { echo "NOT STARTED: block H's proxy or chain is running (one paid run at a time)"; exit 1; }
# the bundle: the same checks as block G's run script (verify_bundle, no added knowledge, the arm's file list, the
# split of data/adamson_cf, the knowledge summary within the planner's knowledge-section budget of the code in use)
[ -e "$DATA/manifest.json" ] || { echo "NOT STARTED: $DATA is not a bundle"; exit 1; }
PYTHONPATH="$WT" "$PY" - "$DATA" "$MAIN/data/adamson_cf" "$WANT" <<'PY' || { echo "NOT STARTED: $DATA is not the plan's bundle (above)"; exit 1; }
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
spent=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
num "$spent" && [ "$(echo "$spent >= $START" | bc)" = 1 ] && [ "$(echo "$spent + 2.50 <= $CAP" | bc)" = 1 ] \
  || { echo "NOT STARTED: ledger '$spent' unreadable, below the block's start $START, or plus the run's caps above the block cap $CAP"; exit 2; }
echo "ok: all checks; ledger \$$spent, block cap \$$CAP (ledger \$$START at $CAPDATE)"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (code $D_COMMIT in $WT, data $(basename "$DATA"), discovery mode, DeepSeek ledger \$$spent, block D cap \$$CAP from a start of \$$START at $CAPDATE)" >> "$L/progress.md"
cd "$WT" || exit 1
"$PY" run_research.py --minutes 20 --workers 4 --dataset adamson_cf --planner-provider deepseek --planner-model deepseek-v4-pro \
  --worker-provider deepseek --worker-model deepseek-flash --run-dir "$d" --set run.seed=$S \
  --set run.data_dir="$DATA" --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek="$CAP" \
  --set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5 --set schedule.discovery=true --no-watchdog > "$D/$n.log" 2>&1
rc=$?
unset DEEPSEEK_API_KEY
after=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
stop=""
# an unreadable ledger must stop the block, not pass the $2.00 check with a negative cost
if num "$after" && [ "$(echo "$after >= $spent" | bc)" = 1 ]; then cost=$(echo "$after - $spent" | bc)
else cost="?"; stop="$stop ledger unreadable or below its start after the run ('$after');"; fi
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$after (run \$$cost)" >> "$L/progress.md"
[ "$rc" = 0 ] || stop="$stop exit code $rc;"
[ "$cost" = "?" ] || [ "$(echo "$cost <= 2.00" | bc)" = 1 ] || stop="$stop cost \$$cost over \$2.00;"
"$PY" - "$d" "$D_COMMIT" <<'PY' > "$D/$n.check.txt" || stop="$stop $(grep PROBLEM "$D/$n.check.txt" | tr '\n' ';')"
import json, sys
from pathlib import Path
d, commit = Path(sys.argv[1]), sys.argv[2]
if not (d / "summary.json").exists():
    print("PROBLEM: no summary.json"); sys.exit(1)
s = json.loads((d / "summary.json").read_text()); c = json.loads((d / "config.json").read_text())
pl, b, u, disc = s.get("planner") or {}, s.get("best") or {}, s["llm_usage"], s.get("discovery") or {}
print(f"run: code {s['base_commit'][:10]}, {s['duration_s']} s, seed {c['run']['seed']}, workers {c['run']['workers']}, data {Path(c['run']['data_dir']).name}, external knowledge {c['run'].get('external_knowledge')}, planner {pl.get('configured')} mixed {pl.get('mixed')} exhausted_at_min {pl.get('exhausted_at_min')}, schedule.discovery {(c.get('schedule') or {}).get('discovery')}")
print(f"cost by the run: workers ${u['worker']['cost_usd']:.3f}, planner ${u['planner']['cost_usd']:.3f}")
print(f"selected {b.get('experiment_id')} ({b.get('model')}, {len(b.get('features') or [])} features) visible {b.get('score')}")
print(f"discovery: rounds {disc.get('rounds')} (counted {disc.get('rounds_counted')}), hypotheses {disc.get('hypotheses')}, naming an unread input {disc.get('hypotheses_naming_an_unread_input')}, dry at round {disc.get('dry_at_round')}, inputs proposed {disc.get('inputs_proposed')}")
print(f"discovery: features scored for derivability {disc.get('features_scored_for_derivability')}, new-input features {len(disc.get('new_input_features') or [])}, derived features {len(disc.get('derived_features') or [])} (threshold {disc.get('derived_r2_threshold')}), evidence files {disc.get('evidence_files')}")
store = d / "feature_store"
for t in ("gene_annotation", "gene_constraint", "protein_annotation", "gene_sets", "ppi_network", "prior_network", "transcription_factors", "control_std", "gene_corr", "control_cells"):
    uses = sorted(p.stem for p in store.glob("*.py") if t in p.read_text()) if store.exists() else []
    print(f"features reading {t}: {len(uses)} {uses[:20]}")
try:  # the largest planner state (planner_rounds.state_chars), on a private copy of lab.db and its -wal (write-ahead mode)
    import shutil, sqlite3, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for suf in ("", "-wal"):
            if (d / f"lab.db{suf}").exists(): shutil.copyfile(d / f"lab.db{suf}", f"{tmp}/lab.db{suf}")
        mx = sqlite3.connect(f"{tmp}/lab.db").execute("select coalesce(max(state_chars),0) from planner_rounds").fetchone()[0]
    print(f"largest planner state {mx} characters")
except Exception as exc:
    print(f"largest planner state: not read ({exc})")
bad = [m for m, h in [("planner.mixed not false", pl.get("mixed") is not False), (f"duration_note {s.get('duration_note')}", bool(s.get("duration_note"))),
                      (f"not code {commit}", not s["base_commit"].startswith(commit)),
                      ("knowledge list other than the bundle's own", bool(c["run"].get("external_knowledge"))),
                      ("schedule.discovery not true in config.json", (c.get("schedule") or {}).get("discovery") is not True),
                      ("no discovery record in summary.json", not disc.get("enabled"))] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
cat "$D/$n.check.txt"
if [ -n "$stop" ]; then
  echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n STOPPED the block:$stop" | tee -a "$L/progress.md" >> "$D/block_d_stopped.txt"
  echo "STOPPED:$stop"; exit 3
fi
touch "$D/$n.passed"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n passed" >> "$L/progress.md"
