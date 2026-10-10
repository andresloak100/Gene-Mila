"""Local metadata-only board for a master and feature-pruning workers.

Workers claim jobs and publish results; only the configured master promotes a
champion. Role IDs are a coordination guard, not process authentication. Store
feature names, file references, signatures, and aggregate metrics, never labels
or credentials. This module does not load, execute, or delete feature sources.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import math
from pathlib import Path
import sqlite3
import time


_FORBIDDEN_KEYS = {
    "api_key", "apikey", "access_token", "refresh_token", "secret", "password",
    "authorization", "credentials", "labels", "raw_labels", "train_labels",
    "validation_labels", "test_labels", "sealed_labels", "y_true", "y_train", "y_val", "y_test",
}


def _json(value):
    def check(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("Metadata keys must be strings")
                if key.lower().replace("-", "_").replace(" ", "_") in _FORBIDDEN_KEYS:
                    raise ValueError("The board accepts metadata only, not labels or credentials")
                check(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check(child)
    check(value)
    try:
        return json.dumps(value, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("Metadata must be finite, JSON-serializable values") from exc


def _name(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def _decode(row):
    if row is None:
        return None
    result = dict(row)
    for key in list(result):
        if key.endswith("_json"):
            encoded = result.pop(key)
            result[key[:-5]] = json.loads(encoded) if encoded is not None else None
    return result


class FeatureBoard:
    def __init__(self, path: str | Path, master_id: str = "master", metric_scope: str | None = None):
        """Optionally bind comparisons to one named metric/data/fold definition.

        Declaring a scope on an existing unscoped board is an explicit assertion
        that its current champion used that scope; historical rows are untouched.
        Once declared, the scope cannot be changed and promotions must repeat it.
        Scope strings and actor IDs are integrity metadata, not authentication.
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.master_id = _name(master_id, "master_id")
        if metric_scope is not None:
            _name(metric_scope, "metric_scope")
        with self._connect() as db:
            # Concurrent first-time worker connections can race while switching
            # journal mode; this PRAGMA does not always honor busy_timeout.
            for attempt in range(7):
                try:
                    if db.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal":
                        db.execute("PRAGMA journal_mode=WAL")
                    break
                except sqlite3.OperationalError as exc:
                    if "locked" not in str(exc).lower() or attempt == 6:
                        raise
                    time.sleep(min(.01 * 2 ** attempt, .25))
            db.executescript("""
                CREATE TABLE IF NOT EXISTS board_config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL, parent_id TEXT, status TEXT NOT NULL DEFAULT 'queued',
                    worker_id TEXT, result_json TEXT, failure_reason TEXT,
                    created_at REAL NOT NULL, claimed_at REAL, finished_at REAL);
                CREATE INDEX IF NOT EXISTS tasks_queue ON tasks(status, task_id);
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL,
                    recipient TEXT, task_id INTEGER, body_json TEXT NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS feature_archive (
                    archive_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, status TEXT NOT NULL,
                    feature_names_json TEXT NOT NULL, candidate_signature TEXT NOT NULL,
                    parent_id TEXT, reference_id TEXT, metrics_json TEXT NOT NULL, reason TEXT NOT NULL,
                    source_paths_json TEXT NOT NULL, created_at REAL NOT NULL);
                CREATE TRIGGER IF NOT EXISTS archive_no_update BEFORE UPDATE ON feature_archive
                    BEGIN SELECT RAISE(ABORT, 'feature archive is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS archive_no_delete BEFORE DELETE ON feature_archive
                    BEGIN SELECT RAISE(ABORT, 'feature archive is append-only'); END;
                CREATE TABLE IF NOT EXISTS champion (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1), candidate_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS promotions (
                    promotion_id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_json TEXT NOT NULL,
                    created_at REAL NOT NULL);
            """)
            db.execute("INSERT OR IGNORE INTO board_config VALUES ('master_id', ?)", (self.master_id,))
            if db.execute("SELECT value FROM board_config WHERE key='master_id'").fetchone()[0] != self.master_id:
                raise ValueError("This board is configured for another master_id")
            if metric_scope is not None:
                db.execute("INSERT OR IGNORE INTO board_config VALUES ('metric_scope', ?)", (metric_scope,))
            scope = db.execute("SELECT value FROM board_config WHERE key='metric_scope'").fetchone()
            self.metric_scope = None if scope is None else scope[0]
            if metric_scope is not None and self.metric_scope != metric_scope:
                raise ValueError("This board is configured for another metric_scope")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, kind: str, payload: dict, parent_id=None) -> int:
        _name(kind, "kind")
        if not isinstance(payload, dict):
            raise ValueError("Task payload must be a metadata dictionary")
        encoded = _json(payload)
        with self._connect() as db:
            return db.execute("INSERT INTO tasks(kind,payload_json,parent_id,created_at) VALUES (?,?,?,?)",
                              (kind, encoded, None if parent_id is None else str(parent_id), time.time())).lastrowid

    def claim(self, worker_id: str) -> dict | None:
        _name(worker_id, "worker_id")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT task_id FROM tasks WHERE status='queued' ORDER BY task_id LIMIT 1").fetchone()
            if row is None:
                return None
            db.execute("UPDATE tasks SET status='running',worker_id=?,claimed_at=? WHERE task_id=?",
                       (worker_id, time.time(), row[0]))
            return _decode(db.execute("SELECT * FROM tasks WHERE task_id=?", (row[0],)).fetchone())

    @staticmethod
    def _owned(db, task_id, worker_id):
        row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        if row["worker_id"] != worker_id:
            raise PermissionError("Only the worker that claimed this task may finish it")
        if row["status"] != "running":
            raise ValueError("Only a running task may be finished")
        return _decode(row)

    def complete(self, task_id: int, worker_id: str, result: dict) -> None:
        if not isinstance(result, dict):
            raise ValueError("Result must be a metadata dictionary")
        encoded = _json(result)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._owned(db, task_id, worker_id)
            db.execute("UPDATE tasks SET status='completed',result_json=?,finished_at=? WHERE task_id=?",
                       (encoded, time.time(), task_id))

    def fail(self, task_id: int, worker_id: str, reason: str, *, feature_names=None,
             candidate_signature=None, metrics=None, reference_id=None, source_paths=None) -> int:
        _name(reason, "reason")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            task = self._owned(db, task_id, worker_id)
            payload = task["payload"]
            archive_id = self._archive(db, status="failed", task_id=task_id,
                feature_names=payload.get("feature_names", []) if feature_names is None else feature_names,
                candidate_signature=candidate_signature or payload.get("candidate_signature") or f"task:{task_id}",
                parent_id=task["parent_id"], reference_id=reference_id or payload.get("reference_id"),
                metrics=metrics or {}, reason=reason,
                source_paths=payload.get("source_paths", []) if source_paths is None else source_paths)
            db.execute("UPDATE tasks SET status='failed',failure_reason=?,finished_at=? WHERE task_id=?",
                       (reason, time.time(), task_id))
            return archive_id

    def task(self, task_id: int) -> dict | None:
        with self._connect() as db:
            return _decode(db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone())

    def tasks(self, status: str | None = None) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM tasks" + (" WHERE status=?" if status else "") + " ORDER BY task_id",
                              (status,) if status else ())
            return [_decode(row) for row in rows]

    def result(self, task_id: int) -> dict | None:
        task = self.task(task_id)
        return None if task is None else task["result"]

    def post_message(self, sender: str, body, *, task_id=None, recipient=None) -> int:
        _name(sender, "sender")
        if recipient is not None:
            _name(recipient, "recipient")
        encoded = _json(body)
        with self._connect() as db:
            return db.execute("INSERT INTO messages(sender,recipient,task_id,body_json,created_at) VALUES (?,?,?,?,?)",
                              (sender, recipient, task_id, encoded, time.time())).lastrowid

    def messages(self, task_id=None, after_id: int = 0) -> list[dict]:
        with self._connect() as db:
            sql = "SELECT * FROM messages WHERE message_id>?"
            args = [after_id]
            if task_id is not None:
                sql += " AND task_id=?"
                args.append(task_id)
            return [_decode(row) for row in db.execute(sql + " ORDER BY message_id", args)]

    @staticmethod
    def _archive(db, *, status, feature_names, candidate_signature, metrics, reason,
                 task_id=None, parent_id=None, reference_id=None, source_paths=None):
        if status not in ("failed", "rejected"):
            raise ValueError("Archive status must be failed or rejected")
        _name(candidate_signature, "candidate_signature")
        _name(reason, "reason")
        if not isinstance(feature_names, (list, tuple)) or not all(isinstance(x, str) for x in feature_names):
            raise ValueError("feature_names must be a list of strings")
        return db.execute("""INSERT INTO feature_archive
            (task_id,status,feature_names_json,candidate_signature,parent_id,reference_id,metrics_json,
             reason,source_paths_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (task_id, status, _json(feature_names), candidate_signature,
             None if parent_id is None else str(parent_id), None if reference_id is None else str(reference_id),
             _json(metrics), reason, _json(source_paths or []), time.time())).lastrowid

    def archive_candidate(self, *, status, feature_names, candidate_signature, metrics, reason,
                          task_id=None, parent_id=None, reference_id=None, source_paths=None) -> int:
        with self._connect() as db:
            return self._archive(db, status=status, feature_names=feature_names,
                candidate_signature=candidate_signature, metrics=metrics, reason=reason, task_id=task_id,
                parent_id=parent_id, reference_id=reference_id, source_paths=source_paths)

    def archive(self) -> list[dict]:
        with self._connect() as db:
            return [_decode(row) for row in db.execute("SELECT * FROM feature_archive ORDER BY archive_id")]

    def champion(self) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT candidate_json FROM champion WHERE singleton=1").fetchone()
            return None if row is None else json.loads(row[0])

    def promote_candidate(self, actor_id: str, *, validation_pearson, n_columns: int,
                          feature_names: list[str], candidate_signature: str, task_id=None,
                          parent_id=None, metrics=None, source_paths=None, metric_scope=None) -> dict:
        """Master-only scoped Pearson promotion; exact ties require fewer columns."""
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._promote_candidate_in_transaction(
                db, actor_id, validation_pearson=validation_pearson, n_columns=n_columns,
                feature_names=feature_names, candidate_signature=candidate_signature, task_id=task_id,
                parent_id=parent_id, metrics=metrics, source_paths=source_paths, metric_scope=metric_scope)

    def _promote_candidate_in_transaction(self, db, actor_id: str, *, validation_pearson, n_columns: int,
                                          feature_names: list[str], candidate_signature: str, task_id=None,
                                          parent_id=None, metrics=None, source_paths=None, metric_scope=None) -> dict:
        """Master-only: higher Pearson in [-1,1] wins; exact ties need fewer columns.

        On a scoped board metric_scope must match. A cited completed task's
        published top-level promotion fields must agree with the proposed values
        when present; missing fields retain compatibility with generic tasks.
        This detects accidental mismatches, not fabricated worker measurements.
        """
        if actor_id != self.master_id:
            raise PermissionError("Only the master may promote a champion")
        _name(candidate_signature, "candidate_signature")
        if metric_scope is not None:
            _name(metric_scope, "metric_scope")
        if isinstance(n_columns, bool) or not isinstance(n_columns, int) or n_columns < 0:
            raise ValueError("n_columns must be a nonnegative integer")
        if not isinstance(feature_names, list) or not all(isinstance(x, str) for x in feature_names):
            raise ValueError("feature_names must be a list of strings")
        try:
            score = float(validation_pearson)
            finite = math.isfinite(score) and not isinstance(validation_pearson, bool)
            valid = finite and -1 <= score <= 1
        except (TypeError, ValueError):
            score, valid, finite = None, False, False
        candidate = {"task_id": task_id, "candidate_signature": candidate_signature,
                     "feature_names": feature_names, "n_columns": n_columns,
                     "validation_pearson": score if valid else None, "parent_id": parent_id,
                     "metrics": metrics or {}, "source_paths": source_paths or [],
                     "promoted_by": actor_id, "promoted_at": time.time()}
        if metric_scope is not None:
            candidate["metric_scope"] = metric_scope
        encoded = _json(candidate)
        scope = db.execute("SELECT value FROM board_config WHERE key='metric_scope'").fetchone()
        if scope is not None and metric_scope != scope[0]:
            raise ValueError("Promotion metric_scope must match the configured board scope")
        if task_id is not None:
            task = db.execute("SELECT status,result_json FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if task is None or task[0] != "completed":
                raise ValueError("A candidate task must be completed before promotion")
            published = json.loads(task["result_json"])
            for field in ("validation_pearson", "n_columns", "candidate_signature", "feature_names",
                          "parent_id", "metric_scope"):
                if field in published and published[field] != candidate.get(field):
                    raise ValueError(f"Promotion {field} does not match the completed task result")
        row = db.execute("SELECT candidate_json FROM champion WHERE singleton=1").fetchone()
        current = None if row is None else json.loads(row[0])
        accepted = valid and (current is None or score > current["validation_pearson"] or
            (score == current["validation_pearson"] and n_columns < current["n_columns"]))
        if accepted:
            db.execute("INSERT OR REPLACE INTO champion VALUES (1,?)", (encoded,))
            db.execute("INSERT INTO promotions(candidate_json,created_at) VALUES (?,?)", (encoded, time.time()))
            return {"accepted": True, "reason": "initial champion" if current is None else
                    ("higher validation Pearson" if score > current["validation_pearson"] else
                     "equal validation Pearson with fewer columns"), "champion": candidate}
        reason = ("validation Pearson is not finite" if not finite else
                  "validation Pearson is outside [-1,1]") if not valid else (
            "validation Pearson regressed" if score < current["validation_pearson"] else
            "equal validation Pearson without fewer columns")
        archive_id = self._archive(db, status="rejected", task_id=task_id,
            feature_names=feature_names, candidate_signature=candidate_signature, parent_id=parent_id,
            reference_id=None if current is None else current["candidate_signature"],
            metrics={**(metrics or {}), "validation_pearson": score if valid else None},
            reason=reason, source_paths=source_paths)
        return {"accepted": False, "reason": reason, "champion": current, "archive_id": archive_id}
