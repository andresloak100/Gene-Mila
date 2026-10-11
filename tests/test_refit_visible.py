"""tools/refit_visible.py: the pre-specified refit on all visible labels reproduces the lab's own fits, scores
each refit exactly once through its own oracle, leaves the run untouched, and re-renders from its JSON twin."""

import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import refit_visible as rv  # noqa: E402

from genemila.benchmark.oracle import QueryOracle  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402


def test_source_never_names_the_sealed_labels():
    src = (ROOT / "tools" / "refit_visible.py").read_text()
    for word in ("val2", "query_only_pearson", "private/"):
        assert word not in src, word
    # the oracle is the one allowed reference: imported and called, never its label files
    assert "QueryOracle" in src and "labels_path" not in src


def test_augmented_context_adds_the_visible_validation_labels(lab_factory, tmp_path):
    lab = lab_factory()
    public = FeatureContext(lab.public_dir)
    ctx = rv.training_context(lab, tmp_path / "cache")
    n_train, n_val = len(lab._train.perts), len(lab._val1.perts)
    assert len(ctx.train_perts) == n_train + n_val and ctx.train_perts[:n_train] == public.train_perts
    assert ctx.train_signature != public.train_signature and ctx._train_delta.shape == (n_train + n_val, ctx.n_genes)
    names, d = ctx.train_delta(exclude=lab._val1.perts[0])
    assert lab._val1.perts[0] not in names and d.shape[0] == n_train + n_val - 1
    i = ctx._train_pos[lab._val1.perts[1]]
    assert np.allclose(ctx._train_delta[i], lab._val1.means[1] - lab.control_mean)
    # the public context is untouched, and the training-only context is the public one
    assert len(public.train_perts) == n_train and public._train_delta.shape[0] == n_train
    assert rv.training_context(lab, tmp_path / "c2", augment=False).train_signature == public.train_signature
    with pytest.raises(ValueError):
        public.with_extra_train([public.train_perts[0]], np.zeros((1, public.n_genes)))
    with pytest.raises(ValueError):
        public.with_extra_train(["x"], np.zeros((2, public.n_genes)))


def test_seed_repeats_recompute_the_features_under_every_seed(lab_factory, tmp_path):
    """--seed-repeats is real: a feature that draws random numbers is recomputed under each seed and the
    multi-seed prediction is the mean of the single-seed ones; deterministic features make every seed agree."""
    from genemila.features.api import REGISTRY, Feature, register

    @register
    class Noisy(Feature):
        name = "refit_test_noisy"
        description = "draws random numbers (test fixture)"
        rationale = "tests that seeds are real"
        dim = 1

        def compute(self, ctx, perts, params):
            return np.random.rand(len(perts), ctx.n_genes, 1)

    try:
        ctx = rv.training_context(lab_factory(), tmp_path / "cache")
        out = [p for p in ctx.perts if p not in set(ctx.train_perts)][:4]

        def noisy(seeds):
            return rv.fit_predict(ctx, ["control_mean", "refit_test_noisy"], {}, "ridge", 1.0, seeds, None, out)

        a, b, ab = noisy([3]), noisy([4]), noisy([3, 4])
        assert a.shape == (4, ctx.n_genes) and not np.allclose(a, b)
        assert np.allclose(ab, (a + b) / 2) and np.allclose(noisy([3]), a)

        def fixed(seeds):
            return rv.fit_predict(ctx, ["control_mean", "is_target"], {}, "ridge", 1.0, seeds, tmp_path / "f", out)

        assert np.allclose(fixed([3, 4, 5]), fixed([3]))
    finally:
        REGISTRY.pop("refit_test_noisy", None)


def test_analytic_baselines_are_refit_by_their_own_rule(lab_factory, tmp_path, code_repo):
    """An analytic baseline is refit as itself: the additive baseline of a bundle with pairs by the lab's additive
    rule over the refit's training set (the visible validation singles count as training singles), never as the mean
    response; the two other baselines exactly as before; any other group is refused."""
    from conftest import make_cfg
    from test_norman_lab import make_pair_bundle
    from genemila.lab import Lab, additive_delta
    bundle = make_pair_bundle(tmp_path / "norman_toy")
    cfg = make_cfg(tmp_path)
    cfg["run"]["data_dir"] = str(bundle)
    lab = Lab(cfg, tmp_path / "run", bundle, repo=code_repo)
    try:
        public = rv.training_context(lab, tmp_path / "cache", augment=False)
        held = [p for p in public.perts if p not in set(public.train_perts)]
        got = rv._analytic_delta(public, "baseline_additive", held)
        assert np.allclose(got, lab._analytic_baseline("baseline_additive", held) - lab.control_mean, rtol=0,
                           atol=1e-12)
        names, d = public.train_delta()
        single = {public.target_genes(q)[0]: d[i] for i, q in enumerate(names) if len(public.target_genes(q)) == 1}
        both = [p for p in held if len(public.target_genes(p)) == 2 and all(g in single for g in
                                                                            public.target_genes(p))]
        assert both
        for p in both:   # A and B trained: Δ_A + Δ_B, not the mean training delta
            a, b = public.target_genes(p)
            assert np.allclose(got[held.index(p)], single[a] + single[b], rtol=0, atol=1e-12)
            assert not np.allclose(got[held.index(p)], d.mean(axis=0))
        # on all visible labels the visible validation singles join the training singles
        ctx = rv.training_context(lab, tmp_path / "cache")
        out = [p for p in ctx.perts if p not in set(ctx.train_perts)]
        names, d = ctx.train_delta()
        rows = {}
        for i, q in enumerate(names):
            if len(ctx.target_genes(q)) == 1:
                rows.setdefault(ctx.target_genes(q)[0], []).append(i)
        fill = d[[i for r in rows.values() for i in r]].mean(axis=0)
        want = np.array([sum(d[rows[g]].mean(axis=0) if g in rows else fill for g in ctx.target_genes(p))
                         for p in out])
        refit = rv._analytic_delta(ctx, "baseline_additive", out)
        assert np.allclose(refit, want, rtol=0, atol=1e-12)
        val1_genes = {ctx.target_genes(p)[0] for p in lab._val1.perts if len(ctx.target_genes(p)) == 1}
        uses = [p for p in out if set(ctx.target_genes(p)) & val1_genes]
        assert uses and not np.allclose(refit[[out.index(p) for p in uses]], got[[held.index(p) for p in uses]])
        assert np.array_equal(refit, additive_delta(out, {p: ctx.target_genes(p) for p in ctx.perts}, names, d))
        with pytest.raises(ValueError, match="unknown analytic baseline"):
            rv._analytic_delta(ctx, "baseline_something", out)
        with pytest.raises(ValueError, match="unknown analytic baseline"):
            rv._analytic_delta(ctx, "", out)
    finally:
        lab.close()
    # a single-target bundle: no change and the mean training delta, as the code before computed them
    lab = lab_factory()
    ctx = rv.training_context(lab, tmp_path / "c3")
    out = [p for p in ctx.perts if p not in set(ctx.train_perts)]
    _, d = ctx.train_delta()
    assert np.array_equal(rv._analytic_delta(ctx, "baseline_mean_response", out), np.tile(d.mean(axis=0), (len(out), 1)))
    assert np.array_equal(rv._analytic_delta(ctx, "baseline_unchanged", out), np.zeros((len(out), ctx.n_genes)))


def test_cache_is_keyed_by_the_bundle_not_the_run_directory(dataset, tmp_path):
    """Two run directories of the same name on different bundles never share a feature or gene_corr cache."""
    from genemila.data.synthetic import generate
    other = generate(tmp_path / "other" / "synthetic", n_genes=60, n_perts=20, n_control=200, cells_per_pert=20, seed=2)
    key = rv._bundle_key(dataset, "synthetic", "s")
    assert key == rv._bundle_key(dataset, "synthetic", "s") and key.startswith("synthetic__s__")
    assert len(key) == len("synthetic__s__") + 12 and rv._bundle_key(other, "synthetic", "s") != key


@pytest.fixture(scope="module")
def finished_run(tmp_path_factory, dataset, code_repo):
    """A small finished run with sealed scores: scripted planner, mock workers, under a minute."""
    from conftest import make_cfg
    from genemila.controller import Controller
    from genemila.lab import Lab
    from genemila.providers.mock import MockProvider, ScriptedPlanner
    tmp = tmp_path_factory.mktemp("refit")
    cfg = make_cfg(tmp, schedule__max_planner_calls=2)
    cfg["run"]["data_dir"] = str(dataset)
    lab = Lab(cfg, tmp / "run0", dataset, repo=code_repo)
    try:
        Controller(lab, workers=2, seconds=45, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
                   quiet=True).run()
    finally:
        lab.stop_event.set()
        lab.kill_event.set()
        lab.close()
    (lab.run_dir / "config.json").write_text(json.dumps(lab.cfg))
    return lab.run_dir


def _db(run_dir: Path) -> sqlite3.Connection:
    c = sqlite3.connect(run_dir / "lab.db")
    c.row_factory = sqlite3.Row
    return c


def _snapshot(run_dir: Path) -> dict:
    c = _db(run_dir)
    return {"events": c.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "queries": c.execute("SELECT COUNT(*) FROM events WHERE kind='query_only'").fetchone()[0],
            "sealed": [tuple(r) for r in c.execute("SELECT experiment_id, query_metrics_json FROM experiments "
                                                   "ORDER BY experiment_id")],
            "cache": sorted(str(p) for p in (run_dir / "cache").rglob("*")) if (run_dir / "cache").exists() else []}


def _counting_oracle(monkeypatch):
    calls = []
    orig = QueryOracle.query

    def query(self, experiment_id, pred, pert_order, control_mean, celleval_profile=None, genes=None):
        calls.append(experiment_id)
        return orig(self, experiment_id, pred, pert_order, control_mean, celleval_profile, genes)
    monkeypatch.setattr(QueryOracle, "query", query)
    return calls


def test_end_to_end_matches_the_summary_and_leaves_the_run_alone(finished_run, tmp_path, monkeypatch):
    run_dir = finished_run
    summary = json.loads((run_dir / "summary.json").read_text())
    gen = summary["generalization_query_only"]
    assert gen, "the run must have scored finalists on the sealed set"
    before = _snapshot(run_dir)
    calls = _counting_oracle(monkeypatch)
    out = tmp_path / "refit.md"
    assert rv.main(["--runs", str(run_dir), "--out", str(out), "--cache", str(tmp_path / "cache")]) == 0
    assert out.exists() and out.with_suffix(".json").exists()
    rep = json.loads(out.with_suffix(".json").read_text())
    assert len(rep["runs"]) == 1
    r = rep["runs"][0]
    # (iv) one oracle query per finalist: the singles, the ensemble if one was kept, and the starting baseline
    c = _db(run_dir)
    n_singles = c.execute("SELECT COUNT(*) FROM experiments WHERE status='completed' AND query_metrics_json IS NOT NULL "
                          "AND kind NOT IN ('baseline', 'ensemble')").fetchone()[0]
    n_ens = c.execute("SELECT COUNT(*) FROM experiments WHERE status='completed' AND kind='ensemble' "
                      "AND query_metrics_json IS NOT NULL").fetchone()[0]
    assert n_singles >= 1 and n_ens in (0, 1)
    assert len(calls) == n_singles + n_ens + 1 == r["n_queries"] == len(r["finalists"])
    assert [f["role"] for f in r["finalists"]] == ["single"] * n_singles + ["ensemble"] * n_ens + ["baseline"]
    # (iii) the original numbers are the run's own summary numbers, and the selected finalist is the summary's headline
    by_id = {g["experiment_id"]: g for g in gen}
    for f in r["finalists"]:
        g = by_id[f["experiment_id"]]
        assert f["original"]["pearson_delta"] == pytest.approx(g["query_only_pearson_delta"], abs=1e-12)
        assert f["visible_score"] == pytest.approx(g["visible_score"], abs=1e-12)
        comp = (g.get("comparable") or {}).get("val2") or {}
        for k in ("cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de"):
            assert f["original"][k] == pytest.approx(comp[k], abs=1e-12)
            assert f["refit"][k] is not None
        assert f["difference"]["pearson_delta"] == pytest.approx(f["refit"]["pearson_delta"] - f["original"]["pearson_delta"])
    assert r["selected"] == gen[0]["experiment_id"]  # the summary's headline row: highest visible score, baseline last
    if gen[0]["kind"] != "ensemble" and summary["best"]["experiment_id"] in by_id:
        assert r["selected"] == summary["best"]["experiment_id"]
    assert sum(f["selected"] for f in r["finalists"]) == 1
    assert r["n_train_refit"] == r["n_train"] + r["n_visible_validation"] and r["augmented"]
    assert r["train_signature"]["original"] != r["train_signature"]["refit"]
    assert r["arm"] == "scripted control (no LLM)" and r["workers"] == 2 and r["selection_rule"] == "pearson_delta"
    sel = next(f for f in r["finalists"] if f["selected"])
    assert sel["model"] in ("ridge", "lasso", "ols", "elasticnet", "ensemble") and sel["features"]
    md = out.read_text()
    assert "fixed before any sealed result under it was read" in md and "## By arm" in md and "## Reading" in md
    assert f"| {run_dir.name} | scripted control (no LLM) | 2 | {sel['experiment_id']} |" in md
    assert f"| {sel['experiment_id']}* |" in md and "1 of 1 runs" in md
    assert "—" not in md
    # the run itself is untouched: no event, no query charged, no sealed score changed, no cache written
    assert _snapshot(run_dir) == before
    # the tool's own cache is named by the bundle, not by the run directory
    dirs = [d.name for d in (tmp_path / "cache").iterdir()]
    assert len(dirs) == 1 and dirs[0].startswith("synthetic__split_") and run_dir.name not in dirs
    # (v) the JSON twin re-renders the markdown byte for byte
    again = tmp_path / "again.md"
    assert rv.main(["--from-json", str(out.with_suffix(".json")), "--out", str(again)]) == 0
    assert again.read_bytes() == out.read_bytes()
    assert rv.render(json.loads(json.dumps(rep))) == md


def test_arm_ensembles_average_the_selected_finalists(finished_run, tmp_path, monkeypatch):
    """Two run directories of the same arm (here the same run twice) give one arm ensemble: two more queries,
    and the average of identical predictions scores exactly like one of them."""
    run_dir = finished_run
    before = _snapshot(run_dir)
    calls = _counting_oracle(monkeypatch)
    out = tmp_path / "arms.md"
    assert rv.main(["--runs", str(run_dir), str(run_dir), "--out", str(out), "--cache", str(tmp_path / "cache"),
                    "--arm-ensembles", "--json", str(tmp_path / "twin.json")]) == 0
    rep = json.loads((tmp_path / "twin.json").read_text())
    r0, r1 = rep["runs"]
    assert len(calls) == 2 * r0["n_queries"] + 2 and r0["finalists"] == r1["finalists"]
    assert [c for c in calls if c.startswith("arm:")] == [c for c in calls][-2:]
    assert len(rep["arms"]) == 1
    arm = rep["arms"][0]
    assert arm["n"] == 2 and arm["difference"]["n"] == 2 and arm["ensemble"]["n_queries"] == 2
    sel = next(f for f in r0["finalists"] if f["selected"])
    assert arm["ensemble"]["original"]["pearson_delta"] == pytest.approx(sel["original"]["pearson_delta"], abs=1e-9)
    assert arm["ensemble"]["refit"]["pearson_delta"] == pytest.approx(sel["refit"]["pearson_delta"], abs=1e-9)
    assert arm["original"]["mean"] == pytest.approx(sel["original"]["pearson_delta"]) and arm["original"]["sd"] == 0.0
    md = out.read_text()
    assert "## Arm ensembles" in md and "| scripted control (no LLM) | 2 | 2 |" in md
    assert _snapshot(run_dir) == before
    again = tmp_path / "again.md"
    assert rv.main(["--from-json", str(tmp_path / "twin.json"), "--out", str(again)]) == 0
    assert again.read_bytes() == out.read_bytes()


def test_training_set_refit_reproduces_the_runs_sealed_scores(finished_run, tmp_path, monkeypatch):
    """(vii) With the public training set instead of all visible labels, the tool's fit path is the pipeline's:
    every finalist's sealed pearson_delta comes back within 1e-6 of the run's own, the baseline included."""
    run_dir = finished_run
    calls = _counting_oracle(monkeypatch)
    r = rv.refit_run(run_dir, tmp_path / "cache", augment=False)
    assert not r["augmented"] and r["n_train_refit"] == r["n_train"]
    assert r["train_signature"]["original"] == r["train_signature"]["refit"]
    assert len(calls) == len(r["finalists"]) >= 2
    kinds = {f["role"] for f in r["finalists"]}
    assert "baseline" in kinds and "single" in kinds
    for f in r["finalists"]:
        assert f["refit"]["pearson_delta"] == pytest.approx(f["original"]["pearson_delta"], abs=1e-6), f["experiment_id"]
        for k in ("cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de"):
            assert f["refit"][k] == pytest.approx(f["original"][k], abs=1e-6), (f["experiment_id"], k)
    base = next(f for f in r["finalists"] if f["role"] == "baseline")
    assert base["model"] in ("ridge", "lasso", "ols") and set(base["features"]) == {"control_mean", "mean_response", "is_target"}
