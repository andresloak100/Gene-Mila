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
import json
import pickle
import sys
import time
import traceback
from pathlib import Path

import numpy as np

from .features import registry
from .features.api import FeatureContext


def build_matrix(ctx: FeatureContext, feature_set: list[str], feature_params: dict, perts: list[str],
                 timings: dict) -> tuple[np.ndarray, list[str]]:
    blocks, columns = [], []
    for name in feature_set:
        cls = registry.get(name)
        params = {**cls.params, **feature_params.get(name, {})}
        t0 = time.process_time()
        arr = np.asarray(cls().compute(ctx, perts, params), dtype=np.float64)
        timings[name] = timings.get(name, 0.0) + time.process_time() - t0
        if arr.ndim == 2:
            arr = arr[:, :, None]
        if arr.shape[:2] != (len(perts), ctx.n_genes):
            raise ValueError(f"feature {name} returned shape {arr.shape}, expected ({len(perts)}, {ctx.n_genes}, dim)")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"feature {name} produced NaN/inf values")
        blocks.append(arr)
        columns += [name] if arr.shape[2] == 1 else [f"{name}[{j}]" for j in range(arr.shape[2])]
    X = np.concatenate(blocks, axis=2)
    return X.reshape(len(perts) * ctx.n_genes, X.shape[2]), columns


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


def run(spec: dict, public_dir: Path, plugin_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    seed = int(spec.get("seed", 0))
    np.random.seed(seed)
    registry.load_plugins(plugin_dir)
    ctx = FeatureContext(public_dir)
    feature_set = spec["feature_set"]
    feature_params = spec.get("feature_params", {})
    hp = spec.get("hyperparameters", {})
    model_type = spec.get("model_type", "ridge")
    alphas = [0.0] if model_type == "ols" else list(hp.get("alpha_grid", [hp.get("alpha", 1.0)]))

    train = ctx.train_perts
    evals = [p for p in ctx.perts if p not in set(train)]
    timings: dict = {}
    t0 = time.process_time()
    X_tr, columns = build_matrix(ctx, feature_set, feature_params, train, timings)
    X_ev, _ = build_matrix(ctx, feature_set, feature_params, evals, timings)
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
            "train_cpu_s": train_time, "inference_cpu_s": infer_time,
        },
        "model_size_bytes": int((out_dir / "models.pkl").stat().st_size),
    }
    (out_dir / "result.json").write_text(json.dumps(result, indent=1))
    return result


def smoke(feature: str, public_dir: Path, plugin_dir: Path, out_dir: Path) -> dict:
    """Fast correctness test for a new feature: shape, finiteness, determinism, leakage."""
    out_dir.mkdir(parents=True, exist_ok=True)
    registry.load_plugins(plugin_dir)
    cls = registry.get(feature)
    meta = cls.metadata()
    ctx = FeatureContext(public_dir)
    evals = [p for p in ctx.perts if p not in set(ctx.train_perts)]
    perts = ctx.train_perts[:2] + evals[:2]
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
        b = np.asarray(cls().compute(FeatureContext(public_dir), perts, dict(cls.params)), dtype=np.float64)
        if b.ndim == 2:
            b = b[:, :, None]
        if not np.allclose(a, b):
            problems.append("non-deterministic output")
        # Leakage: replace p0's own training label with noise; p0's features must not change.
        p0 = ctx.train_perts[0]
        leak_ctx = FeatureContext(public_dir)
        rng = np.random.default_rng(0)
        leak_ctx._train_delta[leak_ctx._train_pos[p0]] = rng.normal(0, 5, size=leak_ctx.n_genes)
        c = np.asarray(cls().compute(leak_ctx, [p0], dict(cls.params)), dtype=np.float64)
        if c.ndim == 2:
            c = c[:, :, None]
        if not np.allclose(a[:1], c):
            problems.append(f"label leakage: features for training perturbation {p0} depend on its own label "
                            "(use ctx.train_delta(exclude=p))")
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
    args = ap.parse_args(argv)
    out = Path(args.out)
    try:
        if args.mode == "run":
            run(json.loads(Path(args.spec).read_text()), Path(args.public), Path(args.plugins), out)
        else:
            r = smoke(args.feature, Path(args.public), Path(args.plugins), out)
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
