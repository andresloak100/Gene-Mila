"""tools/block_f_readings.py: the two-stage block F reading on hand-made feature_compare reports."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import block_f_readings as bfr  # noqa: E402


def _row(source, feature, mean, se_adj, p=None, failed=(), kind="add_one", status="ok"):
    oof = {"delta": {"pearson_delta": {"mean_diff": mean, "se_adj": se_adj}}}
    if p is not None:
        oof["null"] = {"p": p}
    return {"source": source, "feature": feature, "kind": kind, "status": status, "tiers": {"oof": oof},
            "failed_criteria": list(failed)}


def _setup(tmp: Path):
    plugins = tmp / "plugins"
    for run, feats in {"r0": ["ga_a", "ga_b"], "r2": ["ga_a", "ga_c"], "r3": ["ga_d"]}.items():
        (plugins / run).mkdir(parents=True)
        for f in feats:
            body = "import numpy as np\n" + ("x = 'replogle2022_k562'\n" if f == "ga_c" else "")
            (plugins / run / f"{f}.py").write_text(body)
    stage1 = {"rows": [
        _row("f_r0", "ga_a", 0.03, 0.01, failed=["null p (Holm) > 0.05"]),               # z 3
        _row("f_r0", "ga_b", 0.001, 0.01, failed=["M1 gain not above 2 SE_adj with wins > n/2", "no null"]),
        _row("f_r2", "ga_a", 0.05, 0.01),                                                  # z 5, best
        _row("f_r2", "ga_c", 0.04, 0.01),                                                  # z 4, reads Replogle
        _row("f_r3", "ga_d", 0.02, 0.0),                                                   # se 0: ranked last
        _row("f_r0", "ga_x", 0.9, 0.001, status="guard"),                                  # not scored
        _row("f_r0", "(set)", 0.9, 0.001, kind="set"),                                     # not an add-one row
        _row("other", "ga_z", 0.9, 0.001),                                                 # not a block F source
    ]}
    (tmp / "stage1.json").write_text(json.dumps(stage1))
    return plugins


def test_select_ranks_by_z_copies_per_run_and_sets_the_replicates(tmp_path):
    plugins = _setup(tmp_path)
    rec = bfr.select(tmp_path / "stage1.json", plugins, tmp_path / "top", k=3)
    assert rec["m_total"] == 5 and rec["null_reps"] == 199  # 20 * 5 - 1 < 199
    assert [(s["source"], s["feature"]) for s in rec["selected"]] == [("f_r2", "ga_a"), ("f_r2", "ga_c"), ("f_r0", "ga_a")]
    assert sorted(p.relative_to(tmp_path / "top").as_posix() for p in (tmp_path / "top").rglob("*.py")) == [
        "r0/ga_a.py", "r2/ga_a.py", "r2/ga_c.py"]


def test_pool_applies_holm_over_the_whole_family_with_untested_at_one(tmp_path):
    plugins = _setup(tmp_path)
    stage2 = {"rows": [
        _row("f_r2", "ga_a", 0.05, 0.01, p=0.001),                                        # passes: 0.001 * 5 = 0.005
        _row("f_r2", "ga_c", 0.04, 0.01, p=0.004),                                        # 0.004 * 4 = 0.016, Replogle
        _row("f_r0", "ga_a", 0.03, 0.01, p=0.02, failed=["no M2 gain"]),                 # Holm ok but another criterion fails
    ]}
    (tmp_path / "stage2.json").write_text(json.dumps(stage2))
    rec = bfr.pool(tmp_path / "stage1.json", tmp_path / "stage2.json", plugins, tmp_path / "pooled")
    assert rec["family"] == 5 and rec["tested"] == 3
    by = {(r["source"], r["feature"]): r for r in rec["rows"]}
    assert by[("f_r2", "ga_a")]["found"] and by[("f_r2", "ga_a")]["found_tier1"]
    assert abs(by[("f_r2", "ga_a")]["p_holm_pooled"] - 0.005) < 1e-12
    assert by[("f_r2", "ga_c")]["found"] and not by[("f_r2", "ga_c")]["found_tier1"]  # reads the Replogle file
    assert not by[("f_r0", "ga_a")]["found"] and by[("f_r0", "ga_a")]["other_failed"] == ["no M2 gain"]
    assert not by[("f_r0", "ga_b")]["tested"] and by[("f_r0", "ga_b")]["p_holm_pooled"] == 1.0
    assert (tmp_path / "pooled" / "pooled_holm.md").read_text().count("**yes**") == 3
