"""Research worker: an executor slot that takes any experiment from the queue.

LLM time and CPU time are separated: the worker holds an LLM only while it is
writing or fixing code; the CPU experiment runs in a limited subprocess while
the worker merely waits on it (no tokens are spent), and the number of
simultaneous CPU experiments is capped independently of the worker count.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np

from .benchmark import PRIMARY_HIGHER_IS_BETTER
from .guard import CodeViolation, check_diff, check_plugin_source
from .isolation import sha256_text
from .lab import Lab
from .llm import BudgetExceeded, TokenLimitExceeded
from .providers.base import AgentProvider, ProviderError, extract_code
from .spec import PLUGIN_DIR, ExperimentSpec


class ExperimentFailure(Exception):
    def __init__(self, stage: str, reason: str, retryable: bool = False):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.retryable = retryable  # an infrastructure error that may pass on a later attempt


def prune_predictions(path: Path, keep_index: int) -> None:
    """Keep only the chosen alpha's predictions (the others were scored and are never read again).
    The experiment is reproducible from its spec; this cuts artifact disk use by the size of the alpha grid."""
    z = np.load(path, allow_pickle=False)
    if z["delta"].shape[0] <= 1:
        return
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, delta=z["delta"][keep_index:keep_index + 1], perts=z["perts"],
                        alphas=z["alphas"][keep_index:keep_index + 1])
    os.replace(tmp, path)


class Worker:
    def __init__(self, lab: Lab, worker_id: str, provider: AgentProvider | None,
                 escalation: AgentProvider | None, cpu_slots: threading.Semaphore):
        self.lab = lab
        self.db = lab.db
        self.worker_id = worker_id
        self.provider = provider
        self.escalation = escalation
        self.cpu_slots = cpu_slots
        self.wcfg = lab.cfg["worker"]
        self.current: str | None = None
        self.completed = 0

    # ------------------------------------------------------------------ loop
    def loop(self, idle_sleep: float = 0.5) -> None:
        while not self.lab.stop_event.is_set():
            rec = self.db.claim_next(self.worker_id)
            if rec is None:
                time.sleep(idle_sleep)
                continue
            self.process(rec)

    def process(self, rec: dict) -> str:
        """Run one experiment end to end. Never raises."""
        eid = rec["experiment_id"]
        self.current = eid
        spec = ExperimentSpec.from_record(rec)
        art = self.lab.artifacts / eid
        art.mkdir(parents=True, exist_ok=True)
        (art / "spec.json").write_text(json.dumps(spec.to_dict(), indent=1))
        wt = None
        t0 = time.monotonic()
        status = "failed"
        try:
            wt = self.lab.worktrees.create(eid)
            installed = self.lab.worktrees.install_features(
                wt, self.lab.store_files([f for f in spec.feature_set if f != (spec.proposed_feature or {}).get("name")]))
            if spec.kind == "new_feature":
                self._set(eid, status="implementing")
                self._implement(spec, wt, art)
            else:
                self._set(eid, provider="python", model="deterministic")
            files = check_diff(wt, self.lab.base_commit, spec.allowed_files, list(installed))
            for rel, digest in installed.items():
                if sha256_text((wt / rel).read_text()) != digest:
                    raise ExperimentFailure("guard", f"installed feature file {rel} was modified")
            commit = self.lab.worktrees.commit(wt, eid, f"{eid}: {spec.hypothesis[:60]}")
            self._set(eid, files_changed_json=files, code_commit=commit, status="running",
                      code_hash=sha256_text("".join(sorted(installed.values())) + "".join(
                          sha256_text((wt / f).read_text()) for f in files)))
            result, proc = self._run_experiment(spec, wt, art)
            ev = self.lab.evaluate_artifact(art / "predictions.npz")
            (art / "metrics.json").write_text(json.dumps(ev, indent=1))
            if not self.lab.cfg["experiment"].get("keep_all_alphas", False):
                prune_predictions(art / "predictions.npz", ev["alpha_index"])
                if (art / "cv.npz").exists():
                    prune_predictions(art / "cv.npz", ev["alpha_index"])
            self.lab.trim_feature_cache()
            parent = self.db.get_experiment(spec.parent_experiment_id) if spec.parent_experiment_id else None
            pscore = parent.get("primary_score") if parent else None
            score = ev["metrics"]["primary"]
            delta = None if pscore is None else (score - pscore) * (1 if PRIMARY_HIGHER_IS_BETTER else -1)
            self._set(eid, status="completed", val_metrics_json={**ev["metrics"], "alpha_scores": ev["alpha_scores"]},
                      diagnostics_json={**ev["diagnostics"], "coefficients": self._coefs(result, ev["best_alpha"])},
                      primary_score=score, parent_score=pscore, delta_from_parent=delta,
                      best_alpha=ev["best_alpha"], timing_json=result["timing"],
                      model_size_bytes=result["model_size_bytes"], cpu_s=proc.cpu_s, peak_rss_mb=proc.peak_rss_mb)
            if spec.kind == "new_feature":
                name = spec.proposed_feature["name"]
                self.lab.add_to_store(name, wt / spec.allowed_files[0], eid, result["feature_metadata"][name],
                                      result["timing"]["per_feature_cpu_s"].get(name, 0.0))
            status = "completed"
            self.completed += 1
        except ExperimentFailure as exc:
            status = "killed" if exc.stage == "killed" else "failed"
            max_attempts = int(self.lab.cfg["experiment"].get("max_attempts", 2))
            if exc.retryable and (rec.get("attempts") or 1) < max_attempts and not self.lab.stop_event.is_set():
                status = "queued"  # a transient API error (429/5xx/network): another attempt, not a verdict
                self._set(eid, status=status, worker_id=None, failure_stage=exc.stage,
                          failure_reason=f"attempt {rec.get('attempts') or 1} requeued: {exc.reason[:1800]}")
                self.db.event("experiment_requeued", f"{exc.stage}: {exc.reason[:300]}", eid, "info")
            else:
                self._set(eid, status=status, failure_stage=exc.stage, failure_reason=exc.reason[:2000])
                self.db.event("experiment_failed", f"{exc.stage}: {exc.reason[:300]}", eid, "warning")
        except (BudgetExceeded, TokenLimitExceeded) as exc:
            # a spent budget is a run-level condition, not a result about this hypothesis
            status = "cancelled" if isinstance(exc, BudgetExceeded) else "failed"
            self._set(eid, status=status, failure_stage="budget", failure_reason=str(exc))
        except CodeViolation as exc:
            self._set(eid, status="rejected", failure_stage="guard", failure_reason=str(exc)[:2000])
            self.db.event("guard_violation", str(exc)[:300], eid, "warning")
        except Exception as exc:  # worker crash: record it, keep the worker alive
            self._set(eid, status="failed", failure_stage="worker_crash",
                      failure_reason=f"{type(exc).__name__}: {exc}"[:2000])
            (art / "worker_crash.txt").write_text(traceback.format_exc())
            self.db.event("worker_crash", f"{type(exc).__name__}: {exc}"[:300], eid, "error")
        finally:
            self._set(eid, finished_at=time.time(), wall_s=time.monotonic() - t0, artifact_dir=str(art))
            if wt is not None:
                if spec.kind == "new_feature":
                    src = wt / spec.allowed_files[0]
                    if src.exists():
                        shutil.copy2(src, art / src.name)
                try:
                    self.lab.worktrees.remove(wt)
                except Exception:
                    pass
            self.current = None
        return status

    # -------------------------------------------------------------- internals
    def _set(self, eid: str, **fields) -> None:
        self.db.update_experiment(eid, heartbeat=time.time(), **fields)

    @staticmethod
    def _coefs(result: dict, alpha: float) -> dict:
        for c in result["coefficients"]:
            if c["alpha"] == alpha:
                return {k: round(v, 5) for k, v in c["coef"].items()}
        return {}

    def _task(self, spec: ExperimentSpec) -> dict:
        existing = []
        for f in spec.feature_set:
            if f == spec.proposed_feature["name"]:
                continue
            meta = self.db.feature(f)
            existing.append(f"{f} ({(meta or {}).get('description', '')[:80]})")
        return {"experiment_id": spec.experiment_id, "hypothesis": spec.hypothesis,
                "rationale": spec.scientific_rationale, "new_feature": spec.proposed_feature,
                "data_summary": self.lab.data_summary(), "knowledge_summary": self.lab.knowledge_summary(),
                "existing_features": "; ".join(existing)}

    def _llm(self, provider: AgentProvider, op: str, spec: ExperimentSpec, **kw):
        if self.lab.stop_event.is_set():
            raise ExperimentFailure("killed", "deadline reached before LLM call")
        est = sum(len(str(v)) for v in kw.values()) // 3 + 2500
        try:
            resp = self.lab.gateway.call(provider, op, role="worker", max_tokens=int(self.wcfg["max_output_tokens"]),
                                         est_input_tokens=est, experiment_id=spec.experiment_id,
                                         worker_id=self.worker_id, **kw)
        except ProviderError as exc:
            raise ExperimentFailure("llm_api", str(exc), retryable=exc.retryable) from None
        self._set(spec.experiment_id, provider=provider.name, model=resp.model or provider.model)
        return resp

    def _implement(self, spec: ExperimentSpec, wt: Path, art: Path) -> None:
        if self.provider is None:
            raise ExperimentFailure("implement", "no worker LLM provider configured")
        task = self._task(spec)
        name = spec.proposed_feature["name"]
        target = wt / PLUGIN_DIR / f"{name}.py"
        attempts: list[tuple[AgentProvider, str]] = [(self.provider, "implement")]
        attempts += [(self.provider, "diagnose")] * int(self.wcfg.get("llm_retries", 1))
        if self.escalation is not None:
            attempts.append((self.escalation, "diagnose"))
        code, error, violation = "", "", None
        for i, (prov, op) in enumerate(attempts):
            if error.startswith("TRUNCATED") and prov is not self.escalation:
                continue  # the same provider and limit would be truncated again
            if prov is self.escalation:
                self._set(spec.experiment_id, escalated=1)
                self.db.event("escalation", f"escalating to {prov.name}/{prov.model}", spec.experiment_id)
            kw = {"task": task} if op == "implement" else {"task": task, "code": code, "error": error}
            resp = self._llm(prov, op, spec, **kw)
            if resp.truncated_empty:  # a retry with the same limit ends the same way: stop paying for it
                error = (f"TRUNCATED {prov.name}/{resp.model or prov.model} reached the output limit "
                         f"({self.wcfg['max_output_tokens']} tokens, {resp.reasoning_tokens} of them reasoning) "
                         "before writing any code; raise worker.max_output_tokens or set worker.thinking = "
                         "\"disabled\"")
                self.db.event("llm_truncated", error[10:], spec.experiment_id, "warning")
                continue
            code = extract_code(resp.text)
            (art / f"attempt_{i + 1}_{prov.name}.py").write_text(code)
            try:
                check_plugin_source(code, name)
            except CodeViolation as exc:
                error = f"static check failed: {exc}"
                violation = exc
                continue
            violation = None
            target.write_text(code)
            self._set(spec.experiment_id, status="testing")
            smoke = self._smoke(name, wt, art, i + 1)
            if smoke is None:
                return
            error = smoke
        if violation is not None and "not allowed" in str(violation):
            raise violation  # forbidden behaviour persisted after the fix attempts: reject
        if error.startswith("TRUNCATED"):
            raise ExperimentFailure("llm_truncated", error[10:])
        raise ExperimentFailure("test", f"feature failed after {len(attempts)} attempts: {error[-800:]}")

    def _smoke(self, name: str, wt: Path, art: Path, attempt: int) -> str | None:
        out = art / f"smoke_{attempt}"
        proc = self.lab.executor.run(
            ["smoke", "--feature", name, "--public", str(self.lab.public_dir), "--plugins", str(wt / PLUGIN_DIR),
             "--out", str(out)],
            cwd=wt, log_dir=out, timeout_s=min(90.0, self.lab.limits["timeout_s"]),
            ram_mb=self.lab.limits["ram_limit_mb"], cpu_s=self.lab.limits["cpu_limit_s"],
            env={"PYTHONPATH": str(wt)}, kill_event=self.lab.kill_event, name="smoke")
        if proc.killed_reason and self.lab.kill_event.is_set():
            raise ExperimentFailure("killed", proc.killed_reason)
        if proc.returncode == 0:
            return None
        if (out / "smoke.json").exists():
            r = json.loads((out / "smoke.json").read_text())
            msg = "; ".join(r["problems"])
            if any("leakage" in p for p in r["problems"]):
                msg = "LEAKAGE " + msg
            return msg
        if (out / "error.json").exists():
            e = json.loads((out / "error.json").read_text())
            return f"{e['error_type']}: {e['error']}\n{e['traceback'][-1200:]}"
        return proc.killed_reason or f"smoke test exited {proc.returncode}: {proc.stderr_tail[-800:]}"

    def _run_experiment(self, spec: ExperimentSpec, wt: Path, art: Path):
        (art / "run_spec.json").write_text(json.dumps(spec.run_spec(), indent=1))
        while not self.cpu_slots.acquire(timeout=0.5):
            if self.lab.kill_event.is_set():
                raise ExperimentFailure("killed", "deadline reached while waiting for a CPU slot")
        try:
            proc = self.lab.executor.run(
                ["run", "--spec", str(art / "run_spec.json"), "--public", str(self.lab.public_dir),
                 "--plugins", str(wt / PLUGIN_DIR), "--out", str(art)],
                cwd=wt, log_dir=art, timeout_s=spec.timeout_s, ram_mb=spec.ram_limit_mb, cpu_s=spec.cpu_limit_s,
                env={"PYTHONPATH": str(wt)}, kill_event=self.lab.kill_event, name="experiment")
        finally:
            self.cpu_slots.release()
        self._set(spec.experiment_id, cpu_s=proc.cpu_s, peak_rss_mb=proc.peak_rss_mb)
        if proc.killed_reason:
            stage = "killed" if self.lab.kill_event.is_set() and not proc.timed_out else (
                "timeout" if proc.timed_out else "resources")
            raise ExperimentFailure(stage, proc.killed_reason)
        if proc.returncode != 0:
            if (art / "error.json").exists():
                e = json.loads((art / "error.json").read_text())
                raise ExperimentFailure("experiment", f"{e['error_type']}: {e['error']}")
            if proc.returncode in (-9, -24, 137, 152):
                raise ExperimentFailure("resources", f"killed by resource limit (exit {proc.returncode})")
            raise ExperimentFailure("experiment", f"exit {proc.returncode}: {proc.stderr_tail[-600:]}")
        return json.loads((art / "result.json").read_text()), proc
