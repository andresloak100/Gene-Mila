"""tools/cellforge_bridge.py: the export holds only control and training cells on the bundle's genes, normalised as
the bundle was, and lists every non-training perturbation as held out; the score reads predictions in either format
and scores them once through the oracle (a perfect prediction scores pearson_delta 1)."""
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

import cellforge_bridge as cb  # noqa: E402
from genemila.data.bundle import write_bundle  # noqa: E402
from genemila.data.real import _normalise_log1p  # noqa: E402


@pytest.fixture()
def screen(tmp_path):
    rng = np.random.default_rng(0)
    n_genes = 40
    genes = [f"G{i:02d}" for i in range(n_genes)] + ["EXTRA1", "EXTRA2"]
    perts = [f"G{i:02d}" for i in range(12)]
    base = rng.uniform(1, 20, len(genes))
    rows, labels = [], []
    for p in ["control"] + perts:
        lam = base.copy()
        if p != "control":
            lam[genes.index(p)] *= 0.2
            lam[rng.choice(n_genes, 5, replace=False)] *= rng.uniform(0.5, 2.0, 5)
        n = 300 if p == "control" else 30
        rows.append(rng.poisson(lam, size=(n, len(genes))))
        labels += [p if p == "control" else f"{p}_sg1"] * n
    counts = np.vstack(rows).astype(np.float32)
    h5 = tmp_path / "screen.h5ad"
    ad.AnnData(X=counts, obs=pd.DataFrame({"perturbation": labels}, index=[f"c{i}" for i in range(len(labels))]),
               var=pd.DataFrame(index=genes)).write_h5ad(h5)
    norm = np.asarray(_normalise_log1p(counts))
    lab = np.array(labels)
    bundle_genes = genes[:n_genes]
    gi = [genes.index(g) for g in bundle_genes]
    means = {p: norm[lab == f"{p}_sg1"][:, gi].mean(0) for p in perts}
    splits = {"train": perts[:6], "val1": perts[6:9], "val2": perts[9:], "split_id": "split_test"}
    bundle = write_bundle(tmp_path / "bundle", "test", bundle_genes, norm[lab == "control"][:, gi], means,
                          {p: 30 for p in perts}, {p: [p] for p in perts}, splits)
    return h5, bundle, means, splits


def test_export_holds_only_training_and_control_cells(screen, tmp_path):
    h5, bundle, means, splits = screen
    rec = cb.export(bundle, [h5], tmp_path / "cf")
    a = ad.read_h5ad(tmp_path / "cf" / "cellforge_input.h5ad")
    assert set(a.obs["perturbation"]) == {"control", *splits["train"]}
    assert list(a.var_names) == [f"G{i:02d}" for i in range(40)]
    assert rec["n_control_cells"] == 300 and rec["train_missing_in_file"] == []
    held = json.loads((tmp_path / "cf" / "heldout_perturbations.json").read_text())
    assert held == sorted(splits["val1"] + splits["val2"])
    x = a.X.toarray() if hasattr(a.X, "toarray") else a.X
    p = splits["train"][0]
    assert np.allclose(x[a.obs["perturbation"].to_numpy() == p].mean(0), means[p], atol=1e-5)
    with pytest.raises(SystemExit):
        cb.export(bundle, [h5], tmp_path / "cf")


def test_score_perfect_prediction_in_both_formats(screen, tmp_path):
    h5, bundle, means, splits = screen
    held = sorted(splits["val1"] + splits["val2"])
    genes = [f"G{i:02d}" for i in range(40)]
    npz = tmp_path / "pred.npz"
    np.savez(npz, perts=np.array(held), means=np.stack([means[p] for p in held]), genes=np.array(genes))
    rep = cb.score(bundle, npz)
    assert rep["cellforge"]["metrics"]["pearson_delta"] == pytest.approx(1.0, abs=1e-6)
    cells = np.repeat(np.stack([means[p] for p in held]), 3, axis=0)
    h = tmp_path / "pred.h5ad"
    ad.AnnData(X=cells.astype(np.float32), obs=pd.DataFrame({"perturbation": np.repeat(held, 3)},
               index=[f"p{i}" for i in range(len(cells))]), var=pd.DataFrame(index=genes)).write_h5ad(h)
    assert cb.score(bundle, h)["cellforge"]["metrics"]["pearson_delta"] == pytest.approx(1.0, abs=1e-5)
    np.savez(tmp_path / "short.npz", perts=np.array(held[:2]), means=np.stack([means[p] for p in held[:2]]))
    with pytest.raises(SystemExit):
        cb.score(bundle, tmp_path / "short.npz")
    assert "pearson_delta" in cb.render(rep)
