"""tools/fresh_test_score.py, the holder's scoring: on a synthetic cohort a model predicting the cohort's own deltas
scores pearson_delta 1 and beats a model predicting no change, per subset, with one Holm over both parts; a deposit
whose hashes do not match is refused; a model missing a target is refused."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ad = pytest.importorskip("anndata")
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import fresh_test_score as fts  # noqa: E402
from genemila.data.real import _normalise_log1p  # noqa: E402


@pytest.fixture()
def setup(tmp_path):
    rng = np.random.default_rng(0)
    genes = [f"G{i:03d}" for i in range(60)] + ["X1", "X2"]
    targets = [f"G{i:03d}" for i in range(24)]
    base = rng.uniform(1, 15, len(genes))
    rows, labels = [], []
    for t in ["non-targeting"] + targets:
        lam = base.copy()
        if t != "non-targeting":
            lam[genes.index(t)] *= 0.2
            lam[rng.choice(60, 6, replace=False)] *= rng.uniform(0.4, 2.5, 6)
        n = 400 if t == "non-targeting" else 25
        rows.append(rng.poisson(lam, size=(n, len(genes))))
        labels += [t if t == "non-targeting" else f"{t}_guide"] * n
    X = np.vstack(rows).astype(np.float32)
    cohort = tmp_path / "cohort.h5ad"
    ad.AnnData(X=X, obs=pd.DataFrame({"gene": labels}, index=[f"c{i}" for i in range(len(labels))]),
               var=pd.DataFrame({"gene_name": genes}, index=[f"E{i}" for i in range(len(genes))])).write_h5ad(cohort)
    panel = genes[:60]
    trows = [{"symbol": t, "labels": [f"{t}_guide"], "eligible": True, "in_distribution": (i // 2) % 2 == 0}
             for i, t in enumerate(targets)]
    manifest = {"h5ad": {"label_col": "gene", "gene_col": "gene_name"}, "targets": trows,
                "draw": {"r1": targets[::2], "r2": targets[1::2]},
                "common_gene_panel": {"genes": panel, "cohort_symbols": panel}}
    mpath = tmp_path / "manifest.json"
    mpath.write_text(json.dumps(manifest))
    N = np.asarray(_normalise_log1p(X))
    L = np.array(labels)
    gi = [genes.index(g) for g in panel]
    ctrl = N[L == "non-targeting"][:, gi].mean(0)
    true_delta = np.stack([N[L == f"{t}_guide"][:, gi].mean(0) - ctrl for t in targets])
    dep = tmp_path / "deposit"
    for name, delta in (("perfect", true_delta), ("zero", np.zeros_like(true_delta) + 1e-3 * rng.normal(size=true_delta.shape))):
        (dep / name).mkdir(parents=True)
        np.savez(dep / name / "predictions.npz", delta=delta.astype(np.float32), perts=np.array(targets),
                 genes=np.array(panel))
    (dep / "batch.json").write_text(json.dumps({"models": [{"name": "perfect", "dir": "perfect"},
                                                           {"name": "zero", "dir": "zero"}],
                                                "comparisons": [["perfect", "zero"]]}))
    return cohort, mpath, dep


def test_scores_and_paired_reading(setup):
    cohort, mpath, dep = setup
    reps = [fts.score(cohort, mpath, dep, p, max_control=10_000) for p in ("r1", "r2")]
    fts.holm_over(reps)
    for rep in reps:
        assert rep["n_targets"] == 12 and rep["subset_sizes"]["in_distribution"] == 6
        assert rep["models"]["perfect"]["all"]["pearson_delta"] == pytest.approx(1.0, abs=1e-6)
        c = rep["comparisons"][0]
        assert c["all"]["verdict"] == "a" and c["all"]["wins_a"] == 12
        if "mean_diff" in c["in_distribution"]:
            assert "p_holm" in c["in_distribution"]
    assert "perfect" in fts.render(reps[0])


def test_refuses_a_bad_deposit(setup):
    cohort, mpath, dep = setup
    (dep / "deposit_sha256.json").write_text(json.dumps({"perfect/predictions.npz": "0" * 64}))
    with pytest.raises(SystemExit):
        fts.score(cohort, mpath, dep, "r1")
    (dep / "deposit_sha256.json").unlink()
    z = dict(np.load(dep / "zero" / "predictions.npz"))
    np.savez(dep / "zero" / "predictions.npz", delta=z["delta"][:3], perts=z["perts"][:3], genes=z["genes"])
    with pytest.raises(SystemExit):
        fts.score(cohort, mpath, dep, "r1")
