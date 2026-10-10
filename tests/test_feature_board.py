from concurrent.futures import ThreadPoolExecutor
import math
import sqlite3
from threading import Barrier

import pytest

from genemila.feature_board import FeatureBoard


def test_two_workers_claim_unique_tasks_and_share_results(tmp_path):
    path = tmp_path / "board.sqlite"
    master = FeatureBoard(path)
    ids = [master.enqueue("ablation", {"feature_names": [f"f{i}"]}, parent_id="reference") for i in range(2)]
    barrier = Barrier(2)

    def work(worker):
        board = FeatureBoard(path)
        barrier.wait()
        task = board.claim(worker)
        board.complete(task["task_id"], worker, {"validation_pearson": 0.6, "n_columns": 1})
        board.post_message(worker, {"event": "result_ready"}, task_id=task["task_id"], recipient="master")
        return task["task_id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(work, ["worker-a", "worker-b"]))
    assert sorted(claimed) == ids
    assert master.claim("worker-c") is None
    assert all(master.result(tid) == {"validation_pearson": 0.6, "n_columns": 1} for tid in ids)
    assert all(task["status"] == "completed" and task["parent_id"] == "reference" for task in master.tasks())
    assert {m["sender"] for m in master.messages()} == {"worker-a", "worker-b"}
    assert len(master.messages(task_id=ids[0])) == 1
    assert master.champion() is None  # Publishing a strong result never auto-promotes.


def test_two_workers_cannot_claim_the_same_single_task(tmp_path):
    board = FeatureBoard(tmp_path / "board.sqlite")
    tid = board.enqueue("merge", {})
    barrier = Barrier(2)

    def claim(worker):
        barrier.wait()
        return board.claim(worker)

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, ["a", "b"]))
    assert [c["task_id"] for c in claims if c is not None] == [tid]


def test_only_owner_completes_and_failure_is_archived_without_deleting_sources(tmp_path):
    board = FeatureBoard(tmp_path / "board.sqlite")
    source = tmp_path / "feature.py"
    source.write_text("# Preserve the rejected candidate for future reuse.\n")
    tid = board.enqueue("prune", {"feature_names": ["feature"], "candidate_signature": "candidate-1",
                                 "source_paths": [str(source)], "reference_id": "baseline"}, parent_id="parent")
    board.claim("worker-a")
    with pytest.raises(PermissionError):
        board.complete(tid, "worker-b", {})
    archive_id = board.fail(tid, "worker-a", "source dependency missing")
    entry = board.archive()[0]
    assert entry["archive_id"] == archive_id and entry["status"] == "failed"
    assert entry["feature_names"] == ["feature"] and entry["candidate_signature"] == "candidate-1"
    assert entry["parent_id"] == "parent" and entry["reference_id"] == "baseline"
    assert entry["source_paths"] == [str(source)] and source.exists()
    with pytest.raises(ValueError):
        board.complete(tid, "worker-a", {})
    with sqlite3.connect(board.path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("UPDATE feature_archive SET reason='changed'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("DELETE FROM feature_archive")


def test_master_guard_rejects_regression_and_promotes_exact_ties_only_when_smaller(tmp_path):
    board = FeatureBoard(tmp_path / "board.sqlite")
    base = dict(feature_names=["a", "b"], candidate_signature="baseline", validation_pearson=0.6, n_columns=2)
    with pytest.raises(PermissionError):
        board.promote_candidate("worker-a", **base)
    assert board.promote_candidate("master", **base)["accepted"]
    regression = board.promote_candidate("master", **{**base, "candidate_signature": "regressed",
                                                      "validation_pearson": 0.599999999, "n_columns": 1})
    assert not regression["accepted"] and "regressed" in regression["reason"]
    same_size = board.promote_candidate("master", **{**base, "candidate_signature": "same"})
    assert not same_size["accepted"]
    compact = board.promote_candidate("master", **{**base, "candidate_signature": "compact", "n_columns": 1})
    assert compact["accepted"] and board.champion()["candidate_signature"] == "compact"
    stronger = board.promote_candidate("master", **{**base, "candidate_signature": "stronger", "validation_pearson": 0.61})
    assert stronger["accepted"]
    assert {e["candidate_signature"] for e in board.archive()} == {"regressed", "same"}
    assert all(e["reference_id"] == "baseline" for e in board.archive())


def test_concurrent_master_decisions_cannot_replace_a_stronger_champion(tmp_path):
    board = FeatureBoard(tmp_path / "board.sqlite")
    barrier = Barrier(2)

    def promote(score):
        barrier.wait()
        return board.promote_candidate("master", feature_names=["a"], candidate_signature=str(score),
                                       validation_pearson=score, n_columns=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(promote, [0.61, 0.62]))
    assert board.champion()["validation_pearson"] == 0.62


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, None, True])
def test_nonfinite_pearson_never_promotes_and_is_json_safe(tmp_path, invalid):
    board = FeatureBoard(tmp_path / "board.sqlite")
    decision = board.promote_candidate("master", feature_names=["x"], candidate_signature="invalid",
                                       validation_pearson=invalid, n_columns=1)
    assert not decision["accepted"] and board.champion() is None
    assert board.archive()[0]["metrics"]["validation_pearson"] is None


def test_candidate_task_must_publish_before_master_promotion(tmp_path):
    board = FeatureBoard(tmp_path / "board.sqlite")
    tid = board.enqueue("candidate", {})
    candidate = dict(task_id=tid, feature_names=["x"], candidate_signature="x", validation_pearson=0.6, n_columns=1)
    with pytest.raises(ValueError, match="completed"):
        board.promote_candidate("master", **candidate)
    board.claim("worker-a")
    board.complete(tid, "worker-a", {"validation_pearson": 0.6})
    assert board.promote_candidate("master", **candidate)["accepted"]


@pytest.mark.parametrize("payload", [{"nested": {"api_key": "secret"}}, {"raw_labels": [1, 2]},
                                      {"score": math.nan}, {"bad": object()}])
def test_metadata_contract_rejects_labels_credentials_and_non_json(tmp_path, payload):
    board = FeatureBoard(tmp_path / "board.sqlite")
    with pytest.raises(ValueError):
        board.enqueue("candidate", payload)
    assert board.tasks() == []


@pytest.mark.parametrize("invalid", [-1.01, 1.01, 2.0])
def test_out_of_range_pearson_cannot_be_champion(tmp_path, invalid):
    board = FeatureBoard(tmp_path / "board.sqlite")
    decision = board.promote_candidate("master", validation_pearson=invalid, n_columns=1,
                                       feature_names=["x"], candidate_signature="invalid-range")
    assert not decision["accepted"] and "outside [-1,1]" in decision["reason"]
    assert board.champion() is None and board.archive()[0]["metrics"]["validation_pearson"] is None


@pytest.mark.parametrize("changed", [
    {"validation_pearson": .7}, {"n_columns": 2}, {"candidate_signature": "other"},
    {"feature_names": ["different"]}, {"parent_id": "different"},
])
def test_promotion_must_match_published_task_fields(tmp_path, changed):
    board = FeatureBoard(tmp_path / "board.sqlite")
    tid = board.enqueue("candidate", {})
    candidate = dict(validation_pearson=.6, n_columns=1, candidate_signature="sig", feature_names=["x"],
                     parent_id="parent")
    board.claim("worker")
    board.complete(tid, "worker", candidate)
    with pytest.raises(ValueError, match="does not match"):
        board.promote_candidate("master", task_id=tid, **{**candidate, **changed})
    assert board.champion() is None
    assert board.promote_candidate("master", task_id=tid, **candidate)["accepted"]


def test_explicit_scope_upgrade_preserves_history_and_enforces_existing_handles(tmp_path):
    path = tmp_path / "board.sqlite"
    original = FeatureBoard(path)
    candidate = dict(validation_pearson=.6, n_columns=2, feature_names=["x"], candidate_signature="old")
    original.promote_candidate("master", **candidate)
    with sqlite3.connect(path) as db:
        old_promotion = db.execute("SELECT candidate_json FROM promotions").fetchone()[0]
    scoped = FeatureBoard(path, metric_scope="public_cv50_seed0_v1")
    assert scoped.metric_scope == "public_cv50_seed0_v1"
    assert FeatureBoard(path).metric_scope == scoped.metric_scope
    with pytest.raises(ValueError, match="metric_scope"):
        original.promote_candidate("master", **{**candidate, "validation_pearson": .9})
    with pytest.raises(ValueError, match="metric_scope"):
        scoped.promote_candidate("master", metric_scope="cv67", **candidate)
    assert original.promote_candidate("master", metric_scope=scoped.metric_scope,
                                       **{**candidate, "candidate_signature": "compact", "n_columns": 1})["accepted"]
    assert scoped.champion()["metric_scope"] == scoped.metric_scope
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT candidate_json FROM promotions ORDER BY promotion_id LIMIT 1").fetchone()[0] == old_promotion
    with pytest.raises(ValueError, match="another metric_scope"):
        FeatureBoard(path, metric_scope="cv67")


def test_task_scope_cannot_be_relabelled_during_promotion(tmp_path):
    board = FeatureBoard(tmp_path / "board.sqlite", metric_scope="cv50")
    tid = board.enqueue("candidate", {})
    board.claim("worker")
    board.complete(tid, "worker", {"validation_pearson": .7, "metric_scope": "cv67"})
    with pytest.raises(ValueError, match="does not match"):
        board.promote_candidate("master", task_id=tid, validation_pearson=.7, n_columns=1,
                                feature_names=["x"], candidate_signature="sig", metric_scope="cv50")
