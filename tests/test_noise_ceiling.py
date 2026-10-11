"""tools/noise_ceiling.py: the split-half noise ceiling of pearson_delta reads visible data only."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import noise_ceiling as nc  # noqa: E402

from genemila.data.bundle import split_id_for, write_bundle  # noqa: E402
from genemila.pipeline import run as run_pipeline  # noqa: E402
from genemila.spec import ExperimentSpec  # noqa: E402
from genemila.worker import prune_predictions  # noqa: E402

N_GENES = 100


def test_never_reads_the_sealed_labels():
    src = (ROOT / "tools" / "noise_ceiling.py").read_text().lower()
    for word in ("val2", "query_only", "queryoracle", "benchmark.oracle", "lab.oracle", "oracle.query"):
        assert word not in src, word


def _bundle(tmp_path, seed=0):
    """A bundle with known biology: two strong, well-sampled visible-validation perturbations, two weak,
    thinly sampled ones, and one with too few cells. Returns (dir, true deltas, lab control mean)."""
    rng = np.random.default_rng(seed)
    genes = [f"G{i:03d}" for i in range(N_GENES)]
    mu = rng.gamma(4.0, 1.0, N_GENES) + 2.0

    def cells(n, delta):
        return np.clip(mu + delta + rng.normal(0, 0.5, size=(n, N_GENES)), 0, None).astype(np.float32)

    public_control = cells(500, 0.0)
    design = {"STRONG1": (200, 0.4), "STRONG2": (200, 0.4), "WEAK1": (10, 0.05), "WEAK2": (10, 0.05), "TINY": (3, 0.4)}
    truth, eval_cells, means, ncells, targets = {}, {"control": cells(100, 0.0)}, {}, {}, {}
    for name, (n, scale) in design.items():
        truth[name] = rng.normal(0, scale, N_GENES)
        eval_cells[name] = cells(n, truth[name])
        means[name] = eval_cells[name].astype(np.float64).mean(axis=0)
        ncells[name] = n
        targets[name] = [genes[0]]
    for name in ("T1", "T2", "T3", "SEALED1"):
        means[name] = cells(50, rng.normal(0, 0.3, N_GENES)).mean(axis=0)
        ncells[name] = 50
        targets[name] = [genes[1]]
    splits = {"train": ["T1", "T2", "T3"], "val1": sorted(design), "val2": ["SEALED1"], "seed": 0}
    splits["split_id"] = split_id_for(splits)
    out = write_bundle(tmp_path / "bundle", "toy", genes, public_control, means, ncells, targets, splits,
                       eval_cells=eval_cells)
    return out, truth, public_control.astype(np.float64).mean(axis=0)


def test_strong_well_sampled_effects_sit_near_one_and_weak_ones_lower(tmp_path):
    out, truth, control_mean = _bundle(tmp_path)
    rep = nc.analyse_dataset(out, repeats=30, seed=0)
    rows = {r["pert"]: r for r in rep["perturbations"]}
    assert set(rows) == {"STRONG1", "STRONG2", "WEAK1", "WEAK2"}
    for p in ("STRONG1", "STRONG2"):
        assert rows[p]["n_cells"] == 200 and rows[p]["r_half_mean"] > 0.9 and rows[p]["ceiling"] > 0.9
        assert rows[p]["target_is_stored_mean"]
    for p in ("WEAK1", "WEAK2"):
        assert rows[p]["n_cells"] == 10 and rows[p]["ceiling"] < 0.7
        assert rows[p]["r_half_mean"] < rows["STRONG1"]["r_half_mean"]
        assert rows[p]["ceiling"] < rows["STRONG1"]["ceiling"] and rows[p]["ceiling"] < rows["STRONG2"]["ceiling"]
    # the ceiling is what a perfect predictor of the true delta scores against the recorded (noisy) target
    z = np.load(out / "private" / "val1.npz", allow_pickle=False)
    recorded = {str(p): m.astype(np.float64) for p, m in zip(z["perts"], z["means"])}
    for p in ("STRONG1", "STRONG2"):
        perfect = nc.pearson(truth[p], recorded[p] - control_mean)
        assert abs(perfect - rows[p]["ceiling"]) < 0.05
    ov = rep["overall"]
    assert ov["n"] == 4 and ov["min_ceiling"] < 0.7 < 0.9 < ov["max_ceiling"]
    assert ov["mean_ceiling"] == pytest.approx(np.mean([r["ceiling"] for r in rows.values()]))
    assert ov["n_target_is_stored_mean"] == 4
    assert rep["control"]["n_cells"] == 100 and rep["control"]["n_public_control_cells"] == 500
    assert abs(rep["control"]["r_half_mean"]) < 0.3  # disjoint control samples: only the shared control mean is common
    assert rep["repeats"] == 30 and rep["seed"] == 0 and rep["n_genes"] == N_GENES
    # the splits are seeded: the same call gives the same numbers
    again = nc.analyse_dataset(out, repeats=30, seed=0)
    assert again["perturbations"] == rep["perturbations"]


def test_ceiling_is_bounded_and_degenerate_cases_are_handled(tmp_path):
    out, _, _ = _bundle(tmp_path)
    rep = nc.analyse_dataset(out, repeats=10, seed=3)
    for r in rep["perturbations"]:
        assert 0.0 <= r["ceiling"] <= 1.0 and -1.0 <= r["r_half_mean"] <= 1.0 and r["valid_repeats"] == 10
        assert np.isfinite(r["r_full"])
    assert [s["pert"] for s in rep["skipped"]] == ["TINY"] and rep["skipped"][0]["n_cells"] == 3
    assert "fewer than 4" in rep["skipped"][0]["reason"]
    md = nc.render(rep)
    assert "Skipped: TINY (3 cells: fewer than 4 stored cells)." in md and "| TINY |" not in md
    # negative or perfect reliabilities map into [0, 1]
    assert nc.ceiling_from(-0.5) == (-2.0, 0.0) and nc.ceiling_from(-1.0)[1] == 0.0 and nc.ceiling_from(1.0) == (1.0, 1.0)
    assert nc.ceiling_from(0.5) == pytest.approx((2 / 3, np.sqrt(2 / 3)))
    # a constant delta has no correlation: NaN, excluded from the average rather than counted as 0
    assert np.isnan(nc.pearson(np.ones(5), np.arange(5.0)))
    control_mean = np.arange(N_GENES, dtype=np.float64)  # integer-valued, so the deltas are exactly constant
    flat = np.tile(control_mean + 1.0, (8, 1))
    rs = nc.split_half_correlations(flat, control_mean, np.random.default_rng(0), 5)
    assert np.isnan(rs).all() and nc._summ(rs) == (None, None, 0)
    mixed = np.array([0.5, np.nan, 0.7])
    mean, sd, n = nc._summ(mixed)
    assert n == 2 and mean == pytest.approx(0.6) and sd == pytest.approx(np.std([0.5, 0.7], ddof=1))
    # no NaN reaches the JSON twin
    assert "NaN" not in json.dumps(nc._clean({"a": float("nan"), "b": [np.float64("inf"), np.int64(3), 1.5]}))
    assert nc._clean({"a": float("nan"), "b": [np.float64("inf"), np.int64(3), 1.5]}) == {"a": None, "b": [None, 3, 1.5]}


def _subsampled_bundle(tmp_path, seed=0, n_all=1000, n_stored=300, scale=0.05):
    """A bundle like a real one: the recorded target of SUB averages n_all cells but only n_stored of them are
    stored for cell-eval. Returns (dir, true mean expression of SUB, lab control mean)."""
    rng = np.random.default_rng(seed)
    genes = [f"G{i:03d}" for i in range(N_GENES)]
    mu = rng.gamma(4.0, 1.0, N_GENES) + 2.0

    def cells(n, delta):
        return np.clip(mu + delta + rng.normal(0, 0.5, size=(n, N_GENES)), 0, None).astype(np.float32)

    public_control = cells(500, 0.0)
    truth = rng.normal(0, scale, N_GENES)
    every = cells(n_all, truth)
    stored = every[rng.choice(n_all, size=n_stored, replace=False)]
    means = {"SUB": every.astype(np.float64).mean(axis=0), "T1": cells(50, 0.0).mean(axis=0),
             "S1": cells(50, 0.0).mean(axis=0)}
    ncells = {"SUB": n_all, "T1": 50, "S1": 50}
    targets = {k: [genes[0]] for k in means}
    splits = {"train": ["T1"], "val1": ["SUB"], "val2": ["S1"], "seed": 0}
    splits["split_id"] = split_id_for(splits)
    out = write_bundle(tmp_path / "sub", "toy", genes, public_control, means, ncells, targets, splits,
                       eval_cells={"control": cells(100, 0.0), "SUB": stored})
    return out, mu + truth, public_control.astype(np.float64).mean(axis=0)


def test_target_over_more_cells_than_stored_needs_the_cell_count(tmp_path):
    out, true_mean, control_mean = _subsampled_bundle(tmp_path)
    z = np.load(out / "private" / "val1.npz", allow_pickle=False)
    recorded = z["means"][0].astype(np.float64)
    # what the lab's metric gives a predictor of the true mean expression (both sides subtract the same control mean)
    perfect = nc.pearson(true_mean - control_mean, recorded - control_mean)
    # without the count the ceiling is that of the 300 stored cells: a lower bound, and reported as one
    low = nc.analyse_dataset(out, repeats=30, seed=0)
    row = low["perturbations"][0]
    assert row["pert"] == "SUB" and row["n_cells"] == 300 and row["n_target"] is None and row["sb_k"] == 2.0
    assert not row["target_is_stored_mean"] and row["ceiling"] < perfect - 0.03
    assert low["overall"]["lower_bound"] and low["overall"]["n_target_unknown"] == 1 and low["overall"]["n_corrected"] == 0
    md = nc.render(low)
    assert "can reach at least about" in md and "lower bound" in md and "cannot exceed" not in md
    assert "| SUB | 300 | unknown (lower bound) |" in md
    # with the count, Spearman-Brown is carried to the 1000 cells behind the target and the ceiling is right
    high = nc.analyse_dataset(out, repeats=30, seed=0, ncells={"SUB": 1000, "T1": 50})
    row = high["perturbations"][0]
    assert row["n_target"] == 1000 and row["sb_k"] == pytest.approx(2000 / 300)
    assert abs(row["ceiling"] - perfect) < 0.03 and row["ceiling"] > low["perturbations"][0]["ceiling"]
    assert row["r_half_mean"] == low["perturbations"][0]["r_half_mean"]  # the split itself is unchanged
    assert not high["overall"]["lower_bound"] and high["overall"]["n_corrected"] == 1
    md = nc.render(high)
    assert "cannot exceed about" in md and "carried to" in md and "| SUB | 300 | 1000 |" in md
    # a count below the stored cells is a contradiction
    with pytest.raises(ValueError):
        nc.analyse_dataset(out, repeats=5, seed=0, ncells={"SUB": 200})
    # through the CLI, with the JSON twin re-rendering byte-identically
    nfile = tmp_path / "ncells.json"
    nfile.write_text(json.dumps({"SUB": 1000}))
    md_path = tmp_path / "c.md"
    assert nc.main(["--data", str(out), "--out", str(md_path), "--ncells", str(nfile), "--repeats", "8"]) == 0
    rep = json.loads(md_path.with_suffix(".json").read_text())
    assert rep["ncells_file"] == str(nfile) and rep["n_ncells_given"] == 1 and rep["perturbations"][0]["n_target"] == 1000
    assert str(nfile) in md_path.read_text()
    again = tmp_path / "again.md"
    assert nc.main(["--from-json", str(md_path.with_suffix(".json")), "--out", str(again)]) == 0
    assert again.read_bytes() == md_path.read_bytes()
    # the generalised step reduces to the familiar one at k = 2 and never leaves [0, 1]
    assert nc.spearman_brown(0.5, 2.0) == nc.spearman_brown(0.5) == pytest.approx(2 / 3)
    assert nc.spearman_brown(0.6, 20 / 3) == pytest.approx((20 / 3 * 0.6) / (1 + (17 / 3) * 0.6))
    assert nc.ceiling_from(-0.3, 20 / 3) == (-1.0, 0.0) and nc.ceiling_from(-0.1, 20 / 3)[1] == 0.0
    assert nc.ceiling_from(1.0, 20 / 3) == (1.0, 1.0)


def test_cli_writes_a_json_twin_that_re_renders_byte_identically(tmp_path):
    out, _, _ = _bundle(tmp_path)
    md = tmp_path / "ceiling.md"
    assert nc.main(["--data", str(out), "--out", str(md), "--repeats", "8", "--seed", "1"]) == 0
    twin = md.with_suffix(".json")
    rep = json.loads(twin.read_text())
    assert rep["dataset"] == "toy" and rep["repeats"] == 8 and rep["seed"] == 1 and rep["runs"] == []
    text = md.read_text()
    assert text.startswith("# Noise ceiling of pearson_delta on toy") and "## Reading" in text
    assert "## Control-noise caveat" in text and "null ceiling" in text and "cannot exceed about" in text
    assert "\u2014" not in text  # no em-dashes in the prose
    again = tmp_path / "again.md"
    assert nc.main(["--from-json", str(twin), "--out", str(again)]) == 0
    assert again.read_bytes() == md.read_bytes()
    # an explicit --json path
    assert nc.main(["--data", str(out), "--out", str(tmp_path / "x.md"), "--json", str(tmp_path / "y.json"),
                    "--repeats", "8", "--seed", "1"]) == 0
    assert (tmp_path / "y.json").read_text() == twin.read_text() and not (tmp_path / "x.json").exists()


def test_runs_show_achieved_against_the_ceiling(lab_factory, tmp_path):
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
        art = lab.artifacts / eid
        run_pipeline(spec.run_spec(), lab.public_dir, lab.run_dir / "plugins", art)
        ev = lab.evaluate_artifact(art / "predictions.npz")
        prune_predictions(art / "predictions.npz", ev["alpha_index"])
        prune_predictions(art / "cv.npz", ev["alpha_index"])
        lab.db.update_experiment(eid, status="completed", artifact_dir=str(art), best_alpha=ev["best_alpha"],
                                 primary_score=ev["metrics"]["primary"], val_metrics_json=ev["metrics"])
        recs.append(lab.db.get_experiment(eid))
    (lab.run_dir / "config.json").write_text(json.dumps(lab.cfg))
    best = max(recs, key=lambda r: r["primary_score"])
    other = min(recs, key=lambda r: r["primary_score"])
    assert best["experiment_id"] != other["experiment_id"]
    data = nc.analyse_dataset(lab.data_dir, repeats=5, seed=0)
    assert data["split_id"] == lab.split_id and data["overall"]["n"] == len(lab._val1.perts)
    # nothing was scored on the sealed set yet: the best completed experiment is the run's model
    r = nc.analyse_run(lab.run_dir, data)
    assert r.get("error") is None, r
    assert r["experiment_id"] == best["experiment_id"] and "none was scored" in r["selected_by"]
    assert r["n_matched"] == r["n_visible"] == len(lab._val1.perts) and r["note"] is None
    assert r["mean_achieved"] == pytest.approx(best["val_metrics_json"]["pearson_delta"], abs=1e-6)
    assert r["recorded_pearson_delta"] == pytest.approx(r["pearson_delta_all_visible"], abs=1e-6)
    assert r["mean_ceiling"] == pytest.approx(data["overall"]["mean_ceiling"])
    assert r["headroom"] == pytest.approx(r["mean_ceiling"] - r["mean_achieved"])
    assert all(t["gap"] == pytest.approx(t["ceiling"] - t["achieved"]) for t in r["per_perturbation"])
    assert -1.0 <= r["achieved_vs_ceiling_r"] <= 1.0 and r["arm"] == "scripted control (no LLM)"
    # the run's selected model is the best visible score among the experiments it scored on the sealed set at
    # its end; marking only the weaker one as scored makes it the selected model
    lab.db.update_experiment(other["experiment_id"], query_metrics_json={"primary": 0.0})
    r2 = nc.analyse_run(lab.run_dir, data)
    assert r2["experiment_id"] == other["experiment_id"] and "sealed set" in r2["selected_by"]
    assert r2["mean_achieved"] == pytest.approx(other["val_metrics_json"]["pearson_delta"], abs=1e-6)
    assert lab.oracle.used == 0, "the ceiling tool must not query the sealed set"
    md = tmp_path / "ceiling.md"
    assert nc.main(["--data", str(lab.data_dir), "--out", str(md), "--runs", str(lab.run_dir), str(tmp_path / "missing"),
                    "--repeats", "5"]) == 0
    text = md.read_text()
    assert "## Achieved vs ceiling" in text and f"Selected model {other['experiment_id']}" in text
    assert "| perturbation | cells | ceiling | achieved | gap |" in text and "headroom" in text
    assert "Not scored:" in text  # the missing run directory is shown, not fatal
    rep = json.loads(md.with_suffix(".json").read_text())
    assert [x["run_id"] for x in rep["runs"]] == [lab.run_id, "missing"] and rep["runs"][1]["error"]
    again = tmp_path / "again.md"
    assert nc.main(["--from-json", str(md.with_suffix(".json")), "--out", str(again)]) == 0
    assert again.read_bytes() == md.read_bytes()
    # a run whose selected model's artifacts are gone (copied from another machine, cleaned up) is a row, not a crash
    lab.db.update_experiment(other["experiment_id"], artifact_dir=str(tmp_path / "gone"))
    r3 = nc.analyse_run(lab.run_dir, data)
    assert r3["error"].startswith("FileNotFoundError") and r3["run_id"] == lab.run_id and r3["arm"] == r["arm"]
    # predictions that cover none of the visible perturbations are a row too
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    np.savez(foreign / "predictions.npz", perts=np.array(["NOT_A_VALIDATION_PERT"]), alphas=np.array([1.0]),
             delta=np.zeros((1, 1, len(lab.control_mean))))
    lab.db.update_experiment(other["experiment_id"], artifact_dir=str(foreign))
    r4 = nc.analyse_run(lab.run_dir, data)
    assert "cover none of the visible validation perturbations" in r4["error"]
    broken = tmp_path / "broken.md"
    assert nc.main(["--data", str(lab.data_dir), "--out", str(broken), "--runs", str(lab.run_dir), "--repeats", "5"]) == 0
    text = broken.read_text()
    assert "Not scored: " in text and "cover none" in text and "## Reading" in text
    assert json.loads(broken.with_suffix(".json").read_text())["runs"][0]["error"] == r4["error"]
    assert lab.oracle.used == 0
