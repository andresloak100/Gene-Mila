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
    target gene), a combinatorial label, a label pairing a target with a gene the screen did not measure
    (ambiguous: it must not be pooled), an unrelated label, and two control labels."""
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
    cells(f"{t1}_ZZZ9", 6, t1, scale=2.0)         # t1 plus a gene the screen did not measure: ambiguous, skipped
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
        assert k["source"]["n_labels_ambiguous_skipped"] == 1                         # t1_ZZZ9, not pooled into t1
        assert k["source"]["labels_ambiguous_skipped"] == [f"{t['t1']}_ZZZ9"]
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
    assert f"(ambiguous, skipped): 1: {t['t1']}_ZZZ9" in out                       # named, not just counted
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
    with pytest.raises(ValueError, match="raw counts") as e:
        es.build(norm, dataset, "ext_norm", with_md5=False)
    assert "pass --already-normalised" in str(e.value)                                 # non-integer: the override applies
    a.X = sp.csr_matrix(np.minimum(X, 20.0))                                           # integers capped at 20
    capped = tmp_path / "capped.h5ad"
    a.write_h5ad(capped)
    with pytest.raises(ValueError, match="raw counts") as e:
        es.build(capped, dataset, "ext_capped", with_md5=False)
    assert "integers" in str(e.value) and "maximum is 20" in str(e.value)
    assert "pass --already-normalised" not in str(e.value)                             # integer data: not recommended
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
    cats = ["control", "ATF6", "xbp1_guide2", "HSPA5+ctrl", "ATF6_XBP1", "DDIT3", "ACTB_1", "NOTAGENE", "nt",
            "ATF6_ZZZ9", "ATF6+UNMEASUREDGENE", "XBP1 (1)", "hspa5_p1p2"]
    m = es.match_labels(cats, targets, ext_genes)
    assert sorted(m["control"]) == ["control", "nt"]
    assert m["by_target"] == {"ATF6": ["ATF6"], "HSPA5": ["HSPA5+ctrl", "hspa5_p1p2"], "XBP1": ["xbp1_guide2", "XBP1 (1)"]}
    assert m["missing"] == [] and m["multi_gene"] == ["ATF6_XBP1"] and m["n_other"] == 3
    assert m["ambiguous"] == ["ATF6+UNMEASUREDGENE", "ATF6_ZZZ9"]                  # a partner the screen did not measure
    assert "ATF6_ZZZ9" not in sum(m["by_target"].values(), [])
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


def test_count_detector_samples_the_most_populated_columns(tmp_path):
    """In a CSC file every spread window sits inside one column; the most populated columns (the highest
    expressed genes) must be sampled too, or a raw-count file whose sampled genes stay below 21 is refused."""
    import h5py
    import pandas as pd
    import scipy.sparse as sp
    rng = np.random.default_rng(3)
    n, g = 400, 40
    mu = np.full(g, 0.8)
    mu[23] = 60.0                                                     # one highly expressed gene in the middle
    X = rng.poisson(mu, size=(n, g)).astype(np.float32)
    assert X[:, [j for j in range(g) if j != 23]].max() <= 20 < X[:, 23].min()
    for layout, M in (("csc", sp.csc_matrix), ("csr", sp.csr_matrix)):
        path = tmp_path / f"probe_{layout}.h5ad"
        ad.AnnData(X=M(X), obs=pd.DataFrame(index=[f"c{i}" for i in range(n)]),
                   var=pd.DataFrame(index=[f"g{i}" for i in range(g)])).write_h5ad(path)
        with h5py.File(path, "r") as f:
            spread = es._sample_values(f, layout, n_windows=2, window=40, n_top=0)  # two small windows: the start and the end
            full = es._sample_values(f, layout, n_windows=2, window=40)
        assert es.integer_valued(spread) and es.integer_valued(full)
        if layout == "csc":
            assert not es.looks_like_counts(spread), spread.max()        # the spread windows alone miss the high gene
        assert es.looks_like_counts(full), (layout, full.max())


def test_row_chunks_respect_both_limits():
    indptr = np.array([0, 5, 5, 100, 101, 110, 200, 200])      # 7 rows
    chunks = list(es._row_chunks(7, chunk=3, chunk_nnz=50, indptr=indptr))
    assert chunks == [(0, 2), (2, 3), (3, 5), (5, 6), (6, 7)]  # row 2 alone exceeds the budget and still goes
    assert list(es._row_chunks(7, chunk=4, chunk_nnz=10 ** 9, indptr=indptr)) == [(0, 4), (4, 7)]
    assert list(es._row_chunks(7, chunk=4, chunk_nnz=25, n_genes=10)) == [(0, 2), (2, 4), (4, 6), (6, 7)]   # dense
    assert list(es._row_chunks(3, chunk=4, chunk_nnz=1, n_genes=10)) == [(0, 1), (1, 2), (2, 3)]
    assert sum(r1 - r0 for r0, r1 in es._row_chunks(1000, chunk=64, chunk_nnz=10, n_genes=3)) == 1000


def test_aliases_match_renamed_targets_and_genes(tmp_path):
    targets, ext_genes = ["SLMO2", "ATF6"], ["PRELID3B", "ATF6", "ATP5F1B", "ACTB"]
    cats = ["control", "PRELID3B_guide1", "ATF6", "PRELID3B_ATF6"]
    m = es.match_labels(cats, targets, ext_genes, aliases={"SLMO2": "PRELID3B", "ATP5B": "ATP5F1B"})
    assert m["by_target"] == {"ATF6": ["ATF6"], "SLMO2": ["PRELID3B_guide1"]} and m["via_alias"] == ["SLMO2"]
    assert m["multi_gene"] == ["PRELID3B_ATF6"]                                   # the alias is a gene of the screen
    assert es.match_labels(cats, targets, ext_genes)["missing"] == ["SLMO2"]      # without it the target is missing
    # genes: the bundle's own symbol first, then its alias, each exact before case-insensitive
    assert es.map_genes(["ATP5B", "ACTB", "GONE"], ext_genes, {"ATP5B": "ATP5F1B"}).tolist() == [2, 3, -1]
    assert es.map_genes(["ACTB"], ext_genes, {"ACTB": "ATF6"}).tolist() == [3]
    with pytest.raises(ValueError, match="another gene of the bundle"):
        es.map_genes(["ATP5B", "ATP5F1B"], ext_genes, {"ATP5B": "ATP5F1B"})        # two bundle genes on one column
    with pytest.raises(ValueError, match="same external gene"):
        es.map_genes(["A", "B"], ext_genes, {"A": "ACTB", "B": "actb"})
    f = tmp_path / "aliases.json"
    f.write_text(json.dumps({"SRPR": "SRPRA"}))
    assert es.parse_aliases([" SLMO2 = PRELID3B"], f) == {"SRPR": "SRPRA", "SLMO2": "PRELID3B"}
    for bad in ("SLMO2", "=X", "X="):
        with pytest.raises(ValueError, match="OLD=NEW"):
            es.parse_aliases([bad])
    f.write_text(json.dumps(["SRPR", "SRPRA"]))
    with pytest.raises(ValueError, match="JSON object"):
        es.parse_aliases(None, f)


OLD_KEYS = ["description", "source", "genes", "measured", "control", "perts", "bundle_targets_missing",
            "bundle_targets_below_min_cells"]


def test_modality_sign_and_the_bundles_modality(tmp_path):
    assert es.modality_sign("CRISPRi", "CRISPRa") == -1
    assert es.modality_sign(" crispri ", "CRISPRi") == 1                          # case and space do not count
    assert es.modality_sign("CRISPRi", None) == es.modality_sign(None, "CRISPRa") == es.modality_sign(None, None) == 1
    assert es.bundle_modality(tmp_path) is None                                    # no manifest
    (tmp_path / "manifest.json").write_text(json.dumps({"name": "x"}))
    assert es.bundle_modality(tmp_path) is None                                    # a bundle built before the field
    (tmp_path / "manifest.json").write_text(json.dumps({"name": "x", "modality": "CRISPRa"}))
    assert es.bundle_modality(tmp_path) == "CRISPRa"


def test_build_without_modality_writes_the_file_as_before(tmp_path, dataset):
    """No --modality: the keys (so the planner's 'dict of N entries' line), the description and the source are
    those every earlier file had; and every gene of a pair in targets.json is looked up in the screen."""
    import shutil
    bundle = tmp_path / "bundle"
    shutil.copytree(dataset, bundle)
    path, X, labels, genes, t = external_screen(tmp_path, bundle, "csr")
    targets = json.loads((bundle / "knowledge" / "targets.json").read_text())
    other = next(str(g) for g in np.load(bundle / "public.npz")["genes"] if str(g) not in es.bundle_targets(bundle))
    targets[f"{t['t1']}+{other}"] = [t["t1"], other]                                # a pair whose second gene has no single
    (bundle / "knowledge" / "targets.json").write_text(json.dumps(targets))
    assert other in es.bundle_targets(bundle)
    k = json.loads(es.build(path, bundle, "ext_plain", with_md5=False).read_text())
    assert list(k) == OLD_KEYS and "sign" not in k and "modality" not in k["source"]
    assert k["description"] == (
        "External screen deltas: perts[gene].delta = mean over cells of log1p(10,000 x counts / cell total) of that "
        "screen's cells of the perturbation minus its own control mean, over this bundle's genes in bundle order (null "
        f"where unmeasured there); source: Perturb-seq screen {path.name}.")
    assert other in k["bundle_targets_missing"] and t["t1"] in k["perts"]
    md = cli.render(k)
    assert "Screen modality" not in md and "(a knockdown should be negative)" in md
    assert es.build(path, bundle, "ext_blank", with_md5=False, modality="  ").read_text().count('"sign"') == 0


def test_build_with_modality_records_the_sign(tmp_path, dataset, capsys):
    import shutil
    bundle = tmp_path / "bundle"
    shutil.copytree(dataset, bundle)
    path, X, labels, genes, t = external_screen(tmp_path, bundle, "csr")
    plain = json.loads(es.build(path, bundle, "ext_plain", with_md5=False).read_text())
    # the session bundle records no modality: sign +1, and the description says so
    k = json.loads(es.build(path, bundle, "ext_i", with_md5=False, modality="CRISPRi").read_text())
    assert list(k) == ["description", "sign"] + OLD_KEYS[1:] and k["sign"] == 1
    assert k["description"].startswith("CRISPRi screen deltas, sign +1 (bundle modality not recorded): ")
    assert k["source"]["modality"] == "CRISPRi" and k["source"]["bundle_modality"] is None
    # a CRISPRa bundle: sign -1, the first 60 characters the planner reads say so, the deltas do not change
    manifest = json.loads((bundle / "manifest.json").read_text())
    (bundle / "manifest.json").write_text(json.dumps({**manifest, "modality": "CRISPRa"}))
    args = ["--h5ad", str(path), "--bundle", str(bundle), "--name", "ext_a", "--no-md5", "--modality", "CRISPRi",
            "--min-cells", "0"]                                                      # as build() defaults
    assert cli.main(args + ["--dry-run"]) == 0
    assert "- modality: screen CRISPRi, bundle CRISPRa; sign -1 would be written" in capsys.readouterr().out
    assert cli.main(args) == 0
    md = capsys.readouterr().out
    out = bundle / "knowledge" / "ext_a.json"
    k = json.loads(out.read_text())
    assert list(k)[:2] == ["description", "sign"] and k["sign"] == -1
    assert k["description"][:60] == "CRISPRi screen deltas, sign -1 (this bundle is CRISPRa): per"
    assert "multiply a target's delta by sign (-1)" in k["description"]
    assert k["source"]["modality"] == "CRISPRi" and k["source"]["bundle_modality"] == "CRISPRa"
    assert k["perts"] == plain["perts"] and k["control"] == plain["control"] and k["genes"] == plain["genes"]
    assert {**k["source"], "modality": None, "bundle_modality": None, "seconds": 0, "date": 0} == {
        **plain["source"], "modality": None, "bundle_modality": None, "seconds": 0, "date": 0}
    assert "Screen modality CRISPRi, bundle modality CRISPRa: sign -1, since the two differ" in md
    assert "the file's sign of -1 records that" in md
    again = tmp_path / "again.md"
    assert cli.main(["--from-json", str(out), "--report", str(again)]) == 0
    assert again.read_text() + "\n" == md
    # the leave-one-out tool reads the sign the builder wrote
    import external_loo
    assert external_loo.load_external(bundle, "ext_a", k["genes"])["sign"] == -1
    assert external_loo.load_external(bundle, "ext_plain", k["genes"])["sign"] == 1


def test_build_with_an_alias_and_a_cell_minimum(tmp_path, dataset, capsys):
    path, X, labels, genes, t = external_screen(tmp_path, dataset, "csr")
    bundle_genes = [str(g) for g in np.load(dataset / "public.npz")["genes"]]
    renamed = bundle_genes[3]                                                      # absent from the screen
    assert renamed not in genes
    args = ["--h5ad", str(path), "--bundle", str(dataset), "--name", "ext_alias", "--no-md5",
            "--alias", f"{renamed}=EXTRA0", "--min-cells", "20"]
    assert cli.main(args + ["--dry-run"]) == 0
    dry = capsys.readouterr().out
    assert f"genes measured through one: {renamed}" in dry and f"{t['t3']} (12)" in dry
    out = dataset / "knowledge" / "ext_alias.json"
    try:
        assert cli.main(args) == 0
        k = json.loads(out.read_text())
        i = bundle_genes.index(renamed)
        assert k["measured"][i] is True
        totals = X.sum(axis=1)
        N = np.log1p(X * (1e4 / totals)[:, None])
        j = genes.index("EXTRA0")
        ctrl = N[np.isin(labels, ["control", "non-targeting"])].mean(axis=0)
        assert abs(k["perts"][t["t1"]]["delta"][i] - (N[labels == t["t1"]].mean(axis=0)[j] - ctrl[j])) < 1e-4
        assert t["t3"] not in k["perts"] and k["bundle_targets_below_min_cells"] == {t["t3"]: 12}
        assert t["t3"] in k["bundle_targets_missing"] and set(k["perts"]) == {t["t1"], t["t2"]}
        assert k["source"]["aliases"] == {renamed: "EXTRA0"} and k["source"]["min_cells"] == 20
        assert k["source"]["aliases_matched"] == {"targets": [], "genes": [renamed]}
        md = capsys.readouterr().out
        assert f"Aliases (bundle symbol = screen symbol): {renamed}=EXTRA0" in md
        assert f"fewer than 20 cells in the screen get no row: {t['t3']} (12 cells)" in md
    finally:
        if out.exists():
            out.unlink()


def _as_nullable_strings(f, path: str) -> None:
    """Rewrite a string dataset of an open h5ad as the "nullable-string-array" group anndata 0.13 writes for string
    indexes and categories (values plus a mask); a no-op when the local anndata already wrote it that way."""
    import h5py
    if isinstance(f[path], h5py.Group):
        return
    data = [v.decode() if isinstance(v, bytes) else str(v) for v in f[path][...].tolist()]
    del f[path]
    g = f.create_group(path)
    g.attrs["encoding-type"] = "nullable-string-array"
    g.attrs["encoding-version"] = "0.1.0"
    g.create_dataset("values", data=np.array(data, dtype=object), dtype=h5py.string_dtype())
    g.create_dataset("mask", data=np.zeros(len(data), dtype=bool))


def _as_plain_strings(f, path: str) -> None:
    """The reverse: an encoded string group rewritten as the plain string dataset older anndata wrote (masked
    entries as ''); a no-op on a plain dataset."""
    import h5py
    node = f[path]
    if isinstance(node, h5py.Dataset):
        return
    data = [v.decode() if isinstance(v, bytes) else str(v) for v in node["values"][...].tolist()]
    if "mask" in node:
        data = ["" if m else v for v, m in zip(data, np.asarray(node["mask"][...], dtype=bool).tolist())]
    del f[path]
    d = f.create_dataset(path, data=np.array(data, dtype=object), dtype=h5py.string_dtype())
    d.attrs["encoding-type"] = "string-array"
    d.attrs["encoding-version"] = "0.2.0"


@pytest.mark.filterwarnings("ignore::Warning")
@pytest.mark.parametrize("reader", ["anndata", "fallback"])
def test_a_screen_written_by_a_newer_anndata_reads_the_same(tmp_path, dataset, monkeypatch, reader):
    """anndata 0.13 stores a string var index and categorical categories as encoded groups, not datasets (the
    Mac's suite failed on [...] of a group, 11 Oct 2026): the gene symbols, the labels and the built file must
    equal those of the same screen stored the old way, through anndata's reader or the direct fallback. The two
    copies are made from whatever the local anndata wrote, so the test means the same under either anndata."""
    import h5py
    import shutil
    bundle = tmp_path / "bundle"                     # builds write into knowledge/: never into the shared fixture
    shutil.copytree(dataset, bundle)
    path, X, labels, genes, t = external_screen(tmp_path, bundle, "csr")
    old, new = tmp_path / "screen_old_encoding.h5ad", tmp_path / "screen_new_encoding.h5ad"
    for copy, rewrite in ((old, _as_plain_strings), (new, _as_nullable_strings)):
        shutil.copy(path, copy)
        with h5py.File(copy, "r+") as f:
            index_name = f["var"].attrs.get("_index", "_index")
            index_name = index_name.decode() if isinstance(index_name, bytes) else index_name
            rewrite(f, f"var/{index_name}")
            rewrite(f, "obs/perturbation/categories")
    with h5py.File(old, "r") as f:
        assert isinstance(f["var"][index_name], h5py.Dataset)
    with h5py.File(new, "r") as f:
        assert isinstance(f["var"][index_name], h5py.Group)
    if reader == "fallback":
        import anndata.io

        def refuse(elem, *a, **k):
            raise NotImplementedError("an anndata that predates the encoding")
        monkeypatch.setattr(anndata.io, "read_elem", refuse)
    with h5py.File(old, "r") as old_f, h5py.File(new, "r") as new_f:
        assert es.read_gene_symbols(new_f) == es.read_gene_symbols(old_f) == ("_index", genes)
        old_lab, new_lab = es.read_label_codes(old_f), es.read_label_codes(new_f)
        assert new_lab[0] == old_lab[0] and new_lab[1] == old_lab[1] == sorted(set(labels.tolist()))
        np.testing.assert_array_equal(new_lab[2], old_lab[2])
    monkeypatch.undo()
    a = json.loads(es.build(old, bundle, "ext_old", with_md5=False).read_text())
    b = json.loads(es.build(new, bundle, "ext_new", with_md5=False).read_text())
    assert a["perts"] == b["perts"] and a["genes"] == b["genes"] and a["measured"] == b["measured"]
