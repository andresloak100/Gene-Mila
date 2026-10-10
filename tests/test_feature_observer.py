"""Fake laboratory metadata exercises actual worker/board/master integration."""

from concurrent.futures import ThreadPoolExecutor
import copy
import json
import sqlite3
from types import SimpleNamespace

import pytest

from genemila.controller import Controller
from genemila.feature_board import FeatureBoard
from genemila.feature_observer import publish_worker_observation, review_worker_observations
from genemila.spec import ExperimentSpec
from genemila.worker import ExperimentFailure, Worker


@pytest.fixture
def lab(tmp_path):
    records, events = {}, []
    return SimpleNamespace(
        cfg={"feature_board": {"path": "board.sqlite", "metric_scope": "lab_oof_fixture_v1"}},
        run_dir=tmp_path, run_id="fixture", dataset="synthetic", split_id="one", cv_folds=5, cv_seed=0,
        selection="pearson_delta", records=records, events=events,
        db=SimpleNamespace(get_experiment=lambda eid: copy.deepcopy(records.get(eid)),
                           event=lambda *args, **kwargs: events.append((args, kwargs))),
    )


def candidate(lab, eid, score=.6, columns=3, status="completed"):
    lab.records[eid] = {"experiment_id": eid, "status": status, "primary_score": .999,
        "feature_set_json": ["mean_response", "fixture_feature"], "feature_params_json": {"fixture_feature": {"k": 3}},
        "config_hash": f"config:{eid}", "code_commit": f"commit:{eid}", "parent_id": None,
        "model_type": "ridge", "best_alpha": 1., "failure_stage": "shape", "failure_reason": "shape mismatch",
        "val_metrics_json": {"pearson_delta_cv": score, "primary": .999, "pearson_delta": .998,
                             "sealed_pearson": "DO_NOT_COPY"}, "query_metrics_json": {"primary": "DO_NOT_COPY"}}
    return {"n_features": columns, "feature_sources": ["mean_response", "dependency_only", "fixture_feature"]}


def board(lab):
    return FeatureBoard(lab.run_dir / "board.sqlite", metric_scope="lab_oof_fixture_v1")


def test_opt_in_requires_both_path_and_scope_and_old_behavior_creates_nothing(lab):
    lab.cfg = {}
    assert publish_worker_observation(lab, "unknown", "W0") is None
    assert review_worker_observations(lab) == []
    lab.cfg = {"feature_board": {"path": "board.sqlite"}}
    assert publish_worker_observation(lab, "unknown", "W0") is None
    assert not (lab.run_dir / "board.sqlite").exists()
    lab.cfg = {"feature_board": {"metric_scope": "explicit"}}
    with pytest.raises(ValueError, match="explicit board path"):
        review_worker_observations(lab)


def test_worker_publishes_and_master_retains_best_archives_regressions_without_lab_ranking_changes(lab):
    worker = Worker.__new__(Worker)
    worker.lab, worker.db, worker.worker_id = lab, lab.db, "W0"
    ctl = Controller.__new__(Controller)
    ctl.lab, ctl._next_feature_board_review = lab, 0.
    result = candidate(lab, "EXP_1", .6, 3)
    original = copy.deepcopy(lab.records)
    worker._publish_feature_observation("EXP_1", result)
    assert board(lab).champion() is None  # workers do not promote
    ctl._review_feature_observations(force=True)
    assert board(lab).champion()["validation_pearson"] == .6
    assert lab.records == original
    assert publish_worker_observation(lab, "EXP_1", "W0", result)["duplicate"] is True
    assert review_worker_observations(lab) == []
    for eid, score, columns in (("EXP_2", .59, 2), ("EXP_3", .61, 4), ("EXP_4", .61, 2)):
        result = candidate(lab, eid, score, columns)
        worker._publish_feature_observation(eid, result)
        ctl._review_feature_observations(force=True)
    champion = board(lab).champion()
    assert (champion["validation_pearson"], champion["n_columns"]) == (.61, 2)
    assert len(board(lab).archive()) == 1
    assert "regressed" in board(lab).archive()[0]["reason"]
    encoded = json.dumps(board(lab).tasks() + board(lab).archive() + [champion])
    assert "DO_NOT_COPY" not in encoded and "0.999" not in encoded and "0.998" not in encoded
    assert "dependency_only.py" in encoded


def test_failed_observation_is_archived_once_after_master_review(lab):
    candidate(lab, "EXP_fail", status="failed")
    publish_worker_observation(lab, "EXP_fail", "W0")
    assert board(lab).archive() == []
    first = review_worker_observations(lab)
    assert len(first) == 1 and first[0]["accepted"] is False
    assert board(lab).archive()[0]["reason"] == "shape: shape mismatch"
    assert review_worker_observations(lab) == []
    assert publish_worker_observation(lab, "EXP_fail", "W0")["duplicate"] is True
    assert len(board(lab).archive()) == 1


def test_changed_result_cannot_replace_canonical_completed_observation(lab):
    result = candidate(lab, "EXP_1")
    publish_worker_observation(lab, "EXP_1", "W0", result)
    lab.records["EXP_1"]["val_metrics_json"]["pearson_delta_cv"] = .7
    with pytest.raises(ValueError, match="conflicting result replay"):
        publish_worker_observation(lab, "EXP_1", "W0", result)
    assert len(board(lab).tasks()) == 1
    assert review_worker_observations(lab)[0]["champion"]["validation_pearson"] == .6


@pytest.mark.parametrize(("field", "value"), [("cv_seed", 11), ("cv_folds", 3),
                                               ("split_id", "other"), ("dataset", "other"),
                                               ("selection", "pearson_delta+r2_top")])
def test_protocol_mismatch_refuses_to_mix_results(lab, field, value):
    publish_worker_observation(lab, "EXP_1", "W0", candidate(lab, "EXP_1"))
    review_worker_observations(lab)
    before = board(lab).champion()
    setattr(lab, field, value)
    with pytest.raises(ValueError, match="protocol differs"):
        review_worker_observations(lab)
    assert board(lab).champion() == before


def test_existing_offline_results_are_not_assumed_to_share_the_protocol(lab):
    existing = board(lab)
    existing.promote_candidate("master", validation_pearson=.8, n_columns=1,
                               feature_names=["old"], candidate_signature="old", metric_scope="lab_oof_fixture_v1")
    with pytest.raises(ValueError, match="already has results without this observer protocol"):
        publish_worker_observation(lab, "EXP_1", "W0", candidate(lab, "EXP_1"))
    assert existing.champion()["candidate_signature"] == "old"


def test_review_and_acknowledgment_roll_back_together_on_canonical_task_mismatch(lab):
    for eid, score in (("EXP_1", .6), ("EXP_2", .5)):
        publish_worker_observation(lab, eid, "W0", candidate(lab, eid, score))
    path = lab.run_dir / "board.sqlite"
    with sqlite3.connect(path) as db:
        saved = db.execute("SELECT result_json FROM tasks WHERE task_id=2").fetchone()[0]
        altered = json.loads(saved)
        altered["validation_pearson"] = .9
        db.execute("UPDATE tasks SET result_json=? WHERE task_id=2", (json.dumps(altered),))
    with pytest.raises(ValueError, match="canonical board task result"):
        review_worker_observations(lab)
    assert board(lab).champion() is None and board(lab).archive() == []
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM external_observations WHERE reviewed_at IS NOT NULL").fetchone()[0] == 0
        db.execute("UPDATE tasks SET result_json=? WHERE task_id=2", (saved,))
    assert len(review_worker_observations(lab)) == 2
    assert board(lab).champion()["validation_pearson"] == .6
    assert len(board(lab).archive()) == 1


def test_eight_workers_can_publish_idempotently_before_master_review(lab):
    results = {f"EXP_{i}": candidate(lab, f"EXP_{i}", .4 + i / 100) for i in range(8)}

    def publish(i):
        eid = f"EXP_{i}"
        first = publish_worker_observation(lab, eid, f"W{i}", results[eid])
        second = publish_worker_observation(lab, eid, f"W{i}", results[eid])
        return first, second

    with ThreadPoolExecutor(max_workers=8) as workers:
        published = list(workers.map(publish, range(8)))
    assert all(not first["duplicate"] and second["duplicate"] for first, second in published)
    assert len(board(lab).tasks()) == 8
    assert len(review_worker_observations(lab)) == 8
    assert board(lab).champion()["validation_pearson"] == pytest.approx(.47)
    assert review_worker_observations(lab) == []


def test_invalid_measurement_is_reported_without_failing_or_changing_experiment(lab):
    worker = Worker.__new__(Worker)
    worker.lab, worker.db, worker.worker_id = lab, lab.db, "W0"
    result = candidate(lab, "EXP_bad", score=None)
    original = copy.deepcopy(lab.records)
    worker._publish_feature_observation("EXP_bad", result)
    assert lab.records == original
    assert any(event[0][0] == "feature_board_error" for event in lab.events)
    assert board(lab).tasks() == []


@pytest.mark.parametrize("fails", [False, True])
def test_actual_worker_finalization_publishes_success_or_failure_using_only_fakes(lab, monkeypatch, fails):
    import genemila.worker as worker_module

    lab.cfg["experiment"] = {"keep_all_alphas": True, "max_attempts": 1}
    lab.artifacts = lab.run_dir / "artifacts"
    lab.base_commit = "fixture"
    lab.store_files = lambda names: {}
    lab.trim_feature_cache = lambda: None
    lab.worktrees = SimpleNamespace(create=lambda eid: lab.run_dir, install_features=lambda *args: {},
                                     commit=lambda *args: "fixture_commit", remove=lambda *args: None)
    monkeypatch.setattr(worker_module, "check_diff", lambda *args: [])
    lab.evaluate_artifact = lambda path: {"metrics": {"primary": .99, "pearson_delta_cv": .55},
                                          "diagnostics": {}, "best_alpha": 1., "alpha_scores": []}
    spec = ExperimentSpec(experiment_id="EXP_final", hypothesis="Fake metadata finalization fixture.",
                          scientific_rationale="No feature computation or evaluator is called.",
                          feature_set=["mean_response"], status="claimed")
    record = spec.to_record(lab.dataset, lab.split_id, lab.run_id)
    lab.records[spec.experiment_id] = record
    worker = Worker.__new__(Worker)
    worker.lab, worker.db, worker.worker_id, worker.completed = lab, lab.db, "W0", 0
    worker._set = lambda eid, **fields: lab.records[eid].update(fields)

    def fake_run(*args):
        if fails:
            raise ExperimentFailure("experiment", "fixture computation failed")
        return ({"n_features": 1, "feature_sources": ["mean_response"], "timing": {}, "model_size_bytes": 1,
                 "coefficients": [{"alpha": 1., "coef": {"mean_response": 1.}}]},
                SimpleNamespace(cpu_s=.01, peak_rss_mb=1.))

    worker._run_experiment = fake_run
    assert worker.process(record) == ("failed" if fails else "completed")
    assert len(board(lab).tasks()) == 1 and board(lab).champion() is None
    assert lab.records[spec.experiment_id]["finished_at"] is not None
    reviewed = review_worker_observations(lab)
    assert len(reviewed) == 1
    if fails:
        assert "fixture computation failed" in board(lab).archive()[0]["reason"]
    else:
        assert board(lab).champion()["validation_pearson"] == .55
        assert lab.records[spec.experiment_id]["primary_score"] == .99
