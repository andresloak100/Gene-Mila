"""The laboratory: shared run context used by the controller, workers and planner."""

from __future__ import annotations

import json
import re
import shutil
import threading
import time
from pathlib import Path

import numpy as np

from . import REPO_ROOT
from .benchmark import PRIMARY_HIGHER_IS_BETTER, PRIMARY_METRIC
from .benchmark import comparable, reference
from .benchmark.evaluator import evaluate
from .benchmark.oracle import QueryOracle
from .data.bundle import LabelSet, export_public, verify_bundle
from .db import Database
from .features.registry import BUILTIN_FEATURES
from .isolation import WorktreeManager, git, sha256_text
from .llm import LLMGateway, SpendLedger
from .spec import PLUGIN_DIR, ExperimentSpec, GuardrailViolation, config_hash, validate_spec


class Lab:
    def __init__(self, cfg: dict, run_dir: Path, data_dir: Path, repo: Path = REPO_ROOT, run_id: str | None = None,
                 base_commit: str | None = None, reopen: bool = False):
        self.cfg = cfg
        self.run_dir = Path(run_dir).resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or self.run_dir.name
        self.repo = Path(repo).resolve()
        self.data_dir = Path(data_dir).resolve()
        problems = verify_bundle(self.data_dir)
        if problems:
            raise RuntimeError(f"dataset integrity check failed: {problems}")
        self.manifest = json.loads((self.data_dir / "manifest.json").read_text())
        self.split_id = self.manifest["split_id"]
        self.dataset = self.manifest["name"]
        existing = self.run_dir / "public_data"
        # re-opening a live run (status, reproduce) must not rewrite files experiments are reading
        self.public_dir = existing if reopen and (existing / "public.npz").exists() else \
            export_public(self.data_dir, existing)
        self.db = Database(self.run_dir / "lab.db")
        self.artifacts = self.run_dir / "artifacts"
        self.store = self.run_dir / "feature_store"
        self.artifacts.mkdir(exist_ok=True)
        self.store.mkdir(exist_ok=True)
        self.worktrees = WorktreeManager(self.repo, self.run_dir / "worktrees", self.run_id, base_commit)
        self.base_commit = self.worktrees.base_commit
        ledger_path = Path(cfg["budget"].get("ledger", "runs/spend_ledger.sqlite"))
        if not ledger_path.is_absolute():
            ledger_path = self.repo / ledger_path
        self.gateway = LLMGateway(self.db, cfg, self.run_id, SpendLedger(ledger_path))
        # the query-only cap is per run: queries already recorded in lab.db count, whichever process asks
        self.oracle = QueryOracle(self.data_dir, max_queries=int(cfg.get("final", {}).get("max_queries", 5)),
                                  used=lambda: self.db.query("SELECT COUNT(*) AS n FROM events WHERE kind='query_only'")[0]["n"])
        self.stop_event = threading.Event()   # no new experiments / LLM calls
        self.kill_event = threading.Event()   # terminate running subprocesses
        self.gateway.stop_event = self.stop_event  # waits inside the gateway end at the deadline
        self._closed = False
        self._val1 = LabelSet.load(self.data_dir / "private" / "val1.npz")
        self._val1_ref = reference.load(self.data_dir, "val1")  # ground-truth DE genes for comparable metrics
        z = np.load(self.public_dir / "public.npz", allow_pickle=False)
        self.control_mean = z["control_cells"].astype(np.float64).mean(axis=0)
        self.genes = [str(g) for g in z["genes"]]
        self._train = LabelSet([str(p) for p in z["train_perts"]], z["train_means"].astype(np.float64))
        # model selection: K-fold out-of-fold predictions of the training perturbations join the visible
        # validation set, so the selection signal rests on every visible perturbation (0 = validation set only)
        self.cv_folds = int(cfg["experiment"].get("cv_folds", 0) or 0)
        self.cv_seed = int(cfg["run"].get("seed", 0) or 0)
        self.limits = {k: float(cfg["experiment"][k]) for k in ("cpu_limit_s", "ram_limit_mb", "timeout_s")}
        self._register_builtins()
        self._executor = None
        self._exec_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        if not self.db.query("SELECT 1 FROM runs WHERE run_id=?", (self.run_id,)):
            self.db.execute("INSERT INTO runs (run_id, started_at, dataset, split_id, base_commit, config_json, "
                            "workers) VALUES (?,?,?,?,?,?,?)",
                            (self.run_id, time.time(), self.dataset, self.split_id, self.base_commit,
                             json.dumps(cfg), int(cfg["run"]["workers"])))

    def trim_feature_cache(self) -> None:
        """Evict the oldest cached feature blocks once the cache exceeds experiment.feature_cache_max_mb.
        Readers tolerate a block vanishing (they recompute it), so eviction needs no coordination."""
        cap = float(self.cfg["experiment"].get("feature_cache_max_mb", 4096)) * 1e6
        cache = self.run_dir / "cache" / "features"
        if cap <= 0 or not cache.exists():
            return
        with self._cache_lock:
            files = []
            for p in cache.glob("*.npy"):
                try:
                    st = p.stat()
                except OSError:
                    continue
                files.append((st.st_mtime, st.st_size, p))
            total = sum(f[1] for f in files)
            if total <= cap:
                return
            for mtime, size, p in sorted(files):
                try:
                    p.unlink()
                except OSError:
                    continue
                total -= size
                if total <= cap * 0.8:
                    break
            self.db.event("feature_cache_trimmed", f"feature cache over {cap / 1e6:.0f} MB; evicted oldest blocks")

    # ----------------------------------------------------------------- executor
    @property
    def executor(self):
        """Runs experiment and smoke-test processes (warm fork server by default)."""
        from .sandbox import Executor
        with self._exec_lock:
            if self._closed:
                from .worker import ExperimentFailure
                raise ExperimentFailure("killed", "the lab is shutting down")
            if self._executor is None:
                ecfg = self.cfg["experiment"]
                mode = ecfg.get("executor", "forkserver")
                cache = self.run_dir / "cache" if ecfg.get("feature_cache", True) else None
                server_cwd = self.worktrees.create("_server") if mode == "forkserver" else None
                self._executor = Executor(mode, server_cwd, self.public_dir, cache,
                                          on_fallback=lambda msg: self.db.event("executor_fallback", msg, level="warning"))
            return self._executor

    def close(self) -> None:
        with self._exec_lock:
            self._closed = True
        if self._executor is not None:
            self._executor.close()
            if self._executor._args[0] is not None:
                try:
                    self.worktrees.remove(Path(self._executor._args[0]))
                except Exception:
                    pass
            self._executor = None

    # ----------------------------------------------------------------- features
    def _register_builtins(self) -> None:
        from .features.registry import get
        for name in BUILTIN_FEATURES:
            if not self.db.feature(name):
                meta = get(name).metadata()
                self.db.upsert_feature({**meta, "builtin": 1, "implementation_path": "genemila/features/builtin.py",
                                        "code_hash": "builtin", "creator_experiment": "builtin"})

    def known_features(self) -> set[str]:
        return {f["name"] for f in self.db.features()}

    def feature_code_hashes(self) -> dict[str, str]:
        return {f["name"]: f["code_hash"] for f in self.db.features()}

    def store_files(self, names: list[str]) -> dict[str, Path]:
        out = {}
        for n in names:
            if n in BUILTIN_FEATURES:
                continue
            p = self.store / f"{n}.py"
            if p.exists():
                out[n] = p
        return out

    def add_to_store(self, name: str, source: Path, experiment_id: str, metadata: dict, compute_cpu_s: float) -> None:
        dst = self.store / f"{name}.py"
        shutil.copy2(source, dst)
        self.db.upsert_feature({**metadata, "implementation_path": str(dst.relative_to(self.run_dir)),
                                "code_hash": sha256_text(dst.read_text()), "creator_experiment": experiment_id,
                                "compute_cpu_s": compute_cpu_s})

    # -------------------------------------------------------------------- queue
    def queue(self, spec: ExperimentSpec) -> tuple[str, str]:
        """Validate and enqueue. Returns (experiment_id, status). Rejections are recorded, not dropped."""
        if spec.experiment_id is None:
            spec.experiment_id = self.db.next_experiment_id()
        num = int(spec.experiment_id.split("_")[1])
        if spec.kind == "new_feature" and spec.proposed_feature:
            base = re.sub(r"[^a-z0-9_]", "_", spec.proposed_feature.get("name", "feature").lower()).strip("_")[:40]
            base = base if base and base[0].isalpha() else f"f_{base}"
            name = f"{base}_e{num}"
            old = spec.proposed_feature.get("name")
            spec.proposed_feature = {**spec.proposed_feature, "name": name}
            spec.feature_set = [name if f == old else f for f in spec.feature_set]
            if name not in spec.feature_set:
                spec.feature_set.append(name)
            spec.allowed_files = [f"{PLUGIN_DIR}/{name}.py"]
        spec.cpu_limit_s = min(spec.cpu_limit_s, self.limits["cpu_limit_s"])
        spec.ram_limit_mb = min(spec.ram_limit_mb, self.limits["ram_limit_mb"])
        spec.timeout_s = min(spec.timeout_s, self.limits["timeout_s"])
        parent = self.db.get_experiment(spec.parent_experiment_id) if spec.parent_experiment_id else None
        record = spec.to_record(self.dataset, self.split_id, self.run_id)
        try:
            flags = validate_spec(spec, self.known_features(), self.limits, parent)
        except GuardrailViolation as exc:
            record.update(status="rejected", failure_stage="guardrail", failure_reason=str(exc),
                          finished_at=time.time())
            self.db.insert_experiment(record)
            self.db.event("rejected", str(exc), spec.experiment_id, "warning")
            return spec.experiment_id, "rejected"
        record["flags_json"] = flags
        if self.cv_folds > 1:  # set by the lab after validation (agents cannot choose it): same folds for all
            spec.hyperparameters = {**spec.hyperparameters, "cv_folds": self.cv_folds, "cv_seed": self.cv_seed}
            record["hyperparameters_json"] = spec.hyperparameters
        if spec.kind != "new_feature":
            ch = config_hash(spec, self.feature_code_hashes(), self.split_id)
            record["config_hash"] = ch
            dup = self.db.find_by_config_hash(ch)
            if dup:
                record.update(status="duplicate", duplicate_of=dup["experiment_id"], finished_at=time.time(),
                              failure_reason=f"identical configuration to {dup['experiment_id']}")
                self.db.insert_experiment(record)
                return spec.experiment_id, "duplicate"
        self.db.insert_experiment(record)
        return spec.experiment_id, "queued"

    # --------------------------------------------------------------- evaluation
    def evaluate_artifact(self, pred_path: Path) -> dict:
        """Score every alpha on the visible perturbations; choose the best. Trusted controller code.

        Visible = the visible validation set plus, when the experiment was cross-validated (cv.npz next to
        the predictions), the out-of-fold predictions of the training perturbations. The primary score is
        the mean over all of them: selection on 60-70 perturbations instead of 15-20 is far less noisy.
        `pearson_delta` stays the validation-set value and `pearson_delta_cv` the out-of-fold value."""
        z = np.load(pred_path, allow_pickle=False)
        perts = [str(p) for p in z["perts"]]
        idx = {p: i for i, p in enumerate(perts)}
        missing = [p for p in self._val1.perts if p not in idx]
        if missing:
            raise ValueError(f"predictions missing validation perturbations {missing[:3]}")
        rows = [idx[p] for p in self._val1.perts]
        cv = None
        cv_path = pred_path.with_name("cv.npz")
        if self.cv_folds > 1:
            if not cv_path.exists():
                raise ValueError("experiment produced no cross-validation predictions (cv.npz)")
            c = np.load(cv_path, allow_pickle=False)
            if [str(p) for p in c["perts"]] != self._train.perts or \
                    list(map(float, c["alphas"])) != list(map(float, z["alphas"])):
                raise ValueError("cv.npz does not match predictions.npz (perturbations or alphas)")
            cv = c["delta"]
        best, scores = None, []
        for k, alpha in enumerate(z["alphas"]):
            pred = z["delta"][k][rows].astype(np.float64) + self.control_mean
            res = evaluate(pred, self._val1.means, self.control_mean, self._val1.perts)
            if cv is not None:
                cv_res = evaluate(cv[k].astype(np.float64) + self.control_mean, self._train.means,
                                  self.control_mean, self._train.perts)
                self._combine_visible(res["metrics"], cv_res["metrics"])
            scores.append({"alpha": float(alpha), PRIMARY_METRIC: res["metrics"][PRIMARY_METRIC],
                           "primary": res["metrics"]["primary"]})
            better = best is None or (res["metrics"]["primary"] > best[1]["metrics"]["primary"]
                                      if PRIMARY_HIGHER_IS_BETTER else
                                      res["metrics"]["primary"] < best[1]["metrics"]["primary"])
            if better:
                best = (k, res)
        k, res = best
        pred = z["delta"][k][rows].astype(np.float64) + self.control_mean
        res["metrics"].update(self.comparable_val1(pred))
        return {"alpha_index": k, "best_alpha": float(z["alphas"][k]), "metrics": res["metrics"],
                "diagnostics": res["diagnostics"], "alpha_scores": scores}

    def _combine_visible(self, metrics: dict, cv_metrics: dict) -> None:
        """primary = mean of the per-perturbation primary metric over validation + out-of-fold training
        perturbations (each perturbation weighs the same)."""
        n1, nt = len(self._val1.perts), len(self._train.perts)
        metrics[f"{PRIMARY_METRIC}_cv"] = cv_metrics[PRIMARY_METRIC]
        metrics["primary"] = (n1 * metrics[PRIMARY_METRIC] + nt * cv_metrics[PRIMARY_METRIC]) / (n1 + nt)
        metrics["n_visible"] = n1 + nt
        metrics["cv_folds"] = self.cv_folds

    def _cv_baseline(self, which: str) -> np.ndarray:
        """Out-of-fold analytic baseline for the training perturbations, on the run's folds."""
        from .pipeline import cv_folds_of
        pred = np.tile(self.control_mean, (len(self._train.perts), 1))
        if which == "baseline_mean_response":
            pos = {p: i for i, p in enumerate(self._train.perts)}
            delta = self._train.means - self.control_mean
            for fold in cv_folds_of(self._train.perts, self.cv_folds, self.cv_seed):
                rows = [pos[p] for p in fold]
                rest = np.setdiff1d(np.arange(len(pos)), rows)
                pred[rows] += delta[rest].mean(axis=0)
        return pred

    def comparable_val1(self, pred: np.ndarray) -> dict:
        """CellForge and VCWorld metrics on visible validation ({} when the bundle has no held-out cells)."""
        return comparable.score(pred, self._val1.means, self._val1.perts, self._val1_ref, self.control_mean)

    def _predict(self, rec: dict, perts: list[str]) -> tuple[np.ndarray, list[str]]:
        """Absolute predicted expression of an experiment (or analytic baseline) for the given perturbations."""
        if rec["kind"] == "baseline" and not rec.get("artifact_dir"):
            return self._analytic_baseline(rec["hypothesis_group"], perts), list(perts)
        z = np.load(Path(rec["artifact_dir"]) / "predictions.npz", allow_pickle=False)
        have = [str(p) for p in z["perts"]]
        alphas = list(map(float, z["alphas"]))
        k = alphas.index(rec["best_alpha"]) if rec["best_alpha"] in alphas else 0
        pred = z["delta"][k].astype(np.float64) + self.control_mean
        keep = [i for i, p in enumerate(have) if p in set(perts)]
        return pred[keep], [have[i] for i in keep]

    @property
    def celleval_profile(self) -> str | None:
        """cell-eval profile for final scoring, or None when disabled, not installed, or no held-out cells."""
        f = self.cfg.get("final", {})
        if not f.get("celleval", True) or not (self.data_dir / "private" / "val1_cells.npz").exists():
            return None
        from .benchmark import celleval
        return f.get("celleval_profile", "full") if celleval.available() else None

    def _celleval_path(self, experiment_id: str, part: str) -> Path:
        d = self.run_dir / "celleval"
        d.mkdir(exist_ok=True)
        return d / f"{experiment_id}_{part}.json"

    def celleval_val1(self, experiment_id: str) -> dict | None:
        """cell-eval metrics on the visible validation set (cached on disk). None when unavailable."""
        profile = self.celleval_profile
        rec = self.db.get_experiment(experiment_id)
        if not profile or not rec:
            return None
        path = self._celleval_path(experiment_id, "val1")
        if path.exists():
            return json.loads(path.read_text())
        from .benchmark import celleval
        pred, perts = self._predict(rec, self._val1.perts)
        X, labels = celleval.load_real_cells(self.data_dir, "val1")
        out = celleval.score(dict(zip(perts, pred - self.control_mean)), X, labels, self.genes, profile=profile)
        path.write_text(json.dumps(out, indent=1))
        return out

    def query_only(self, experiment_id: str) -> dict | None:
        rec = self.db.get_experiment(experiment_id)
        if not rec:
            return None
        pred, perts = self._predict(rec, self.oracle.perts)
        out = self.oracle.query(experiment_id, pred, perts, self.control_mean,
                                celleval_profile=self.celleval_profile, genes=self.genes)
        self.db.update_experiment(experiment_id, query_metrics_json=out["metrics"])
        if "cell_eval" in out:
            self._celleval_path(experiment_id, "val2").write_text(json.dumps(out["cell_eval"], indent=1))
        elif "cell_eval_error" in out:
            self.db.event("celleval_error", out["cell_eval_error"], experiment_id, "warning")
        self.db.event("query_only", f"query-only evaluation of {experiment_id}", experiment_id)
        return out

    def celleval_val2(self, experiment_id: str) -> dict | None:
        path = self._celleval_path(experiment_id, "val2")
        return json.loads(path.read_text()) if path.exists() else None

    # ---------------------------------------------------------------- baselines
    def _analytic_baseline(self, which: str, perts: list[str]) -> np.ndarray:
        z = np.load(self.public_dir / "public.npz", allow_pickle=False)
        if which == "baseline_unchanged":
            delta = np.zeros_like(self.control_mean)
        else:  # baseline_mean_response
            delta = z["train_means"].astype(np.float64).mean(axis=0) - self.control_mean
        return np.tile(self.control_mean + delta, (len(perts), 1))

    def record_analytic_baselines(self) -> None:
        for key, hyp in [("baseline_unchanged", "Perturbations do not change expression (predict control mean)."),
                         ("baseline_mean_response", "Every perturbation produces the average training response.")]:
            if self.db.query("SELECT 1 FROM experiments WHERE hypothesis_group=?", (key,)):
                continue
            t0 = time.process_time()
            pred = self._analytic_baseline(key, self._val1.perts)
            res = evaluate(pred, self._val1.means, self.control_mean, self._val1.perts)
            if self.cv_folds > 1:
                cv_res = evaluate(self._cv_baseline(key), self._train.means, self.control_mean, self._train.perts)
                self._combine_visible(res["metrics"], cv_res["metrics"])
            res["metrics"].update(self.comparable_val1(pred))
            eid = self.db.next_experiment_id()
            self.db.insert_experiment({
                "experiment_id": eid, "run_id": self.run_id, "status": "completed", "kind": "baseline",
                "category": "baseline", "hypothesis": hyp, "rationale": "Reference point required before any "
                "autonomous experimentation.", "hypothesis_group": key, "feature_set_json": [],
                "model_type": "none", "dataset": self.dataset, "split_id": self.split_id, "proposer": "python",
                "provider": "python", "model": "analytic", "val_metrics_json": res["metrics"],
                "diagnostics_json": res["diagnostics"], "primary_score": res["metrics"]["primary"],
                "cpu_s": time.process_time() - t0, "wall_s": time.process_time() - t0, "finished_at": time.time(),
                "code_commit": self.base_commit, "seed": 0})

    def queue_model_baselines(self) -> None:
        if self.db.query("SELECT 1 FROM experiments WHERE kind='baseline' AND model_type!='none'"):
            return
        grid = list(self.cfg["experiment"]["default_alpha_grid"])
        base = ["control_mean", "mean_response", "is_target"]
        for model, hp in [("ols", {}), ("ridge", {"alpha_grid": grid}),
                          ("lasso", {"alpha_grid": [a / 1000 for a in grid]})]:
            self.queue(ExperimentSpec(
                hypothesis=f"{model.upper()} on baseline features (control mean, mean response, target indicator).",
                scientific_rationale="Simple linear reference model; all discoveries are measured against it.",
                kind="baseline", category="baseline", feature_set=list(base), model_type=model,
                hyperparameters=hp, proposer="python", priority=100.0,
                hypothesis_group=f"baseline_{model}"))

    # ------------------------------------------------------------------ helpers
    def best(self) -> dict | None:
        return self.db.best()

    def best_baseline(self) -> dict | None:
        rows = self.db.query("SELECT * FROM experiments WHERE kind='baseline' AND status='completed' "
                             "ORDER BY primary_score DESC LIMIT 1")
        return rows[0] if rows else None

    def data_summary(self) -> str:
        m = self.manifest
        targets = json.loads((self.public_dir / "knowledge" / "targets.json").read_text())
        sizes = [len(v) for v in targets.values()] or [1]
        multi = sum(1 for n in sizes if n > 1)
        kind = "single-gene targets" if not multi else (
            f"targets of 1 to {max(sizes)} genes; {multi} of {len(sizes)} perturbations hit more than one gene")
        return (f"{m['name']}: {m['n_genes']} genes, {m['n_control_cells']} control cells, "
                f"{m['n_train']} training perturbations ({kind}); predict unseen perturbations.")

    def knowledge_summary(self) -> str:
        parts = []
        for p in sorted((self.public_dir / "knowledge").glob("*.json")):
            obj = json.loads(p.read_text())
            if isinstance(obj, dict):
                k = next(iter(obj), None)
                parts.append(f"{p.stem}: dict of {len(obj)} entries, e.g. {k!r}: {str(obj[k])[:60]}")
            else:
                parts.append(f"{p.stem}: list of {len(obj)}, e.g. {str(obj[0])[:60] if obj else ''}")
        return "; ".join(parts) or "none"

    def git_head_dirty(self) -> bool:
        return bool(git(self.repo, "status", "--porcelain", "--untracked-files=no"))


def open_run(run_dir: str | Path) -> Lab:
    """Re-open an existing run (for status, reproduction and summaries)."""
    from .db import Database
    run_dir = Path(run_dir).resolve()
    db = Database(run_dir / "lab.db")
    row = db.query("SELECT * FROM runs LIMIT 1")
    if not row:
        raise FileNotFoundError(f"no run recorded in {run_dir}")
    cfg = json.loads(row[0]["config_json"])
    return Lab(cfg, run_dir, Path(cfg["run"]["data_dir"]), run_id=row[0]["run_id"],
               base_commit=row[0]["base_commit"], reopen=True)


def latest_run(root: str | Path = REPO_ROOT / "runs") -> Path:
    runs = sorted((p for p in Path(root).glob("*") if (p / "lab.db").exists()), key=lambda p: p.stat().st_mtime)
    if not runs:
        raise FileNotFoundError("no runs found under runs/")
    return runs[-1]
