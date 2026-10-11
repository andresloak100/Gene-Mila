"""genemila/data/external_screen.py and tools/build_external_screen.py: an external Perturb-seq screen becomes a
knowledge file (per target gene, the external delta over the bundle's genes), streamed from the h5ad."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_external_screen as cli  # noqa: E402

from genemila.data import external_screen as es  # noqa: E402

ad = pytest.importorskip("anndata")


def test_source_never_names_the_sealed_labels():
    for rel in ("genemila/data/external_screen.py", "tools/build_external_screen.py"):
        src = (ROOT / rel).read_text()
        for word in ("val2", "query_only", "oracle", "private/"):
            assert word not in src, (rel, word)


def external_screen(tmp_path, dataset, layout, ensembl_index=False, seed=0):
    """A raw-count screen over most of the bundle's genes (shuffled order) plus extra genes, with three bundle
    targets (one pooled over two labels, one written in lower case with a guide suffix, one equal to the
    target gene), a combinatorial label, an unrelated label, and two control labels."""
    import pandas as pd
    import scipy.sparse as sp
    rng = np.random.default_rng(seed)
    bundle_genes = [str(g) for g in np.load(dataset / "public.npz")["genes"]]
    targets = sorted({g for gs in json.loads((dataset / "knowledge" / "targets.json").read_text()).values() for g in gs})
    t1, t2, t3, t4 = targets[:4]
    present = [g for g in bundle_genes if g not in (bundle_genes[3], bundle_genes[7], t4)]  # t4 is a bundle target unmeasured here
    rng.shuffle(present)
    genes = present[:len(present) // 2] + [f"EXTRA{i}" for i in range(15)] + present[len(present) // 2:]
    base = rng.gamma(2.0, 3.0, len(genes))
    gi = {g: i for i, g in enumerate(genes)}
    rows, labels = [], []

    def cells(label, n, target=None, scale=1.0):
        mu = base * scale
        if target is not None and target in gi:
            mu = mu.copy()
            mu[gi[target]] *= 0.1
            mu[(gi[target] + 1) % len(genes)] *= 3.0
        rows.append(rng.poisson(mu, size=(n, len(genes))))
        labels.extend([label] * n)

    cells("control", 60)
    cells("non-targeting", 20, scale=1.3)       # a second control label, different depth
    cells(t1, 25, t1)                             # label equal to the target gene
    cells(f"{t2.lower()}_guide1", 15, t2)         # lower case plus a guide suffix
    cells(f"{t2}+guide2", 10, t2, scale=0.7)      # pooled with the one above
    cells(f"{t3}_ctrl", 12, t3)                   # GEARS-style suffix
    cells(f"{t1}_{t3}", 9, t1)                    # two genes: a combinatorial perturbation, skipped
    cells("EXTRA2", 8, "EXTRA2")                  # a gene the bundle does not target: ignored
    cells("NOTAGENE", 5)                          # unknown label: ignored
    X = np.vstack(rows).astype(np.float32)
    M = {"csr": sp.csr_matrix, "csc": sp.csc_matrix, "dense": np.asarray}[layout](X)
    obs = pd.DataFrame({"perturbation": pd.Categorical(labels)}, index=[f"c{i}" for i in range(len(labels))])
    if ensembl_index:
        var = pd.DataFrame({"gene_name": genes}, index=[f"ENSG{i:08d}" for i in range(len(genes))])
    else:
        var = pd.DataFrame(index=genes)
    a = ad.AnnData(X=M, obs=obs, var=var)
    path = tmp_path / f"screen_{layout}.h5ad"
    a.write_h5ad(path)
    return path, X, np.array(labels), genes, {"t1": t1, "t2": t2, "t3": t3, "t4": t4}


def dense_reference(X, labels, genes, bundle_genes, groups):
    """What the knowledge file must contain: per cell counts per 10k then log1p, mean per group, minus the
    control mean; None where the bundle gene is absent."""
    totals = X.sum(axis=1)
    N = np.log1p(X * (1e4 / np.where(totals > 0, totals, 1.0))[:, None])
    col = {g: i for i, g in enumerate(genes)}
    ctrl = N[np.isin(labels, groups["control"])].mean(axis=0)
    out = {}
    for t, labs in groups.items():
        if t == "control":
            continue
        delta = N[np.isin(labels, labs)].mean(axis=0) - ctrl
        out[t] = [None if g not in col else float(delta[col[g]]) for g in bundle_genes]
    return ctrl, out, col


@pytest.mark.parametrize("layout", ["csr", "csc", "dense"])
def test_deltas_match_a_dense_computation(tmp_path, dataset, layout):
    path, X, labels, genes, t = external_screen(tmp_path, dataset, layout, ensembl_index=(layout == "csc"))
    bundle_genes = [str(g) for g in np.load(dataset / "public.npz")["genes"]]
    groups = {"control": ["control", "non-targeting"], t["t1"]: [t["t1"]],
              t["t2"]: [f"{t['t2'].lower()}_guide1", f"{t['t2']}+guide2"], t["t3"]: [f"{t['t3']}_ctrl"]}
    ctrl_ref, ref, col = dense_reference(X, labels, genes, bundle_genes, groups)
    # small chunks so every layout runs through several chunks (and CSC batches split on the value budget)
    out = es.build(path, dataset, f"ext_{layout}", chunk=7, chunk_nnz=400, with_md5=(layout == "csr"))
    assert out == dataset / "knowledge" / f"ext_{layout}.json"
    try:
        k = json.loads(out.read_text())
        assert list(k)[0] == "description"                                            # the planner reads the first key
        assert k["description"].startswith("External screen deltas") and path.name in k["description"]
        assert k["genes"] == bundle_genes
        assert k["measured"] == [g in col for g in bundle_genes]
        assert k["source"]["encoding"] == layout and k["source"]["raw_counts"] is True
        assert k["source"]["n_cells"] == X.shape[0] and k["source"]["n_genes"] == len(genes)
        assert k["source"]["gene_col"] == ("gene_name" if layout == "csc" else "_index")
        assert sorted(k["source"]["control_labels"]) == ["control", "non-targeting"]
        assert k["source"]["md5"] == (es.md5_file(path) if layout == "csr" else None)
        assert k["control"]["n_cells"] == 80
        for g, m in zip(bundle_genes, k["control"]["mean"]):
            if g in col:
                assert abs(m - ctrl_ref[col[g]]) < 1e-4
            else:
                assert m is None
        assert sorted(k["perts"]) == sorted(ref)
        assert k["perts"][t["t1"]]["n_cells"] == 25 and k["perts"][t["t1"]]["labels"] == [t["t1"]]
        assert k["perts"][t["t2"]]["n_cells"] == 25                                   # pooled by cell count
        assert sorted(k["perts"][t["t2"]]["labels"]) == sorted(groups[t["t2"]])
        assert k["perts"][t["t3"]]["n_cells"] == 12
        for target, deltas in ref.items():
            got = k["perts"][target]["delta"]
            assert len(got) == len(bundle_genes)
            for g, a, b in zip(bundle_genes, got, deltas):
                if b is None:
                    assert a is None, (target, g)
                else:
                    assert abs(a - b) < 1e-4, (target, g, a, b)
        assert t["t4"] in k["bundle_targets_missing"] and t["t1"] not in k["bundle_targets_missing"]
        assert k["source"]["n_labels_multi_gene_skipped"] == 1                        # t1_t3
        assert k["source"]["n_labels_other"] == 2                                     # EXTRA2, NOTAGENE
        assert k["source"]["n_cells_used"] == 80 + 25 + 25 + 12
        md = cli.render(k)
        assert f"| {t['t2']} | 25 |" in md and "largest deltas" in md
        assert cli.render(json.loads(out.read_text())) == md                          # deterministic re-render
    finally:
        out.unlink()


def test_dry_run_writes_nothing_and_reports_the_matching(tmp_path, dataset, capsys):
    path, X, labels, genes, t = external_screen(tmp_path, dataset, "csr")
    before = sorted(p.name for p in (dataset / "knowledge").iterdir())
    assert cli.main(["--h5ad", str(path), "--bundle", str(dataset), "--name", "ext_dry", "--dry-run"]) == 0
    assert sorted(p.name for p in (dataset / "knowledge").iterdir()) == before
    out = capsys.readouterr().out
    assert "control labels: ['control', 'non-targeting'] (80 cells)" in out
    assert "bundle targets found: 3 of" in out and t["t4"] in out and "(skipped): 1" in out
    assert f"| {t['t2']} |" in out and "| 25 |" in out


def test_cli_build_force_and_from_json(tmp_path, dataset):
    path, X, labels, genes, t = external_screen(tmp_path, dataset, "csr")
    out = dataset / "knowledge" / "ext_cli.json"
    report = tmp_path / "r" / "report.md"
    try:
        args = ["--h5ad", str(path), "--bundle", str(dataset), "--name", "ext_cli", "--no-md5", "--report", str(report)]
        assert cli.main(args) == 0 and out.exists()
        md = report.read_text()
        assert md.startswith(f"# External screen {path.name}") and "## Reading" in md
        with pytest.raises(FileExistsError):
            cli.main(args)                                                             # refuses to overwrite
        assert cli.main(args + ["--force"]) == 0
        again = tmp_path / "again.md"
        assert cli.main(["--from-json", str(out), "--report", str(again)]) == 0
        assert again.read_text() == md
    finally:
        if out.exists():
            out.unlink()


def test_refuses_non_counts_unless_already_normalised(tmp_path, dataset):
    path, X, labels, genes, t = external_screen(tmp_path, dataset, "csr")
    a = ad.read_h5ad(path)
    import scipy.sparse as sp
    a.X = sp.csr_matrix(np.log1p(X / 3.0))
    norm = tmp_path / "normalised.h5ad"
    a.write_h5ad(norm)
    with pytest.raises(ValueError, match="raw counts"):
        es.build(norm, dataset, "ext_norm", with_md5=False)
    out = es.build(norm, dataset, "ext_norm", already_normalised=True, with_md5=False)
    try:
        k = json.loads(out.read_text())
        assert k["source"]["raw_counts"] is False and "already normalised" in k["source"]["normalisation"]
        bundle_genes = k["genes"]
        N = np.log1p(X / 3.0)
        col = {g: i for i, g in enumerate(genes)}
        ctrl = N[np.isin(labels, ["control", "non-targeting"])].mean(axis=0)
        delta = N[labels == t["t1"]].mean(axis=0) - ctrl
        for g, v in zip(bundle_genes, k["perts"][t["t1"]]["delta"]):
            if g in col:
                assert abs(v - delta[col[g]]) < 1e-4
    finally:
        out.unlink()


def test_label_matching_rules():
    targets = ["ATF6", "XBP1", "HSPA5"]
    ext_genes = ["ATF6", "XBP1", "HSPA5", "DDIT3", "ACTB"]
    cats = ["control", "ATF6", "xbp1_guide2", "HSPA5+ctrl", "ATF6_XBP1", "DDIT3", "ACTB_1", "NOTAGENE", "nt"]
    m = es.match_labels(cats, targets, ext_genes)
    assert sorted(m["control"]) == ["control", "nt"]
    assert m["by_target"] == {"ATF6": ["ATF6"], "HSPA5": ["HSPA5+ctrl"], "XBP1": ["xbp1_guide2"]}
    assert m["missing"] == [] and m["multi_gene"] == ["ATF6_XBP1"] and m["n_other"] == 3
    m2 = es.match_labels(cats, targets, ext_genes, control=["control"])        # an explicit control list replaces detection
    assert m2["control"] == ["control"] and m2["n_other"] == 4
    with pytest.raises(ValueError, match="not found"):
        es.match_labels(cats, targets, ext_genes, control=["nope"])
    with pytest.raises(ValueError, match="control"):
        es.match_labels(["ATF6", "XBP1"], targets, ext_genes)
    assert es.map_genes(["ATF6", "actb", "GONE"], ext_genes).tolist() == [0, 4, -1]


def test_column_chunks_respect_both_limits():
    indptr = np.array([0, 5, 5, 100, 101, 110, 200, 200])      # 7 columns
    cols = np.arange(7)
    batches = [b.tolist() for b in es._column_chunks(indptr, cols, max_cols=3, max_nnz=50)]
    assert batches == [[0, 1], [2], [3, 4], [5], [6]]           # column 2 alone exceeds the budget and still goes
    assert [b.tolist() for b in es._column_chunks(indptr, np.array([1, 2, 4, 5]), max_cols=10, max_nnz=10 ** 9)] == [[1, 2, 4, 5]]
    assert list(es._runs(np.array([1, 2, 4, 5, 9]))) == [(1, 3, 0), (4, 6, 2), (9, 10, 4)]
