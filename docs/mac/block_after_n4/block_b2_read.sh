#!/bin/bash
# B2's readings (docs/PLAN_AFTER_N4.md: B2, "The combined model of an arm", "The arm reading", its amendment of
# 20:30 UTC, the note of 22:50 UTC and its addendum of 23:10 UTC), once the control and the arm's three paid runs have
# passed their checks. The arm is seeds 0, 2 and 3: seed 1 (runs/norman_ds_addstart_w4_r1) was killed by the watchdog
# while finishing and is its own arm, so it is in no arm reading and no combined model; its own per-run reading is
# made last, written as norman_b2_r1_killed_sealed_reading, and reported in a row of its own. The arm as first
# specified (seeds 0 and 2) is read against the start too, reported and not read (addendum of 23:10 UTC). Free: no LLM, no key, no lab run. Start it as  bash block_b2_read.sh
# from anywhere: it works in the main checkout with the tools at the commit block_b2_control.sh recorded, writes
# docs/results/norman_b2_<what>.md and the JSON twin each tool writes beside it, never over an existing file, and
# prints every file's md5. The only sealed reads are the tools' paired queries on oracles of their own, which each
# report counts. No reading chooses a model: each compares a run's selected model (summary.json "best", chosen on
# visible data), its additive baseline or its start, and the delivered Norman model is chosen at the end from the
# visible validation perturbations only, by the rule the plan fixed. The pinned commit predates this script: bring it
# in without moving the checkout (HANDOFF.md section 1), as
#   git -C "$M" fetch origin claude/autonomous-research-system-3k435s && git -C "$M" show \
#     FETCH_HEAD:docs/mac/block_after_n4/block_b2_read.sh > "$L/b2_resume/block_b2_read.sh"
set +x
M="$HOME/Documents/Mila/Gene-Mila/gene-mila"; L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
PY="$M/.venv/bin/python"; LEDGER="$M/runs/spend_ledger.sqlite"
COMMIT_FILE="$L/block_after_n4_b2b3_commit.txt"; STOPPED="$L/block_after_n4_stopped.txt"; LOG="$L/norman_b2_read.log"
P=docs/results/norman_b2
CTL=runs/norman_control_addstart_w4_r0
ARM="0 2 3"   # the arm's seeds (note of 22:50 UTC: seed 3 in seed 1's place)
OWN=1         # seed 1, its own arm: read alone, beside the arm, never in it
RUNS=""; for s in $ARM; do RUNS="$RUNS runs/norman_ds_addstart_w4_r$s"; done
R1=runs/norman_ds_addstart_w4_r$OWN
B1="runs/norman_ds_from_n2_w4_r1 runs/norman_ds_from_n2_w4_r2 runs/norman_ds_from_n2_w4_r3"
# B1's combined model as B1 read it (tools d0fb635, draft PR #6; md5 from docs/mac/MD5SUMS_b1.txt): the visible
# validation score B2's combined model has to beat. B1_COMBINED=<path> in front points at another copy of that file.
B1J="${B1_COMBINED:-$M/docs/results/norman_b1_combined_vs_n2.json}"; B1J_MD5=9d6bfc3e0c9f2887f01989ce50542625
NAMES="control_sealed_reading"
for s in $ARM; do NAMES="$NAMES r${s}_sealed_reading"; done
NAMES="$NAMES r${OWN}_killed_sealed_reading arm_r0_r2_vs_start_reported"
for s in $ARM; do NAMES="$NAMES r${s}_versus_control"; done
NAMES="$NAMES arm_vs_start arm_vs_additive arm_vs_control combined_vs_start combined_vs_control combined_vs_additive"
NAMES="$NAMES combined_vs_b1_combined"
unset DEEPSEEK_API_KEY API_KEY  # free: with no key in its environment nothing here can spend
no() { echo "NOT DONE: $*"; exit 2; }
ok() { echo "ok: $*"; }
cd "$M" || no "no checkout at $M"
[ -e "$STOPPED" ] && no "the block is stopped ($STOPPED); the readings wait until the cause is written up"
pgrep -f run_research.py > /dev/null && no "a lab run is running (pgrep -f run_research.py); read once it has ended"
pgrep -f scale_seq.sh > /dev/null && no "the scaling driver is running (pgrep -f scale_seq.sh)"
ok "block not stopped, no lab run or driver running"
# the code: the recorded B2/B3 commit, nothing tracked changed, nothing untracked among the code the tools import
[ -e "$COMMIT_FILE" ] || no "no recorded B2/B3 commit ($COMMIT_FILE)"
want=$(cat "$COMMIT_FILE"); head=$(git rev-parse HEAD)
[ "$head" = "$want" ] || no "HEAD $head is not the recorded B2/B3 commit $want"
[ -z "$(git status --porcelain --untracked-files=no)$(git status --porcelain -- genemila configs tools)" ] \
  || no "tracked files changed, or untracked files under genemila/, configs/ or tools/, in $M"
ok "tools at the recorded commit $head, clean"
# the reports: none exists yet, so the set comes from one commit in one pass
for n in $NAMES; do for x in md json; do [ -e "${P}_$n.$x" ] && no "${P}_$n.$x exists; not overwriting"; done; done
ok "none of the $(echo $NAMES | wc -w | tr -d ' ') reports (${P}_*.md and .json) exists"
[ -e "$B1J" ] || no "B1's combined reading $B1J is missing: git -C $M show origin/claude/mac-b1-2026-10-11:docs/\
results/norman_b1_combined_vs_n2.json > $L/norman_b1_combined_vs_n2.json, then B1_COMBINED=$L/norman_b1_combined_vs_n2.json"
[ "$(md5 -q "$B1J")" = "$B1J_MD5" ] || no "$B1J has md5 $(md5 -q "$B1J"), not B1's $B1J_MD5"
ok "B1's combined reading $B1J, md5 $B1J_MD5"
# each arm step passed its checks on the pinned commit (the marker block_b2_control.sh and block_b2_run.sh write last);
# seed 1 stopped the block and has none
for d in $CTL $RUNS; do
  m="$L/$(basename "$d").passed"
  [ -e "$m" ] || no "no pass marker $m: $d has not finished and passed its checks"
  [ "$(awk '{print $2}' "$m")" = "$want" ] || no "$m records $(cat "$m"), not the pinned commit $want"
done
ok "the control and seeds $ARM passed their checks on $want (their .passed markers)"
# the runs: the control and the arm's runs ended and wrote their summaries on the recorded commit, planner unchanged
# (a run whose planner changed is its own arm, and combine refuses it), at most $2.00 by their own count; B1's three on
# 076282c likewise; seed 1, its own arm, on the recorded commit with a summary (its fallback one); all on one split
"$PY" - "$want" $CTL $RUNS -- $B1 -- $R1 <<'EOF' || no "a run is not ready to be read (above)"
import json, sys
from pathlib import Path
want, rest = sys.argv[1], sys.argv[2:]
i = rest.index("--"); j = rest.index("--", i + 1)
b2, b1, own = rest[:i], rest[i + 1:j], rest[j + 1:]
bad, splits = [], set()
for d in b2 + b1 + own:
    if not (Path(d) / "summary.json").exists():
        if d in own:   # its own arm, read only if it can be: no summary is noted, and stops nothing
            print(f"NOTE: {d} has no summary.json; its own reading may still be made"); continue
        bad.append(f"{d} has no summary.json"); continue
    s = json.loads((Path(d) / "summary.json").read_text())
    pl, cost, code = s.get("planner") or {}, s["llm_usage"]["all"]["cost_usd"], "076282c" if d in b1 else want
    splits.add((s["dataset"], s["split_id"]))
    print(f"{d}: code {s['base_commit'][:7]}, {s['dataset']} {s['split_id']}, planner {pl.get('configured')} mixed "
          f"{pl.get('mixed')}, ${cost:.3f}, selected {s['best']['experiment_id']} (visible {s['best']['score']:.4f})"
          + (f"; its own arm, not in B2's (duration_note: {s.get('duration_note')})" if d in own else ""))
    checks = [(f"code {s['base_commit']}, not {code}", not s["base_commit"].startswith(code))]
    if d not in own:
        checks += [
            ("planner.mixed is not false (changed, ran out, or no record): its own arm", pl.get("mixed") is not False),
            (f"cut before it wrote its summary ({s.get('duration_note')})", bool(s.get("duration_note"))),
            (f"cost ${cost:.3f} by its own count, over $2.00", cost > 2.0)]
    bad += [f"{d}: {m}" for m, hit in checks if hit]
if len(splits) != 1:
    bad.append(f"the runs are not on one dataset and split: {sorted(splits)}")
for m in bad:
    print("PROBLEM:", m)
sys.exit(1 if bad else 0)
EOF
ok "the control, seeds $ARM and B1's three repeats ended cleanly on one split; seed $OWN checked as its own arm"
spent=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
[ -n "$spent" ] || no "cannot read the ledger $LEDGER"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) B2 readings started (tools $(git rev-parse --short HEAD), free," \
  "DeepSeek ledger \$$spent)" >> "$L/progress.md"
echo "== $(date -u +%Y-%m-%dT%H:%MZ) B2 readings, tools $want" >> "$LOG"
no() { echo "- $(date -u +%Y-%m-%dT%H:%MZ) B2 readings stopped: $*" >> "$L/progress.md"; echo "NOT DONE: $*"; exit 2; }
run_tool() {  # run_tool WHAT TOOL ARGS...: one report and its JSON twin; the tool's console output goes to $LOG
  local out="${P}_$1.md"; shift
  echo "== $out: $*" >> "$LOG"
  "$PY" "$@" --out "$out" >> "$LOG" 2>&1
}
step() {  # step WHAT TOOL ARGS...: as run_tool, and a failure stops the readings
  run_tool "$@" || { tail -5 "$LOG"; no "${P}_$1.md failed (all output in $LOG); move the reports written so far aside, never delete them"; }
  ok "${P}_$1.md and its JSON twin"
}
# per run: the selected model against its start (baseline_ridge_additive on this code) and the additive baseline
step control_sealed_reading tools/sealed_reading.py --runs $CTL
for s in $ARM; do step r${s}_sealed_reading tools/sealed_reading.py --runs runs/norman_ds_addstart_w4_r$s; done
# the start each run's reading resolved, before anything is read against it (combine resolves RUN:start the same way,
# through sealed_reading's _fresh_start): the fresh start baseline_ridge_additive in every run
starts=""; for s in $ARM; do starts="$starts ${P}_r${s}_sealed_reading.json"; done
"$PY" - ${P}_control_sealed_reading.json $starts <<'EOF' || no "a run's start is not baseline_ridge_additive (above)"
import json, sys
bad = 0
for f in sys.argv[1:]:
    r = json.load(open(f))["runs"][0]
    c = r["continuation"]
    st = c.get("start") or {}
    print(f"{r['run']}: start {c.get('kind')} {st.get('experiment_id')} ({st.get('hypothesis_group')}, alpha "
          f"{st.get('alpha')}, visible {st.get('visible_score')})")
    bad += c.get("kind") != "fresh" or st.get("hypothesis_group") != "baseline_ridge_additive"
sys.exit(1 if bad else 0)
EOF
ok "every run's start is its own fresh baseline_ridge_additive"
# what the agents actually started from: each run's best modelled baseline on visible data (the planner's default
# parent). The plan's reference is baseline_ridge_additive whatever this shows; another one here is printed and noted.
for d in $CTL $RUNS; do
  b=$(sqlite3 "$d/lab.db" "select experiment_id || ' ' || hypothesis_group || ' visible ' || round(primary_score, 4) from experiments where kind='baseline' and status='completed' and model_type!='none' and primary_score is not null order by primary_score desc limit 1")
  echo "$d: best modelled baseline $b"
  case "$b" in *" baseline_ridge_additive "*) ;; *) echo "NOTE: $d's agents started from another baseline than baseline_ridge_additive; say so beside its reading" ;; esac
done
# per arm run: its selected model against the control's (the report repeats both runs' own readings)
for s in $ARM; do
  step r${s}_versus_control tools/sealed_reading.py --versus --runs runs/norman_ds_addstart_w4_r$s $CTL
done
# the arm over seeds 0, 2 and 3: PRIMARY against each run's start, then against the additive baseline and the control
step arm_vs_start tools/arm_reading.py rule --against start --readings $starts
step arm_vs_additive tools/arm_reading.py rule --against additive --readings $starts
vs=""; for s in $ARM; do vs="$vs ${P}_r${s}_versus_control.json"; done
step arm_vs_control tools/arm_reading.py rule --against versus --readings $vs
# the arm as first specified (seeds 0 and 2; addendum of 23:10 UTC): reported beside the primary reading, not read
step arm_r0_r2_vs_start_reported tools/arm_reading.py rule --against start --readings ${P}_r0_sealed_reading.json \
  ${P}_r2_sealed_reading.json
# the combined model of seeds 0, 2 and 3 against baseline_ridge_additive (r0's start), the control's selected model,
# the additive baseline and B1's combined model
r0=$(echo $RUNS | awk '{print $1}')
step combined_vs_start tools/arm_reading.py combine --members $RUNS --reference ${r0}:start
step combined_vs_control tools/arm_reading.py combine --members $RUNS --reference $CTL
step combined_vs_additive tools/arm_reading.py combine --members $RUNS --reference ${r0}:additive
step combined_vs_b1_combined tools/arm_reading.py combine --members $RUNS --reference $B1
# last, seed 1 alone (note of 22:50 UTC: its sealed reading, "made like the others' after B2 has ended, is reported in
# a row of its own, labelled as a run killed while finishing, and decides nothing"); a failure here is reported and
# stops nothing.
if run_tool r${OWN}_killed_sealed_reading tools/sealed_reading.py --runs $R1; then
  ok "${P}_r${OWN}_killed_sealed_reading.md and its JSON twin (its own arm)"
else
  tail -5 "$LOG"; echo "NOTE: ${P}_r${OWN}_killed_sealed_reading failed (output in $LOG): seed $OWN is reported as not read"
fi
# what the reports hold, checked: the tools' commit, the models compared, the reproduction of each stored sealed
# score, the sealed scorings made, the readings, and the delivered-model choice
"$PY" - "$want" "$B1J" "$ARM" "$OWN" <<'EOF' 2>&1 | tee -a "$LOG"
import json, sys
from pathlib import Path
want, b1_path, P = sys.argv[1], sys.argv[2], "docs/results/norman_b2_"
arm, own = sys.argv[3].split(), sys.argv[4]
ctl, runs = "norman_control_addstart_w4_r0", [f"norman_ds_addstart_w4_r{s}" for s in arm]
r1, r1n = f"norman_ds_addstart_w4_r{own}", f"r{own}_killed_sealed_reading"
b1 = [f"norman_ds_from_n2_w4_r{s}" for s in (1, 2, 3)]
best = {n: json.loads(Path(f"runs/{n}/summary.json").read_text())["best"]["experiment_id"]
        for n in [ctl] + runs + b1 + [r1] if Path(f"runs/{n}/summary.json").exists()}
singles = ["control_sealed_reading"] + [f"r{s}_sealed_reading" for s in arm]
versus = [f"r{s}_versus_control" for s in arm]
arms = [("arm_vs_start", "PRIMARY, the arm against each run's start (baseline_ridge_additive)"),
        ("arm_vs_additive", "secondary, the arm against the additive baseline"),
        ("arm_vs_control", "secondary, the arm against the control's selected model")]
combos = ["start", "control", "additive", "b1_combined"]
J = lambda n: json.loads(Path(P + n + ".json").read_text())
r1_read = Path(P + r1n + ".json").exists() and Path(P + r1n + ".md").exists()
bad = []
def problem(m):
    bad.append(m); print("PROBLEM:", m)
def flag(n, m):   # seed 1's reading decides nothing (note of 22:50 UTC): what it shows is noted, and holds nothing up
    print("NOTE (seed " + own + ", its own arm):", m) if n == r1n else problem(m)
def d(p):
    if "verdict" not in p:
        return "too few to report"
    v = {"a": "A better", "b": "B better", "none": "no difference established"}[p["verdict"]]
    return f"{p['mean_diff']:+.4f} ± {p['se']:.4f}, A better on {p['wins_a']} and worse on {p['wins_b']} of {p['n']}: {v}"
def ratio(cr):
    return "none" if not cr or cr.get("ratio") is None else f"{cr['ratio']:.2f}"
print("Sealed scorings (each on an oracle of the tool's own, outside the runs' caps):")
total = 0
for n in singles + versus + [a for a, _ in arms] + ["arm_r0_r2_vs_start_reported"] + [f"combined_vs_{x}" for x in combos] + ([r1n] if r1_read else []):
    j = J(n)
    pr = j["protocol"]
    total += pr["sealed_scorings"]
    first = pr.get("first_sealed_scorings") or []
    print(f"  {P}{n}.md: {pr['sealed_scorings']}" + (f" (first ever for {', '.join(first)})" if first else ""))
    if j.get("code_commit") != want:
        flag(n, f"{n}: tool code {j.get('code_commit')}, not the recorded {want}")
print(f"  in all {total}; the arm readings read the JSON twins only and scored nothing.")
print(f"The arm over seeds {', '.join(arm)} (docs/PLAN_AFTER_N4.md, \"The arm reading\"; seed {own} is its own arm):")
for n, what in arms:
    j = J(n)
    p = j["pooled"]
    for e in j["excluded"]:
        problem(f"{n}: {e['run']} left out ({e['why']})")
    if sorted(x["run"] for x in j["runs"]) != sorted(runs) or j["protocol"]["sealed_scorings"] != 0:
        problem(f"{n}: runs {[x['run'] for x in j['runs']]}, sealed scorings {j['protocol']['sealed_scorings']}")
    v = {"a": "the arm better", "b": "the arm worse", "none": "no difference established"}[p["verdict"]]
    print(f"  {what}: R {p['R']}, G {p['G']:+.4f}, SE {p['SE']:.4f} (S {p['S']:.4f}, sd_g {p['sd_g']:.4f}), k "
          f"{p['k']:.2f}, wins {p['wins_selected']}/{p['wins_reference']} of {p['pairs']} pairs: {v}  [{P}{n}.md]")
j = J("arm_r0_r2_vs_start_reported")
p = j["pooled"]
if sorted(x["run"] for x in j["runs"]) != sorted(runs[:2]) or j["protocol"]["sealed_scorings"] != 0 or j["excluded"]:
    problem(f"arm_r0_r2_vs_start_reported: runs {[x['run'] for x in j['runs']]}, excluded {j['excluded']}")
print(f"  reported, not read: the arm as first specified, seeds 0 and 2, against each run's start: R {p['R']}, "
      f"G {p['G']:+.4f}, SE {p['SE']:.4f}, k {p['k']:.2f}  [{P}arm_r0_r2_vs_start_reported.md]")
print("Everything below is secondary and descriptive.")
print("Per run, sealed pooled pearson_delta, A minus B with its paired SE, by the per-run rule (A the run's selected "
      "model, B its start or its additive baseline; the arm reading inflates the SE by the clustering ratio above 1):")
for n in singles + versus + ([r1n] if r1_read else []):
    j = J(n)
    for r in j["runs"]:
        c = r["continuation"]
        st = c.get("start") or {}
        sealed = [("additive", r.get("sealed")), ("start", c.get("sealed"))] + (
            [("pair", j["pair"]["sealed"])] if j.get("pair") else [])
        for what, s in sealed:
            for side in ("a", "b"):
                if s and s[side].get("matches_stored") is False:
                    flag(n, f"{n}: {r['run']}, {what} comparison: {s[side]['experiment_id']}'s sealed score differs "
                            "from what its run stored; read nothing until that is explained")
        if n in versus:
            continue
        if r["selected"]["experiment_id"] != best.get(r["run"], r["selected"]["experiment_id"]):
            flag(n, f"{n}: selected {r['selected']['experiment_id']}, summary.json best {best[r['run']]}")
        if (r.get("additive") or {}).get("hypothesis_group") != "baseline_additive":
            flag(n, f"{n}: the additive baseline is {r.get('additive')}")
        if c.get("kind") != "fresh" or st.get("hypothesis_group") != "baseline_ridge_additive":
            flag(n, f"{n}: the start is {c.get('kind')} {st.get('experiment_id')} ({st.get('hypothesis_group')})")
        tag = (" [its own arm, killed by the watchdog while finishing (note of 22:50 UTC); in no arm reading]"
               if n == r1n else "")
        print(f"  {r['run']}{tag}: selected {r['selected']['experiment_id']}; start {st.get('experiment_id')} alpha "
              f"{st.get('alpha')} visible {st.get('visible_score')}; against its start "
              f"{d(c['sealed']['paired']) if c.get('sealed') else c.get('note')} (ratio {ratio(c.get('cluster_ratio'))}); "
              f"against the additive baseline {d(r['sealed']['paired']) if r.get('sealed') else r.get('note')} "
              f"(ratio {ratio(r.get('cluster_ratio'))})")
if not r1_read:
    print(f"  {r1} [its own arm]: not read (its reading failed or is incomplete; see the log)")
for n in versus:
    p = J(n)["pair"]
    if (p["a"]["run"], p["b"]["run"]) not in [(x, ctl) for x in runs] \
            or (p["a"]["experiment_id"], p["b"]["experiment_id"]) != (best[p["a"]["run"]], best[ctl]):
        problem(f"{n}: compares {p['a']['run']}:{p['a']['experiment_id']} with {p['b']['run']}:{p['b']['experiment_id']}")
    print(f"  {p['a']['run']} (A) against the control (B): {d(p['sealed']['paired'])}")
print("The combined model of the arm's runs (A) against each reference (B), read by the per-run rule:")
expect = {"start": [(runs[0], "start", "baseline_ridge_additive")], "control": [(ctl, "selected", best[ctl])],
          "additive": [(runs[0], "additive", "baseline_additive")], "b1_combined": [(x, "selected", best[x]) for x in b1]}
vv = {}
for x in combos:
    j = J(f"combined_vs_{x}")
    a, b = j["a"]["models"], j["b"]["models"]
    if [(m["run"], m["role"], m["experiment_id"], m["base_commit"]) for m in a] != \
            [(r, "selected", best[r], want) for r in runs]:
        problem(f"combined_vs_{x}: the members are {[(m['run'], m['role'], m['experiment_id']) for m in a]}")
    if [(m["run"], m["role"], m["experiment_id"] if m["role"] == "selected" else m["hypothesis_group"]) for m in b] \
            != expect[x] or (x == "b1_combined" and any(not m["base_commit"].startswith("076282c") for m in b)):
        problem(f"combined_vs_{x}: the reference is "
                f"{[(m['run'], m['role'], m['experiment_id'], m['hypothesis_group']) for m in b]}")
    vv[x] = j["visible_validation"]
    print(f"  against {j['b']['label']}: sealed {d(j['sealed']['paired'])}; visible validation (n {vv[x]['n']}, "
          f"reported, not read) A {vv[x]['a']:.4f}, B {vv[x]['b']:.4f}")
# the delivered Norman model: B1's combined model unless B2's scores higher on pooled pearson_delta over the visible
# validation perturbations. Both are scored in combined_vs_b1_combined on the same perturbations by the same code; B1's
# score there must reproduce B1's own reading (tools d0fb635, runs on 076282c), so the two readings are comparable.
b1r, jx = json.loads(Path(b1_path).read_text()), J("combined_vs_b1_combined")
v1, vx = b1r["visible_validation"], vv["b1_combined"]
for what, x, y in [("dataset and split", (b1r["dataset"], b1r["split_id"]), (jx["dataset"], jx["split_id"])),
                   ("B1's members", [(m["run"], m["experiment_id"]) for m in b1r["a"]["models"]],
                    [(m["run"], m["experiment_id"]) for m in jx["b"]["models"]]),
                   ("metric and visible validation perturbations (n)", (v1["metric"], v1["n"]), (vx["metric"], vx["n"]))]:
    if x != y:
        problem(f"not comparable with B1's reading, {what}: {x} there, {y} here")
if abs(vx["b"] - v1["a"]) > 1e-9:
    problem(f"not comparable with B1's reading: B1's combined model scores {vx['b']!r} on the visible validation "
            f"perturbations here and {v1['a']!r} in B1's reading (tools {b1r['code_commit'][:7]})")
if max(v["a"] for v in vv.values()) - min(v["a"] for v in vv.values()) > 1e-12:
    problem(f"B2's combined model scores differently on the visible validation perturbations across its readings: "
            f"{[v['a'] for v in vv.values()]}")
print("No reading chose a model: every model compared is a run's summary.json best, its additive baseline or its "
      "start, as checked above; the delivered model below is chosen on the visible validation perturbations only.")
if bad:
    print(f"{len(bad)} PROBLEM(S) above: the delivered-model choice waits until they are explained.")
    sys.exit(1)
print(f"Delivered Norman model (docs/PLAN_AFTER_N4.md, fixed before B2): "
      f"{'B2' if vx['a'] > vx['b'] else 'B1'}'s combined model. Pooled pearson_delta over the {vx['n']} visible "
      f"validation perturbations: B2's combined {vx['a']:.4f}, B1's combined {vx['b']:.4f} (B1's own reading "
      f"{v1['a']:.4f}); B2's is chosen only if it scores higher.")
EOF
rc=${PIPESTATUS[0]}
echo "md5 of every report:"
for n in $NAMES; do for x in md json; do
  f="${P}_$n.$x"; if [ -e "$f" ]; then echo "$(md5 -q "$f")  $f"; else echo "(not written)  $f"; fi
done; done | tee -a "$LOG"
after=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
[ "$after" = "$spent" ] || { echo "PROBLEM: the DeepSeek ledger moved from \$$spent to \$$after"; rc=1; }
echo "- $(date -u +%Y-%m-%dT%H:%MZ) B2 readings finished rc=$rc (${P}_*.md, md5s in $LOG)" \
  "DeepSeek ledger \$$after" >> "$L/progress.md"
[ "$rc" = 0 ] || { echo "READ_DONE rc=$rc: problems above; nothing is read until they are explained"; exit 3; }
echo "READ_DONE rc=0"
