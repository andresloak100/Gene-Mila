import json

import pytest

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


def _run_dir(tmp_path, name, workers, planner, worker, gain_sealed, wall_s, commit="abc1234", seed=0, rule=None,
             start_metrics=None, continue_from=None):
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
    cfg = {"run": {"workers": workers, "seed": seed}, "planner": {"provider": planner, "model": planner},
           "worker": {"provider": worker, "model": worker}}
    if rule:  # a run under another selection rule: its scores are on that rule's scale, pearson_delta by name
        cfg["experiment"] = {"selection": rule}
        summary["selection"] = {"rule": rule}
        summary["best"] = {**summary["best"], "score": 0.71, "metrics": {"pearson_delta": 0.61}}
        summary["improvement_over_baseline"] = 0.075
        for g in summary["generalization_query_only"]:
            g["query_only_pearson_delta"] = g["query_only_score"]
            g["query_only_score"] = g["query_only_score"] + 0.1
        if start_metrics:
            summary["baseline"]["metrics"] = start_metrics
    (run / "summary.json").write_text(json.dumps(summary))
    if continue_from:
        cfg["run"]["continue_from"] = continue_from
    (run / "config.json").write_text(json.dumps(cfg))
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
    # each control is placed against the agent arms at its worker count (here one agent arm, gains 0.08 and 0.09)
    lines = [l for l in sr.render(runs).splitlines() if "against the agent arms at 4 workers" in l]
    assert len(lines) == 2
    assert any(l.startswith("- scripted control (no LLM) @ abc1234, 4 workers against the agent arms at 4 workers: "
                            "sealed gain 0.0340 ± 0.0000 vs 0.0850 ± 0.0071 (") and l.endswith("): below every agent arm.") for l in lines), lines
    dirs.append(_run_dir(tmp_path, "strong_control_r0", 4, "scripted", "mock", 0.086, 180, commit="fff0000"))
    lines = [l for l in sr.render(sr.load_runs(dirs)).splitlines() if "against the agent arms at 4 workers" in l]
    assert any(l.startswith("- scripted control (no LLM) @ fff0000, 4 workers against") and l.endswith(
        "): above every agent arm, so the agents' gain over this control on sealed pearson_delta is not established.")
        for l in lines), lines
    # two arms at the same worker count (another code version, another planner) are tested against each
    # other too, and the planner-dollar row no longer calls API spend an estimate
    dirs += [_run_dir(tmp_path, f"newcode_w4_r{i}", 4, "claude_cli", "deepseek", 0.06 + 0.01 * i, 1200, commit="def5678")
             for i in range(2)]
    dirs += [_run_dir(tmp_path, f"ds_w4_r{i}", 4, "deepseek", "deepseek", 0.02 + 0.06 * i, 1200, commit="def5678")
             for i in range(2)]
    md = sr.render(sr.load_runs(dirs))
    assert "- claude_cli:claude_cli planner, deepseek:deepseek workers @ abc1234 vs claude_cli:claude_cli planner, " \
           "deepseek:deepseek workers @ def5678 (4 workers): sealed gain" in md
    assert "workers @ def5678 vs deepseek:deepseek planner, deepseek:deepseek workers @ def5678 (4 workers)" in md
    assert "| planner $ (API spend, or the Claude CLI's usage estimate) |" in md and "(CLI estimate)" not in md
    # the report can be re-rendered from its own json twin when the run directories are elsewhere
    runs = sr.load_runs(dirs)
    (tmp_path / "scaling.json").write_text(json.dumps(runs, indent=1, default=str))
    import subprocess, sys
    out = tmp_path / "again.md"
    subprocess.run([sys.executable, sr.__file__, "--from-json", str(tmp_path / "scaling.json"),
                    "--out", str(out)], check=True, capture_output=True)
    assert out.read_text() == md and not out.with_suffix(".json").exists()


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


def test_run_config_honours_an_explicit_data_dir(tmp_path):
    """`--set run.data_dir=<path>` points a run at a bundle outside the checkout (a clone can read the main
    checkout's data without copying it); without it the dataset name resolves under data/."""
    import run_research as rr
    from genemila import REPO_ROOT
    cfg = rr.build_config(rr.parse_args(["--dataset", "adamson_cf", "--planner-provider", "scripted",
                                         "--worker-provider", "mock", "--set", f"run.data_dir={tmp_path}/bundle"]))
    assert cfg["run"]["data_dir"] == str((tmp_path / "bundle").resolve())
    cfg = rr.build_config(rr.parse_args(["--dataset", "adamson_cf", "--planner-provider", "scripted",
                                         "--worker-provider", "mock"]))
    assert cfg["run"]["data_dir"] == str(REPO_ROOT / "data" / "adamson_cf")


def test_a_different_selection_rule_is_its_own_arm():
    cfg = {"planner": {"provider": "claude_cli", "model": "opus"}, "worker": {"provider": "deepseek", "model": "deepseek-flash"}}
    assert table.run_arm(cfg) == "claude_cli:opus planner, deepseek:deepseek-flash workers"
    assert table.run_arm({**cfg, "experiment": {"selection": "pearson_delta"}}) == table.run_arm(cfg)
    assert table.run_arm({**cfg, "experiment": {"selection": "pearson_delta+r2_top"}}) == \
        "claude_cli:opus planner, deepseek:deepseek-flash workers (selection pearson_delta+r2_top)"
    ctl = {"planner": {"provider": "scripted"}, "worker": {"provider": "mock"}, "experiment": {"selection": "pearson_delta+r2_top"}}
    assert table.run_arm(ctl) == "scripted control (no LLM) (selection pearson_delta+r2_top)"


def test_another_selection_rule_keeps_the_report_on_one_scale(tmp_path):
    import scaling_report as sr
    dirs = [_run_dir(tmp_path, f"w4_r{i}", 4, "claude_cli", "deepseek", 0.08 + 0.01 * i, 1200) for i in range(2)]
    dirs.append(_run_dir(tmp_path, "derule_r0", 4, "claude_cli", "deepseek", 0.06, 1200, rule="pearson_delta+r2_top"))
    dirs.append(_run_dir(tmp_path, "derule_r1", 4, "claude_cli", "deepseek", 0.07, 1200, rule="pearson_delta+r2_top",
                         start_metrics={"pearson_delta": 0.556}))
    runs = {r["dir"]: r for r in sr.load_runs(dirs)}
    assert runs["derule_r0"]["arm"].endswith("(selection pearson_delta+r2_top)")
    # sealed numbers come from the pearson_delta field, not from the combined score
    assert runs["derule_r0"]["values"]["best_sealed"] == pytest.approx(0.56)
    assert runs["derule_r0"]["values"]["gain_sealed"] == pytest.approx(0.06)
    # the visible gain is on the pearson_delta scale when the summary allows it, else blank
    assert runs["derule_r0"]["values"]["gain_visible"] is None
    assert runs["derule_r1"]["values"]["gain_visible"] == pytest.approx(0.61 - 0.556)
    assert runs["w4_r0"]["values"]["gain_visible"] == pytest.approx(0.014 + 0.08)
    md = sr.render(list(runs.values()))
    assert "(second minus first; " in md and " ahead)" in md and "visible gain on the pearson_delta scale" in md


def test_table_reads_the_sealed_score_by_name_and_pools_the_starting_model(tmp_path):
    comp = {f"cellforge_{c}": v for c, v in zip(table.COLUMNS, (0.01, 0.98, 0.95, 0.2, 0.9, 0.8))}
    base = {f"cellforge_{c}": v for c, v in zip(table.COLUMNS, (0.02, 0.97, 0.93, 0.3, 0.85, 0.7))}
    runs = []
    for name, rule in (("plain_r0", None), ("derule_r0", "pearson_delta+r2_top")):
        run = tmp_path / name
        run.mkdir()
        best_row = {"experiment_id": "EXP_0100", "kind": "new_feature", "query_only_score": 0.5,
                    "comparable": {"val1": comp, "val2": comp}}
        start_row = {"experiment_id": "EXP_0003", "kind": "baseline", "query_only_score": 0.4,
                     "comparable": {"val1": base, "val2": base}}
        cfg = {"run": {"workers": 4, "data_dir": str(tmp_path / "nodata")},
               "planner": {"provider": "claude_cli", "model": "opus"}, "worker": {"provider": "deepseek", "model": "deepseek-flash"}}
        if rule:
            best_row.update(query_only_score=0.7, query_only_pearson_delta=0.48)
            start_row.update(query_only_score=0.6, query_only_pearson_delta=0.4)
            cfg["experiment"] = {"selection": rule}
        summary = {"run_id": name, "dataset": "adamson_cf", "split_id": "split_x", "workers": 4, "duration_s": 1200,
                   "best": {"features": ["a"], "model": "ridge"}, "baseline": {"description": "OLS"},
                   "generalization_query_only": [best_row, start_row]}
        (run / "summary.json").write_text(json.dumps(summary))
        (run / "config.json").write_text(json.dumps(cfg))
        runs.append(run)
    t = table.build(runs, tmp_path / "no_paper.json", part="val2")
    by_arm = {b["arm"]: b for b in t["blocks"]}
    derule = next(b for a, b in by_arm.items() if "(selection pearson_delta+r2_top)" in a)
    plain = next(b for a, b in by_arm.items() if "(selection" not in a)
    assert derule["best_primary"] == [0.48] and plain["best_primary"] == [0.5]
    # the starting model is pooled over both runs, not taken from whichever block comes first
    assert t["start_all"]["adamson_cf|split_x"]["mse"]["n"] == 2
    md = table.render(t)
    assert "| Gene-Mila starting model | ours | 0.0200 ± 0.0000" in md  # pooled over both runs (n=2), rank mark follows


def test_continued_runs_are_named_after_their_source_and_are_not_controls():
    import scaling_report as sr
    ctl = {"run": {"workers": 4, "continue_from": "/x/runs/newcode_opus_w4_r0"}, "planner": {"provider": "scripted"},
           "worker": {"provider": "mock"}}
    assert table.run_arm(ctl) == "no-LLM continuation of newcode_opus_w4_r0"
    assert not sr._is_control(table.run_arm(ctl))  # never the equal-time reference, never "a control against the agents"
    llm = {"run": {"continue_from": "runs/a"}, "planner": {"provider": "claude_cli", "model": "opus"},
           "worker": {"provider": "deepseek", "model": "deepseek-flash"}}
    assert table.run_arm(llm) == "claude_cli:opus planner, deepseek:deepseek-flash workers (continued from a)"


def test_continued_runs_stay_out_of_the_comparisons(tmp_path):
    import scaling_report as sr
    dirs = [_run_dir(tmp_path, f"agents_w4_r{i}", 4, "claude_cli", "deepseek", 0.08 + 0.01 * i, 1200) for i in range(2)]
    dirs.append(_run_dir(tmp_path, "ctl_r0", 4, "scripted", "mock", 0.034, 126))
    dirs.append(_run_dir(tmp_path, "cont_r0", 4, "scripted", "mock", 0.079, 1200, continue_from="/x/runs/agents_w4_r0"))
    runs = sr.load_runs(dirs)
    assert {r["arm"] for r in runs if r["dir"] == "cont_r0"} == {"no-LLM continuation of agents_w4_r0"}  # one code version: no suffix
    md = sr.render(runs)
    assert "no-LLM continuation of agents_w4_r0, 4 workers (n=1)" in md  # in the table ...
    noise = md.split("## Is the ordering real?")[1]
    vs = [l for l in noise.splitlines() if " vs " in l or "against the agent arms" in l]
    assert vs and not any("continuation" in l for l in vs)  # ... but in no comparison, on either side
    assert ("- cont_r0 (no-LLM continuation of agents_w4_r0, 4 workers): sealed gain 0.0790 against 0.0800 "
            "for the run it continued (agents_w4_r0); its model is that campaign's") in noise
