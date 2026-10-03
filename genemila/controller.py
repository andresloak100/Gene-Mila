"""Wall-clock controller. Owns scheduling, concurrency, timeouts, retries,
the deadline and persistence. Agents never control any of these.

At the deadline it: stops issuing experiments and LLM calls, lets running
experiments finish within a grace window, kills what is left, preserves the
database, artifacts and logs, evaluates the best visible-validation
candidates on the query-only set, and writes the final report.
"""

from __future__ import annotations

import os
import threading
import time
import traceback
from pathlib import Path

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
        self._planner_thread: threading.Thread | None = None
        self.max_planner_calls = int(self.cfg["schedule"]["max_planner_calls"])

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
    def _maybe_plan(self) -> None:
        if self.planner is None or self.lab.stop_event.is_set():
            return
        if self._planner_thread and self._planner_thread.is_alive():
            return
        if self.planner.rounds >= self.max_planner_calls:
            return
        low = int(self.cfg["schedule"]["queue_low_water"]) or 2 * self.n_workers
        queued = self.lab.db.count_by_status().get("queued", 0)
        if queued >= low:
            return
        # back off only when the previous round produced nothing new (avoids hammering a failing planner)
        if self.planner.last_queued == 0 and self.planner.rounds > 0 and \
                time.time() - self.planner.last_call < float(self.cfg["schedule"]["planner_min_interval_s"]):
            return
        n = int(self.cfg["schedule"].get("planner_batch", 0)) or min(20, max(6, 2 * self.n_workers))

        def run():
            try:
                ids = self.planner.refill(n)
                self._log(f"planner round {self.planner.rounds}: queued {len(ids)} experiments")
            except Exception as exc:
                self.lab.db.event("planner_crash", f"{type(exc).__name__}: {exc}", level="error")
                self._log(f"planner error: {exc}")

        self._planner_thread = threading.Thread(target=run, name="planner", daemon=True)
        self._planner_thread.start()

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
        self.lab.db.execute("UPDATE runs SET started_at=?, deadline=?, workers=? WHERE run_id=?",
                            (self.started, self.deadline, self.n_workers, self.lab.run_id))
        if self.lab.git_head_dirty():
            self._log("warning: repository has uncommitted changes; worktrees use the committed HEAD "
                      f"{self.lab.base_commit[:10]}")
        self._log(f"run {self.lab.run_id}: {self.n_workers} workers, {self.n_cpu} CPU slots, "
                  f"{self.seconds / 60:.1f} min, dataset {self.lab.dataset} ({self.lab.split_id})")
        self.lab.record_analytic_baselines()
        self.lab.queue_model_baselines()
        for i in range(self.n_workers):
            self._start_worker(i)
        interval = float(self.cfg["run"]["status_interval_s"])
        next_status = 0.0
        try:
            while time.time() < self.deadline:
                if self._baselines_done():
                    self._maybe_plan()
                self._supervise()
                if time.time() >= next_status:
                    self._log(self.status_line())
                    next_status = time.time() + interval
                if self._exhausted():
                    self._log("nothing left to do (planner exhausted and queue empty); stopping early")
                    break
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._log("interrupted; shutting down")
        return self.shutdown()

    def _baselines_done(self) -> bool:
        return not self.lab.db.query("SELECT 1 FROM experiments WHERE kind='baseline' AND status IN "
                                     "('queued','claimed','running')")

    def _exhausted(self) -> bool:
        if self.planner is not None and self.planner.rounds < self.max_planner_calls \
                and self.planner.empty_rounds < 3:
            return False
        if self._planner_thread and self._planner_thread.is_alive():
            return False
        c = self.lab.db.count_by_status()
        return c.get("queued", 0) == 0 and not any(w.current for w in self.workers)

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
        summary = finalize(self.lab, wall_s=time.time() - self.started, workers=self.n_workers)
        self._log(f"summary written to {self.lab.run_dir / 'summary.md'}")
        return summary
