import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from genemila.features.api import FeatureContext
from genemila.features import registry
from genemila.guard import CodeViolation, check_plugin_source
from genemila.pipeline import smoke
from genemila.providers.mock import CHEAT, LEAKY, TEMPLATES


def public(dataset, tmp_path):
    from genemila.data.bundle import export_public
    return export_public(dataset, tmp_path / "pub")


def test_builtin_registry_metadata():
    for name in registry.BUILTIN_FEATURES:
        meta = registry.get(name).metadata()
        for key in ("name", "version", "description", "rationale", "inputs", "params", "dim", "dependencies"):
            assert key in meta
        assert meta["description"] and meta["rationale"]


def test_builtin_features_shapes_and_loo(dataset, tmp_path):
    ctx = FeatureContext(public(dataset, tmp_path))
    perts = ctx.train_perts[:3]
    for name in registry.BUILTIN_FEATURES:
        arr = registry.get(name)().compute(ctx, perts, {})
        assert arr.shape == (3, ctx.n_genes, 1)
        assert np.isfinite(arr).all()
    # mean_response must be leave-one-out for training perturbations
    mr = registry.get("mean_response")().compute(ctx, perts[:1], {})[0, :, 0]
    _, d = ctx.train_delta(exclude=perts[0])
    assert np.allclose(mr, d.mean(axis=0))


def test_public_bundle_has_no_validation_labels(dataset, tmp_path):
    pub = public(dataset, tmp_path)
    assert not (pub / "private").exists()
    z = np.load(pub / "public.npz")
    assert set(z.files) == {"genes", "control_cells", "perts", "train_perts", "train_means", "train_ncells"}
    splits = json.loads((dataset / "splits.json").read_text())
    assert set(z["train_perts"]) == set(splits["train"])


def _write_plugin(tmp_path, code, name="feat"):
    d = tmp_path / "plugins"
    d.mkdir(exist_ok=True)
    (d / f"{name}.py").write_text(code.format(name=name))
    return d


def run_smoke(dataset, tmp_path, code, name="feat"):
    pub = public(dataset, tmp_path)
    plugins = _write_plugin(tmp_path, code, name)
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, "-m", "genemila.pipeline", "smoke", "--feature", name, "--public", str(pub),
                        "--plugins", str(plugins), "--out", str(tmp_path / "out")], cwd=root, capture_output=True)
    return json.loads((tmp_path / "out" / "smoke.json").read_text()) if (tmp_path / "out" / "smoke.json").exists() else None


def test_smoke_accepts_good_feature(dataset, tmp_path):
    r = run_smoke(dataset, tmp_path, TEMPLATES["coexpr"])
    assert r["status"] == "ok", r


def test_smoke_detects_label_leakage(dataset, tmp_path):
    r = run_smoke(dataset, tmp_path, LEAKY)
    assert r["status"] == "failed"
    assert any("leakage" in p for p in r["problems"])


def test_smoke_detects_bad_shape_and_constant(dataset, tmp_path):
    bad = TEMPLATES["variance"].replace("(len(perts), ctx.n_genes, 1)).copy()", "(len(perts), ctx.n_genes, 1)).copy()[:, :5]")
    r = run_smoke(dataset, tmp_path, bad)
    assert r["status"] == "failed" and "shape" in r["problems"][0]
    const = TEMPLATES["variance"].replace("ctx.control_std[None, :, None]", "np.ones((1, ctx.n_genes, 1))")
    r = run_smoke(dataset, tmp_path, const, name="const")
    assert r["status"] == "failed" and "constant" in r["problems"][0]


@pytest.mark.parametrize("snippet", [
    "open('x')", "np.load('data/private/val2.npz')", "ctx._train_delta", "getattr(ctx, 'x')",
    "__import__('os')", "eval('1')", "ctx.public_dir",
])
def test_guard_blocks_forbidden_code(snippet):
    code = TEMPLATES["variance"].format(name="f").replace("return np.broadcast_to", f"_ = {snippet}\n        return np.broadcast_to")
    with pytest.raises(CodeViolation):
        check_plugin_source(code, "f")


@pytest.mark.parametrize("imp", ["import os", "import subprocess", "from pathlib import Path", "import socket",
                                 "import pickle", "from genemila.benchmark import evaluator"])
def test_guard_blocks_imports(imp):
    code = imp + "\n" + TEMPLATES["variance"].format(name="f")
    with pytest.raises(CodeViolation):
        check_plugin_source(code, "f")


def test_guard_accepts_templates_and_checks_name():
    for key, tpl in TEMPLATES.items():
        check_plugin_source(tpl.format(name="abc"), "abc")
    with pytest.raises(CodeViolation):
        check_plugin_source(TEMPLATES["variance"].format(name="abc"), "other")
    with pytest.raises(CodeViolation):
        check_plugin_source(CHEAT.format(name="abc"), "abc")
    with pytest.raises(CodeViolation):
        check_plugin_source("def broken(:\n", "abc")


@pytest.mark.parametrize("snippet", [
    "full = type(ctx)._preloaded",                       # the process-wide context behind a fold view
    "full = FeatureContext.shared('public_data')",       # re-loading the full training set
    "view = ctx.without_train([])",                      # making one's own view
    "arr = ctx._disk_cached('x', lambda: ctx.control_mean)",
])
def test_guard_blocks_routes_around_fold_views(snippet):
    code = TEMPLATES["coexpr"].replace("def compute(self, ctx, perts, params):",
                                       f"def compute(self, ctx, perts, params):\n        {snippet}")
    assert "def compute" in code and snippet in code
    with pytest.raises(CodeViolation):
        check_plugin_source(code, "coexpr")
