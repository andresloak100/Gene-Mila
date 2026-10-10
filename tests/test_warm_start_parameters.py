"""Continuation tests use fabricated metadata only: no labels, feature execution, or LLM calls."""

import json

import pytest

from genemila.benchmark import PRIMARY_METRIC
from genemila.db import Database
from genemila.features.registry import FeatureDependencyError
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


def _composite_winner(source):
    for name, dependencies in (("leaf", []), ("middle", ["leaf"]), ("composite", ["middle"])):
        code = f"raise AssertionError('must not execute {name}')\n"
        (source.store / f"{name}.py").write_text(code)
        source.db.upsert_feature({"name": name, "params": {"scale": 1}, "dependencies": dependencies,
                                  "creator_experiment": "EXP_0001", "code_hash": name})
    winner = ExperimentSpec(
        experiment_id="EXP_0001", hypothesis="A composite is the prior winning model.",
        scientific_rationale="Metadata fixture tests closure preservation without execution.",
        feature_set=["mean_response", "composite"], feature_params={"leaf": {"scale": 7}},
        hyperparameters={"alpha_grid": [1.]}, status="completed")
    record = winner.to_record(source.dataset, source.split_id, source.run_id)
    record["primary_score"] = 0.6
    source.db.insert_experiment(record)
    return winner


def test_exact_warm_start_imports_dependency_only_sources_and_params(tmp_path):
    source, target = _metadata_lab(tmp_path / "source"), _metadata_lab(tmp_path / "target")
    try:
        winner = _composite_winner(source)
        info = target.warm_start(source.run_dir, strict=True)
        queued = target.db.get_experiment(info["start_experiment"])
        assert queued["feature_set_json"] == winner.feature_set
        assert queued["feature_params_json"] == {"leaf": {"scale": 7}}
        assert set(info["imported"]) == {"leaf", "middle", "composite"}
        assert info["dropped_features"] == [] and info["missing_sources"] == {}
        assert info["strict"] is True
        assert set(target.store_files(queued["feature_set_json"])) == {"leaf", "middle", "composite"}
    finally:
        source.db.close_thread_conn()
        target.db.close_thread_conn()


def test_exact_warm_start_missing_dependency_fails_before_import_or_queue(tmp_path):
    source, target = _metadata_lab(tmp_path / "source"), _metadata_lab(tmp_path / "target")
    try:
        _composite_winner(source)
        (source.store / "leaf.py").unlink()
        with pytest.raises(FeatureDependencyError, match="exact warm start.*composite.*leaf"):
            target.warm_start(source.run_dir, strict=True)
        assert list(target.store.iterdir()) == []
        assert target.db.query("SELECT * FROM experiments") == []
    finally:
        source.db.close_thread_conn()
        target.db.close_thread_conn()


def test_partial_warm_start_reports_consumer_dropped_for_missing_input(tmp_path):
    source, target = _metadata_lab(tmp_path / "source"), _metadata_lab(tmp_path / "target")
    try:
        _composite_winner(source)
        (source.store / "leaf.py").unlink()
        info = target.warm_start(source.run_dir)
        queued = target.db.get_experiment(info["start_experiment"])
        assert queued["feature_set_json"] == ["mean_response"]
        assert queued["feature_params_json"] == {}
        assert info["dropped_features"] == ["composite"]
        assert "leaf" in info["missing_sources"]["composite"]
    finally:
        source.db.close_thread_conn()
        target.db.close_thread_conn()


def test_exact_warm_start_rejects_conflicting_existing_dependency(tmp_path):
    source, target = _metadata_lab(tmp_path / "source"), _metadata_lab(tmp_path / "target")
    try:
        _composite_winner(source)
        target.db.upsert_feature({"name": "leaf", "params": {"scale": 1}, "dependencies": [], "code_hash": "other"})
        (target.store / "leaf.py").write_text("raise AssertionError('different source')\n")
        with pytest.raises(FeatureDependencyError, match="exact warm start.*existing source 'leaf' differs"):
            target.warm_start(source.run_dir, strict=True)
        assert target.db.query("SELECT * FROM experiments") == []
        assert {p.name for p in target.store.iterdir()} == {"leaf.py"}
    finally:
        source.db.close_thread_conn()
        target.db.close_thread_conn()


def test_config_hash_tracks_transitive_code_defaults_params_and_availability(tmp_path):
    lab = _metadata_lab(tmp_path / "lab")
    try:
        spec = _composite_winner(lab)
        original = lab.config_hash_for(spec)
        leaf = lab.db.feature("leaf")
        lab.db.upsert_feature({**leaf, "code_hash": "new_leaf_source"})
        assert lab.config_hash_for(spec) != original
        lab.db.upsert_feature(leaf)
        assert lab.config_hash_for(spec) == original
        lab.db.upsert_feature({**leaf, "params": {"scale": 1, "power": 2}})
        assert lab.config_hash_for(spec) != original
        lab.db.upsert_feature(leaf)
        spec.feature_params["leaf"]["scale"] = 8
        assert lab.config_hash_for(spec) != original
        spec.feature_params["leaf"]["scale"] = 7
        assert lab.config_hash_for(spec) == original
        (lab.store / "leaf.py").unlink()
        assert lab.config_hash_for(spec) != original
        # Invalid proposals still get identities so the queue can archive their rejection.
        spec.feature_set = ["unknown_feature"]
        assert lab.config_hash_for(spec).startswith("C_")
    finally:
        lab.db.close_thread_conn()


@pytest.mark.parametrize("selector", [
    {"method": "lasso", "alpha": .003, "max_iter": 4000},
    {"method": "elasticnet", "alpha": .002, "l1_ratio": .7, "max_iter": 3000},
    {"method": "variance"},
])
def test_warm_start_preserves_column_selector_feature_order_and_seed(tmp_path, selector):
    source, target = _metadata_lab(tmp_path / "source"), _metadata_lab(tmp_path / "target")
    try:
        winner = ExperimentSpec(
            experiment_id="EXP_0001", hypothesis="A selected column model is the prior winner.",
            scientific_rationale="Synthetic continuation must keep the fitted model's selector configuration.",
            feature_set=["is_target", "mean_response"], model_type="ridge", seed=17,
            hyperparameters={"alpha_grid": [3., 30.], "column_selection": selector}, status="completed")
        record = winner.to_record(source.dataset, source.split_id, source.run_id)
        record["primary_score"] = .6
        source.db.insert_experiment(record)
        # Metadata-only legacy callers intentionally have no cfg attribute.
        assert not hasattr(target, "cfg")
        info = target.warm_start(source.run_dir, strict=True)
        queued = target.db.get_experiment(info["start_experiment"])
        assert info["start_status"] == "queued"
        assert queued["hyperparameters_json"] == winner.hyperparameters
        assert queued["feature_set_json"] == ["is_target", "mean_response"]
        assert queued["model_type"] == "ridge" and queued["seed"] == 17
        assert source.db.get_experiment("EXP_0001")["hyperparameters_json"] == winner.hyperparameters
    finally:
        source.db.close_thread_conn()
        target.db.close_thread_conn()
