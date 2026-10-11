"""tools/external_loo.py: the free leave-one-out check of an external screen reads visible data only."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import external_loo  # noqa: E402

from genemila.data.bundle import export_public  # noqa: E402


def test_never_reads_the_sealed_labels():
    src = (ROOT / "tools" / "external_loo.py").read_text()
    for word in ("val2", "query_metrics", "query_only", "oracle", "private/"):
        assert word not in src, word


@pytest.fixture(scope="module")
def public_dir(dataset, tmp_path_factory):
    """Only the public part of the synthetic bundle: the tool must run without anything else on disk."""
    return export_public(dataset, tmp_path_factory.mktemp("public") / "bundle")


def _bundle(public_dir):
    return external_loo.load_bundle(public_dir)


def _write_external(public_dir, name, bundle, mode, drop=(), unmeasured_every=10, seed=0):
    """A synthetic external screen in the format of tools/build_external_screen.py. mode 'signal': each
    target's external change is the bundle's own change, rescaled, plus small noise; 'noise': unrelated noise.
    Targets in `drop` get no row; every unmeasured_every-th gene is unmeasured (null)."""
    rng = np.random.default_rng(seed)
    genes, D = bundle["genes"], bundle["deltas"]
    measured = [j % unmeasured_every != 0 for j in range(len(genes))]

    def masked(v):
        return [float(x) if m else None for m, x in zip(measured, v)]

    perts = {}
    for i, p in enumerate(bundle["perts"]):
        target = bundle["targets"][p][0]
        if target in drop:
            continue
        if mode == "signal":
            d = 1.7 * D[i] + rng.normal(0, 0.1 * D[i].std(), len(genes))
        else:
            d = rng.normal(0, 0.3, len(genes))
        perts[target] = {"n_cells": 100 + i, "labels": [target], "delta": masked(d)}
    rec = {"description": f"synthetic external screen ({mode})", "source": {"file": "x.h5ad"}, "genes": genes,
           "measured": measured, "control": {"n_cells": 1000, "mean": masked(bundle["control_mean"])},
           "perts": perts, "bundle_targets_missing": sorted(drop)}
    (public_dir / "knowledge" / f"{name}.json").write_text(json.dumps(rec))
    return name


def _means(rep):
    return {p["name"]: p["mean"] for p in rep["predictors"]}


def test_signal_external_beats_mean_response_and_gene_sets(public_dir):
    bundle = _bundle(public_dir)
    name = _write_external(public_dir, "ext_signal", bundle, "signal")
    external = external_loo.load_external(public_dir, name, bundle["genes"])
    assert external["measured"].sum() == len(bundle["genes"]) - len(range(0, len(bundle["genes"]), 10))
    rep = external_loo.analyse(bundle, external, k=5)
    n = rep["n_train"]
    assert n == len(bundle["perts"]) and rep["coverage"]["with_external_row"] == n
    m = _means(rep)
    # the external change is the truth plus a little noise: the direct predictor and the stack must be near 1,
    # the external neighbour rule must clearly beat the floor and the gene-set neighbour rule
    assert m["external_direct"] > 0.9 and m["external_direct"] > m["mean_response"] + 0.2
    assert m["external_stack"] > m["external_direct"] - 0.03
    assert m["external_knn"] > m["mean_response"] + 0.05 and m["external_knn"] > m["geneset_knn"] + 0.03
    P = {p["name"]: p for p in rep["predictors"]}
    assert P["external_direct"]["vs_mean_response"]["wins"] == n
    assert P["external_knn"]["vs_mean_response"]["wins"] >= 0.8 * n
    assert P["external_stack"]["vs_geneset_knn"]["wins"] >= 0.9 * n
    fb = rep["fallbacks"]
    assert fb["external_direct_no_row"] == fb["external_knn_no_row"] == fb["external_knn_no_positive_neighbour"] == 0
    assert rep["agreement"]["n"] == n and rep["agreement"]["min"] > 0.95
    for r in rep["per_perturbation"]:
        assert all(np.isfinite(v) for v in r["scores"].values())
        assert r["n_genes_shared"] == int(external["measured"].sum())  # unmeasured genes are filled, not scored
        assert r["n_cells_bundle"] == 40 and r["n_cells_external"] >= 100 and r["alpha"] in rep["alpha_grid"]
    md = external_loo.render(rep)
    assert "The external screen adds information beyond the gene sets on this check" in md
    assert f"{n} of the {n} training perturbations have a row" in md
    assert "confirmed on the sealed set by a labelled arm" in md


def test_noise_external_does_not_help_and_stack_holds(public_dir):
    bundle = _bundle(public_dir)
    name = _write_external(public_dir, "ext_noise", bundle, "noise")
    rep = external_loo.analyse(bundle, external_loo.load_external(public_dir, name, bundle["genes"]), k=5)
    m = _means(rep)
    P = {p["name"]: p for p in rep["predictors"]}
    n = rep["n_train"]
    # an unrelated screen: the direct predictor is near zero, the neighbour rule is a noisier floor, and the
    # stack learns to ignore the two external columns
    assert abs(m["external_direct"]) < 0.2 and m["external_direct"] < m["mean_response"] - 0.2
    assert m["external_knn"] <= m["mean_response"] + 2 * P["external_knn"]["vs_mean_response"]["se_diff"]
    assert m["external_stack"] >= m["geneset_knn"] - 0.05
    assert P["external_knn"]["vs_geneset_knn"]["wins"] < n / 2
    assert rep["agreement"]["n"] == n and abs(rep["agreement"]["median"]) < 0.3
    md = external_loo.render(rep)
    assert "The external screen adds information beyond the gene sets" not in md
    assert "No clear gain beyond the gene sets" in md or "The external predictors are behind the gene sets" in md


def test_missing_targets_fall_back_and_are_counted(public_dir):
    bundle = _bundle(public_dir)
    perts = bundle["perts"]
    drop = {bundle["targets"][p][0] for p in perts[::2]}
    name = _write_external(public_dir, "ext_half", bundle, "signal", drop=drop)
    external = external_loo.load_external(public_dir, name, bundle["genes"])
    assert external["n_bundle_targets_missing"] == len(drop) and external["n_perts"] == len(perts) - len(drop)
    rep = external_loo.analyse(bundle, external, k=5)
    n = rep["n_train"]
    assert rep["coverage"]["with_external_row"] == n - len(drop)
    assert sorted(rep["coverage"]["without_external_row"]) == sorted(perts[::2])
    fb = rep["fallbacks"]
    assert fb["external_direct_no_row"] == fb["external_knn_no_row"] == len(drop)
    assert rep["agreement"]["n"] == n - len(drop)
    P = {p["name"]: p for p in rep["predictors"]}
    assert P["external_direct"]["coverage"] == n - len(drop) and P["mean_response"]["coverage"] == n
    for r in rep["per_perturbation"]:
        s = r["scores"]
        if r["pert"] in perts[::2]:   # no external row: exactly the fallbacks, and dashes in the table
            assert s["external_direct"] == s["mean_response"] and s["external_knn"] == s["geneset_knn"]
            assert r["n_cells_external"] is None and r["agreement"] is None and r["n_genes_shared"] == 0
            assert r["fallbacks"]["external_direct"] == r["fallbacks"]["external_knn"] == "no external row"
        else:
            assert s["external_direct"] > s["mean_response"] and r["agreement"] > 0.95
            assert r["fallbacks"]["external_direct"] is None
    md = external_loo.render(rep)
    assert f"external_direct used mean_response for {len(drop)} perturbations without an external row" in md
    assert f"{n - len(drop)} of the {n} training perturbations have a row" in md
    first_missing = next(r for r in rep["per_perturbation"] if r["pert"] in perts[::2])
    assert f"| {first_missing['pert']} | {first_missing['target']} | 40 | – | 0 | – |" in md


def test_cli_and_from_json_rerender_byte_identical(public_dir, tmp_path):
    bundle = _bundle(public_dir)
    name = _write_external(public_dir, "ext_cli", bundle, "signal", drop={bundle["targets"][bundle["perts"][0]][0]})
    out = tmp_path / "report.md"
    assert external_loo.main(["--bundle", str(public_dir), "--knowledge", name, "--k", "3", "--out", str(out)]) == 0
    md = out.read_text()
    twin = out.with_suffix(".json")
    rep = json.loads(twin.read_text())
    assert rep["k"] == 3 and rep["knowledge"] == name and rep["coverage"]["with_external_row"] == rep["n_train"] - 1
    assert "runtime_s" in rep and rep["runtime_s"] < 60
    assert "(k = 3 for both neighbour rules)" in md
    again = tmp_path / "sub" / "again.md"
    subprocess.run([sys.executable, external_loo.__file__, "--from-json", str(twin), "--out", str(again)],
                   check=True, capture_output=True)
    assert again.read_bytes() == out.read_bytes() and not again.with_suffix(".json").exists()
    # the twin can be named, and the two input modes are exclusive
    named = tmp_path / "named.json"
    assert external_loo.main(["--bundle", str(public_dir), "--knowledge", name + ".json", "--k", "3",
                              "--out", str(tmp_path / "b.md"), "--json", str(named)]) == 0
    b = json.loads(named.read_text())
    b.pop("runtime_s"), rep.pop("runtime_s")
    assert b == rep
    with pytest.raises(SystemExit):
        external_loo.main(["--from-json", str(twin), "--bundle", str(public_dir), "--knowledge", name,
                           "--out", str(tmp_path / "c.md")])


def test_knn_and_stack_helpers():
    D = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [5.0, 5.0, 5.0]])
    # top-k positive weights only; NaN and non-positive weights never count
    np.testing.assert_allclose(external_loo._knn(np.array([3.0, 1.0, np.nan, -2.0]), D, k=2), [0.75, 0.25, 0.0])
    np.testing.assert_allclose(external_loo._knn(np.array([3.0, 1.0, 0.5, 0.0]), D, k=5), [6 / 9, 2 / 9, 1 / 9])
    assert external_loo._knn(np.array([0.0, -1.0, np.nan, 0.0]), D, k=3) is None
    # the stack recovers a column that is the target up to scale and offset, whatever the other columns hold
    rng = np.random.default_rng(0)
    cols, ys = [], []
    for _ in range(8):
        y = rng.normal(size=200)
        cols.append(np.stack([rng.normal(size=200), rng.normal(size=200), 3.0 * y + 1.0, rng.normal(size=200)]))
        ys.append(y)
    y_test = rng.normal(size=200)
    test = np.stack([rng.normal(size=200), rng.normal(size=200), 3.0 * y_test + 1.0, rng.normal(size=200)])
    pred, alpha, fit = external_loo._stack(cols, ys, test)
    assert external_loo.pearson_delta(pred, y_test) > 0.99 and alpha == 0.1
    assert abs(fit["weights"][2]) > 5 * max(abs(fit["weights"][j]) for j in (0, 1, 3))
    # a constant column (every row fell back to the same thing) does not break the fit
    flat = [np.stack([c[0], c[1], c[2], np.ones(200)]) for c in cols]
    pred2, _, _ = external_loo._stack(flat, ys, np.stack([test[0], test[1], test[2], np.ones(200)]))
    assert external_loo.pearson_delta(pred2, y_test) > 0.99
