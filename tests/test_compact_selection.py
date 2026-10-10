"""Stored synthetic metadata only: no Lab construction, dataset, fitting, or oracle."""

from copy import deepcopy
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from genemila.lab import Lab
from genemila.model_selection import (
    _artifact_metadata, select_compact, score_tolerance, visible_metadata,
)
from genemila.report import _compact_finalists, _read_frozen_selection, run_query_only


CFG = {"curation": {"enabled": True}, "final": {"ensemble": False}}


def record(eid, columns=99, val=.6, cv=.6, *, finished=1):
    primary = (17 * val + 50 * cv) / 67
    return {"experiment_id": eid, "status": "completed", "kind": "config", "model_type": "ridge",
            "hypothesis": f"Synthetic {eid}", "hypothesis_group": eid,
            "primary_score": primary, "dataset": "synthetic", "split_id": "split-A", "finished_at": finished,
            "feature_set_json": ["same_feature_module"], "hyperparameters_json": {"cv_folds": 5, "cv_seed": 0},
            "val_metrics_json": {"primary": primary, "pearson_delta": val, "pearson_delta_cv": cv,
                                 "selection_rule": "pearson_delta", "cv_folds": 5, "cv_seed": 0,
                                 "n_visible": 67, "n_validation": 17},
            "diagnostics_json": {"n_features": columns}, "query_metrics_json": None}


def choose(records, raw=None, cfg=None):
    return select_compact(records, raw or records[0], cfg or CFG)


def test_equal_accuracy_selects_actual_numeric_columns_and_keeps_raw():
    raw, compact = record("RAW"), record("COMPACT", 18)
    result = choose([raw, compact])
    assert result["selected_id"] == "COMPACT"
    assert result["raw_accuracy_champion_id"] == "RAW"
    assert result["compact_selected_winner"]["n_features"] == 18
    assert result["raw_accuracy_champion"]["n_features"] == 99
    assert len(result["pareto_frontier"]) == 1
    assert result["pareto_frontier"][0]["experiment_id"] == "COMPACT"


def test_default_has_no_accuracy_tradeoff_even_for_one_column():
    raw, slim = record("RAW"), record("SLIM", 1, .599999, .599999)
    result = choose([raw, slim])
    assert result["selected_id"] == "RAW"
    assert result["score_tolerance"] == 0
    assert result["excluded"] == [{"experiment_id": "SLIM", "reason": "visible primary below accuracy guard"}]
    assert [r["experiment_id"] for r in result["pareto_frontier"]] == ["SLIM", "RAW"]


def test_tolerance_does_not_waive_validation_or_cv_guard():
    raw = record("RAW", val=.62, cv=.62)
    candidates = [record("BAD_VAL", 3, .59, .63), record("BAD_CV", 2, .64, .61)]
    result = choose([raw, *candidates], cfg={"curation": {"enabled": True, "score_tolerance": .1}})
    assert result["selected_id"] == "RAW"
    assert all("constituent regressed" in r["reason"] for r in result["excluded"])


@pytest.mark.parametrize("value", [-.001, float("nan"), float("inf"), -float("inf"), None, True, "bad"])
def test_invalid_tolerance_rejected(value):
    with pytest.raises(ValueError, match="finite and nonnegative"):
        score_tolerance({"curation": {"score_tolerance": value}})


def test_heldout_scores_are_neither_read_nor_copied():
    class Sealed(dict):
        def get(self, *args, **kwargs):
            raise AssertionError("query-only scores entered selection")
    raw, slim = record("RAW"), record("SLIM", 10)
    first = choose([raw, slim])
    raw["query_metrics_json"] = Sealed(primary=1)
    slim["query_metrics_json"] = Sealed(primary=-1)
    raw["test_score"] = 1
    slim["heldout_score"] = -1
    assert choose([raw, slim]) == first
    encoded = json.dumps(first)
    assert "heldout_score" not in encoded and "query_metrics_json" not in encoded


@pytest.mark.parametrize("field,value", [("dataset", "elsewhere"), ("split_id", "split-B"),
                                        ("cv_seed", 11), ("cv_folds", 4), ("selection_protocol", "different")])
def test_incomparable_scope_is_not_promoted(field, value):
    raw, slim = record("RAW"), record("SLIM", 8)
    if field in ("dataset", "split_id"):
        slim[field] = value
    else:
        slim["val_metrics_json"][field] = value
        if field in slim["hyperparameters_json"]:
            slim["hyperparameters_json"][field] = value
    result = choose([raw, slim])
    assert result["selected_id"] == "RAW"
    assert "protocol differs" in result["excluded"][0]["reason"]


def test_public_cv_only_cannot_compete_with_validation_plus_cv():
    raw, slim = record("RAW"), record("CV_ONLY", 1)
    slim["val_metrics_json"].pop("pearson_delta")
    slim["val_metrics_json"].update(n_visible=50, n_validation=0, metric_scope="public_cv50_seed0_v1")
    result = choose([raw, slim])
    assert result["selected_id"] == "RAW"
    # A scope tag that claims public CV is refused even if other fields were copied from a visible result.
    slim = record("MISLABELED", 1)
    slim["val_metrics_json"]["metric_scope"] = "public_cv50_seed0_v1"
    result = choose([raw, slim])
    assert "complete visible selection scope" in result["excluded"][0]["reason"]


@pytest.mark.parametrize("missing", ["n_features", "n_validation", "selection_rule", "pearson_delta_cv"])
def test_incomplete_champion_metadata_falls_back_to_raw(missing):
    raw, slim = record("RAW"), record("SLIM", 8)
    raw["diagnostics_json"].pop(missing, None)
    raw["val_metrics_json"].pop(missing, None)
    result = choose([raw, slim])
    assert result["selected_id"] == "RAW" and result["fallback_reason"]


def test_conflicting_metadata_or_unjustified_primary_fails_closed():
    raw, slim = record("RAW"), record("SLIM", 8)
    slim["diagnostics_json"]["cv_seed"] = 11
    assert "conflicting cv_seed" in choose([raw, slim])["excluded"][0]["reason"]
    slim = record("SLIM", 8)
    slim["val_metrics_json"]["pearson_delta"] = .1
    assert "does not match" in choose([raw, slim])["excluded"][0]["reason"]


@pytest.mark.parametrize("count", [None, 0, -1, True, 3.5, float("nan")])
def test_invalid_numeric_column_count_is_refused(count):
    raw, slim = record("RAW"), record("SLIM", count)
    assert choose([raw, slim])["selected_id"] == "RAW"


def test_deterministic_tie_break_and_ensemble_is_not_an_incumbent():
    raw, b, a = record("RAW"), record("B", 8), record("A", 8)
    ensemble = record("ENSEMBLE", 1, .9, .9)
    ensemble["kind"] = "ensemble"
    assert choose([raw, b, ensemble, a])["selected_id"] == "A"
    assert choose([a, ensemble, b, raw], raw=raw)["selected_id"] == "A"


def test_artifact_column_count_fallback_is_cached_and_invalidated(tmp_path):
    candidate = record("FROM_ARTIFACT")
    candidate["diagnostics_json"] = {}
    candidate["artifact_dir"] = str(tmp_path)
    path = tmp_path / "result.json"
    path.write_text(json.dumps({"n_features": 2, "columns": ["a", "b"]}))
    _artifact_metadata.cache_clear()
    assert visible_metadata(candidate)["n_features"] == 2
    assert visible_metadata(candidate)["n_features"] == 2
    assert _artifact_metadata.cache_info().misses == 1
    assert _artifact_metadata.cache_info().hits == 1
    path.write_text(json.dumps({"n_features": 3, "columns": ["a", "b", "c"]}))
    assert visible_metadata(candidate)["n_features"] == 3
    assert _artifact_metadata.cache_info().misses == 2
    path.write_text(json.dumps({"n_features": 9, "columns": ["a"]}))
    with pytest.raises(ValueError, match="column count conflicts"):
        visible_metadata(candidate)


class MemoryDB:
    def __init__(self, rows):
        self.rows = {r["experiment_id"]: r for r in rows}
        self.lock = threading.RLock()
        self.conn = SimpleNamespace(execute=lambda sql: None)
        self.completed_reads = 0

    def best(self):
        rows = [r for r in self.rows.values() if r["status"] == "completed" and r["kind"] != "ensemble"]
        return min(rows, key=lambda r: (-r["primary_score"], r["finished_at"])) if rows else None

    def completed(self):
        self.completed_reads += 1
        return [r for r in self.rows.values() if r["status"] == "completed"]

    def get_experiment(self, eid):
        return self.rows.get(eid)

    def query(self, sql, *args):
        if "COUNT(*) n" in sql:
            completed = [r for r in self.rows.values() if r["status"] == "completed"]
            return [{"n": len(completed), "latest": max((r["finished_at"] for r in completed), default=None)}]
        rows = [r for r in self.rows.values() if r["status"] == "completed"]
        if "kind NOT IN ('baseline', 'ensemble')" in sql:
            rows = [r for r in rows if r["kind"] not in ("baseline", "ensemble")]
        elif "kind='baseline'" in sql:
            rows = [r for r in rows if r["kind"] == "baseline"]
        elif "kind='ensemble'" in sql:
            rows = [r for r in rows if r["kind"] == "ensemble"]
        if "query_metrics_json IS NOT NULL" in sql:
            rows = [r for r in rows if r.get("query_metrics_json")]
        return sorted(rows, key=lambda r: -r["primary_score"])

    def event(self, *args, **kwargs):
        pass


def stub_lab(tmp_path, rows, *, cfg=None):
    lab = Lab.__new__(Lab)  # No initialization, labels, gateway or oracle.
    lab.cfg = deepcopy(cfg or CFG)
    lab.run_id = "synthetic-run"
    lab.run_dir = tmp_path
    lab.db = MemoryDB(rows)
    lab.celleval_val1 = lambda eid: None
    lab.query_only = lambda eid: pytest.fail("tests must not invoke an oracle")
    return lab


def test_lab_best_opt_in_and_cache_preserve_raw_database_ranking(tmp_path):
    raw, slim = record("RAW"), record("SLIM", 4, finished=2)
    lab = stub_lab(tmp_path, [raw, slim])
    assert lab.best()["experiment_id"] == "SLIM"
    assert lab.db.best()["experiment_id"] == "RAW"
    assert lab.best()["experiment_id"] == "SLIM" and lab.db.completed_reads == 1
    slim["query_metrics_json"] = {"primary": -.9}
    assert lab.best()["experiment_id"] == "SLIM" and lab.db.completed_reads == 1
    new = record("NEW", 3, .61, .61, finished=3)
    lab.db.rows[new["experiment_id"]] = new
    assert lab.best()["experiment_id"] == "NEW" and lab.db.completed_reads == 2
    lab.cfg["curation"] = {"enabled": False, "score_tolerance": float("nan")}
    assert lab.best() is lab.db.best()  # Disabled runs ignore curation settings entirely.


def test_finalists_frozen_before_query_fields_are_read(tmp_path):
    class NoQueryRead(dict):
        def get(self, key, *args):
            if key == "query_metrics_json":
                raise AssertionError("query score read before freeze")
            return super().get(key, *args)
    raw, slim = NoQueryRead(record("RAW")), NoQueryRead(record("SLIM", 4))
    lab = stub_lab(tmp_path, [raw, slim])
    picked = _compact_finalists(lab, 2, allow_new=False)
    assert [r["experiment_id"] for r in picked] == ["SLIM", "RAW"]
    frozen = json.loads((tmp_path / "final_selection.json").read_text())
    assert frozen["selected_id"] == "SLIM"
    assert frozen["finalist_ids"] == ["SLIM", "RAW"]
    assert not list(tmp_path.glob(".selection-*"))
    assert "query_metrics_json" not in json.dumps(frozen)


def test_resummary_does_not_select_by_heldout_score_or_availability(tmp_path):
    raw, slim = record("RAW"), record("SLIM", 4)
    raw["query_metrics_json"] = {"primary": .95}
    slim["query_metrics_json"] = {"primary": -.9}
    lab = stub_lab(tmp_path, [raw, slim])
    rows = run_query_only(lab, 2, allow_new=False)
    assert [r["experiment_id"] for r in rows] == ["SLIM", "RAW"]
    original = (tmp_path / "final_selection.json").read_bytes()
    lab.cfg["curation"]["score_tolerance"] = .2
    raw["query_metrics_json"], slim["query_metrics_json"] = {"primary": -1}, None
    later = record("NEW", 1, .9, .9, finished=3)
    later["query_metrics_json"] = {"primary": 1}
    lab.db.rows["NEW"] = later
    rows = run_query_only(lab, 99, allow_new=False)
    assert [r["experiment_id"] for r in rows] == ["RAW"]
    assert (tmp_path / "final_selection.json").read_bytes() == original
    assert _read_frozen_selection(lab)["selected_id"] == "SLIM"
    lab.cfg["curation"]["enabled"] = False
    assert [r["experiment_id"] for r in run_query_only(lab, 99, allow_new=False)] == ["RAW"]
    assert (tmp_path / "final_selection.json").read_bytes() == original


def test_legacy_query_order_and_no_freeze_when_disabled(tmp_path):
    raw, slim = record("RAW"), record("SLIM", 4, .59, .59)
    # Different modules preserve both under original module/model deduplication.
    slim["feature_set_json"] = ["other_module"]
    for row in (raw, slim):
        row["query_metrics_json"] = {"primary": 0}
    lab = stub_lab(tmp_path, [raw, slim], cfg={"final": {"ensemble": False}})
    assert [r["experiment_id"] for r in run_query_only(lab, 2, allow_new=False)] == ["RAW", "SLIM"]
    assert not (tmp_path / "final_selection.json").exists()


def test_frozen_selected_model_cannot_be_an_ensemble_or_missing_finalist(tmp_path):
    raw, slim = record("RAW"), record("SLIM", 4)
    lab = stub_lab(tmp_path, [raw, slim])
    _compact_finalists(lab, 2, allow_new=False)
    slim["kind"] = "ensemble"
    with pytest.raises(ValueError, match="completed single model"):
        _read_frozen_selection(lab)
    slim["kind"] = "config"
    path = tmp_path / "final_selection.json"
    data = json.loads(path.read_text())
    data["finalist_ids"] = ["RAW"]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="absent from the finalist list"):
        _read_frozen_selection(lab)


@pytest.mark.parametrize("contents", ["{truncated", "{}", "[]"])
def test_malformed_frozen_policy_fails_closed_without_reselection(tmp_path, contents):
    lab = stub_lab(tmp_path, [record("RAW"), record("SLIM", 4)])
    (tmp_path / "final_selection.json").write_text(contents)
    with pytest.raises(ValueError):
        run_query_only(lab, 2, allow_new=False)
    assert (tmp_path / "final_selection.json").read_text() == contents


def test_regenerated_summary_uses_frozen_winner_and_labels_both_roles(tmp_path, monkeypatch):
    from genemila import report
    raw, slim = record("RAW"), record("SLIM", 4)
    raw["best_alpha"] = slim["best_alpha"] = 1
    lab = stub_lab(tmp_path, [raw, slim])
    lab.cfg["run"] = {}
    lab.dataset, lab.split_id, lab.base_commit = "synthetic", "split-A", "test-commit"
    lab.selection, lab.cv_folds = "pearson_delta", 5
    lab._val1, lab._train = SimpleNamespace(perts=list(range(17))), SimpleNamespace(perts=list(range(50)))
    query = lab.db.query
    lab.db.query = lambda sql, *args: [{"started_at": 1, "finished_at": 11, "workers": 2}] \
        if "FROM runs" in sql else query(sql, *args)
    lab.db.lineage = lambda eid: []
    lab.db.features = lambda: []
    lab.db.llm_totals = lambda *args: {"cost_usd": 0, "calls": 0, "input_tokens": 0,
                                      "output_tokens": 0, "cached_tokens": 0}
    monkeypatch.setattr(report, "planner_health", lambda *args: {})
    _compact_finalists(lab, 2, allow_new=False)
    first = report.build_summary(lab, 10, 2, [])
    lab.cfg["curation"]["score_tolerance"] = .5
    slim["query_metrics_json"] = {"primary": -1}
    later = record("LATER", 1, .9, .9, finished=3)
    later["best_alpha"] = 1
    lab.db.rows["LATER"] = later
    second = report.build_summary(lab, 10, 2, [])
    assert first["best"] == second["best"]
    assert second["best"]["experiment_id"] == "SLIM"
    assert second["raw_accuracy_champion"]["experiment_id"] == "RAW"
    assert second["model_selection"]["score_tolerance"] == 0
    lab.cfg["curation"]["enabled"] = False
    assert report.build_summary(lab, 10, 2, [])["best"] == first["best"]
    text = report.render_markdown(second)
    assert "Raw accuracy champion: RAW" in text and "Compact selected winner: SLIM" in text
    assert "Pareto frontier" in text


def test_sparse_finalist_diversity_preserves_feature_order(tmp_path):
    raw, compact = record("RAW"), record("COMPACT", 4)
    a, b = record("A", 5, .59, .59), record("B", 5, .58, .58)
    a["feature_set_json"], b["feature_set_json"] = ["x", "y"], ["y", "x"]
    for rec in (a, b):
        rec["hyperparameters_json"]["column_selection"] = {"method": "lasso", "alpha": .001}
    lab = stub_lab(tmp_path, [raw, compact, a, b])
    assert [r["experiment_id"] for r in _compact_finalists(lab, 4, allow_new=False)] == ["COMPACT", "RAW", "A", "B"]


def test_baseline_raw_fallback_is_in_frozen_finalist_list(tmp_path):
    baseline, other = record("BASELINE"), record("OTHER", 4, .5, .5)
    baseline["kind"] = "baseline"
    baseline["model_type"] = "none"
    baseline["diagnostics_json"] = {}
    lab = stub_lab(tmp_path, [baseline, other])
    picked = _compact_finalists(lab, 1, allow_new=False)
    assert [r["experiment_id"] for r in picked] == ["BASELINE", "OTHER"]
    assert _read_frozen_selection(lab)["selected_id"] == "BASELINE"


def test_protocol_stamping_uses_only_named_visible_scope(tmp_path):
    lab = stub_lab(tmp_path, [])
    lab.selection, lab.cv_folds, lab.cv_seed = "pearson_delta", 5, 11
    lab._val1, lab._train = SimpleNamespace(perts=list(range(17))), SimpleNamespace(perts=list(range(50)))
    assert lab.visible_selection_protocol() == {
        "selection_rule": "pearson_delta", "cv_folds": 5, "cv_seed": 11, "n_validation": 17, "n_visible": 67}


def test_concurrent_completion_cannot_mix_raw_champion_and_candidate_snapshots(tmp_path, monkeypatch):
    from genemila.db import Database
    raw, slim, future = record("RAW"), record("SLIM", 4, finished=2), record("NEW", 99, .7, .7, finished=3)
    future["status"] = "running"
    lab = stub_lab(tmp_path, [])
    lab.db = Database(tmp_path / "synthetic.db")
    for rec in (raw, slim, future):
        lab.db.insert_experiment(rec)
    first_read, completed = threading.Event(), threading.Event()
    errors = []
    original_best = lab.db.best
    first_call = True

    def best_then_allow_completion():
        nonlocal first_call
        champion = original_best()
        if first_call:
            first_call = False
            first_read.set()
            assert completed.wait(5), "synthetic completion did not finish"
        return champion

    def finish_new_champion():
        try:
            assert first_read.wait(5), "selection did not start"
            lab.db.update_experiment("NEW", status="completed")
        except BaseException as exc:
            errors.append(exc)
        finally:
            completed.set()
            lab.db.close_thread_conn()

    monkeypatch.setattr(lab.db, "best", best_then_allow_completion)
    worker = threading.Thread(target=finish_new_champion)
    worker.start()
    try:
        snapshot = lab.compact_selection()
        worker.join(5)
        assert not worker.is_alive() and not errors
        assert snapshot["raw_accuracy_champion_id"] == "RAW"
        assert snapshot["selected_id"] == "SLIM"
        assert "NEW" not in {r["experiment_id"] for key in ("eligible", "excluded", "pareto_frontier")
                             for r in snapshot[key]}
        assert not lab.db.conn.in_transaction
        refreshed = lab.compact_selection()
        assert refreshed["raw_accuracy_champion_id"] == refreshed["selected_id"] == "NEW"
        # Also preserve an outer caller transaction rather than committing or rolling it back.
        lab.db.conn.execute("BEGIN")
        assert lab.compact_selection()["selected_id"] == "NEW"
        assert lab.db.conn.in_transaction
        lab.db.conn.execute("ROLLBACK")
    finally:
        worker.join(5)
        lab.db.close_thread_conn()
