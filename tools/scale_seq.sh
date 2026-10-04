#!/bin/bash
# Paid comparison driver, one run at a time. Contains no key: DEEPSEEK_API_KEY must be in the
# environment of the process that starts it. A file named STOP in this directory halts it
# between runs. It waits for any other lab run on the machine to finish before each start.
#
#   nohup caffeinate -i -s bash scale_seq.sh > driver.log 2>&1 &
#
# Sequence: scale_w8_r1, scale_w16_r1 (old code, Opus planner, no failover), then
# newcode_opus_w4_r0/_r1 (current code, Opus planner, DeepSeek planner as failover), then
# newcode_ds_w4_r0/_r1 (current code, DeepSeek planner). If the Claude CLI is at its usage
# limit, the DeepSeek-planned runs go first and the Opus-planned ones are retried afterwards.

L="$HOME/Documents/Loak-documents/genemila_scale_logs"
MAIN="$HOME/Documents/Loak-documents/gene-mila"
OLD="$HOME/Documents/Loak-documents/gene-mila-2492e11"
PY="$MAIN/.venv/bin/python"
LEDGER="$MAIN/runs/spend_ledger.sqlite"
LEDGER_STOP=14          # start no paid run once DeepSeek spend reaches this
PROBE_EVERY=900         # seconds between Claude CLI probes
PROBE_MAX=18000         # give up on the Opus-planned runs after this long

log() { echo "- $(date -u +%Y-%m-%dT%H:%MZ) $*" >> "$L/progress.md"; }
deepseek_spend() { sqlite3 "$LEDGER" "SELECT ROUND(COALESCE(SUM(cost_usd),0),2) FROM spend WHERE provider='deepseek'"; }
stop_requested() { [ -f "$L/STOP" ]; }

wait_idle() {  # never overlap with another lab run (timing measures would be distorted)
  while pgrep -f "run_research.py" > /dev/null; do sleep 30; done
}

claude_ok() {  # one tiny planner call; fails on the usage limit or any CLI error
  out=$(claude -p "Reply with the single word OK." --model opus 2>&1 | head -c 400)
  case "$out" in *"limit"*|*"Limit"*|"") return 1;; esac
  case "$out" in *OK*|*ok*|*Ok*) return 0;; esac
  return 1
}

contaminated() {  # true if the scripted planner proposed anything, or the planner errored
  n=$(sqlite3 "$1/lab.db" "SELECT (SELECT COUNT(*) FROM experiments WHERE proposer LIKE '%scripted%') + (SELECT COUNT(*) FROM events WHERE kind IN ('planner_error','breaker_open'))" 2>/dev/null)
  [ "${n:-0}" -gt 0 ]
}

# run_one <name> <code dir> <args...>
run_one() {
  name=$1; code=$2; shift 2
  dir="$MAIN/runs/$name"
  if [ -f "$dir/summary.json" ]; then log "$name already has summary.json; skipped"; return 0; fi
  if stop_requested; then log "STOP file present; halted before $name"; exit 3; fi
  spent=$(deepseek_spend)
  if [ "$(echo "$spent >= $LEDGER_STOP" | bc)" = 1 ]; then log "LEDGER GATE: DeepSeek \$$spent >= \$$LEDGER_STOP; $name not started"; return 2; fi
  wait_idle
  [ -d "$dir" ] && mv "$dir" "${dir}_interrupted_$(date -u +%H%M)"
  log "$name started (code $(git -C "$code" rev-parse --short HEAD), DeepSeek ledger \$$spent)"
  ( cd "$code" && "$PY" run_research.py --dataset adamson_cf --minutes 20 --quiet \
      --set run.data_dir="$MAIN/data/adamson_cf" --set budget.ledger="$LEDGER" \
      --run-dir "$dir" "$@" ) > "$L/$name.log" 2>&1
  rc=$?
  ( cd "$MAIN" && "$PY" analyze_run.py --run "$dir" ) > "$L/$name.analysis.log" 2>&1
  log "$name finished rc=$rc summary=$([ -f "$dir/summary.json" ] && echo yes || echo NO) DeepSeek ledger \$$(deepseek_spend) -> $dir"
  [ -f "$dir/summary.json" ] || { log "HALT: $name wrote no summary.json"; exit 5; }
  return 0
}

old_opus() {   # <name> <workers> <worker cap>; old code has no planner failover
  run_one "$1" "$OLD" --workers "$2" --set run.seed=1 --planner-provider claude_cli --planner-model opus \
      --set budget.cumulative_usd.deepseek=10 --set budget.max_total_usd="$3" || return $?
  if contaminated "$MAIN/runs/$1"; then
    mv "$MAIN/runs/$1" "$MAIN/runs/${1}_contaminated"
    log "$1 CONTAMINATED (scripted planner or planner errors); renamed ${1}_contaminated"
    return 9
  fi
}
new_opus() {   # <seed>
  run_one "newcode_opus_w4_r$1" "$MAIN" --workers 4 --set run.seed="$1" --planner-provider claude_cli --planner-model opus \
      --set planner.fallback=deepseek:deepseek-v4-pro --set budget.cumulative_usd.deepseek=15 --set budget.max_total_usd=1.5
}
new_ds() {     # <seed>
  run_one "newcode_ds_w4_r$1" "$MAIN" --workers 4 --set run.seed="$1" --planner-provider deepseek --planner-model deepseek-v4-pro \
      --set budget.cumulative_usd.deepseek=15 --set budget.max_total_usd=2.5
}
opus_runs() {  # each Opus-planned run is preceded by a probe; a contaminated old-code run is redone once
  for spec in "w8 8 2" "w16 16 3"; do
    set -- $spec
    for attempt in 1 2; do
      claude_ok || return 1
      old_opus "scale_${1}_r1" "$2" "$3"; r=$?
      [ $r = 9 ] || break
    done
  done
  for s in 0 1; do claude_ok || return 1; new_opus $s; done
  return 0
}

[ -n "$DEEPSEEK_API_KEY" ] || { log "HALT: DEEPSEEK_API_KEY is not in the driver's environment"; exit 6; }
log "paid driver started (pid $$)"

ds_done=0
waited=0
until opus_runs; do
  log "Claude CLI probe failed (usage limit or CLI error)"
  if [ $ds_done = 0 ]; then new_ds 0; new_ds 1; ds_done=1; continue; fi
  if [ $waited -ge $PROBE_MAX ]; then log "gave up on the Opus-planned runs after ${PROBE_MAX}s of probing"; break; fi
  stop_requested && { log "STOP file present; halted while waiting for the Claude CLI"; exit 3; }
  sleep $PROBE_EVERY; waited=$((waited + PROBE_EVERY))
done
[ $ds_done = 0 ] && { new_ds 0; new_ds 1; }
log "paid driver complete"
