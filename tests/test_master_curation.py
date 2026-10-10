"""Scheduling and metadata tests only; never initialize a Lab or run an evaluator."""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import threading

import pytest

from genemila import exploit
from genemila.controller import Controller
from genemila.curation_scheduler import CurationScheduler, PROPOSER, candidates
from genemila.db import Database
from genemila.spec import ExperimentSpec, config_hash, validate_spec
from genemila.worker import Worker


class MetadataLab:
    def __init__(self, path, **curation):
        self.run_dir = path
        path.mkdir()
        self.db = Database(path / "lab.db")
        self.cfg = {"curation": {"enabled": True, "reserved_workers": 2,
                                "max_candidates_per_round": 4, "interval_s": 60, **curation},
                    "run": {"cpu_slots": 8, "status_interval_s": 5},
                    "experiment": {"default_alpha_grid": [0.1, 1., 10.]},
                    "schedule": {"python_exploit": False}, "worker": {},
                    "budget": {"max_planner_usd": 1.}}
        self.stop_event = threading.Event()
        self.run_id = "synthetic"
        self.dataset, self.split_id = "synthetic", "fixture"
        self.selection, self.cv_folds, self.cv_seed = "pearson_delta", 5, 7
        self.gateway = SimpleNamespace(role_caps={"worker": 0., "planner": 0.})
        self.limits = {"cpu_limit_s": 600., "ram_limit_mb": 4096., "timeout_s": 300.}
        for name, dim, deps in [("is_target", 1, []), ("big_block", 50, ["leaf"]),
                                ("small_a", 1, []), ("small_b", 2, []), ("small_c", 3, []),
                                ("leaf", 1, [])]:
            self.db.upsert_feature({"name": name, "dim": dim, "dependencies": deps})
        self.parent = self.add_parent()

    def add_parent(self, score=.5, selector=None):
        hp = {"alpha_grid": [.1, 1., 10.], "cv_folds": 5, "cv_seed": 7}
        if selector is not None:
            hp["column_selection"] = selector
        return self.db.insert_experiment({"status": "completed", "kind": "config", "model_type": "ridge",
            "primary_score": score, "feature_set_json": ["is_target", "big_block", "small_a", "small_b", "small_c"],
            "feature_params_json": {"leaf": {"scale": 7}, "big_block": {"power": 2}},
            "hyperparameters_json": hp, "seed": 19, "best_alpha": 1.,
            "hypothesis": "Synthetic reference model for metadata scheduling tests.",
            "rationale": "Fabricated metadata avoids any data access or execution."})

    def known_features(self):
        return {item["name"] for item in self.db.features()}

    def best(self):
        return self.db.best()

    def config_hash_for(self, spec):
        return config_hash(spec, {name: "synthetic" for name in self.known_features()}, self.split_id)

    def queue(self, spec):
        parent = self.db.get_experiment(spec.parent_experiment_id) if spec.parent_experiment_id else None
        validate_spec(spec, self.known_features(), self.limits, parent)
        digest = self.config_hash_for(spec)
        if self.db.query("SELECT 1 FROM experiments WHERE config_hash=?", (digest,)):
            raise AssertionError("Scheduler should suppress every duplicate before queueing")
        record = spec.to_record(self.dataset, self.split_id, self.run_id)
        record["config_hash"] = digest
        return self.db.insert_experiment(record), "queued"


@pytest.fixture
def lab(tmp_path):
    value = MetadataLab(tmp_path / "metadata")
    yield value
    value.db.close_thread_conn()


def add_discovery(lab, count=20, priority=1000):
    return [lab.db.insert_experiment({"status": "queued", "kind": "new_feature", "proposer": "llm:fixture",
                                      "priority": priority, "hypothesis": f"Synthetic queued idea {i}"})
            for i in range(count)]


def finish_round(lab, ids):
    for eid in ids:
        lab.db.update_experiment(eid, status="failed", failure_stage="synthetic_fixture")


def test_reserved_workers_claim_pruning_from_busy_discovery_queue_and_borrow(lab):
    discovery = add_discovery(lab)
    scheduler = CurationScheduler(lab, 8)
    pruning = scheduler.maybe_queue(now=100)
    assert len(pruning) == 4
    assert [scheduler.lane(i) for i in range(8)].count("curation") == 2
    assert lab.db.claim_next("W0", lane=scheduler.lane(0))["experiment_id"] in pruning
    assert lab.db.claim_next("W2", lane=scheduler.lane(2))["experiment_id"] == discovery[0]
    # A very high-priority curator still cannot displace discovery's own lane.
    lab.db.update_experiment(pruning[-1], priority=100000)
    assert lab.db.claim_next("W3", lane="discovery")["experiment_id"] in discovery
    lab.db.execute("UPDATE experiments SET status='failed' WHERE proposer=?", (PROPOSER,))
    assert lab.db.claim_next("W0", lane="curation")["experiment_id"] in discovery
    lab.db.execute("UPDATE experiments SET status='failed' WHERE status='queued'")
    extra = lab.db.insert_experiment({"status": "queued", "proposer": PROPOSER})
    assert lab.db.claim_next("W2", lane="discovery")["experiment_id"] == extra


def test_busy_controller_run_schedules_curation_without_suppressing_discovery(lab, monkeypatch):
    import genemila.controller as module
    discovery = add_discovery(lab)
    ctl = Controller(lab, workers=8, seconds=20, quiet=True)
    started, phases = [], []
    monkeypatch.setattr(module, "_raise_fd_limit", lambda: None)
    lab.git_head_dirty = lambda: False
    lab.record_analytic_baselines = lambda: None
    lab.queue_model_baselines = lambda: None
    ctl._start_worker = lambda i: started.append(ctl.curation.lane(i))
    ctl._baselines_done = lambda: True
    ctl._maybe_plan = lambda: phases.append("discovery")
    ctl._maybe_exploit = lambda: None
    ctl._supervise = lambda: None
    ctl._review_feature_observations = lambda: None
    ctl.status_line = lambda: "synthetic status"
    ctl._exhausted = lambda: True  # inspect exactly one real controller scheduling iteration
    ctl.shutdown = lambda: {"synthetic": True}
    assert ctl.run() == {"synthetic": True}
    assert len(lab.db.query("SELECT 1 FROM experiments WHERE proposer=?", (PROPOSER,))) == 4
    assert ctl._queued_discovery() == len(discovery)
    assert phases == ["discovery"] and started.count("curation") == 2
    assert lab.db.query("SELECT * FROM llm_calls") == []


def test_round_freezes_parent_and_waits_for_all_jobs_even_after_new_champion(lab):
    scheduler = CurationScheduler(lab, 8)
    first = scheduler.maybe_queue(now=100)
    new_parent = lab.add_parent(score=.7)
    assert scheduler.maybe_queue(now=1000, force=True) == []
    assert scheduler.parent_id == lab.parent
    assert {lab.db.get_experiment(eid)["parent_id"] for eid in first} == {lab.parent}
    finish_round(lab, first[:-1])
    assert scheduler.maybe_queue(now=1000) == []
    finish_round(lab, first[-1:])
    second = scheduler.maybe_queue(now=1000)
    assert 0 < len(second) <= 4
    assert {lab.db.get_experiment(eid)["parent_id"] for eid in second} == {new_parent}


def test_restart_respects_existing_round_and_all_attempted_hashes_are_skipped(lab):
    scheduler = CurationScheduler(lab, 8)
    first = scheduler.maybe_queue(now=0)
    scheduler = CurationScheduler(lab, 8)
    assert scheduler.maybe_queue(now=1000, force=True) == []
    finish_round(lab, first)
    for iteration in range(20):
        batch = scheduler.maybe_queue(now=1000 + iteration, force=True)
        if not batch:
            break
        assert len(batch) <= 4
        finish_round(lab, batch)
    else:
        pytest.fail("bounded candidate family failed to exhaust")
    rows = lab.db.query("SELECT config_hash,kind,proposer FROM experiments WHERE config_hash IS NOT NULL")
    assert len({row["config_hash"] for row in rows}) == len(rows)
    assert all(row["kind"] == "config" and row["proposer"] == PROPOSER for row in rows)
    assert lab.db.query("SELECT * FROM llm_calls") == []


def test_exhaustion_flushes_curation_despite_interval_and_honors_stop(lab):
    ctl = Controller(lab, workers=8, seconds=20, quiet=True)
    ctl.curation.next_round_at = float("inf")
    assert ctl._exhausted() is False
    assert len(ctl.curation.round_ids) == 4
    finish_round(lab, ctl.curation.round_ids)
    lab.stop_event.set()
    assert ctl.curation.maybe_queue(force=True) == []


def test_curator_preserves_params_and_selector_for_module_and_dependency_blocks(lab):
    parent_id = lab.add_parent(.7, selector={"method": "variance"})
    parent = lab.db.get_experiment(parent_id)
    offered = list(candidates(lab, parent))
    screens = [spec for spec in offered if spec.hypothesis_group.startswith("curation_screen")]
    assert {spec.hyperparameters["column_selection"]["method"] for spec in screens} == {"lasso", "elasticnet"}
    assert all(spec.model_type == "ridge" for spec in screens)
    for spec in offered:
        validate_spec(spec, lab.known_features(), lab.limits, parent)
        assert spec.seed == 19 and not {"cv_folds", "cv_seed"} & spec.hyperparameters.keys()
        if "big_block" in spec.feature_set:
            assert spec.feature_params["leaf"] == {"scale": 7}
        if spec.hypothesis_group.startswith("curation_drop"):
            assert spec.hyperparameters["column_selection"] == {"method": "variance"}
    assert any(len(parent["feature_set_json"]) - len(spec.feature_set) == 2 for spec in offered)
    offered[0].feature_params["leaf"]["scale"] = 99
    assert parent["feature_params_json"]["leaf"]["scale"] == 7


def test_exploit_preserves_selector_and_dependency_only_overrides(lab):
    parent_id = lab.add_parent(.7, selector={"method": "lasso", "alpha": .01})
    parent = lab.db.get_experiment(parent_id)
    offered = exploit.candidates(lab, parent)
    assert offered and all(spec.model_type == "ridge" for spec in offered)
    for spec in offered:
        assert spec.hyperparameters["column_selection"] == {"method": "lasso", "alpha": .01}
        assert not {"cv_folds", "cv_seed"} & spec.hyperparameters.keys()
        if "big_block" in spec.feature_set:
            assert spec.feature_params["leaf"] == {"scale": 7}
    assert any(spec.hypothesis_group.startswith("exploit_alpha") for spec in offered)


def test_ablation_of_selected_dependency_keeps_its_params_for_remaining_consumer(lab):
    parent = lab.best()
    parent["feature_set_json"].append("leaf")
    offered = exploit.candidates(lab, parent)
    drop = next(spec for spec in offered if spec.hypothesis_group.startswith("exploit_drop_leaf_"))
    assert "leaf" not in drop.feature_set and "big_block" in drop.feature_set
    assert drop.feature_params["leaf"] == {"scale": 7}


def test_concurrent_workers_claim_exclusive_jobs_in_their_reserved_lanes(lab):
    scheduler = CurationScheduler(lab, 8)
    add_discovery(lab, count=30)
    scheduler.maybe_queue()
    barrier = threading.Barrier(8)
    def claim(index):
        barrier.wait()
        try:
            return lab.db.claim_next(f"W{index}", lane=scheduler.lane(index))
        finally:
            lab.db.close_thread_conn()
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(claim, range(8)))
    assert len({row["experiment_id"] for row in rows}) == 8
    assert all(row["proposer"] == PROPOSER for row in rows[:2])
    assert all(row["proposer"] != PROPOSER for row in rows[2:])


def test_subset_exploit_inherits_actual_selected_parent_not_current_best(lab):
    # A smaller old model is the nearest valid subset parent. Its selector and seed must survive.
    old_id = lab.db.insert_experiment({"status": "completed", "kind": "config", "model_type": "ridge",
        "primary_score": .4, "feature_set_json": ["is_target", "big_block"],
        "feature_params_json": {"leaf": {"scale": 12}}, "seed": 31,
        "hyperparameters_json": {"alpha_grid": [9.], "column_selection": {"method": "variance"}}})
    offered = exploit.candidates_subsets(lab, lab.best())
    children = [spec for spec in offered if spec.parent_experiment_id == old_id]
    assert children
    for spec in children:
        assert spec.seed == 31 and spec.hyperparameters == {"alpha_grid": [9.], "column_selection": {"method": "variance"}}
        if "big_block" in spec.feature_set:
            assert spec.feature_params["leaf"] == {"scale": 12}


def test_worker_uses_assigned_lane_and_persists_numeric_policy_metadata(lab):
    scheduler = CurationScheduler(lab, 8)
    add_discovery(lab)
    pruning = scheduler.maybe_queue()
    worker = Worker(lab, "W0", None, None, threading.Semaphore(1), queue_lane="curation")
    claimed = []
    def record_only(rec):
        claimed.append(rec["experiment_id"])
        lab.stop_event.set()
    worker.process = record_only
    worker.loop()
    assert claimed[0] in pruning
    result = {"n_features": 3, "n_raw_features": 99,
              "coefficients": [{"alpha": 1., "coef": {"a": .123456}}]}
    evaluation = {"diagnostics": {"unchanged": True}, "best_alpha": 1.,
                  "metrics": {"n_visible": 70, "n_validation": 20}}
    diagnostic = worker._diagnostics(result, evaluation)
    assert diagnostic == {"unchanged": True, "coefficients": {"a": .12346},
        "n_features": 3, "n_raw_features": 99, "n_available_features": 99,
        "selection_rule": "pearson_delta", "cv_folds": 5, "cv_seed": 7,
        "n_visible": 70, "n_validation": 20}


def test_disabled_scheduler_keeps_historical_priority_queue(lab):
    lab.cfg.pop("curation")
    scheduler = CurationScheduler(lab, 8)
    assert scheduler.maybe_queue() == [] and scheduler.lane(0) is None
    ordinary = add_discovery(lab, count=1)[0]
    lab.db.insert_experiment({"status": "queued", "proposer": PROPOSER, "priority": -1})
    assert lab.db.claim_next("W0")["experiment_id"] == ordinary


@pytest.mark.parametrize("settings", [
    {"enabled": "false"}, {"reserved_workers": 0}, {"reserved_workers": True},
    {"max_candidates_per_round": 0}, {"interval_s": float("nan")},
    {"score_tolerance": -1}, {"score_tolerance": float("inf")},
])
def test_invalid_curation_configuration_fails_before_workers(lab, settings):
    lab.cfg["curation"].update(settings)
    with pytest.raises(ValueError):
        Controller(lab, workers=8, seconds=20)


def test_worker_reservation_keeps_discovery_capacity(lab):
    lab.cfg["curation"]["reserved_workers"] = 20
    assert CurationScheduler(lab, 8).reserved_workers == 7
    with pytest.raises(ValueError, match="at least two"):
        CurationScheduler(lab, 1)
