"""Continuation tests use fabricated metadata only: no labels, feature execution, or LLM calls."""

import json

import pytest

from genemila.benchmark import PRIMARY_METRIC
from genemila.db import Database
from genemila.lab import Lab
from genemila.spec import ExperimentSpec


def _metadata_lab(run_dir):
    """Construct only the metadata/store/queue portion of a lab, without opening a dataset."""
    lab = object.__new__(Lab)
    lab.run_dir = run_dir
    lab.run_dir.mkdir()
    lab.store = run_dir / "feature_store"
    lab.store.mkdir()
    lab.db = Database(run_dir / "lab.db")
    lab.run_id = run_dir.name
    lab.dataset = "synthetic_metadata"
    lab.split_id = "synthetic_split"
    lab.selection = PRIMARY_METRIC
    lab.cv_folds = 0
    lab.limits = {"cpu_limit_s": 600, "ram_limit_mb": 4096, "timeout_s": 300}
    lab._register_builtins()
    lab.db.execute("INSERT INTO runs (run_id, dataset, split_id, config_json) VALUES (?, ?, ?, ?)",
                   (lab.run_id, lab.dataset, lab.split_id,
                    json.dumps({"experiment": {"selection": PRIMARY_METRIC}})))
    return lab


@pytest.mark.parametrize("missing_feature", [False, True])
def test_warm_start_preserves_parameters_and_seed_for_surviving_features(tmp_path, missing_feature):
    source = _metadata_lab(tmp_path / "source")
    target = _metadata_lab(tmp_path / "target")
    try:
        feature_name = "neighbour_transfer"
        code = "raise AssertionError('Metadata continuation must not execute feature code')\n"
        (source.store / f"{feature_name}.py").write_text(code)
        source.db.upsert_feature({"name": feature_name, "params": {"k": 5, "power": 1},
                                  "creator_experiment": "EXP_0001", "code_hash": "fixture"})
        feature_set = ["mean_response", feature_name]
        overrides = {feature_name: {"k": 3, "power": 2}}
        if missing_feature:
            source.db.upsert_feature({"name": "missing_transfer", "params": {"m": 20}})
            feature_set.append("missing_transfer")
            overrides["missing_transfer"] = {"m": 80}
        winner = ExperimentSpec(
            experiment_id="EXP_0001", hypothesis="A parameterized transfer is the prior winning model.",
            scientific_rationale="Synthetic metadata tests preservation of a tuned configuration.",
            feature_set=feature_set, feature_params=overrides, seed=17,
            hyperparameters={"alpha_grid": [8000]}, status="completed")
        record = winner.to_record(source.dataset, source.split_id, source.run_id)
        record["primary_score"] = 0.6
        source.db.insert_experiment(record)

        info = target.warm_start(source.run_dir)

        assert info["start_status"] == "queued"
        queued = target.db.get_experiment(info["start_experiment"])
        assert queued["feature_set_json"] == ["mean_response", feature_name]
        assert queued["feature_params_json"] == {feature_name: {"k": 3, "power": 2}}
        assert queued["seed"] == 17
        assert queued["hyperparameters_json"] == {"alpha_grid": [8000]}
        assert (target.store / f"{feature_name}.py").read_text() == code
        assert target.db.feature(feature_name)["params"] == {"k": 5, "power": 1}
        assert info["missing"] == (["missing_transfer"] if missing_feature else [])
        assert source.db.get_experiment("EXP_0001")["feature_params_json"] == overrides
    finally:
        source.db.close_thread_conn()
        target.db.close_thread_conn()
