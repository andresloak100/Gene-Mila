#!/bin/bash
# receipt.sh RECEIPT_DIR NAME -- COMMAND...
# Runs COMMAND with stdout and stderr in NAME.log and writes NAME.command.txt, NAME.exit and NAME.runtime.json
# (UTC start and end, wall seconds, exit code, cwd, machine) beside it. API keys and tokens are removed from the
# command's environment before it starts.
set -u
dir="$1"; name="$2"; shift 2; [ "${1:-}" = "--" ] && shift
mkdir -p "$dir"
printf '%s\n' "$*" > "$dir/$name.command.txt"
ts() { python3 -c 'import datetime;print(datetime.datetime.now(datetime.timezone.utc).isoformat())'; }
start=$(ts); s0=$(python3 -c 'import time;print(time.time())')
env -u DEEPSEEK_API_KEY -u API_KEY -u GITHUB_TOKEN -u GH_TOKEN "$@" > "$dir/$name.log" 2>&1
rc=$?
end=$(ts); s1=$(python3 -c 'import time;print(time.time())')
echo "$rc" > "$dir/$name.exit"
python3 - "$dir/$name.runtime.json" "$start" "$end" "$s0" "$s1" "$rc" "$PWD" <<'PY'
import json, sys, platform
p, start, end, s0, s1, rc, cwd = sys.argv[1:]
json.dump({"start_utc": start, "end_utc": end, "wall_seconds": round(float(s1) - float(s0), 3), "exit": int(rc),
           "cwd": cwd, "machine": platform.platform()}, open(p, "w"), indent=1)
PY
exit $rc
