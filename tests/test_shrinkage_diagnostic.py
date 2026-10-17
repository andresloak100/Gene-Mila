"""Methodology checks on synthetic public-only data; no real bundle is accessed."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from genemila.features.api import FeatureContext
from tools import shrinkage_diagnostic as diagnostic


@pytest.fixture
def public_bundle(tmp_path):
    public = tmp_path / "public"
    (public / "knowledge").mkdir(parents=True)
    genes = [f"G{i:02}" for i in range(24)]
    singles = [f"single_{i}" for i in range(20)]
    pairs = [f"pair_{i}" for i in range(10)]
    perts = singles + pairs
    targets = {p: [genes[i]] for i, p in enumerate(singles)}
    targets.update({p: [genes[2 * i], genes[2 * i + 1]] for i, p in enumerate(pairs)})
    rng = np.random.default_rng(22)
    control = 3 + np.linspace(0, 2, 24)[None, :] + rng.normal(0, 0.03, (8, 24))
    effects = rng.normal(0, 0.15, (20, 24)) + np.linspace(-0.2, 0.2, 24)
    deltas = np.vstack([effects, np.array([effects[2 * i] + effects[2 * i + 1] for i in range(10)])])
    np.savez(public / "public.npz", genes=genes, control_cells=control,
             perts=perts + ["unscored_metadata_only"], train_perts=perts,
             train_means=control.mean(0) + deltas)
    (public / "knowledge" / "targets.json").write_text(json.dumps(targets))
    (public / "manifest.json").write_text(json.dumps({"name": "synthetic_methodology", "split_id": "public-only"}))
    return public


def test_outer_response_changes_cannot_change_fit_or_calibration(public_bundle, monkeypatch):
    ctx = FeatureContext(public_bundle)
    fold, hide = diagnostic._folds(ctx, diagnostic.OUTER_FOLDS, 0)[0]
    changed = copy.copy(ctx)
    changed._train_delta = ctx._train_delta.copy()
    hidden_rows = [i for i, p in enumerate(ctx.train_perts) if p in hide]
    changed._train_delta[hidden_rows] += 1000 * np.arange(ctx.n_genes)
    observed_views = []
    original_fit = diagnostic._fit_predictions

    def checked_fit(view, perts, alphas, seed):
        assert not set(view.train_perts).intersection(hide)
        assert not set(view.train_perts).intersection(perts)
        observed_views.append(tuple(view.train_perts))
        return original_fit(view, perts, alphas, seed)

    monkeypatch.setattr(diagnostic, "_fit_predictions", checked_fit)
    before, meta_before = diagnostic.fit_outer(ctx, fold, hide, 0, 0)
    after, meta_after = diagnostic.fit_outer(changed, fold, hide, 0, 0)
    assert meta_before == meta_after
    for recipe in diagnostic.RECIPES:
        np.testing.assert_array_equal(before[recipe], after[recipe])
    assert len(observed_views) == 2 * (diagnostic.INNER_FOLDS + 1)
    assert all(not set(row["train"]).intersection(row["hide"]) for row in meta_before["inner_folds"])


def test_builtins_are_recomputed_under_each_restricted_view(public_bundle, monkeypatch):
    ctx = FeatureContext(public_bundle)
    seen = []
    original = diagnostic._matrix

    def checked_matrix(view, perts):
        # A full-training cached label-dependent feature must never reach an inner/outer fit.
        assert len(view.train_perts) < len(ctx.train_perts)
        seen.append(tuple(view.train_perts))
        return original(view, perts)

    monkeypatch.setattr(diagnostic, "_matrix", checked_matrix)
    fold, hide = diagnostic._folds(ctx, diagnostic.OUTER_FOLDS, 1)[0]
    _, meta = diagnostic.fit_outer(ctx, fold, hide, 1, 0)
    assert len(seen) == diagnostic.INNER_FOLDS + 1
    assert seen[-1] == tuple(meta["train"])
    assert len(set(seen)) > 1


@pytest.mark.parametrize("truth, expected", [
    (np.array([[2.0, 4.0]]), 2.0),
    (np.array([[10.0, 20.0]]), 4.0),
    (np.array([[-1.0, -2.0]]), 0.0),
])
def test_calibration_is_training_ls_with_fixed_bounds(truth, expected):
    result = diagnostic._calibration(np.array([[1.0, 2.0]]), truth)
    assert result["scale"] == expected
    assert not result["zero_denominator"]


def test_zero_signal_calibration_is_identity_and_positive_scale_preserves_pearson():
    assert diagnostic._calibration(np.zeros((1, 3)), np.ones((1, 3)))["scale"] == 1.0
    p = np.array([[0.2, -0.1, 0.5], [-0.2, 0.4, 0.1]])
    d = np.array([[0.7, -0.2, 0.3], [-0.5, 0.6, 0.2]])
    assert diagnostic._pearson_delta(3 * p, d) == pytest.approx(diagnostic._pearson_delta(p, d), abs=1e-12)


def test_real_entry_point_reads_only_allowed_public_inputs(public_bundle, tmp_path, monkeypatch):
    original_load = np.load
    original_read_text = Path.read_text
    opened_npz = []
    opened_text = []

    def checked_load(path, *args, **kwargs):
        path = Path(path).resolve()
        assert path == (public_bundle / "public.npz").resolve()
        opened_npz.append(path)
        return original_load(path, *args, **kwargs)

    def checked_read_text(path, *args, **kwargs):
        assert path.resolve() in {(public_bundle / "knowledge" / "targets.json").resolve(),
                                  (public_bundle / "manifest.json").resolve()}
        opened_text.append(path.resolve())
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(np, "load", checked_load)
    monkeypatch.setattr(Path, "read_text", checked_read_text)
    out = tmp_path / "new_diagnostic"
    original_diagnose = diagnostic.diagnose

    def config_precedes_fit(ctx):
        config = json.loads(original_read_text(out / "config.json"))
        assert config["status"] == "fixed_before_fitting"
        assert config["alphas"] == list(diagnostic.ALPHAS)
        assert config["outer_seeds"] == [0, 1, 2]
        return original_diagnose(ctx)

    monkeypatch.setattr(diagnostic, "diagnose", config_precedes_fit)
    summary = diagnostic.run(public_bundle, out)
    assert opened_npz == [(public_bundle / "public.npz").resolve()]
    assert set(opened_text) == {(public_bundle / "knowledge" / "targets.json").resolve(),
                                (public_bundle / "manifest.json").resolve()}
    assert summary["status"] == "complete"
    assert "unscored_metadata_only" not in summary["scored_training_perturbations"]
    assert [repeat["seed"] for repeat in summary["repeats"]] == [0, 1, 2]
    assert list(summary["mean_sd_over_seeds"]) == list(diagnostic.RECIPES)
    assert (out / "summary.json").exists()
    for recipe in diagnostic.RECIPES:
        for metric in diagnostic.METRICS:
            values = [repeat["metrics"][recipe][metric] for repeat in summary["repeats"]]
            aggregated = summary["mean_sd_over_seeds"][recipe][metric]
            assert aggregated["mean"] == pytest.approx(np.mean(values))
            assert aggregated["sd"] == pytest.approx(np.std(values, ddof=1))


def test_existing_directory_and_bundle_output_are_refused(public_bundle, tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("original")
    with pytest.raises(FileExistsError):
        diagnostic.run(public_bundle, out)
    assert sentinel.read_text() == "original"
    with pytest.raises(ValueError, match="input bundle"):
        diagnostic.run(public_bundle, public_bundle / "output")
    assert not (public_bundle / "output").exists()


def test_degenerate_fold_fails_without_trying_another_split(public_bundle, monkeypatch):
    ctx = FeatureContext(public_bundle)
    monkeypatch.setattr(diagnostic, "cv_folds_of", lambda train, count, seed, targets:
                        [(train, train)] * count)
    with pytest.raises(ValueError, match="partition"):
        diagnostic.diagnose(ctx)
    with pytest.raises(ValueError, match="three distinct"):
        diagnostic.fit_outer(ctx, ctx.train_perts, ctx.train_perts, 0, 0)


def test_nonfinite_response_stops_with_preserved_config(public_bundle, tmp_path, monkeypatch):
    original_diagnose = diagnostic.diagnose

    def bad_training(ctx):
        ctx._train_delta[0, 0] = np.nan
        return original_diagnose(ctx)

    monkeypatch.setattr(diagnostic, "diagnose", bad_training)
    out = tmp_path / "failed_diagnostic"
    with pytest.raises(ValueError, match="nonfinite"):
        diagnostic.run(public_bundle, out)
    assert (out / "config.json").exists()
    assert (out / "FAILED.txt").exists()
    assert not (out / "summary.json").exists()
