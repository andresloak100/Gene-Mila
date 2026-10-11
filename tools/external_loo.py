#!/usr/bin/env python3
"""Does an external perturbation screen carry information the transfer features lack? A free check on visible data,
run before any paid arm.

Leave-one-out over the bundle's training perturbations: each one is held out in turn, its expression change (its
pseudobulk mean minus the control mean of public.npz) is predicted from the other training perturbations and the
public knowledge files, and the prediction is scored by pearson_delta (the benchmark's primary metric: Pearson
correlation across all genes between the predicted and the measured change). Nothing of the held-out
perturbation's own label is used by any predictor. Five predictors are compared:

    mean_response    mean change of the other training perturbations (the floor every feature must beat)
    geneset_knn      weighted mean of the other perturbations' changes, weights = Jaccard similarity of the
                     targets' gene-set memberships (knowledge/gene_sets.json), top k with positive similarity;
                     the in-bundle reference close to what the agents found
    external_direct  the external screen's change for the same target gene, unmeasured genes filled from
                     mean_response; mean_response when the target has no external row
    external_knn     weighted mean of the other perturbations' changes, weights = Pearson correlation of the
                     external changes of the two targets over the genes measured in both, top k with positive
                     correlation; geneset_knn when the held-out target has no external row (or no neighbour
                     correlates positively)
    external_stack   ridge over gene rows combining the four columns above (standardised with training-row
                     statistics), trained on the other perturbations' own leave-one-out columns, alpha picked
                     by an inner leave-one-out over those perturbations from a small grid

Added on 2026-10-11 after the first reading of this check, so a second look and not pre-specified: two predictors
appended after the five above (which they never change), read in their own section after the pre-specified reading:

    external_krr        kernel ridge through the external screen: mean_response + k^T (K + lambda I)^-1 (Y - mean),
                        over the other training perturbations with an external row (Y their changes), K the Pearson
                        correlation between their external rows, k their correlations with the held-out target's
                        row, so other responses enter with signed weights; lambda from LAMBDA_GRID by an inner
                        leave-one-out over those perturbations (a closed form, tested equal to refitting); geneset_knn
                        when the held-out target has no row or fewer than KRR_MIN_ROWS others have one
    external_stack_krr  the external_stack ridge over five columns, the four stack columns plus external_krr, every
                        training row's columns (its kernel ridge lambda included) computed without that perturbation
                        and without the held-out one

A JSON twin written before these were added has no "added_after_first_reading" key, and --from-json renders it to
exactly the markdown the earlier code wrote (tests/data/external_loo_v1). Runtime for 50 perturbations x 2,055 genes:
about 12 s in a 4-core cloud container (2 s before the additions), nearly all of it the nested lambda choices of the
five-column stack's training columns.

The external knowledge file (knowledge/<name>.json, written by tools/build_external_screen.py from the raw
external h5ad and the bundle's public gene and target lists) is an outside measurement the agents will be given
as a knowledge file, so it is public. The sealed labels are never read by this tool; the result is a reading on
whether the external screen deserves a labelled arm, not a benchmark score.

    python tools/external_loo.py --bundle data/adamson_cf --knowledge replogle2022_k562 \\
        --out genemila_scale_logs/external_loo_replogle2022_k562.md
    python tools/external_loo.py --from-json genemila_scale_logs/external_loo_replogle2022_k562.json --out again.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.benchmark.evaluator import _pearson as pearson_delta  # noqa: E402  the benchmark's own definition

PREDICTORS = ["mean_response", "geneset_knn", "external_direct", "external_knn", "external_stack"]
STACK_COLUMNS = PREDICTORS[:4]
ALPHA_GRID = (0.1, 1.0, 10.0, 100.0, 1000.0)   # the pre-specified grid; --alpha-grid widens it, and the report says so
MIN_SHARED_GENES = 3   # genes two external rows must share before their correlation is used as a weight

# Added on 2026-10-11 after the first reading of this check, so their numbers are a second look, not pre-specified
# results: kernel ridge regression through the external screen, and the stack with it as a fifth column. They are
# appended after the five pre-specified predictors and never change them, their order or their numbers.
ADDED_PREDICTORS = ["external_krr", "external_stack_krr"]
ADDED_REFERENCE = {"external_krr": "external_knn", "external_stack_krr": "external_stack"}   # what each is read against
STACK_KRR_COLUMNS = STACK_COLUMNS + ["external_krr"]
LAMBDA_GRID = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)   # kernel ridge penalties, fixed
KRR_MIN_ROWS = 3   # training perturbations with an external row that kernel ridge needs, else geneset_knn
TIE_TOL = 1e-12    # inner scores this close count as tied; ties go to the larger lambda


# ----------------------------------------------------------------------------------------------- inputs

def load_bundle(bundle_dir: Path) -> dict:
    """The visible part of a bundle: public.npz plus knowledge/targets.json and knowledge/gene_sets.json."""
    bundle_dir = Path(bundle_dir)
    z = np.load(bundle_dir / "public.npz", allow_pickle=False)
    genes = [str(g) for g in z["genes"]]
    perts = [str(p) for p in z["train_perts"]]
    control_mean = z["control_cells"].astype(np.float64).mean(axis=0)
    deltas = z["train_means"].astype(np.float64) - control_mean
    n_cells = [int(c) for c in z["train_ncells"]] if "train_ncells" in z.files else [None] * len(perts)
    kdir = bundle_dir / "knowledge"
    targets = json.loads((kdir / "targets.json").read_text())
    gene_sets = json.loads((kdir / "gene_sets.json").read_text()) if (kdir / "gene_sets.json").exists() else {}
    name = bundle_dir.name
    if (bundle_dir / "manifest.json").exists():
        name = json.loads((bundle_dir / "manifest.json").read_text()).get("name", name)
    return {"name": name, "genes": genes, "perts": perts, "deltas": deltas, "control_mean": control_mean,
            "n_cells": n_cells, "targets": {p: [str(t) for t in targets.get(p, [])] for p in perts},
            "gene_sets": {k: [str(g) for g in v] for k, v in gene_sets.items()}}


def load_external(bundle_dir: Path, knowledge: str, genes: list[str]) -> dict:
    """The external screen knowledge file, aligned to the bundle's gene order. A bundle gene the file does not
    list, or lists as unmeasured, is NaN in every row."""
    fname = knowledge if knowledge.endswith(".json") else knowledge + ".json"
    raw = json.loads((Path(bundle_dir) / "knowledge" / fname).read_text())
    ext_genes = [str(g) for g in raw["genes"]]
    index = {g: j for j, g in enumerate(ext_genes)}
    pos = np.array([index.get(g, -1) for g in genes], dtype=int)
    present = pos >= 0
    measured_file = np.array([bool(m) for m in raw.get("measured", [True] * len(ext_genes))], dtype=bool)
    measured = np.zeros(len(genes), dtype=bool)
    measured[present] = measured_file[pos[present]]

    def align(values) -> np.ndarray:
        v = np.array([np.nan if x is None else float(x) for x in values], dtype=np.float64)
        out = np.full(len(genes), np.nan)
        out[present] = v[pos[present]]
        out[~measured] = np.nan
        return out

    rows, cells, zero_cell = {}, {}, []
    for target, rec in (raw.get("perts") or {}).items():
        n_cells = rec.get("n_cells")
        if n_cells is not None and int(n_cells) <= 0:
            # a label the file lists but no cell carries (a category a subset file kept): its delta is the
            # control mean negated, not a measurement, so the target counts as missing from the screen
            zero_cell.append(str(target))
            continue
        rows[str(target)] = align(rec["delta"])
        cells[str(target)] = int(n_cells or 0)
    return {"name": fname.removesuffix(".json"), "description": str(raw.get("description", "")),
            "source": raw.get("source", {}), "measured": measured, "rows": rows, "n_cells": cells,
            "n_control_cells": int((raw.get("control") or {}).get("n_cells") or 0), "n_perts": len(rows),
            "n_bundle_targets_missing": len(raw.get("bundle_targets_missing") or []) + len(zero_cell),
            "zero_cell_targets": zero_cell}


# ------------------------------------------------------------------------------------------- predictors

def _jaccard(memberships: list[set]) -> np.ndarray:
    n = len(memberships)
    J = np.zeros((n, n))
    for a in range(n):
        for b in range(a + 1, n):
            union = len(memberships[a] | memberships[b])
            J[a, b] = J[b, a] = len(memberships[a] & memberships[b]) / union if union else 0.0
    return J


def _pairwise_corr(E: np.ndarray, has: np.ndarray) -> np.ndarray:
    """Pearson between external rows over the genes finite in both; NaN where either row is missing."""
    n = E.shape[0]
    C = np.full((n, n), np.nan)
    for a in range(n):
        if not has[a]:
            continue
        for b in range(a + 1, n):
            if not has[b]:
                continue
            m = np.isfinite(E[a]) & np.isfinite(E[b])
            C[a, b] = C[b, a] = pearson_delta(E[a, m], E[b, m]) if m.sum() >= MIN_SHARED_GENES else 0.0
    return C


def _knn(weights: np.ndarray, D: np.ndarray, k: int) -> np.ndarray | None:
    """Weighted mean of the rows of D with the k largest positive weights (NaN counts as zero); None when no
    weight is positive."""
    w = np.where(np.isfinite(weights), weights, 0.0)
    order = np.argsort(-w, kind="stable")[:k]
    order = order[w[order] > 0]
    if order.size == 0:
        return None
    return (w[order] @ D[order]) / w[order].sum()


def _features(i: int, avail: np.ndarray, S: dict, k: int) -> tuple[np.ndarray, dict]:
    """The four stack columns for perturbation i, each a per-gene vector computed from the perturbations in
    `avail` only (i is never in avail). Returns (4 x n_genes, flags naming the fallbacks taken)."""
    D, J, C, E, has = S["deltas"], S["jaccard"], S["ext_corr"], S["ext"], S["has_ext"]
    mean_response = D[avail].mean(axis=0)
    flags = {"geneset_knn": None, "external_direct": None, "external_knn": None}
    gs = _knn(np.where(avail, J[i], 0.0), D, k)
    if gs is None:
        flags["geneset_knn"] = "no positive similarity"
        gs = mean_response
    if has[i]:
        direct = np.where(np.isfinite(E[i]), E[i], mean_response)
        ek = _knn(np.where(avail & has, C[i], 0.0), D, k)
        if ek is None:
            flags["external_knn"] = "no positive neighbour"
            ek = gs
    else:
        flags["external_direct"] = flags["external_knn"] = "no external row"
        direct, ek = mean_response, gs
    return np.stack([mean_response, gs, direct, ek]), flags


# ------------------------------------------------------------------------------------------------ stack

def _group_stats(X: np.ndarray, y: np.ndarray) -> dict:
    return {"n": float(X.shape[0]), "sx": X.sum(axis=0), "sxx": X.T @ X, "sxy": X.T @ y, "sy": float(y.sum())}


def _ridge(stats: dict, alpha: float) -> tuple:
    """Ridge with intercept on standardised columns, from the sums in `stats`; alpha is added to the
    standardised Gram matrix as sklearn's Ridge does."""
    n = stats["n"]
    mu, ybar = stats["sx"] / n, stats["sy"] / n
    cxx = stats["sxx"] - n * np.outer(mu, mu)
    cxy = stats["sxy"] - n * mu * ybar
    sd = np.sqrt(np.maximum(np.diag(cxx) / n, 0.0))
    sd = np.where(sd > 0, sd, 1.0)
    w = np.linalg.solve(cxx / np.outer(sd, sd) + alpha * np.eye(len(mu)), cxy / sd)
    return mu, sd, w, ybar


def _predict(model: tuple, X: np.ndarray) -> np.ndarray:
    mu, sd, w, ybar = model
    return ybar + ((X - mu) / sd) @ w


def _stack(train_cols: list[np.ndarray], train_y: list[np.ndarray], test_cols: np.ndarray,
           alphas=ALPHA_GRID) -> tuple[np.ndarray, float, dict]:
    """Fit the stack on the training perturbations' rows (one group per perturbation), choose alpha by an
    inner leave-one-group-out pearson_delta, refit on all groups and predict the held-out columns."""
    groups = [_group_stats(F.T, y) for F, y in zip(train_cols, train_y)]
    total = {key: sum(g[key] for g in groups) for key in groups[0]}
    inner: dict[str, float] = {}
    best_alpha, best = None, -np.inf
    for alpha in alphas:
        scores = []
        for g, F, y in zip(groups, train_cols, train_y):
            held = {key: total[key] - g[key] for key in total}
            scores.append(pearson_delta(_predict(_ridge(held, alpha), F.T), y))
        inner[str(alpha)] = float(np.mean(scores))
        if inner[str(alpha)] > best:
            best_alpha, best = alpha, inner[str(alpha)]
    model = _ridge(total, best_alpha)
    return _predict(model, test_cols.T), float(best_alpha), {"inner_scores": inner, "weights": [float(x) for x in model[2]]}


# ------------------------------------------------------------- kernel ridge (added after the first reading)

def _unit_rows(E: np.ndarray, has: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Each external row centred over its finite genes and scaled to unit norm, unmeasured or null genes 0, so that
    Z @ Z.T is the Pearson correlation between rows (exactly when the rows share their finite genes, as they do
    in a file whose only gaps are its global "measured" mask; a null inside a measured gene counts as the row's
    mean there). The kernel is positive semidefinite with diagonal 1. A row with fewer than MIN_SHARED_GENES
    finite genes, or none of their spread, is unusable (ok False) and counts as no row for kernel ridge."""
    Z = np.zeros_like(E)
    ok = np.zeros(E.shape[0], dtype=bool)
    for a in np.flatnonzero(has):
        m = np.isfinite(E[a])
        if m.sum() < MIN_SHARED_GENES:
            continue
        x = E[a, m] - E[a, m].mean()
        norm = np.sqrt((x * x).sum())
        if norm > 0:
            Z[a, m], ok[a] = x / norm, True
    return Z, ok


def krr_predict(K: np.ndarray, k: np.ndarray, Y: np.ndarray, ybar: np.ndarray, lam: float) -> np.ndarray:
    """ybar + k^T (K + lam I)^-1 (Y - ybar): kernel ridge over the rows of Y (training changes), K their kernel,
    k their kernel values with the target, ybar the mean change the residuals are taken from."""
    w = np.linalg.solve(K + lam * np.eye(len(K)), k)
    return ybar * (1.0 - w.sum()) + w @ Y


def krr_loo_exact(K: np.ndarray, Y: np.ndarray, ybars: np.ndarray, lam: float) -> np.ndarray:
    """Leave-one-out kernel ridge predictions over the rows of Y, by refitting without each row i; ybars[i] is
    the mean change computed without row i. The reference the closed forms below are tested against."""
    n = len(K)
    out = np.empty_like(Y)
    for i in range(n):
        rest = np.flatnonzero(np.arange(n) != i)
        out[i] = krr_predict(K[np.ix_(rest, rest)], K[rest, i], Y[rest], ybars[i], lam)
    return out


def _loo_weights(K: np.ndarray, lambdas) -> dict:
    """{lambda: W} with W[j, i] the weight row i's leave-one-out refit puts on row j: with A the inverse of
    K + lam I, the refit without i solves (K + lam I)_{-i,-i} w = K_{-i,i}, whose solution is -A[-i, i] / A[i, i]
    (block inversion). One eigendecomposition of K serves every row and every lambda."""
    s, V = np.linalg.eigh(K)
    s = np.clip(s, 0.0, None)
    out = {}
    for lam in lambdas:
        A = (V / (s + lam)) @ V.T
        W = -A / np.diag(A)[None, :]
        np.fill_diagonal(W, 0.0)
        out[lam] = W
    return out


def krr_loo(K: np.ndarray, Y: np.ndarray, ybars: np.ndarray, lambdas=LAMBDA_GRID) -> dict:
    """The predictions of krr_loo_exact for every lambda, in closed form: {lambda: predictions}."""
    return {lam: W.T @ Y + (1.0 - W.sum(axis=0))[:, None] * ybars for lam, W in _loo_weights(K, lambdas).items()}


def krr_loo_scores(K: np.ndarray, Y: np.ndarray, ybars: np.ndarray, lambdas=LAMBDA_GRID) -> dict:
    """{lambda: mean pearson_delta of krr_loo's predictions against the rows of Y}, without forming them: Pearson
    ignores a row's shift, so with Yc, Bc the row-centred Y and ybars the centred prediction of row i is
    sum_j W[j, i] Yc_j + c_i Bc_i (c = 1 - column sums of W), and its products with Yc_i and itself need only
    the Gram matrices Yc Yc^T and Yc Bc^T. Tested equal to scoring krr_loo_exact's predictions."""
    Yc = Y - Y.mean(axis=1, keepdims=True)
    Bc = ybars - ybars.mean(axis=1, keepdims=True)
    G, M = Yc @ Yc.T, Yc @ Bc.T            # G[j, i] = Yc_j . Yc_i, M[j, i] = Yc_j . Bc_i
    yy, mb, bb = np.diag(G), np.diag(M), (Bc * Bc).sum(axis=1)
    out = {}
    for lam, W in _loo_weights(K, lambdas).items():
        c = 1.0 - W.sum(axis=0)
        num = (W * G).sum(axis=0) + c * mb
        pp = np.maximum(((G @ W) * W).sum(axis=0) + 2.0 * c * (W * M).sum(axis=0) + c * c * bb, 0.0)
        den = np.sqrt(pp * yy)
        out[lam] = float(np.mean(np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)))
    return out


def _choose_lambda(scores: dict) -> float:
    """The lambda with the best inner score; scores within TIE_TOL of the best tie, and ties go to the larger."""
    best = max(scores.values())
    return max(lam for lam, sc in scores.items() if sc >= best - TIE_TOL)


def _krr(i: int, avail: np.ndarray, S: dict, lambdas=LAMBDA_GRID) -> dict:
    """external_krr for perturbation i from the labels of the perturbations in `avail` only (i is never in avail):
    ybar = their mean change, R = those with a usable external row, prediction = ybar + k_i^T (K_RR + lam I)^-1
    (Y_R - ybar), lam chosen by an inner leave-one-out over R (row j predicted from R minus j, its ybar computed
    without i and j) scored by pearson_delta. pred None (with a flag) when i has no usable row or R has fewer than
    KRR_MIN_ROWS rows; the caller then falls back."""
    D, Z, ok = S["deltas"], S["krr_z"], S["krr_ok"]
    if not ok[i]:
        return {"pred": None, "lambda": None, "inner": None, "flag": "no external row"}
    R = np.flatnonzero(avail & ok)
    if R.size < KRR_MIN_ROWS:
        return {"pred": None, "lambda": None, "inner": None, "flag": f"fewer than {KRR_MIN_ROWS} rows"}
    total, n_avail = D[avail].sum(axis=0), int(avail.sum())
    Y = D[R]
    K = Z[R] @ Z[R].T
    ybars = (total - Y) / (n_avail - 1)
    inner = krr_loo_scores(K, Y, ybars, lambdas)
    lam = _choose_lambda(inner)
    pred = krr_predict(K, Z[R] @ Z[i], Y, total / n_avail, lam)
    return {"pred": pred, "lambda": float(lam), "inner": inner, "flag": None}


# --------------------------------------------------------------------------------------------- analysis

def _prepare(bundle: dict, external: dict) -> dict:
    """The matrices every fold reads: labels, gene-set Jaccard, external rows (a perturbation's row is that of its
    first target gene with one) and their pairwise correlations, and the unit rows kernel ridge uses."""
    perts, D = bundle["perts"], bundle["deltas"]
    n, n_genes = D.shape
    sets_of: dict[str, set] = {}
    for name, members in bundle["gene_sets"].items():
        for g in members:
            sets_of.setdefault(g, set()).add(name)
    memberships = [set().union(*(sets_of.get(t, set()) for t in bundle["targets"][p])) for p in perts]
    E = np.full((n, n_genes), np.nan)
    has = np.zeros(n, dtype=bool)
    ext_target: list[str | None] = [None] * n
    for i, p in enumerate(perts):
        for t in bundle["targets"][p]:
            if t in external["rows"]:
                E[i], has[i], ext_target[i] = external["rows"][t], True, t
                break
    Z, ok = _unit_rows(E, has)
    return {"deltas": D, "jaccard": _jaccard(memberships), "ext_corr": _pairwise_corr(E, has), "ext": E,
            "has_ext": has, "ext_target": ext_target, "krr_z": Z, "krr_ok": ok}


def _fold(i: int, S: dict, k: int, alphas=ALPHA_GRID, lambdas=LAMBDA_GRID) -> dict:
    """Everything the leave-one-out computes for held-out perturbation i, from the other perturbations' labels
    only: the four stack columns and the stack (pre-specified), and external_krr and the five-column stack (added
    after the first reading). Each training row's columns, its kernel ridge lambda included, are computed without
    that perturbation and without i."""
    D = S["deltas"]
    avail = np.ones(D.shape[0], dtype=bool)
    avail[i] = False
    cols, flags = _features(i, avail, S, k)
    train, train_cols, train_y, train_krr = [], [], [], []
    for q in np.flatnonzero(avail):
        inner_avail = avail.copy()
        inner_avail[q] = False   # q's own columns never see q's label, and never see p's
        q_cols = _features(int(q), inner_avail, S, k)[0]
        q_krr = _krr(int(q), inner_avail, S, lambdas)["pred"]
        train.append(int(q))
        train_cols.append(q_cols)
        train_y.append(D[q])
        train_krr.append(q_cols[1] if q_krr is None else q_krr)   # geneset_knn when kernel ridge falls back
    stacked, alpha, fit = _stack(train_cols, train_y, cols, alphas)
    krr = _krr(i, avail, S, lambdas)
    krr_col = cols[1] if krr["pred"] is None else krr["pred"]
    train_cols5 = [np.vstack([c, q[None]]) for c, q in zip(train_cols, train_krr)]
    cols5 = np.vstack([cols, krr_col[None]])
    stacked_krr, alpha_krr, fit_krr = _stack(train_cols5, train_y, cols5, alphas)
    return {"cols": cols, "flags": {**flags, "external_krr": krr["flag"]}, "stacked": stacked, "alpha": alpha,
            "fit": fit, "krr": krr, "krr_col": krr_col, "train": train, "train_cols5": train_cols5,
            "stacked_krr": stacked_krr, "alpha_krr": alpha_krr, "fit_krr": fit_krr}


def analyse(bundle: dict, external: dict, k: int = 5, alphas=ALPHA_GRID, lambdas=LAMBDA_GRID) -> dict:
    perts, D = bundle["perts"], bundle["deltas"]
    n, n_genes = D.shape
    if n < 3:
        raise ValueError("leave-one-out needs at least three training perturbations")
    S = _prepare(bundle, external)
    E, has, ext_target = S["ext"], S["has_ext"], S["ext_target"]

    rows = []
    for i, p in enumerate(perts):
        f = _fold(i, S, k, alphas, lambdas)
        preds = dict(zip(STACK_COLUMNS, f["cols"]))
        preds["external_stack"] = f["stacked"]
        preds["external_krr"] = f["krr_col"]
        preds["external_stack_krr"] = f["stacked_krr"]
        agreement = None
        if has[i]:
            m = np.isfinite(E[i])
            agreement = float(pearson_delta(D[i, m], E[i, m])) if m.sum() >= MIN_SHARED_GENES else None
        rows.append({
            "pert": p, "target": ", ".join(bundle["targets"][p]) or "?", "external_target": ext_target[i],
            "n_cells_bundle": bundle["n_cells"][i],
            "n_cells_external": external["n_cells"].get(ext_target[i]) if has[i] else None,
            "n_genes_shared": int(np.isfinite(E[i]).sum()) if has[i] else 0,
            "agreement": agreement,
            "scores": {name: float(pearson_delta(preds[name], D[i])) for name in PREDICTORS + ADDED_PREDICTORS},
            "alpha": f["alpha"], "stack_weights": f["fit"]["weights"], "fallbacks": f["flags"],
            # added after the first reading
            "krr_lambda": f["krr"]["lambda"],
            "krr_inner_scores": None if f["krr"]["inner"] is None else
            {str(lam): sc for lam, sc in f["krr"]["inner"].items()},
            "alpha_stack_krr": f["alpha_krr"], "stack_krr_weights": f["fit_krr"]["weights"],
        })

    def paired(name: str, ref: str) -> dict:
        d = np.array([r["scores"][name] - r["scores"][ref] for r in rows])
        return {"wins": int((d > 0).sum()), "mean_diff": float(d.mean()),
                "se_diff": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None}

    n_ext = int(has.sum())
    n_krr = sum(1 for r in rows if r["fallbacks"]["external_krr"] is None)
    predictors = []
    for name in PREDICTORS + ADDED_PREDICTORS:
        s = np.array([r["scores"][name] for r in rows])
        entry = {
            "name": name, "mean": float(s.mean()), "sd": float(s.std(ddof=1)) if n > 1 else None,
            "median": float(np.median(s)), "min": float(s.min()), "max": float(s.max()),
            "vs_mean_response": paired(name, "mean_response"), "vs_geneset_knn": paired(name, "geneset_knn"),
            "coverage": n_krr if name == "external_krr" else n_ext if name.startswith("external") else n,
        }
        if name in ADDED_REFERENCE:
            entry["added_after_first_reading"] = True
            entry[f"vs_{ADDED_REFERENCE[name]}"] = paired(name, ADDED_REFERENCE[name])
        predictors.append(entry)
    agreements = [r["agreement"] for r in rows if r["agreement"] is not None]
    fallbacks = {
        "external_direct_no_row": sum(1 for r in rows if r["fallbacks"]["external_direct"] == "no external row"),
        "external_knn_no_row": sum(1 for r in rows if r["fallbacks"]["external_knn"] == "no external row"),
        "external_knn_no_positive_neighbour":
            sum(1 for r in rows if r["fallbacks"]["external_knn"] == "no positive neighbour"),
        "geneset_knn_no_positive_similarity": sum(1 for r in rows if r["fallbacks"]["geneset_knn"] is not None),
        "external_krr_no_row": sum(1 for r in rows if r["fallbacks"]["external_krr"] == "no external row"),
        "external_krr_too_few_rows":
            sum(1 for r in rows if r["fallbacks"]["external_krr"] == f"fewer than {KRR_MIN_ROWS} rows"),
    }
    return {
        "bundle": bundle["name"], "knowledge": external["name"], "description": external["description"],
        "k": int(k), "alpha_grid": [float(a) for a in alphas], "n_train": int(n), "n_genes": int(n_genes),
        "n_genes_measured_external": int(external["measured"].sum()),
        "external_file": {"n_perts": external["n_perts"], "n_control_cells": external["n_control_cells"],
                          "n_bundle_targets_missing": external["n_bundle_targets_missing"],
                          "zero_cell_targets": list(external.get("zero_cell_targets", []))},
        "coverage": {"with_external_row": n_ext,
                     "without_external_row": [p for p, h in zip(perts, has) if not h]},
        "fallbacks": fallbacks,
        "agreement": {"n": len(agreements), "mean": float(np.mean(agreements)) if agreements else None,
                      "median": float(median(agreements)) if agreements else None,
                      "min": float(min(agreements)) if agreements else None,
                      "max": float(max(agreements)) if agreements else None},
        "alphas_chosen": {str(a): sum(1 for r in rows if r["alpha"] == a) for a in alphas},
        "predictors": predictors,
        "per_perturbation": rows,
        # added after the first reading: a second look, not pre-specified
        "added_after_first_reading": list(ADDED_PREDICTORS),
        "krr_lambda_grid": [float(lam) for lam in lambdas],
        "krr_min_rows": KRR_MIN_ROWS,
        "stack_krr_columns": list(STACK_KRR_COLUMNS),   # the order of each row's stack_krr_weights
        "krr_lambdas_chosen": {str(lam): sum(1 for r in rows if r["krr_lambda"] == lam) for lam in lambdas},
        "alphas_chosen_stack_krr": {str(a): sum(1 for r in rows if r["alpha_stack_krr"] == a) for a in alphas},
    }


# ----------------------------------------------------------------------------------------------- report

def _f(x, nd: int = 3) -> str:
    return "–" if x is None else f"{x:.{nd}f}"


def _signed(x, nd: int = 3) -> str:
    return "–" if x is None else f"{x:+.{nd}f}"


def _int(x) -> str:
    return "–" if x is None else f"{x:,}"


def _reading(rep: dict) -> str:
    n = rep["n_train"]
    P = {p["name"]: p for p in rep["predictors"]}
    gk, ed, ek, es, mr = (P[k] for k in ("geneset_knn", "external_direct", "external_knn", "external_stack",
                                         "mean_response"))
    cov = rep["coverage"]["with_external_row"]
    agr = rep["agreement"]
    out = []
    if cov == 0:
        out.append(f"None of the {n} training perturbations has a row in the external screen, so every external "
                   "predictor collapsed to its fallback and this check says nothing about the screen.")
        return " ".join(out)
    out.append(f"Same-target agreement: for the {agr['n']} training perturbations the external screen also "
               f"measured, the Pearson correlation across measured genes between the bundle's change and the "
               f"external change has median {_f(agr['median'])} (range {_f(agr['min'])} to {_f(agr['max'])}); "
               f"that is how alike the two screens are for the same knockdown, and it bounds what external_direct "
               f"can do.")
    out.append(f"Against the floor, external_direct scores {_f(ed['mean'])} versus mean_response "
               f"{_f(mr['mean'])} (paired difference {_signed(ed['vs_mean_response']['mean_diff'])} "
               f"± {_f(ed['vs_mean_response']['se_diff'])} standard error, better on "
               f"{ed['vs_mean_response']['wins']} of {n}).")
    best = max((ek, es), key=lambda p: p["mean"])
    gain, se, wins = best["vs_geneset_knn"]["mean_diff"], best["vs_geneset_knn"]["se_diff"], best["vs_geneset_knn"]["wins"]
    detail = (f"geneset_knn {_f(gk['mean'])}, external_knn {_f(ek['mean'])} "
              f"({_signed(ek['vs_geneset_knn']['mean_diff'])} ± {_f(ek['vs_geneset_knn']['se_diff'])}, better on "
              f"{ek['vs_geneset_knn']['wins']} of {n}), external_stack {_f(es['mean'])} "
              f"({_signed(es['vs_geneset_knn']['mean_diff'])} ± {_f(es['vs_geneset_knn']['se_diff'])}, better on "
              f"{es['vs_geneset_knn']['wins']} of {n})")
    noise = se is not None and abs(gain) <= 2 * se
    if gain > 0 and not noise and wins > n / 2:
        verdict = (f"The external screen adds information beyond the gene sets on this check: {detail}. The best "
                   f"external predictor ({best['name']}) is ahead of geneset_knn by more than twice its paired "
                   f"standard error and on a majority of perturbations.")
    elif noise or (gain > 0 and wins <= n / 2):
        verdict = (f"No clear gain beyond the gene sets on this check: {detail}. The difference is within about "
                   f"twice its paired standard error or not carried by a majority of perturbations, so the "
                   f"external screen may add nothing the gene sets do not already give.")
    else:
        verdict = (f"The external predictors are behind the gene sets on this check: {detail}. As a transfer "
                   f"feature the screen would have to be used differently, or not at all.")
    out.append(verdict)
    out.append(f"Caveats: this is {n} perturbations of one bundle and one external screen "
               f"({cov} of the {n} targets have an external row; the rest fell back), the scores are leave-one-out "
               f"on training perturbations rather than held-out validation, and a gain here must still be confirmed "
               f"on the sealed set by a labelled arm that is given the knowledge file before it counts.")
    return " ".join(out)


def _g(x) -> str:
    return "–" if x is None else f"{float(x):g}"


def _second_look(rep: dict) -> str:
    """The paragraph after the pre-specified reading on the predictors added after it: each read against the
    predictor it was built to improve on (paired), and said plainly to be a second look."""
    n = rep["n_train"]
    P = {p["name"]: p for p in rep["predictors"]}
    fb = rep["fallbacks"]
    kr, sk, ek, es = P["external_krr"], P["external_stack_krr"], P["external_knn"], P["external_stack"]

    def against(new: dict, ref: dict) -> str:
        v = new[f"vs_{ref['name']}"]
        size = ""
        if v["se_diff"] is not None:
            size = (", within twice its standard error" if abs(v["mean_diff"]) <= 2 * v["se_diff"]
                    else ", more than twice its standard error")
        return (f"{new['name']} scores {_f(new['mean'])} against {ref['name']} {_f(ref['mean'])} "
                f"(paired difference {_signed(v['mean_diff'])} ± {_f(v['se_diff'])}{size}; better on {v['wins']} of "
                f"{n})")

    def chosen(counts: dict) -> str:
        return ", ".join(f"{float(a):g} for {c}" for a, c in counts.items() if c) or "none (every fold fell back)"

    return (f"external_krr and external_stack_krr were designed after the first result of this check was seen, to "
            f"ask whether signed weights on the other perturbations' responses, learned through the external screen, "
            f"do better than the top-k neighbour weights; their numbers are therefore a second look, not "
            f"pre-specified results, and the reading above does not rest on them. external_krr is kernel ridge "
            f"regression through the screen: the mean change of the other training perturbations plus "
            f"k^T (K + lambda I)^-1 (Y - mean), where K is the Pearson correlation between the external rows of the "
            f"other training perturbations that have one, k their correlations with the held-out target's row and Y "
            f"their measured changes, so each response enters with a signed weight; lambda is chosen in every fold "
            f"by an inner leave-one-out over those perturbations from {rep['krr_lambda_grid']} (ties to the larger), "
            f"and geneset_knn stands in when the held-out target has no external row "
            f"({fb['external_krr_no_row']} perturbations) or fewer than {rep['krr_min_rows']} other training "
            f"perturbations have one ({fb['external_krr_too_few_rows']}). external_stack_krr is the ridge stack of "
            f"external_stack over five columns, the four above plus external_krr, each training row's columns (its "
            f"kernel ridge lambda included) computed without that perturbation and without the held-out one, alpha "
            f"chosen as for external_stack from the same grid {rep['alpha_grid']}"
            f"{'' if _is_prespecified_grid(rep) else ' (not the pre-specified one, see the note on external_stack)'}"
            f". {against(kr, ek)}; {against(sk, es)}. Kernel ridge lambda chosen per "
            f"fold: {chosen(rep['krr_lambdas_chosen'])}; five-column stack alpha chosen per fold: "
            f"{chosen(rep['alphas_chosen_stack_krr'])}. Like every number here, a gain must still be confirmed on "
            f"the sealed set by a labelled arm before it counts.")


def _is_prespecified_grid(rep: dict) -> bool:
    return [float(a) for a in rep["alpha_grid"]] == [float(a) for a in ALPHA_GRID]


def _grid_note(rep: dict) -> str:
    """Say so when the stack's grid is not the pre-specified one: its number is then a second look. A report with the
    predictors added after the first reading also says that external_stack_krr picks its alpha from the same grid
    (an older JSON twin, without them, keeps the note it was written with)."""
    if _is_prespecified_grid(rep):
        return ""
    if not rep.get("added_after_first_reading"):
        return (f" This grid is not the pre-specified one ({list(ALPHA_GRID)}): it was chosen after an earlier "
                "reading, so the stack's number here is a second look, not a pre-specified result; the other four "
                "predictors do not depend on it.")
    return (f" This grid is not the pre-specified one ({list(ALPHA_GRID)}): it was chosen after an earlier reading, "
            "so the stack's number here is a second look, not a pre-specified result; the other four pre-specified "
            "predictors do not depend on it. Of the two predictors added after the first reading (last section), "
            "external_stack_krr picks its alpha from this same grid and external_krr does not use it.")


def render(rep: dict) -> str:
    n = rep["n_train"]
    zc = rep["external_file"].get("zero_cell_targets") or []
    L = ["# Does an external screen carry information the transfer features lack?", "",
         f"Leave-one-out over the {n} training perturbations of the `{rep['bundle']}` bundle, visible data only: "
         f"each training perturbation is held out in turn, its expression change (pseudobulk mean minus the control "
         f"mean of public.npz) is predicted from the other {n - 1} training perturbations and the public knowledge "
         f"files, and the prediction is scored by pearson_delta, the Pearson correlation across all "
         f"{rep['n_genes']:,} genes between the predicted and the measured change. Nothing of the held-out "
         f"perturbation's own label reaches any predictor. The protocol, the five predictors and the reading rule "
         f"below were fixed before the external file was opened, and the result is reported whatever it shows. "
         f"The sealed set is never read; this is a reading on whether the external screen deserves a labelled "
         f"arm, not a benchmark score.", "",
         f"External screen: `{rep['knowledge']}`" + (f", {rep['description'].rstrip('.')}" if rep["description"] else "") +
         f". The file holds {rep['external_file']['n_perts']:,} target genes over "
         f"{rep['external_file']['n_control_cells']:,} control cells; {rep['n_genes_measured_external']:,} of the "
         f"bundle's {rep['n_genes']:,} genes are measured in it, and {rep['coverage']['with_external_row']} of the "
         f"{n} training perturbations have a row (their first target gene with one)." +
         (f" The file also lists {len(zc)} bundle target{'s' if len(zc) != 1 else ''} with zero cells "
          f"({', '.join(zc)}); such a row is no measurement and was treated as missing." if zc else ""), "",
         "Predictors (k = %d for both neighbour rules):" % rep["k"], "",
         "- `mean_response`: mean change of the other training perturbations, the floor every feature must beat.",
         "- `geneset_knn`: weighted mean of the other perturbations' changes, weights = Jaccard similarity of the "
         "targets' gene-set memberships (knowledge/gene_sets.json), top k with positive similarity, else "
         "mean_response. The in-bundle reference close to what the agents found.",
         "- `external_direct`: the external change of the same target gene, unmeasured genes filled from "
         "mean_response; mean_response when the target has no external row.",
         "- `external_knn`: weighted mean of the other perturbations' changes, weights = Pearson correlation "
         "between the external changes of the two targets over the genes measured in both, top k with positive "
         "correlation; geneset_knn when the held-out target has no external row or no neighbour correlates "
         "positively.",
         "- `external_stack`: ridge over gene rows combining the four columns above (standardised with the "
         "training rows' statistics), trained on the other perturbations' rows, each row's columns computed "
         "without that perturbation and without the held-out one; alpha chosen by an inner leave-one-out over "
         f"those perturbations from the grid {rep['alpha_grid']}." + _grid_note(rep), "",
         "## Predictors", "",
         "| predictor | pearson_delta, mean ± sd | median | min | max | better than mean_response | paired gain "
         "vs mean_response | better than geneset_knn | paired gain vs geneset_knn | coverage |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for p in rep["predictors"]:
        cov = f"{p['coverage']} of {n}" + ("" if p["name"].startswith("external") else " (no external input)")
        cells = []
        for ref in ("mean_response", "geneset_knn"):
            v = p[f"vs_{ref}"]
            cells += ["–", "–"] if p["name"] == ref else [f"{v['wins']} of {n}",
                                                           f"{_signed(v['mean_diff'])} ± {_f(v['se_diff'])}"]
        L.append(f"| {p['name']} | {_f(p['mean'])} ± {_f(p['sd'])} | {_f(p['median'])} | {_f(p['min'])} | "
                 f"{_f(p['max'])} | " + " | ".join(cells) + f" | {cov} |")
    fb = rep["fallbacks"]
    added = rep.get("added_after_first_reading") or []   # absent from a report written before the second look
    L += ["",
          "\"Better than\" counts perturbations whose score is strictly higher, paired; the paired gain is the mean "
          "difference ± its standard error over the perturbations. Fallbacks taken: external_direct used "
          f"mean_response for {fb['external_direct_no_row']} perturbations without an external row; external_knn "
          f"used geneset_knn for {fb['external_knn_no_row']} without a row and "
          f"{fb['external_knn_no_positive_neighbour']} without a positively correlated neighbour; geneset_knn used "
          f"mean_response for {fb['geneset_knn_no_positive_similarity']} without a positively similar "
          "perturbation. Stack alpha chosen per fold: " +
          ", ".join(f"{float(a):g} for {c}" for a, c in rep["alphas_chosen"].items() if c) + "." +
          (f" The last {len(added)} rows ({', '.join(added)}) were added after the first reading; they are defined "
           "and read in the last section." if added else ""), "",
          "## Per perturbation", "",
          "| perturbation | target | cells (bundle) | cells (external) | genes shared | same-target agreement | "
          "mean_response | geneset_knn | external_direct | external_knn | external_stack | alpha |" +
          (" external_krr | external_stack_krr | KRR lambda | alpha (stack_krr) |" if added else ""),
          "|---|---|---|---|---|---|---|---|---|---|---|---|" + ("---|---|---|---|" if added else "")]
    for r in rep["per_perturbation"]:
        s = r["scores"]
        L.append(f"| {r['pert']} | {r['target']} | {_int(r['n_cells_bundle'])} | {_int(r['n_cells_external'])} | "
                 f"{r['n_genes_shared']:,} | {_f(r['agreement'])} | {_f(s['mean_response'])} | {_f(s['geneset_knn'])} "
                 f"| {_f(s['external_direct'])} | {_f(s['external_knn'])} | {_f(s['external_stack'])} | "
                 f"{r['alpha']:g} |" +
                 (f" {_f(s['external_krr'])} | {_f(s['external_stack_krr'])} | {_g(r['krr_lambda'])} | "
                  f"{_g(r['alpha_stack_krr'])} |" if added else ""))
    L += ["", "Same-target agreement is the Pearson correlation across the genes measured in both screens between "
          "the bundle's change and the external change for the same target gene; cells are the perturbed cells "
          "behind each side's mean. A dash means no external row.", "",
          "## Reading", "", _reading(rep)]
    if added:
        L += ["", "## Added after the first reading (a second look)", "", _second_look(rep)]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bundle", help="bundle directory (public.npz, knowledge/)")
    ap.add_argument("--knowledge", help="name of the external screen knowledge file, knowledge/<name>.json")
    ap.add_argument("--k", type=int, default=5, help="neighbours for geneset_knn and external_knn (default 5)")
    ap.add_argument("--alpha-grid", type=float, nargs="+", default=None,
                    help=f"ridge alphas for the stack (default the pre-specified {list(ALPHA_GRID)}; another grid is "
                         "named in the report as a second look)")
    ap.add_argument("--out", required=True, help="markdown report")
    ap.add_argument("--json", help="JSON twin of the report (default: --out with a .json suffix)")
    ap.add_argument("--from-json", help="re-render the markdown from a JSON twin written by an earlier call "
                                        "(the bundle is not read and the twin is left as it is)")
    args = ap.parse_args(argv)
    if bool(args.from_json) == bool(args.bundle and args.knowledge):
        ap.error("give --bundle and --knowledge, or --from-json, not both")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.from_json:
        rep = json.loads(Path(args.from_json).read_text())
    else:
        t0 = time.time()
        bundle = load_bundle(Path(args.bundle))
        external = load_external(Path(args.bundle), args.knowledge, bundle["genes"])
        rep = analyse(bundle, external, k=args.k, alphas=tuple(args.alpha_grid) if args.alpha_grid else ALPHA_GRID)
        rep["runtime_s"] = round(time.time() - t0, 2)
        Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1))
    md = render(rep)
    out.write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
