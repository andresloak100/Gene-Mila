"""The offline selection-rule replay reproduces the lab's own selection and the oracle's sealed numbers."""

import json

import numpy as np
import pytest

from genemila.pipeline import run
from genemila.spec import ExperimentSpec
from genemila.worker import prune_predictions
from tools.replay_selection import main, render, replay_run


def test_replay_matches_the_lab_and_the_oracle(lab_factory, tmp_path):
    lab = lab_factory(experiment__cv_folds=3)
    lab.record_analytic_baselines()
    for feats, grid in [(["control_mean", "mean_response", "is_target"], [1.0, 1000.0]),
                        (["control_mean", "is_target"], [0.1, 10.0])]:
        eid, status = lab.queue(ExperimentSpec(hypothesis=f"ridge on {len(feats)} builtins",
                                               scientific_rationale="a reference model on the built-in features",
                                               feature_set=feats, hyperparameters={"alpha_grid": grid}))
        assert status == "queued"
        spec = ExperimentSpec.from_record(lab.db.get_experiment(eid))
        out = lab.artifacts / eid
        run(spec.run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
        ev = lab.evaluate_artifact(out / "predictions.npz")
        prune_predictions(out / "predictions.npz", ev["alpha_index"])  # as the worker does: one alpha survives
        prune_predictions(out / "cv.npz", ev["alpha_index"])
        lab.db.update_experiment(eid, status="completed", artifact_dir=str(out), best_alpha=ev["best_alpha"],
                                 primary_score=ev["metrics"]["primary"], val_metrics_json=ev["metrics"])
    best = lab.db.query("SELECT * FROM experiments WHERE status='completed' AND kind NOT IN ('baseline', 'ensemble') "
                        "ORDER BY primary_score DESC LIMIT 1")[0]
    q = lab.query_only(best["experiment_id"])["metrics"]
    (lab.run_dir / "config.json").write_text(json.dumps(lab.cfg))
    rep = replay_run(lab.run_dir)
    assert rep["n_candidates"] == 2 and rep["cross_validated"] and not rep["skipped"]
    pick = rep["rules"]["pearson_delta"]
    assert pick["experiment_id"] == best["experiment_id"]
    assert pick["visible_score"] == pytest.approx(best["primary_score"], abs=1e-6)
    assert pick["sealed"]["pearson_delta"] == pytest.approx(q["pearson_delta"], abs=1e-6)
    assert pick["sealed"]["cellforge_r2_de"] == pytest.approx(q["cellforge_r2_de"], abs=1e-6)
    assert lab.oracle.used == 1, "the replay must not query the oracle"
    de = rep["rules"]["pearson_delta+r2_top"]
    assert de["visible_score"] == de["visible"]["pearson_delta+r2_top"] and de["sealed"]["r2_top"] is not None
    md = render([rep, rep])
    assert best["experiment_id"] in md and "## Across runs" in md and "pearson_delta+r2_top" in md
    out = tmp_path / "replay.md"
    assert main(["--runs", str(lab.run_dir), "--out", str(out)]) == 0
    assert out.exists() and json.loads(out.with_suffix(".json").read_text())[0]["run_id"] == rep["run_id"]
