#!/bin/bash
# One block G run (docs/PLAN_G_CLEAN_ARM.md): B2's settings on a clean tier-1 bundle, with (g1) or without (g0) the
# three new tables, DeepSeek planner + 4 workers, fresh start, code <G_COMMIT>.
# Usage: block_g_run.sh <norman|adamson_cf> <g0|g1> <seed 0|2|3>. Contains no key: DEEPSEEK_API_KEY must be in the
# environment of the process. Every check that can refuse comes before the run, so a refusal costs nothing.
G_COMMIT="<G_COMMIT>"  # 7 characters; filled in by the dated note of the plan that names the code, before the chain
DS="$1"; ARM="$2"; S="$3"
case "$DS" in norman|adamson_cf) ;; *) echo "usage: $0 norman|adamson_cf g0|g1 0|2|3"; exit 1 ;; esac
case "$ARM" in g0|g1) ;; *) echo "usage: $0 norman|adamson_cf g0|g1 0|2|3"; exit 1 ;; esac
case "$S" in 0|2|3) ;; *) echo "usage: $0 norman|adamson_cf g0|g1 0|2|3"; exit 1 ;; esac
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"
WT="${G_WT:-$HOME/Documents/Mila/Gene-Mila/gene-mila-$G_COMMIT}"  # the dedicated checkout at G_COMMIT (as block F's gene-mila-ce1b530); never the main checkout
n=${DS}_${ARM}_ds_w4_r$S; d="$MAIN/runs/$n"; LEDGER="$MAIN/runs/spend_ledger.sqlite"
case "$ARM" in g0) DATA="$MAIN/data/${DS}_clean"; WANT="gene_sets.json ppi_network.json prior_network.json targets.json transcription_factors.json" ;;
                g1) DATA="$MAIN/data/${DS}_clean_tables"; WANT="gene_annotation.json gene_constraint.json gene_sets.json ppi_network.json prior_network.json protein_annotation.json targets.json transcription_factors.json" ;; esac
PY="$MAIN/.venv/bin/python"
unset API_KEY  # as B2: the lab reads DEEPSEEK_API_KEY only, so no second copy reaches it or its experiment processes
num() { case "$1" in ''|*[!0-9.]*|*.*.*) return 1 ;; esac; }
[ -n "$DEEPSEEK_API_KEY" ] || { echo "NOT STARTED: no key in the environment"; exit 1; }
case "$G_COMMIT" in *'<'*|'') echo "NOT STARTED: G_COMMIT is not filled in (plan, dated note before the chain)"; exit 1 ;; esac
# the block cap, written once before the chain (plan, Money) as "<cap> <ledger at the start> <UTC date>"
read -r CAP START CAPDATE 2> /dev/null < "$L/block_g_cap.txt"
num "$CAP" && num "$START" && [ "$(echo "$CAP <= $START + 20" | bc)" = 1 ] \
  || { echo "NOT STARTED: no valid block cap in $L/block_g_cap.txt (docs/PLAN_G_CLEAN_ARM.md, Money)"; exit 1; }
[ "$(git -C "$WT" rev-parse --short=7 HEAD)" = "$G_COMMIT" ] || { echo "NOT STARTED: $WT is not at $G_COMMIT"; exit 1; }
[ -z "$(git -C "$WT" status --porcelain --untracked-files=no)" ] || { echo "NOT STARTED: $WT has changes"; exit 1; }
[ -e "$d" ] && { echo "NOT STARTED: $d exists"; exit 1; }
[ -e "$L/$n.log" ] && { echo "NOT STARTED: $L/$n.log exists; not overwriting"; exit 1; }
[ -e "$L/STOP" ] && { echo "NOT STARTED: STOP file present"; exit 3; }
[ -e "$L/block_g_stopped.txt" ] && { echo "NOT STARTED: block stopped"; exit 3; }
pgrep -f '[r]un_research.py' > /dev/null && { echo "NOT STARTED: a lab run is running"; exit 1; }
pgrep -f '[s]cale_seq.sh' > /dev/null && { echo "NOT STARTED: the scaling driver is running (pgrep -f scale_seq.sh)"; exit 1; }
pgrep -f '[f]eature_compare.py' > /dev/null && { echo "NOT STARTED: a feature_compare reading is running (block F's readings must have finished)"; exit 1; }
# the bundle: its manifest's hashes cover every knowledge file written at build time, so verify_bundle proves the
# files are byte for byte the builder's; added_knowledge (what the run records as run.external_knowledge, computed by
# the code that records it) must be empty, or a stray file in knowledge/ would make the run its own arm; the file list
# is the arm's; the split is the existing bundle's, so the arms compare with B2 and with each other. The knowledge
# summary (one line per file, genemila.lab.Lab.knowledge_summary) must fit the knowledge section's budget of the code
# at $WT (genemila.research_state: KNOWLEDGE_SECTION_CHARS after the planner-state change, SECTION_CHARS = 2,500
# before it, which the eight-file bundle exceeds), or the planner would not see every file: a g1 run on a head
# without the change is refused here.
[ -e "$DATA/manifest.json" ] || { echo "NOT STARTED: $DATA is not a bundle (run prepare_clean_bundles.sh)"; exit 1; }
PYTHONPATH="$WT" "$PY" - "$DATA" "$MAIN/data/$DS" "$WANT" <<'PY' || { echo "NOT STARTED: $DATA is not the plan's bundle (above)"; exit 1; }
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
# The whole planner state is still cut at 20,000 characters (research_state.TOTAL_CHARS); no arm on this code has
# state sizes to match, so the check after the run records each run's largest state instead (reading 4).
spent=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
num "$spent" && [ "$(echo "$spent >= $START" | bc)" = 1 ] && [ "$(echo "$spent + 2.50 <= $CAP" | bc)" = 1 ] \
  || { echo "NOT STARTED: ledger '$spent' unreadable, below the block's start $START, or plus the run's caps above the block cap $CAP"; exit 2; }
echo "ok: all checks; ledger \$$spent, block cap \$$CAP (ledger \$$START at $CAPDATE)"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (code $G_COMMIT in $WT, data $(basename "$DATA"), DeepSeek ledger \$$spent, block G cap \$$CAP from a start of \$$START at $CAPDATE)" >> "$L/progress.md"
cd "$WT" || exit 1
"$PY" run_research.py --minutes 20 --workers 4 --dataset "$DS" --planner-provider deepseek --planner-model deepseek-v4-pro \
  --worker-provider deepseek --worker-model deepseek-flash --run-dir "$d" --set run.seed=$S \
  --set run.data_dir="$DATA" --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek="$CAP" \
  --set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5 --no-watchdog > "$L/$n.log" 2>&1
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
"$PY" - "$d" "$G_COMMIT" <<'PY' > "$L/$n.check.txt" || stop="$stop $(grep PROBLEM "$L/$n.check.txt" | tr '\n' ';')"
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
store = d / "feature_store"
for t in ("gene_annotation", "gene_constraint", "protein_annotation"):
    uses = sorted(p.stem for p in store.glob("*.py") if t in p.read_text()) if store.exists() else []
    print(f"features reading {t}: {len(uses)} {uses[:20]}")
try:  # the largest planner state (planner_rounds.state_chars), on a private copy of lab.db and its -wal (write-ahead mode)
    import shutil, sqlite3, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for suf in ("", "-wal"):
            if (d / f"lab.db{suf}").exists(): shutil.copyfile(d / f"lab.db{suf}", f"{tmp}/lab.db{suf}")
        mx = sqlite3.connect(f"{tmp}/lab.db").execute("select coalesce(max(state_chars),0) from planner_rounds").fetchone()[0]
    print(f"largest planner state {mx} characters (TOTAL_CHARS cut 20000 {'reached' if mx >= 20000 else 'not reached'})")
except Exception as exc:
    print(f"largest planner state: not read ({exc})")
bad = [m for m, h in [("planner.mixed not false", pl.get("mixed") is not False), (f"duration_note {s.get('duration_note')}", bool(s.get("duration_note"))),
                      (f"not code {commit}", not s["base_commit"].startswith(commit)),
                      ("knowledge list other than the bundle's own", bool(c["run"].get("external_knowledge")))] if h]
for m in bad: print("PROBLEM:", m)
sys.exit(1 if bad else 0)
PY
cat "$L/$n.check.txt"
if [ -n "$stop" ]; then echo "$(date -u +%Y-%m-%dT%H:%MZ) $n:$stop" >> "$L/block_g_stopped.txt"; echo "STOPPED:$stop"; exit 3; fi
touch "$L/$n.passed"; echo "RUN_DONE $n rc=0"
