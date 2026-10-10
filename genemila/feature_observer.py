"""Opt-in worker results and master decisions, using metadata and already-computed CV scores.

This bridge never evaluates predictions, reads labels, or changes Lab.best(). The
board is a separate retained candidate and append-only failure/rejection archive.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import time

from .feature_board import FeatureBoard, _json
from .features.registry import BUILTIN_FEATURES


def _protocol(lab) -> dict:
    if isinstance(lab.cv_folds, bool) or int(lab.cv_folds) < 2:
        raise ValueError("automatic feature observation requires at least two public training CV folds")
    return {"version": 1, "dataset": str(lab.dataset), "split_id": str(lab.split_id),
            "metric": "pearson_delta_cv", "aggregation": "mean_over_training_perturbations",
            "cv_folds": int(lab.cv_folds), "cv_seed": int(lab.cv_seed),
            "alpha_selection": f"lab_visible_selection:{lab.selection}"}


def _open(lab):
    settings = lab.cfg.get("feature_board") or {}
    path, scope = settings.get("path"), settings.get("metric_scope")
    if scope is None or scope == "":
        return None  # a path alone is the existing read-only prompt-memory mode
    if not path or not isinstance(scope, str) or not scope.strip():
        raise ValueError("automatic feature observation requires explicit board path and metric_scope")
    path = Path(path).expanduser()
    if path.suffix.lower() == ".json":
        raise ValueError("automatic feature observation requires a SQLite board, not exported JSON")
    if not path.is_absolute():
        path = lab.run_dir / path
    protocol = _protocol(lab)
    board = FeatureBoard(path, master_id=settings.get("master_id", "master"), metric_scope=scope)
    with board._connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS external_observer_config
                      (singleton INTEGER PRIMARY KEY CHECK(singleton=1), protocol_json TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS external_observations (
            observation_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
            experiment_id TEXT NOT NULL, worker_id TEXT NOT NULL, status TEXT NOT NULL,
            result_json TEXT NOT NULL, result_digest TEXT NOT NULL, task_id INTEGER NOT NULL,
            observed_at REAL NOT NULL, reviewed_at REAL, decision_json TEXT,
            UNIQUE(run_id, experiment_id))""")
        current = db.execute("SELECT protocol_json FROM external_observer_config WHERE singleton=1").fetchone()
        encoded = _json(protocol)
        if current is None:
            occupied = any(db.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() is not None
                           for table in ("tasks", "champion", "promotions", "feature_archive"))
            if occupied:
                raise ValueError("board already has results without this observer protocol; use a separate board")
            db.execute("INSERT INTO external_observer_config VALUES (1,?)", (encoded,))
        elif current[0] != encoded:
            raise ValueError("feature board protocol differs (dataset, split, folds, seed, metric, or alpha selection)")
        _check_champion_protocol(db, protocol)
    return board, protocol


def _check_champion_protocol(db, protocol):
    row = db.execute("SELECT candidate_json FROM champion WHERE singleton=1").fetchone()
    if row is not None and (json.loads(row[0]).get("metrics") or {}).get("protocol") != protocol:
        raise ValueError("feature board champion belongs to a different or unspecified observer protocol")


def publish_worker_observation(lab, experiment_id: str, worker_id: str, result: dict | None = None):
    """Record a finalized experiment once; a conflicting replay is an error.

    Only the public training-CV Pearson at the laboratory's selected alpha is
    published. Combined selection scores, validation metrics, and sealed metrics
    are excluded. Failure text and source references contain no new measurements.
    """
    opened = _open(lab)
    if opened is None:
        return None
    board, protocol = opened
    record = lab.db.get_experiment(experiment_id)
    if record is None or record.get("status") not in ("completed", "failed", "rejected", "killed"):
        return None
    status = record["status"]
    features = list(record.get("feature_set_json") or [])
    parent = record.get("parent_id")
    parent_id = f"{lab.run_id}:{parent}" if parent else None
    identity = {"run_id": lab.run_id, "experiment_id": experiment_id, "protocol": protocol,
                "config_hash": record.get("config_hash"), "code_commit": record.get("code_commit"),
                "feature_names": features, "feature_params": record.get("feature_params_json") or {},
                "model_type": record.get("model_type"), "best_alpha": record.get("best_alpha")}
    signature = hashlib.sha256(_json(identity).encode()).hexdigest()
    sources = list((result or {}).get("feature_sources") or features)
    commit = record.get("code_commit")
    source_paths = [f"git:{commit}:" + ("genemila/features/builtin.py" if name in BUILTIN_FEATURES else
                                      f"genemila/features/plugins/{name}.py") for name in sources] if commit else []
    payload = {"run_id": lab.run_id, "experiment_id": experiment_id, "status": status,
               "feature_names": features, "candidate_signature": signature, "parent_id": parent_id,
               "metric_scope": board.metric_scope, "metrics": {"protocol": protocol}, "source_paths": source_paths}
    if status == "completed":
        score = (record.get("val_metrics_json") or {}).get("pearson_delta_cv")
        if isinstance(score, bool) or not isinstance(score, (float, int)) or not math.isfinite(score) or not -1 <= score <= 1:
            raise ValueError("completed experiment has no valid public pearson_delta_cv; observation skipped")
        columns = (result or {}).get("n_features")
        if isinstance(columns, bool) or not isinstance(columns, int) or columns < 1:
            raise ValueError("completed observation requires a positive predictor column count")
        payload.update(validation_pearson=float(score), n_columns=columns)
    else:
        payload["failure_reason"] = f"{record.get('failure_stage') or status}: {record.get('failure_reason') or status}"[:2000]
    encoded = _json(payload)
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    with board._connect() as db:
        db.execute("BEGIN IMMEDIATE")
        old = db.execute("SELECT observation_id,result_digest FROM external_observations WHERE run_id=? AND experiment_id=?",
                         (lab.run_id, experiment_id)).fetchone()
        if old is not None:
            if old["result_digest"] != digest:
                raise ValueError("conflicting result replay for an already observed experiment")
            return {"observation_id": old["observation_id"], "duplicate": True}
        now = time.time()
        task_id = db.execute("""INSERT INTO tasks
            (kind,payload_json,parent_id,status,worker_id,result_json,failure_reason,created_at,claimed_at,finished_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", ("external_experiment", _json(identity), parent_id,
            "completed" if status == "completed" else "failed", worker_id, encoded,
            payload.get("failure_reason"), now, now, now)).lastrowid
        observation_id = db.execute("""INSERT INTO external_observations
            (run_id,experiment_id,worker_id,status,result_json,result_digest,task_id,observed_at)
            VALUES (?,?,?,?,?,?,?,?)""", (lab.run_id, experiment_id, worker_id, status, encoded, digest, task_id, now)).lastrowid
        return {"observation_id": observation_id, "duplicate": False}


def review_worker_observations(lab, limit: int = 32) -> list[dict]:
    """Master atomically reviews observations and acknowledges each decision once."""
    opened = _open(lab)
    if opened is None:
        return []
    board, protocol = opened
    decisions = []
    with board._connect() as db:
        db.execute("BEGIN IMMEDIATE")
        _check_champion_protocol(db, protocol)
        rows = db.execute("SELECT * FROM external_observations WHERE reviewed_at IS NULL ORDER BY observation_id LIMIT ?",
                          (max(1, int(limit)),)).fetchall()
        for row in rows:
            encoded = row["result_json"]
            if hashlib.sha256(encoded.encode()).hexdigest() != row["result_digest"]:
                raise ValueError("observed experiment result digest does not match its canonical payload")
            payload = json.loads(encoded)
            task = db.execute("SELECT status,result_json FROM tasks WHERE task_id=?", (row["task_id"],)).fetchone()
            expected_status = "completed" if row["status"] == "completed" else "failed"
            if task is None or task["status"] != expected_status or task["result_json"] != encoded:
                raise ValueError("observed experiment does not match its canonical board task result")
            if payload["metrics"]["protocol"] != protocol or payload["metric_scope"] != board.metric_scope:
                raise ValueError("observation metric scope or protocol differs from the board")
            common = {key: payload[key] for key in ("feature_names", "candidate_signature", "parent_id", "metrics", "source_paths")}
            if row["status"] == "completed":
                decision = board._promote_candidate_in_transaction(
                    db, board.master_id, task_id=row["task_id"], validation_pearson=payload["validation_pearson"],
                    n_columns=payload["n_columns"], metric_scope=board.metric_scope, **common)
            else:
                archive_id = board._archive(db, status="rejected" if row["status"] == "rejected" else "failed",
                                            task_id=row["task_id"], reason=payload["failure_reason"], **common)
                decision = {"accepted": False, "reason": payload["failure_reason"], "archive_id": archive_id}
            db.execute("UPDATE external_observations SET reviewed_at=?,decision_json=? WHERE observation_id=?",
                       (time.time(), _json(decision), row["observation_id"]))
            decisions.append({"run_id": row["run_id"], "experiment_id": row["experiment_id"], **decision})
    return decisions
