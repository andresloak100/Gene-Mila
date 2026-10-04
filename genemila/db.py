"""Shared experiment database (SQLite, WAL mode, one connection per thread).

It is the single source of truth for the queue, every experiment's record
(including failures, which are scientifically informative), the feature
registry, LLM usage, and planner rounds.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY, started_at REAL, deadline REAL, finished_at REAL,
    workers INTEGER, dataset TEXT, split_id TEXT, base_commit TEXT,
    config_json TEXT, summary_json TEXT
);
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    run_id TEXT, parent_id TEXT, created_at REAL, started_at REAL, finished_at REAL,
    status TEXT NOT NULL,            -- queued|claimed|implementing|testing|running|completed|failed|rejected|killed|duplicate
    priority REAL DEFAULT 0,
    kind TEXT,                       -- baseline|new_feature|config
    category TEXT,                   -- baseline|explore|exploit|risky
    hypothesis TEXT, rationale TEXT, hypothesis_group TEXT,
    proposed_feature_json TEXT,      -- {name, description, implementation_hint}
    feature_set_json TEXT, feature_params_json TEXT, new_feature TEXT,
    allowed_files_json TEXT, files_changed_json TEXT,
    model_type TEXT, hyperparameters_json TEXT, seed INTEGER,
    cpu_limit_s REAL, ram_limit_mb REAL, timeout_s REAL,
    dataset TEXT, split_id TEXT,
    proposer TEXT,                   -- who proposed the hypothesis (planner model / sweep / baseline)
    provider TEXT, model TEXT, worker_id TEXT, attempts INTEGER DEFAULT 0, escalated INTEGER DEFAULT 0,
    val_metrics_json TEXT, diagnostics_json TEXT, primary_score REAL, parent_score REAL,
    delta_from_parent REAL, best_alpha REAL, timing_json TEXT, model_size_bytes INTEGER,
    cpu_s REAL, wall_s REAL, peak_rss_mb REAL,
    failure_stage TEXT, failure_reason TEXT, flags_json TEXT,
    code_commit TEXT, code_hash TEXT, config_hash TEXT, duplicate_of TEXT,
    artifact_dir TEXT, query_metrics_json TEXT,
    llm_input_tokens INTEGER DEFAULT 0, llm_output_tokens INTEGER DEFAULT 0,
    llm_cached_tokens INTEGER DEFAULT 0, llm_cost_usd REAL DEFAULT 0, llm_calls INTEGER DEFAULT 0,
    heartbeat REAL
);
CREATE INDEX IF NOT EXISTS idx_exp_status ON experiments(status, priority, created_at);
CREATE TABLE IF NOT EXISTS features (
    name TEXT PRIMARY KEY, version INTEGER, description TEXT, rationale TEXT,
    implementation_path TEXT, code_hash TEXT, inputs_json TEXT, params_json TEXT,
    dim INTEGER, dependencies_json TEXT, creator_experiment TEXT, compute_cpu_s REAL,
    builtin INTEGER DEFAULT 0, created_at REAL
);
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, role TEXT, provider TEXT, model TEXT,
    experiment_id TEXT, worker_id TEXT, purpose TEXT,
    input_tokens INTEGER, output_tokens INTEGER, cached_tokens INTEGER,
    cost_usd REAL, latency_s REAL, ok INTEGER, error TEXT
);
CREATE TABLE IF NOT EXISTS planner_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, provider TEXT, model TEXT,
    state_chars INTEGER, n_proposed INTEGER, n_queued INTEGER, synthesis TEXT, raw_path TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, level TEXT, kind TEXT,
    experiment_id TEXT, message TEXT
);
"""

JSON_FIELDS = {c for c in (
    "proposed_feature_json feature_set_json feature_params_json allowed_files_json files_changed_json "
    "hyperparameters_json val_metrics_json diagnostics_json timing_json flags_json query_metrics_json"
).split()}

ACTIVE = ("claimed", "implementing", "testing", "running")
TERMINAL = ("completed", "failed", "rejected", "killed", "duplicate")


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._local = threading.local()
        self.lock = threading.Lock()  # serialises claims across threads
        with self.conn:
            self.conn.executescript(SCHEMA)

    @property
    def conn(self) -> sqlite3.Connection:
        c = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(self.path, timeout=30, isolation_level=None, check_same_thread=False)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA busy_timeout=30000")
            self._local.conn = c
        return c

    def close_thread_conn(self) -> None:
        """Close this thread's connection (short-lived threads such as planner rounds)."""
        c = getattr(self._local, "conn", None)
        if c is not None:
            c.close()
            self._local.conn = None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _encode(fields: dict) -> dict:
        out = {}
        for k, v in fields.items():
            out[k] = json.dumps(v) if k in JSON_FIELDS and v is not None and not isinstance(v, str) else v
        return out

    @staticmethod
    def decode(row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        d = dict(row)
        for k in list(d):
            if k in JSON_FIELDS and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except json.JSONDecodeError:
                    pass
        return d

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, tuple(params))

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict]:
        return [self.decode(r) for r in self.conn.execute(sql, tuple(params)).fetchall()]

    # -------------------------------------------------------------- experiments
    def next_experiment_id(self) -> str:
        with self.lock:
            row = self.conn.execute(
                "SELECT experiment_id FROM experiments WHERE experiment_id LIKE 'EXP_%' "
                "ORDER BY CAST(substr(experiment_id, 5) AS INTEGER) DESC LIMIT 1").fetchone()
            n = int(row[0][4:]) + 1 if row else 1
            # reserve the id immediately to avoid races
            self.conn.execute("INSERT INTO experiments(experiment_id, status, created_at) VALUES (?, 'reserved', ?)",
                              (f"EXP_{n:04d}", time.time()))
            return f"EXP_{n:04d}"

    def insert_experiment(self, record: dict) -> str:
        record = dict(record)
        if not record.get("experiment_id"):
            record["experiment_id"] = self.next_experiment_id()
        record.setdefault("created_at", time.time())
        record.setdefault("status", "queued")
        enc = self._encode(record)
        cols = ", ".join(enc)
        marks = ", ".join("?" for _ in enc)
        updates = ", ".join(f"{k}=excluded.{k}" for k in enc if k != "experiment_id")
        self.conn.execute(
            f"INSERT INTO experiments ({cols}) VALUES ({marks}) ON CONFLICT(experiment_id) DO UPDATE SET {updates}",
            tuple(enc.values()))
        return record["experiment_id"]

    def update_experiment(self, experiment_id: str, **fields) -> None:
        if not fields:
            return
        enc = self._encode(fields)
        sets = ", ".join(f"{k}=?" for k in enc)
        self.conn.execute(f"UPDATE experiments SET {sets} WHERE experiment_id=?", (*enc.values(), experiment_id))

    def get_experiment(self, experiment_id: str) -> dict | None:
        return self.decode(self.conn.execute("SELECT * FROM experiments WHERE experiment_id=?",
                                             (experiment_id,)).fetchone())

    def claim_next(self, worker_id: str) -> dict | None:
        """Atomically move the highest-priority queued experiment to 'claimed'."""
        with self.lock:
            c = self.conn
            c.execute("BEGIN IMMEDIATE")
            try:
                row = c.execute("SELECT experiment_id FROM experiments WHERE status='queued' "
                                "ORDER BY priority DESC, created_at ASC LIMIT 1").fetchone()
                if row is None:
                    c.execute("COMMIT")
                    return None
                now = time.time()
                c.execute("UPDATE experiments SET status='claimed', worker_id=?, started_at=?, heartbeat=?, "
                          "attempts=attempts+1 WHERE experiment_id=? AND status='queued'",
                          (worker_id, now, now, row[0]))
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise
        return self.get_experiment(row[0])

    def count_by_status(self) -> dict[str, int]:
        rows = self.conn.execute("SELECT status, COUNT(*) FROM experiments GROUP BY status").fetchall()
        return {r[0]: r[1] for r in rows}

    def completed(self, order_by_score: bool = True) -> list[dict]:
        sql = "SELECT * FROM experiments WHERE status='completed'"
        if order_by_score:
            sql += " ORDER BY primary_score DESC"
        return self.query(sql)

    def best(self) -> dict | None:
        rows = self.query("SELECT * FROM experiments WHERE status='completed' AND primary_score IS NOT NULL "
                          "ORDER BY primary_score DESC, finished_at ASC LIMIT 1")
        return rows[0] if rows else None

    def find_by_config_hash(self, config_hash: str) -> dict | None:
        rows = self.query("SELECT * FROM experiments WHERE config_hash=? AND status IN "
                          "('queued','claimed','implementing','testing','running','completed') LIMIT 1",
                          (config_hash,))
        return rows[0] if rows else None

    def lineage(self, experiment_id: str) -> list[dict]:
        chain, seen = [], set()
        cur = self.get_experiment(experiment_id)
        while cur and cur["experiment_id"] not in seen:
            seen.add(cur["experiment_id"])
            chain.append(cur)
            cur = self.get_experiment(cur["parent_id"]) if cur.get("parent_id") else None
        return list(reversed(chain))

    # ----------------------------------------------------------------- features
    def upsert_feature(self, meta: dict) -> None:
        enc = {
            "name": meta["name"], "version": meta.get("version", 1), "description": meta.get("description"),
            "rationale": meta.get("rationale"), "implementation_path": meta.get("implementation_path"),
            "code_hash": meta.get("code_hash"), "inputs_json": json.dumps(meta.get("inputs", [])),
            "params_json": json.dumps(meta.get("params", {})), "dim": meta.get("dim", 1),
            "dependencies_json": json.dumps(meta.get("dependencies", [])),
            "creator_experiment": meta.get("creator_experiment"), "compute_cpu_s": meta.get("compute_cpu_s"),
            "builtin": int(meta.get("builtin", 0)), "created_at": time.time(),
        }
        cols = ", ".join(enc)
        self.conn.execute(f"INSERT OR REPLACE INTO features ({cols}) VALUES ({', '.join('?' * len(enc))})",
                          tuple(enc.values()))

    def features(self) -> list[dict]:
        rows = self.query("SELECT * FROM features ORDER BY created_at")
        for r in rows:
            for k in ("inputs_json", "params_json", "dependencies_json"):
                r[k[:-5]] = json.loads(r.pop(k) or "null")
        return rows

    def feature(self, name: str) -> dict | None:
        rows = [f for f in self.features() if f["name"] == name]
        return rows[0] if rows else None

    # -------------------------------------------------------------- usage/events
    def log_llm_call(self, **fields) -> None:
        fields.setdefault("ts", time.time())
        cols = ", ".join(fields)
        self.conn.execute(f"INSERT INTO llm_calls ({cols}) VALUES ({', '.join('?' * len(fields))})",
                          tuple(fields.values()))
        if fields.get("experiment_id"):
            self.conn.execute(
                "UPDATE experiments SET llm_input_tokens=llm_input_tokens+?, llm_output_tokens=llm_output_tokens+?, "
                "llm_cached_tokens=llm_cached_tokens+?, llm_cost_usd=llm_cost_usd+?, llm_calls=llm_calls+1 "
                "WHERE experiment_id=?",
                (fields.get("input_tokens") or 0, fields.get("output_tokens") or 0, fields.get("cached_tokens") or 0,
                 fields.get("cost_usd") or 0.0, fields["experiment_id"]))

    def llm_totals(self, role: str | None = None) -> dict:
        sql = ("SELECT COUNT(*) calls, COALESCE(SUM(input_tokens),0) input_tokens, "
               "COALESCE(SUM(output_tokens),0) output_tokens, COALESCE(SUM(cached_tokens),0) cached_tokens, "
               "COALESCE(SUM(cost_usd),0) cost_usd, COALESCE(SUM(1-ok),0) failed_calls FROM llm_calls")
        rows = self.query(sql + (" WHERE role=?" if role else ""), (role,) if role else ())
        return rows[0]

    def event(self, kind: str, message: str, experiment_id: str | None = None, level: str = "info") -> None:
        self.conn.execute("INSERT INTO events (ts, level, kind, experiment_id, message) VALUES (?,?,?,?,?)",
                          (time.time(), level, kind, experiment_id, message[:4000]))
