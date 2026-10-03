"""Subprocess execution with hard limits: wall-clock timeout, CPU seconds,
address space (Linux) / RSS polling (everywhere), and external kill events."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover (non-POSIX)
    resource = None

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


@dataclass
class ProcResult:
    returncode: int | None
    wall_s: float
    cpu_s: float
    peak_rss_mb: float
    timed_out: bool = False
    killed_reason: str | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""


def _limits(ram_mb: float | None, cpu_s: float | None):
    def apply():
        if resource is None:
            return
        try:
            if ram_mb and sys.platform.startswith("linux"):
                b = int(ram_mb * 1024 * 1024)
                resource.setrlimit(resource.RLIMIT_AS, (b, b))
            if cpu_s:
                resource.setrlimit(resource.RLIMIT_CPU, (int(cpu_s), int(cpu_s) + 5))
        except (ValueError, OSError):
            pass
    return apply


def _tail(path: Path, n: int = 3000) -> str:
    try:
        data = path.read_bytes()
        return data[-n:].decode(errors="replace")
    except OSError:
        return ""


def run_limited(cmd: list[str], cwd: Path, log_dir: Path, timeout_s: float, ram_mb: float | None = None,
                cpu_s: float | None = None, env: dict | None = None, kill_event: threading.Event | None = None,
                name: str = "proc") -> ProcResult:
    log_dir.mkdir(parents=True, exist_ok=True)
    out_p, err_p = log_dir / f"{name}.stdout", log_dir / f"{name}.stderr"
    full_env = {**os.environ, **(env or {})}
    full_env.setdefault("OMP_NUM_THREADS", "1")
    full_env.setdefault("OPENBLAS_NUM_THREADS", "1")
    full_env.setdefault("MKL_NUM_THREADS", "1")
    t0 = time.monotonic()
    with open(out_p, "wb") as out, open(err_p, "wb") as err:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=out, stderr=err, env=full_env,
                                preexec_fn=_limits(ram_mb, cpu_s), start_new_session=True)
    ps = psutil.Process(proc.pid) if psutil else None
    peak_rss, timed_out, reason, status, rusage = 0.0, False, None, None, None

    def kill(why: str):
        nonlocal reason
        reason = reason or why
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(proc.pid, sig)
            except (ProcessLookupError, PermissionError):
                return
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if os.waitpid(proc.pid, os.WNOHANG) != (0, 0):
                    return
                time.sleep(0.05)

    while True:
        pid, status, rusage = os.wait4(proc.pid, os.WNOHANG)
        if pid != 0:
            break
        if ps is not None:
            try:
                rss = ps.memory_info().rss / 2**20
                for ch in ps.children(recursive=True):
                    rss += ch.memory_info().rss / 2**20
                peak_rss = max(peak_rss, rss)
                if ram_mb and rss > ram_mb:
                    kill(f"memory limit exceeded ({rss:.0f} MB > {ram_mb:.0f} MB)")
            except psutil.Error:
                pass
        if time.monotonic() - t0 > timeout_s:
            timed_out = True
            kill(f"timeout after {timeout_s:.0f}s")
        elif kill_event is not None and kill_event.is_set():
            kill("terminated by controller (deadline)")
        if reason:
            try:
                pid, status, rusage = os.wait4(proc.pid, 0)
            except ChildProcessError:
                status, rusage = None, None
            break
        time.sleep(0.05)

    proc.returncode = os.waitstatus_to_exitcode(status) if status is not None else -9
    cpu = (rusage.ru_utime + rusage.ru_stime) if rusage else 0.0
    if rusage:
        maxrss = rusage.ru_maxrss / (2**20 if sys.platform == "darwin" else 1024)
        peak_rss = max(peak_rss, maxrss)
    return ProcResult(proc.returncode, time.monotonic() - t0, cpu, peak_rss, timed_out, reason,
                      _tail(out_p), _tail(err_p))
