"""tools/sealed_reading.py: the pre-specified sealed readings of docs/NORMAN_PLAN.md section 5 over finished runs.
It compares only each run's selected model with its additive baseline and with its starting model (a continued run's
or a fresh run's) and, for two runs, the selected model of the run with external knowledge with that of the run
without, in either order given, or with --versus the first run's with the second's; its answers are the oracle's own
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

    def factory(bundle=None, alpha_grid=(1.0, 100.0), score_additive=False, continue_from=None, start_score=0.5,
                start_exists=False):
        bundle = bundle or bundles[0]
        cfg = make_cfg(tmp_path)
        cfg["run"]["data_dir"] = str(bundle)
        if continue_from is not None:
            cfg["run"]["continue_from"] = str(continue_from)
        lab = Lab(cfg, tmp_path / f"run{len(made)}", bundle, repo=code_repo)
        made.append(lab)
        lab.record_analytic_baselines()
        if continue_from is not None:  # the previous run's best, queued as this run's first experiment and fitted
            if start_exists:  # an identical experiment already in the run: the warm start is queued as its duplicate
                eid0, status = lab.queue(_ridge_spec("the previous run's model, already in this run"))
                assert status == "queued"
            info = lab.warm_start(Path(continue_from))
            sid = eid0 if start_exists else info["start_experiment"]
            assert info["start_status"] == ("duplicate" if start_exists else "queued")
            rec = lab.db.get_experiment(sid)
            out = lab.artifacts / sid
            run(ExperimentSpec.from_record(rec).run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
            ev = lab.evaluate_artifact(out / "predictions.npz")
            lab.db.update_experiment(sid, status="completed", primary_score=start_score, best_alpha=ev["best_alpha"],
                                     artifact_dir=str(out), val_metrics_json=ev["metrics"])
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


def _start_id(lab) -> str:
    return lab.db.query("SELECT experiment_id FROM experiments WHERE hypothesis_group LIKE 'warm_start_%'")[0][
        "experiment_id"]


def test_a_continued_run_is_read_against_its_starting_model(make_lab):
    """N4 (NORMAN_PLAN.md section 8): a run that continued another is read against its additive baseline and against
    its starting model, the second by the oracle's paired query like every other comparison; a run that continues
    nothing is read against its fresh start instead."""
    prev, _ = make_lab()
    lab, eid = make_lab(alpha_grid=(1000.0,), continue_from=prev.run_dir)
    start = _start_id(lab)
    before = _sealed_events(lab)
    r = sealed_reading.read_run(lab)
    c = r["continuation"]
    assert c["from"] == prev.run_dir.name and c["start"]["experiment_id"] == start and c["note"] is None
    perts = lab.oracle.perts
    pa, oa = lab._predict(lab.db.get_experiment(eid), perts)
    pb, ob = lab._predict(lab.db.get_experiment(start), perts)
    own = QueryOracle(lab.data_dir, max_queries=2).query_paired(eid, pa, oa, start, pb, ob, lab.control_mean,
                                                                metric="pearson_delta")
    assert c["sealed"]["paired"] == own["paired"] and c["sealed"]["b"]["matches_stored"] is None
    assert c["visible"] == lab.compare_visible(eid, start, metric="pearson_delta")
    assert _sealed_events(lab) == before
    assert sealed_reading.read_run(prev)["continuation"]["kind"] == "fresh" and c["kind"] == "warm_start"
    rep = json.loads(json.dumps(sealed_reading.analyse([lab.run_dir]), default=float))
    assert rep["protocol"]["sealed_scorings"] == 4
    assert f"{lab.run_dir.name}:{start}" in rep["protocol"]["first_sealed_scorings"]
    md = sealed_reading.render(rep)
    assert "selected model against its starting model" in md and "| selected | start |" in md
    assert "against its starting model, sealed pooled: selected minus start" in md.split("## Reading", 1)[1]


def test_a_continued_run_that_kept_its_start_has_nothing_to_compare(make_lab):
    prev, _ = make_lab()
    lab, _ = make_lab(alpha_grid=(1000.0,), continue_from=prev.run_dir, start_score=100.0)
    c = sealed_reading.read_run(lab)["continuation"]
    assert c["sealed"] is None and c["note"] == "the run selected its starting model: its search added nothing it kept"
    rep = sealed_reading.analyse([lab.run_dir])
    assert rep["protocol"]["sealed_scorings"] == 2   # the selected start against the additive baseline only
    assert "its search added nothing it kept" in sealed_reading.render(rep)


def test_a_start_queued_as_a_duplicate_is_the_experiment_it_duplicates(make_lab):
    """When the run already holds the starting configuration (a model baseline, say), Lab.warm_start queues its start
    as a duplicate; the reading follows duplicate_of to the experiment that ran."""
    prev, _ = make_lab()
    lab, eid = make_lab(alpha_grid=(1000.0,), continue_from=prev.run_dir, start_exists=True)
    warm = json.loads((lab.run_dir / "warm_start.json").read_text())
    dup = lab.db.get_experiment(warm["start_experiment"])
    assert dup["status"] == "duplicate"
    c = sealed_reading.read_run(lab)["continuation"]
    assert c["start"]["experiment_id"] == dup["duplicate_of"] != eid and c["sealed"] is not None


def test_a_start_that_did_not_run_is_named_by_its_status(make_lab):
    prev, _ = make_lab()
    lab, _ = make_lab(alpha_grid=(1000.0,), continue_from=prev.run_dir)
    sid = json.loads((lab.run_dir / "warm_start.json").read_text())["start_experiment"]
    lab.db.update_experiment(sid, status="failed")
    c = sealed_reading.read_run(lab)["continuation"]
    assert c["sealed"] is None
    assert c["note"] == f"the run's starting model {sid} ended with status failed: nothing to compare"
    assert "is not available" in sealed_reading.render(sealed_reading.analyse([lab.run_dir]))


def _queue_and_fit(lab, spec, group=None, score=0.4):
    """Queue a spec as an experiment of the run, fit it and record it completed with the given visible score."""
    spec.hyperparameters["alpha_grid"] = [10.0 if group == "baseline_ridge_additive" else 3.0]  # no duplicate
    if group:
        spec.kind, spec.hypothesis_group = "baseline", group
    eid, status = lab.queue(spec)
    assert status == "queued"
    rec = lab.db.get_experiment(eid)
    out = lab.artifacts / eid
    run(ExperimentSpec.from_record(rec).run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
    ev = lab.evaluate_artifact(out / "predictions.npz")
    lab.db.update_experiment(eid, status="completed", primary_score=score, best_alpha=ev["best_alpha"],
                             artifact_dir=str(out), val_metrics_json=ev["metrics"])
    return eid


def test_a_fresh_run_is_read_against_its_built_in_additive_start(make_lab):
    """B2 of docs/PLAN_AFTER_N4.md: a fresh run on a bundle with pairs started from baseline_ridge_additive, so its
    search is read against that model, even when another baseline scores higher on visible data (the reported start,
    Lab.best_baseline, leaves the built-in start out)."""
    lab, eid = make_lab()
    start = _queue_and_fit(lab, _ridge_spec("ridge on the built-ins plus additive_response"),
                           group="baseline_ridge_additive", score=0.3)
    assert lab.best_baseline()["experiment_id"] != start
    before = _sealed_events(lab)
    c = sealed_reading.read_run(lab)["continuation"]
    assert c["kind"] == "fresh" and c["from"] is None and c["start"]["experiment_id"] == start
    perts = lab.oracle.perts
    pa, oa = lab._predict(lab.db.get_experiment(eid), perts)
    pb, ob = lab._predict(lab.db.get_experiment(start), perts)
    own = QueryOracle(lab.data_dir, max_queries=2).query_paired(eid, pa, oa, start, pb, ob, lab.control_mean,
                                                                metric="pearson_delta")
    assert c["sealed"]["paired"] == own["paired"]
    assert c["visible"] == lab.compare_visible(eid, start, metric="pearson_delta")
    assert _sealed_events(lab) == before
    md = sealed_reading.render(json.loads(json.dumps(sealed_reading.analyse([lab.run_dir]), default=float)))
    assert "The run started fresh; its starting model, the built-in additive start" in md
    assert "against its starting model, sealed pooled: selected minus start" in md.split("## Reading", 1)[1]


def test_a_fresh_run_without_the_built_in_is_read_against_its_reported_start(make_lab):
    """B3: a fresh Adamson-like run is read against the starting model it reports (its best baseline); when that is
    the additive baseline, the comparison already shown is the one, and no second section repeats it."""
    lab, eid = make_lab()
    other = _queue_and_fit(lab, _ridge_spec("a model baseline"), group="baseline_ridge", score=0.99)
    assert lab.best_baseline()["experiment_id"] == other
    c = sealed_reading.read_run(lab)["continuation"]
    assert c["kind"] == "fresh" and c["start"]["experiment_id"] == other and c["sealed"] is not None
    lab.db.update_experiment(_additive_id(lab), primary_score=1.5)   # still below the selected model's
    assert lab.best_baseline()["experiment_id"] == _additive_id(lab)
    c = sealed_reading.read_run(lab)["continuation"]
    assert c["sealed"] is None and c["is_additive"] is True
    rep = json.loads(json.dumps(sealed_reading.analyse([lab.run_dir]), default=float))
    assert rep["protocol"]["sealed_scorings"] == 2
    md = sealed_reading.render(rep)
    assert "selected model against its starting model" not in md and "against its starting model" not in md


def test_versus_reads_the_first_run_s_selected_model_minus_the_second_s(make_lab, tmp_path):
    """B3's agents against the no-LLM control with the same screen: --versus takes the runs in the order given,
    requires the same external knowledge, and shows the visible comparison across the two runs beside the sealed."""
    bundle = make_pair_bundle(tmp_path / "bundle")
    (bundle / "knowledge" / "toy_screen.json").write_text("{}")
    first, e1 = make_lab(bundle=bundle, alpha_grid=(1000.0,))
    second, e2 = make_lab(bundle=bundle)
    before = [_sealed_events(first), _sealed_events(second)]
    rep = json.loads(json.dumps(sealed_reading.analyse([first.run_dir, second.run_dir], versus=True), default=float))
    p = rep["pair"]
    assert p["mode"] == "versus" and (p["a"]["experiment_id"], p["b"]["experiment_id"]) == (e1, e2)
    assert p["a"]["external_knowledge"] == p["b"]["external_knowledge"] == ["toy_screen"]
    perts = first.oracle.perts
    pa, oa = first._predict(first.db.get_experiment(e1), perts)
    pb, ob = second._predict(second.db.get_experiment(e2), perts)
    own = QueryOracle(first.data_dir, max_queries=2).query_paired(e1, pa, oa, e2, pb, ob, first.control_mean,
                                                                  metric="pearson_delta")
    assert p["sealed"]["paired"] == json.loads(json.dumps(own["paired"]))
    vis = first.compare_visible(e1, e1)   # the same run's folds: the cross-run comparison matches the in-run one
    assert p["visible"]["same_folds"] is True and p["visible"]["n"] == vis["n"]
    assert [_sealed_events(first), _sealed_events(second)] == before
    flipped = sealed_reading.analyse([second.run_dir, first.run_dir], versus=True)["pair"]["sealed"]["paired"]
    assert flipped["mean_diff"] == pytest.approx(-p["sealed"]["paired"]["mean_diff"])
    md = sealed_reading.render(rep)
    assert "(A) against" in md and "| A | B |" in md and "No expected direction was fixed" in md
    assert "Expected direction" not in md.split("\n\n", 2)[1]
    with pytest.raises(ValueError, match="--versus compares two runs"):
        sealed_reading.analyse([first.run_dir], versus=True)


def test_versus_refuses_runs_with_different_knowledge_or_the_same_run(make_lab, tmp_path):
    bundle = make_pair_bundle(tmp_path / "bundle")
    without, _ = make_lab(bundle=bundle)
    (bundle / "knowledge" / "toy_screen.json").write_text("{}")
    with_screen, _ = make_lab(bundle=bundle, alpha_grid=(1000.0,))
    with pytest.raises(ValueError, match="same external knowledge"):
        sealed_reading.read_versus(with_screen, without)
    with pytest.raises(ValueError, match="the same run twice"):
        sealed_reading.read_versus(without, without)


def test_the_gene_clustering_ratio_is_the_overlap_robust_se_on_visible_labels(make_lab, monkeypatch):
    """docs/PLAN_AFTER_N4.md (amendment of 20:30 UTC): the arm reading inflates a run's sealed SE by how much shared
    genes widen the paired SE on the visible validation perturbations, the overlap-robust variance over the plain
    one; the leave-one-gene-out jackknife first specified is kept beside, reported only."""
    import numpy as np
    from genemila.benchmark.evaluator import metric_values
    lab, eid = make_lab()
    add = _additive_id(lab)
    cr = sealed_reading.read_run(lab)["cluster_ratio"]
    sa, _ = lab.score_visible(lab.visible_predictions(eid)[0], None)
    sb, _ = lab.score_visible(lab.visible_predictions(add)[0], None)
    a, b = metric_values(sa, "pearson_delta"), metric_values(sb, "pearson_delta")
    perts = list(lab._val1.perts)
    assert any(len(lab._targets[p]) > 1 for p in perts)
    e = np.array([a[p] - b[p] for p in perts])
    e -= e.mean()
    share = np.array([[bool(set(lab._targets[p]) & set(lab._targets[q])) for q in perts] for p in perts])
    assert cr["estimator"] == "overlap-robust"
    assert cr["ratio"] == pytest.approx(np.sqrt(max(0.0, e @ share @ e) / (e @ e)))
    assert cr["n_overlapping_pairs"] == int(share.sum()) - len(perts) and cr["jackknife_ratio"] is not None
    monkeypatch.setattr(lab, "_targets", {})   # every perturbation its own gene: the plain SE
    rec = lab.db.get_experiment
    assert sealed_reading._cluster_ratio(lab, rec(eid), lab, rec(add))["ratio"] == pytest.approx(1.0)


class _StubLab:
    """Just enough of a Lab for _cluster_ratio: given per-perturbation differences and targets."""
    selection = "pearson_delta"

    def __init__(self, diffs, targets):
        self._val1 = type("V", (), {"perts": list(diffs)})()
        self._targets, self._diffs = targets, diffs

    def visible_predictions(self, eid):
        return eid, None

    def score_visible(self, which, cv):
        sign = 1.0 if which == "a" else 0.0
        return {p: {"pearson_delta": sign * d} for p, d in self._diffs.items()}, {}


def test_independent_pairs_give_a_ratio_of_one_where_the_jackknife_gives_more():
    """The review's null case: pairs that share no gene, with independent differences. The overlap-robust ratio is
    exactly 1; the leave-one-gene-out jackknife is sqrt((2n-1)/(n-1)) whatever the data, counting each pair twice."""
    import numpy as np
    rng = np.random.default_rng(0)
    n = 30
    diffs = {f"G{2 * i}+G{2 * i + 1}": float(x) for i, x in enumerate(rng.normal(size=n))}
    targets = {p: p.split("+") for p in diffs}
    lab = _StubLab(diffs, targets)
    cr = sealed_reading._cluster_ratio(lab, {"experiment_id": "a"}, lab, {"experiment_id": "b"})
    assert cr["ratio"] == pytest.approx(1.0) and cr["n_overlapping_pairs"] == 0
    assert cr["jackknife_ratio"] == pytest.approx(np.sqrt((2 * n - 1) / (n - 1)))
    shared = {f"A+G{i}": float(x) for i, x in enumerate(np.full(n, 1.0) + rng.normal(scale=0.01, size=n))}
    shared.update({f"B+H{i}": float(x) for i, x in enumerate(np.full(n, -1.0) + rng.normal(scale=0.01, size=n))})
    lab = _StubLab(shared, {p: p.split("+") for p in shared})
    assert sealed_reading._cluster_ratio(lab, {"experiment_id": "a"}, lab, {"experiment_id": "b"})["ratio"] > 5
