import json
import re
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


def run_smoke(dataset, tmp_path, code, name="feat", pub=None):
    pub = pub or public(dataset, tmp_path)
    plugins = _write_plugin(tmp_path, code, name)
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, "-m", "genemila.pipeline", "smoke", "--feature", name, "--public", str(pub),
                        "--plugins", str(plugins), "--out", str(tmp_path / "out")], cwd=root, capture_output=True)
    return json.loads((tmp_path / "out" / "smoke.json").read_text()) if (tmp_path / "out" / "smoke.json").exists() else None


def test_smoke_accepts_good_feature(dataset, tmp_path):
    r = run_smoke(dataset, tmp_path, TEMPLATES["coexpr"])
    assert r["status"] == "ok", r


def test_smoke_accepts_components_template(dataset, tmp_path):
    from genemila.providers.mock import _pick_template
    assert _pick_template("response_components low-rank response components") == "components"
    assert _pick_template("pca_alignment PCA loadings product of target and gene g on top PCs") == "pca"
    r = run_smoke(dataset, tmp_path, TEMPLATES["components"], name="comp")
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


def test_smoke_samples_pairs_only_on_a_bundle_with_pairs(dataset, tmp_path):
    """The smoke test as the worker runs it (a subprocess), docs/NORMAN_PLAN.md section 4, item 10: a feature zero on
    every single passes on a bundle with pairs, whose sample adds a training and a held-out pair, and is refused as
    constant on a single-target bundle, whose sample is the first two training and held-out perturbations as before;
    a feature reading only a pair's first target is refused on the bundle with pairs alone."""
    from test_norman_templates import FIRST_TARGET, PAIR_ONLY, make_pairs_bundle
    from genemila.data.bundle import export_public

    pairs = export_public(make_pairs_bundle(tmp_path / "pairs_bundle"), tmp_path / "pairs" / "pub")
    assert run_smoke(dataset, tmp_path / "pairs", PAIR_ONLY, pub=pairs)["status"] == "ok"
    (tmp_path / "single").mkdir()
    r = run_smoke(dataset, tmp_path / "single", PAIR_ONLY)
    assert r["status"] == "failed" and r["problems"] == ["feature is constant across all rows (no information)"]
    (tmp_path / "first").mkdir()
    r = run_smoke(dataset, tmp_path / "first", FIRST_TARGET, pub=pairs)
    assert r["status"] == "failed" and "order of a pair's target genes" in r["problems"][0]


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
        check_plugin_source(tpl.format(name="abc", knowledge="ext_screen"), "abc")  # external templates name a file
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


# hash() and id() differ between processes (str hashes are salted per process, id() is a memory address): a feature
# built on them is noise no other process reproduces, which the smoke test's in-process determinism check never sees
@pytest.mark.parametrize("snippet, what", [
    ("h = abs(hash(perts[0])) % ctx.n_genes", "use of 'hash'"),            # as found in a past run's plugin
    ("s = 1.0 / (1.0 + abs(hash(perts[0]) % 1000) / 1000.0)", "use of 'hash'"),
    ("h = hash", "use of 'hash'"),                                          # an alias, called later
    ("h = sorted(perts, key=hash)", "use of 'hash'"),
    ("h = perts[0].__hash__()", "access to .__hash__"),
    ("h = str.__hash__", "access to .__hash__"),
    ("h = id(ctx) % 7", "call of id()"),
    ("h = sorted(perts, key=id)", "use of 'id'"),                           # the builtin, not a variable
    ("h = __builtins__['hash']", "use of '__builtins__'"),                  # reaching any builtin by name
    # the builtins module through an allowed module's attributes, or an attribute looked up by string
    ("import dataclasses\n        h = dataclasses.builtins.id(ctx)", "access to .builtins"),
    ("import dataclasses\n        h = dataclasses.sys.modules['builtins'].hash(perts[0])", "access to .sys"),
    ("from dataclasses import builtins\n        h = builtins.id(ctx)", "import of ['builtins'] from 'dataclasses'"),
    ("h = len.__self__.hash(perts[0])", "access to .__self__"),                 # a builtin function's module
    ("import genemila.features.api as api\n        h = api.os.getpid()", "access to .os"),
    ("h = str.__getattribute__(perts[0], '__ha' + 'sh__')()", "access to .__getattribute__"),
    ("h = object.__getattribute__(ctx, '_train' + '_delta')", "access to .__getattribute__"),
    # a set of functions is ordered by their addresses, which PYTHONHASHSEED does not fix
    ("x = np.arange(4.0) ** 2\n        a, b = [f(x) for f in {np.mean, np.median}]", "iteration over a set of objects"),
    ("for f in frozenset([np.mean, np.max]):\n            pass", "iteration over a set of objects"),
])
def test_guard_refuses_hash_and_id_and_says_why(snippet, what):
    code = TEMPLATES["variance"].format(name="f").replace("return np.broadcast_to",
                                                          f"{snippet}\n        return np.broadcast_to")
    with pytest.raises(CodeViolation, match=re.escape(what)) as exc:
        check_plugin_source(code, "f")
    if what.startswith(("use of 'hash'", "use of 'id'", "call of id()", "access to .__hash__", "iteration")):
        msg = str(exc.value)
        assert "differ between processes" in msg and "sorted order" in msg and "ctx.perts or ctx.genes" in msg
        assert "zlib.crc32" in msg and "hashlib" in msg and "allowed imports" in msg
        assert "set of objects other than strings and numbers" in msg and "tuple or list" in msg


@pytest.mark.parametrize("module, body, what", [
    # a binding of id elsewhere (another function's argument) does not hide the builtin here
    ("def _helper(id=0):\n    return id\n\n\nADDR = id", "h = ADDR(perts[0])", "use of 'id'"),
    ("def _helper(id=0):\n    return id", "h = sorted(perts, key=id)", "use of 'id'"),
    ("def _loop():\n    for id in range(3):\n        pass", "h = list(map(id, perts))", "use of 'id'"),
    # a module-level binding counts from the next statement on: until then the name is still the builtin
    ("hash = hash", "h = hash(perts[0])", "use of 'hash'"),
    ("def hash(s, h=hash):\n    return zlib.crc32(s.encode())", "h = hash(perts[0])", "use of 'hash'"),
    ("H = id\n\n\ndef id(x):\n    return 0", "h = H(perts[0])", "use of 'id'"),
    # a name the plugin binds where the use sees it is not the builtin
    ("def hash(s):\n    return zlib.crc32(s.encode())", "h = hash(perts[0])", None),  # the replacement suggested
    ("", "hash = zlib.crc32(perts[0].encode())\n        h = hash % 7", None),
    ("", "for id in range(2):\n            h = id", None),
    ("", "h = [id for id in range(3)]", None),
    ("", "h = (lambda id: id + 1)(2)", None),
    ("ID = 3\n\n\ndef id(x):\n    return ID", "h = id(perts[0])", None),
    # sets used without their order, or of literals whose hash the fixed seed fixes
    ("", "h = [p in {perts[0], perts[-1]} for p in perts]", None),
    ("", "h = sorted({perts[0], perts[-1]}) + [len({np.mean, np.max})]", None),
    ("", "for g in {'ATF4', 'XBP1', 3, (1, 'a')}:\n            pass", None),
])
def test_guard_resolves_hash_and_id_by_scope(module, body, what):
    """hash and id are refused where they reach the builtins, by Python's scoping: a binding in another function, or
    one at module level after (or in) the statement that uses the name, leaves the use on the builtin; a binding the
    use sees (a local, a loop variable, a helper def hash built on zlib.crc32) does not."""
    code = TEMPLATES["variance"].format(name="f").replace("import numpy as np", f"import zlib\n\nimport numpy as np\n\n{module}\n")
    code = code.replace("return np.broadcast_to", f"{body}\n        return np.broadcast_to")
    if what is None:
        check_plugin_source(code, "f")
    else:
        with pytest.raises(CodeViolation, match=re.escape(f"{what} not allowed: hash() and id() differ")):
            check_plugin_source(code, "f")


def test_guard_allows_the_stable_replacements_it_recommends(dataset, tmp_path):
    """zlib.crc32 and hashlib on encoded bytes pass the guard, as its message says, and run in the smoke test (a
    subprocess, as the worker runs it); a variable named id is not the builtin."""
    code = TEMPLATES["variance"].replace("import numpy as np", "import hashlib\nimport zlib\n\nimport numpy as np")
    code = code.replace("return np.broadcast_to", "w = np.array([zlib.crc32(p.encode()) % 7 + int(hashlib.sha256("
                        "p.encode()).hexdigest()[:2], 16) for p in perts], dtype=float)\n"
                        "        for id in range(2):\n            w = w + id\n"
                        "        return w[:, None, None] + np.broadcast_to")
    check_plugin_source(code.format(name="stable"), "stable")
    r = run_smoke(dataset, tmp_path, code, name="stable")
    assert r["status"] == "ok", r


def _plugin_sources() -> dict[str, str]:
    """Every feature plugin source the lab ships or the tests use: the built-in features, the plugin directory, every
    string constant in genemila/providers (the scripted templates among them) and in the tests that registers a
    feature (formatted when it is a template)."""
    import ast
    root = Path(__file__).resolve().parent.parent
    out = {"genemila/features/builtin.py": (root / "genemila" / "features" / "builtin.py").read_text()}
    for p in sorted((root / "genemila" / "features" / "plugins").glob("*.py")):
        out[str(p.relative_to(root))] = p.read_text()
    for f in sorted((root / "genemila" / "providers").glob("*.py")) + sorted((root / "tests").glob("*.py")):
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and "@register" in node.value:
                # a template ({name} in it) is formatted first: its escaped braces {{}} parse as a set of a dict
                fmt = node.value.replace("{{", "{").replace("}}", "}")
                for src in ((fmt, node.value) if "{name}" in node.value else (node.value, fmt)):
                    try:
                        ast.parse(src)
                    except SyntaxError:
                        continue
                    out[f"{f.relative_to(root)}:{node.lineno}"] = src
                    break
    return out


def test_no_shipped_template_or_fixture_plugin_uses_hash_or_id():
    import ast
    from genemila.guard import process_dependent_uses
    sources = _plugin_sources()
    assert any(k.startswith("genemila/providers/mock.py") for k in sources)
    assert any(k.startswith("tests/test_determinism.py") for k in sources)  # the set-order plugin there is allowed
    assert {k: process_dependent_uses(ast.parse(s)) for k, s in sources.items()} == {k: [] for k in sources}
    for key, tpl in TEMPLATES.items():  # and the guard as a whole still takes every scripted template
        check_plugin_source(tpl.format(name="abc", knowledge="ext_screen"), "abc")
