#!/bin/bash
# Block H: reset a failed probe so block_h_probe.sh can run again (docs/PLAN_H_COMPARISON.md, step 6, note of
# 2026-10-17 22:00 UTC). A failed probe leaves files the scripts refuse to overwrite or to run beside: h_probe*.log,
# h_probe*.txt (the check, credential-scan and val1-scan files), proxy/h_probe* (the proxy's log and its own output),
# work/h_probe*, out/h_probe* and handback/h_probe* (the package copy, the runner's output and the hand-back, in account
# mode under $SHARED too), and block_h_stopped.txt when session_after stopped the block. This script moves them, never
# deletes, into $H/failed/h_probe_<utc>/ and appends one line to progress.md. It runs only once the cause is written up
# in the plan's dated note: the argument names that note. Usage:
#   bash block_h_reset_probe.sh '<date of the plan note that writes the failure up>'
# It refuses when the probe passed (nothing to reset), when nothing of a failed probe exists, when a proxy or an
# h_agent container is running, and when block_h_stopped.txt holds a stop of another session (that one is written up
# and reset by hand: the stop of an arm is never cleared here).
. "$(dirname "$0")/block_h_common.sh"
NOTE="$1"
[ -n "$NOTE" ] || { echo "usage: $0 '<date of the plan note that writes the failure up>'"; exit 1; }
[ -e "$H/h_probe.passed" ] && no "the probe passed; nothing to reset"
pgrep -f '[l]edger_proxy.py' > /dev/null && no "a ledger proxy is running"
docker ps --format '{{.Names}}' 2> /dev/null | grep -qx h_agent && no "an h_agent container is running"
if [ -e "$H/block_h_stopped.txt" ] && grep -qvE '^[^ ]+ h_probe:' "$H/block_h_stopped.txt"; then
  no "block_h_stopped.txt holds a stop of another session; write it up in the plan and reset it by hand"
fi
found=""
for p in "$H"/h_probe* "$H"/proxy/h_probe* "$H"/work/h_probe* "$H"/out/h_probe* "$H"/handback/h_probe* \
         "$SHARED"/work/h_probe* "$SHARED"/out/h_probe* "$SHARED"/proxy/h_probe* "$H/block_h_stopped.txt"; do
  [ -e "$p" ] && found="$found$p
"
done
[ -n "$found" ] || no "no failed probe to reset (nothing of h_probe under $H or $SHARED)"
D="$H/failed/h_probe_$(date -u +%Y%m%dT%H%MZ)"
[ -e "$D" ] && no "$D exists; wait a minute"
mkdir -p "$D/proxy" "$D/work" "$D/out" "$D/handback" "$D/shared" || no "cannot make $D"
moved=0
move() {  # move <path> <destination directory>
  [ -e "$1" ] || return 0
  mv "$1" "$2/" || no "could not move $1 to $2"
  moved=$((moved + 1))
}
for p in "$H"/h_probe* "$H/block_h_stopped.txt"; do move "$p" "$D"; done
for p in "$H"/proxy/h_probe*; do move "$p" "$D/proxy"; done
for d in work out handback; do for p in "$H/$d"/h_probe*; do move "$p" "$D/$d"; done; done
for d in work out proxy; do for p in "$SHARED/$d"/h_probe*; do mkdir -p "$D/shared/$d"; move "$p" "$D/shared/$d"; done; done
printf '%s\n' "$found" > "$D/moved.txt"
echo "- $(utc) probe reset: $moved files or directories of the failed probe moved to $D (cause written up: $NOTE)" >> "$L/progress.md"
echo "reset: $moved files or directories moved to $D; block_h_probe.sh may run again (the chain reruns it, its .passed marker being absent)"
