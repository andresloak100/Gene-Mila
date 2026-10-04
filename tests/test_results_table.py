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
