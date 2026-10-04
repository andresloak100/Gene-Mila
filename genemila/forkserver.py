"""Warm fork server for experiment subprocesses.

Starting a fresh Python interpreter and importing numpy/scipy/sklearn costs
about a second of CPU per experiment, which dominated measured CPU use. This
single-threaded server imports everything and loads the public data once,
then forks one child per request. Each child is still a separate process
with its own session, resource limits, working directory and log files, so
isolation, timeouts and kills work exactly as for a fresh subprocess.

The server runs from a worktree at the run's base commit; experiment
worktrees may differ only in feature plugins (enforced by the diff guard),
which children load from the request's plugin directory.

Protocol: JSON lines. Request on stdin:
    {"id": 1, "argv": [...pipeline args...], "cwd": ..., "stdout": ..., "stderr": ..., "ram_mb": ..., "cpu_s": ...}
Replies on stdout:
    {"id": 1, "pid": 1234}                                  (child started)
    {"exit": 1234, "status": 0, "cpu_s": 0.4, "maxrss": ...} (child finished)
"""

from __future__ import annotations

import json
import os
import selectors
import signal
import sys
import traceback


def _child(req: dict) -> None:
    code = 70
    try:
        os.setsid()
        from .sandbox import _limits
        _limits(req.get("ram_mb"), req.get("cpu_s"))()
        os.chdir(req["cwd"])
        for fd, path in ((1, req["stdout"]), (2, req["stderr"])):
            f = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            os.dup2(f, fd)
            os.close(f)
        os.close(0)
        from . import pipeline
        code = pipeline.main(req["argv"])
        sys.stdout.flush()
        sys.stderr.flush()
    except BaseException:
        try:
            traceback.print_exc()
            sys.stderr.flush()
        except Exception:
            pass
    finally:
        os._exit(code if isinstance(code, int) else 70)


def serve(public_dir: str | None, cache_dir: str | None) -> None:
    import numpy  # noqa: F401  (warm imports inherited by every child)
    import scipy  # noqa: F401
    import sklearn.linear_model  # noqa: F401
    from . import pipeline  # noqa: F401
    from .features import registry  # noqa: F401
    from .features.api import FeatureContext
    if public_dir:
        # data only; no BLAS work before fork (fork-safety on macOS Accelerate)
        FeatureContext.shared(public_dir, os.path.join(cache_dir, "shared") if cache_dir else None)
    out = sys.stdout

    def send(msg: dict) -> None:
        out.write(json.dumps(msg) + "\n")
        out.flush()

    send({"ready": os.getpid()})
    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)
    buf = ""
    live: set[int] = set()
    while True:
        for _key, _ in sel.select(timeout=0.05):
            chunk = os.read(sys.stdin.fileno(), 65536).decode()
            if not chunk:  # controller went away: nothing supervises the children any more
                for p in live:
                    try:
                        os.killpg(p, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
                return
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if not line.strip():
                    continue
                req = json.loads(line)
                out.flush()
                pid = os.fork()
                if pid == 0:
                    _child(req)
                live.add(pid)
                send({"id": req["id"], "pid": pid})
        while True:
            try:
                pid, status, ru = os.wait4(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
            live.discard(pid)
            send({"exit": pid, "status": os.waitstatus_to_exitcode(status),
                  "cpu_s": ru.ru_utime + ru.ru_stime, "maxrss": ru.ru_maxrss})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--public")
    ap.add_argument("--cache")
    a = ap.parse_args()
    serve(a.public, a.cache)
