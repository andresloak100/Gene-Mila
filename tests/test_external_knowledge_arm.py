"""Knowledge files added to a bundle after it was built make a run its own arm."""

import json
import shutil

import pytest

from genemila.benchmark.table import run_arm
from genemila.data.bundle import added_knowledge, verify_bundle


def _copy(dataset, tmp_path):
    dst = tmp_path / "bundle"
    shutil.copytree(dataset, dst)
    return dst


def test_added_knowledge_lists_only_files_added_after_the_build(dataset, tmp_path):
    bundle = _copy(dataset, tmp_path)
    assert added_knowledge(bundle) == []
    (bundle / "knowledge" / "replogle_test.json").write_text(json.dumps({"perts": {}}))
    (bundle / "knowledge" / "notes.md").write_text("x")
    (bundle / "knowledge" / "partial.json.tmp").write_text("x")  # an unfinished atomic write is not a file yet
    assert added_knowledge(bundle) == ["notes.md", "replogle_test"]
    assert verify_bundle(bundle) == []  # adding a file is not tampering; the arm label is what separates the runs


def test_run_arm_names_the_external_knowledge():
    cfg = {"planner": {"provider": "deepseek", "model": "deepseek-v4-pro"},
           "worker": {"provider": "deepseek", "model": "deepseek-v4-flash"}, "run": {}}
    plain = "deepseek:deepseek-v4-pro planner, deepseek:deepseek-v4-flash workers"
    assert run_arm(cfg) == plain
    cfg["run"]["external_knowledge"] = []
    assert run_arm(cfg) == plain
    cfg["run"]["external_knowledge"] = ["replogle2022_k562"]
    assert run_arm(cfg) == plain + " (external knowledge: replogle2022_k562)"
    ctl = {"planner": {"provider": "scripted"}, "worker": {"provider": "mock"},
           "run": {"external_knowledge": ["b", "a"]}}
    assert run_arm(ctl) == "scripted control (no LLM) (external knowledge: a, b)"


def test_lab_records_the_added_files_and_refuses_a_config_that_disagrees(dataset, code_repo, tmp_path):
    from conftest import make_cfg
    from genemila.lab import Lab

    bundle = _copy(dataset, tmp_path)
    cfg = make_cfg(tmp_path)
    lab = Lab(cfg, tmp_path / "run_plain", bundle, repo=code_repo)
    try:
        assert "external_knowledge" not in lab.cfg["run"]
    finally:
        lab.close()

    (bundle / "knowledge" / "replogle_test.json").write_text(json.dumps({"perts": {}}))
    cfg = make_cfg(tmp_path)
    lab = Lab(cfg, tmp_path / "run_ext", bundle, repo=code_repo)
    try:
        assert (lab.public_dir / "knowledge" / "replogle_test.json").exists()  # the agents can read it
        assert lab.cfg["run"]["external_knowledge"] == ["replogle_test"]
        row = lab.db.query("SELECT config_json FROM runs WHERE run_id=?", (lab.run_id,))[0]
        assert json.loads(row["config_json"])["run"]["external_knowledge"] == ["replogle_test"]
        assert run_arm(lab.cfg).endswith("(external knowledge: replogle_test)")
    finally:
        lab.close()

    cfg = make_cfg(tmp_path)
    cfg["run"]["external_knowledge"] = []  # configured before the file was added
    with pytest.raises(RuntimeError, match="external_knowledge"):
        Lab(cfg, tmp_path / "run_stale", bundle, repo=code_repo)
