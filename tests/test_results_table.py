import json

import numpy as np

from genemila.benchmark import table


def test_simple_baselines_and_calibration(dataset):
    base = table.simple_baselines(dataset, "val2", rf_seeds=(0, 1))
    assert set(base) >= {"Unperturbed", "Linear Regression", "Random Forest", "Mean training response"}
    for name, row in base.items():
        for c in table.COLUMNS:
            assert row[c] is not None and np.isfinite(row[c]["mean"]), (name, c)
    assert base["Random Forest"]["mse"]["n"] == 2 and base["Unperturbed"]["mse"]["n"] == 1
    # under the unseen-perturbation protocol one-hot codes carry nothing: LR returns one profile for every
    # held-out perturbation, the mean training response
    assert abs(base["Linear Regression"]["mse"]["mean"] - base["Mean training response"]["mse"]["mean"]) < 1e-6

    cal = table.calibration(dataset, "val2", rf_seeds=(0,))
    defs = cal["definitions"]["Unperturbed"]
    assert set(defs) >= {"means/log1p", "means/log1p/pooled", "means/delta", "cells/log1p/pooled"}
    assert defs["means/log1p"][:6] == [base["Unperturbed"][c]["mean"] for c in table.COLUMNS]
    # a constant prediction has no correlation with the truth once genes are centred over samples
    assert abs(defs["means/log1p/pooled"][1]) < 1e-9 and defs["means/log1p/pooled"][2] < 0
    md = table.render_calibration(cal, {"Unperturbed": [0.98, 0.0, -0.01, 3.8, 0.0, -4.2]})
    assert "Closest to the paper" in md


def test_table_from_run_summary(tmp_path, dataset):
    """A run directory with a summary.json renders next to the paper's rows, ranked from the means."""
    run = tmp_path / "run_w4"
    run.mkdir()
    comp = {f"cellforge_{c}": v for c, v in zip(table.COLUMNS, (0.01, 0.98, 0.95, 0.2, 0.9, 0.8))}
    base = {f"cellforge_{c}": v for c, v in zip(table.COLUMNS, (0.02, 0.97, 0.93, 0.3, 0.85, 0.7))}
    summary = {"run_id": "run_w4", "dataset": "adamson_cf", "split_id": "split_x", "workers": 4, "duration_s": 1200,
               "best": {"features": ["a", "b"], "model": "ridge"},
               "baseline": {"description": "RIDGE on baseline features"},
               "generalization_query_only": [
                   {"experiment_id": "EXP_0100", "kind": "new_feature", "query_only_score": 0.5,
                    "comparable": {"val1": comp, "val2": comp}},
                   {"experiment_id": "EXP_0003", "kind": "baseline", "query_only_score": 0.4,
                    "comparable": {"val1": base, "val2": base}}]}
    (run / "summary.json").write_text(json.dumps(summary))
    (run / "config.json").write_text(json.dumps({"run": {"workers": 4, "data_dir": str(dataset)},
                                                 "planner": {"provider": "claude_cli", "model": "opus"},
                                                 "worker": {"provider": "deepseek", "model": "deepseek-flash"}}))
    paper = tmp_path / "paper.json"
    paper.write_text(json.dumps({"source": "test", "notes": ["n1"], "datasets": {"adamson": {
        "title": "Adamson", "rows": {"Unperturbed": [0.98, 0.0, -0.01, 3.8, 0.0, -4.2],
                                     "CPA": [0.0067, 0.9833, 0.9845, 0.1447, 0.9024, 0.8896]},
        "std": {}}}}))
    t = table.build([run], paper, part="val2")
    assert t["blocks"][0]["best"]["mse"]["mean"] == 0.01 and t["blocks"][0]["n_runs"] == 1
    md = table.render(t)
    assert "| CPA | reported |" in md and "Unperturbed (rerun) | rerun |" in md
    assert "| CPA | reported | **0.0067**¹" in md
    assert "Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers, 4 workers (n=1) | ours | 0.0100²" in md
    assert "No scripted no-LLM control run" in md
    assert "Gene-Mila starting model | ours |" in md and "documented DE set" in md


def _run_dir(tmp_path, name, workers, planner, worker, gain_sealed, wall_s, commit="abc1234", seed=0):
    run = tmp_path / name
    run.mkdir()
    base_q, best_q = 0.50, 0.50 + gain_sealed
    summary = {"run_id": name, "dataset": "adamson_cf", "split_id": "split_x", "workers": workers, "duration_s": wall_s,
               "base_commit": commit, "best": {"score": 0.57 + gain_sealed, "features": ["a"], "model": "ridge"},
               "baseline": {"score": 0.556, "description": "OLS"}, "improvement_over_baseline": 0.014 + gain_sealed,
               "experiments_completed": 9, "experiments_failed": 1, "unique_hypotheses": 9, "duplicate_experiments": 0,
               "cpu_hours": 0.01, "llm_usage": {"all": {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "cost_usd": 0}},
               "compute_efficiency": {"experiments_per_hour": 9 / (wall_s / 3600)},
               "generalization_query_only": [
                   {"experiment_id": "EXP_0010", "kind": "config", "visible_score": 0.571, "query_only_score": best_q},
                   {"experiment_id": "EXP_0003", "kind": "baseline", "visible_score": 0.556, "query_only_score": base_q}]}
    (run / "summary.json").write_text(json.dumps(summary))
    (run / "config.json").write_text(json.dumps({"run": {"workers": workers, "seed": seed},
                                                 "planner": {"provider": planner, "model": planner},
                                                 "worker": {"provider": worker, "model": worker}}))
    return run


def test_scaling_report_handles_a_deterministic_short_control(tmp_path):
    """Six identical control runs give no noise estimate and ended early: the report says both instead of
    announcing a zero-width noise band; runs on another code version form their own arm."""
    import scaling_report as sr
    dirs = [_run_dir(tmp_path, f"scale_control_r{i}", 4, "scripted", "mock", 0.034, 126, seed=i) for i in range(3)]
    dirs += [_run_dir(tmp_path, f"scale_w4_r{i}", 4, "claude_cli", "deepseek", 0.08 + 0.01 * i, 1200) for i in range(2)]
    dirs += [_run_dir(tmp_path, f"scale_w8_r{i}", 8, "claude_cli", "deepseek", 0.07 + 0.03 * i, 1200) for i in range(2)]
    md = sr.render(sr.load_runs(dirs))
    assert "identical results every time" in md and "not a noise reference" in md
    assert "2 x this sd (0.0000)" not in md
    assert "not an equal-time arm" in md and "2.1 min on average" in md
    assert "4 vs 8 workers" in md and "Welch" in md
    # a control on new code is a separate arm, not more repeats of the old one
    dirs.append(_run_dir(tmp_path, "newcode_control_r0", 4, "scripted", "mock", 0.05, 1200, commit="def5678"))
    runs = sr.load_runs(dirs)
    assert {r["arm"] for r in runs if r["dir"].startswith("newcode")} == {"scripted control (no LLM) @ def5678"}
    bullets = [l for l in sr.render(runs).splitlines() if l.startswith("- scripted control (no LLM) @")]
    assert sum(l.startswith("- scripted control (no LLM) @ abc1234, 4 workers (3 runs)") for l in bullets) == 1
    assert sum(l.startswith("- scripted control (no LLM) @ def5678, 4 workers (1 run,") for l in bullets) == 1


def test_handoff_state_flags_stale_clones_and_ledger_bypass(tmp_path):
    """The one-command state says how far the checkout is from the integration branch and names paid runs
    whose config points at another ledger (they would bypass the cumulative cap)."""
    import handoff_state as hs
    (tmp_path / "runs").mkdir()
    shared = tmp_path / "runs" / "spend_ledger.sqlite"
    on = _run_dir(tmp_path / "runs", "paid_on_ledger", 4, "deepseek", "deepseek", 0.05, 1200)
    off = _run_dir(tmp_path / "runs", "paid_elsewhere", 4, "deepseek", "deepseek", 0.05, 1200)
    free = _run_dir(tmp_path / "runs", "free_control", 4, "scripted", "mock", 0.05, 1200)
    for d, ledger in ((on, str(shared)), (off, "runs/other.sqlite"), (free, "runs/other.sqlite")):
        cfg = json.loads((d / "config.json").read_text())
        cfg["budget"] = {"ledger": ledger}
        (d / "config.json").write_text(json.dumps(cfg))
    rows = {r["dir"]: r for r in (hs.run_state(d, shared) for d in (on, off, free))}
    assert rows["paid_on_ledger"]["paid"] and rows["paid_on_ledger"]["ledger_ok"]
    assert rows["paid_elsewhere"]["paid"] and rows["paid_elsewhere"]["ledger_ok"] is False
    assert not rows["free_control"]["paid"] and rows["free_control"]["ledger_ok"] is None
    g = hs.git_state(hs.REPO_ROOT)
    assert g["integration_branch"] == hs.INTEGRATION_BRANCH and ("behind" in g)
