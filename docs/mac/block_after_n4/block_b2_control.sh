#!/bin/bash
# B2's free no-LLM control (docs/PLAN_AFTER_N4.md, B2): runs/norman_control_addstart_w4_r0, scripted planner, mock
# workers, 4 workers, 20 minutes, Norman with its Replogle file, seed 0: N2's command (docs/NORMAN_PLAN.md section 6,
# steps 4 and 7) on the lab head, where a bundle with pairs starts from baseline_ridge_additive. It records the one
# commit every B2 and B3 run uses. Free: no LLM is called and no key reaches it. Start it as  bash block_b2_control.sh
# (B1_WRITTEN_UP=1 in front only once a B1 run that tripped the stop rule is written up in the repository).
M="$HOME/Documents/Mila/Gene-Mila/gene-mila"; L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
PY="$M/.venv/bin/python"; LEDGER="$M/runs/spend_ledger.sqlite"
COMMIT_FILE="$L/block_after_n4_b2b3_commit.txt"; STOPPED="$L/block_after_n4_stopped.txt"
n=norman_control_addstart_w4_r0; d="$M/runs/$n"
unset DEEPSEEK_API_KEY API_KEY  # a free run: with no key in its environment it can never spend
no() { echo "NOT STARTED: $*"; exit 2; }
ok() { echo "ok: $*"; }
cd "$M" || no "no checkout at $M"
[ -e "$STOPPED" ] && no "the block is stopped ($STOPPED); write up the cause first"
[ -e "$d" ] && no "$d exists; not overwriting"
pgrep -f run_research.py > /dev/null && no "a lab run is running (pgrep -f run_research.py)"
[ -e "$L/STOP" ] && no "the STOP file $L/STOP is present (it holds every lab run); remove it for this run only"
pgrep -f scale_seq.sh > /dev/null && no "the scaling driver is running (pgrep -f scale_seq.sh)"
ok "block not stopped, no STOP file, $n does not exist, no lab run or driver running"
# B1 comes first (plan: one run at a time, in order): its three repeats ended, none tripped the stop rule
"$PY" - "$M/runs" "$B1_WRITTEN_UP" <<'EOF' || no "B1 has not ended cleanly (above)"
import json, sys
from pathlib import Path
bad = 0
for s in (1, 2, 3):
    p = Path(sys.argv[1]) / f"norman_ds_from_n2_w4_r{s}" / "summary.json"
    if not p.exists():
        print(f"B1 r{s}: no summary.json"); bad += 1; continue
    j = json.loads(p.read_text()); mixed = (j.get("planner") or {}).get("mixed"); cost = j["llm_usage"]["all"]["cost_usd"]
    trip = mixed is not False or cost > 2.0 or bool(j.get("duration_note"))
    print(f"B1 r{s}: planner.mixed {mixed}, cost ${cost:.3f}, duration_note {j.get('duration_note')}"
          + (" <- stop rule" if trip else ""))
    bad += trip and sys.argv[2] != "1"
sys.exit(1 if bad else 0)
EOF
# the code: committed, nothing tracked changed (the controller runs the working tree), with the plan's amendment
head=$(git rev-parse HEAD)
echo "code: $(git rev-parse --abbrev-ref HEAD) at $head; origin's lab branch as last fetched: $(git rev-parse origin/claude/autonomous-research-system-3k435s)"
[ -z "$(git status --porcelain --untracked-files=no)$(git status --porcelain -- genemila configs)" ] \
  || no "tracked files changed, or untracked files under genemila/ or configs/, in $M"
git merge-base --is-ancestor d0fb635 HEAD || no "HEAD does not contain d0fb635 (the plan's amendment and its tools)"
if [ ! -e "$COMMIT_FILE" ]; then   # the first B2 start: the commit is the lab branch head now (plan, B2)
  git fetch -q origin claude/autonomous-research-system-3k435s || no "cannot fetch the lab branch"
  tip=$(git rev-parse origin/claude/autonomous-research-system-3k435s)
  [ "$head" = "$tip" ] || no "HEAD $head is not the lab branch head $tip; git pull --ff-only first"
fi
if [ -e "$COMMIT_FILE" ] && [ "$(cat "$COMMIT_FILE")" != "$head" ]; then
  no "$COMMIT_FILE records $(cat "$COMMIT_FILE"), not HEAD $head"
fi
ok "clean tree, contains d0fb635, the lab branch head when B2 started"
# the knowledge: N2 to N4's Replogle file and nothing else added (run_research.py records it as run.external_knowledge)
k=$("$PY" -c 'import sys; from genemila.data.bundle import added_knowledge; print(" ".join(added_knowledge(sys.argv[1])))' "$M/data/norman")
[ "$k" = replogle2022_k562 ] || no "knowledge added to data/norman is '$k', not replogle2022_k562"
km=$(md5 -q "$M/data/norman/knowledge/replogle2022_k562.json")
[ "$km" = d9eff528143dcd4d72c87393df724084 ] || no "replogle2022_k562.json has md5 $km, not N2 to N4's d9eff528..."
ok "external knowledge replogle2022_k562 only, md5 $km"
spent=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
[ -n "$spent" ] || no "cannot read the ledger $LEDGER"
ok "DeepSeek ledger \$$spent (a free run leaves it as it is)"
[ -e "$COMMIT_FILE" ] || echo "$head" > "$COMMIT_FILE"
ok "B2 and B3 run on $head (recorded in $COMMIT_FILE)"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (code $(git rev-parse --short HEAD), free, DeepSeek ledger \$$spent)" >> "$L/progress.md"
"$PY" run_research.py --minutes 20 --workers 4 --dataset norman --worker-provider mock --planner-provider scripted \
  --run-dir "$d" --set run.seed=0 > "$L/$n.log" 2>&1
rc=$?
"$PY" analyze_run.py --run "$d" > "$L/$n.analysis.log" 2>&1
after=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$after" >> "$L/progress.md"
# what stops the block (plan, Money), and what the control is for: the new start's score on record
stop=""
[ "$rc" = 0 ] || stop="$stop exit code $rc;"
grep -qE 'WATCHDOG|interrupted; shutting down' "$L/$n.log" && stop="$stop killed or interrupted (see $L/$n.log);"
[ "$after" = "$spent" ] || stop="$stop the ledger moved from \$$spent to \$$after;"
"$PY" - "$d" "$head" "$M/runs/norman_control_replogle_w4_r0" <<'EOF' | tee "$L/$n.check.txt"
import json, sys
from pathlib import Path
d, commit, ref = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
if not (d / "summary.json").exists():
    print("PROBLEM: no summary.json"); sys.exit(1)
s, c = json.loads((d / "summary.json").read_text()), json.loads((d / "config.json").read_text())
pl, best, base, u = s.get("planner") or {}, s.get("best") or {}, s.get("baseline") or {}, s["llm_usage"]
know, ref_know = c["run"].get("external_knowledge"), json.loads((ref / "config.json").read_text())["run"].get("external_knowledge")
print(f"run: code {s['base_commit'][:10]}, split {s['split_id']}, {s['duration_s']} s, seed {c['run']['seed']}, "
      f"knowledge {know} ({ref.name}: {ref_know}), planner {pl.get('configured')} used {pl.get('used')}, "
      f"mixed {pl.get('mixed')}, exhausted_at_min {pl.get('exhausted_at_min')}")
print(f"cost by the run: workers ${u['worker']['cost_usd']:.3f}, planner ${u['planner']['cost_usd']:.3f}")
print(f"selected {best.get('experiment_id')} ({best.get('model')}, {len(best.get('features') or [])} features, "
      f"alpha {best.get('alpha')}) visible {best.get('score')}; reported start {base.get('experiment_id')} {base.get('score')}")
bad = [m for m, hit in [("planner.mixed is not false (planner changed, ran out, or no record)", pl.get("mixed") is not False),
                        (f"cut before it wrote its summary ({s.get('duration_note')})", bool(s.get("duration_note"))),
                        (f"base_commit {s['base_commit']} is not {commit}", s["base_commit"] != commit),
                        (f"external knowledge {know} is not {ref.name}'s {ref_know}", know != ref_know)] if hit]
for m in bad:
    print("PROBLEM:", m)
sys.exit(1 if bad else 0)
EOF
[ "${PIPESTATUS[0]}" = 0 ] || stop="$stop $(grep '^PROBLEM' "$L/$n.check.txt" | sed 's/^PROBLEM: //' | tr '\n' ';')"
echo "baselines, best first (visible pearson_delta; the agents' default parent is the best one with a model):"
sqlite3 "$d/lab.db" "select experiment_id, hypothesis_group, model_type, status, round(primary_score, 4) from experiments where kind='baseline' order by primary_score desc"
start=$(sqlite3 "$d/lab.db" "select hypothesis_group from experiments where kind='baseline' and status='completed' and model_type!='none' and primary_score is not null order by primary_score desc limit 1")
[ "$start" = baseline_ridge_additive ] || stop="$stop the start is '$start', not baseline_ridge_additive as B2 assumes;"
top=$(sqlite3 "$d/lab.db" "select hypothesis_group || ' (' || coalesce(model_type, '?') || ', visible ' || round(primary_score, 4) || ')' from experiments where kind='baseline' and status='completed' and primary_score is not null order by primary_score desc limit 1")
echo "best baseline overall (lab.best(), what the exploit engine refines; analytic ones give it nothing to refine until beaten): $top"
if [ -n "$stop" ]; then
  echo "$(date -u +%Y-%m-%dT%H:%MZ) $n:$stop" >> "$STOPPED"
  echo "STOP (docs/PLAN_AFTER_N4.md, Money):$stop the block stops until the cause is written up ($STOPPED)"
  echo "RUN_DONE rc=$rc STOPPED"; exit 3
fi
ok "the start is baseline_ridge_additive; nothing stops the block"
echo "$(date -u +%Y-%m-%dT%H:%MZ) $head" > "$L/$n.passed"
echo "RUN_DONE rc=$rc"
