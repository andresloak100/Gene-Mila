"""The offline selection-rule replay works on visible data only, reproduces the lab's own numbers, and never
touches the sealed labels or the oracle."""

import json
from pathlib import Path

import numpy as np
import pytest

import tools.replay_selection as replay
from genemila.pipeline import run
from genemila.spec import ExperimentSpec
from genemila.worker import prune_predictions


def test_replay_never_reads_the_sealed_labels():
    src = Path(replay.__file__).read_text()
    assert "val2" not in src and "oracle" not in src.lower().replace("no oracle", "")


def test_replay_matches_the_lab_on_both_visible_parts(lab_factory, tmp_path):
    lab = lab_factory(experiment__cv_folds=3)
    lab.record_analytic_baselines()
    recs = []
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
        recs.append(lab.db.get_experiment(eid))
    (lab.run_dir / "config.json").write_text(json.dumps(lab.cfg))
    rep = replay.replay_run(lab.run_dir)
    assert rep["n_candidates"] == 2 and rep["skipped"] == {"no_artifact": 0, "no_oof": 0}
    by_id = {r["experiment_id"]: r["val_metrics_json"] for r in recs}
    # select on validation, score out of fold: the pick is the best validation pearson_delta, scored by its
    # recorded out-of-fold value
    sel_val1 = rep["picks"][replay.DIRECTIONS[1][0]]["pearson_delta"]
    want = max(by_id, key=lambda k: by_id[k]["pearson_delta"])
    assert sel_val1["experiment_id"] == want
    assert sel_val1["selection_score"] == pytest.approx(by_id[want]["pearson_delta"], abs=1e-6)
    assert sel_val1["scored"]["pearson_delta"] == pytest.approx(by_id[want]["pearson_delta_cv"], abs=1e-6)
    # select out of fold, score on validation: CellForge's DE metrics match what the lab recorded for val1
    sel_oof = rep["picks"][replay.DIRECTIONS[0][0]]["pearson_delta"]
    want = max(by_id, key=lambda k: by_id[k]["pearson_delta_cv"])
    assert sel_oof["experiment_id"] == want
    assert sel_oof["scored"]["cellforge_r2_de"] == pytest.approx(by_id[want]["cellforge_r2_de"], abs=1e-6)
    assert sel_oof["scored"]["r2_top"] == pytest.approx(by_id[want]["r2_top"], abs=1e-6)
    de = rep["picks"][replay.DIRECTIONS[0][0]]["pearson_delta+r2_top"]
    assert de and de["scored"]["mse_top"] is not None
    assert lab.oracle.used == 0, "the replay must not query the oracle"
    md = replay.render([rep, rep])
    assert want in md and "## Across the 2 usable runs" in md and "pearson_delta+r2_top" in md
    out = tmp_path / "replay.md"
    assert replay.main(["--runs", str(lab.run_dir), "--out", str(out)]) == 0
    assert json.loads(out.with_suffix(".json").read_text())[0]["run_id"] == rep["run_id"]
    # a run without out-of-fold predictions has one visible part and is skipped, not scored
    for r in recs:
        (Path(r["artifact_dir"]) / "cv.npz").unlink()
    rep2 = replay.replay_run(lab.run_dir)
    assert rep2["n_candidates"] == 0 and rep2["skipped"]["no_oof"] == 2 and "Skipped" in replay.render([rep2])
