"""tools/external_loo.py: the free leave-one-out check of an external screen reads visible data only."""

import json
import os
import shutil
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
    for word in ("val1", "val2", "query_metrics", "query_only", "oracle", "private"):
        assert word not in src, word


_WATCHED: list[str] = []   # directory prefixes whose opens the audit hook records; empty = dormant
_OPENED: list[str] = []


def _audit(event, args):
    if event != "open" or not _WATCHED:
        return
    try:
        path = os.fsdecode(args[0]) if isinstance(args[0], (str, bytes, os.PathLike)) else None
    except Exception:
        return
    if path and any(path.startswith(w) for w in _WATCHED):
        _OPENED.append(path)


def test_runtime_never_opens_the_bundle_private_directory(dataset, tmp_path):
    """The string guard above cannot see a path built as Path(bundle) / 'private' / ..., so the full CLI is run on
    a bundle copy that does have a private directory, with an audit hook recording every open under the copy."""
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(dataset, bundle_dir)
    sealed = bundle_dir / "private"
    assert sealed.is_dir() and any(sealed.iterdir())
    bundle = _bundle(bundle_dir)
    name = _write_external(bundle_dir, "ext_guard", bundle, "signal")
    if not getattr(sys, "_external_loo_audit", False):
        sys.addaudithook(_audit)
        sys._external_loo_audit = True   # a hook cannot be removed; it is installed once and sleeps otherwise
    _OPENED.clear()
    _WATCHED[:] = [str(bundle_dir), str(bundle_dir.resolve())]
    try:
        assert external_loo.main(["--bundle", str(bundle_dir), "--knowledge", name, "--out",
                                  str(tmp_path / "guard.md")]) == 0
    finally:
        _WATCHED.clear()
    opened = {os.path.relpath(x, bundle_dir) if x.startswith(str(bundle_dir)) else
              os.path.relpath(x, bundle_dir.resolve()) for x in _OPENED}
    assert "public.npz" in opened and f"knowledge/{name}.json" in opened   # the hook does see the tool's reads
    assert not [x for x in opened if x.split(os.sep)[0] == "private"], sorted(opened)


@pytest.fixture(scope="module")
def public_dir(dataset, tmp_path_factory):
    """Only the public part of the synthetic bundle: the tool must run without anything else on disk."""
    return export_public(dataset, tmp_path_factory.mktemp("public") / "bundle")


def _bundle(public_dir):
    return external_loo.load_bundle(public_dir)


def _write_external(public_dir, name, bundle, mode, drop=(), zero_cells=(), unmeasured_every=10, seed=0):
    """A synthetic external screen in the format of tools/build_external_screen.py. mode 'signal': each
    target's external change is the bundle's own change, rescaled, plus small noise; 'noise': unrelated noise.
    Targets in `drop` get no row; targets in `zero_cells` get the row the builder writes for a label no cell
    carries (n_cells 0, delta = 0 minus the control mean); every unmeasured_every-th gene is unmeasured (null)."""
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
        if target in zero_cells:
            perts[target] = {"n_cells": 0, "labels": [target], "delta": masked(-bundle["control_mean"])}
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


def test_zero_cell_rows_are_treated_as_missing(public_dir):
    """A subset h5ad keeps every category of the genome-wide file, so the builder can write a bundle target with
    n_cells 0 and delta = -control_mean: the largest row in the file and no measurement at all."""
    bundle = _bundle(public_dir)
    perts = bundle["perts"]
    zero = {bundle["targets"][p][0] for p in perts[:3]}
    drop = {bundle["targets"][perts[3]][0]}
    name = _write_external(public_dir, "ext_zero", bundle, "signal", drop=drop, zero_cells=zero)
    raw = json.loads((public_dir / "knowledge" / f"{name}.json").read_text())
    assert all(raw["perts"][t]["n_cells"] == 0 for t in zero) and len(raw["perts"]) == len(perts) - len(drop)
    external = external_loo.load_external(public_dir, name, bundle["genes"])
    assert not (zero & set(external["rows"])) and sorted(external["zero_cell_targets"]) == sorted(zero)
    assert external["n_perts"] == len(perts) - len(drop) - len(zero)
    assert external["n_bundle_targets_missing"] == len(drop) + len(zero)
    rep = external_loo.analyse(bundle, external, k=5)
    n = rep["n_train"]
    assert rep["coverage"]["with_external_row"] == n - len(drop) - len(zero)
    assert sorted(rep["coverage"]["without_external_row"]) == sorted(perts[:4])
    assert rep["agreement"]["n"] == n - 4 and rep["agreement"]["min"] > 0.95
    assert rep["fallbacks"]["external_direct_no_row"] == rep["fallbacks"]["external_knn_no_row"] == 4
    assert sorted(rep["external_file"]["zero_cell_targets"]) == sorted(zero)
    for r in rep["per_perturbation"][:3]:   # exactly the no-row fallbacks, never a score against -control_mean
        s = r["scores"]
        assert s["external_direct"] == s["mean_response"] and s["external_knn"] == s["geneset_knn"]
        assert r["n_cells_external"] is None and r["agreement"] is None and r["n_genes_shared"] == 0
    md = external_loo.render(rep)
    assert f"{n - 4} of the {n} training perturbations have a row" in md
    assert f"The file also lists {len(zero)} bundle targets with zero cells" in md
    assert "such a row is no measurement and was treated as missing" in md
    # a file written without the field (an older twin) still renders
    rep["external_file"].pop("zero_cell_targets")
    assert "with zero cells" not in external_loo.render(rep)


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
    # the pre-specified grid carries no note; another grid is named as a second look (the section on the predictors
    # added after the first reading is always a second look, so the grid note itself is what is checked)
    assert "This grid is not the pre-specified one" not in md and rep["alpha_grid"] == list(external_loo.ALPHA_GRID)
    wide = tmp_path / "wide.md"
    assert external_loo.main(["--bundle", str(public_dir), "--knowledge", name, "--k", "3", "--out", str(wide),
                              "--alpha-grid", "1000", "1e5", "1e7"]) == 0
    w = json.loads(wide.with_suffix(".json").read_text())
    assert w["alpha_grid"] == [1000.0, 1e5, 1e7] and sum(w["alphas_chosen"].values()) == w["n_train"]
    assert "not the pre-specified one" in wide.read_text() and "second look" in wide.read_text()
    # external_stack_krr picks its alpha from that grid too, and both the note and its own section say so
    assert sum(w["alphas_chosen_stack_krr"].values()) == w["n_train"]
    note = wide.read_text().split("## Predictors")[0]
    assert "the other four predictors do not depend on it" not in note
    assert "external_stack_krr picks its alpha from this same grid and external_krr does not use it" in note
    assert ("chosen as for external_stack from the same grid [1000.0, 100000.0, 10000000.0] (not the pre-specified "
            "one" in wide.read_text().split("## Added after the first reading")[1])
    assert "(not the pre-specified one" not in md.split("## Added after the first reading")[1]
    assert ".." not in md.split("External screen:")[1].split("\n")[0]                # no doubled full stop


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


# ------------------------------------------------- added after the first reading: external_krr, external_stack_krr

V1 = ROOT / "tests" / "data" / "external_loo_v1"


def test_report_written_before_the_second_look_renders_byte_identical(tmp_path):
    """tests/data/external_loo_v1 holds a JSON twin and its markdown written by the code before external_krr existed
    (see the README there). The current code must render that JSON to exactly that markdown: an old twin re-rendered
    with --from-json never gains the added rows, columns or section."""
    rep = json.loads((V1 / "report.json").read_text())
    assert "added_after_first_reading" not in rep and len(rep["predictors"]) == 5
    assert external_loo.render(rep) == (V1 / "report.md").read_text()
    out = tmp_path / "again.md"
    subprocess.run([sys.executable, external_loo.__file__, "--from-json", str(V1 / "report.json"), "--out", str(out)],
                   check=True, capture_output=True)
    assert out.read_bytes() == (V1 / "report.md").read_bytes()
    # an old twin written with another grid keeps the grid note the old code wrote (the frozen one used the default)
    wide = external_loo.render({**rep, "alpha_grid": [1000.0, 1e5]})
    assert ("[1000.0, 100000.0]. This grid is not the pre-specified one ([0.1, 1.0, 10.0, 100.0, 1000.0]): it was "
            "chosen after an earlier reading, so the stack's number here is a second look, not a pre-specified result; "
            "the other four predictors do not depend on it.\n") in wide


def _latent_case(n=30, n_genes=200, rank=8, ext_noise=0.3, label_noise=0.2, seed=0):
    """A bundle and external screen in memory, in the shapes load_bundle and load_external return. Each perturbation
    has a hidden unit vector u; its change is u B plus noise and its external row u C plus noise, with B and C
    unrelated, so the external row of the same target says nothing gene by gene (external_direct is near 0) while
    the correlation of two external rows tracks u_p . u_q. Any response is then a linear mix of the others with
    weights of both signs given by external similarity: what kernel ridge can learn and top-k positive neighbours
    cannot."""
    rng = np.random.default_rng(seed)
    U = rng.normal(size=(n, rank))
    U /= np.linalg.norm(U, axis=1, keepdims=True)
    B, C = rng.normal(size=(rank, n_genes)), rng.normal(size=(rank, n_genes))
    genes = [f"G{j:03d}" for j in range(n_genes)]
    perts = [f"{g}_KO" for g in genes[:n]]
    measured = np.arange(n_genes) % 10 != 0
    rows = {}
    for i in range(n):
        x = U[i] @ C + rng.normal(0, ext_noise, n_genes)
        x[~measured] = np.nan
        rows[genes[i]] = x
    bundle = {"name": "latent", "genes": genes, "perts": perts,
              "deltas": U @ B + rng.normal(0, label_noise, (n, n_genes)), "control_mean": np.zeros(n_genes),
              "n_cells": [50] * n, "targets": {p: [genes[i]] for i, p in enumerate(perts)}, "gene_sets": {}}
    external = {"name": "ext_latent", "description": "latent test case", "source": {}, "measured": measured,
                "rows": rows, "n_cells": {g: 50 for g in rows}, "n_control_cells": 100, "n_perts": n,
                "n_bundle_targets_missing": 0, "zero_cell_targets": []}
    return bundle, external


def test_krr_beats_external_knn_when_responses_mix_with_signed_weights():
    bundle, external = _latent_case()
    rep = external_loo.analyse(bundle, external, k=5)
    n = rep["n_train"]
    m = _means(rep)
    P = {p["name"]: p for p in rep["predictors"]}
    assert abs(m["external_direct"]) < 0.15 and m["mean_response"] < 0.15        # nothing to copy, nothing shared
    assert m["external_knn"] > 0.6                                              # neighbours do carry information
    v = P["external_krr"]["vs_external_knn"]
    assert m["external_krr"] > m["external_knn"] + 0.08 and v["mean_diff"] > 3 * v["se_diff"] and v["wins"] >= 0.8 * n
    assert m["external_stack_krr"] > m["external_stack"] + 0.08
    assert P["external_stack_krr"]["vs_external_stack"]["wins"] >= 0.8 * n
    assert rep["fallbacks"]["external_krr_no_row"] == rep["fallbacks"]["external_krr_too_few_rows"] == 0
    assert P["external_krr"]["coverage"] == n and sum(rep["krr_lambdas_chosen"].values()) == n
    for r in rep["per_perturbation"]:
        assert r["krr_lambda"] in external_loo.LAMBDA_GRID and r["fallbacks"]["external_krr"] is None
        assert set(r["krr_inner_scores"]) == {str(lam) for lam in external_loo.LAMBDA_GRID}
        assert r["alpha_stack_krr"] in external_loo.ALPHA_GRID and len(r["stack_krr_weights"]) == 5
    # the weights kernel ridge puts on the other responses really are of both signs
    S = external_loo._prepare(bundle, external)
    Z, R = S["krr_z"], np.arange(1, n)
    lam = rep["per_perturbation"][0]["krr_lambda"]
    w = np.linalg.solve(Z[R] @ Z[R].T + lam * np.eye(n - 1), Z[R] @ Z[0])
    assert (w > 0.05).sum() >= 3 and (w < -0.05).sum() >= 3
    md = external_loo.render(rep)
    assert "| external_krr |" in md and "| external_stack_krr |" in md and "| KRR lambda |" in md
    tail = md.split("## Reading")[1]
    assert "## Added after the first reading (a second look)" in tail
    assert "designed after the first result of this check was seen" in tail
    assert "a second look, not pre-specified results" in tail
    assert f"better on {v['wins']} of {n}" in tail and "external_stack_krr scores" in tail


def test_krr_stays_near_the_mean_on_a_noise_screen(public_dir):
    bundle = _bundle(public_dir)
    name = _write_external(public_dir, "ext_noise_krr", bundle, "noise")
    rep = external_loo.analyse(bundle, external_loo.load_external(public_dir, name, bundle["genes"]), k=5)
    m = _means(rep)
    P = {p["name"]: p for p in rep["predictors"]}
    v = P["external_krr"]["vs_mean_response"]
    # unrelated external rows: kernel ridge shrinks to the mean change instead of chasing chance correlations
    assert abs(m["external_krr"] - m["mean_response"]) < 0.05 and abs(v["mean_diff"]) <= 2 * v["se_diff"]
    assert m["external_krr"] > m["external_knn"]                   # the neighbour rule does chase them
    assert m["external_stack_krr"] >= m["external_stack"] - 0.03
    assert sum(c for lam, c in rep["krr_lambdas_chosen"].items() if float(lam) >= 1.0) >= 0.8 * rep["n_train"]
    tail = external_loo.render(rep).split("## Added after the first reading (a second look)")[1]
    assert "external_krr scores" in tail


def test_krr_lambda_and_training_columns_never_see_the_held_out_label():
    bundle, external = _latent_case(n=16, n_genes=120, rank=4)
    S = external_loo._prepare(bundle, external)
    i = 5
    base = external_loo._fold(i, S, k=5)
    D2 = S["deltas"].copy()
    D2[i] = np.random.default_rng(1).normal(0, 5, D2.shape[1])   # the held-out perturbation's own label, replaced
    moved = external_loo._fold(i, {**S, "deltas": D2}, k=5)
    assert base["krr"]["lambda"] == moved["krr"]["lambda"] and base["krr"]["inner"] == moved["krr"]["inner"]
    assert np.array_equal(base["krr_col"], moved["krr_col"])
    assert base["train"] == moved["train"] and i not in base["train"]
    for a, b in zip(base["train_cols5"], moved["train_cols5"]):
        assert np.array_equal(a, b)
    assert base["alpha_krr"] == moved["alpha_krr"] and np.array_equal(base["stacked_krr"], moved["stacked_krr"])
    assert np.array_equal(base["stacked"], moved["stacked"])
    # the check has teeth: another training perturbation's label does reach the inner selection
    D3 = S["deltas"].copy()
    D3[base["train"][0]] = D2[i]
    other = external_loo._fold(i, {**S, "deltas": D3}, k=5)
    assert other["krr"]["inner"] != base["krr"]["inner"]
    assert not np.array_equal(other["train_cols5"][1], base["train_cols5"][1])


def test_krr_closed_form_matches_refitting():
    rng = np.random.default_rng(3)
    n, g = 12, 40
    X = rng.normal(size=(n, 3)) @ rng.normal(size=(3, g)) + 0.3 * rng.normal(size=(n, g))
    X[:, ::7] = np.nan                                             # unmeasured genes
    X[2, 5] = np.nan                                               # a null inside a measured gene
    Z, ok = external_loo._unit_rows(X, np.ones(n, dtype=bool))
    assert ok.all()
    K = Z @ Z.T
    np.testing.assert_allclose(np.diag(K), 1.0)
    assert np.linalg.eigvalsh(K).min() > -1e-10                       # positive semidefinite
    m = np.isfinite(X[0]) & np.isfinite(X[1])
    assert abs(K[0, 1] - external_loo.pearson_delta(X[0, m], X[1, m])) < 1e-12   # Pearson where rows share genes
    Y = rng.normal(size=(n, 30))                                   # labels; any will do for an identity
    ybars = rng.normal(size=(n, 30)) * 0.1
    closed = external_loo.krr_loo(K, Y, ybars)
    scores = external_loo.krr_loo_scores(K, Y, ybars)
    for lam in external_loo.LAMBDA_GRID:
        exact = external_loo.krr_loo_exact(K, Y, ybars, lam)
        np.testing.assert_allclose(closed[lam], exact, rtol=1e-8, atol=1e-10)
        ref = np.mean([external_loo.pearson_delta(exact[j], Y[j]) for j in range(n)])
        assert abs(scores[lam] - ref) < 1e-10
    # ties go to the larger lambda; a row without spread is unusable
    assert external_loo._choose_lambda({0.1: 0.5, 1.0: 0.5, 10.0: 0.4}) == 1.0
    flat = np.ones((2, g))
    flat[1] = np.nan
    assert not external_loo._unit_rows(flat, np.ones(2, dtype=bool))[1].any()


def test_krr_fallbacks_are_counted(public_dir):
    bundle = _bundle(public_dir)
    perts = bundle["perts"]
    n = len(perts)
    # half the targets without a row: exactly geneset_knn for those, and counted
    drop = {bundle["targets"][p][0] for p in perts[::2]}
    name = _write_external(public_dir, "ext_half_krr", bundle, "signal", drop=drop)
    rep = external_loo.analyse(bundle, external_loo.load_external(public_dir, name, bundle["genes"]), k=5)
    fb = rep["fallbacks"]
    assert fb["external_krr_no_row"] == len(drop) and fb["external_krr_too_few_rows"] == 0
    P = {p["name"]: p for p in rep["predictors"]}
    assert P["external_krr"]["coverage"] == n - len(drop)
    for r in rep["per_perturbation"]:
        if r["pert"] in perts[::2]:
            assert r["scores"]["external_krr"] == r["scores"]["geneset_knn"]
            assert r["fallbacks"]["external_krr"] == "no external row" and r["krr_lambda"] is None
            assert r["krr_inner_scores"] is None
        else:
            assert r["fallbacks"]["external_krr"] is None and r["krr_lambda"] in external_loo.LAMBDA_GRID
    assert sum(rep["krr_lambdas_chosen"].values()) == n - len(drop)
    tail = external_loo.render(rep).split("## Added after the first reading (a second look)")[1]
    assert f"no external row ({len(drop)} perturbations)" in tail
    # three rows in the file: each of the three sees only two others, too few for kernel ridge
    keep = [bundle["targets"][p][0] for p in perts[:3]]
    name = _write_external(public_dir, "ext_three_krr", bundle, "signal",
                           drop={bundle["targets"][p][0] for p in perts} - set(keep))
    rep = external_loo.analyse(bundle, external_loo.load_external(public_dir, name, bundle["genes"]), k=5)
    fb = rep["fallbacks"]
    assert fb["external_krr_no_row"] == n - 3 and fb["external_krr_too_few_rows"] == 3
    assert all(r["scores"]["external_krr"] == r["scores"]["geneset_knn"] for r in rep["per_perturbation"])
    assert all(c == 0 for c in rep["krr_lambdas_chosen"].values())
    tail = external_loo.render(rep).split("## Added after the first reading (a second look)")[1]
    assert "fewer than 3 other training perturbations have one (3)" in tail
    assert "Kernel ridge lambda chosen per fold: none (every fold fell back)" in tail
    # four rows: each sees three, enough
    keep4 = [bundle["targets"][p][0] for p in perts[:4]]
    name = _write_external(public_dir, "ext_four_krr", bundle, "signal",
                           drop={bundle["targets"][p][0] for p in perts} - set(keep4))
    rep = external_loo.analyse(bundle, external_loo.load_external(public_dir, name, bundle["genes"]), k=5)
    assert rep["fallbacks"]["external_krr_too_few_rows"] == 0 and rep["fallbacks"]["external_krr_no_row"] == n - 4
    assert sum(rep["krr_lambdas_chosen"].values()) == 4
