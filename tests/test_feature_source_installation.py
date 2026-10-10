"""Metadata-only source installation tests; no Lab initialization or evaluations."""

from types import SimpleNamespace

import pytest

from genemila.db import Database
from genemila.features.registry import FeatureDependencyError
from genemila.guard import CodeViolation, check_plugin_source
from genemila.isolation import WorktreeManager
from genemila.lab import Lab
from genemila.spec import ExperimentSpec, PLUGIN_DIR
from genemila.worker import Worker


@pytest.fixture
def metadata_lab(tmp_path):
    lab = Lab.__new__(Lab)  # intentionally bypass data/oracle/evaluator setup
    lab.db = Database(tmp_path / "metadata.db")
    lab.store = tmp_path / "store"
    lab.store.mkdir()
    for name, dependencies in (("control_mean", []), ("leaf", []),
                               ("middle", ["leaf", "control_mean"]), ("composite", ["middle"])):
        lab.db.upsert_feature({"name": name, "dependencies": dependencies,
                               "builtin": name == "control_mean"})
        if name != "control_mean":
            # Any accidental import of a stored source would fail this test.
            (lab.store / f"{name}.py").write_text("raise AssertionError('controller executed a plugin')\n")
    lab.worktrees = SimpleNamespace(install_features=lambda wt, files: WorktreeManager.install_features(None, wt, files))
    yield lab
    lab.db.close_thread_conn()


def test_store_resolves_transitive_sources_without_adding_columns(metadata_lab):
    selected = ["composite"]
    files = metadata_lab.store_files(selected)
    assert list(files) == ["leaf", "middle", "composite"]
    assert selected == ["composite"]
    assert metadata_lab.store_files(["control_mean"]) == {}


def test_store_reports_missing_dependency_metadata(metadata_lab):
    metadata_lab.db.execute("DELETE FROM features WHERE name='leaf'")
    with pytest.raises(FeatureDependencyError, match="composite -> middle -> leaf"):
        metadata_lab.store_files(["composite"])


def test_store_reports_missing_source_file(metadata_lab):
    (metadata_lab.store / "leaf.py").unlink()
    with pytest.raises(FeatureDependencyError, match="missing feature source file for 'leaf'"):
        metadata_lab.store_files(["composite"])


def test_store_reports_dependency_cycle(metadata_lab):
    metadata_lab.db.upsert_feature({"name": "leaf", "dependencies": ["composite"]})
    with pytest.raises(FeatureDependencyError, match="cycle: composite -> middle -> leaf -> composite"):
        metadata_lab.store_files(["composite"])


def test_worker_preserves_installed_hashes_across_dependency_retries(metadata_lab, tmp_path):
    worker = Worker.__new__(Worker)
    worker.lab = metadata_lab
    wt = tmp_path / "worktree"
    installed = {}
    worker._install_dependency_sources(["middle"], wt, installed)
    assert set(installed) == {f"{PLUGIN_DIR}/leaf.py", f"{PLUGIN_DIR}/middle.py"}
    before = dict(installed)
    # A retry must not overwrite and hide an unauthorized edit to an installed source.
    leaf = wt / PLUGIN_DIR / "leaf.py"
    leaf.write_text("unauthorized edit")
    worker._install_dependency_sources(["middle"], wt, installed)
    assert installed == before and leaf.read_text() == "unauthorized edit"


NEW_COMPOSITE = '''import numpy as np
from genemila.features.api import Feature, register
@register
class F(Feature):
    name = "new_composite"
    dependencies = ["middle"]
    def compute(self, ctx, perts, params):
        return ctx.feature("middle", perts)
'''


def test_worker_installs_new_declared_inputs_before_smoke(metadata_lab, tmp_path):
    worker = Worker.__new__(Worker)
    worker.lab = metadata_lab
    worker.provider = SimpleNamespace(name="fixture", model="fixture")
    worker.escalation = None
    worker.wcfg = {"llm_retries": 0}
    worker._task = lambda spec: {}
    worker._set = lambda *args, **kwargs: None
    worker._llm = lambda *args, **kwargs: SimpleNamespace(text=NEW_COMPOSITE, truncated_empty=False)
    wt, art = tmp_path / "worktree", tmp_path / "artifact"
    (wt / PLUGIN_DIR).mkdir(parents=True)
    art.mkdir()
    installed = {}

    def fake_smoke(name, wt, art, attempt):
        assert name == "new_composite"
        assert (wt / PLUGIN_DIR / "leaf.py").is_file()
        assert (wt / PLUGIN_DIR / "middle.py").is_file()
        assert (wt / PLUGIN_DIR / "new_composite.py").read_text().strip() == NEW_COMPOSITE.strip()
        return None

    worker._smoke = fake_smoke
    spec = ExperimentSpec(hypothesis="fixture hypothesis", scientific_rationale="fixture rationale",
                          experiment_id="EXP_0001", kind="new_feature", feature_set=["new_composite"],
                          proposed_feature={"name": "new_composite"})
    worker._implement(spec, wt, art, installed)
    assert spec.feature_set == ["new_composite"]
    assert set(installed) == {f"{PLUGIN_DIR}/leaf.py", f"{PLUGIN_DIR}/middle.py"}


def test_guard_returns_literal_dependencies():
    assert check_plugin_source(NEW_COMPOSITE, "new_composite")["dependencies"] == ["middle"]
    for replacement in ("('middle',)", "list(['middle'])", "[42]"):
        with pytest.raises(CodeViolation, match="dependencies must be a literal list"):
            check_plugin_source(NEW_COMPOSITE.replace('["middle"]', replacement), "new_composite")


@pytest.mark.parametrize("declaration", ['    dependencies = []\n', '    dependencies = ["other"]\n', ""])
@pytest.mark.parametrize("call", ['ctx.feature("middle", perts)', 'ctx.feature(name="middle", perts=perts)'])
def test_guard_rejects_undeclared_literal_dependency(declaration, call):
    code = NEW_COMPOSITE.replace('    dependencies = ["middle"]\n', declaration)
    code = code.replace('ctx.feature("middle", perts)', call)
    with pytest.raises(CodeViolation, match="undeclared dependencies.*middle.*add these names"):
        check_plugin_source(code, "new_composite")
