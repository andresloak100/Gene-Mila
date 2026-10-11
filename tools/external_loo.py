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
ALPHA_GRID = (0.1, 1.0, 10.0, 100.0, 1000.0)
MIN_SHARED_GENES = 3   # genes two external rows must share before their correlation is used as a weight


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

    rows, cells = {}, {}
    for target, rec in (raw.get("perts") or {}).items():
        rows[str(target)] = align(rec["delta"])
        cells[str(target)] = int(rec.get("n_cells") or 0)
    return {"name": fname.removesuffix(".json"), "description": str(raw.get("description", "")),
            "source": raw.get("source", {}), "measured": measured, "rows": rows, "n_cells": cells,
            "n_control_cells": int((raw.get("control") or {}).get("n_cells") or 0), "n_perts": len(rows),
            "n_bundle_targets_missing": len(raw.get("bundle_targets_missing") or [])}


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


# --------------------------------------------------------------------------------------------- analysis

def analyse(bundle: dict, external: dict, k: int = 5, alphas=ALPHA_GRID) -> dict:
    perts, D = bundle["perts"], bundle["deltas"]
    n, n_genes = D.shape
    if n < 3:
        raise ValueError("leave-one-out needs at least three training perturbations")
    sets_of: dict[str, set] = {}
    for name, members in bundle["gene_sets"].items():
        for g in members:
            sets_of.setdefault(g, set()).add(name)
    memberships = [set().union(*(sets_of.get(t, set()) for t in bundle["targets"][p])) for p in perts]
    # a perturbation's external row is that of its first target gene with one
    E = np.full((n, n_genes), np.nan)
    has = np.zeros(n, dtype=bool)
    ext_target: list[str | None] = [None] * n
    for i, p in enumerate(perts):
        for t in bundle["targets"][p]:
            if t in external["rows"]:
                E[i], has[i], ext_target[i] = external["rows"][t], True, t
                break
    S = {"deltas": D, "jaccard": _jaccard(memberships), "ext_corr": _pairwise_corr(E, has), "ext": E, "has_ext": has}

    rows = []
    for i, p in enumerate(perts):
        avail = np.ones(n, dtype=bool)
        avail[i] = False
        cols, flags = _features(i, avail, S, k)
        train_cols, train_y = [], []
        for q in np.flatnonzero(avail):
            inner_avail = avail.copy()
            inner_avail[q] = False   # q's own columns never see q's label, and never see p's
            train_cols.append(_features(int(q), inner_avail, S, k)[0])
            train_y.append(D[q])
        stacked, alpha, fit = _stack(train_cols, train_y, cols, alphas)
        preds = dict(zip(STACK_COLUMNS, cols))
        preds["external_stack"] = stacked
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
            "scores": {name: float(pearson_delta(preds[name], D[i])) for name in PREDICTORS},
            "alpha": alpha, "stack_weights": fit["weights"], "fallbacks": flags,
        })

    def paired(name: str, ref: str) -> dict:
        d = np.array([r["scores"][name] - r["scores"][ref] for r in rows])
        return {"wins": int((d > 0).sum()), "mean_diff": float(d.mean()),
                "se_diff": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None}

    n_ext = int(has.sum())
    predictors = []
    for name in PREDICTORS:
        s = np.array([r["scores"][name] for r in rows])
        predictors.append({
            "name": name, "mean": float(s.mean()), "sd": float(s.std(ddof=1)) if n > 1 else None,
            "median": float(np.median(s)), "min": float(s.min()), "max": float(s.max()),
            "vs_mean_response": paired(name, "mean_response"), "vs_geneset_knn": paired(name, "geneset_knn"),
            "coverage": n_ext if name.startswith("external") else n,
        })
    agreements = [r["agreement"] for r in rows if r["agreement"] is not None]
    fallbacks = {
        "external_direct_no_row": sum(1 for r in rows if r["fallbacks"]["external_direct"] == "no external row"),
        "external_knn_no_row": sum(1 for r in rows if r["fallbacks"]["external_knn"] == "no external row"),
        "external_knn_no_positive_neighbour":
            sum(1 for r in rows if r["fallbacks"]["external_knn"] == "no positive neighbour"),
        "geneset_knn_no_positive_similarity": sum(1 for r in rows if r["fallbacks"]["geneset_knn"] is not None),
    }
    return {
        "bundle": bundle["name"], "knowledge": external["name"], "description": external["description"],
        "k": int(k), "alpha_grid": [float(a) for a in alphas], "n_train": int(n), "n_genes": int(n_genes),
        "n_genes_measured_external": int(external["measured"].sum()),
        "external_file": {"n_perts": external["n_perts"], "n_control_cells": external["n_control_cells"],
                          "n_bundle_targets_missing": external["n_bundle_targets_missing"]},
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


def render(rep: dict) -> str:
    n = rep["n_train"]
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
         f"External screen: `{rep['knowledge']}`" + (f", {rep['description']}" if rep["description"] else "") +
         f". The file holds {rep['external_file']['n_perts']:,} target genes over "
         f"{rep['external_file']['n_control_cells']:,} control cells; {rep['n_genes_measured_external']:,} of the "
         f"bundle's {rep['n_genes']:,} genes are measured in it, and {rep['coverage']['with_external_row']} of the "
         f"{n} training perturbations have a row (their first target gene with one).", "",
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
         f"those perturbations from the grid {rep['alpha_grid']}.", "",
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
    L += ["",
          "\"Better than\" counts perturbations whose score is strictly higher, paired; the paired gain is the mean "
          "difference ± its standard error over the perturbations. Fallbacks taken: external_direct used "
          f"mean_response for {fb['external_direct_no_row']} perturbations without an external row; external_knn "
          f"used geneset_knn for {fb['external_knn_no_row']} without a row and "
          f"{fb['external_knn_no_positive_neighbour']} without a positively correlated neighbour; geneset_knn used "
          f"mean_response for {fb['geneset_knn_no_positive_similarity']} without a positively similar "
          "perturbation. Stack alpha chosen per fold: " +
          ", ".join(f"{float(a):g} for {c}" for a, c in rep["alphas_chosen"].items() if c) + ".", "",
          "## Per perturbation", "",
          "| perturbation | target | cells (bundle) | cells (external) | genes shared | same-target agreement | "
          "mean_response | geneset_knn | external_direct | external_knn | external_stack | alpha |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rep["per_perturbation"]:
        s = r["scores"]
        L.append(f"| {r['pert']} | {r['target']} | {_int(r['n_cells_bundle'])} | {_int(r['n_cells_external'])} | "
                 f"{r['n_genes_shared']:,} | {_f(r['agreement'])} | {_f(s['mean_response'])} | {_f(s['geneset_knn'])} "
                 f"| {_f(s['external_direct'])} | {_f(s['external_knn'])} | {_f(s['external_stack'])} | "
                 f"{r['alpha']:g} |")
    L += ["", "Same-target agreement is the Pearson correlation across the genes measured in both screens between "
          "the bundle's change and the external change for the same target gene; cells are the perturbed cells "
          "behind each side's mean. A dash means no external row.", "",
          "## Reading", "", _reading(rep)]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bundle", help="bundle directory (public.npz, knowledge/)")
    ap.add_argument("--knowledge", help="name of the external screen knowledge file, knowledge/<name>.json")
    ap.add_argument("--k", type=int, default=5, help="neighbours for geneset_knn and external_knn (default 5)")
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
        rep = analyse(bundle, external, k=args.k)
        rep["runtime_s"] = round(time.time() - t0, 2)
        Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1))
    md = render(rep)
    out.write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
