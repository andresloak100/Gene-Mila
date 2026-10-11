"""Experiment execution. Runs inside an isolated subprocess, inside a worktree.

It sees only the public data copy: control cells, training labels and
perturbation metadata. It predicts every non-training perturbation without
knowing which are visible-validation and which are query-only; the controller
scores the predictions with its own evaluator.

Usage:
    python -m genemila.pipeline run   --spec spec.json --public DIR --plugins DIR --out DIR
    python -m genemila.pipeline smoke --feature NAME --public DIR --plugins DIR --out DIR
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import pickle
import sys
import time
import traceback
from pathlib import Path

import numpy as np

from .features import registry
from .features.api import FeatureContext, _atomic_save


_SOURCE_HASH: dict[str, str] = {}


def _source_hash(cls) -> str:
    path = inspect.getsourcefile(cls)
    if path not in _SOURCE_HASH:
        with open(path, "rb") as fh:
            _SOURCE_HASH[path] = hashlib.sha256(fh.read()).hexdigest()
    return _SOURCE_HASH[path]


def feature_cache_key(ctx: FeatureContext, cls, params: dict, perts: list[str]) -> str:
    """Identifies a computed feature block: same code, parameters, data and perturbations."""
    manifest = json.loads((ctx.public_dir / "manifest.json").read_text())
    deps = sorted((d, _source_hash(registry.get(d))) for d in cls.dependencies if d in registry.REGISTRY)
    payload = json.dumps([cls.name, cls.version, _source_hash(cls), params, deps, manifest.get("name"),
                          manifest.get("split_id"), list(perts), ctx.train_signature], sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def feature_blocks(ctx: FeatureContext, feature_set: list[str], feature_params: dict, perts: list[str],
                   timings: dict, cache_dir: Path | None = None, cache_log: dict | None = None,
                   label_dep: dict | None = None) -> dict[str, np.ndarray]:
    """One (n_perts, n_genes, dim) block per feature. label_dep, when given, records per feature whether
    computing it read training labels (a cached block carries the flag in a sidecar file; a block whose
    flag is unknown counts as label-dependent)."""
    blocks = {}
    for name in feature_set:
        cls = registry.get(name)
        params = {**cls.params, **feature_params.get(name, {})}
        t0 = time.process_time()
        path = cache_dir / f"{name}__{feature_cache_key(ctx, cls, params, perts)}.npy" if cache_dir else None
        arr, dep = None, True
        if path is not None and path.exists():
            try:
                arr = np.load(path, allow_pickle=False)
                side = path.with_suffix(".dep")
                dep = side.read_text().strip() != "0" if side.exists() else True
            except (OSError, ValueError):  # evicted or half-written by another process: recompute
                arr = None
            else:
                if cache_log is not None:
                    cache_log.setdefault("hits", []).append(name)
        if arr is None:
            before = ctx.label_reads
            arr = np.asarray(cls().compute(ctx, perts, params), dtype=np.float64)
            dep = ctx.label_reads > before
            if path is not None and np.all(np.isfinite(arr)):
                _atomic_save(path, arr)
                path.with_suffix(".dep").write_text("1" if dep else "0")
                if cache_log is not None:
                    cache_log.setdefault("misses", []).append(name)
        timings[name] = timings.get(name, 0.0) + time.process_time() - t0
        if arr.ndim == 2:
            arr = arr[:, :, None]
        if arr.shape[:2] != (len(perts), ctx.n_genes):
            raise ValueError(f"feature {name} returned shape {arr.shape}, expected ({len(perts)}, {ctx.n_genes}, dim)")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"feature {name} produced NaN/inf values")
        blocks[name] = arr
        if label_dep is not None:
            label_dep[name] = label_dep.get(name, False) or dep
    return blocks


def _concat(blocks: dict[str, np.ndarray], feature_set: list[str], n_perts: int, n_genes: int) -> tuple[np.ndarray, list[str]]:
    columns = []
    for name in feature_set:
        d = blocks[name].shape[2]
        columns += [name] if d == 1 else [f"{name}[{j}]" for j in range(d)]
    X = np.concatenate([blocks[n] for n in feature_set], axis=2)
    return X.reshape(n_perts * n_genes, X.shape[2]), columns


def build_matrix(ctx: FeatureContext, feature_set: list[str], feature_params: dict, perts: list[str],
                 timings: dict, cache_dir: Path | None = None, cache_log: dict | None = None,
                 label_dep: dict | None = None) -> tuple[np.ndarray, list[str]]:
    blocks = feature_blocks(ctx, feature_set, feature_params, perts, timings, cache_dir, cache_log, label_dep)
    return _concat(blocks, feature_set, len(perts), ctx.n_genes)


CV_GROUPS = (None, "gene")  # the run's fold grouping (hyperparameter cv_groups, set by the lab, never by an agent)


def cv_folds_of(train: list[str], k: int, seed: int, targets: dict[str, list[str]] | None = None
                ) -> list[tuple[list[str], list[str]]]:
    """Deterministic K folds over the training perturbations (same folds for every experiment of a run), each a
    pair (predict, hide): the fold's out-of-fold predictions are made for `predict` by a model and features that
    see the training labels without `hide`. The `predict` sets partition the training perturbations.

    Without targets the folds are random over names and hide equals predict (every single-target bundle without
    a gene split: Adamson's folds are unchanged). With targets (perturbation -> target genes; the lab passes them
    for a bundle with pairs or a gene-grouped split) the folds are grouped by gene, as the sealed split is: the
    genes named by the training perturbations, sorted and permuted by the seed, are dealt into K folds; a
    perturbation is predicted in the lowest fold of its genes (a single in its gene's fold) and hidden from every
    fold holding one of its genes. So no view holds a perturbation sharing a gene with a single it predicts, a
    pair is predicted with none or one of its singles in the view's training set, and a pair stays out of the
    view of every fold of its genes. A perturbation without a listed target is grouped alone, under its own name.
    Folds that predict nothing (more folds than genes) are left out."""
    if targets is None:
        order = list(np.random.default_rng(seed).permutation(sorted(train)))
        return [(sorted(order[i::k]), sorted(order[i::k])) for i in range(k)]
    genes_of = {p: sorted(set(targets.get(p) or [])) or [f"\0{p}"] for p in train}
    order = list(np.random.default_rng(seed).permutation(sorted({g for gs in genes_of.values() for g in gs})))
    fold_of = {g: i % k for i, g in enumerate(order)}
    folds = []
    for i in range(k):
        predict = sorted(p for p in train if min(fold_of[g] for g in genes_of[p]) == i)
        hide = sorted(p for p in train if any(fold_of[g] == i for g in genes_of[p]))
        if predict:
            folds.append((predict, hide))
    return folds


def cv_fold_targets(ctx: FeatureContext, groups: str | None) -> dict[str, list[str]] | None:
    """What cv_folds_of groups a context's training perturbations by under a run's cv_groups setting: nothing
    (None: random folds over names) or, for "gene", every training perturbation's target genes."""
    if groups not in CV_GROUPS:
        raise ValueError(f"unknown cv_groups {groups!r} (allowed: {', '.join(map(str, CV_GROUPS))})")
    return None if groups is None else {p: ctx.target_genes(p) for p in ctx.train_perts}


def cross_validate(ctx: FeatureContext, feature_set: list[str], feature_params: dict, model_type: str,
                   alphas: list[float], seed: int, k: int, fold_seed: int, timings: dict, feature_cache,
                   cache_log, train_blocks: dict[str, np.ndarray], label_dep: dict[str, bool],
                   groups: str | None = None) -> np.ndarray:
    """Out-of-fold predicted deltas for every training perturbation, per alpha: (n_alphas, n_train, n_genes).

    Each fold is a context whose training labels exclude the fold's hidden perturbations, so feature code (which
    may only read training labels) recomputes its features without them; the fold's model is fitted on the rest
    and predicts the fold's own perturbations. The predictions are therefore honest out-of-sample predictions,
    like those for the held-out sets. Under random folds (groups None) a fold hides exactly what it predicts;
    under gene-grouped folds (groups "gene", see cv_folds_of) it also hides every training perturbation sharing
    a gene of the fold. Features that never read training labels are the same under every view, so their rows
    are sliced from the full-training blocks instead of recomputed. Plugin modules are re-executed before each
    fold so no module-level memo can carry full-training aggregates into a fold."""
    pos = {p: i for i, p in enumerate(ctx.train_perts)}
    out = np.zeros((len(alphas), len(ctx.train_perts), ctx.n_genes), dtype=np.float32)
    for fold, hide in cv_folds_of(ctx.train_perts, k, fold_seed, cv_fold_targets(ctx, groups)):
        registry.reload_plugins()
        view = ctx.without_train(hide)
        both = view.train_perts + fold
        dep_feats = [f for f in feature_set if label_dep.get(f, True)]
        fresh = feature_blocks(view, dep_feats, feature_params, both, timings, feature_cache, cache_log)
        n_tr = len(view.train_perts)
        tr_rows = [pos[p] for p in view.train_perts]
        fo_rows = [pos[p] for p in fold]
        blocks_tr = {f: (fresh[f][:n_tr] if f in fresh else train_blocks[f][tr_rows]) for f in feature_set}
        blocks_fo = {f: (fresh[f][n_tr:] if f in fresh else train_blocks[f][fo_rows]) for f in feature_set}
        X_tr, _ = _concat(blocks_tr, feature_set, n_tr, ctx.n_genes)
        X_fo, _ = _concat(blocks_fo, feature_set, len(fold), ctx.n_genes)
        _, d_tr = view.train_delta()
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd == 0] = 1.0
        X_tr, X_fo = (X_tr - mu) / sd, (X_fo - mu) / sd
        for j, a in enumerate(alphas):
            model = make_model(model_type, a, seed)
            model.fit(X_tr, d_tr.reshape(-1))
            pred = model.predict(X_fo).reshape(len(fold), ctx.n_genes)
            if not np.all(np.isfinite(pred)):
                raise ValueError(f"model produced non-finite cross-validation predictions at alpha={a}")
            out[j, fo_rows] = pred.astype(np.float32)
    return out


def make_model(model_type: str, alpha: float, seed: int):
    from sklearn.linear_model import Lasso, LinearRegression, Ridge, ElasticNet
    if model_type == "ridge":
        return Ridge(alpha=alpha)
    if model_type == "lasso":
        return Lasso(alpha=alpha, max_iter=5000, random_state=seed)
    if model_type == "elasticnet":
        return ElasticNet(alpha=alpha, l1_ratio=0.5, max_iter=5000, random_state=seed)
    if model_type == "ols":
        return LinearRegression()
    raise ValueError(f"unsupported model_type {model_type!r} (allowed: ridge, lasso, elasticnet, ols)")


def run(spec: dict, public_dir: Path, plugin_dir: Path, out_dir: Path, cache_dir: Path | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    seed = int(spec.get("seed", 0))
    np.random.seed(seed)
    registry.load_plugins(plugin_dir)
    feature_cache = Path(cache_dir) / "features" if cache_dir else None
    ctx = FeatureContext.shared(public_dir, Path(cache_dir) / "shared" if cache_dir else None)
    cache_log: dict = {}
    feature_set = spec["feature_set"]
    feature_params = spec.get("feature_params", {})
    hp = spec.get("hyperparameters", {})
    model_type = spec.get("model_type", "ridge")
    alphas = [0.0] if model_type == "ols" else list(hp.get("alpha_grid", [hp.get("alpha", 1.0)]))

    train = ctx.train_perts
    evals = [p for p in ctx.perts if p not in set(train)]
    timings: dict = {}
    t0 = time.process_time()
    label_dep: dict = {}
    train_blocks = feature_blocks(ctx, feature_set, feature_params, train, timings, feature_cache, cache_log, label_dep)
    X_tr, columns = _concat(train_blocks, feature_set, len(train), ctx.n_genes)
    X_ev, _ = build_matrix(ctx, feature_set, feature_params, evals, timings, feature_cache, cache_log, label_dep)
    feat_time = time.process_time() - t0
    _, d_train = ctx.train_delta()
    y = d_train.reshape(-1)

    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    sd[sd == 0] = 1.0
    X_tr = (X_tr - mu) / sd
    X_ev = (X_ev - mu) / sd

    preds, coefs, train_time, infer_time = [], [], 0.0, 0.0
    models = []
    for a in alphas:
        model = make_model(model_type, a, seed)
        t = time.process_time()
        model.fit(X_tr, y)
        train_time += time.process_time() - t
        t = time.process_time()
        p = model.predict(X_ev).reshape(len(evals), ctx.n_genes)
        infer_time += time.process_time() - t
        if not np.all(np.isfinite(p)):
            raise ValueError(f"model produced non-finite predictions at alpha={a}")
        preds.append(p.astype(np.float32))
        coefs.append({"alpha": a, "intercept": float(model.intercept_),
                      "coef": dict(zip(columns, map(float, np.ravel(model.coef_))))})
        models.append(model)

    np.savez_compressed(out_dir / "predictions.npz", delta=np.stack(preds), perts=np.array(evals),
                        alphas=np.array(alphas, dtype=np.float64))
    cv_folds = int(hp.get("cv_folds") or 0)
    cv_groups = hp.get("cv_groups")
    cv_time = 0.0
    if cv_folds > 1:
        t = time.process_time()
        cv = cross_validate(ctx, feature_set, feature_params, model_type, alphas, seed, cv_folds,
                            int(hp.get("cv_seed") or 0), timings, feature_cache, cache_log, train_blocks, label_dep,
                            groups=cv_groups)
        np.savez_compressed(out_dir / "cv.npz", delta=cv, perts=np.array(train),
                            alphas=np.array(alphas, dtype=np.float64), folds=np.array([cv_folds]))
        cv_time = time.process_time() - t
    with open(out_dir / "models.pkl", "wb") as fh:
        pickle.dump({"models": models, "columns": columns, "x_mean": mu, "x_std": sd}, fh)
    result = {
        "status": "ok",
        "columns": columns,
        "n_train_rows": int(X_tr.shape[0]),
        "n_features": int(X_tr.shape[1]),
        "alphas": alphas,
        "coefficients": coefs,
        "feature_metadata": {n: registry.get(n).metadata() for n in feature_set},
        "timing": {
            "feature_cpu_s": feat_time, "per_feature_cpu_s": timings,
            "train_cpu_s": train_time, "inference_cpu_s": infer_time, "cv_cpu_s": cv_time,
        },
        "cv_folds": cv_folds,
        **({"cv_groups": cv_groups} if cv_folds > 1 and cv_groups else {}),
        "label_dependent_features": sorted(n for n, d in label_dep.items() if d),
        "model_size_bytes": int((out_dir / "models.pkl").stat().st_size),
        "feature_cache": {"hits": sorted(set(cache_log.get("hits", []))),
                          "misses": sorted(set(cache_log.get("misses", [])))},
    }
    (out_dir / "result.json").write_text(json.dumps(result, indent=1))
    return result


def smoke(feature: str, public_dir: Path, plugin_dir: Path, out_dir: Path, cache_dir: Path | None = None) -> dict:
    """Fast correctness test for a new feature: shape, finiteness, determinism, leakage; on a bundle with pairs of
    genes also leakage on a training pair and the same output whatever order a pair's targets are listed in."""
    out_dir.mkdir(parents=True, exist_ok=True)
    registry.load_plugins(plugin_dir)
    cls = registry.get(feature)
    meta = cls.metadata()
    shared = Path(cache_dir) / "shared" if cache_dir else None
    ctx = FeatureContext(public_dir, shared)
    evals = [p for p in ctx.perts if p not in set(ctx.train_perts)]
    perts = ctx.train_perts[:2] + evals[:2]
    # A bundle with pairs (perturbations of several genes; docs/NORMAN_PLAN.md section 4, item 10): the first training
    # pair and the first pair outside training join the alphabetical sample, so a feature that only pairs move is not
    # constant on it and pair code runs. A single-target bundle (Adamson's) is sampled and checked exactly as before.
    multi = {p for p in ctx.perts if len(set(ctx.target_genes(p))) > 1}
    pairs = [next((p for p in group if p in multi), None) for group in (ctx.train_perts, evals)]
    perts += [p for p in pairs if p is not None and p not in perts]
    t = time.process_time()
    a = np.asarray(cls().compute(ctx, perts, dict(cls.params)), dtype=np.float64)
    elapsed = time.process_time() - t
    problems = []
    if a.ndim == 2:
        a = a[:, :, None]
    if a.shape[:2] != (len(perts), ctx.n_genes):
        problems.append(f"shape {a.shape} != ({len(perts)}, {ctx.n_genes}, dim)")
    elif a.shape[2] != cls.dim:
        problems.append(f"declared dim={cls.dim} but returned {a.shape[2]} columns")
    if not np.all(np.isfinite(a)):
        problems.append("NaN/inf values")
    if not problems:
        if np.allclose(a.std(axis=(0, 1)), 0):
            problems.append("feature is constant across all rows (no information)")
        registry.reload_plugins()  # fresh module state: a memo must not hide non-determinism or leakage
        cls = registry.get(feature)
        b = np.asarray(cls().compute(FeatureContext(public_dir, shared), perts, dict(cls.params)), dtype=np.float64)
        if b.ndim == 2:
            b = b[:, :, None]
        if not np.allclose(a, b):
            problems.append("non-deterministic output")
        # Leakage: replace p0's own training label with noise; p0's features must not change. p0 is the first
        # training perturbation and then, on a bundle with pairs, the first training pair.
        for p0 in dict.fromkeys([ctx.train_perts[0]] + [p for p in pairs[:1] if p is not None]):
            leak_ctx = FeatureContext(public_dir, shared)
            rng = np.random.default_rng(0)
            leak_ctx._train_delta[leak_ctx._train_pos[p0]] = rng.normal(0, 5, size=leak_ctx.n_genes)
            registry.reload_plugins()
            cls = registry.get(feature)
            c = np.asarray(cls().compute(leak_ctx, [p0], dict(cls.params)), dtype=np.float64)
            if c.ndim == 2:
                c = c[:, :, None]
            i = perts.index(p0)
            if not np.allclose(a[i:i + 1], c):
                problems.append(f"label leakage: features for training perturbation {p0} depend on its own label "
                                "(use ctx.train_delta(exclude=p))")
                break
        if multi & set(perts):
            # A pair's targets are an unordered set: the output must not change when the sampled perturbations and
            # every other one of the rest list their targets in reverse order (in target_genes, target_indices and
            # the targets knowledge file alike), which moves a feature that reads only the first target and one that
            # pairs two perturbations' targets by position (A with C, B with D) alike.
            flip = set(perts) | set(ctx.perts[::2])
            swap_ctx = FeatureContext(public_dir, shared)
            swap_ctx._targets = {p: list(reversed(v)) if p in flip else list(v) for p, v in swap_ctx._targets.items()}
            read = swap_ctx.knowledge
            swap_ctx.knowledge = lambda name: ({p: list(v) for p, v in swap_ctx._targets.items()}
                                               if name == "targets" else read(name))
            registry.reload_plugins()
            cls = registry.get(feature)
            s = np.asarray(cls().compute(swap_ctx, perts, dict(cls.params)), dtype=np.float64)
            if s.ndim == 2:
                s = s[:, :, None]
            if s.shape != a.shape or not np.allclose(a, s):
                problems.append("output depends on the order of a pair's target genes: a perturbation's targets are "
                                "an unordered set (use every target, never only the first, and never match two "
                                "perturbations' targets by position)")
    est_full = elapsed / len(perts) * len(ctx.perts) * (1 if not problems else 0)
    result = {"status": "ok" if not problems else "failed", "problems": problems, "metadata": meta,
              "smoke_cpu_s": elapsed, "estimated_full_cpu_s": est_full}
    (out_dir / "smoke.json").write_text(json.dumps(result, indent=1))
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run", "smoke"])
    ap.add_argument("--spec")
    ap.add_argument("--feature")
    ap.add_argument("--public", required=True)
    ap.add_argument("--plugins", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", help="run-level cache for computed features and shared matrices")
    args = ap.parse_args(argv)
    out = Path(args.out)
    try:
        if args.mode == "run":
            run(json.loads(Path(args.spec).read_text()), Path(args.public), Path(args.plugins), out,
                Path(args.cache) if args.cache else None)
        else:
            r = smoke(args.feature, Path(args.public), Path(args.plugins), out,
                      Path(args.cache) if args.cache else None)
            return 0 if r["status"] == "ok" else 3
        return 0
    except Exception as exc:  # report, never hang
        out.mkdir(parents=True, exist_ok=True)
        (out / "error.json").write_text(json.dumps({
            "error_type": type(exc).__name__, "error": str(exc)[:2000],
            "traceback": traceback.format_exc()[-4000:]}))
        print(traceback.format_exc(), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
