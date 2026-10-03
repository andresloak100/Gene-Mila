import threading

from genemila.db import Database


def test_insert_update_roundtrip(tmp_path):
    db = Database(tmp_path / "x.db")
    eid = db.insert_experiment({"status": "queued", "hypothesis": "h", "feature_set_json": ["a", "b"],
                                "hyperparameters_json": {"alpha_grid": [1.0]}})
    assert eid == "EXP_0001"
    db.update_experiment(eid, val_metrics_json={"primary": 0.5}, primary_score=0.5, status="completed")
    rec = db.get_experiment(eid)
    assert rec["feature_set_json"] == ["a", "b"]
    assert rec["val_metrics_json"]["primary"] == 0.5
    assert db.best()["experiment_id"] == eid


def test_failed_experiments_are_preserved(tmp_path):
    db = Database(tmp_path / "x.db")
    eid = db.insert_experiment({"status": "queued", "hypothesis": "h"})
    db.update_experiment(eid, status="failed", failure_stage="test", failure_reason="NaN values")
    assert db.get_experiment(eid)["failure_reason"] == "NaN values"
    assert db.count_by_status() == {"failed": 1}


def test_concurrent_claims_are_exclusive(tmp_path):
    db = Database(tmp_path / "x.db")
    ids = [db.insert_experiment({"status": "queued", "hypothesis": f"h{i}", "priority": i % 3}) for i in range(40)]
    claimed, lock = [], threading.Lock()

    def worker(w):
        while True:
            rec = db.claim_next(f"W{w}")
            if rec is None:
                return
            with lock:
                claimed.append(rec["experiment_id"])

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(claimed) == sorted(ids)
    assert len(set(claimed)) == len(claimed)
    assert db.count_by_status() == {"claimed": 40}


def test_priority_order(tmp_path):
    db = Database(tmp_path / "x.db")
    db.insert_experiment({"status": "queued", "hypothesis": "low", "priority": 0})
    hi = db.insert_experiment({"status": "queued", "hypothesis": "high", "priority": 5})
    assert db.claim_next("W0")["experiment_id"] == hi


def test_lineage(tmp_path):
    db = Database(tmp_path / "x.db")
    a = db.insert_experiment({"status": "completed", "hypothesis": "base"})
    b = db.insert_experiment({"status": "completed", "hypothesis": "b", "parent_id": a})
    c = db.insert_experiment({"status": "completed", "hypothesis": "c", "parent_id": b})
    assert [e["experiment_id"] for e in db.lineage(c)] == [a, b, c]
