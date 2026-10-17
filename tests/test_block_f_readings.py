"""tools/block_f_readings.py: the two-stage block F reading on hand-made feature_compare reports, under the corrected
test (docs/ROADMAP.md D2, D3): every row selected, 999 replicates, duplicates collapsed, the pooled max-gain
step-down over the union, both nulls for proportional rows, the minimum effect."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import block_f_readings as bfr  # noqa: E402

B = 999


def _null(observed, scale, seed, reps=B):
    g = np.random.default_rng(seed).normal(0, scale, reps)
    return {"reps": reps, "observed": observed, "gains": g.tolist(), "p": float((1 + np.sum(g >= observed)) / (reps + 1))}


def _row(source, feature, mean, se_adj, null=None, failed=(), kind="add_one", status="ok", pert=None, hash_=None,
         reason=""):
    oof = {"delta": {"pearson_delta": {"mean_diff": mean, "se_adj": se_adj}}}
    if null is not None:
        oof["null"] = null
        oof["null_pert"] = pert
    row = {"source": source, "feature": feature, "kind": kind, "status": status, "tiers": {"oof": oof},
           "failed_criteria": list(failed), "reason": reason, "proportional": pert is not None,
           "parent_column": "additive_response" if pert is not None else None, "coef_candidate_sign": "+",
           "coef_candidate_std": [0.1, 0.2]}
    if hash_:
        row["prediction_hash"] = hash_
    return row


def _setup(tmp: Path):
    plugins = tmp / "plugins"
    for run, feats in {"r0": ["ga_a", "ga_b"], "r2": ["ga_a", "ga_c", "ga_p"], "r3": ["ga_d", "ga_a2"]}.items():
        (plugins / run).mkdir(parents=True)
        for f in feats:
            body = "import numpy as np\n" + ("x = 'replogle2022_k562'\n" if f == "ga_c" else "")
            (plugins / run / f"{f}.py").write_text(body)
    stage1 = {"rows": [
        _row("f_r0", "ga_a", 0.03, 0.01, failed=["null p (FWER) > 0.05"]),                 # z 3
        _row("f_r0", "ga_b", 0.001, 0.01, failed=["M1 gain not above 2 SE_adj with wins > n/2", "no null"]),
        _row("f_r2", "ga_a", 0.05, 0.01),                                                   # z 5, best
        _row("f_r2", "ga_c", 0.04, 0.01),                                                   # z 4, reads Replogle
        _row("f_r2", "ga_p", 0.03, 0.002),                                                  # z 15, proportional
        _row("f_r3", "ga_d", 0.02, 0.0),                                                    # se 0: ranked last
        _row("f_r3", "ga_a2", 0.05, 0.01),                                                  # same column as f_r2 ga_a
        _row("f_r0", "ga_x", 0.9, 0.001, status="guard"),                                   # not scored
        _row("f_r0", "(set)", 0.9, 0.001, kind="set"),                                      # not an add-one row
        _row("other", "ga_z", 0.9, 0.001),                                                  # not a block F source
    ]}
    (tmp / "stage1.json").write_text(json.dumps(stage1))
    return plugins


def test_select_copies_every_row_by_default_and_refuses_k_without_partial(tmp_path, capsys):
    plugins = _setup(tmp_path)
    rec = bfr.select(tmp_path / "stage1.json", plugins, tmp_path / "top")
    assert rec["m_total"] == 7 and rec["null_reps"] == 999 and rec["k"] is None
    assert [(s["source"], s["feature"]) for s in rec["selected"]][:3] == [("f_r2", "ga_p"), ("f_r2", "ga_a"),
                                                                        ("f_r3", "ga_a2")]
    assert len(list((tmp_path / "top").rglob("*.py"))) == 7
    assert "warning" not in capsys.readouterr().err
    with pytest.raises(SystemExit, match="partial"):
        bfr.select(tmp_path / "stage1.json", plugins, tmp_path / "top3", k=3)
    assert not (tmp_path / "top3").exists()
    rec = bfr.select(tmp_path / "stage1.json", plugins, tmp_path / "top3", k=3, null_reps=1999, partial=True)
    assert rec["null_reps"] == 1999 and len(rec["selected"]) == 3
    assert sorted(p.relative_to(tmp_path / "top3").as_posix() for p in (tmp_path / "top3").rglob("*.py")) == [
        "r2/ga_a.py", "r2/ga_p.py", "r3/ga_a2.py"]
    assert "family-wise correction needs every member" in capsys.readouterr().err


def test_pool_runs_the_step_down_over_the_unique_union_with_both_nulls_and_the_minimum_effect(tmp_path):
    plugins = _setup(tmp_path)
    stage2 = {"rows": [
        _row("f_r2", "ga_a", 0.05, 0.01, null=_null(0.05, 0.005, 1), hash_="h1"),           # clear pass
        _row("f_r3", "ga_a2", 0.05, 0.01, null=_null(0.05, 0.005, 1), hash_="h1"),          # same hash: duplicate
        _row("f_r2", "ga_c", 0.04, 0.01, null=_null(0.04, 0.005, 2), hash_="h2"),           # pass, reads Replogle
        _row("f_r2", "ga_p", 0.03, 0.002, null=_null(0.03, 0.00001, 3), hash_="h3",         # gene null a spike
             pert=_null(0.03, 0.03, 4)),                                                    # the pert null is not small
        _row("f_r0", "ga_a", 0.03, 0.01, null=_null(0.03, 0.005, 5), hash_="h4", failed=["no M2 gain"]),
        _row("f_r3", "ga_d", 0.0015, 0.0005, null=_null(0.0015, 0.0001, 6), hash_="h5"),    # under the minimum effect
        _row("f_r0", "ga_b", 0.001, 0.01, status="duplicate", reason="duplicate of ga_a: identical OOF predictions",
             hash_="h4"),
    ]}
    (tmp_path / "stage2.json").write_text(json.dumps(stage2))
    rec = bfr.pool(tmp_path / "stage1.json", tmp_path / "stage2.json", plugins, tmp_path / "pooled")
    assert rec["stage1_rows"] == 7 and rec["tested"] == 6 and rec["duplicates"] == 2 and rec["family"] == 5
    assert rec["null_reps"] == 999 and rec["null_too_coarse_need"] is None
    assert rec["partial"] is False and rec["untested"] == []
    by = {(r["source"], r["feature"]): r for r in rec["rows"]}
    a = by[("f_r2", "ga_a")]
    assert a["found"] and a["found_tier1"] and a["p_fwer_pooled"] <= 0.05 and a["duplicate_of"] is None
    assert a["coef_sign"] == "+" and a["min_effect"] == 0.02
    a2 = by[("f_r3", "ga_a2")]
    assert not a2["found"] and a2["duplicate_of"] == "ga_a (f_r2)" and a2["p_fwer_pooled"] is None
    c = by[("f_r2", "ga_c")]
    assert c["found"] and not c["found_tier1"]  # reads the Replogle file
    p = by[("f_r2", "ga_p")]
    assert p["proportional"] and p["parent_column"] == "additive_response"
    assert p["p_fwer_pooled"] <= 0.05 and p["p_fwer_pert_pooled"] > 0.05 and not p["found"]
    assert not by[("f_r0", "ga_a")]["found"] and by[("f_r0", "ga_a")]["other_failed"] == ["no M2 gain"]
    d = by[("f_r3", "ga_d")]
    assert d["p_fwer_pooled"] <= 0.05 and d["gain"] > 2 * d["se_adj"] and not d["found"]  # 0.0015 < 0.002
    b = by[("f_r0", "ga_b")]
    assert not b["tested"] and b["duplicate_of"] == "ga_a" and not b["found"]
    # the pooled p is monotone down the observed order and at or above every row's raw p
    fw = [r["p_fwer_pooled"] for r in rec["rows"] if r["p_fwer_pooled"] is not None]
    assert all(r["p_fwer_pooled"] >= r["p"] - 1e-12 for r in rec["rows"] if r["p_fwer_pooled"] is not None) and fw
    md = (tmp_path / "pooled" / "pooled_holm.md").read_text()
    assert md.count("**yes**") == 3 and "max(2 SE_adj, 0.002)" in md and "additive_response" in md
    # a stage 2 that omits one stage-1 row (--k, or a failed file) is partial: the subset step-down finds nothing
    stage2["rows"] = [x for x in stage2["rows"] if x["feature"] != "ga_d"]
    (tmp_path / "stage2b.json").write_text(json.dumps(stage2))
    rec = bfr.pool(tmp_path / "stage1.json", tmp_path / "stage2b.json", plugins, tmp_path / "pooled_b")
    assert rec["partial"] is True and rec["untested"] == ["ga_d (f_r3)"] and rec["family"] == 4
    assert not any(r["found"] for r in rec["rows"])
    assert rec["rows"][0]["p_fwer_pooled"] is not None  # the p values are still written, flagged as partial
    assert "not a family-wise reading" in (tmp_path / "pooled_b" / "pooled_holm.md").read_text()


def test_pool_refuses_a_report_without_gains_and_says_when_the_null_is_too_coarse(tmp_path):
    plugins = _setup(tmp_path)
    old = {"rows": [_row("f_r2", "ga_a", 0.05, 0.01, null={"p": 0.001, "reps": 199, "observed": 0.05}),
                    _row("f_r2", "ga_c", 0.04, 0.01, null={"p": 0.004, "reps": 199, "observed": 0.04})]}
    (tmp_path / "old.json").write_text(json.dumps(old))
    try:
        bfr.pool(tmp_path / "stage1.json", tmp_path / "old.json", plugins, tmp_path / "pooled")
    except SystemExit as exc:
        assert "no null gains" in str(exc)
    else:
        raise AssertionError("a report without gains must be refused")
    coarse = {"rows": [_row("f_r2", "ga_a", 0.05, 0.01, null=_null(0.05, 0.005, 1, reps=199), hash_="h1"),
                       _row("f_r2", "ga_c", 0.04, 0.01, null=_null(0.04, 0.005, 2, reps=199), hash_="h2")]}
    (tmp_path / "coarse.json").write_text(json.dumps(coarse))
    rec = bfr.pool(tmp_path / "stage1.json", tmp_path / "coarse.json", plugins, tmp_path / "pooled2")
    assert rec["null_too_coarse_need"] == 999 and not any(r["found"] for r in rec["rows"])
    assert "too coarse" in (tmp_path / "pooled2" / "pooled_holm.md").read_text()
