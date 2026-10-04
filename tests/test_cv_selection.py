"""Cross-validated model selection: out-of-fold predictions of the training perturbations join the visible
validation set, computed through fold views that hide the fold's labels from feature code."""

import json
from pathlib import Path

import numpy as np
import pytest

from genemila.data.bundle import export_public
from genemila.features.api import FeatureContext
from genemila.pipeline import cv_folds_of, run


def test_fold_view_hides_the_fold_and_leaves_the_original_alone(dataset, tmp_path):
    ctx = FeatureContext(export_public(dataset, tmp_path / "pub"))
    folds = cv_folds_of(ctx.train_perts, 3, seed=0)
    assert sorted(sum(folds, [])) == sorted(ctx.train_perts)
    assert all(len(f) in (len(ctx.train_perts) // 3, len(ctx.train_perts) // 3 + 1) for f in folds)
    assert cv_folds_of(ctx.train_perts, 3, seed=0) == folds  # deterministic
    assert cv_folds_of(ctx.train_perts, 3, seed=1) != folds
    full_n = len(ctx.train_perts)
    view = ctx.without_train(folds[0])
    assert not set(view.train_perts) & set(folds[0])
    assert len(view.train_perts) == full_n - len(folds[0])
    perts, d = view.train_delta(exclude=view.train_perts[0])
    assert len(perts) == len(view.train_perts) - 1 and d.shape[0] == len(perts)
    assert view.train_signature != ctx.train_signature
    assert len(ctx.train_perts) == full_n and ctx.train_delta()[1].shape[0] == full_n  # untouched
    assert view.perts == ctx.perts and view.n_genes == ctx.n_genes
    view.cache["x"] = 1
    assert "x" not in ctx.cache


def test_pipeline_writes_out_of_fold_predictions(dataset, tmp_path):
    pub = export_public(dataset, tmp_path / "pub")
    spec = {"experiment_id": "EXP_t", "feature_set": ["control_mean", "mean_response", "is_target"],
            "feature_params": {}, "model_type": "ridge",
            "hyperparameters": {"alpha_grid": [1.0, 10.0], "cv_folds": 3, "cv_seed": 0}, "seed": 0}
    out = tmp_path / "out"
    res = run(spec, pub, tmp_path / "plugins", out, cache_dir=tmp_path / "cache")
    assert res["cv_folds"] == 3 and res["timing"]["cv_cpu_s"] >= 0
    z = np.load(out / "cv.npz")
    ctx = FeatureContext(pub)
    assert z["delta"].shape == (2, len(ctx.train_perts), ctx.n_genes)
    assert [str(p) for p in z["perts"]] == ctx.train_perts
    assert np.all(np.isfinite(z["delta"])) and np.abs(z["delta"]).sum() > 0
    # out-of-fold predictions must be worse than in-sample fitted values (they never saw their own label)
    _, d = ctx.train_delta()
    oof = np.mean([np.corrcoef(z["delta"][0, i], d[i])[0, 1] for i in range(len(ctx.train_perts))])
    assert 0 < oof < 1
    # the cache keys on the training set: fold blocks and full blocks coexist without clashing
    names = {p.name.split("__")[0] for p in (tmp_path / "cache" / "features").glob("*.npy")}
    assert names == set(spec["feature_set"])
    # label-dependent feature: one block for train, one for evals, one per fold (train-without-fold + fold)
    assert len(list((tmp_path / "cache" / "features").glob("mean_response__*.npy"))) == 2 + 3


def test_lab_selects_on_validation_plus_out_of_fold(lab_factory):
    lab = lab_factory(experiment__cv_folds=3)
    assert lab.cv_folds == 3
    lab.record_analytic_baselines()
    base = lab.best_baseline()
    m = base["val_metrics_json"]
    assert m["n_visible"] == len(lab._train.perts) + len(lab._val1.perts) and m["cv_folds"] == 3
    n1, nt = len(lab._val1.perts), len(lab._train.perts)
    assert m["primary"] == pytest.approx((n1 * m["pearson_delta"] + nt * m["pearson_delta_cv"]) / (n1 + nt))
    # a pipeline experiment: cv_folds reach the subprocess through the hyperparameters set at queue time
    from genemila.spec import ExperimentSpec
    eid, status = lab.queue(ExperimentSpec(hypothesis="ridge on builtins", scientific_rationale="a reference model on the built-in features",
                                           feature_set=["control_mean", "mean_response", "is_target"],
                                           hyperparameters={"alpha_grid": [1.0]}))
    rec = lab.db.get_experiment(eid)
    assert status == "queued" and rec["hyperparameters_json"]["cv_folds"] == 3
    spec = ExperimentSpec.from_record(rec)
    out = lab.artifacts / eid
    run(spec.run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
    ev = lab.evaluate_artifact(out / "predictions.npz")
    assert ev["metrics"]["n_visible"] == n1 + nt and "pearson_delta_cv" in ev["metrics"]
    assert ev["alpha_scores"][0]["primary"] == ev["metrics"]["primary"]
    # with cross-validation on, an artifact without cv.npz is refused rather than silently scored on val1 only
    (out / "cv.npz").unlink()
    with pytest.raises(ValueError, match="cv.npz"):
        lab.evaluate_artifact(out / "predictions.npz")


def test_cv_off_keeps_the_old_protocol(lab_factory):
    lab = lab_factory(experiment__cv_folds=0)
    lab.record_analytic_baselines()
    m = lab.best_baseline()["val_metrics_json"]
    assert "n_visible" not in m and m["primary"] == m["pearson_delta"]


def test_ensemble_finalist_is_kept_only_when_it_wins(lab_factory):
    """The average of the finalists becomes one more candidate for the sealed set only when it beats the best
    single model on the visible perturbations; it never becomes the lab's 'best' experiment."""
    from genemila.controller import Controller
    from genemila.providers.mock import MockProvider, ScriptedPlanner
    from genemila.report import ensemble_finalist, run_query_only
    lab = lab_factory(final__ensemble=False, schedule__max_planner_calls=2)
    Controller(lab, workers=2, seconds=45, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
               quiet=True).run()
    singles = lab.db.query("SELECT * FROM experiments WHERE status='completed' AND kind!='baseline' "
                           "ORDER BY primary_score DESC LIMIT 3")
    assert len(singles) >= 2
    ens = ensemble_finalist(lab, singles)
    best_single = max(s["primary_score"] for s in singles)
    if ens is None:
        assert lab.db.query("SELECT 1 FROM events WHERE kind='ensemble_skipped'")
        assert not lab.db.query("SELECT 1 FROM experiments WHERE kind='ensemble'")
        assert not lab.db.query("SELECT 1 FROM experiments WHERE status='reserved'")
    else:
        assert ens["kind"] == "ensemble" and ens["primary_score"] > best_single
        assert (Path(ens["artifact_dir"]) / "predictions.npz").exists()
        assert (Path(ens["artifact_dir"]) / "cv.npz").exists() == (lab.cv_folds > 1)
        assert set(ens["diagnostics_json"]["members"]) == {s["experiment_id"] for s in singles}
        assert ensemble_finalist(lab, singles)["experiment_id"] == ens["experiment_id"]  # built once
        assert lab.best()["kind"] != "ensemble"
        lab.cfg["final"]["ensemble"] = True
        rows = run_query_only(lab, 3, allow_new=True)
        kinds = [r["kind"] for r in rows]
        assert kinds[0] == "ensemble" and kinds[-1] == "baseline" and rows[0]["members"]
        assert rows[0]["query_only_score"] is not None
        from genemila.report import build_summary
        s = build_summary(lab, 45.0, 2, rows)
        assert s["ensemble"]["experiment_id"] == ens["experiment_id"] and s["best"]["experiment_id"] != ens["experiment_id"]
        assert s["experiments_completed"] == len(lab.db.query(
            "SELECT 1 FROM experiments WHERE status='completed' AND kind NOT IN ('baseline','ensemble')"))
        assert s["compute_efficiency"]["experiments_per_hour"] == round(s["experiments_completed"] / (45 / 3600), 2)
        assert sum(s["completed_by_proposer"].values()) == s["experiments_completed"]
        from genemila.report import render_markdown
        assert "## ENSEMBLE FINALIST" in render_markdown(s) and ens["experiment_id"] in render_markdown(s)
        # a re-summary without new queries keeps every queried finalist, the ensemble included
        again = run_query_only(lab, 3, allow_new=False)
        assert [r["experiment_id"] for r in again] == [r["experiment_id"] for r in rows]


def test_query_cap_drops_the_ensemble_before_the_baseline(lab_factory):
    """Query order is singles, starting model, ensemble: with a cap of top_k + 1 the baseline row (the gain's
    reference) survives and the ensemble is the row left unscored; a later re-summary does not invent it."""
    from genemila.controller import Controller
    from genemila.providers.mock import MockProvider, ScriptedPlanner
    from genemila.report import run_query_only
    lab = lab_factory(final__ensemble=False, final__top_k=2, final__max_queries=3, schedule__max_planner_calls=2)
    Controller(lab, workers=2, seconds=45, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
               quiet=True).run()
    lab.cfg["final"]["ensemble"] = True
    rows = run_query_only(lab, 2, allow_new=True)
    kinds = [r["kind"] for r in rows]
    assert kinds[-1] == "baseline" and "ensemble" not in kinds and len(rows) <= 3
    again = run_query_only(lab, 2, allow_new=False)
    assert [r["experiment_id"] for r in again] == [r["experiment_id"] for r in rows]


def test_a_damaged_member_does_not_abort_the_report(lab_factory):
    from genemila.controller import Controller
    from genemila.providers.mock import MockProvider, ScriptedPlanner
    from genemila.report import run_query_only
    lab = lab_factory(final__ensemble=False, schedule__max_planner_calls=2)
    Controller(lab, workers=2, seconds=45, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
               quiet=True).run()
    singles = lab.db.query("SELECT * FROM experiments WHERE status='completed' AND kind!='baseline' "
                           "ORDER BY primary_score DESC LIMIT 2")
    (Path(singles[0]["artifact_dir"]) / "predictions.npz").write_bytes(b"not an npz")
    lab.cfg["final"]["ensemble"] = True
    rows = run_query_only(lab, 2, allow_new=True)
    assert [r["kind"] for r in rows][-1] == "baseline" and "ensemble" not in [r["kind"] for r in rows]
    assert lab.db.query("SELECT 1 FROM events WHERE kind='ensemble_error'")
    assert not lab.db.query("SELECT 1 FROM experiments WHERE status='reserved'")
    assert not lab.db.query("SELECT 1 FROM experiments WHERE kind='ensemble'")


def test_ensemble_mechanics_on_identical_members(lab_factory):
    """Two identical members average to themselves: the ensemble cannot beat them, so nothing is kept."""
    from genemila.report import ensemble_finalist
    from genemila.spec import ExperimentSpec
    from genemila.pipeline import run as run_pipeline
    lab = lab_factory()
    lab.record_analytic_baselines()
    recs = []
    for i in range(2):
        eid, _ = lab.queue(ExperimentSpec(hypothesis=f"ridge on builtins {i}", scientific_rationale="a reference model",
                                          feature_set=["control_mean", "mean_response", "is_target"],
                                          hyperparameters={"alpha_grid": [1.0]}, kind="config"))
        rec = lab.db.get_experiment(eid)
        if rec["status"] != "queued":  # the second is a duplicate configuration: run it anyway for the test
            lab.db.update_experiment(eid, status="queued")
        out = lab.artifacts / eid
        run_pipeline(ExperimentSpec.from_record(lab.db.get_experiment(eid)).run_spec(), lab.public_dir,
                     lab.run_dir / "plugins", out)
        ev = lab.evaluate_artifact(out / "predictions.npz")
        lab.db.update_experiment(eid, status="completed", primary_score=ev["metrics"]["primary"],
                                 best_alpha=ev["best_alpha"], artifact_dir=str(out), val_metrics_json=ev["metrics"])
        recs.append(lab.db.get_experiment(eid))
    assert ensemble_finalist(lab, recs) is None
    assert not lab.db.query("SELECT 1 FROM experiments WHERE status='reserved'")


MEMO_LEAKY = '''import numpy as np
from genemila.features.api import Feature, register
_MEMO = {}

@register
class F(Feature):
    name = "memo_leak"
    description = "Leaky through a module-level memo (test fixture)."
    rationale = "fixture"
    dim = 1

    def compute(self, ctx, perts, params):
        if "d" not in _MEMO:
            _MEMO["d"] = ctx.train_delta()
        names, d = _MEMO["d"]
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            if p in names:
                out[i, :, 0] = d[names.index(p)]
        return out
'''


def test_module_memo_cannot_hide_leakage_or_reach_a_fold(dataset, tmp_path):
    from genemila.pipeline import smoke
    from genemila.features import registry
    pub = export_public(dataset, tmp_path / "pub")
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "memo_leak.py").write_text(MEMO_LEAKY)
    r = smoke("memo_leak", pub, plugins, tmp_path / "smoke")
    assert r["status"] == "failed" and any("leakage" in p for p in r["problems"])
    # a fold view after a reload starts with an empty memo: the fold's labels are not in it
    import sys
    registry.load_plugins(plugins)
    ctx = FeatureContext(pub)
    registry.get("memo_leak")().compute(ctx, ctx.train_perts[:2], {})
    assert "d" in sys.modules["genemila_plugin_memo_leak"]._MEMO
    registry.reload_plugins()
    assert "d" not in sys.modules["genemila_plugin_memo_leak"]._MEMO


def test_label_independent_features_are_sliced_not_recomputed(dataset, tmp_path):
    pub = export_public(dataset, tmp_path / "pub")
    spec = {"experiment_id": "EXP_t", "feature_set": ["control_mean", "mean_response", "is_target"],
            "feature_params": {}, "model_type": "ridge",
            "hyperparameters": {"alpha_grid": [1.0], "cv_folds": 3, "cv_seed": 0}, "seed": 0}
    res = run(spec, pub, tmp_path / "plugins", tmp_path / "out", cache_dir=tmp_path / "cache")
    assert res["label_dependent_features"] == ["mean_response"]
    cache = tmp_path / "cache" / "features"
    assert len(list(cache.glob("control_mean__*.npy"))) == 2      # train and evals only, never per fold
    assert len(list(cache.glob("is_target__*.npy"))) == 2
    assert len(list(cache.glob("mean_response__*.npy"))) == 2 + 3  # plus one block per fold
    assert (next(cache.glob("control_mean__*.dep"))).read_text() == "0"
    assert (next(cache.glob("mean_response__*.dep"))).read_text() == "1"


@pytest.mark.parametrize("snippet", [
    "full = FeatureContext('../../public_data')",
    "full = type(ctx)('x')",
    "ctx.__init__('x')",
    "p = __file__",
])
def test_guard_blocks_constructing_contexts(snippet):
    from genemila.guard import CodeViolation, check_plugin_source
    from genemila.providers.mock import TEMPLATES
    code = TEMPLATES["coexpr"].replace("def compute(self, ctx, perts, params):",
                                       f"def compute(self, ctx, perts, params):\n        {snippet}")
    with pytest.raises(CodeViolation):
        check_plugin_source(code, "coexpr")
