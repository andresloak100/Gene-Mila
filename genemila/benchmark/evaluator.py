"""Deterministic evaluation of perturbation predictions.

All metrics are computed per perturbation and averaged. "delta" means
expression minus the control mean, which is the quantity that actually carries
perturbation information; raw-expression correlations are reported too but are
dominated by baseline expression.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import PRIMARY_METRIC, SELECTION_RULES, TOP_DE, selection_score

# A category of fewer perturbations reports its n only: one perturbation's mean is its own value, and two
# perturbations' mean and sd give both values back, so neither may leave the oracle. The pooled mean is returned
# beside the categories, so a hidden category is never hidden alone (hidden_categories): the pooled sum minus the
# reported categories' sums gives the hidden members' sum, which must cover CATEGORY_MIN_N perturbations too.
CATEGORY_MIN_N = 3


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else 0.0


def _r2(truth: np.ndarray, pred: np.ndarray) -> float:
    ss_tot = ((truth - truth.mean()) ** 2).sum()
    return float(1 - ((truth - pred) ** 2).sum() / ss_tot) if ss_tot > 0 else 0.0


def evaluate(pred: np.ndarray, truth: np.ndarray, control_mean: np.ndarray, perts: list[str] | None = None,
             top_de: int = TOP_DE, selection: str = PRIMARY_METRIC, *, targets: dict | None = None,
             categories: dict | None = None) -> dict:
    """pred, truth: (n_perts, n_genes) expression. Returns metrics + diagnostics; `primary` is the selection
    score under `selection` (see SELECTION_RULES).

    Two extras, both off by default (the lab and the oracle pass them only for a bundle with strata, see
    bundle_strata, so every other bundle is scored exactly as before): with targets (perturbation -> column
    indices of its own target genes) every perturbation also gets `pearson_delta_nontarget`, pearson_delta over
    the genes other than its targets, whose mean joins the metrics like any other; with categories (perturbation
    -> category) the metrics gain `by_category` (category_summary: mean, sd and n per category). Neither changes
    `primary`, so selection is untouched."""
    if selection not in SELECTION_RULES:
        raise ValueError(f"unknown selection rule {selection!r}; one of {sorted(SELECTION_RULES)}")
    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, dtype=np.float64)
    if pred.shape != truth.shape:
        raise ValueError(f"prediction shape {pred.shape} != truth shape {truth.shape}")
    if not np.all(np.isfinite(pred)):
        raise ValueError("predictions contain NaN or infinite values")
    d_pred = pred - control_mean
    d_true = truth - control_mean
    err = pred - truth

    per_pert = []
    for i in range(truth.shape[0]):
        top = np.argsort(-np.abs(d_true[i]))[:top_de]
        per_pert.append({
            "pearson_delta": _pearson(d_pred[i], d_true[i]),
            "pearson_delta_top": _pearson(d_pred[i, top], d_true[i, top]),
            "direction_acc_top": float(np.mean(np.sign(d_pred[i, top]) == np.sign(d_true[i, top]))),
            "mse_top": float(np.mean(err[i, top] ** 2)),
            "r2_top": _r2(truth[i, top], pred[i, top]),
            "pearson_expr": _pearson(pred[i], truth[i]),
        })
    names = perts or [str(i) for i in range(len(per_pert))]
    if targets is not None:
        for i, name in enumerate(names):
            keep = np.ones(truth.shape[1], dtype=bool)
            keep[list(targets.get(name) or [])] = False
            per_pert[i]["pearson_delta_nontarget"] = _pearson(d_pred[i, keep], d_true[i, keep])
    metrics = {
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mae": float(np.mean(np.abs(err))),
        "mse": float(np.mean(err ** 2)),
    }
    for key in per_pert[0]:
        metrics[key] = float(np.mean([p[key] for p in per_pert]))
    metrics["primary"] = selection_score(metrics, selection)
    metrics["selection_rule"] = selection
    if categories is not None:
        metrics["by_category"] = category_summary(dict(zip(names, per_pert)), categories)

    # Diagnostics: where the errors are. Safe to show agents (aggregates only).
    order = np.argsort([p["pearson_delta"] for p in per_pert])
    expr_q = np.quantile(control_mean, [0.25, 0.5, 0.75])
    bins = np.digitize(control_mean, expr_q)
    diagnostics = {
        "worst_perturbations": [{"pert": names[i], "pearson_delta": round(per_pert[i]["pearson_delta"], 3)}
                                for i in order[:5]],
        "best_perturbations": [{"pert": names[i], "pearson_delta": round(per_pert[i]["pearson_delta"], 3)}
                               for i in order[::-1][:3]],
        "rmse_by_control_expression_quartile": [
            round(float(np.sqrt(np.mean(err[:, bins == b] ** 2))), 4) for b in range(4)
        ],
        "mean_abs_true_delta": round(float(np.mean(np.abs(d_true))), 4),
        "mean_abs_pred_delta": round(float(np.mean(np.abs(d_pred))), 4),
        "delta_scale_ratio": round(float(np.mean(np.abs(d_pred)) / max(1e-12, np.mean(np.abs(d_true)))), 3),
    }
    return {"metrics": metrics, "diagnostics": diagnostics, "per_perturbation": dict(zip(names, per_pert))}


def hidden_categories(sizes: dict[str, int], loose: int = 0) -> set[str]:
    """The categories that report their n only, from each category's number of scored perturbations and the number
    of scored perturbations without a category (`loose`, pooled but in no category): every category of fewer than
    CATEGORY_MIN_N, and then, while the hidden members (loose ones included) number more than 0 but fewer than
    CATEGORY_MIN_N and some category is still reported, the smallest reported category as well (ties by name).
    Complementary suppression: the pooled mean over every scored perturbation, which the oracle also returns, times
    their number, minus each reported category's n times its mean, is the sum over the hidden members, so that sum
    must never be one or two perturbations' values. With no category below CATEGORY_MIN_N and nothing loose,
    nothing is hidden."""
    hidden = {c for c, n in sizes.items() if n < CATEGORY_MIN_N}
    while 0 < loose + sum(sizes[c] for c in hidden) < CATEGORY_MIN_N and len(hidden) < len(sizes):
        hidden.add(min((c for c in sizes if c not in hidden), key=lambda c: (sizes[c], c)))
    return hidden


def category_summary(per_pert: dict[str, dict], categories: dict[str, str]) -> dict:
    """{category: {"n": n, metric: {"mean": m, "sd": s}, ...}} over the scored perturbations that have a category
    (the others are left out), sd with ddof 1, for every per-perturbation metric; a category in hidden_categories
    (fewer than CATEGORY_MIN_N perturbations, or the smallest ones that keep the hidden members at CATEGORY_MIN_N
    or more) reports its n only. Aggregates only, so the oracle may return it."""
    groups: dict[str, list[dict]] = {}
    loose = 0
    for name, vals in per_pert.items():
        if categories.get(name) is not None:
            groups.setdefault(str(categories[name]), []).append(vals)
        else:
            loose += 1
    hidden = hidden_categories({c: len(v) for c, v in groups.items()}, loose)
    out = {}
    for cat in sorted(groups):
        rows = groups[cat]
        entry: dict = {"n": len(rows)}
        if cat not in hidden:
            for key in rows[0]:
                v = np.array([r[key] for r in rows], dtype=np.float64)
                entry[key] = {"mean": float(v.mean()), "sd": float(v.std(ddof=1))}
        out[cat] = entry
    return out


def categories_of(perts: list[str], targets: dict[str, list[str]], train: list[str]) -> dict[str, str]:
    """Each perturbation's category against a training set, by the rule of the gene-grouped split
    (genemila.data.bundle.pert_category): "single" for one target, else "pair_seenK" with K the number of its
    targets whose single-gene perturbation is in `train`."""
    seen = {targets[p][0] for p in train if len(targets.get(p) or []) == 1}
    out = {}
    for p in perts:
        tg = list(targets.get(p) or [])
        out[p] = "single" if len(tg) == 1 else f"pair_seen{sum(1 for g in tg if g in seen)}"
    return out


def metric_values(per_pert: dict[str, dict], metric: str, selection: str = PRIMARY_METRIC) -> dict[str, float]:
    """One per-perturbation metric of an evaluate() result's per_perturbation; "primary" is the selection rule
    applied to each perturbation's own metrics, so its mean is the pooled primary."""
    if metric == "primary":
        return {p: selection_score(v, selection) for p, v in per_pert.items()}
    missing = [p for p, v in per_pert.items() if metric not in v]
    if missing:
        raise ValueError(f"metric {metric!r} is not scored per perturbation here (e.g. for {missing[0]!r})")
    return {p: float(v[metric]) for p, v in per_pert.items()}


def _paired(diff: np.ndarray) -> dict:
    n = len(diff)
    out: dict = {"n": n}
    if n < CATEGORY_MIN_N:
        return out
    mean, se = float(diff.mean()), float(diff.std(ddof=1) / np.sqrt(n))
    wins_a, wins_b = int((diff > 0).sum()), int((diff < 0).sum())
    verdict = "a" if mean > 2 * se and wins_a > n / 2 else "b" if -mean > 2 * se and wins_b > n / 2 else "none"
    out.update(mean_diff=mean, se=se, wins_a=wins_a, wins_b=wins_b, ties=n - wins_a - wins_b, verdict=verdict)
    return out


def paired_summary(a: dict[str, float], b: dict[str, float], categories: dict[str, str] | None = None) -> dict:
    """Paired comparison of two models' per-perturbation scores over the perturbations both score, a minus b:
    n, the mean difference, its paired standard error (sd of the differences, ddof 1, over sqrt n), the
    perturbations each side wins and the ties, and the reading rule's verdict: "a" (or "b") when the mean gain
    exceeds twice its paired SE and that side wins on more than half the perturbations, else "none". With
    categories, the same within each category under "by_category" (perturbations without one left out). Below
    CATEGORY_MIN_N perturbations only n is reported, and a category in hidden_categories reports its n only, as in
    category_summary, so the pooled answer minus the reported categories never isolates one perturbation's
    difference or winner. Aggregates only."""
    common = [p for p in a if p in b]
    diff = {p: float(a[p]) - float(b[p]) for p in common}
    out = _paired(np.array([diff[p] for p in common], dtype=np.float64))
    if categories is not None:
        groups: dict[str, list[float]] = {}
        for p in common:
            if categories.get(p) is not None:
                groups.setdefault(str(categories[p]), []).append(diff[p])
        hidden = hidden_categories({c: len(v) for c, v in groups.items()},
                                   sum(1 for p in common if categories.get(p) is None))
        out["by_category"] = {c: ({"n": len(groups[c])} if c in hidden else
                                  _paired(np.array(groups[c], dtype=np.float64))) for c in sorted(groups)}
    return out


def bundle_strata(data_dir: Path) -> dict | None:
    """What a bundle is scored by beyond the pooled metrics, read from the bundle itself (manifest, splits.json,
    targets and the public gene and training lists). None for a bundle whose perturbations all have one target,
    whose split is not gene-grouped and that records no modality (Adamson's): it is scored exactly as before.
    Otherwise {"targets": perturbation -> target genes, "target_idx": perturbation -> their columns (for
    pearson_delta_nontarget), "grouped": True for a bundle with pairs or a gene-grouped split (whose
    cross-validation folds the lab groups by gene and whose perturbations are scored by category), "categories":
    the held-out perturbations' categories (as splits.json records them, else derived by categories_of against
    the training set; empty when not grouped)}."""
    data_dir = Path(data_dir)
    manifest = json.loads((data_dir / "manifest.json").read_text())
    splits = json.loads((data_dir / "splits.json").read_text())
    targets = {str(p): [str(g) for g in v] for p, v in
               json.loads((data_dir / "knowledge" / "targets.json").read_text()).items()}
    grouped = any(len(v) > 1 for v in targets.values()) or splits.get("mode") == "gene"
    if not grouped and not splits.get("categories") and not manifest.get("modality"):
        return None
    z = np.load(data_dir / "public.npz", allow_pickle=False)
    col = {str(g): i for i, g in enumerate(z["genes"])}
    categories = {str(p): str(c) for p, c in (splits.get("categories") or {}).items()}
    if grouped and not categories:
        categories = categories_of(list(splits["val1"]) + list(splits["val2"]), targets,
                                   [str(p) for p in z["train_perts"]])
    return {"targets": targets, "target_idx": {p: [col[g] for g in v if g in col] for p, v in targets.items()},
            "grouped": bool(grouped), "categories": categories}


def is_better(a: float | None, b: float | None, higher_is_better: bool = True) -> bool:
    if a is None:
        return False
    if b is None:
        return True
    return a > b if higher_is_better else a < b
