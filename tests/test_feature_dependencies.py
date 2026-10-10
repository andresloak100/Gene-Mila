"""Dependency sources stay available without becoming predictor columns."""

import json
import os

import numpy as np
import pytest

from genemila.features import registry
from genemila.features.api import FeatureContext
from genemila.pipeline import build_matrix, feature_blocks, run


@pytest.fixture
def public_data(tmp_path):
    """A tiny wholly artificial public bundle; no evaluator or held-out labels."""
    public = tmp_path / "public"
    (public / "knowledge").mkdir(parents=True)
    np.savez(public / "public.npz", genes=np.array(["g1", "g2", "g3"]),
             control_cells=np.array([[1., 2., 3.], [3., 4., 5.]]),
             perts=np.array(["a", "b", "c", "d"]), train_perts=np.array(["a", "b", "c"]),
             train_means=np.array([[3., 4., 5.], [4., 6., 8.], [5., 8., 11.]]))
    (public / "knowledge" / "targets.json").write_text("{}")
    (public / "manifest.json").write_text(json.dumps({"name": "artificial", "split_id": "one"}))
    return public


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path):
    # Tests and repeated in-process experiments must not retain another directory's sources.
    empty = tmp_path / "empty_plugins"
    empty.mkdir()
    registry.load_plugins(empty)
    yield
    registry.load_plugins(empty)
    FeatureContext._preloaded.clear()


def write_feature(plugins, name, body, dependencies=(), params=None):
    plugins.mkdir(exist_ok=True)
    path = plugins / f"{name}.py"
    path.write_text(
        "import numpy as np\nfrom genemila.features.api import Feature, register\n"
        f"@register\nclass F(Feature):\n    name = {name!r}\n"
        f"    dependencies = {list(dependencies)!r}\n    params = {params or {}!r}\n"
        f"    def compute(self, ctx, perts, params):\n        {body}\n")
    return path


def chain(tmp_path):
    plugins = tmp_path / "plugins"
    write_feature(plugins, "leaf", "return np.broadcast_to(ctx.control_mean[None, :, None] * params['scale'], (len(perts), ctx.n_genes, 1)).copy()", params={"scale": 1.})
    write_feature(plugins, "middle", "return ctx.feature('leaf', perts) + 1", ["leaf"])
    write_feature(plugins, "composite", "return ctx.feature('middle', perts) * 2", ["middle"])
    registry.load_plugins(plugins)
    return plugins


def test_dependency_only_sources_and_transitive_params(public_data, tmp_path):
    chain(tmp_path)
    ctx = FeatureContext(public_data)
    perts = ctx.train_perts
    assert registry.dependency_closure(["composite"]) == ["leaf", "middle", "composite"]
    configured = {"leaf": {"scale": 3.}}
    matrix, columns = build_matrix(ctx, ["composite"], configured, perts, {})
    assert columns == ["composite"]  # neither dependency adds a model column
    expected = np.tile((ctx.control_mean * 3 + 1) * 2, len(perts))[:, None]
    np.testing.assert_array_equal(matrix, expected)
    np.testing.assert_array_equal(ctx.feature("leaf", perts, {"scale": 4.})[0, :, 0], ctx.control_mean * 4)
    view = ctx.without_train([perts[0]])
    np.testing.assert_array_equal(view.feature("composite", perts), ctx.feature("composite", perts))


def test_transitive_parameter_and_source_changes_invalidate_warm_cache(public_data, tmp_path):
    plugins = chain(tmp_path)
    ctx = FeatureContext(public_data)
    perts = ctx.train_perts
    cache = tmp_path / "cache"

    def block(params):
        log = {}
        arr = feature_blocks(ctx, ["composite"], params, perts, {}, cache, log)["composite"]
        return arr, log

    original, cold = block({})
    repeated, warm = block({})
    np.testing.assert_array_equal(original, repeated)
    assert cold == {"misses": ["composite"]} and warm == {"hits": ["composite"]}
    changed_params, log = block({"leaf": {"scale": 3.}})
    assert log == {"misses": ["composite"]}
    np.testing.assert_array_equal(changed_params[0, :, 0], (ctx.control_mean * 3 + 1) * 2)

    # Only a grandchild source changes, at the same path and with the same byte count.
    leaf = plugins / "leaf.py"
    old_stat = leaf.stat()
    leaf.write_text(leaf.read_text().replace("params['scale']", "(2.00 * 1.0000)"))
    assert leaf.stat().st_size == old_stat.st_size
    os.utime(leaf, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
    registry.reload_plugins()
    changed_source, log = block({})
    assert log == {"misses": ["composite"]}
    np.testing.assert_array_equal(changed_source[0, :, 0], (ctx.control_mean * 2 + 1) * 2)
    clean = feature_blocks(FeatureContext(public_data), ["composite"], {}, perts, {})["composite"]
    np.testing.assert_array_equal(changed_source, clean)


def test_transitive_default_parameter_change_invalidates_cache(public_data, tmp_path):
    chain(tmp_path)
    ctx = FeatureContext(public_data)
    cache = tmp_path / "cache"
    feature_blocks(ctx, ["composite"], {}, ctx.train_perts, {}, cache)
    registry.get("leaf").params = {"scale": 5.}
    log = {}
    arr = feature_blocks(ctx, ["composite"], {}, ctx.train_perts, {}, cache, log)["composite"]
    assert log == {"misses": ["composite"]}
    np.testing.assert_array_equal(arr[0, :, 0], (ctx.control_mean * 5 + 1) * 2)


@pytest.mark.parametrize("cached", [False, True])
def test_missing_transitive_source_fails_even_with_cached_composite(public_data, tmp_path, cached):
    plugins = chain(tmp_path)
    ctx = FeatureContext(public_data)
    cache = tmp_path / "cache" if cached else None
    feature_blocks(ctx, ["composite"], {}, ctx.train_perts, {}, cache)
    (plugins / "leaf.py").unlink()
    registry.load_plugins(plugins)
    with pytest.raises(registry.FeatureDependencyError, match="composite -> middle -> leaf"):
        feature_blocks(ctx, ["composite"], {}, ctx.train_perts, {}, cache)


def test_dependency_cycle_is_reported_before_computation(public_data, tmp_path):
    plugins = chain(tmp_path)
    write_feature(plugins, "leaf", "return ctx.feature('composite', perts)", ["composite"])
    registry.reload_plugins()
    with pytest.raises(registry.FeatureDependencyError, match="cycle: composite -> middle -> leaf -> composite"):
        feature_blocks(FeatureContext(public_data), ["composite"], {}, ["a"], {})


def test_memoized_label_dependency_remains_label_dependent(public_data, tmp_path):
    plugins = tmp_path / "plugins"
    write_feature(plugins, "first", "return ctx.feature('mean_response', perts)", ["mean_response"])
    write_feature(plugins, "second", "return ctx.feature('mean_response', perts) * 2", ["mean_response"])
    registry.load_plugins(plugins)
    ctx = FeatureContext(public_data)
    labels = {}
    blocks = feature_blocks(ctx, ["first", "second"], {}, ctx.train_perts, {}, label_dep=labels)
    assert labels == {"first": True, "second": True}
    np.testing.assert_array_equal(blocks["second"], 2 * blocks["first"])
    fold = ctx.without_train(["a"])
    fold_block = feature_blocks(fold, ["second"], {}, ["b"], {})["second"]
    assert not np.array_equal(fold_block, blocks["second"][1:2])


def test_predictions_and_cv_match_cold_and_warm_cache(public_data, tmp_path):
    plugins = chain(tmp_path)
    write_feature(plugins, "response", "return ctx.feature('mean_response', perts) * params['scale']", ["mean_response"], {"scale": 1.})
    spec = {"feature_set": ["composite", "response"], "feature_params": {"leaf": {"scale": 3.}},
            "model_type": "ridge", "hyperparameters": {"alpha_grid": [0.1, 10.], "cv_folds": 3}}
    results = []
    for name, cache in (("cold", None), ("fill", tmp_path / "cache"), ("warm", tmp_path / "cache")):
        results.append(run(spec, public_data, plugins, tmp_path / name, cache))
    for artifact in ("predictions.npz", "cv.npz"):
        arrays = [np.load(tmp_path / name / artifact)["delta"] for name in ("cold", "fill", "warm")]
        np.testing.assert_array_equal(arrays[0], arrays[1])
        np.testing.assert_array_equal(arrays[1], arrays[2])
    assert results[2]["feature_cache"]["hits"] == ["composite", "response"]
    assert results[2]["feature_cache"]["misses"] == []
    assert results[2]["columns"] == ["composite", "response"]
    assert set(results[2]["feature_sources"]) == {"composite", "middle", "leaf", "response", "mean_response"}
