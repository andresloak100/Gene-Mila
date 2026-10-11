"""tools/arm_reading.py: the arm reading and the combined model of docs/PLAN_AFTER_N4.md. The rule reads the runs'
own sealed readings only (G = mean difference, SE = sqrt(S² + sd_g²/R) with S the mean inflated paired SE, a gain
when G > k·SE, every run has G's sign and the favoured side wins most perturbation-run pairs);
the combined model is the plain average of the members' predictions, answered by one paired query of the tool's own
oracle, with the visible comparison beside it; nothing is written into a run."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from genemila.benchmark.evaluator import metric_values, paired_summary
from genemila.benchmark.oracle import QueryOracle

from test_norman_lab import make_pair_bundle
from test_sealed_reading import _additive_id, _sealed_events, bundles, make_lab  # noqa: F401  (fixtures)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import arm_reading  # noqa: E402


W = [(40, 16, 56)] * 3


def test_the_arm_rule_adds_run_to_run_spread_and_needs_one_sign_and_most_wins():
    from scipy import stats
    r = arm_reading.arm_rule([0.010, 0.012, 0.008], [0.002, 0.002, 0.002], W, 56)
    sd = np.std([0.010, 0.012, 0.008], ddof=1)
    se = np.sqrt(0.002 ** 2 + sd ** 2 / 3)
    nu = se ** 4 / (0.002 ** 4 / 55 + (sd ** 2 / 3) ** 2 / 2)
    assert r["SE"] == pytest.approx(se) and r["nu"] == pytest.approx(nu)
    assert r["k"] == pytest.approx(max(2, stats.t.ppf(0.975, nu))) and r["verdict"] == "a"
    # the reviewer's example: one run far above the others widens SE until the gain no longer counts
    wide = arm_reading.arm_rule([0.008, 0.001, 0.020], [0.004, 0.004, 0.005], W, 56)
    assert wide["verdict"] == "none" and wide["G"] < wide["k"] * wide["SE"]
    assert arm_reading.arm_rule([0.020, 0.020, -0.001], [0.002] * 3, W, 56)["verdict"] == "none"   # one sign
    assert arm_reading.arm_rule([-0.010, -0.012, -0.008], [0.002] * 3, [(16, 40, 56)] * 3, 56)["verdict"] == "b"
    assert arm_reading.arm_rule([0.010, 0.0], [0.001, 0.0], [(40, 16, 56), (0, 0, 56)], 56)["verdict"] == "none"
    assert arm_reading.arm_rule([0.010, 0.012, 0.008], [0.002] * 3, [(20, 36, 56)] * 3, 56)["verdict"] == "none"
    same = arm_reading.arm_rule([0.01, 0.01], [0.002, 0.002], W[:2], 56)   # no run-to-run spread: k is about 2
    assert same["sd_g"] == 0 and same["k"] == pytest.approx(max(2, stats.t.ppf(0.975, 55)))


def _paired(d, se, n=56, cats=None):
    out = {"n": n, "mean_diff": d, "se": se, "wins_a": n // 2 + 1, "wins_b": n // 2 - 1, "ties": 0,
           "verdict": "a" if d > 2 * se else "none"}
    if cats:
        out["by_category"] = cats
    return out


def _reading(tmp_path, run, d, se, split="split_x", start=True, is_additive=False, cats=None, pd=0.72,
             planner=None, kept=False, ratio=1.0):
    planner = planner or {"configured": "deepseek:deepseek-v4-pro", "mixed": False}
    metrics = {"pearson_delta": pd, "cellforge_mse_de": 0.1, "cellforge_pcc_de": 0.9, "cellforge_r2_de": 0.8}
    sealed = {"a": {"metrics": metrics}, "b": {"metrics": {}}, "paired": _paired(d, se, cats=cats)}
    add_sealed = {"a": {"metrics": metrics}, "b": {"metrics": {}}, "paired": _paired(d / 2, se, cats=cats)}
    r = {"run": run, "dataset": "norman", "split_id": split, "base_commit": "076282c", "planner": planner,
         "selected": {"experiment_id": "EXP_9"}, "additive": {"experiment_id": "EXP_2"}, "sealed": add_sealed,
         "visible": _paired(d * 3, se), "cluster_ratio": None, "note": None}
    if start:
        r["continuation"] = ({"kind": "fresh", "start": None, "sealed": None, "note": "same", "is_additive": True}
                             if is_additive else
                             {"start": {"experiment_id": "EXP_7"}, "sealed": None, "visible": None,
                              "cluster_ratio": None, "note": "the run selected its starting model: its search added "
                                                            "nothing it kept"}
                             if kept else
                             {"start": {"experiment_id": "EXP_7"}, "sealed": sealed, "visible": _paired(d * 2, se),
                              "cluster_ratio": {"ratio": ratio}, "note": None})
    path = tmp_path / f"{run}.json"
    path.write_text(json.dumps({"runs": [r], "pair": None}))
    return path


def test_the_arm_reading_reads_the_runs_own_readings(tmp_path):
    cats = {"single": _paired(0.01, 0.004, n=40), "combo_seen0": _paired(0.02, 0.01, n=8)}
    paths = [_reading(tmp_path, f"r{i}", d, 0.004, cats=cats, pd=pd)
             for i, (d, pd) in enumerate(((0.010, 0.726), (0.012, 0.730), (0.009, 0.722)))]
    rep = arm_reading.read_arm(paths, "start")
    p = rep["pooled"]
    assert p["G"] == pytest.approx(0.010333, abs=1e-6) and p["S"] == pytest.approx(0.004) and p["verdict"] == "a"
    assert p["SE"] > p["S"] and p["G"] > p["k"] * p["SE"]   # runs this close add little to S
    assert rep["protocol"]["sealed_scorings"] == 0 and rep["same_code"] is True
    assert rep["by_category"]["single"]["read"] is True and rep["by_category"]["combo_seen0"]["read"] is False
    assert rep["visible"]["G"] == pytest.approx(2 * p["G"]) and rep["visible"]["S"] == pytest.approx(0.004)
    s = rep["selected_spread"]["pearson_delta"]
    assert s["mean"] == pytest.approx(0.726) and s["sd"] == pytest.approx(np.std([0.726, 0.730, 0.722], ddof=1))
    add = arm_reading.read_arm(paths, "additive")
    assert add["pooled"]["G"] == pytest.approx(p["G"] / 2)
    assert [x["sha256"] for x in rep["readings"]] == [arm_reading._sha256(x) for x in paths]
    md = arm_reading.render_arm(rep)
    assert "| sealed, pooled | +0.0103 | 0.0040 |" in md and "| arm better |" in md
    assert "reported, not read" in md
    assert "scored nothing on the sealed set" in md and "## Reading" in md


def test_a_fresh_start_that_is_the_additive_baseline_reads_the_additive_comparison(tmp_path):
    paths = [_reading(tmp_path, "a", 0.01, 0.004, is_additive=True), _reading(tmp_path, "b", 0.01, 0.004)]
    rep = arm_reading.read_arm(paths, "start")
    assert rep["runs"][0]["mean_diff"] == pytest.approx(0.005) and rep["runs"][1]["mean_diff"] == pytest.approx(0.01)


def test_inflation_kept_references_and_changed_planners(tmp_path):
    """A run's SE is multiplied by its gene-clustering ratio when above 1; a run that kept its reference enters with
    g = 0, s = 0 (so the gain cannot count); a run whose planner changed is left out and named."""
    a = _reading(tmp_path, "a", 0.010, 0.002, ratio=1.5)
    b = _reading(tmp_path, "b", 0.010, 0.002, ratio=0.8)
    rep = arm_reading.read_arm([a, b], "start")
    assert [r["inflation"] for r in rep["runs"]] == [1.5, 1.0]
    assert rep["pooled"]["S"] == pytest.approx((0.003 + 0.002) / 2)
    kept = _reading(tmp_path, "kept", 0.0, 0.0, kept=True)
    rep = arm_reading.read_arm([a, b, kept], "start")
    assert rep["pooled"]["g"][2] == 0 and rep["pooled"]["verdict"] == "none" and rep["runs"][2]["selected_reference"]
    assert rep["pooled"]["pairs"] == 3 * 56 and "kept the reference" in rep["selected_spread_note"]
    assert "0 (kept its reference)" in arm_reading.render_arm(rep)
    lost = _reading(tmp_path, "lost", 0.05, 0.002, planner={"configured": "deepseek:deepseek-v4-pro", "mixed": True,
                                                           "used": ["deepseek:deepseek-v4-pro"],
                                                           "exhausted_at_min": 18.7})
    rep = arm_reading.read_arm([a, b, lost], "start")
    assert [r["run"] for r in rep["runs"]] == ["a", "b"] and rep["excluded"][0]["run"] == "lost"
    assert "Left out, each its own arm" in arm_reading.render_arm(rep)
    with pytest.raises(ValueError, match="at least two runs whose planner did not change"):
        arm_reading.read_arm([a, lost], "start")


def test_old_readings_are_read_again(tmp_path):
    a = _reading(tmp_path, "a", 0.01, 0.004)
    rep = json.loads(a.read_text())
    del rep["runs"][0]["planner"]
    old = tmp_path / "old.json"
    old.write_text(json.dumps(rep))
    with pytest.raises(ValueError, match="read the run again"):
        arm_reading.read_arm([old, _reading(tmp_path, "b", 0.01, 0.004)], "start")


def test_the_arm_reading_refuses_what_it_cannot_read(tmp_path):
    a, b = _reading(tmp_path, "a", 0.01, 0.004), _reading(tmp_path, "b", 0.01, 0.004, split="split_y")
    with pytest.raises(ValueError, match="differ in split_id"):
        arm_reading.read_arm([a, b], "start")
    with pytest.raises(ValueError, match="at least two runs"):
        arm_reading.read_arm([a], "start")
    with pytest.raises(ValueError, match="every run kept its reference"):
        arm_reading.read_arm([_reading(tmp_path, "k1", 0, 0, kept=True), _reading(tmp_path, "k2", 0, 0, kept=True)],
                             "start")
    with pytest.raises(ValueError, match="appears twice"):
        arm_reading.read_arm([a, a], "start")
    c = _reading(tmp_path, "c", 0.01, 0.004, start=False)
    with pytest.raises(ValueError, match="no starting-model comparison"):
        arm_reading.read_arm([a, c], "start")
    with pytest.raises(ValueError, match="no --versus reading"):
        arm_reading.read_arm([a, c], "versus")


def test_versus_readings_make_an_arm(tmp_path):
    paths = []
    for i, d in enumerate((0.02, 0.03)):
        rep = {"runs": [{"run": f"f1_r{i}", "dataset": "adamson", "split_id": "s", "planner": None},
                        {"run": "f0", "dataset": "adamson", "split_id": "s", "planner": None}],
               "pair": {"mode": "versus", "a": {"run": f"f1_r{i}", "experiment_id": "EXP_5", "base_commit": "x"},
                        "b": {"run": "f0", "experiment_id": "EXP_3"},
                        "sealed": {"a": {"metrics": {"pearson_delta": 0.6}}, "paired": _paired(d, 0.005, n=21)},
                        "visible": _paired(d, 0.004, n=67), "cluster_ratio": {"ratio": 1.0}}}
        paths.append(tmp_path / f"v{i}.json")
        paths[-1].write_text(json.dumps(rep))
    arm = arm_reading.read_arm(paths, "versus")
    assert arm["pooled"]["G"] == pytest.approx(0.025) and arm["pooled"]["SE"] > arm["pooled"]["S"]
    assert arm["runs"][0]["reference"] == "f0:EXP_3"


def test_the_combined_model_is_the_members_average_against_one_reference(make_lab, tmp_path):
    bundle = make_pair_bundle(tmp_path / "bundle")
    r0, e0 = make_lab(bundle=bundle)
    r1, e1 = make_lab(bundle=bundle, alpha_grid=(1000.0,))
    before = [_sealed_events(r0), _sealed_events(r1)]
    rep = arm_reading.combine([str(r0.run_dir), str(r1.run_dir)], [f"{r0.run_dir}:additive"])
    assert [m["experiment_id"] for m in rep["a"]["models"]] == [e0, e1]
    assert rep["b"]["models"][0]["experiment_id"] == _additive_id(r0) and rep["protocol"]["sealed_scorings"] == 2
    oracle = QueryOracle(bundle, max_queries=2)
    perts = list(oracle.perts)
    p0, o0 = r0._predict(r0.db.get_experiment(e0), perts)
    p1, o1 = r1._predict(r1.db.get_experiment(e1), perts)
    assert o0 == o1 == perts
    pa = (p0 + p1) / 2
    pb, _ = r0._predict(r0.db.get_experiment(_additive_id(r0)), perts)
    own = oracle.query_paired("combined", pa, perts, "reference", pb, perts, r0.control_mean, metric="pearson_delta")
    assert rep["sealed"]["paired"] == json.loads(json.dumps(own["paired"]))
    v0, c0 = r0.visible_predictions(e0)
    v1, c1 = r1.visible_predictions(e1)
    vb, cb = r0.visible_predictions(_additive_id(r0))
    sa, cats = r0.score_visible((v0 + v1) / 2, (c0 + c1) / 2)
    sb, _ = r0.score_visible(vb, cb)
    vis = paired_summary(metric_values(sa, "pearson_delta"), metric_values(sb, "pearson_delta"), cats or None)
    assert rep["visible"]["same_folds"] is True and rep["visible"]["mean_diff"] == pytest.approx(vis["mean_diff"])
    assert [_sealed_events(r0), _sealed_events(r1)] == before
    md = arm_reading.render_combined(rep)
    assert "A: combined model of" in md and "| sealed, pooled |" in md and "## Reading" in md
    out = tmp_path / "combined.md"
    assert arm_reading.main(["combine", "--members", str(r0.run_dir), str(r1.run_dir), "--reference",
                             f"{r0.run_dir}:additive", "--out", str(out)]) == 0
    assert json.loads(out.with_suffix(".json").read_text())["sealed"]["paired"] == rep["sealed"]["paired"]


def test_a_combined_model_against_another_combined_model(make_lab, tmp_path):
    bundle = make_pair_bundle(tmp_path / "bundle")
    labs = [make_lab(bundle=bundle, alpha_grid=(g,))[0] for g in (1.0, 10.0, 100.0, 1000.0)]
    rep = arm_reading.combine([str(labs[0].run_dir), str(labs[1].run_dir)],
                              [str(labs[2].run_dir), str(labs[3].run_dir)])
    assert len(rep["b"]["models"]) == 2 and rep["b"]["label"].startswith("combined model of")


def test_combine_refuses_what_it_cannot_compare(make_lab, bundles, tmp_path):
    a, _ = make_lab()
    b, _ = make_lab(alpha_grid=(1000.0,))
    other, _ = make_lab(bundle=bundles[1])
    with pytest.raises(ValueError, match="differ in"):
        arm_reading.combine([str(a.run_dir), str(other.run_dir)], [f"{a.run_dir}:additive"])
    with pytest.raises(ValueError, match="selected models only"):
        arm_reading.combine([str(a.run_dir), f"{b.run_dir}:additive"], [f"{a.run_dir}:additive"])
    with pytest.raises(ValueError, match="at least two members"):
        arm_reading.combine([str(a.run_dir)], [f"{a.run_dir}:additive"])
    with pytest.raises(ValueError, match="the combined model itself"):
        arm_reading.combine([str(a.run_dir), str(b.run_dir)], [str(a.run_dir), str(b.run_dir)])
    with pytest.raises(ValueError, match="not 'EXP_0001'"):
        arm_reading.combine([str(a.run_dir), str(b.run_dir)], [f"{a.run_dir}:EXP_0001"])
