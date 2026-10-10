"""Full compact flow on the generated test fixture; zero final oracle/API calls."""

import json
from pathlib import Path
import threading

from genemila.curation_scheduler import CurationScheduler
from genemila.feature_board import FeatureBoard
from genemila.feature_observer import review_worker_observations
from genemila.spec import ExperimentSpec
from genemila.worker import Worker


def test_generated_fixture_worker_curation_selection_and_failure_archive(lab_factory):
    lab = lab_factory(curation__enabled=True, feature_board__path="board.sqlite",
                      feature_board__metric_scope="synthetic_compact_flow")
    base = ExperimentSpec(hypothesis="Fit a reproducible reference on generated test data",
        scientific_rationale="Exercise the full integration without an external model provider",
        feature_set=["control_mean", "mean_response", "is_target"],
        hyperparameters={"alpha_grid": [1.]}, proposer="fixture")
    eid, status = lab.queue(base)
    assert status == "queued"
    worker = Worker(lab, "W0", None, None, threading.Semaphore(1), queue_lane="curation")
    assert worker.process(lab.db.claim_next("W0")) == "completed"
    scheduler = CurationScheduler(lab, workers=8)
    queued = scheduler.maybe_queue()
    assert queued
    screen = lab.db.claim_next("W0", lane="curation")
    assert screen["hyperparameters_json"]["column_selection"] == {"method": "variance"}
    assert worker.process(screen) == "completed"
    record = lab.db.get_experiment(screen["experiment_id"])
    artifact = json.loads((Path(record["artifact_dir"]) / "result.json").read_text())
    assert artifact["n_features"] <= artifact["n_raw_features"]
    assert len(artifact["cv_column_selection"]) == lab.cv_folds
    policy = lab.compact_selection()
    assert policy["fallback_reason"] is None
    assert policy["selected_id"] == lab.best()["experiment_id"]
    assert lab.db.best()["experiment_id"] == policy["raw_accuracy_champion_id"]
    assert lab.best()["primary_score"] >= lab.db.get_experiment(eid)["primary_score"]

    failed = ExperimentSpec(hypothesis="Test explicit rejection of an empty sparse support",
        scientific_rationale="An extreme penalty deliberately exercises the failure archive",
        parent_experiment_id=eid, feature_set=base.feature_set, proposer="fixture",
        hyperparameters={"alpha_grid": [1.], "column_selection": {"method": "lasso", "alpha": 1e8}})
    bad_id, status = lab.queue(failed)
    assert status == "queued"
    assert worker.process(lab.db.get_experiment(bad_id)) == "failed"
    assert "empty" in lab.db.get_experiment(bad_id)["failure_reason"].lower()
    review_worker_observations(lab)
    board = FeatureBoard(lab.run_dir / "board.sqlite", metric_scope="synthetic_compact_flow")
    assert any("empty" in row["reason"].lower() for row in board.archive())
    assert lab.db.query("SELECT * FROM llm_calls") == []
    assert lab.oracle.queries == []
