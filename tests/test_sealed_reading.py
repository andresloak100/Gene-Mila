"""tools/sealed_reading.py: the pre-specified sealed readings of docs/NORMAN_PLAN.md section 5 over finished runs.
It compares only each run's selected model with its additive baseline and, for two runs, the selected model of the
run with external knowledge with that of the run without, in either order given; its answers are the oracle's own
paired queries; it names every model it scores on the sealed set for the first time; it never writes into a run."""

import json
import sys
from pathlib import Path

import pytest

from genemila.benchmark.oracle import QueryOracle
from genemila.pipeline import run
from genemila.spec import ExperimentSpec

from test_norman_lab import _ridge_spec, make_pair_bundle

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sealed_reading  # noqa: E402


@pytest.fixture(scope="module")
def bundles(tmp_path_factory):
    root = tmp_path_factory.mktemp("sealed_reading")
    return make_pair_bundle(root / "norman_toy"), make_pair_bundle(root / "norman_other", seed=1)


@pytest.fixture
def make_lab(tmp_path, bundles, code_repo):
    from conftest import make_cfg
    from genemila.lab import Lab
    made = []

    def factory(bundle=None, alpha_grid=(1.0, 100.0), score_additive=False):
        bundle = bundle or bundles[0]
        cfg = make_cfg(tmp_path)
        cfg["run"]["data_dir"] = str(bundle)
        lab = Lab(cfg, tmp_path / f"run{len(made)}", bundle, repo=code_repo)
        made.append(lab)
        lab.record_analytic_baselines()
        spec = _ridge_spec()
        spec.hyperparameters["alpha_grid"] = list(alpha_grid)
        eid, status = lab.queue(spec)
        assert status == "queued"
        rec = lab.db.get_experiment(eid)
        out = lab.artifacts / eid
        run(ExperimentSpec.from_record(rec).run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
        ev = lab.evaluate_artifact(out / "predictions.npz")
        # selected by visible score above every baseline, as a run's selected model is
        lab.db.update_experiment(eid, status="completed", primary_score=1.0 + len(made), best_alpha=ev["best_alpha"],
                                 artifact_dir=str(out), val_metrics_json=ev["metrics"])
        lab.query_only(eid)  # scored on the sealed set when its run ended, as a run's finalists are
        if score_additive:   # as when the additive baseline is the run's best baseline
            lab.query_only(_additive_id(lab))
        return lab, eid
    yield factory
    for lab in made:
        lab.stop_event.set()
        lab.kill_event.set()
        lab.close()


def _additive_id(lab) -> str:
    return lab.db.query("SELECT experiment_id FROM experiments WHERE hypothesis_group='baseline_additive'")[0][
        "experiment_id"]


def _sealed_events(lab) -> int:
    return lab.db.query("SELECT COUNT(*) AS n FROM events WHERE kind IN ('query_only', 'query_paired')")[0]["n"]


def test_run_reading_is_the_oracle_s_paired_query_and_writes_nothing(make_lab, bundles):
    lab, eid = make_lab(score_additive=True)
    add = _additive_id(lab)
    before = _sealed_events(lab)
    r = sealed_reading.read_run(lab)
    assert r["selected"]["experiment_id"] == eid and r["additive"]["experiment_id"] == add
    perts = lab.oracle.perts
    pa, oa = lab._predict(lab.db.get_experiment(eid), perts)
    pb, ob = lab._predict(lab.db.get_experiment(add), perts)
    own = QueryOracle(bundles[0], max_queries=2).query_paired(eid, pa, oa, add, pb, ob, lab.control_mean,
                                                              metric="pearson_delta")
    assert r["sealed"]["paired"] == own["paired"] and r["sealed"]["a"]["metrics"] == own["a"]["metrics"]
    assert "by_category" in r["sealed"]["paired"] and "by_category" in r["sealed"]["a"]["metrics"]
    assert r["sealed"]["a"]["matches_stored"] is True and r["sealed"]["b"]["matches_stored"] is True
    assert r["run_queries"] == {"used": 2, "cap": lab.oracle.max_queries} and r["base_commit"] == lab.base_commit
    assert r["visible"] == lab.compare_visible(eid, add, metric="pearson_delta")
    assert _sealed_events(lab) == before and not (lab.run_dir / "query_paired").exists()


def test_two_runs_compare_with_the_screen_minus_without_in_either_order(make_lab, tmp_path):
    """The run that records external knowledge is the minuend whatever the order of --runs; the additive baselines,
    never scored when their runs ended here, are named as first sealed scorings, and the Reading reads every
    category of at least MIN_READ sealed perturbations by the rule."""
    bundle = make_pair_bundle(tmp_path / "bundle")
    without, e1 = make_lab(bundle=bundle)
    (bundle / "knowledge" / "toy_screen.json").write_text("{}")   # added after the build: the next run is its own arm
    with_screen, e2 = make_lab(bundle=bundle, alpha_grid=(1000.0,))
    assert with_screen.cfg["run"]["external_knowledge"] == ["toy_screen"]
    assert not without.cfg["run"].get("external_knowledge")
    before = [_sealed_events(without), _sealed_events(with_screen)]
    rep = sealed_reading.analyse([without.run_dir, with_screen.run_dir])
    assert sealed_reading.analyse([with_screen.run_dir, without.run_dir])["pair"] == rep["pair"]
    assert rep["protocol"]["sealed_scorings"] == 6
    p = rep["pair"]
    assert (p["a"]["run"], p["a"]["experiment_id"], p["a"]["external_knowledge"]) == (
        with_screen.run_dir.name, e2, ["toy_screen"])
    assert (p["b"]["run"], p["b"]["experiment_id"]) == (without.run_dir.name, e1) and p["same_code"] is True
    perts = without.oracle.perts
    pa, oa = with_screen._predict(with_screen.db.get_experiment(e2), perts)
    pb, ob = without._predict(without.db.get_experiment(e1), perts)
    own = QueryOracle(without.data_dir, max_queries=2).query_paired(e2, pa, oa, e1, pb, ob, without.control_mean,
                                                                    metric="pearson_delta")
    assert p["sealed"]["paired"] == json.loads(json.dumps(own["paired"]))
    assert [_sealed_events(without), _sealed_events(with_screen)] == before
    first = rep["protocol"]["first_sealed_scorings"]
    assert first == sorted([f"{without.run_dir.name}:{_additive_id(without)}",
                            f"{with_screen.run_dir.name}:{_additive_id(with_screen)}"])
    md = sealed_reading.render(rep)
    assert md.count("\n## ") == 4 and "| sealed, pooled |" in md and "with screen" in md and "## Reading" in md
    assert "scored here for the first time" in md and "No stored sealed score to check" in md
    assert "every compared model was already scored" not in md
    reading = md.split("## Reading", 1)[1]
    for cat, pc in p["sealed"]["paired"]["by_category"].items():
        assert f"{cat} (n {pc['n']})" in reading or f"{cat} with screen minus without" in reading
    out = tmp_path / "reading.md"
    assert sealed_reading.main(["--runs", str(with_screen.run_dir), str(without.run_dir), "--out", str(out)]) == 0
    again = tmp_path / "again.md"
    sealed_reading.main(["--from-json", str(out.with_suffix(".json")), "--out", str(again)])
    assert again.read_text() == out.read_text()


def test_two_runs_without_external_knowledge_are_refused(make_lab):
    first, _ = make_lab()
    second, _ = make_lab(alpha_grid=(1000.0,))
    with pytest.raises(ValueError, match="exactly one of the two runs"):
        sealed_reading.read_pair(first, second)


def test_a_run_whose_additive_baseline_was_scored_is_not_a_first_scoring(make_lab):
    lab, _ = make_lab(score_additive=True)
    rep = sealed_reading.analyse([lab.run_dir])
    assert rep["protocol"]["first_sealed_scorings"] == [] and rep["pair"] is None
    md = sealed_reading.render(rep)
    assert "every compared model was already scored on the sealed set" in md and "Expected direction" not in md


def test_runs_on_another_split_are_refused(make_lab, bundles):
    first, _ = make_lab()
    other, _ = make_lab(bundle=bundles[1])
    assert first.split_id != other.split_id
    with pytest.raises(ValueError, match="differ in"):
        sealed_reading.read_pair(first, other)


def test_small_categories_are_reported_not_read():
    p = {"n": 8, "mean_diff": 0.2, "se": 0.01, "wins_a": 8, "wins_b": 0, "ties": 0, "verdict": "a"}
    assert sealed_reading._verdict(p, "x", "y", p["n"]) == "reported, not read"
    assert sealed_reading._verdict({**p, "n": 12}, "x", "y", 12) == "x better"
    assert sealed_reading._verdict({"n": 2}, "x", "y", 2) == "too few to report"


def test_a_difference_that_rounds_to_zero_still_shows():
    assert sealed_reading._diff({"mean_diff": 0.00031, "se": 0.00012}) == "+0.00031 ± 0.00012"
    assert sealed_reading._diff({"mean_diff": 0.012, "se": 0.004}) == "+0.012 ± 0.004"
