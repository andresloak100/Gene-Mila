"""Wall-clock controller. Owns scheduling, concurrency, timeouts, retries,
the deadline and persistence. Agents never control any of these.

At the deadline it: stops issuing experiments and LLM calls, lets running
experiments finish within a grace window, kills what is left, preserves the
database, artifacts and logs, evaluates the best visible-validation
candidates on the query-only set, and writes the final report.
"""

from __future__ import annotations

import math
import os
import shutil
import threading
import time
import traceback
from pathlib import Path

from . import exploit
from .db import ACTIVE
from .lab import Lab
from .planner import Planner
from .providers import make_provider
from .report import finalize
from .worker import Worker

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

# Concurrent planner rounds get different emphases so they do not propose the same ideas.
PLANNER_FOCI = [
    None,  # balanced: follow the configured explore / exploit / risky mix
    "EXPLORE: propose only new-feature hypotheses from biological idea areas not tried yet (see UNEXPLORED IDEA "
    "AREAS), clearly different from everything IN FLIGHT.",
    "EXPLOIT: improve the current best model: add helpful features missing from it, test untested interactions, "
    "ablate features that do not help, or sweep their parameters.",
    "RISKY: propose bolder, less obvious biological hypotheses than those in flight; accept a higher failure rate.",
]


def build_providers(cfg: dict):
    w = cfg["worker"]
    worker = make_provider(w["provider"], w["model"], {**w, **cfg.get("providers", {}).get(w["provider"], {})})
    esc = None
    if w.get("escalation_provider"):
        esc = make_provider(w["escalation_provider"], w["escalation_model"],
                            {**w, **cfg.get("providers", {}).get(w["escalation_provider"], {})})
    p = cfg["planner"]
    planner = make_provider(p["provider"], p["model"], p)
    fallback = make_provider("scripted", "scripted") if p.get("fallback", "scripted") == "scripted" else None
    return worker, esc, planner, fallback


class Controller:
    def __init__(self, lab: Lab, workers: int, seconds: float, worker_provider=None, escalation=None,
                 planner_provider=None, planner_fallback=None, quiet: bool = False):
        self.lab = lab
        self.cfg = lab.cfg
        self.n_workers = workers
        self.seconds = seconds
        cpu = int(self.cfg["run"].get("cpu_slots") or 0) or (os.cpu_count() or 1)
        self.cpu_slots = threading.Semaphore(cpu)
        self.n_cpu = cpu
        self.worker_provider = worker_provider
        self.escalation = escalation
        self.planner = Planner(lab, planner_provider, planner_fallback) if planner_provider else None
        self.workers: list[Worker] = []
        self.threads: dict[str, threading.Thread] = {}
        self.quiet = quiet
        self.started = None
        self.deadline = None
        self._planner_threads: list[threading.Thread] = []
        self.max_planner_calls = int(self.cfg["schedule"].get("max_planner_calls", 0))  # 0 = no limit
        self.python_exploit = bool(self.cfg["schedule"].get("python_exploit", True))
        self._next_exploit = 0.0
        self.min_free_mb = float(self.cfg["run"].get("min_free_disk_mb", 2000))
        b = self.cfg["budget"]
        if float(b.get("max_planner_usd", 0)) <= 0:  # 0 = scale the planner cap with run length and worker count
            per_wh = float(b.get("planner_usd_per_worker_hour", b.get("planner_usd_per_hour", 15.0) / 4))
            self.lab.gateway.role_caps["planner"] = max(1.0, per_wh * max(4, workers) * seconds / 3600)
        self._halt_logged = False

    @property
    def planner_concurrency(self) -> int:
        k = int(self.cfg["schedule"].get("planner_concurrency", 0) or 0)
        return k if k > 0 else max(1, math.ceil(self.n_workers / 6))

    @property
    def planner_batch(self) -> int:
        return int(self.cfg["schedule"].get("planner_batch", 0) or 0) or min(12, max(6, 2 * self.n_workers))

    # ------------------------------------------------------------------ status
    def status_line(self) -> str:
        c = self.lab.db.count_by_status()
        best = self.lab.best()
        llm = self.lab.db.llm_totals()
        elapsed = max(1.0, time.time() - self.started)
        done = c.get("completed", 0)
        cpu = f"{psutil.cpu_percent():.0f}%" if psutil else "n/a"
        active = sum(1 for w in self.workers if w.current)
        best_txt = f"best {best['primary_score']:.4f} ({best['experiment_id']})" if best else "best n/a"
        return (f"[{time.strftime('%H:%M:%S')}] left {max(0, self.deadline - time.time()):5.0f}s | "
                f"workers {active}/{self.n_workers} active | queued {c.get('queued', 0)} | done {done} | "
                f"failed {c.get('failed', 0)} | rejected {c.get('rejected', 0)} | {best_txt} | "
                f"{done / elapsed * 3600:.0f} exp/h | CPU {cpu} | LLM {llm['calls']} calls ${llm['cost_usd']:.4f}")

    def _log(self, msg: str) -> None:
        line = msg if msg.startswith("[") else f"[{time.strftime('%H:%M:%S')}] {msg}"
        with open(self.lab.run_dir / "controller.log", "a") as fh:
            fh.write(line + "\n")
        if not self.quiet:
            print(line, flush=True)

    # --------------------------------------------------------------- planning
    def _planners_alive(self) -> int:
        self._planner_threads = [t for t in self._planner_threads if t.is_alive()]
        return len(self._planner_threads)

    def _maybe_plan(self) -> None:
        """Start planner rounds while the queue is short: up to `planner_concurrency` at once, each with its
        own focus, so planning keeps up with many workers."""
        if self.planner is None or self.lab.stop_event.is_set():
            return
        alive = self._planners_alive()
        if alive >= self.planner_concurrency:
            return
        if self.max_planner_calls and self.planner.rounds >= self.max_planner_calls:
            return
        why = self._workers_halted()
        if why:  # new hypotheses would only be burned: let the queue drain and stop
            if not self._halt_logged:
                self._halt_logged = True
                self._log(f"worker LLM calls are refused ({why}); no further planning")
            return
        gw = self.lab.gateway
        elapsed = time.time() - (self.started or time.time())
        allowed = gw.role_caps["planner"] * min(1.0, (elapsed + 900) / max(1.0, self.seconds))
        if gw.spent["planner"] + gw.reserved["planner"] >= allowed:
            return  # pace the planner budget over the run instead of spending it all early and halting
        n = self.planner_batch
        low = int(self.cfg["schedule"]["queue_low_water"]) or 2 * self.n_workers
        queued = self.lab.db.count_by_status().get("queued", 0)
        if queued + alive * n >= low:  # rounds in flight will add about n experiments each
            return
        if self.planner.backing_off(float(self.cfg["schedule"]["planner_min_interval_s"])):
            return
        focus = PLANNER_FOCI[alive % len(PLANNER_FOCI)]

        def run():
            try:
                ids = self.planner.refill(n, focus=focus)
                self._log(f"planner round {self.planner.rounds}{' [' + focus.split(':')[0] + ']' if focus else ''}: "
                          f"queued {len(ids)} experiments")
            except Exception as exc:
                self.lab.db.event("planner_crash", f"{type(exc).__name__}: {exc}", level="error")
                self._log(f"planner error: {exc}")
            finally:
                self.lab.db.close_thread_conn()

        t = threading.Thread(target=run, name=f"planner{alive}", daemon=True)
        self._planner_threads.append(t)
        t.start()

    def _maybe_exploit(self) -> None:
        """Keep workers busy while the planner thinks: when fewer experiments are queued than there are
        workers, queue deterministic follow-ups around the current best (no LLM involved)."""
        if not self.python_exploit or self.lab.stop_event.is_set() or time.time() < self._next_exploit:
            return
        self._next_exploit = time.time() + 15
        queued = self.lab.db.count_by_status().get("queued", 0)
        if queued >= self.n_workers:
            return
        n_queued = 0
        for spec in exploit.propose(self.lab, self.n_workers - queued):
            _, status = self.lab.queue(spec)
            n_queued += status == "queued"
        if n_queued:
            self.lab.db.event("python_exploit", f"queued {n_queued} deterministic follow-ups around the best model")
            self._log(f"exploit: queued {n_queued} follow-ups around the best model (no LLM)")

    # ---------------------------------------------------------------- workers
    def _start_worker(self, i: int) -> None:
        wid = f"W{i:03d}"
        w = Worker(self.lab, wid, self.worker_provider, self.escalation, self.cpu_slots)

        def target():
            try:
                w.loop()
            except Exception:
                self.lab.db.event("worker_thread_died", traceback.format_exc()[-1500:], level="error")

        t = threading.Thread(target=target, name=wid, daemon=True)
        if len(self.workers) > i:
            self.workers[i] = w
        else:
            self.workers.append(w)
        self.threads[wid] = t
        t.start()

    def _supervise(self) -> None:
        for i, w in enumerate(self.workers):
            t = self.threads[w.worker_id]
            if not t.is_alive() and not self.lab.stop_event.is_set():
                self._log(f"worker {w.worker_id} died; restarting")
                self._start_worker(i)
        # requeue experiments orphaned by a dead worker (bounded by max_attempts)
        max_attempts = int(self.cfg["experiment"]["max_attempts"])
        live = {w.current for w in self.workers if w.current}
        for e in self.lab.db.query(f"SELECT * FROM experiments WHERE status IN ({','.join('?' * len(ACTIVE))})", ACTIVE):
            if e["experiment_id"] in live:
                continue
            if time.time() - (e.get("heartbeat") or 0) < 30:
                continue
            if (e.get("attempts") or 0) < max_attempts:
                self.lab.db.update_experiment(e["experiment_id"], status="queued")
                self.lab.db.event("requeued", "orphaned experiment requeued", e["experiment_id"])
            else:
                self.lab.db.update_experiment(e["experiment_id"], status="failed", failure_stage="orphaned",
                                              failure_reason="worker lost the experiment; retry limit reached",
                                              finished_at=time.time())

    # -------------------------------------------------------------------- run
    def run(self) -> dict:
        self.started = time.time()
        self.deadline = self.started + self.seconds
        _raise_fd_limit()
        self.lab.db.execute("UPDATE runs SET started_at=?, deadline=?, workers=? WHERE run_id=?",
                            (self.started, self.deadline, self.n_workers, self.lab.run_id))
        if self.lab.git_head_dirty():
            self._log("warning: repository has uncommitted changes; worktrees use the committed HEAD "
                      f"{self.lab.base_commit[:10]}")
        self._log(f"run {self.lab.run_id}: {self.n_workers} workers, {self.n_cpu} CPU slots, "
                  f"{self.seconds / 60:.1f} min, dataset {self.lab.dataset} ({self.lab.split_id}); caps: workers "
                  f"${self.lab.gateway.role_caps['worker']:.2f}, planner ${self.lab.gateway.role_caps['planner']:.2f}")
        self.lab.record_analytic_baselines()
        self.lab.queue_model_baselines()
        prev = self.cfg["run"].get("continue_from")
        if prev:
            info = self.lab.warm_start(Path(prev))
            self._log(f"warm start from {info['run_id']}: {len(info['imported'])} features imported, starting model "
                      f"{info['start_experiment']} on {len(info['features'])} features"
                      + (f"; missing {info['missing']}" if info["missing"] else ""))
        for i in range(self.n_workers):
            self._start_worker(i)
        interval = float(self.cfg["run"]["status_interval_s"])
        next_status = next_disk_check = 0.0
        try:
            while time.time() < self.deadline:
                if self._baselines_done():
                    self._maybe_plan()
                    self._maybe_exploit()
                self._supervise()
                if time.time() >= next_status:
                    self._log(self.status_line())
                    next_status = time.time() + interval
                if self._exhausted():
                    self._log("nothing left to do (planner exhausted and queue empty); stopping early")
                    self.lab.db.event("exhausted", "planner exhausted, queue empty, no exploit follow-up left")
                    break
                if time.time() >= next_disk_check:
                    next_disk_check = time.time() + 30
                    free_mb = shutil.disk_usage(self.lab.run_dir).free / 1e6
                    if free_mb < self.min_free_mb:
                        self._log(f"only {free_mb:.0f} MB free on disk (limit {self.min_free_mb:.0f}); stopping early")
                        self.lab.db.event("disk_low", f"{free_mb:.0f} MB free", level="error")
                        break
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._log("interrupted; shutting down")
        return self.shutdown()

    def _baselines_done(self) -> bool:
        return not self.lab.db.query("SELECT 1 FROM experiments WHERE kind='baseline' AND status IN "
                                     "('queued','claimed','running')")

    def _workers_halted(self) -> str | None:
        """Why worker LLM calls are refused for the rest of the run (a dollar cap), else None."""
        pname = self.worker_provider.name if self.worker_provider is not None else ""
        return self.lab.gateway.is_halted("worker", pname)

    def _exhausted(self) -> bool:
        """True only when no more work can come: the planner hit its call limit or ran dry, or the worker
        budget is spent, nothing is queued and no worker is busy. An LLM planner that had empty or failed
        rounds backs off and tries again."""
        if self._planners_alive():
            return False
        if self.planner is not None and not self._workers_halted():
            capped = self.max_planner_calls and self.planner.rounds >= self.max_planner_calls
            if not capped and not self.planner.dry():
                return False
        c = self.lab.db.count_by_status()
        if c.get("queued", 0) or any(w.current for w in self.workers):
            return False
        if self.python_exploit:  # the throttle must not end a run while follow-ups remain
            self._next_exploit = 0.0
            self._maybe_exploit()
            if self.lab.db.count_by_status().get("queued", 0):
                return False
        return True

    def shutdown(self) -> dict:
        self.lab.stop_event.set()
        grace = float(self.cfg["run"]["shutdown_grace_s"])
        self._log(f"deadline: no new experiments; waiting up to {grace:.0f}s for running experiments")
        end = time.time() + grace
        while time.time() < end and any(w.current for w in self.workers):
            time.sleep(0.25)
        if any(w.current for w in self.workers):
            self._log("grace window over: terminating remaining experiments")
            self.lab.kill_event.set()
            end = time.time() + 10
            while time.time() < end and any(w.current for w in self.workers):
                time.sleep(0.25)
        for e in self.lab.db.query(f"SELECT experiment_id FROM experiments WHERE status IN "
                                   f"({','.join('?' * len(ACTIVE))})", ACTIVE):
            self.lab.db.update_experiment(e["experiment_id"], status="killed", failure_stage="deadline",
                                          failure_reason="terminated at the run deadline", finished_at=time.time())
        self.lab.db.execute("UPDATE experiments SET status='cancelled', failure_reason='not started before deadline' "
                            "WHERE status='queued'")
        self.lab.db.execute("DELETE FROM experiments WHERE status='reserved'")
        self._log(self.status_line())
        self.lab.close()
        # the run's end is the end of experimentation; final scoring and summaries that follow are not
        # worker time (analysis divides throughput and cost by this span)
        self.lab.db.execute("UPDATE runs SET finished_at=? WHERE run_id=?", (time.time(), self.lab.run_id))
        summary = finalize(self.lab, wall_s=time.time() - self.started, workers=self.n_workers)
        self._log(f"summary written to {self.lab.run_dir / 'summary.md'}")
        return summary


def _raise_fd_limit(target: int = 4096) -> None:
    """Many workers hold pipes, logs and database handles; macOS defaults to 256 open files."""
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        want = target if hard == resource.RLIM_INFINITY else min(target, hard)
        if soft != resource.RLIM_INFINITY and soft < want:
            resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
    except (ImportError, ValueError, OSError):
        pass
