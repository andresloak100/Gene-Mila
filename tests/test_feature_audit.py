"""tools/feature_audit.py: the visible scoring engine (ridge on Gram matrices, scores from per-perturbation
sufficient statistics, honest cross-seed penalty, paired comparisons), the one-SE compact choice made on training
perturbations only, redundancy, Lasso stability with a fold-honest penalty, the merge test and the verdicts; plugins
loaded file by file and label dependence detected per feature; end to end on a finished run it writes the report,
its JSON twin and the failed-feature box, re-renders byte for byte, leaves the run directory untouched, survives a
broken plugin, resumes from checkpoints, and reads the sealed set only through two queries of its own oracle when
asked."""

import ast
import gc
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import feature_audit as fa  # noqa: E402

from genemila.benchmark.evaluator import _pearson  # noqa: E402
from genemila.benchmark.oracle import QueryOracle  # noqa: E402
from genemila.data.bundle import LabelSet  # noqa: E402
from genemila.features.api import REGISTRY, FeatureContext  # noqa: E402
from genemila.pipeline import cv_folds_of  # noqa: E402

TOOL = ROOT / "tools" / "feature_audit.py"


# ------------------------------------------------------------------ hygiene
def test_source_never_names_the_sealed_labels_and_fences_the_oracle():
    src = TOOL.read_text()
    for word in ("val2", "query_only", "splits.json"):
        assert word not in src, word
    for word in ("refit_visible", "open_run", "genemila.db", "Database("):
        assert word not in src, word
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "score_sealed")
    lines = [i for i, line in enumerate(src.splitlines(), start=1) if "QueryOracle" in line]
    assert lines and all(fn.lineno <= i <= fn.end_lineno for i in lines), lines


# ------------------------------------------------------------------ the engine
def test_pearson_rows_matches_the_evaluator():
    rng = np.random.default_rng(0)
    P, Y = rng.normal(size=(7, 50)), rng.normal(size=(7, 50))
    P[3] = 2.5  # a constant prediction scores 0, as in the evaluator
    got = fa.pearson_rows(P, Y)
    assert np.allclose(got, [_pearson(P[i], Y[i]) for i in range(7)], atol=1e-12) and got[3] == 0.0
    stacked = fa.pearson_rows(np.stack([P, -P]), Y)  # leading axes broadcast
    assert np.allclose(stacked[0], got) and np.allclose(stacked[1], -got)




def test_ridge_on_the_gram_matrix_equals_sklearn_ridge():
    from sklearn.linear_model import LinearRegression, Ridge
    rng = np.random.default_rng(1)
    X = rng.normal(size=(400, 6)) * [1, 3, 0.1, 10, 1, 2] + [0, 5, -2, 1, 0, 3]
    X[:, 5] = 0.7 * X[:, 1] + 0.1 * rng.normal(size=400)  # correlated columns
    y = X @ [0.5, -1, 2, 0.05, 0, 0.3] + rng.normal(size=400)
    Xo = rng.normal(size=(90, 6)) * 2
    unit = fa.make_unit(X, y, Xo, rng.normal(size=(3, 30)))
    Xs, (Xos,), _, _ = fa.standardise(X, Xo)
    for idx in ([0, 1, 2, 3, 4, 5], [1, 3, 5]):
        for alpha in (0.5, 30.0, 1e4):
            sk = Ridge(alpha=alpha, fit_intercept=True).fit(Xs[:, idx], y)
            w = fa.ridge_weights(unit.G, unit.b, idx, alpha)
            assert np.allclose(w, sk.coef_, atol=1e-6) and unit.ybar == pytest.approx(sk.intercept_, abs=1e-6)
            assert np.allclose(Xos[:, idx] @ w + unit.ybar, sk.predict(Xos[:, idx]), atol=1e-6)
        W = fa.ridge_weight_grid(unit.G, unit.b, idx, [0.5, 30.0, 1e4])
        assert np.allclose(W[:, 1], Ridge(alpha=30.0).fit(Xs[:, idx], y).coef_, atol=1e-6)
        ols = LinearRegression().fit(Xs[:, idx], y)  # alpha 0 is ordinary least squares
        assert np.allclose(fa.ridge_weights(unit.G, unit.b, idx, 0.0), ols.coef_, atol=1e-6)
        assert np.allclose(fa.ridge_weight_grid(unit.G, unit.b, idx, [0.0])[:, 0], ols.coef_, atol=1e-6)
    assert fa.unit_scores(unit, [], [1.0, 10.0]).shape == (2, 3)  # the empty model scores 0 everywhere


def test_scores_from_sufficient_statistics_equal_the_direct_pearson():
    """The engine never forms predictions: per-perturbation statistics give exactly what pearson_rows gives on the
    explicit predictions, for any column subset and alpha, for a transformed design, and for the squared error."""
    rng = np.random.default_rng(11)
    n_tr, n_out, n_g, C = 12, 5, 40, 6
    X = rng.normal(size=(n_tr * n_g, C)) * [1, 2, 0.5, 1, 3, 1] + [0, 1, 2, 0, -1, 4]
    y = X @ rng.normal(size=C) + rng.normal(size=n_tr * n_g)
    Xo = rng.normal(size=(n_out * n_g, C))
    Xo[n_g:2 * n_g, :] = Xo[n_g, :]  # a perturbation whose rows are identical: constant prediction, score 0
    Yo = rng.normal(size=(n_out, n_g))
    unit = fa.make_unit(X, y, Xo, Yo)
    Xs, (Xos,), _, _ = fa.standardise(X, Xo)
    alphas = [0.0, 1.0, 100.0]
    for idx in ([0, 1, 2, 3, 4, 5], [4, 1], [2]):
        W = fa.ridge_weight_grid(unit.G, unit.b, idx, alphas)
        P = (Xos[:, idx] @ W + unit.ybar).T.reshape(len(alphas), n_out, n_g)
        direct = fa.pearson_rows(P, Yo)
        direct[:, 1] = 0.0  # pearson_rows sees rounding noise there; the statistics see a constant, as they should
        assert np.allclose(fa.unit_scores(unit, idx, alphas), direct, atol=1e-10)
        sse = ((Yo[None] - P) ** 2).sum(axis=(1, 2))
        assert np.allclose(fa.unit_sse(unit.subset(idx), W), sse, rtol=1e-10)
    assert np.all(fa.unit_scores(unit, [0, 1, 2], alphas)[:, 1] == 0.0)
    T = rng.normal(size=(C, 3))  # the unit of the design X @ T, for training and predicted rows alike
    tu = unit.transform(T)
    W = fa.ridge_weight_grid(tu.G, tu.b, [0, 1, 2], [10.0])
    assert np.allclose(W[:, 0], np.linalg.solve((Xs @ T).T @ (Xs @ T) + 10.0 * np.eye(3), (Xs @ T).T @ (y - y.mean())))
    P = (Xos @ T @ W + tu.ybar).T.reshape(1, n_out, n_g)
    got = fa.unit_scores(tu, [0, 1, 2], [10.0])
    assert tu.M.shape == (n_out, 3, 3) and got[0, 1] == 0.0
    assert np.allclose(got[:, [0, 2, 3, 4]], fa.pearson_rows(P, Yo)[:, [0, 2, 3, 4]], atol=1e-10)


def test_the_cross_seed_alpha_uses_only_seed_a_training_scores():
    """Seed A's training perturbations favour alpha 1, its validation perturbations favour alpha 100 by far, and
    seed B's training perturbations favour alpha 100: the pair (A -> B) must report B's vector at alpha 1."""
    n_train, alphas = 4, [1.0, 100.0]
    A = np.array([[0.6, 0.6, 0.6, 0.6, 0.0, 0.0],
                  [0.5, 0.5, 0.5, 0.5, 0.99, 0.99]])
    B = np.array([[0.1, 0.1, 0.1, 0.1, 0.0, 0.0],
                  [0.7, 0.7, 0.7, 0.7, 0.99, 0.99]])
    vec, chosen = fa.honest_choice([A, B], n_train, alphas, seeds=[0, 1])
    assert chosen == [{"select_seed": 0, "report_seed": 1, "alpha": 1.0},
                      {"select_seed": 1, "report_seed": 0, "alpha": 100.0}]
    assert np.allclose(vec, (B[0] + A[1]) / 2)
    # an alpha chosen on the reporting seed's own folds (the optimistic choice) would have scored higher
    optimistic = (B[int(np.argmax(B[:, :n_train].mean(axis=1)))] + A[int(np.argmax(A[:, :n_train].mean(axis=1)))]) / 2
    assert vec.mean() < optimistic.mean()
    A2 = A.copy()
    A2[:, n_train:] = [[1.0, 1.0], [-1.0, -1.0]]  # seed A's validation scores never enter its choice
    assert fa.honest_choice([A2, B], n_train, alphas, [0, 1])[1] == chosen
    with pytest.raises(ValueError):
        fa.honest_choice([A], n_train, alphas)


def test_paired_comparison_grid_alpha_and_classes():
    u, v = np.array([0.5, 0.6, 0.7, 0.4]), np.array([0.4, 0.6, 0.5, 0.5])
    p = fa.paired(u, v)
    d = u - v
    assert p["diff"] == pytest.approx(d.mean()) and p["se"] == pytest.approx(d.std(ddof=1) / 2)
    assert (p["wins"], p["losses"], p["n"]) == (2, 1, 4)
    grid = [0.01, 1.0, 10.0, 100.0, 1000.0]
    assert fa.grid_alpha([100.0, 1000.0], grid) == 1000.0  # mean 550, nearest on a log scale
    assert fa.grid_alpha([10.0, 10.0], grid) == 10.0 and fa.grid_alpha([0.0, 0.0], [0.0] + grid) == 0.0
    # the 0.001 margin is a margin of practical equivalence, told apart from a difference that is not established
    assert fa.classify(0.0005, 0.001) == "not_established" and fa.classify(-0.0008, 0.0002) == "below_margin"
    assert fa.classify(0.003, 0.001) == "higher" and fa.classify(-0.003, 0.002) == "lower"


def _synthetic(seed=0, n_train=40, n_val=12, n_genes=60, n_noise=4, Y_val=None):
    """Two informative columns, an exact duplicate of the first, and noise columns; one column per feature."""
    rng = np.random.default_rng(seed)
    n = n_train + n_val
    inf1, inf2 = rng.normal(size=(n, n_genes)), rng.normal(size=(n, n_genes))
    cols = [inf1, inf2, inf1.copy()] + [rng.normal(size=(n, n_genes)) for _ in range(n_noise)]
    names = ["inf1", "inf2", "dup"] + [f"noise{i}" for i in range(n_noise)]
    X = np.stack(cols, axis=2)
    Y = 1.0 * inf1 + 0.8 * inf2 + 0.6 * rng.normal(size=(n, n_genes))
    Yv = Y[n_train:] if Y_val is None else Y_val
    eng = fa.static_engine(X[:n_train], Y[:n_train], X[n_train:], Yv, {f: [i] for i, f in enumerate(names)},
                           seeds=[0, 1], k=5, alphas=[1.0, 10.0, 100.0, 1e3, 1e4])
    return eng, names, X[:n_train]


def test_one_se_rule_picks_the_small_set():
    eng, names, _ = _synthetic()
    bwd = fa.backward_path(eng, names)
    assert [st["n_features"] for st in bwd] == list(range(len(names), 0, -1))
    vecs = [eng.train_part(eng.score(st["features"])["vector"]) for st in bwd]
    assert all(v.size == eng.n_train for v in vecs)
    pick, best, cmp = fa.one_se_choice(vecs, [(st["n_features"], st["n_columns"]) for st in bwd])
    compact = set(bwd[pick]["features"])
    assert len(compact) == 2 and "inf2" in compact and compact & {"inf1", "dup"}
    assert cmp[pick]["diff"] <= fa.noise_band(cmp[pick]["se"]) and cmp[best]["diff"] == 0.0
    one = bwd[-1]  # a single informative column is far below the best set
    assert cmp[len(bwd) - 1]["diff"] > 3 * cmp[len(bwd) - 1]["se"] and one["n_features"] == 1
    # a tiny, perfectly systematic difference (an exact duplicate column shifts a score by about 1e-5 with a paired SE
    # far smaller) is established by one SE alone; the margin of practical equivalence lets the smaller set through
    rng = np.random.default_rng(7)
    small = rng.normal(0.6, 0.1, size=50)
    larger = small + 1e-5 + 1e-8 * rng.normal(size=50)
    assert fa.one_se_choice([larger, small], [(2, 2), (1, 1)])[0] == 1
    assert fa.one_se_choice([larger, small], [(2, 2), (1, 1)], floor=0.0)[0] == 0
    assert fa.noise_band(1e-5) == fa.NOISE_FLOOR == 0.001
    fwd = fa.forward_path(eng, names)
    assert {fwd[0]["added"], fwd[1]["added"]} in ({"inf1", "inf2"}, {"dup", "inf2"})
    assert fwd[-1]["n_features"] == len(names) and fwd[1]["train_mean"] > fwd[0]["train_mean"]


def test_paths_and_the_compact_set_never_look_at_the_validation_perturbations():
    """The same training data with entirely different validation labels: every path step, every penalty and the
    compact choice stay the same; only the validation scores, on which compact and full are compared, change."""
    eng, names, _ = _synthetic()
    noise = np.random.default_rng(99).normal(size=(12, 60))
    other, _, _ = _synthetic(Y_val=noise)
    for path in (fa.backward_path, fa.forward_path):
        a, b = path(eng, names), path(other, names)
        assert [s["features"] for s in a] == [s["features"] for s in b]
        assert [s["alphas"] for s in a] == [s["alphas"] for s in b]
        assert [s["train_mean"] for s in a] == pytest.approx([s["train_mean"] for s in b], abs=1e-12)
        assert [s["val_mean"] for s in a] != pytest.approx([s["val_mean"] for s in b], abs=1e-3)
    res = [fa.analyse_model(e, names, np.eye(len(names)), names, {}) for e in (eng, other)]
    assert res[0]["compact"]["features"] == res[1]["compact"]["features"]
    assert res[0]["compact"]["vs_best"] == res[1]["compact"]["vs_best"]
    vs = res[0]["compact"]["vs_full"]  # compact versus full on the validation perturbations alone
    assert vs["n"] == eng.n_val and res[0]["compact"]["vs_full_train"]["n"] == eng.n_train
    assert vs["class"] == fa.classify(vs["diff"], vs["se"])
    assert vs["diff"] != pytest.approx(res[1]["compact"]["vs_full"]["diff"], abs=1e-6)


def test_duplicates_clusters_and_rank():
    rng = np.random.default_rng(3)
    a = rng.normal(size=500)
    X = np.stack([a, a.copy(), a + 0.3 * rng.normal(size=500), rng.normal(size=500), np.full(500, 2.0)], axis=1)
    Xs, _, _, sd = fa.standardise(X)
    cols, feats = ["a", "b", "c", "d", "e"], ["fa", "fb", "fc", "fd", "fe"]
    red = fa.redundancy(Xs, cols, feats, constant=X.std(axis=0) == 0)
    assert red["constant_columns"] == ["e"] and red["duplicate_groups"] == [["a", "b"]]
    assert red["n_duplicate_columns"] == 1 and red["rank"] == 3
    assert red["n_pairs_above_0.9"] == 3 and red["n_pairs_above_0.7"] == 3
    assert [cl["columns"] for cl in red["clusters"]] == [["a", "b", "c"]]
    assert red["clusters"][0]["features"] == ["fa", "fb", "fc"] and red["clusters"][0]["max_abs_r"] == pytest.approx(1)
    assert red["top_pairs"][0]["a"] == "a" and red["top_pairs"][0]["b"] == "b"
    assert red["condition_number"] is None and 1.0 < red["effective_rank"] < 4.0
    assert fa.union_find(5, [(0, 1), (3, 4), (1, 0)]) == [[0, 1], [3, 4]]


def _row_units(X, y, n_p, n_g, folds):
    """Fold units over a fixed design (rows grouped by perturbation): each fold's training rows standardised alone."""
    groups = np.repeat(np.arange(n_p), n_g)
    units = []
    for fold in folds:
        te = np.isin(groups, fold)
        units.append(fa.make_unit(X[~te], y[~te], X[te], y[te].reshape(len(fold), n_g)))
    return units


def test_lasso_from_the_gram_matrix_equals_sklearn_on_the_rows():
    from sklearn.linear_model import lasso_path
    rng = np.random.default_rng(6)
    X = rng.normal(size=(300, 5))
    X[:, 4] = X[:, 0] + 0.05 * rng.normal(size=300)  # nearly collinear columns
    y = X @ [1.0, 0.0, -0.5, 0.2, 0.0] + rng.normal(size=300)
    Xs = fa.standardise(X)[0]
    yc = y - y.mean()
    lams = np.array([0.3, 0.05, 0.01, 0.001])
    _, ref, _ = lasso_path(Xs, yc, alphas=lams, max_iter=100000, tol=1e-12)
    got = fa.lasso_gram_path(Xs.T @ Xs, Xs.T @ yc, len(y), lams[::-1])[:, ::-1]  # any order of the lambdas
    assert np.allclose(got, ref, atol=1e-5)
    one = fa.lasso_gram_path(Xs[:, :1].T @ Xs[:, :1], Xs[:, :1].T @ yc, len(y), [0.01])  # a single column works too
    assert one.shape == (1, 1) and one[0, 0] == pytest.approx(lasso_path(Xs[:, :1], yc, alphas=[0.01])[1][0, 0],
                                                               abs=1e-6)


def test_lasso_stability_ranks_the_informative_columns_first():
    rng = np.random.default_rng(4)
    n_p, n_g = 24, 60
    X = rng.normal(size=(n_p * n_g, 8))
    y = 1.0 * X[:, 2] - 0.7 * X[:, 5] + 0.8 * rng.normal(size=n_p * n_g)
    Xs = fa.standardise(X)[0]
    groups = np.repeat(np.arange(n_p), n_g)
    names = [f"c{i}" for i in range(8)]
    folds = [[int(s.lstrip("p")) for s in f] for f in cv_folds_of([f"p{i:02d}" for i in range(n_p)], 5, 0)]
    units = _row_units(Xs, y, n_p, n_g, folds)
    res = fa.lasso_stability(Xs, y, groups, units, 20, 0, names, ["f" + n for n in names])
    assert set(res["ranking"][:2]) == {"c2", "c5"}
    assert res["column_frequency"]["c2"] == 1.0 and res["column_frequency"]["c5"] == 1.0
    assert res["feature_frequency"]["fc2"] == 1.0 and {"fc2", "fc5"} <= set(res["stable_features"])
    assert 0 < res["lambda"] <= res["lambda_max"] and len(res["path"]) == 5 and res["cv_folds"] == 5
    kept = [p["n_columns"] for p in res["path"]]
    assert kept == sorted(kept) and kept[0] == 0  # the largest lambda zeroes every column
    # the penalty's cross-validation is the folds' own designs: the same as fitting each fold's rows directly
    from sklearn.linear_model import lasso_path
    grid = res["lambda_max"] * np.logspace(0, np.log10(fa.LASSO_RATIO), fa.LASSO_LAMBDAS)
    direct = np.zeros(len(grid))
    for fold in folds:
        te = np.isin(groups, fold)
        Xtr, (Xte,), _, _ = fa.standardise(Xs[~te], Xs[te])
        _, coefs, _ = lasso_path(Xtr, y[~te] - y[~te].mean(), alphas=grid, max_iter=100000, tol=1e-10)
        direct += ((y[te][:, None] - Xte @ coefs - y[~te].mean()) ** 2).mean(axis=0) / len(folds)
    assert np.allclose(res["cv_mse"], direct, rtol=1e-4)


def test_merge_by_first_component_is_fitted_on_fold_train_rows_only():
    rng = np.random.default_rng(5)
    base = rng.normal(size=300)
    Xtr = np.stack([base + 0.2 * rng.normal(size=300), 3 * base + rng.normal(size=300), rng.normal(size=300)], axis=1)
    Xout = rng.normal(size=(120, 3)) * [1, -5, 1]  # the predicted rows look nothing like the training rows
    Yout = rng.normal(size=(4, 30))
    y = Xtr @ [1.0, 0.2, -0.5] + rng.normal(size=300)
    unit = fa.make_unit(Xtr, y, Xout, Yout)
    merged, (v,) = fa.merge_unit(unit, [[0, 1]])
    Xs, (Xos,), _, _ = fa.standardise(Xtr, Xout)
    pc = np.linalg.eigh(np.corrcoef(Xs[:, :2].T))[1][:, -1]  # the component of the training rows alone
    assert np.allclose(np.abs(v), np.abs(pc), atol=1e-8)
    z = Xs[:, :2] @ v
    z_out = Xos[:, :2] @ v / z.std()
    Xm = np.column_stack([Xs[:, 2], z / z.std()])
    assert np.allclose(merged.G, Xm.T @ Xm, atol=1e-6) and np.allclose(merged.b, Xm.T @ (y - y.mean()), atol=1e-6)
    want = fa.unit_from_standardised(Xm, y, np.column_stack([Xos[:, 2], z_out]), Yout)  # the predicted rows' stats
    for k in ("M", "c", "m"):
        assert np.allclose(getattr(merged, k), getattr(want, k), atol=1e-8), k
    other = fa.make_unit(Xtr, y, -50 * Xout + 7, Yout)  # other predicted rows, same training rows
    merged2, (v2,) = fa.merge_unit(other, [[0, 1]])
    assert np.allclose(v2, v) and np.allclose(merged2.G, merged.G)
    eng, names, _ = _synthetic()
    m = fa.merged_engine(eng, eng.columns(names), [[0, 2]])  # inf1 and its duplicate become one column
    assert m.val_unit.G.shape == (len(names) - 1,) * 2
    full = eng.score(names)["mean"]
    assert abs(m.score_idx(range(len(names) - 1))["mean"] - full) < 0.02


def test_verdict_logic():
    feats = ["a", "b", "c", "d"]
    single = {f: {"mean": 0.3, "se": 0.01} for f in feats}
    drop = {"a": fa.paired([0.6, 0.7], [0.5, 0.5]),
            "b": {"diff": -0.02, "se": 0.005, "wins": 3, "losses": 60, "n": 67},
            "c": {"diff": 0.001, "se": 0.002, "wins": 34, "losses": 33, "n": 67},
            "d": {"diff": -0.001, "se": 0.002, "wins": 30, "losses": 37, "n": 67}}
    part = {f: {"feature": "a", "column": "a", "own_column": f, "r": 0.95} for f in feats}
    kept_part = {"b": {"feature": "a", "column": "a", "own_column": "b", "r": 0.97},
                 "c": {"feature": "a", "column": "a[1]", "own_column": "c", "r": -0.93},
                 "d": {"feature": "a", "column": "a", "own_column": "d", "r": 0.5}}
    feats.append("f")  # dropping it raises the score by more than its SE but less than the margin
    single["f"], part["f"] = single["a"], part["a"]
    drop["f"] = {"diff": -0.0008, "se": 0.0001, "wins": 20, "losses": 47, "n": 67}
    kept_part["f"] = {"feature": "a", "column": "a", "own_column": "f", "r": 0.2}
    feats.append("g")  # an established gain in the full model, yet outside the compact set: not "no gain"
    single["g"], part["g"] = single["a"], part["a"]
    drop["g"] = {"diff": 0.0015, "se": 0.0008, "wins": 40, "losses": 27, "n": 67}
    kept_part["g"] = {"feature": "a", "column": "a", "own_column": "g", "r": 0.6}
    out = fa.assign_verdicts(feats, ["a"], {f: 1 for f in feats}, single, drop, part, kept_part,
                             {"a": 1.0, "b": 0.2}, {"e": "KeyError: unknown feature 'e'" + "x" * 300})
    v = {o["feature"]: o for o in out}
    assert [o["feature"] for o in out] == ["a", "b", "c", "d", "f", "g", "e"] and v["f"]["verdict"] == "no_gain"
    assert v["a"]["verdict"] == "kept"
    assert v["b"]["verdict"] == "harmful" and "0.0200" in v["b"]["reason"]  # harmful outranks redundant
    assert v["c"]["verdict"] == "redundant" and "a[1]" in v["c"]["reason"] and "-0.930" in v["c"]["reason"]
    assert v["d"]["verdict"] == "no_gain" and "0.0020" in v["d"]["reason"]
    assert v["g"]["verdict"] == "substitutable" and "+0.0015" in v["g"]["reason"] and "established" in v["g"]["reason"]
    assert v["e"]["verdict"] == "unrecomputable" and len(v["e"]["reason"]) == 200
    assert v["b"]["evidence"]["lasso_frequency"] == 0.2 and v["c"]["evidence"]["lasso_frequency"] is None
    assert v["b"]["evidence"]["drop_one"]["diff"] == -0.02 and v["b"]["evidence"]["partner"]["r"] == 0.95
    assert set(fa.VERDICTS) >= {o["verdict"] for o in out} and "substitutable" in fa.RULE


def test_the_box_has_one_entry_per_run_and_feature_and_never_a_builtin():
    def verdict(f, v):
        return {"feature": f, "verdict": v, "reason": f"{v} because", "evidence": {"columns": 1}}
    run = {"run": "r1", "run_id": "R1", "arm_class": "agent", "selected": {"experiment_id": "EXP_9"},
           "introduced_by": {"x_e3": "EXP_3", "y_e4": "EXP_4", "z_e5": "EXP_5"},
           "selected_analysis": {"verdicts": [verdict("x_e3", "no_gain"), verdict("y_e4", "redundant"),
                                              verdict("control_mean", "no_gain"), verdict("w_e1", "kept")]},
           "pool": {"verdicts": [verdict("x_e3", "kept"), verdict("y_e4", "no_gain"), verdict("z_e5", "redundant"),
                                 verdict("control_mean", "no_gain"), verdict("w_e1", "kept")]}}
    box = fa.build_box({"runs": [run]})
    e = {x["feature"]: x for x in box["entries"]}
    assert set(e) == {"y_e4", "z_e5"}  # x_e3 is kept in the pool, control_mean is a built-in, w_e1 is kept
    assert e["y_e4"]["verdict"] == "redundant" and e["y_e4"]["scope"] == "selected"
    assert e["y_e4"]["experiment"] == "EXP_9" and e["y_e4"]["introduced_by"] == "EXP_4"
    assert e["y_e4"]["evidence"]["scopes"] == {"selected": {"verdict": "redundant", "reason": "redundant because"},
                                               "pool": {"verdict": "no_gain", "reason": "no_gain because"}}
    assert e["z_e5"]["scope"] == "pool" and e["z_e5"]["experiment"] == "EXP_5" and e["z_e5"]["arm_class"] == "agent"
    comb = {c["feature"]: c for c in fa.combined_verdicts(run)}
    assert comb["x_e3"]["verdict"] == "kept" and comb["x_e3"]["kept_in"] == ["pool"] and comb["control_mean"]["builtin"]


# ------------------------------------------------------------------ plugins and label dependence
PLUGIN = '''
import numpy as np
from genemila.features.api import Feature, register


@register
class F(Feature):
    name = "{name}"

    def compute(self, ctx, perts, params):
{body}
'''


def _plugin(store: Path, name: str, body: str, prefix: str = "") -> None:
    (store / f"{name}.py").write_text(prefix + PLUGIN.format(name=name, body=body))


def test_plugins_load_file_by_file_and_a_failing_reload_marks_only_its_features(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    (store / "aa_broken.py").write_text("import nonexistent_pkg_xyz\n")  # sorted first: it must not stop the rest
    _plugin(store, "good_feat", "        return np.ones((len(perts), ctx.n_genes, 1))")
    _plugin(store, "flaky_feat", "        return np.ones((len(perts), ctx.n_genes, 1))",
            prefix="import os\nif os.environ.get('FA_FLAKY_SEEN'):\n    raise RuntimeError('broken on re-execution')\n"
                   "os.environ['FA_FLAKY_SEEN'] = '1'\n")
    (store / "_private.py").write_text("raise RuntimeError('never imported')\n")
    os.environ.pop("FA_FLAKY_SEEN", None)
    try:
        errors = fa.load_run_plugins(store)
        assert set(errors) == {"aa_broken"} and errors["aa_broken"].startswith("ModuleNotFoundError")
        assert {"good_feat", "flaky_feat"} <= set(REGISTRY)
        failed = fa.reload_run_plugins()
        assert set(failed) == {"flaky_feat"} and "failed on re-execution" in failed["flaky_feat"]
        miss = fa.missing_feature_errors(["aa_broken", "good_feat", "nowhere"], store, errors)
        assert set(miss) == {"aa_broken", "nowhere"}
        assert miss["aa_broken"].startswith("plugin aa_broken.py failed to import: ModuleNotFoundError")
        assert "failed to import" in miss["nowhere"]
    finally:
        os.environ.pop("FA_FLAKY_SEEN", None)
        fa.load_run_plugins(tmp_path / "empty")  # leaves the built-ins only
    assert "good_feat" not in REGISTRY and set(fa.BUILTIN_FEATURES) <= set(REGISTRY)


def test_label_dependence_is_detected_per_feature_and_those_features_are_recomputed_per_fold(tmp_path, dataset,
                                                                                               monkeypatch):
    """memo_b reaches the labels only through ctx.feature("mean_response"), a memo memo_a has already filled on a
    shared context, and private_d reads the private label array directly: both must count as label-dependent and be
    recomputed without each fold; the label-free free_c is sliced."""
    store = tmp_path / "store"
    store.mkdir()
    for name in ("memo_a", "memo_b"):
        _plugin(store, name, "        return 2.0 * np.asarray(ctx.feature('mean_response', perts, {}))")
    _plugin(store, "private_d", "        d = ctx._train_delta.mean(axis=0)\n"
                                "        return np.broadcast_to(d[None, :, None], (len(perts), ctx.n_genes, 1)).copy()")
    _plugin(store, "free_c", "        return np.broadcast_to(ctx.control_mean[None, :, None] ** 2, "
                             "(len(perts), ctx.n_genes, 1)).copy()")
    calls = []
    real = fa.feature_blocks

    def spy(ctx, names, *a, **k):
        calls.append((tuple(names), ctx.train_signature, len(a[1]) if len(a) > 1 else None))
        return real(ctx, names, *a, **k)
    monkeypatch.setattr(fa, "feature_blocks", spy)
    try:
        fa.load_run_plugins(store)
        ctx = FeatureContext(dataset)
        val1 = LabelSet.load(dataset / "private" / "val1.npz")
        feats = ["memo_a", "memo_b", "private_d", "free_c"]
        fits = fa.compute_fits(ctx, feats, {}, [0, 1], 5, val1.perts, val1.means - ctx.control_mean)
    finally:
        fa.load_run_plugins(tmp_path / "empty")
    assert fits["label_dependent"] == ["memo_a", "memo_b", "private_d"] and not fits["failed"]
    for s in (0, 1):
        for fold in cv_folds_of(ctx.train_perts, 5, s):
            sig = ctx.without_train(fold).train_signature
            done = {names[0] for names, signature, _ in calls if signature == sig}
            assert done == {"memo_a", "memo_b", "private_d"}, (s, fold, done)
    # the old, shared-context detection misses memo_b: the reason the detection runs on a fresh view per feature
    label_dep = {}
    fa.load_run_plugins(store)
    try:
        shared = FeatureContext(dataset)
        for f in feats:
            real(shared, [f], {}, list(shared.train_perts), {}, None, None, label_dep)
    finally:
        fa.load_run_plugins(tmp_path / "empty")
    assert label_dep["memo_a"] and not label_dep["memo_b"] and not label_dep["private_d"]


# ------------------------------------------------------------------ opening runs read only
def _listing(d: Path) -> dict:
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*"))
            if p.is_file()}


def test_database_is_read_without_creating_files(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    c = sqlite3.connect(run / "lab.db", isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE t (x)")
    c.execute("INSERT INTO t VALUES (1)")
    c.close()
    before = _listing(run)
    assert set(before) == {"lab.db"}
    ro = fa.open_db_readonly(run, tmp_path / "scratch")
    assert [tuple(x) for x in ro.execute("SELECT x FROM t").fetchall()] == [(1,)]
    ro.close()
    assert _listing(run) == before  # no -wal, no -shm
    w = sqlite3.connect(run / "lab.db", isolation_level=None)  # a live writer: the log holds uncheckpointed rows
    w.execute("PRAGMA wal_autocheckpoint=0")
    w.execute("INSERT INTO t VALUES (2)")
    live = _listing(run)
    ro = fa.open_db_readonly(run, tmp_path / "scratch2")
    assert sorted(tuple(x) for x in ro.execute("SELECT x FROM t").fetchall()) == [(1,), (2,)]
    ro.close()
    assert _listing(run) == live
    w.close()


def test_a_run_without_its_data_is_skipped(tmp_path):
    run = tmp_path / "gone"
    run.mkdir()
    c = sqlite3.connect(run / "lab.db")
    c.execute("CREATE TABLE runs (run_id TEXT, split_id TEXT, dataset TEXT, base_commit TEXT, config_json TEXT)")
    c.execute("CREATE TABLE experiments (experiment_id TEXT, status TEXT, kind TEXT, primary_score REAL, "
              "finished_at REAL, feature_set_json TEXT, new_feature TEXT, feature_params_json TEXT, "
              "delta_from_parent REAL)")
    c.execute("INSERT INTO runs VALUES ('gone', 's', 'synthetic', '', ?)",
              (json.dumps({"run": {"data_dir": str(tmp_path / "nowhere")}, "experiment": {},
                           "planner": {"provider": "claude_cli", "model": "opus"}}),))
    c.execute("INSERT INTO experiments VALUES ('EXP_1', 'completed', 'config', 0.5, 1, '[\"control_mean\"]', NULL, "
              "'{}', NULL)")
    c.commit()
    c.close()
    r = fa.audit_run(run, log=lambda m: None)
    assert r["status"] == "skipped" and "nowhere" in r["reason"] and "is missing" in r["reason"]
    assert r["arm"].startswith("claude_cli:opus planner") and r["arm_class"] == "agent"  # known before the skip
    empty = tmp_path / "empty"
    empty.mkdir()
    assert fa.audit_run(empty, log=lambda m: None)["reason"] == "no lab.db"
    rep = fa.analyse([run, empty], tmp_path / "cache", resamples=2, log=lambda m: None)
    md = fa.render(json.loads(json.dumps(fa._plain(rep))))
    assert "skipped: data dir" in md and "No run could be audited" in md
    assert not (tmp_path / "cache" / "audits").exists()  # a skipped run leaves no checkpoint


# ------------------------------------------------------------------ end to end on a finished run
@pytest.fixture(scope="module")
def finished_run(tmp_path_factory, dataset, code_repo):
    """A small finished run with sealed scores: scripted planner, mock workers, about half a minute."""
    from conftest import make_cfg
    from genemila.controller import Controller
    from genemila.lab import Lab
    from genemila.providers.mock import MockProvider, ScriptedPlanner
    tmp = tmp_path_factory.mktemp("audit")
    cfg = make_cfg(tmp, schedule__max_planner_calls=2)
    cfg["run"]["data_dir"] = str(dataset)
    lab = Lab(cfg, tmp / "run0", dataset, repo=code_repo)
    try:
        Controller(lab, workers=2, seconds=30, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
                   quiet=True).run()
    finally:
        lab.stop_event.set()
        lab.kill_event.set()
        lab.close()
        lab.db.close_thread_conn()
    (lab.run_dir / "config.json").write_text(json.dumps(lab.cfg))
    run_dir = lab.run_dir
    del lab
    for _ in range(100):  # checkpoint, so the run is at rest as a finished run is; a worker thread or process that
        gc.collect()      # still holds the database open keeps its log alive, so wait for it to let go
        c = sqlite3.connect(run_dir / "lab.db")
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        c.close()
        if not (run_dir / "lab.db-wal").exists() and not (run_dir / "lab.db-shm").exists():
            break
        time.sleep(0.1)
    return run_dir


def _copy_run(run_dir: Path, dst: Path) -> Path:
    shutil.copytree(run_dir, dst, ignore=shutil.ignore_patterns("worktrees", "__pycache__"))
    return dst


def _counting(monkeypatch):
    """Counts oracle instances and queries, and records every numpy read of a file whose name says it is sealed,
    with whether an oracle method was running at the time."""
    state = {"inits": 0, "queries": [], "inside": 0, "sealed_reads": [], "val1_reads": 0}
    init, query, perts = QueryOracle.__init__, QueryOracle.query, QueryOracle.perts
    np_load = np.load

    def _init(self, *a, **k):
        state["inits"] += 1
        init(self, *a, **k)

    def _query(self, experiment_id, *a, **k):
        state["queries"].append(experiment_id)
        state["inside"] += 1
        try:
            return query(self, experiment_id, *a, **k)
        finally:
            state["inside"] -= 1

    def _perts(self):
        state["inside"] += 1
        try:
            return perts.fget(self)
        finally:
            state["inside"] -= 1

    def _load(file, *a, **k):
        name = str(file)
        if "val" + "2" in Path(name).name:
            state["sealed_reads"].append((Path(name).name, state["inside"] > 0))
        if Path(name).name == "val1.npz":
            state["val1_reads"] += 1
        return np_load(file, *a, **k)
    monkeypatch.setattr(QueryOracle, "__init__", _init)
    monkeypatch.setattr(QueryOracle, "query", _query)
    monkeypatch.setattr(QueryOracle, "perts", property(_perts))
    monkeypatch.setattr(np, "load", _load)
    return state


def test_end_to_end_report_twin_box_and_an_untouched_run(finished_run, tmp_path, monkeypatch):
    run_dir = finished_run
    assert not (run_dir / "lab.db-wal").exists() and not (run_dir / "lab.db-shm").exists()
    before = _listing(run_dir)
    state = _counting(monkeypatch)
    out = tmp_path / "audit.md"
    assert fa.main(["--runs", str(run_dir), "--out", str(out), "--cache", str(tmp_path / "cache"),
                    "--resamples", "8"]) == 0
    # the run directory is byte for byte what it was: no -wal/-shm, no __pycache__, no cache, nothing
    assert _listing(run_dir) == before
    assert not (run_dir / "lab.db-wal").exists() and not (run_dir / "lab.db-shm").exists()
    assert state["inits"] == 0 and not state["queries"] and not state["sealed_reads"] and state["val1_reads"] >= 1
    rep = json.loads(out.with_suffix(".json").read_text())
    box = json.loads((tmp_path / "audit_feature_box.json").read_text())
    (r,) = rep["runs"]
    assert r["status"] == "audited", r.get("reason")
    assert r["arm_class"] == "no_llm" and rep["aggregate"]["primary"] == "no_llm" and r["plugin_errors"] == {}
    assert "mean_response" in r["label_dependent"] and "control_mean" not in r["label_dependent"]
    assert list((tmp_path / "cache" / "audits").glob(f"{run_dir.name}__*.json"))  # the run's checkpoint
    con = sqlite3.connect(run_dir / "lab.db")
    best = con.execute("SELECT experiment_id FROM experiments WHERE status='completed' AND primary_score IS NOT NULL "
                       "AND COALESCE(kind, '') NOT IN ('baseline', 'ensemble') "
                       "ORDER BY primary_score DESC, finished_at, experiment_id LIMIT 1").fetchone()[0]
    con.close()
    sel = r["selected"]
    assert sel["experiment_id"] == best and r["fold_seeds"] == [0, 1] and r["folds"] == 5
    assert r["n_train"] + r["n_val"] == r["selected_analysis"]["full"]["n"]
    pool = r["pool_features"]  # the model's features, then those that improved on their parent, then the built-ins
    con = sqlite3.connect(run_dir / "lab.db")
    gains = [f for (f,) in con.execute("SELECT new_feature FROM experiments WHERE status='completed' "
                                       "AND new_feature IS NOT NULL AND delta_from_parent > 0.0005 "
                                       "ORDER BY delta_from_parent DESC, experiment_id")]
    con.close()
    expected = list(sel["features"])
    for f in gains + ["control_mean", "mean_response", "is_target"]:
        if f not in expected:
            expected.append(f)
    assert pool == expected
    a = r["selected_analysis"]
    n_failed = len([f for f in sel["features"] if f in r["unrecomputable"]])
    assert a["census"]["n_features"] == len(sel["features"]) - n_failed
    assert len(a["backward"]) == a["census"]["n_features"] and len(a["forward"]) == a["census"]["n_features"]
    assert a["backward"][0]["mean"] == pytest.approx(a["full"]["mean"]) and len(a["full"]["alphas"]) == 2
    assert set(a["compact"]["features"]) <= set(a["census"]["features"])
    assert a["compact"]["vs_best"]["diff"] <= fa.noise_band(a["compact"]["vs_best"]["se"]) + 1e-12
    assert a["compact"]["vs_full"]["n"] == r["n_val"] and a["compact"]["vs_full_train"]["n"] == r["n_train"]
    assert set(a["lasso"]["feature_frequency"]) == set(a["census"]["features"]) and a["lasso"]["cv_folds"] == 5
    verdicts = {v["feature"]: v["verdict"] for v in a["verdicts"]}
    assert {f for f, v in verdicts.items() if v == "kept"} == set(a["compact"]["features"])
    assert set(verdicts) == set(sel["features"])
    if sel["model_type"] in ("ridge", "ols"):  # the engine reproduces the lab's own visible scores
        vr = r["visible_reproduction"]
        assert vr["available"] and vr["validation"]["diff"] == pytest.approx(0, abs=1e-4) and not vr["flag"]
        assert vr["out_of_fold"] is not None and vr["out_of_fold"]["diff"] == pytest.approx(0, abs=1e-4)
    assert r["marks"] == []
    pv = {v["feature"]: v["verdict"] for v in r["pool"]["verdicts"]}
    assert set(pv) == set(pool)
    # the box: one entry per feature that is kept in neither scope, built-ins never, with both scopes' verdicts
    assert box["generated_by"] == "tools/feature_audit.py" and "one paired SE" in box["rule"]
    kept_any = {f for f, v in verdicts.items() if v == "kept"} | {f for f, v in pv.items() if v == "kept"}
    expected_boxed = (set(verdicts) | set(pv)) - kept_any - set(fa.BUILTIN_FEATURES)
    assert {e["feature"] for e in box["entries"]} == expected_boxed and len(box["entries"]) == len(expected_boxed)
    for e in box["entries"]:
        assert set(e) >= {"run", "experiment", "feature", "verdict", "reason", "evidence", "scope", "code_hash",
                          "arm_class"}
        assert e["verdict"] in ("redundant", "substitutable", "harmful", "no_gain", "unrecomputable")
        assert e["run"] == run_dir.name and set(e["evidence"]["scopes"]) <= {"selected", "pool"}
        if e["verdict"] != "unrecomputable":
            assert set(e["evidence"]) == {"columns", "single", "drop_one", "lasso_frequency", "partner", "scopes"}
    md = out.read_text()
    for part in ("## Runs", "## Verdicts", f"## Detail: {run_dir.name}", "## Reading", "Backward path", "Forward path",
                 "Merge test", "| run | arm | feat. |", "A1 = scripted control (no LLM)", "Δ val (SE)",
                 "Compact sets (no-LLM runs)", f"- {run_dir.name}: ", "| verdict | no-LLM: selected |",
                 "No agent run was audited"):
        assert part in md, part
    assert "sealed" not in md.split("## Runs")[1].split("## Verdicts")[0].lower() and "†" not in md
    for line in md.splitlines():  # every table row has as many cells as its header
        if line.startswith("|") and "skipped:" not in line:
            assert line.count("|") == line.replace("\\|", "").count("|")
    tables = [b for b in md.split("\n\n") if b.startswith("|")]
    for tb in tables:
        rows = tb.splitlines()
        assert len({r.count("|") for r in rows}) == 1, rows[0]
    assert len(md.encode()) < 15000
    # the JSON twin re-renders the markdown byte for byte, without opening any run
    again = tmp_path / "again.md"
    assert fa.main(["--from-json", str(out.with_suffix(".json")), "--out", str(again)]) == 0
    assert again.read_bytes() == out.read_bytes()
    # a rerun with the same cache takes the run from its checkpoint: the same report, nothing recomputed
    calls = []
    monkeypatch.setattr(fa, "audit_run", lambda *a, **k: calls.append(a) or {})
    third = tmp_path / "third.md"
    assert fa.main(["--runs", str(run_dir), "--out", str(third), "--cache", str(tmp_path / "cache"),
                    "--resamples", "8"]) == 0
    assert not calls and third.read_bytes() == out.read_bytes()
    assert _listing(run_dir) == before


def test_a_plugin_that_fails_to_import_costs_only_its_own_features(finished_run, tmp_path, monkeypatch):
    """A plugin file nothing uses that imports a missing package, and a used feature whose plugin does the same: the
    run is still audited, the used feature is unrecomputable with the import error, the arm survives, and the row is
    marked because the audited model is smaller than the run's."""
    run = _copy_run(finished_run, tmp_path / "runcopy")
    con = sqlite3.connect(f"file:{run / 'lab.db'}?mode=ro", uri=True)
    rows = con.execute("SELECT feature_set_json FROM experiments WHERE status='completed' AND primary_score IS NOT "
                       "NULL AND COALESCE(kind, '') NOT IN ('baseline', 'ensemble') "
                       "ORDER BY primary_score DESC, finished_at, experiment_id LIMIT 1").fetchone()
    con.close()
    victim = next((f for f in json.loads(rows[0]) if f not in fa.BUILTIN_FEATURES
                   and (run / "feature_store" / f"{f}.py").exists()), None)
    assert victim is not None, "the scripted run's selected model has no plugin feature"
    (run / "feature_store" / "aa_unused_e99.py").write_text("import nonexistent_pkg_xyz\n")
    (run / "feature_store" / f"{victim}.py").write_text("import nonexistent_pkg_xyz\n")
    out = tmp_path / "broken.md"
    assert fa.main(["--runs", str(run), "--out", str(out), "--cache", str(tmp_path / "cache"), "--no-pool",
                    "--resamples", "2"]) == 0
    (r,) = json.loads(out.with_suffix(".json").read_text())["runs"]
    assert r["status"] == "audited", r.get("reason")
    assert r["arm"] == "scripted control (no LLM)" and set(r["plugin_errors"]) == {"aa_unused_e99", victim}
    assert r["unrecomputable"][victim].startswith(f"plugin {victim}.py failed to import: ModuleNotFoundError")
    assert r["selected_missing"] == [victim] and r["marks"] and not r["visible_reproduction"]["available"]
    v = {x["feature"]: x for x in r["selected_analysis"]["verdicts"]}
    assert v[victim]["verdict"] == "unrecomputable" and "nonexistent_pkg_xyz" in v[victim]["reason"]
    box = json.loads((tmp_path / "broken_feature_box.json").read_text())
    assert [e["verdict"] for e in box["entries"] if e["feature"] == victim] == ["unrecomputable"]
    md = out.read_text()
    assert "| runcopy † | A1 |" in md and "†: the audited model is not exactly the run's" in md
    # an unexpected error anywhere in a run's audit skips that run with the reason and keeps what was known (its arm)

    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(fa, "compute_fits", boom)
    r = fa.audit_run(run, log=lambda m: None)
    assert r["status"] == "skipped" and r["reason"] == "unexpected error: RuntimeError: boom"
    assert r["arm"] == "scripted control (no LLM)" and r["arm_class"] == "no_llm"


def test_score_sealed_spends_exactly_two_queries_per_run(finished_run, tmp_path, monkeypatch):
    run_dir = finished_run
    before = _listing(run_dir)
    state = _counting(monkeypatch)
    out = tmp_path / "sealed.md"
    assert fa.main(["--runs", str(run_dir), "--out", str(out), "--cache", str(tmp_path / "cache"), "--no-pool",
                    "--resamples", "4", "--score-sealed"]) == 0
    assert state["inits"] == 1 and len(state["queries"]) == 2
    assert [q.rsplit(":", 1)[1] for q in state["queries"]] == ["selected", "compact"]
    assert state["sealed_reads"] and all(inside for _, inside in state["sealed_reads"])  # only through the oracle
    (r,) = json.loads(out.with_suffix(".json").read_text())["runs"]
    sd = r["sealed"]
    assert r["pool"] is None and sd["n_queries"] == 2
    assert sd["difference"] == pytest.approx(sd["compact"] - sd["selected"])
    assert sd["compact_features"] == r["selected_analysis"]["compact"]["features"]
    if sd["stored_selected"] is not None:  # the selected model is reproduced as the lab fitted it
        assert abs(sd["reproduction_diff"]) < 1e-4 and not sd["reproduction_flag"]
    md = out.read_text()
    caution = md.index("already been read for dozens of finalists across about thirty runs")
    assert caution < md.index("## Runs") and "Norman" in md and "| sealed full | sealed compact |" in md
    assert _listing(run_dir) == before
    # two runs: two queries each, from two oracle instances
    copy = _copy_run(run_dir, tmp_path / "copy" / "run0b")
    state["queries"].clear()
    state["inits"] = 0
    two = tmp_path / "two.md"
    assert fa.main(["--runs", str(run_dir), str(copy), "--out", str(two), "--no-pool",
                    "--resamples", "2", "--score-sealed", "--cache", str(tmp_path / "cache")]) == 0
    assert state["inits"] == 2 and len(state["queries"]) == 4
    # an interrupted job restarted with the same cache never reads the sealed set again for runs already audited
    state["queries"].clear()
    state["inits"] = 0
    state["sealed_reads"].clear()
    again = tmp_path / "two_again.md"
    assert fa.main(["--runs", str(run_dir), str(copy), "--out", str(again), "--no-pool",
                    "--resamples", "2", "--score-sealed", "--cache", str(tmp_path / "cache")]) == 0
    assert state["inits"] == 0 and not state["queries"] and not state["sealed_reads"]
    assert again.read_bytes() == two.read_bytes()
    assert _listing(run_dir) == before


def test_the_report_stays_small_for_thirty_runs(finished_run, tmp_path):
    """A pasteable report: thirty runs with long names and arms (agent runs and no-LLM controls apart), a detailed
    run of forty features, and in a second case half the runs skipped with long reasons and many unrecomputable
    features."""
    out = tmp_path / "one.md"
    assert fa.main(["--runs", str(finished_run), "--out", str(out), "--cache", str(tmp_path / "cache"), "--no-pool",
                    "--resamples", "2"]) == 0
    rep = json.loads(out.with_suffix(".json").read_text())
    (r,) = rep["runs"]
    a = r["selected_analysis"]
    long = [f"knn_response_reconstruction_weights_variant_{i:02d}_e{100 + i}" for i in range(40)]
    st = a["backward"][0]
    a["backward"] = [{**st, "removed": long[i] if i else None} for i in range(40)]
    a["forward"] = [{**a["forward"][0], "added": long[i]} for i in range(40)]
    d0, s0 = next(iter(a["drop_one"].values())), next(iter(a["single"].values()))
    a["drop_one"] = {f: d0 for f in long}
    a["single"] = {f: s0 for f in long}
    a["census"]["columns_per_feature"] = {f: 3 for f in long}
    a["compact"]["features"] = long[:9]
    a["lasso"]["stable_features"] = long[:8]
    a["redundancy"]["top_pairs"] = [{"a": long[i] + "[0]", "b": long[i + 1] + "[2]", "r": 0.99} for i in range(15)]
    a["merge"] = [{"columns": [long[i] + "[0]", long[i + 1] + "[1]"], "features": long[i:i + 2], "min_abs_r": 0.95,
                   "n_columns": 100, "mean": 0.5, "se": 0.01, "alphas": [100.0, 1000.0],
                   "vs_full": {"diff": 0.0, "se": 0.001, "wins": 30, "losses": 30, "n": 67}} for i in range(8)]
    a["verdicts"] = [{"feature": f, "verdict": fa.VERDICTS[i % 5], "reason": "x", "evidence": {}}
                     for i, f in enumerate(long)]

    def runs_of(skipped_every=0, unrecomputable=0):
        runs = []
        for i in range(30):
            x = json.loads(json.dumps(r))
            x["run"] = f"newcode_opus_w4_continuation_r{i:02d}"
            x["arm"] = f"claude_cli:opus planner, deepseek:deepseek-v4-flash workers (continued from campaign {i % 4})"
            x["arm_class"] = "no_llm" if i % 5 == 0 else "agent"
            x["sealed"] = {"selected": 0.6, "compact": 0.59, "difference": -0.01, "reproduction_flag": i % 7 == 0,
                           "n_queries": 2}
            x["marks"] = ["1 selected feature(s) unrecomputable"] if i % 6 == 0 else []
            x["unrecomputable"] = {f"{long[j]}_x": "ModuleNotFoundError: No module named 'nonexistent_pkg_" + "y" * 80
                                   + "'" for j in range(unrecomputable)}
            if skipped_every and i % skipped_every == 1:
                x = {"run": x["run"], "path": "/x", "status": "skipped", "arm": x["arm"], "arm_class": x["arm_class"],
                     "reason": "unexpected error: ModuleNotFoundError: No module named 'torch_geometric' " + "z" * 220}
            runs.append(x)
        return runs
    for kw, bound in (({}, 14500), ({"skipped_every": 2, "unrecomputable": 25}, 14500)):
        runs = runs_of(**kw)
        big = {**rep, "runs": runs, "aggregate": fa.aggregate(runs)}
        md = fa.render(json.loads(json.dumps(fa._plain(big))))
        assert md.count("| newcode_opus_w4_continuation_r") == 30 and "A4 = " in md, kw
        assert "| verdict | agent: selected | agent: pools | no-LLM: selected | no-LLM: pools |" in md
        assert "no-LLM runs as a reference" in md and "No-LLM runs (reference)" in md
        assert len(md.encode()) < bound, (kw, len(md.encode()))  # well under 15 KB even in these extreme cases
    assert "+22 more in the JSON" in md and "z" * 100 not in md  # capped lists, truncated reasons
