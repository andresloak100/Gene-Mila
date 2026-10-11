"""The laboratory: shared run context used by the controller, workers and planner."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
import threading
import time
from pathlib import Path

import numpy as np

from . import REPO_ROOT
from .benchmark import PRIMARY_HIGHER_IS_BETTER, PRIMARY_METRIC, SELECTION_RULES, selection_score
from .benchmark import comparable, reference
from .benchmark.evaluator import bundle_strata, categories_of, category_summary, evaluate, metric_values, \
    paired_summary
from .benchmark.oracle import QueryOracle
from .data.bundle import LabelSet, added_knowledge, export_public, verify_bundle
from .db import Database
from .features.registry import BUILTIN_FEATURES
from .guard import CodeViolation, check_plugin_source
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
        # knowledge files added to the bundle after it was built make this run its own arm: record what the
        # agents can read (the run's public copy), and refuse a config that recorded something else
        seen = added_knowledge(self.public_dir)
        recorded = cfg["run"].get("external_knowledge")
        if recorded is None:
            if seen:
                cfg["run"]["external_knowledge"] = seen
        elif sorted(recorded) != seen:
            raise RuntimeError(f"run.external_knowledge {sorted(recorded)} does not match the knowledge files added "
                               f"to the bundle {seen}; the bundle's knowledge/ changed after the run was configured")
        # every experiment process runs with a fixed hash seed (sandbox.HASH_SEED), so a feature that follows str
        # hashes (a set of names iterated in order) computes the same blocks in every process: recorded in the run's
        # config as run.hash_seed. A run reopened from before the seed was fixed records none (its processes each
        # drew their own) and keeps none; it is not part of the arm, whose runs a label already tells apart by code
        from .sandbox import HASH_SEED
        if not reopen:
            if cfg["run"].get("hash_seed", HASH_SEED) != HASH_SEED:
                raise RuntimeError(f"run.hash_seed {cfg['run']['hash_seed']!r} is not the seed every experiment "
                                   f"process runs with ({HASH_SEED}, sandbox.HASH_SEED); it is not configurable")
            cfg["run"]["hash_seed"] = HASH_SEED
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
        # the model-selection rule is a lab setting (never an agent's choice); see benchmark.SELECTION_RULES
        self.selection = str(cfg["experiment"].get("selection") or PRIMARY_METRIC)
        if self.selection not in SELECTION_RULES:
            raise ValueError(f"experiment.selection must be one of {sorted(SELECTION_RULES)}, not {self.selection!r}")
        # a paired sealed query spends two of the cap and is recorded as two query_only events by the oracle itself
        # (on_paired, under its lock), whoever calls it, so a reopened run counts it; a single query is recorded by
        # query_only as before
        self.oracle = QueryOracle(self.data_dir, max_queries=int(cfg.get("final", {}).get("max_queries", 5)),
                                  used=lambda: self.db.query("SELECT COUNT(*) AS n FROM events WHERE kind='query_only'")[0]["n"],
                                  selection=self.selection, on_paired=self._record_paired)
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
        # a bundle with pairs, a gene-grouped split or a recorded modality (benchmark.evaluator.bundle_strata; None
        # for any other bundle, Adamson's included, which keeps every behaviour below exactly as before) is also
        # scored without each perturbation's own targets and, when grouped, by category; a grouped bundle gets
        # gene-grouped cross-validation folds (pipeline.cv_folds_of, recorded as the hyperparameter cv_groups),
        # and one whose targets include a pair the additive baseline
        self._strata = bundle_strata(self.data_dir)
        self._targets = self._strata["targets"] if self._strata else {}
        self.has_pairs = any(len(v) > 1 for v in self._targets.values())
        self.cv_groups = "gene" if self._strata and self._strata["grouped"] else None
        self._cv_categories: dict[str, str] = {}  # out-of-fold training perturbations' categories, against their fold
        if self.cv_groups and self.cv_folds > 1:
            for fold, hide in self._cv_folds():
                gone = set(hide)
                self._cv_categories.update(categories_of(fold, self._targets,
                                                         [p for p in self._train.perts if p not in gone]))
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

    def warm_start(self, prev_run_dir: Path) -> dict:
        """Continue a campaign: import the previous run's useful features (code and metadata) into this run's
        store, queue its best model as this run's starting point, and leave a summary of what it learned for
        the planner (run_dir/warm_start.json, rendered as PRIOR CAMPAIGN in the research state).

        Only a run on the same dataset and split qualifies: a model selected on another split's visible
        perturbations could have been selected on this split's sealed ones. Every imported plugin passes the
        plugin guard as it stands now, as if an agent had just written it, except that id() is allowed (in past
        runs' plugins it is a cache key, which changes no value): a past run's plugin it refuses (one built on
        hash() of a name, whose values no other process reproduced) is not imported, and neither is one
        that names a refused feature (it would compute it through ctx.feature); both are left out of the starting
        model and of the features offered to the planner as helpful, and listed with the guard's reason (refused,
        in warm_start.json and in the warm_start event)."""
        from .research_state import HELP_THRESHOLD
        prev_run_dir = Path(prev_run_dir).resolve()
        prev = Database(prev_run_dir / "lab.db")
        try:
            row = prev.query("SELECT * FROM runs LIMIT 1")
            if not row:
                raise RuntimeError(f"{prev_run_dir} holds no run")
            run = row[0]
            if run["dataset"] != self.dataset or run["split_id"] != self.split_id:
                raise RuntimeError(f"cannot continue from {run['run_id']}: it ran on {run['dataset']} "
                                   f"({run['split_id']}), this run is on {self.dataset} ({self.split_id})")
            raw = run.get("config_json")
            prev_cfg = json.loads(raw) if isinstance(raw, str) else (raw or {})
            prev_rule = str((prev_cfg.get("experiment") or {}).get("selection") or PRIMARY_METRIC)
            if prev_rule != self.selection:  # its scores (and its best) were ranked by another rule
                raise RuntimeError(f"cannot continue from {run['run_id']}: it selected models by {prev_rule}, "
                                   f"this run selects by {self.selection}")
            best = prev.best()
            if best is None:
                raise RuntimeError(f"{run['run_id']} has no completed experiment to continue from")
            feats = {f["name"]: f for f in prev.features()}
            helpful = [r["new_feature"] for r in prev.query(
                "SELECT new_feature, MAX(delta_from_parent) AS d FROM experiments WHERE status='completed' AND "
                "new_feature IS NOT NULL AND delta_from_parent IS NOT NULL GROUP BY new_feature ORDER BY d DESC")
                if r["d"] is not None and r["d"] > HELP_THRESHOLD]
            wanted = [f for f in (best.get("feature_set_json") or []) + helpful if f not in BUILTIN_FEATURES]
            imported, missing, refused, sources = [], [], {}, {}
            for name in dict.fromkeys(wanted):
                src = prev_run_dir / "feature_store" / f"{name}.py"
                meta = feats.get(name)
                if not src.exists() or meta is None:
                    missing.append(name)
                    continue
                if name in self.known_features():
                    continue
                try:
                    check_plugin_source(src.read_text(), name, imported=True)
                except CodeViolation as exc:
                    refused[name] = f"plugin guard: {exc}"[:200]
                    continue
                sources[name] = src.read_text()
            again = True
            while again:  # a feature naming a refused one (ctx.feature) would fail on it: refused too, transitively
                again = False
                for name, text in list(sources.items()):
                    via = sorted(r for r in refused if re.search(rf"\b{re.escape(r)}\b", text))
                    if via:
                        refused[name] = f"names refused feature(s) {', '.join(via)}"[:200]
                        del sources[name]
                        again = True
            for name in sources:
                src, meta = prev_run_dir / "feature_store" / f"{name}.py", feats[name]
                dst = self.store / f"{name}.py"
                shutil.copy2(src, dst)
                self.db.upsert_feature({**meta, "implementation_path": str(dst.relative_to(self.run_dir)),
                                        "code_hash": sha256_text(dst.read_text()),
                                        "creator_experiment": f"warm:{run['run_id']}:{meta.get('creator_experiment')}"})
                imported.append(name)
            start_set = [f for f in (best.get("feature_set_json") or []) if f not in missing and f not in refused]
            helpful = [f for f in helpful if f not in refused]  # not in this run: the planner cannot build on them
            hp = {k: v for k, v in (best.get("hyperparameters_json") or {}).items() if k in ("alpha", "alpha_grid")}
            sealed = (best.get("query_metrics_json") or {}).get("primary")
            eid, status = self.queue(ExperimentSpec(
                hypothesis=f"Warm start: the best model of run {run['run_id']} ({best['experiment_id']}, visible "
                           f"{best['primary_score']:.4f}) is the starting point of this run.",
                scientific_rationale="A continued campaign starts where the previous one ended instead of "
                                     "rediscovering its features; everything proposed here is measured against it.",
                kind="config", category="exploit", feature_set=start_set, model_type=best["model_type"],
                hyperparameters=hp, proposer="python:warm_start", priority=95.0,
                hypothesis_group=f"warm_start_{run['run_id']}"))
            failed = prev.query("SELECT hypothesis, failure_stage, failure_reason FROM experiments WHERE status IN "
                                "('failed','rejected','killed') ORDER BY finished_at DESC LIMIT 12")
            unhelpful = [r["new_feature"] for r in prev.query(
                "SELECT new_feature, MAX(delta_from_parent) AS d FROM experiments WHERE status='completed' AND "
                "new_feature IS NOT NULL AND delta_from_parent IS NOT NULL GROUP BY new_feature")
                if r["d"] is not None and r["d"] <= HELP_THRESHOLD]
            info = {"run_id": run["run_id"], "run_dir": str(prev_run_dir), "best_experiment": best["experiment_id"],
                    "best_visible": best["primary_score"], "best_sealed": sealed, "model": best["model_type"],
                    "features": start_set, "helpful_features": helpful,
                    "unhelpful_features": unhelpful[:20],
                    "failed_ideas": [{"idea": r["hypothesis"][:90], "stage": r["failure_stage"],
                                      "reason": (r["failure_reason"] or "")[:110]} for r in failed],
                    "imported": imported, "missing": missing, "refused": refused, "start_experiment": eid,
                    "start_status": status}
            (self.run_dir / "warm_start.json").write_text(json.dumps(info, indent=1))
            self.db.event("warm_start", f"continued from {run['run_id']}: imported {len(imported)} features, "
                                        f"queued {eid} ({status})" + (f"; missing {missing}" if missing else "")
                                        + (f"; refused by the plugin guard {sorted(refused)}" if refused else ""))
            return info
        finally:
            prev.close_thread_conn()

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
        if spec.kind != "new_feature":  # hashed before validation, so a rejected configuration is never re-proposed
            record["config_hash"] = self.config_hash_for(spec)
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
            spec.hyperparameters = {**spec.hyperparameters, **self._cv_hyperparameters()}
            record["hyperparameters_json"] = spec.hyperparameters
        with self.db.lock:  # the duplicate check and the insert are one step: two proposers cannot both win
            if spec.kind != "new_feature":
                dup = self.db.find_by_config_hash(record["config_hash"])
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
            res = evaluate(pred, self._val1.means, self.control_mean, self._val1.perts, selection=self.selection,
                           **self._extras("val1"))
            if cv is not None:
                cv_res = evaluate(cv[k].astype(np.float64) + self.control_mean, self._train.means,
                                  self.control_mean, self._train.perts, selection=self.selection,
                                  **self._extras("cv"))
                self._combine_visible(res["metrics"], cv_res["metrics"])
                self._combine_strata(res, cv_res)
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
        """primary = the selection rule applied to each of its metrics averaged over validation + out-of-fold
        training perturbations (each perturbation weighs the same); `<metric>` stays the validation-set value
        and `<metric>_cv` the out-of-fold value."""
        n1, nt = len(self._val1.perts), len(self._train.perts)
        combined = {}
        for m in sorted({PRIMARY_METRIC, *SELECTION_RULES[self.selection]}):
            metrics[f"{m}_cv"] = cv_metrics[m]
            combined[m] = (n1 * metrics[m] + nt * cv_metrics[m]) / (n1 + nt)
        metrics["primary"] = selection_score(combined, self.selection)
        metrics["n_visible"] = n1 + nt
        metrics["cv_folds"] = self.cv_folds

    def _extras(self, part: str) -> dict:
        """evaluate()'s extras for this bundle: none without strata (scored exactly as before); else every
        perturbation's target columns (pearson_delta_nontarget) and the categories of the visible validation
        perturbations (part "val1", as the split records them) or of the out-of-fold training ones (part "cv",
        by the same rule against each fold's view)."""
        if self._strata is None:
            return {}
        if part == "val1":  # the visible validation perturbations' own: the split's map also names the sealed ones
            keep = set(self._val1.perts)
            cats = {p: c for p, c in self._strata["categories"].items() if p in keep}
        else:
            cats = self._cv_categories
        return {"targets": self._strata["target_idx"], "categories": cats or None}

    def _combine_strata(self, res: dict, cv_res: dict) -> None:
        """Beside _combine_visible, for a bundle with strata: `pearson_delta_nontarget_cv`, and per category
        `by_category` (the validation set's, as `<metric>` is), `by_category_cv` (out of fold) and
        `by_category_visible` (both pooled, each perturbation weighing the same). Selection is untouched."""
        if self._strata is None:
            return
        m, cm = res["metrics"], cv_res["metrics"]
        if "pearson_delta_nontarget" in cm:
            m["pearson_delta_nontarget_cv"] = cm["pearson_delta_nontarget"]
        if "by_category" in cm:
            m["by_category_cv"] = cm["by_category"]
            m["by_category_visible"] = category_summary(
                {**res["per_perturbation"], **cv_res["per_perturbation"]},
                {**(self._extras("val1")["categories"] or {}), **self._cv_categories})
        if self.cv_groups:
            m["cv_groups"] = self.cv_groups

    def _cv_folds(self) -> list[tuple[list[str], list[str]]]:
        """The run's (predict, hide) folds over the training perturbations, as every experiment's pipeline draws
        them from its hyperparameters (cv_folds, cv_seed and, for a grouped bundle, cv_groups)."""
        from .pipeline import cv_folds_of
        targets = None if self.cv_groups is None else {p: list(self._targets.get(p, [])) for p in self._train.perts}
        return cv_folds_of(self._train.perts, self.cv_folds, self.cv_seed, targets)

    def _cv_hyperparameters(self) -> dict:
        """The fold settings the lab adds to every experiment's hyperparameters when it cross-validates; cv_groups
        only for gene-grouped folds, so a random-fold run's hyperparameters and configuration hashes are unchanged."""
        return {"cv_folds": self.cv_folds, "cv_seed": self.cv_seed,
                **({"cv_groups": self.cv_groups} if self.cv_groups else {})}

    def _cv_baseline(self, which: str) -> np.ndarray:
        """Out-of-fold analytic baseline for the training perturbations, on the run's folds: each fold's
        perturbations predicted from the training perturbations its view keeps."""
        pred = np.tile(self.control_mean, (len(self._train.perts), 1))
        if which in ("baseline_mean_response", "baseline_additive"):
            pos = {p: i for i, p in enumerate(self._train.perts)}
            delta = self._train.means - self.control_mean
            for fold, hide in self._cv_folds():
                rows = [pos[p] for p in fold]
                rest = np.setdiff1d(np.arange(len(pos)), [pos[p] for p in hide])
                if which == "baseline_mean_response":
                    pred[rows] += delta[rest].mean(axis=0)
                else:
                    pred[rows] += self._additive_delta(fold, [self._train.perts[i] for i in rest], delta[rest])
        return pred

    def _additive_delta(self, perts: list[str], train: list[str], train_delta: np.ndarray) -> np.ndarray:
        """baseline_additive's predicted change (additive_delta) with the bundle's targets."""
        return additive_delta(perts, self._targets, train, train_delta)

    def visible_scores(self, experiment_id: str) -> tuple[dict, dict]:
        """Per-perturbation visible scores of a completed experiment or analytic baseline at its chosen alpha: the
        visible validation perturbations and, when the run cross-validates, the out-of-fold training ones, as
        {perturbation: evaluate()'s per-perturbation metrics}, with the categories they fall in ({} for a bundle
        without them). Trusted controller code over visible labels only."""
        rec = self.db.get_experiment(experiment_id)
        if not rec:
            raise KeyError(f"no experiment {experiment_id}")
        pred, perts = self._predict(rec, self._val1.perts)
        idx = {p: i for i, p in enumerate(perts)}
        missing = [p for p in self._val1.perts if p not in idx]
        if missing:
            raise ValueError(f"{experiment_id} has no prediction for validation perturbations {missing[:3]}")
        res = evaluate(pred[[idx[p] for p in self._val1.perts]], self._val1.means, self.control_mean,
                       self._val1.perts, selection=self.selection, **self._extras("val1"))
        scores, cats = dict(res["per_perturbation"]), dict(self._extras("val1").get("categories") or {})
        if self.cv_folds > 1:
            if rec["kind"] == "baseline" and not rec.get("artifact_dir"):
                cv = self._cv_baseline(rec["hypothesis_group"])
            else:
                c = np.load(Path(rec["artifact_dir"]) / "cv.npz", allow_pickle=False)
                if [str(p) for p in c["perts"]] != self._train.perts:
                    raise ValueError(f"{experiment_id}: cv.npz does not cover the training perturbations")
                alphas = list(map(float, c["alphas"]))
                cv = c["delta"][alphas.index(rec["best_alpha"]) if rec["best_alpha"] in alphas else 0]
                cv = cv.astype(np.float64) + self.control_mean
            cv_res = evaluate(cv, self._train.means, self.control_mean, self._train.perts, selection=self.selection,
                              **self._extras("cv"))
            scores.update(cv_res["per_perturbation"])
            cats.update(self._cv_categories)
        return scores, {p: c for p, c in cats.items() if p in scores}

    def compare_visible(self, experiment_a: str, experiment_b: str, metric: str = PRIMARY_METRIC) -> dict:
        """Paired comparison of two experiments on the visible perturbations (visible_scores), a minus b, by one
        per-perturbation metric ("primary": the run's selection rule per perturbation): evaluator.paired_summary's
        mean difference, paired SE, wins and the reading rule's verdict, pooled and per category. Visible labels
        only; the sealed counterpart is Lab.query_paired."""
        (a, cats), (b, _) = self.visible_scores(experiment_a), self.visible_scores(experiment_b)
        return {"experiments": [experiment_a, experiment_b], "metric": metric,
                **paired_summary(metric_values(a, metric, self.selection), metric_values(b, metric, self.selection),
                                 cats or None)}

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

    def query_paired(self, experiment_a: str, experiment_b: str, metric: str = PRIMARY_METRIC) -> dict:
        """The sealed paired comparison of two experiments (or analytic baselines), a minus b, through the run's
        oracle (QueryOracle.query_paired: mean difference, paired SE, wins and verdict, pooled and per category,
        and each model's aggregate metrics). It scores both models on the sealed set, so it spends two of the
        run's queries, and the oracle records both in lab.db before it returns (_record_paired), so a reopened run
        counts them against its cap. The way a run compares two models on the sealed set."""
        recs = [self.db.get_experiment(e) for e in (experiment_a, experiment_b)]
        missing = [e for e, r in zip((experiment_a, experiment_b), recs) if not r]
        if missing:
            raise KeyError(f"no experiment {missing[0]}")
        (pa, oa), (pb, ob) = (self._predict(r, self.oracle.perts) for r in recs)
        return self.oracle.query_paired(experiment_a, pa, oa, experiment_b, pb, ob, self.control_mean, metric=metric)

    def _record_paired(self, out: dict) -> None:
        """The oracle's on_paired hook, under its lock: one query_only event per model scored (the cap counts these
        events, so a later process sees the two queries spent), a query_paired event with the paired summary, and
        the whole answer in query_paired/ beside the run's cell-eval files, so every sealed number is reported."""
        a, b = (str(e) for e in out["experiments"])
        for e, other in ((a, b), (b, a)):
            self.db.event("query_only", f"paired query-only evaluation of {e} against {other}", e)
        d = self.run_dir / "query_paired"
        d.mkdir(exist_ok=True)
        safe = [re.sub(r"[^\w.-]", "_", e) for e in (a, b)]
        path = d / f"{len(list(d.glob('*.json'))) + 1:02d}_{safe[0]}_vs_{safe[1]}.json"
        path.write_text(json.dumps(out, indent=1))
        self.db.event("query_paired", json.dumps({"experiments": [a, b], "metric": out["metric"],
                                                  "file": path.name, "paired": out["paired"]}), a)

    def celleval_val2(self, experiment_id: str) -> dict | None:
        path = self._celleval_path(experiment_id, "val2")
        return json.loads(path.read_text()) if path.exists() else None

    # ---------------------------------------------------------------- baselines
    def _analytic_baseline(self, which: str, perts: list[str]) -> np.ndarray:
        z = np.load(self.public_dir / "public.npz", allow_pickle=False)
        if which == "baseline_unchanged":
            delta = np.zeros_like(self.control_mean)
        elif which == "baseline_additive":
            return self.control_mean + self._additive_delta(perts, self._train.perts,
                                                            self._train.means - self.control_mean)
        else:  # baseline_mean_response
            delta = z["train_means"].astype(np.float64).mean(axis=0) - self.control_mean
        return np.tile(self.control_mean + delta, (len(perts), 1))

    def record_analytic_baselines(self) -> None:
        baselines = [("baseline_unchanged", "Perturbations do not change expression (predict control mean)."),
                     ("baseline_mean_response", "Every perturbation produces the average training response.")]
        if self.has_pairs:  # only a bundle whose targets include a pair: every other bundle keeps its two baselines
            baselines.append(("baseline_additive", "A perturbation changes expression by the sum of its genes' "
                                                   "single-gene changes in training (additive model)."))
        for key, hyp in baselines:
            if self.db.query("SELECT 1 FROM experiments WHERE hypothesis_group=?", (key,)):
                continue
            t0 = time.process_time()
            pred = self._analytic_baseline(key, self._val1.perts)
            res = evaluate(pred, self._val1.means, self.control_mean, self._val1.perts, selection=self.selection,
                           **self._extras("val1"))
            if self.cv_folds > 1:
                cv_res = evaluate(self._cv_baseline(key), self._train.means, self.control_mean, self._train.perts,
                                  selection=self.selection, **self._extras("cv"))
                self._combine_visible(res["metrics"], cv_res["metrics"])
                self._combine_strata(res, cv_res)
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
    def config_hash_for(self, spec: ExperimentSpec) -> str:
        """The configuration hash an experiment gets when queued (includes the run's fold settings)."""
        hp = spec.hyperparameters
        if self.cv_folds > 1:
            hp = {**hp, **self._cv_hyperparameters()}
        return config_hash(replace(spec, hyperparameters=hp), self.feature_code_hashes(), self.split_id)

    def best(self) -> dict | None:
        return self.db.best()

    def best_baseline(self) -> dict | None:
        rows = self.db.query("SELECT * FROM experiments WHERE kind='baseline' AND status='completed' "
                             "ORDER BY primary_score DESC LIMIT 1")
        return rows[0] if rows else None

    def data_summary(self) -> str:
        """The DATASET line of the research state and the worker prompt. A bundle with pairs of genes or a recorded
        modality gets prompts.dataset_line (training singles and pairs, the key rule, the modality); every other
        bundle (Adamson's) the line below, exactly as before."""
        from .prompts import bundle_has_pairs, dataset_line
        m = self.manifest
        targets = json.loads((self.public_dir / "knowledge" / "targets.json").read_text())
        if bundle_has_pairs(targets) or m.get("modality"):
            return dataset_line(m, targets, self._train.perts)
        sizes = [len(v) for v in targets.values()] or [1]
        multi = sum(1 for n in sizes if n > 1)
        kind = "single-gene targets" if not multi else (
            f"targets of 1 to {max(sizes)} genes; {multi} of {len(sizes)} perturbations hit more than one gene")
        return (f"{m['name']}: {m['n_genes']} genes, {m['n_control_cells']} control cells, "
                f"{m['n_train']} training perturbations ({kind}); predict unseen perturbations.")

    def knowledge_summary(self) -> str:
        """One line per knowledge file for the planner and workers. A file that describes itself (an external
        screen's "description", genemila/data/external_screen.py) is shown with its whole description and its keys:
        cut to the first 60 characters, the Norman agents of 11 Oct 2026 read the Replogle screen as an unexplained
        dict and used it in 1 of 355 features."""
        parts = []
        for p in sorted((self.public_dir / "knowledge").glob("*.json")):
            obj = json.loads(p.read_text())
            if isinstance(obj, dict) and isinstance(obj.get("description"), str):
                parts.append(f"{p.stem}: {obj['description'][:900]} (a dict with keys {', '.join(map(str, obj))})")
            elif isinstance(obj, dict):
                k = next(iter(obj), None)
                parts.append(f"{p.stem}: dict of {len(obj)} entries, e.g. {k!r}: {str(obj[k])[:60]}")
            else:
                parts.append(f"{p.stem}: list of {len(obj)}, e.g. {str(obj[0])[:60] if obj else ''}")
        return "; ".join(parts) or "none"

    def git_head_dirty(self) -> bool:
        return bool(git(self.repo, "status", "--porcelain", "--untracked-files=no"))


def additive_delta(perts: list[str], targets: dict, train: list[str], train_delta: np.ndarray) -> np.ndarray:
    """baseline_additive's predicted change, the one rule the lab and tools/refit_visible.py share: the sum over a
    perturbation's target genes (targets: perturbation -> its genes; sorted and without repeats, so the order a
    pair lists them changes nothing) of each gene's single change in `train` (the mean change in train_delta of
    the training perturbations whose one target it is) or, for a gene without a training single, the mean change of
    all training singles. A pair is Δ_A + Δ_B, a held-out single the mean single change; a perturbation without a
    listed target counts as one gene without a single. With no single in training at all, the mean training change
    stands in for the mean single change."""
    rows: dict[str, list[int]] = {}
    for i, p in enumerate(train):
        tg = targets.get(p) or []
        if len(tg) == 1:
            rows.setdefault(tg[0], []).append(i)
    single = {g: train_delta[r].mean(axis=0) for g, r in rows.items()}
    every = [i for r in rows.values() for i in r]
    fill = train_delta[every].mean(axis=0) if every else train_delta.mean(axis=0)
    out = np.zeros((len(perts), train_delta.shape[1]))
    for j, p in enumerate(perts):
        for g in sorted(set(targets.get(p) or [])) or [None]:
            out[j] += single.get(g, fill)
    return out


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
