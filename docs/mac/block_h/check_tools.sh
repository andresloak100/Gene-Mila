#!/bin/bash
# Block H, step 2 (docs/PLAN_H_COMPARISON.md): what the Mac has, before anything paid. Free. Prints a report to post
# on #41; creates nothing but the Docker network genemila_h (free, local). Run from a login zsh:
#   bash ~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_h/check_tools.sh
# It does not write isolation.txt: that line is written by hand from Andres's answer (plan, Isolation).
. "$(dirname "$0")/block_h_common.sh"
echo "== $(utc) block H tool check"
for t in docker gtimeout claude codex sqlite3 screen caffeinate; do printf '%-10s %s\n' "$t" "$(command -v "$t" || echo MISSING)"; done
echo "python     $PY $("$PY" -c 'import platform; print(platform.python_version())' 2>&1)"
echo "== the clone with the runners: $C"
for f in ledger_proxy.py run_biomni.py run_autoresearch.sh collect_handback.py; do
  printf '%-22s %s\n' "$f" "$([ -e "$C/tools/baselines/$f" ] && echo present || echo MISSING)"
done
[ -d "$C" ] && echo "clone at $(git -C "$C" rev-parse --short=7 HEAD 2> /dev/null) ($(git -C "$C" status --porcelain --untracked-files=no | wc -l | tr -d ' ') changed files)"
echo "== the A2 checkout: $HOME/Documents/Mila/Gene-Mila/gene-mila-baa7dfd at $(git -C "$HOME/Documents/Mila/Gene-Mila/gene-mila-baa7dfd" rev-parse --short=7 HEAD 2> /dev/null || echo MISSING)"
echo "== the package: $PKG_SRC"
if [ -e "$PKG_SRC/MANIFEST.json" ]; then (pkg_checks); else echo "not exported yet (ROADMAP section 6, step 7)"; fi
echo "== tier.txt (harness or none, Andres's word on the harness tier): $(cat "$H/tier.txt" 2> /dev/null || echo not written)"
echo "== the ledger: \$$(ledger) (provider deepseek); running: $(pgrep -fl 'run_research.py|scale_seq.sh|feature_compare.py|ledger_proxy.py' | tr '\n' ';' || echo none)"
echo "== UTC now $(date -u +%H:%M), $(date -u +%A); ROADMAP D1 names 01:00-04:00 and 06:00-10:00 UTC on weekdays as DeepSeek's peak hours: start outside them when the session allows"
echo "== Docker"
if command -v docker > /dev/null && docker info > /dev/null 2>&1; then
  echo "daemon running; image genemila-h: $(docker image inspect genemila-h > /dev/null 2>&1 && echo present || echo "MISSING (docker build -t genemila-h -f $C/docs/mac/block_h/Dockerfile --build-arg PKG_REQS=\"\$(tr '\\n' ' ' < $PKG_SRC/requirements.txt)\" $C)")"
  docker network inspect genemila_h > /dev/null 2>&1 || { docker network create --internal genemila_h > /dev/null && echo "network genemila_h created (internal: no route to the internet)"; }
  # the egress test: a throwaway listener on the Mac stands in for the proxy; the relay must reach it, the internet must not
  "$PY" -m http.server --bind 127.0.0.1 $PORT > /dev/null 2>&1 & LISTENER=$!
  docker rm -f h_relay > /dev/null 2>&1
  docker run -d --rm --name h_relay --network genemila_h alpine/socat TCP-LISTEN:$PORT,fork,reuseaddr TCP:host.docker.internal:$PORT > /dev/null \
    && docker network connect bridge h_relay && sleep 2
  echo "from a container on genemila_h: api.deepseek.com $(docker run --rm --network genemila_h alpine/socat -T 5 - TCP:api.deepseek.com:443,connect-timeout=5 < /dev/null > /dev/null 2>&1 && echo REACHABLE: egress not blocked || echo unreachable: good); relay $(docker run --rm --network genemila_h alpine/socat -T 5 - TCP:h_relay:$PORT,connect-timeout=5 < /dev/null > /dev/null 2>&1 && echo reachable: good || echo UNREACHABLE: the proxy route does not work)"
  kill "$LISTENER" 2> /dev/null; wait "$LISTENER" 2> /dev/null; docker rm -f h_relay > /dev/null 2>&1
  echo "isolation available: docker (write 'docker' into $H/isolation.txt once Andres has said so)"
else
  echo "no Docker daemon; isolation needs the second macOS account (write 'account <name>' into $H/isolation.txt once Andres has created it)"
  echo "that account needs: a Python 3.11+ venv at /Users/<account>/genemila_h_venv (or H_ACCOUNT_VENV) with biomni, langchain, langgraph==0.3.18, openai and the package's requirements.txt; Claude Code (claude) on that venv's bin or /usr/local/bin or /opt/homebrew/bin; $SHARED writable. The first session's checks verify both (sudo asks for the password)."
fi
echo "== done; post this output on #41"
