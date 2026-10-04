"""Subprocess execution with hard limits: wall-clock timeout, CPU seconds,
address space (Linux) / RSS polling (everywhere), and external kill events."""

from __future__ import annotations

import json
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


class ForkServerClient:
    """Thread-safe client for genemila.forkserver (one server per run)."""

    def __init__(self, server_cwd: Path, public_dir: Path | None = None, cache_dir: Path | None = None):
        cmd = [sys.executable, "-m", "genemila.forkserver"]
        if public_dir:
            cmd += ["--public", str(public_dir)]
        if cache_dir:
            cmd += ["--cache", str(cache_dir)]
        env = {**os.environ, "PYTHONPATH": str(server_cwd), "OMP_NUM_THREADS": "1",
               "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
        self.proc = subprocess.Popen(cmd, cwd=server_cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     env=env, text=True, bufsize=1, start_new_session=True)
        self._lock = threading.Lock()
        self._next = 0
        self._started: dict[int, dict] = {}
        self._exits: dict[int, dict] = {}
        self._cv = threading.Condition()
        self.healthy = True
        line = self.proc.stdout.readline()
        if not line or "ready" not in line:
            self.healthy = False
            raise RuntimeError("fork server failed to start")
        threading.Thread(target=self._reader, daemon=True, name="forkserver-reader").start()

    def _reader(self) -> None:
        for line in self.proc.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            with self._cv:
                if "exit" in msg:
                    self._exits[msg["exit"]] = msg
                elif "id" in msg:
                    self._started[msg["id"]] = msg
                self._cv.notify_all()
        with self._cv:
            self.healthy = False
            self._cv.notify_all()

    def spawn(self, req: dict, timeout: float = 10.0) -> int:
        with self._lock:
            self._next += 1
            rid = self._next
            self.proc.stdin.write(json.dumps({**req, "id": rid}) + "\n")
            self.proc.stdin.flush()
        with self._cv:
            if not self._cv.wait_for(lambda: rid in self._started or not self.healthy, timeout=timeout):
                # the request is in the server's pipe: kill the server so it cannot fork an unsupervised copy later
                self.healthy = False
                try:
                    self.proc.kill()
                except Exception:
                    pass
                raise RuntimeError("fork server did not answer")
            if rid not in self._started:
                raise RuntimeError("fork server died")
            return self._started.pop(rid)["pid"]

    def poll_exit(self, pid: int) -> dict | None:
        with self._cv:
            return self._exits.pop(pid, None)

    def wait_exit(self, pid: int, timeout: float) -> dict | None:
        with self._cv:
            self._cv.wait_for(lambda: pid in self._exits or not self.healthy, timeout=timeout)
            return self._exits.pop(pid, None)

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


def run_forked(client: ForkServerClient, argv: list[str], cwd: Path, log_dir: Path, timeout_s: float,
               ram_mb: float | None = None, cpu_s: float | None = None,
               kill_event: threading.Event | None = None, name: str = "proc") -> ProcResult:
    """Same contract as run_limited, for a child forked by the warm server."""
    log_dir.mkdir(parents=True, exist_ok=True)
    out_p, err_p = log_dir / f"{name}.stdout", log_dir / f"{name}.stderr"
    t0 = time.monotonic()
    pid = client.spawn({"argv": argv, "cwd": str(cwd), "stdout": str(out_p), "stderr": str(err_p),
                        "ram_mb": ram_mb, "cpu_s": cpu_s})
    ps = None
    if psutil:
        try:
            ps = psutil.Process(pid)
        except psutil.Error:
            ps = None
    peak, timed_out, reason, done = 0.0, False, None, None

    def kill(why: str):
        nonlocal reason, done
        reason = reason or why
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pid, sig)
            except (ProcessLookupError, PermissionError):
                return
            d = client.wait_exit(pid, 2.0)
            if d is not None:
                done = d  # keep the real exit status and CPU time
                return

    while True:
        done = client.poll_exit(pid)
        if done is not None:
            break
        if not client.healthy:
            try:  # the child would otherwise run on unsupervised while the caller reruns the experiment
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            raise RuntimeError("fork server died during an experiment")
        if ps is not None:
            try:
                rss = ps.memory_info().rss / 2**20
                peak = max(peak, rss)
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
            done = done or client.wait_exit(pid, 5.0) or {"status": -9, "cpu_s": 0.0, "maxrss": 0}
            break
        time.sleep(0.02)
    maxrss = (done.get("maxrss") or 0) / (2**20 if sys.platform == "darwin" else 1024)
    return ProcResult(done["status"], time.monotonic() - t0, done.get("cpu_s") or 0.0, max(peak, maxrss),
                      timed_out, reason, _tail(out_p), _tail(err_p))


class Executor:
    """Runs pipeline commands either in the warm fork server or as fresh subprocesses.

    Falls back to fresh subprocesses automatically if the server cannot start or dies."""

    def __init__(self, mode: str = "forkserver", server_cwd: Path | None = None, public_dir: Path | None = None,
                 cache_dir: Path | None = None, on_fallback=None):
        self.mode = mode
        self.cache_dir = cache_dir
        self.client: ForkServerClient | None = None
        self._lock = threading.Lock()
        self._args = (server_cwd, public_dir, cache_dir)
        self.fallbacks = 0
        self.on_fallback = on_fallback  # called with a message whenever the server is bypassed

    def _ensure_client(self) -> ForkServerClient | None:
        if self.mode != "forkserver":
            return None
        with self._lock:
            if self.client is not None and self.client.healthy:
                return self.client
            try:
                self.client = ForkServerClient(*self._args)
            except Exception:
                self.client = None
                self.mode = "subprocess"
            return self.client

    def run(self, argv: list[str], cwd: Path, log_dir: Path, timeout_s: float, ram_mb=None, cpu_s=None,
            env: dict | None = None, kill_event=None, name: str = "proc") -> ProcResult:
        if self.cache_dir:
            argv = [*argv, "--cache", str(self.cache_dir)]
        client = self._ensure_client()
        if client is not None:
            try:
                return run_forked(client, argv, cwd, log_dir, timeout_s, ram_mb, cpu_s, kill_event, name)
            except (RuntimeError, OSError) as exc:  # server trouble: rerun this one as a fresh subprocess
                self.fallbacks += 1
                if self.on_fallback is not None:
                    self.on_fallback(f"fork server bypassed ({type(exc).__name__}: {exc}); fresh subprocess")
        return run_limited([sys.executable, "-m", "genemila.pipeline", *argv], cwd, log_dir, timeout_s, ram_mb,
                           cpu_s, env, kill_event, name)

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
