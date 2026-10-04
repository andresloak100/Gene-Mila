import json

import numpy as np
import pytest

from genemila.benchmark import celleval
from genemila.data.bundle import LabelSet


def fake_screen(tmp_path, n_genes=200, seed=0):
    """A tiny scPerturb-style AnnData: raw counts, obs['perturbation'], two guides for one gene."""
    ad = pytest.importorskip("anndata")
    import pandas as pd
    import scipy.sparse as sp
    rng = np.random.default_rng(seed)
    genes = [f"G{i}" for i in range(n_genes)]
    base = rng.gamma(2.0, 2.0, n_genes)
    labels, rows = [], []
    def cells(label, n, target=None):
        mu = base.copy()
        if target is not None:
            mu[target] *= 0.1
            mu[(target + 1) % n_genes] *= 3.0
        rows.append(rng.poisson(mu, size=(n, n_genes)))
        labels.extend([label] * n)
    cells("control", 400)
    for t in range(1, 21):
        cells(f"G{t}_guide1", 30, t)
    cells("G1_guide2", 30, 1)          # second guide for G1, merged with G1_guide1
    cells("G2+G3", 30, 2)              # a double perturbation
    cells("NOTAGENE", 30)              # unmeasured target, dropped
    X = sp.csr_matrix(np.vstack(rows).astype(np.float32))
    a = ad.AnnData(X=X, obs=pd.DataFrame({"perturbation": labels}, index=[f"c{i}" for i in range(len(labels))]),
                   var=pd.DataFrame(index=genes))
    path = tmp_path / "screen.h5ad"
    a.write_h5ad(path)
    return path


def test_ingest_scperturb_layout(tmp_path):
    from genemila.data.real import describe_h5ad, ingest_h5ad
    path = fake_screen(tmp_path)
    assert describe_h5ad(path)["condition_key"] == "perturbation"
    out = ingest_h5ad(path, tmp_path / "bundle", "fake", n_hvg=50, max_control_cells=200, max_eval_cells=25)
    m = json.loads((out / "manifest.json").read_text())
    assert m["raw_counts_normalised"] and m["control_value"] == ["control"]
    assert m["n_dropped_labels"] == 1
    z = np.load(out / "public.npz", allow_pickle=False)
    perts = set(map(str, z["perts"]))
    assert "G1" in perts and "G2+G3" in perts and len(perts) == 21   # guides merged by target
    assert {"G1", "G2", "G3"} <= set(map(str, z["genes"]))           # targets kept beside HVGs
    assert z["control_cells"].shape[0] == 200 and z["control_cells"].max() < 15  # log-normalised
    targets = json.loads((out / "knowledge" / "targets.json").read_text())
    assert targets["G2+G3"] == ["G2", "G3"]
    X, labels = celleval.load_real_cells(out, "val1")
    v1 = LabelSet.load(out / "private" / "val1.npz")
    assert set(labels) == set(v1.perts) | {"control"}
    assert (labels == "control").sum() == 25 and X.shape[1] == len(z["genes"])
    assert not set(v1.perts) & set(map(str, z["train_perts"]))


def test_external_splits_are_used(tmp_path):
    from genemila.data.real import ingest_h5ad
    path = fake_screen(tmp_path)
    split = {"train": [f"G{i}" for i in range(1, 15)], "val": ["G15", "G16", "G17"],
             "test": ["G18", "G19", "G20", "G2+G3"]}
    (tmp_path / "s.json").write_text(json.dumps(split))
    out = ingest_h5ad(path, tmp_path / "b", "fake", n_hvg=50, splits_file=tmp_path / "s.json")
    s = json.loads((out / "splits.json").read_text())
    assert s["val1"] == ["G15", "G16", "G17"] and s["val2"] == sorted(split["test"])
    assert s["seed"] == "external:s.json"
    assert len(np.load(out / "public.npz")["perts"]) == 21


@pytest.mark.skipif(not celleval.available(), reason="cell-eval not installed")
def test_celleval_ranks_truth_above_baseline(dataset):
    z = np.load(dataset / "public.npz", allow_pickle=False)
    genes = [str(g) for g in z["genes"]]
    lab = LabelSet.load(dataset / "private" / "val1.npz")
    X, labels = celleval.load_real_cells(dataset, "val1")
    ctrl = z["control_cells"].mean(0)
    pred, real = celleval.build_pair({p: m - ctrl for p, m in zip(lab.perts, lab.means)}, X, labels, genes)
    for p in lab.perts:  # one predicted cell per real cell, same controls
        assert (pred.obs["target"] == p).sum() == (real.obs["target"] == p).sum()
    assert (pred.obs["target"] == "control").sum() == (real.obs["target"] == "control").sum()
    truth = celleval.score({p: m - ctrl for p, m in zip(lab.perts, lab.means)}, X, labels, genes, profile="minimal")
    mean = z["train_means"].mean(0) - ctrl
    base = celleval.score({p: mean for p in lab.perts}, X, labels, genes, profile="minimal")
    assert truth["pearson_delta"] > 0.95 and truth["pearson_delta"] > base["pearson_delta"]
    assert truth["mse"] < base["mse"]


@pytest.mark.skipif(not celleval.available(), reason="cell-eval not installed")
def test_final_report_includes_celleval(lab_factory):
    from genemila.report import finalize
    lab = lab_factory(final__celleval=True, final__celleval_profile="minimal", final__top_k=1)
    lab.record_analytic_baselines()
    s = finalize(lab, query=True)
    rows = [g for g in s["generalization_query_only"] if g.get("cell_eval")]
    assert rows, s["generalization_query_only"]
    ce = rows[0]["cell_eval"]
    assert "pearson_delta" in ce["val1"] and "pearson_delta" in ce["val2"]
    assert (lab.run_dir / "celleval" / f"{rows[0]['experiment_id']}_val2.json").exists()
    assert "## CELL-EVAL" in (lab.run_dir / "summary.md").read_text()
    assert len(lab.oracle.queries) == 1  # cell-eval rides on the same capped oracle query


def test_counts_detected_in_csc_with_low_first_genes():
    import scipy.sparse as sp
    from genemila.data.real import _looks_like_counts
    rng = np.random.default_rng(0)
    low = rng.poisson(0.5, size=(3000, 200))         # first genes: tiny counts, max well below 20
    high = rng.poisson(30.0, size=(3000, 400))       # most genes: large counts
    X = sp.csc_matrix(np.hstack([low, high]).astype(np.float32))
    assert X.data[:100_000].max() < 20               # what the old first-entries sample saw
    assert _looks_like_counts(X)
    assert not _looks_like_counts(sp.csc_matrix(np.log1p(X.toarray())))


def test_unlabelled_cells_and_several_control_labels(tmp_path):
    ad = pytest.importorskip("anndata")
    from genemila.data.real import ingest_h5ad
    path = fake_screen(tmp_path)
    a = ad.read_h5ad(path)
    lab = a.obs["perturbation"].astype(object).to_numpy()
    ctrl = (lab == "control").nonzero()[0]
    lab[ctrl[:250]] = "63(mod)_pBA580"                                 # Adamson-style control guide names
    lab[ctrl[250:]] = "Gal4-4(mod)_pBA582"
    lab[:5] = np.nan                                                   # unlabelled cells
    a.obs["perturbation"] = lab
    a.write_h5ad(path)
    with pytest.raises(ValueError):
        ingest_h5ad(path, tmp_path / "b0", "fake", n_hvg=50)          # no known control label
    out = ingest_h5ad(path, tmp_path / "b", "fake", n_hvg=50, max_control_cells=200, max_eval_cells=25,
                      control_value=["63(mod)_pBA580", "Gal4-4(mod)_pBA582"])
    m = json.loads((out / "manifest.json").read_text())
    assert m["control_value"] == ["63(mod)_pBA580", "Gal4-4(mod)_pBA582"]
    assert "unassigned" in m["dropped_labels"]
    assert len(np.load(out / "public.npz")["perts"]) == 21


def test_cellforge_style_train_test_split():
    from genemila.data.real import external_splits
    perts = [f"G{i}" for i in range(1, 41)]
    label_to_key = {f"G{i}_g{j}": f"G{i}" for i in range(1, 41) for j in (1, 2)}
    test_labels = [f"G{i}_g1" for i in range(1, 9)] + ["control", "unknown_label"]
    train_labels = [lab for lab in label_to_key if lab not in test_labels]   # includes G1_g2 .. G8_g2
    s = external_splits({"train": train_labels, "test": test_labels}, perts, label_to_key, seed=3,
                        val_frac_of_train=0.25)
    assert s["val2"] == sorted(f"G{i}" for i in range(1, 9))         # their held-out set, exactly
    assert not set(s["val2"]) & set(s["train"])                      # a gene split across guides stays held out
    assert len(s["val1"]) == 8 and not set(s["val1"]) & set(s["train"])
    assert sorted(s["train"] + s["val1"] + s["val2"]) == sorted(perts)
    assert s == external_splits({"train": train_labels, "test": test_labels}, perts, label_to_key, seed=3)
