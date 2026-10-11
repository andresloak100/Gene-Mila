"""tools/time_to_best.py: the free 'did the run go flat?' check reads visible scores only."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import time_to_best  # noqa: E402

from genemila.db import Database  # noqa: E402


def test_never_reads_the_sealed_labels():
    src = (ROOT / "tools" / "time_to_best.py").read_text()
    for word in ("val2", "query_metrics", "query_only", "oracle"):
        assert word not in src, word


def _run_dir(tmp_path, improvements, budget_s=1200.0, rounds=(100.0, 950.0, 1150.0)):
    d = tmp_path / "run_a"
    d.mkdir(parents=True)
    db = Database(d / "lab.db")
    t0 = 1_000_000.0
    db.conn.execute("INSERT INTO runs (run_id, started_at, deadline, workers) VALUES (?, ?, ?, ?)", ("run_a", t0, t0 + budget_s, 4))
    db.insert_experiment({"experiment_id": "EXP_0001", "status": "completed", "kind": "baseline", "finished_at": t0 + 5,
                          "primary_score": 0.0})  # "predict no change": not the starting model
    db.insert_experiment({"experiment_id": "EXP_0002", "status": "completed", "kind": "baseline", "finished_at": t0 + 10,
                          "primary_score": 0.5})  # the starting model is the best baseline fit
    for n, (sec, score) in enumerate(improvements, start=3):
        db.insert_experiment({"experiment_id": f"EXP_{n:04d}", "status": "completed", "kind": "new_feature",
                              "finished_at": t0 + sec, "primary_score": score})
    db.insert_experiment({"experiment_id": "EXP_0999", "status": "completed", "kind": "ensemble", "finished_at": t0 + 1190,
                          "primary_score": 0.99})  # ensembles are not experiments
    db.insert_experiment({"experiment_id": "EXP_0998", "status": "failed", "finished_at": t0 + 500})
    for ts in rounds:
        db.conn.execute("INSERT INTO planner_rounds (ts, provider, model) VALUES (?, 'scripted', 'scripted')", (t0 + ts,))
    db.conn.commit()
    (d / "config.json").write_text(json.dumps({"planner": {"provider": "scripted"}, "worker": {"provider": "mock"},
                                              "run": {"workers": 4}}))
    return d


def test_last_improvement_and_shares(tmp_path):
    d = _run_dir(tmp_path, [(60, 0.55), (300, 0.60), (400, 0.58), (960, 0.62), (1100, 0.61)])
    r = time_to_best.analyse_run(d)
    assert r["arm"] == "scripted control (no LLM)" and r["workers"] == 4
    assert r["budget_min"] == 20.0 and r["start"] == 0.5 and r["final_best"] == 0.62
    assert r["n_improvements"] == 3 and r["last_improvement_min"] == 16.0 and r["still_rising"] and r["used_budget"]
    assert abs(r["gain_last_quarter"] - 0.02) < 1e-9 and abs(r["gain_last_half"] - 0.02) < 1e-9
    assert abs(r["share_at"]["0.25"] - (0.60 - 0.5) / 0.12) < 1e-9  # 5 min in: best so far 0.60
    assert r["share_at"]["0.5"] == r["share_at"]["0.75"] == r["share_at"]["0.25"]
    assert r["experiments_after"] == 1 and r["experiments"] == 5 and r["planner_rounds_after"] == 1


def test_flat_run_and_report(tmp_path):
    d = _run_dir(tmp_path, [(60, 0.55), (120, 0.56), (1100, 0.50)])
    r = time_to_best.analyse_run(d)
    assert r["last_improvement_min"] == 2.0 and not r["still_rising"] and r["experiments_after"] == 1
    assert r["share_at"]["0.25"] == 1.0 and r["gain_last_quarter"] == 0.0 and r["used_budget"]
    ds = _run_dir(tmp_path / "s", [(60, 0.55), (120, 0.56)])
    Database(ds / "lab.db").conn.execute("DELETE FROM experiments WHERE experiment_id IN ('EXP_0998', 'EXP_0999')")
    Database(ds / "lab.db").conn.commit()
    short = time_to_best.analyse_run(ds)
    assert not short["used_budget"] and short["duration_min"] == 2.0  # ended long before its final quarter: counted neither way
    # a run that lasted its budget but completed nothing late is "no", not "ended early"
    d2 = _run_dir(tmp_path / "q", [(60, 0.55), (780, 0.60)])
    Database(d2 / "lab.db").conn.execute("UPDATE experiments SET finished_at = finished_at + 1100, status='failed' "
                                         "WHERE experiment_id='EXP_0998'")
    Database(d2 / "lab.db").conn.commit()
    quiet = time_to_best.analyse_run(d2)
    assert quiet["used_budget"] and not quiet["still_rising"] and quiet["last_improvement_min"] == 13.0
    out = tmp_path / "report.md"
    assert time_to_best.main(["--runs", str(d), str(tmp_path / "missing"), "--out", str(out)]) == 0
    md = out.read_text()
    assert ("| run_a | scripted control (no LLM) | 4 | 20.0 | 0.500 → 0.560 | 100% / 100% / 100% | +0.0000 | +0.0000 "
            "| 2.0 | 1 of 3 | 2 | no |") in md
    assert "0 of 1 runs that used their budget were still rising" in md
    assert json.loads(out.with_suffix(".json").read_text())[0]["run_id"] == "run_a"


def test_warm_started_runs_are_shown_but_not_counted(tmp_path):
    d = _run_dir(tmp_path, [(5, 0.59), (600, 0.591)])
    cfg = json.loads((d / "config.json").read_text())
    cfg["run"]["continue_from"] = "/x/runs/agents_w4_r0"
    (d / "config.json").write_text(json.dumps(cfg))
    r = time_to_best.analyse_run(d)
    assert r["continuation"] and r["arm"] == "no-LLM continuation of agents_w4_r0"
    md = time_to_best.render([r])
    assert "| continuation (its gain is the warm start) |" in md and "not counted" in md
    assert "No run used its final quarter" in md  # nothing counted: the only run is a continuation
