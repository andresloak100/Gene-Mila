#!/bin/bash
# Mac checks of 17 Oct 2026 (claim #68): a pass-through for check_tools.sh that adds --pull=never to every
# `docker run`, so no image is downloaded without Andres's approval. Every other docker command is unchanged.
REAL=/usr/local/bin/docker
if [ "$1" = run ]; then
  shift
  "$REAL" run --pull=never "$@"; rc=$?
  [ "$rc" -ne 0 ] && echo "$(date -u +%H:%M:%SZ) docker run --pull=never $* -> exit $rc" >> "${SHIM_LOG:-/dev/null}"
  exit "$rc"
fi
exec "$REAL" "$@"
