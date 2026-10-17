"""Synthetic per-row edge semantics, one-file snapshot and shared-fold checks."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from test_b1_development_diagnostic import synthetic as base_synthetic
from genemila.features import registry
from genemila.guard import check_plugin_source
from tools import b1_pair_batch_correction as correction

base = correction.base

# Minimal independent legacy implementation of the original whole-batch rule.
LEGACY_EDGE = '''import numpy as np
from genemila.features.api import Feature, register
@register
class LegacyEdge(Feature):
    name = "pair_target_prior_edge_e34"
    version = 2
    def compute(self, ctx, perts, params):
        lookup = {tuple(sorted((a,b))):float(w) for a,b,w in ctx.knowledge("prior_network") if np.isfinite(float(w))}
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i,p in enumerate(perts):
            t = ctx.target_genes(p)
            if len(t)==2:
                out[i,:,0] = lookup.get(tuple(sorted(t)),0.)
        if not np.any(out):
            for i,p in enumerate(perts):
                t = ctx.target_genes(p)
                if len(t)==2 and all(g in ctx.gene_index for g in t):
                    w = ctx.gene_corr[ctx.gene_index[t[0]],ctx.gene_index[t[1]]]
                    if np.isfinite(w): out[i,:,0] = w
        return out
'''

# The original e401 compute body, preserved in the synthetic snapshot.
PRODUCT = '''import numpy as np
from genemila.features.api import Feature, register
@register
class AdditiveSinglesTimesPairPriorEdgeE401(Feature):
    name = "additive_singles_times_pair_prior_edge_e401"
    def compute(self, ctx, perts, params):
        a = ctx.feature("additive_singles_e15", perts)
        b = ctx.feature("pair_target_prior_edge_e34", perts)
        a = np.asarray(a, dtype=np.float64)
        b = np.asarray(b, dtype=np.float64)
        if a.ndim == 2: a = a[:, :, None]
        if b.ndim == 2: b = b[:, :, None]
        out = a * b
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
'''


@pytest.fixture
def synthetic(base_synthetic):
    package, _, manifest = base_synthetic
    plugins = package / "members/1/plugins"
    (plugins / correction.EDGE_FILE).write_text(LEGACY_EDGE)
    (plugins / "additive_singles_times_pair_prior_edge_e401.py").write_text(PRODUCT)
    (plugins / "additive_singles_e15.py").write_text('''from genemila.features.api import register
from genemila.features.builtin import AdditiveResponse
@register
class AdditiveSingles(AdditiveResponse):
    name = "additive_singles_e15"
''')
    knowledge = package / "context/knowledge/prior_network.json"
    knowledge.write_text(json.dumps([["G0", "G1", .7], ["G2", "G3", -.2], ["G4", "G5", 0.]]))
    features = ["pair_target_prior_edge_e34", "additive_singles_times_pair_prior_edge_e401"]
    manifest["members"][1]["features"].extend(features)
    manifest["members"][1]["columns"].extend(features)
    return package, base.FeatureContext(package / "context"), manifest


@pytest.fixture
def edge_plugins(tmp_path):
    original, variant = tmp_path / "original", tmp_path / "variant"
    original.mkdir(); variant.mkdir()
    (original / correction.EDGE_FILE).write_text(LEGACY_EDGE)
    shutil.copyfile(correction.VARIANT_SOURCE, variant / correction.EDGE_FILE)
    (variant / "e401.py").write_text(PRODUCT)
    return original, variant


def edge_context():
    genes = list("ABCDEFGH")
    index = {g: i for i, g in enumerate(genes)}
    corr = np.eye(8)
    corr[4, 5] = corr[5, 4] = .4
    corr[6, 7] = corr[7, 6] = -.2
    corr[0, 2] = corr[2, 0] = np.nan
    targets = {"positive": ["A", "B"], "negative": ["C", "D"], "missing": ["E", "F"],
        "reverse": ["F", "E"], "zero": ["G", "H"], "nonfinite": ["A", "C"],
        "unknown": ["A", "OUTSIDE"], "singleton": ["A"]}
    ctx = SimpleNamespace(n_genes=8, gene_index=index, gene_corr=corr, cache={},
        target_genes=lambda p: targets[p], knowledge=lambda name: [["A", "B", 2.], ["C", "D", -3.], ["G", "H", 0.], ["A", "C", float("nan")]])

    def feature(name, perts, params=None):
        if name == "additive_singles_e15":
            return np.broadcast_to(np.arange(1., 9.)[None, :, None], (len(perts), 8, 1)).copy()
        return registry.get(name)().compute(ctx, perts, params or {})

    ctx.feature = feature
    return ctx


def test_per_row_fallback_preserves_matched_signs_and_standalone_semantics(edge_plugins):
    original, variant = edge_plugins
    names = ["positive", "negative", "missing", "zero", "nonfinite", "unknown", "singleton"]
    ctx = edge_context()
    with base._plugins(original):
        old_alone = {p: registry.get("pair_target_prior_edge_e34")().compute(ctx, [p], {})[0] for p in names}
        legacy_mix = registry.get("pair_target_prior_edge_e34")().compute(ctx, names, {})
    with base._plugins(variant):
        cls = registry.get("pair_target_prior_edge_e34")
        assert cls.version == 3 and cls.inputs == ["prior_network", "control_cells"]
        corrected = cls().compute(ctx, names, {})
        for i, p in enumerate(names):
            np.testing.assert_array_equal(corrected[i], old_alone[p])
        assert np.all(corrected[0] == 2.) and np.all(corrected[1] == -3.)
        assert np.all(corrected[2] == .4) and np.all(corrected[3] == -.2)
        assert np.all(corrected[4:] == 0.) and np.all(legacy_mix[2:4] == 0.)
        np.testing.assert_array_equal(corrected, cls().compute(ctx, names[::-1], {})[::-1])
        np.testing.assert_array_equal(cls().compute(ctx, ["missing"], {}), cls().compute(ctx, ["reverse"], {}))
        for extra in ("positive", "negative", "singleton"):
            np.testing.assert_array_equal(cls().compute(ctx, ["missing"], {})[0], cls().compute(ctx, [extra, "missing"], {})[1])
    assert check_plugin_source(correction.VARIANT_SOURCE.read_text(), "pair_target_prior_edge_e34")["class_name"] == "PairTargetPriorEdge"


def test_e401_composed_product_is_independent_of_unrelated_query_rows(edge_plugins):
    _, variant = edge_plugins
    ctx = edge_context()
    with base._plugins(variant):
        alone = ctx.feature("additive_singles_times_pair_prior_edge_e401", ["missing"])
        batch = ctx.feature("additive_singles_times_pair_prior_edge_e401", ["positive", "missing", "negative"])
        np.testing.assert_array_equal(alone[0], batch[1])
        np.testing.assert_array_equal(alone[0, :, 0], np.arange(1., 9.) * .4)
        np.testing.assert_array_equal(batch, ctx.feature("additive_singles_times_pair_prior_edge_e401", ["negative", "missing", "positive"])[::-1])


def snapshot(synthetic, tmp_path):
    package, ctx, manifest = synthetic
    out = tmp_path / "snapshot"
    out.mkdir()
    pins = correction.prepare_snapshot(package, out)
    return package, ctx, manifest, pins


def test_only_e34_snapshot_diff_and_full_extra_hide_poisoning(synthetic, tmp_path):
    package, ctx, manifest, pins = snapshot(synthetic, tmp_path)
    changed = [name for name, pin in pins["original_files_sha256"].items() if pin != pins["copied_files_sha256"][name]]
    assert changed == [correction.EDGE_FILE]
    assert pins["variant_e34_sha256"] == pins["published_variant_sha256"] == base._hash(correction.VARIANT_SOURCE)
    predict, hide = next((p, h) for p, h in base._folds(ctx, 12) if set(h) - set(p))
    assert set(hide) - set(predict)
    meta = base.fold_metadata(ctx, predict, hide, 0, set())
    untouched = copy.deepcopy(manifest)
    expected = correction.fit_outer(ctx, package, manifest["members"], Path(pins["copied_directory"]), meta, base.Budget())
    poisoned = copy.copy(ctx); poisoned._train_delta = ctx._train_delta.copy()
    for p in hide:
        poisoned._train_delta[ctx._train_pos[p]] = np.arange(ctx.n_genes) * 1e9
    actual = correction.fit_outer(poisoned, package, manifest["members"], Path(pins["copied_directory"]), meta, base.Budget())
    assert manifest == untouched
    for arm in correction.ARMS:
        np.testing.assert_array_equal(expected[arm], actual[arm])


def prepare_run(synthetic, monkeypatch):
    package, ctx, manifest = synthetic
    monkeypatch.setattr(base, "load_export", lambda *args: manifest)
    original = base._hash
    monkeypatch.setattr(base, "_hash", lambda p: original(p) if p.is_file() else hashlib.sha256(str(p).encode()).hexdigest())
    return package, ctx, manifest


def test_prefit_pins_same_r2_spec_and_45_shared_fits(synthetic, monkeypatch, tmp_path):
    package, ctx, manifest = prepare_run(synthetic, monkeypatch)
    out = tmp_path / "run"
    original, calls = base.fit_member, []
    untouched = copy.deepcopy(manifest)

    def fit(view, predict, plugins, member, budget):
        config = json.loads((out / "config.json").read_text())
        assert config["outer_seeds"] == [12, 13, 14] and config["max_ridge_fits"] == 45
        assert config["variant_spec"] == manifest["members"][1] and member["seed"] in (1, 2)
        assert config["variant_spec"]["alpha"] == .00198 and config["gate"] == correction.GATE
        assert "tools/feature_variants/pair_target_prior_edge_e34.py" in config["source_sha256"]
        assert "docs/results/b1_pair_batch_20261013/run_with_deadline.py" in config["source_sha256"]
        changed = [n for n, h in config["plugin_snapshot"]["original_files_sha256"].items()
                   if h != config["plugin_snapshot"]["copied_files_sha256"][n]]
        assert changed == [correction.EDGE_FILE]
        calls.append((str(plugins), copy.deepcopy(member)))
        return original(view, predict, plugins, member, budget)

    monkeypatch.setattr(base, "fit_member", fit)
    summary = correction.run(package, base.MANIFEST_SHA256, out)
    assert summary["status"] == "complete" and summary["fit_count"] == len(calls) == 45 and manifest == untouched
    for i in range(0, 45, 3):
        assert calls[i][1]["seed"] == 1
        assert calls[i + 1][1] == calls[i + 2][1] == manifest["members"][1]
        assert calls[i + 1][0] == str(package / "members/1/plugins")
        assert calls[i + 2][0] == str(out / "corrected_r2_plugins")
    with np.load(out / "predictions.npz", allow_pickle=False) as saved:
        for repeat in summary["repeats"]:
            seed = repeat["seed"]
            assert sorted(p for f in repeat["folds"] for p in f["predict"]) == sorted(ctx.train_perts)
            np.testing.assert_array_equal(saved[f"seed_{seed}_candidate"], (saved[f"seed_{seed}_member_0"] + saved[f"seed_{seed}_corrected_member_1"]) / 2)
            np.testing.assert_array_equal(saved[f"seed_{seed}_fixed_ensemble"], (saved[f"seed_{seed}_member_0"] + saved[f"seed_{seed}_member_1"]) / 2)
    config = json.loads((out / "config.json").read_text())
    for name, pin in config["plugin_snapshot"]["copied_files_sha256"].items():
        assert base._hash(out / "corrected_r2_plugins" / name) == pin
    original_bytes = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError): correction.run(package, base.MANIFEST_SHA256, out)
    assert (out / "summary.json").read_bytes() == original_bytes and len(calls) == 45


@pytest.mark.parametrize("failure,status", [(RuntimeError("corrected fit failed"), "failed"), (TimeoutError("deadline"), "timed_out")])
def test_failure_preserves_original_members_and_snapshot(synthetic, monkeypatch, tmp_path, failure, status):
    package, _, _ = prepare_run(synthetic, monkeypatch)
    original, calls = base.fit_member, 0

    def fit(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3: raise failure
        return original(*args, **kwargs)

    monkeypatch.setattr(base, "fit_member", fit)
    out = tmp_path / "stopped"
    with pytest.raises(type(failure), match=str(failure)): correction.run(package, base.MANIFEST_SHA256, out)
    assert json.loads((out / "summary.json").read_text())["status"] == status
    assert (out / "corrected_r2_plugins" / correction.EDGE_FILE).read_bytes() == correction.VARIANT_SOURCE.read_bytes()
    with np.load(out / "predictions.npz", allow_pickle=False) as saved:
        assert np.isfinite(saved["seed_12_member_0"]).any() and np.isfinite(saved["seed_12_member_1"]).any()
        assert np.isnan(saved["seed_12_corrected_member_1"]).all()


def gate_rows(gains=(.02, .02, .02), errors=(1., 1., 1.), control=(1., 1., 1.), additive=(1., 1., 1.)):
    return [{"metrics": {"fixed_ensemble": {"pearson_delta": 0., "mse": c, "mse_top": c},
        "candidate": {"pearson_delta": g, "mse": e, "mse_top": e}, "additive": {"mse": a, "mse_top": a}}}
        for g, e, c, a in zip(gains, errors, control, additive)]


def test_gate_strict_pearson_and_four_ratio_of_mean_error_checks():
    assert correction.gate(gate_rows())["passed"]
    assert not correction.gate(gate_rows(gains=(.002, .002, .002)))["passed"]
    assert not correction.gate(gate_rows(gains=(0., .02, .02)))["checks"]["pearson_gain_each_positive"]
    varied = correction.gate(gate_rows(gains=(.0001, .0001, .1)))
    assert varied["primary_pearson_gain_mean_sd"]["sd"] == np.std(varied["primary_pearson_gains"], ddof=1)
    assert not varied["checks"]["pearson_gain_mean_above_threshold"]
    ratios = correction.gate(gate_rows(errors=(2., 99., 100.), control=(1., 100., 100.), additive=(1., 100., 100.)))
    assert ratios["passed"] and all(r["ratio"] == 1. for r in ratios["error_guardrails"].values())
    assert correction.gate(gate_rows(errors=(1.01, 1.01, 1.01)))["passed"]
    assert not correction.gate(gate_rows(errors=(1.01001, 1.01001, 1.01001)))["passed"]
    assert not correction.gate(gate_rows(additive=(.9, .9, .9)))["passed"]
    with pytest.raises(ValueError, match="three completed"): correction.gate(gate_rows()[:2])


def test_parent_timeout_keeps_arrays_snapshot_and_exclusive_directory(tmp_path, monkeypatch):
    import importlib.util
    import subprocess
    source = correction.REPO / "docs/results/b1_pair_batch_20261013/run_with_deadline.py"
    spec = importlib.util.spec_from_file_location("pair_batch_deadline", source)
    launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
    out = tmp_path / "deadline"
    checkpoint = {"status": "running", "fit_count": 2, "repeats": [{"seed": 12}]}

    def timeout(command, **kwargs):
        assert kwargs["timeout"] == 7200 and command[1].endswith("tools/b1_pair_batch_correction.py")
        out.mkdir(); (out / "corrected_r2_plugins").mkdir()
        base._json_write(out / "summary.json", checkpoint)
        (out / "predictions.npz").write_bytes(b"retained partial numeric artifact")
        (out / "corrected_r2_plugins" / correction.EDGE_FILE).write_bytes(correction.VARIANT_SOURCE.read_bytes())
        raise subprocess.TimeoutExpired(command, 7200)

    monkeypatch.setattr(launcher.subprocess, "run", timeout)
    assert launcher.launch(tmp_path / "package", out) == 124
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "timed_out" and saved["fit_count"] == 2 and saved["repeats"] == checkpoint["repeats"]
    assert (out / "predictions.npz").read_bytes() == b"retained partial numeric artifact"
    assert (out / "corrected_r2_plugins" / correction.EDGE_FILE).read_bytes() == correction.VARIANT_SOURCE.read_bytes()
    unchanged = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError): launcher.launch(tmp_path / "package", out)
    assert (out / "summary.json").read_bytes() == unchanged
