#!/bin/bash
# B2's paid runs (docs/PLAN_AFTER_N4.md, B2): the DeepSeek agents start fresh (no --continue-from) on Norman with its
# Replogle file, 4 workers, 20 minutes, from baseline_ridge_additive, on the commit block_b2_control.sh recorded.
# Contains no key: start it as  DEEPSEEK_API_KEY="$API_KEY" bash block_b2_run.sh SEED  with SEED 0, then 1, then 2,
# one at a time, each only after the one before ended with "stop rule passed". The block's caps: the ledger may reach
# $48; this run's workers $1.00 and planner $1.50, so it starts only at a ledger of $45.50 or less.
SEED=$1
case "$SEED" in 0|1|2) ;; *) echo "usage: DEEPSEEK_API_KEY=\"\$API_KEY\" bash block_b2_run.sh 0|1|2"; exit 1 ;; esac
M="$HOME/Documents/Mila/Gene-Mila/gene-mila"; L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
PY="$M/.venv/bin/python"; LEDGER="$M/runs/spend_ledger.sqlite"
COMMIT_FILE="$L/block_after_n4_b2b3_commit.txt"; STOPPED="$L/block_after_n4_stopped.txt"
n=norman_ds_addstart_w4_r$SEED; d="$M/runs/$n"; ctl="$M/runs/norman_control_addstart_w4_r0"
unset API_KEY  # the lab reads DEEPSEEK_API_KEY only; no second copy goes to its processes
no() { unset DEEPSEEK_API_KEY; echo "NOT STARTED: $*"; exit 2; }
ok() { echo "ok: $*"; }
[ -n "$DEEPSEEK_API_KEY" ] || no "no DEEPSEEK_API_KEY in the environment"
ok "a DeepSeek key is in the environment (not shown)"
cd "$M" || no "no checkout at $M"
[ -e "$STOPPED" ] && no "the block is stopped ($STOPPED); write up the cause first"
[ -e "$d" ] && no "$d exists; not overwriting"
pgrep -f run_research.py > /dev/null && no "a lab run is running (pgrep -f run_research.py)"
[ -e "$L/STOP" ] && no "the STOP file $L/STOP is present (it holds every lab run); remove it for this run only"
pgrep -f scale_seq.sh > /dev/null && no "the scaling driver is running (pgrep -f scale_seq.sh)"
ok "block not stopped, no STOP file, $n does not exist, no lab run or driver running"
# order: the control, then seeds 0, 1, 2
[ -e "$L/norman_control_addstart_w4_r0.passed" ] || no "the control has not finished and passed its checks; run block_b2_control.sh first"
if [ "$SEED" -gt 0 ]; then
  p="norman_ds_addstart_w4_r$((SEED - 1))"; [ -e "$L/$p.passed" ] || no "$p has not finished and passed the stop rule"
fi
ok "the control and the seeds before $SEED finished and passed their checks"
# the code: the recorded B2/B3 commit, nothing tracked changed (the controller runs the working tree)
[ -e "$COMMIT_FILE" ] || no "no recorded B2/B3 commit ($COMMIT_FILE); run block_b2_control.sh first"
want=$(cat "$COMMIT_FILE"); head=$(git rev-parse HEAD)
[ "$head" = "$want" ] || no "HEAD $head is not the recorded B2/B3 commit $want"
[ -z "$(git status --porcelain --untracked-files=no)$(git status --porcelain -- genemila configs)" ] \
  || no "tracked files changed, or untracked files under genemila/ or configs/, in $M"
ok "code $head, the recorded commit, clean"
# the knowledge: N2 to N4's Replogle file, byte for byte what the control saw (its run's public copy)
k=$("$PY" -c 'import sys; from genemila.data.bundle import added_knowledge; print(" ".join(added_knowledge(sys.argv[1])))' "$M/data/norman")
[ "$k" = replogle2022_k562 ] || no "knowledge added to data/norman is '$k', not replogle2022_k562"
km=$(md5 -q "$M/data/norman/knowledge/replogle2022_k562.json")
[ "$km" = d9eff528143dcd4d72c87393df724084 ] || no "replogle2022_k562.json has md5 $km, not N2 to N4's d9eff528..."
diff -rq "$M/data/norman/knowledge" "$ctl/public_data/knowledge" || no "data/norman/knowledge differs from what the control saw"
ok "external knowledge replogle2022_k562 only, md5 $km, the same files as the control's"
# the command, and the configuration it gives, checked against the plan before anything is spent
args=(--minutes 20 --workers 4 --dataset norman --planner-provider deepseek --planner-model deepseek-v4-pro
      --worker-provider deepseek --worker-model deepseek-flash --run-dir "$d" --set run.seed="$SEED"
      --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek=48
      --set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5)
echo "command: $PY run_research.py ${args[*]}"
SEED="$SEED" LEDGER="$LEDGER" DATA="$M/data/norman" "$PY" - "${args[@]}" <<'EOF' || no "the configuration is not the plan's (above)"
import os, sys
import run_research as r
c = r.build_config(r.parse_args(sys.argv[1:])); run, b = c["run"], c["budget"]
real = os.path.realpath
checks = [("planner", f"{c['planner']['provider']}:{c['planner']['model']}", "deepseek:deepseek-v4-pro"),
          ("planner.fallback", c["planner"]["fallback"], []),
          ("workers", f"{c['worker']['provider']}:{c['worker']['model']}", "deepseek:deepseek-flash"),
          ("escalation", c["worker"]["escalation_provider"], ""),
          ("dataset, data_dir", (run["dataset"], real(run["data_dir"])), ("norman", real(os.environ["DATA"]))),
          ("minutes, workers, seed", (run["minutes"], run["workers"], run["seed"]), (20, 4, int(os.environ["SEED"]))),
          ("continue_from", run.get("continue_from"), None),
          ("budget.ledger", b["ledger"], os.environ["LEDGER"]),
          ("caps: ledger, workers, planner", (b["cumulative_usd"]["deepseek"], b["max_total_usd"], b["max_planner_usd"]),
           (48, 1.0, 1.5))]
for name, got, want in checks:
    print(("ok: " if got == want else "BAD: ") + f"{name} {got!r}" + ("" if got == want else f", plan {want!r}"))
sys.exit(0 if all(got == want for _, got, want in checks) else 1)
EOF
# the ledger gate: the ledger plus this run's two caps stays within the block's $48
spent=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
[ "$(echo "$spent <= 45.50" | bc)" = 1 ] || no "DeepSeek ledger \$$spent is above \$45.50 (or unreadable)"
ok "DeepSeek ledger \$$spent <= \$45.50"
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n started (code $(git rev-parse --short HEAD), DeepSeek ledger \$$spent)" >> "$L/progress.md"
"$PY" run_research.py "${args[@]}" > "$L/$n.log" 2>&1
rc=$?
unset DEEPSEEK_API_KEY
"$PY" analyze_run.py --run "$d" > "$L/$n.analysis.log" 2>&1
after=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
cost=$(echo "$after - $spent" | bc)
echo "- $(date -u +%Y-%m-%dT%H:%MZ) $n finished rc=$rc DeepSeek ledger \$$after (run \$$cost)" >> "$L/progress.md"
# the stop rule (plan, Money): failed, killed, over $2.00 by the ledger, or planner.mixed true stops the block
stop=""
[ "$rc" = 0 ] || stop="$stop exit code $rc;"
grep -qE 'WATCHDOG|interrupted; shutting down' "$L/$n.log" && stop="$stop killed or interrupted (see $L/$n.log);"
[ -n "$after" ] && [ "$(echo "$cost <= 2.00" | bc)" = 1 ] \
  || stop="$stop cost \$$cost by the ledger (\$$spent to \$$after), over \$2.00 or unreadable;"
"$PY" - "$d" "$want" "$ctl" <<'EOF' | tee "$L/$n.check.txt"
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
# reported, not a stop: the agents' start (the best baseline with a model) and the first planner proposal's parent
if [ -e "$d/summary.json" ]; then
  echo "start (best modelled baseline, the planner's default parent): $(sqlite3 "$d/lab.db" "select experiment_id || ' ' || hypothesis_group || ' visible ' || round(primary_score, 4) from experiments where kind='baseline' and status='completed' and model_type!='none' and primary_score is not null order by primary_score desc limit 1")"
  echo "best baseline overall (lab.best(), what the exploit engine refines; an analytic one gives it nothing until beaten): $(sqlite3 "$d/lab.db" "select experiment_id || ' ' || hypothesis_group || ' ' || coalesce(model_type, '?') || ' visible ' || round(primary_score, 4) from experiments where kind='baseline' and status='completed' and primary_score is not null order by primary_score desc limit 1")"
  echo "first planner proposal: $(sqlite3 "$d/lab.db" "select e.experiment_id || ' parent ' || coalesce(e.parent_id || ' ' || p.hypothesis_group, e.parent_id, 'none') from experiments e left join experiments p on p.experiment_id = e.parent_id where e.kind != 'baseline' and coalesce(e.proposer, '') not like 'python%' order by e.created_at limit 1")"
fi
if [ -n "$stop" ]; then
  echo "$(date -u +%Y-%m-%dT%H:%MZ) $n:$stop" >> "$STOPPED"
  echo "STOP (docs/PLAN_AFTER_N4.md, Money):$stop the block stops until the cause is written up ($STOPPED)"
  echo "RUN_DONE rc=$rc STOPPED"; exit 3
fi
ok "stop rule passed: rc 0, not killed, \$$cost by the ledger, planner unchanged"
echo "$(date -u +%Y-%m-%dT%H:%MZ) $want" > "$L/$n.passed"
echo "RUN_DONE rc=$rc"
