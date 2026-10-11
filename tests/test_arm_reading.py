"""tools/arm_reading.py: the arm reading and the combined model of docs/PLAN_AFTER_N4.md. The rule reads the runs'
own sealed readings only (G = mean difference, SE = sqrt(S² + sd_g²/R) with S the mean paired SE inflated by the
overlap-robust clustering ratio, a gain when G > k·SE, every run has G's sign and the favoured side wins most
perturbation-run pairs) over runs that answer the same question and finished with their planner unchanged; the
combined model is the plain average of the members' predictions, answered by one paired query of the tool's own
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
import sealed_reading  # noqa: E402

W = [(40, 16, 56)] * 3
CLEAN = {"configured": "deepseek:deepseek-v4-pro", "used": ["deepseek:deepseek-v4-pro"], "mixed": False}


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


def _sealed(d, se, cats=None):
    # QueryOracle.query_paired's metrics are evaluate()'s only: the comparable (cellforge_*) ones are not among them
    return {"a": {"metrics": {"pearson_delta": 0.7, "mse": 0.01}}, "b": {"metrics": {}},
            "paired": _paired(d, se, cats=cats)}


def _ratio(r=1.0, jk=1.3):
    return {"ratio": r, "estimator": "overlap-robust", "jackknife_ratio": jk, "n_perts": 63, "n_genes": 42,
            "n_overlapping_pairs": 10}


def _reading(tmp_path, run, d, se, split="split_x", start=True, is_additive=False, cats=None, pd=0.72,
             planner=CLEAN, kept=False, ratio=1.0, has_summary=True, bundle="/data/norman", knowledge=("rep",),
             kind="warm_start", alpha=20000.0):
    """One run's sealed_reading JSON twin: against its additive baseline the difference is d / 2, against its start
    d; the selected model's own end-of-run scoring carries pd and the comparable DE metrics."""
    stored = {"pearson_delta": pd, "cellforge_mse_de": 0.10 + pd / 100, "cellforge_pcc_de": 0.9,
              "cellforge_r2_de": 0.8}
    r = {"run": run, "dataset": "norman", "split_id": split, "bundle": bundle, "has_summary": has_summary,
         "selection": "pearson_delta", "external_knowledge": list(knowledge), "base_commit": "076282c",
         "planner": planner, "selected": {"experiment_id": "EXP_9", "stored_sealed": stored},
         "additive": {"experiment_id": "EXP_2"}, "sealed": _sealed(d / 2, se, cats),
         "visible": _paired(d * 3, se, cats=cats), "cluster_ratio": _ratio(ratio), "note": None}
    if start:
        base = {"kind": kind, "source": {"run": "n2", "experiment_id": "EXP_0198", "alpha": 50000.0},
                "start": {"experiment_id": "EXP_7", "alpha": alpha}}
        r["continuation"] = ({**base, "start": None, "sealed": None, "note": "same", "is_additive": True}
                             if is_additive else
                             {**base, "sealed": None, "visible": None, "cluster_ratio": None,
                              "note": "the run selected its starting model: its search added nothing it kept"}
                             if kept else
                             {**base, "sealed": _sealed(d, se, cats), "visible": _paired(d * 2, se),
                              "cluster_ratio": _ratio(ratio), "note": None})
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
    assert rep["protocol"]["sealed_scorings"] == 0 and rep["same_code"] is True and rep["excluded"] == []
    assert rep["by_category"]["single"]["read"] is True and rep["by_category"]["combo_seen0"]["read"] is False
    assert rep["visible"]["G"] == pytest.approx(2 * p["G"]) and rep["visible"]["S"] == pytest.approx(0.004)
    s = rep["selected_spread"]
    assert s["pearson_delta"]["mean"] == pytest.approx(0.726)
    assert s["pearson_delta"]["sd"] == pytest.approx(np.std([0.726, 0.730, 0.722], ddof=1))
    assert s["MSE_DE"]["n"] == 3 and s["R²_DE"]["mean"] == pytest.approx(0.8)   # from the runs' own scorings
    add = arm_reading.read_arm(paths, "additive")
    assert add["pooled"]["G"] == pytest.approx(p["G"] / 2) and add["selected_spread"] == s
    assert [x["sha256"] for x in rep["readings"]] == [arm_reading._sha256(x) for x in paths]
    assert rep["runs"][0]["start_alpha"] == 20000.0 and rep["runs"][0]["source_alpha"] == 50000.0
    md = arm_reading.render_arm(rep)
    assert "| sealed, pooled | +0.0103 | 0.0040 |" in md and "| arm better |" in md
    assert "reported, not read" in md and "| MSE_DE |" in md and "20000 / 50000" in md
    assert "scored nothing on the sealed set" in md and "## Reading" in md


def test_a_fresh_start_that_is_the_additive_baseline_reads_the_additive_comparison(tmp_path):
    paths = [_reading(tmp_path, "a", 0.01, 0.004, is_additive=True, kind="fresh"),
             _reading(tmp_path, "b", 0.01, 0.004, kind="fresh")]
    rep = arm_reading.read_arm(paths, "start")
    assert rep["runs"][0]["mean_diff"] == pytest.approx(0.005) and rep["runs"][1]["mean_diff"] == pytest.approx(0.01)


def test_inflation_kept_references_and_runs_that_are_their_own_arm(tmp_path):
    """A run's SE is multiplied by its overlap-robust ratio when above 1 (the jackknife first specified is reported
    beside it); a run that kept its reference enters with g = 0, s = 0 and its selected model still counts in the
    spread; a run whose planner changed, or with no summary.json, is left out and named."""
    a = _reading(tmp_path, "a", 0.010, 0.002, ratio=1.5)
    b = _reading(tmp_path, "b", 0.010, 0.002, ratio=0.8, alpha=6e-05)
    rep = arm_reading.read_arm([a, b], "start")
    assert "| 6e-05 / 50000 |" in arm_reading.render_arm(rep)   # small ridge alphas keep their digits
    assert [r["inflation"] for r in rep["runs"]] == [1.5, 1.0]
    assert rep["pooled"]["S"] == pytest.approx((0.003 + 0.002) / 2)
    assert rep["pooled_as_first_specified"]["S"] == pytest.approx(0.002 * 1.3)
    kept = _reading(tmp_path, "kept", 0.0, 0.0, kept=True, pd=0.719)
    rep = arm_reading.read_arm([a, b, kept], "start")
    assert rep["pooled"]["g"][2] == 0 and rep["pooled"]["verdict"] == "none" and rep["runs"][2]["selected_reference"]
    assert rep["pooled"]["pairs"] == 3 * 56 and rep["selected_spread"]["pearson_delta"]["n"] == 3
    assert "0 (kept its reference)" in arm_reading.render_arm(rep)
    lost = _reading(tmp_path, "lost", 0.05, 0.002, planner={**CLEAN, "mixed": True, "exhausted_at_min": 18.7})
    unfinished = _reading(tmp_path, "unfinished", 0.05, 0.002, planner=None, has_summary=False)
    rep = arm_reading.read_arm([a, b, lost, unfinished], "start")
    assert [r["run"] for r in rep["runs"]] == ["a", "b"]
    assert [e["run"] for e in rep["excluded"]] == ["lost", "unfinished"]
    md = arm_reading.render_arm(rep)
    assert "Left out: lost, its planner changed or ran out" in md and "Left out: unfinished, no summary.json" in md
    with pytest.raises(ValueError, match="at least two runs with a summary.json and an unchanged planner"):
        arm_reading.read_arm([a, lost], "start")


def test_old_readings_are_read_again(tmp_path):
    b = _reading(tmp_path, "b", 0.01, 0.004)
    for drop in ("planner", "bundle", "has_summary", "stored_sealed", "estimator"):
        rep = json.loads(_reading(tmp_path, "a", 0.01, 0.004).read_text())
        r = rep["runs"][0]
        if drop == "stored_sealed":
            del r["selected"]["stored_sealed"]
        elif drop == "estimator":
            del r["continuation"]["cluster_ratio"]["estimator"]
        else:
            del r[drop]
        old = tmp_path / "old.json"
        old.write_text(json.dumps(rep))
        with pytest.raises(ValueError, match="read the run again"):
            arm_reading.read_arm([old, b], "start")


def test_the_arm_reading_refuses_runs_that_answer_different_questions(tmp_path):
    a = _reading(tmp_path, "a", 0.01, 0.004)
    for kwargs, what in (({"split": "split_y"}, "split_id"), ({"bundle": "/data/other"}, "bundle"),
                         ({"knowledge": ()}, "external_knowledge"), ({"kind": "fresh"}, "start_kind")):
        with pytest.raises(ValueError, match=f"differ in {what}"):
            arm_reading.read_arm([a, _reading(tmp_path, "b", 0.01, 0.004, **kwargs)], "start")
    with pytest.raises(ValueError, match="at least two runs"):
        arm_reading.read_arm([a], "start")
    with pytest.raises(ValueError, match="appears twice"):
        arm_reading.read_arm([a, a], "start")
    with pytest.raises(ValueError, match="every run kept its reference"):
        arm_reading.read_arm([_reading(tmp_path, "k1", 0, 0, kept=True), _reading(tmp_path, "k2", 0, 0, kept=True)],
                             "start")
    c = _reading(tmp_path, "c", 0.01, 0.004, start=False)
    with pytest.raises(ValueError, match="no starting-model comparison"):
        arm_reading.read_arm([a, c], "start")
    with pytest.raises(ValueError, match="no --versus reading"):
        arm_reading.read_arm([a, c], "versus")


def _versus(tmp_path, name, a_run, b_run, d, b_exp="EXP_3"):
    run = {"dataset": "adamson", "split_id": "s", "bundle": "/data/adamson_fresh", "has_summary": True,
           "selection": "pearson_delta", "external_knowledge": ["rep"], "planner": CLEAN}
    rep = {"runs": [{"run": a_run, **run}, {"run": b_run, **run}],
           "pair": {"mode": "versus",
                    "a": {"run": a_run, "experiment_id": "EXP_5", "base_commit": "x",
                          "stored_sealed": {"pearson_delta": 0.6}},
                    "b": {"run": b_run, "experiment_id": b_exp},
                    "sealed": _sealed(d, 0.005), "visible": _paired(d, 0.004, n=67), "cluster_ratio": _ratio()}}
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(rep))
    return path


def test_versus_readings_make_an_arm_against_one_reference(tmp_path):
    paths = [_versus(tmp_path, f"v{i}", f"f1_r{i}", "f0", d) for i, d in enumerate((0.02, 0.03))]
    arm = arm_reading.read_arm(paths, "versus")
    assert arm["pooled"]["G"] == pytest.approx(0.025) and arm["pooled"]["SE"] > arm["pooled"]["S"]
    assert arm["runs"][0]["reference"] == "f0:EXP_3" and arm["selected_spread"]["pearson_delta"]["n"] == 2
    with pytest.raises(ValueError, match="compare against different models"):
        arm_reading.read_arm([paths[0], _versus(tmp_path, "other", "f1_r1", "f0", 0.03, b_exp="EXP_4")], "versus")
    with pytest.raises(ValueError, match="both a member of the arm and the reference"):
        arm_reading.read_arm([paths[0], _versus(tmp_path, "self", "f0", "f0", 0.01)], "versus")


def _finish(lab, planner=CLEAN):
    """What a run's report writes when it ends, as far as the tools read it: summary.json with its planner record."""
    (lab.run_dir / "summary.json").write_text(json.dumps({"planner": planner}))
    return lab


def test_the_combined_model_is_the_members_average_against_one_reference(make_lab, tmp_path):
    bundle = make_pair_bundle(tmp_path / "bundle")
    r0, e0 = make_lab(bundle=bundle)
    r1, e1 = make_lab(bundle=bundle, alpha_grid=(1000.0,))
    _finish(r0), _finish(r1)
    before = [_sealed_events(r0), _sealed_events(r1)]
    rep = arm_reading.combine([str(r0.run_dir), str(r1.run_dir)], [f"{r0.run_dir}:additive"])
    assert [m["experiment_id"] for m in rep["a"]["models"]] == [e0, e1]
    assert all(m["planner"] == CLEAN and m["has_summary"] for m in rep["a"]["models"])
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
    va, _ = r0.score_visible((v0 + v1) / 2, None)
    vv = rep["visible_validation"]
    assert vv["n"] == len(r0._val1.perts) and vv["a"] == pytest.approx(
        np.mean(list(metric_values(va, "pearson_delta").values())))
    md = arm_reading.render_combined(rep)
    assert "visible validation perturbations alone" in md
    assert "A: combined model of" in md and "| sealed, pooled |" in md and "## Reading" in md
    out = tmp_path / "combined.md"
    assert arm_reading.main(["combine", "--members", str(r0.run_dir), str(r1.run_dir), "--reference",
                             f"{r0.run_dir}:additive", "--out", str(out)]) == 0
    assert json.loads(out.with_suffix(".json").read_text())["sealed"]["paired"] == rep["sealed"]["paired"]


def test_a_combined_model_against_another_combined_model(make_lab, tmp_path):
    bundle = make_pair_bundle(tmp_path / "bundle")
    labs = [_finish(make_lab(bundle=bundle, alpha_grid=(g,))[0]) for g in (1.0, 10.0, 100.0, 1000.0)]
    rep = arm_reading.combine([str(labs[0].run_dir), str(labs[1].run_dir)],
                              [str(labs[2].run_dir), str(labs[3].run_dir)])
    assert len(rep["b"]["models"]) == 2 and rep["b"]["label"].startswith("combined model of")


def test_combine_refuses_what_it_cannot_compare(make_lab, bundles, tmp_path):
    a, _ = make_lab()
    b, _ = make_lab(alpha_grid=(1000.0,))
    other, _ = make_lab(bundle=bundles[1])
    lost, _ = make_lab(alpha_grid=(10.0,))
    unfinished, _ = make_lab(alpha_grid=(3.0,))
    _finish(a), _finish(b), _finish(other), _finish(lost, {**CLEAN, "mixed": True, "exhausted_at_min": 18.7})
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
    with pytest.raises(ValueError, match="its own arm"):
        arm_reading.combine([str(a.run_dir), str(lost.run_dir)], [f"{a.run_dir}:additive"])
    with pytest.raises(ValueError, match="no summary.json"):
        arm_reading.combine([str(a.run_dir), str(unfinished.run_dir)], [f"{a.run_dir}:additive"])


def test_readings_written_by_sealed_reading_feed_the_arm(make_lab, tmp_path):
    """End to end: two runs read by tools/sealed_reading.py, then by the arm tool, whose spread comes from the
    selected models' own end-of-run scorings."""
    bundle = make_pair_bundle(tmp_path / "bundle")
    paths = []
    for i, g in enumerate((1.0, 1000.0)):
        lab, _ = make_lab(bundle=bundle, alpha_grid=(g,))
        _finish(lab)
        out = tmp_path / f"reading{i}.md"
        assert sealed_reading.main(["--runs", str(lab.run_dir), "--out", str(out)]) == 0
        paths.append(out.with_suffix(".json"))
    rep = arm_reading.read_arm(paths, "additive")
    assert rep["excluded"] == [] and rep["pooled"]["R"] == 2
    assert rep["selected_spread"]["pearson_delta"]["n"] == 2
    assert "Arm reading" in arm_reading.render_arm(rep)
