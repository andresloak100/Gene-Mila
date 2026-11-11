"""Synthetic methodology checks; never fit or read a real data bundle."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np
import pytest

from genemila.features.api import FeatureContext
from tools import singleton_transfer_diagnostic as diagnostic


@pytest.fixture
def ctx(tmp_path):
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
    deltas = np.vstack([effects, [effects[2 * i] + effects[2 * i + 1] for i in range(10)]])
    np.savez(public / "public.npz", genes=genes, control_cells=control,
             perts=perts + ["unscored_metadata_only"], train_perts=perts,
             train_means=control.mean(0) + deltas)
    (public / "knowledge" / "targets.json").write_text(json.dumps(targets))
    external = {"genes": genes, "measured": [True] * len(genes), "sign": -1,
                "perts": {g: {"n_cells": 100, "delta": (-effects[i] + rng.normal(0, 0.04, 24)).tolist()}
                          for i, g in enumerate(genes[:20])}}
    (public / "knowledge" / "replogle2022_k562.json").write_text(json.dumps(external))
    return FeatureContext(public)


def _poison(ctx, names):
    changed = copy.copy(ctx)
    changed._train_delta = ctx._train_delta.copy()
    for pert in names:
        changed._train_delta[ctx._train_pos[pert]] += 1000 * np.arange(ctx.n_genes)
    return changed


def test_outer_hidden_responses_cannot_change_selected_alpha_or_predictions(ctx, monkeypatch):
    index, (fold, hide) = next((i, f) for i, f in enumerate(diagnostic._folds(ctx, 5, 0))
                              if set(f[1]) - set(f[0]))
    assert set(hide) - set(fold), "fixture must test the larger full gene-hide union"
    original_fit = diagnostic._fit_predictions
    observed = []

    def checked_fit(view, perts, alphas, seed, budget=None):
        assert not set(hide).intersection(view.train_perts)
        assert not set(perts).intersection(view.train_perts)
        observed.append(tuple(view.train_perts))
        return original_fit(view, perts, alphas, seed, budget)

    monkeypatch.setattr(diagnostic, "_fit_predictions", checked_fit)
    before, first = diagnostic.fit_outer(ctx, fold, hide, 0, index)
    after, second = diagnostic.fit_outer(_poison(ctx, hide), fold, hide, 0, index)
    assert first == second
    assert len(observed) == 8
    assert len(set(observed)) == 4
    for recipe in diagnostic.RECIPES_A:
        np.testing.assert_array_equal(before[recipe], after[recipe])


def test_inner_hidden_responses_cannot_change_fixed_alpha_predictions(ctx):
    _, outer_hide = diagnostic._folds(ctx, 5, 1)[0]
    outer = ctx.without_train(outer_hide)
    fold, hide = diagnostic._folds(outer, 3, 1100)[0]
    alpha = {arm: (1.0,) for arm in diagnostic.ARMS}
    before = diagnostic._fit_predictions(outer.without_train(hide), fold, alpha, 1100)
    after = diagnostic._fit_predictions(_poison(outer, hide).without_train(hide), fold, alpha, 1100)
    for arm in diagnostic.ARMS:
        np.testing.assert_array_equal(before[arm][1.0], after[arm][1.0])


def test_gene_folds_partition_predictions_and_hide_every_touched_gene(ctx):
    for seed in diagnostic.SEEDS:
        folds = diagnostic._folds(ctx, 5, seed)
        assert sorted(p for predict, _ in folds for p in predict) == sorted(ctx.train_perts)
        for predict, hide in folds:
            view = ctx.without_train(hide)
            singles = {ctx.target_genes(p)[0] for p in predict if len(ctx.target_genes(p)) == 1}
            assert all(not singles.intersection(ctx.target_genes(p)) for p in view.train_perts)
            for _, inner_hide in diagnostic._folds(view, 3, 1000 + 100 * seed):
                assert not set(hide).intersection(view.without_train(inner_hide).train_perts)


def _repeats(gains, errors=(1.0, 1.0, 1.0)):
    return [{"metrics": {"control": {"pearson_delta": 0.5, "mse": 1.0, "mse_top": 1.0},
                         "candidate": {"pearson_delta": 0.5 + gain, "mse": error, "mse_top": error}}}
            for gain, error in zip(gains, errors)]


def test_gate_uses_sample_sd_and_strict_pearson_threshold():
    result = diagnostic.gate(_repeats([0.0001, 0.0001, 0.009]))
    expected_sd = np.std([0.0001, 0.0001, 0.009], ddof=1)
    assert result["paired_gain_mean_sd"]["sd"] == pytest.approx(expected_sd)
    assert result["strict_threshold"] == pytest.approx(expected_sd)
    assert not result["passed"]
    assert not diagnostic.gate(_repeats([0.01, 0.01, 0]))["passed"]
    assert diagnostic.gate(_repeats([0.003, 0.004, 0.005]))["passed"]


def test_gate_error_guardrail_is_ratio_of_across_seed_means():
    at_boundary = diagnostic.gate(_repeats([0.01] * 3, (1.01,) * 3))
    assert at_boundary["passed"]
    assert at_boundary["error_guardrails"]["mse"]["ratio"] == pytest.approx(1.01)
    assert not diagnostic.gate(_repeats([0.01] * 3, (1.010001,) * 3))["passed"]
    uneven = _repeats([0.01] * 3, (1.02, 1.0, 1.0))
    assert diagnostic.gate(uneven)["passed"]
    unequal_baselines = _repeats([0.01] * 3, (2.0, 10.0, 100.0))
    for repeat, baseline in zip(unequal_baselines, (1.0, 10.0, 100.0)):
        for metric in ("mse", "mse_top"):
            repeat["metrics"]["control"][metric] = baseline
    result = diagnostic.gate(unequal_baselines)
    assert result["passed"]  # Mean of per-seed ratios would wrongly fail.
    assert result["error_guardrails"]["mse"]["ratio"] == pytest.approx(112 / 111)
    with pytest.raises(ValueError, match="all three"):
        diagnostic.gate(uneven[:2])


def test_b1_refits_use_fresh_plugin_state_restricted_context_and_identical_base_matrices(ctx, tmp_path, monkeypatch):
    package = tmp_path / "package"
    source = '''import numpy as np
from genemila.features.api import Feature, register
calls = 0
@register
class Snapshot(Feature):
    name = "snapshot_feature"
    dim = 1
    def compute(self, ctx, perts, params):
        global calls
        calls += 1
        assert calls <= 2
        if calls == 1:
            assert perts == ctx.train_perts
            ctx.cache["training_batch"] = tuple(perts)
        else:
            assert not set(perts).intersection(ctx.train_perts)
            assert ctx.cache["training_batch"] == tuple(ctx.train_perts)
        values = []
        for pert in perts:
            _, y = ctx.train_delta(exclude=pert)
            values.append(y.mean(0) + np.random.normal(0, .001, ctx.n_genes))
        return np.array(values)[:, :, None]
'''
    members = []
    for i in range(3):
        plugins = package / "members" / str(i) / "plugins"
        plugins.mkdir(parents=True)
        (plugins / "snapshot.py").write_text(source)
        members.append({"features": ["control_mean", "snapshot_feature"], "feature_params": {},
                        "columns": ["control_mean", "snapshot_feature"], "seed": i + 1,
                        "alpha": (1.0, 100.0, 10000.0)[i], "experiment_id": f"synthetic_{i}"})
    fold, hide = diagnostic._folds(ctx, 5, 2)[0]
    calls = []
    original = diagnostic._ridge_predictions

    def paired_matrix_check(train, predict, truth, alphas, seed, budget, stage):
        calls.append((train.copy(), predict.copy(), alphas, seed))
        return original(train, predict, truth, alphas, seed, budget, stage)

    monkeypatch.setattr(diagnostic, "_ridge_predictions", paired_matrix_check)
    before, meta = diagnostic.fit_b1_outer(ctx, fold, hide, package, members, diagnostic.Budget())
    after, second = diagnostic.fit_b1_outer(_poison(ctx, hide), fold, hide, package, members, diagnostic.Budget())
    assert meta == second
    for key in before:
        np.testing.assert_array_equal(before[key], after[key])
    for i in range(0, len(calls), 2):
        np.testing.assert_array_equal(calls[i][0], calls[i + 1][0][:, :-1])
        np.testing.assert_array_equal(calls[i][1], calls[i + 1][1][:, :-1])
        assert calls[i][2:] == calls[i + 1][2:]
    for arm in diagnostic.ARMS:
        np.testing.assert_array_equal(before[arm], np.mean([before[f"{arm}_member_{i}"] for i in range(3)], axis=0))


def test_failed_stage_a_never_starts_stage_b_and_keeps_all_seed_metrics(ctx, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Stage B must not run after a failed fixed gate")

    monkeypatch.setattr(diagnostic, "fit_b1_outer", forbidden)
    original_gate = diagnostic.gate
    monkeypatch.setattr(diagnostic, "gate", lambda repeats: {**original_gate(repeats), "passed": False})
    summary, artifacts, events = {"stages": {}}, {}, []
    budget = diagnostic.Budget()
    diagnostic.diagnose(ctx, Path("unused"), {}, summary, artifacts, budget,
                        lambda kind, **details: events.append((kind, details)))
    assert summary["status"] == "complete"
    assert summary["stages"]["B"]["status"] == "skipped"
    assert budget.fits == {"A": 480, "B": 0}
    repeats = summary["stages"]["A"]["repeats"]
    assert [r["seed"] for r in repeats] == [0, 1, 2]
    for recipe in diagnostic.RECIPES_A:
        assert set(repeats[0]["metrics"][recipe]) == set(diagnostic.METRICS)
        observed = [r["metrics"][recipe]["pearson_delta"] for r in repeats]
        result = summary["stages"]["A"]["mean_sd_over_seeds"][recipe]["pearson_delta"]
        assert result["mean"] == pytest.approx(np.mean(observed))
        assert result["sd"] == pytest.approx(np.std(observed, ddof=1))
    assert len([e for e in events if e[0] == "fold_completed"]) == 15
    assert len(artifacts) == 15
    assert all(np.isfinite(array).all() for array in artifacts.values())


def test_cli_refuses_existing_output_without_reading_inputs(tmp_path, monkeypatch):
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("preserve")
    monkeypatch.setattr(diagnostic, "load_export", lambda *a: pytest.fail("must not read package"))
    with pytest.raises(FileExistsError):
        diagnostic.main(["--package", str(tmp_path / "package"), "--manifest-sha256", diagnostic.MANIFEST_SHA256,
                         "--out", str(out)])
    assert sentinel.read_text() == "preserve"
    with pytest.raises(ValueError, match="separate"):
        diagnostic.run(tmp_path, diagnostic.MANIFEST_SHA256, tmp_path / "nested")


@pytest.mark.parametrize("failure,status", [(TimeoutError("time limit"), "timed_out"),
                                            (ValueError("bad input"), "failed")])
def test_failures_preserve_config_summary_and_partial_predictions(ctx, tmp_path, monkeypatch, failure, status):
    package = tmp_path / "package"
    package.mkdir()
    manifest = {"members": [{"model_type": "ridge"}] * 3}
    monkeypatch.setattr(diagnostic, "load_export", lambda *a: manifest)
    monkeypatch.setattr(diagnostic, "FeatureContext", lambda *a, **kw: ctx)
    monkeypatch.setattr(diagnostic, "fixed_config", lambda *a: {"status": "fixed_before_fitting"})
    out = tmp_path / "newrun"

    calls = []

    def failed_fit(view, fold, hide, seed, index, budget):
        assert json.loads((out / "config.json").read_text())["status"] == "fixed_before_fitting"
        calls.append(index)
        if len(calls) > 1:
            raise failure
        values = {recipe: np.ones((len(fold), view.n_genes)) for recipe in diagnostic.RECIPES_A}
        return values, {"predict": fold, "hide": hide, "train": view.without_train(hide).train_perts}

    monkeypatch.setattr(diagnostic, "fit_outer", failed_fit)
    with pytest.raises(type(failure)):
        diagnostic.run(package, diagnostic.MANIFEST_SHA256, out)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == status
    assert summary["config_sha256"] == diagnostic._hash(out / "config.json")
    assert len(summary["stages"]["A"]["repeats"][0]["folds"]) == 1
    with np.load(out / "predictions.npz", allow_pickle=False) as arrays:
        partial = arrays["stage_A_seed_0_control"]
        assert np.isfinite(partial).any() and np.isnan(partial).any()


def test_expired_budget_stops_before_any_fit():
    budget = diagnostic.Budget(seconds=-1)
    with pytest.raises(TimeoutError):
        budget.fit("A")
    assert budget.fits == {"A": 0, "B": 0}


def test_failed_checkpoint_write_preserves_last_complete_summary(tmp_path):
    path = tmp_path / "summary.json"
    diagnostic._json_write(path, {"completed_folds": 1})
    with pytest.raises(ValueError):
        diagnostic._json_write(path, {"invalid": float("nan")})
    assert json.loads(path.read_text()) == {"completed_folds": 1}


def test_parent_deadline_preserves_corrupt_checkpoint_and_records_failure(tmp_path, monkeypatch):
    source = diagnostic.REPO / "docs/results/singleton_transfer_development_20261013/run_with_deadline.py"
    spec = importlib.util.spec_from_file_location("transfer_deadline", source)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    out = tmp_path / "newrun"

    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 7200
        out.mkdir()
        (out / "summary.json").write_bytes(b'{"interrupted":')
        raise subprocess.TimeoutExpired(args[0], 7200)

    monkeypatch.setattr(launcher.subprocess, "run", timeout)
    assert launcher.launch(tmp_path / "package", out) == 124
    assert (out / "summary.interrupted.json").read_bytes() == b'{"interrupted":'
    assert json.loads((out / "summary.json").read_text())["status"] == "timed_out"
    with pytest.raises(FileExistsError):
        launcher.launch(tmp_path / "package", out)
