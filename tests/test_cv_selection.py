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
    assert len(list((tmp_path / "cache" / "features").glob("mean_response__*.npy"))) >= 1 + 2 * 3


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
