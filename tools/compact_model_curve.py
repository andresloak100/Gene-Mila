# Written and run on the Mac on 2026-10-11 (original md5 dbb27bd37fbb3c06dc2038d82048ac85, 7,081 bytes, run from
# genemila_scale_logs at lab commit 1c434bd); moved into tools/ with the repository root taken from this file's
# location and the output directory as an optional second argument. Output committed byte for byte as
# docs/results/compact_model_curve_newcode_opus_w4_r0.json; reading in docs/results/compact_model_curve.md.
"""How few features does the model need? Free, offline, TRAINING perturbations only.

Takes the feature pool of a finished run (the 12 features of its best model, every other feature that
improved on its parent, and the three built-in ones) and, with the lab's own 5 folds over the 50 training
perturbations (each fold recomputes label-dependent features without the fold, as the lab does):
  1. correlation between the feature columns (redundancy);
  2. forward selection: starting from nothing, add the feature that raises out-of-fold pearson_delta most;
  3. Lasso path on the full pool: which columns survive as the penalty grows.
Never opens data/*/private, splits.json, or the oracle.

    .venv/bin/python ../genemila_scale_logs/compact_model_curve.py runs/newcode_opus_w4_r0
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]  # the repository root (the original hard-coded the Mac's checkout)
sys.path.insert(0, str(REPO))
from genemila.features import registry  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.pipeline import cv_fold_targets, cv_folds_of, feature_blocks  # noqa: E402

run = Path(sys.argv[1]).resolve()
import sqlite3  # noqa: E402
db = sqlite3.connect(f"file:{run / 'lab.db'}?mode=ro", uri=True)
best = db.execute("select feature_set_json from experiments where status='completed' and kind not in ('baseline','ensemble') "
                  "and primary_score is not null order by primary_score desc limit 1").fetchone()[0]
pool = list(json.loads(best))
for (f,) in db.execute("select new_feature from experiments where kind='new_feature' and status='completed' "
                       "and delta_from_parent > 0.0005 order by delta_from_parent desc"):
    if f not in pool: pool.append(f)
for f in ("control_mean", "mean_response", "is_target"):
    if f not in pool: pool.append(f)

registry.load_plugins(run / "feature_store")
cache = Path("/tmp") / "does-not-exist"  # no disk cache: nothing is written anywhere
ctx = FeatureContext(run / "public_data")
train = ctx.train_perts
G = ctx.n_genes
pos = {p: i for i, p in enumerate(train)}
_, D = ctx.train_delta()                       # (n_train, G)


def pear_rows(P, Y):
    P = P - P.mean(1, keepdims=True); Y = Y - Y.mean(1, keepdims=True)
    return (P * Y).sum(1) / np.sqrt((P * P).sum(1) * (Y * Y).sum(1) + 1e-30)


# ---- per fold: standardised training matrix, fold matrix, Gram matrices
folds = []
cols = None
# the run's fold grouping, as the lab recorded it in its experiments' hyperparameters (absent, as for every bundle
# without pairs or a gene split: random folds over names); a fold's view hides its hidden set, predicts the fold
groups = next((json.loads(h).get("cv_groups") for (h,) in db.execute(
    "select hyperparameters_json from experiments where hyperparameters_json like '%cv_groups%' limit 1")), None)
for fold, hide in cv_folds_of(train, 5, 0, cv_fold_targets(ctx, groups)):
    registry.reload_plugins()
    view = ctx.without_train(hide)
    both = view.train_perts + fold
    blocks = feature_blocks(view, pool, {}, both, {}, None, {})
    n_tr = len(view.train_perts)
    names, Xs = [], []
    for f in pool:
        b = np.asarray(blocks[f], dtype=np.float64)
        b = b.reshape(len(both), G, -1)
        for j in range(b.shape[2]):
            names.append(f if b.shape[2] == 1 else f"{f}[{j}]"); Xs.append(b[:, :, j])
    X = np.stack(Xs, axis=2)                    # (perts, G, C)
    Xtr = X[:n_tr].reshape(-1, X.shape[2]); Xfo = X[n_tr:].reshape(-1, X.shape[2])
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1.0
    Xtr = (Xtr - mu) / sd; Xfo = (Xfo - mu) / sd
    _, dtr = view.train_delta()
    y = dtr.reshape(-1); ym = y.mean()
    folds.append({"XtX": Xtr.T @ Xtr, "Xty": Xtr.T @ (y - ym), "ym": ym, "Xfo": Xfo, "Xtr": Xtr, "y": y,
                  "fo_rows": [pos[p] for p in fold], "n_fo": len(fold)})
    cols = names
C = len(cols)
feat_of = [c.split("[")[0] for c in cols]
print(f"pool: {len(pool)} features, {C} columns; {len(train)} training perturbations, 5 folds", flush=True)

ALPHAS = [1.0, 30.0, 300.0, 3000.0, 30000.0]


def cv_score(col_idx):
    """Best out-of-fold pearson_delta over the alpha grid for a column subset (ridge, intercept, as the lab fits)."""
    best = (-9, None)
    idx = np.array(col_idx)
    for a in ALPHAS:
        P = np.zeros_like(D)
        for fd in folds:
            A = fd["XtX"][np.ix_(idx, idx)] + a * np.eye(len(idx))
            w = np.linalg.solve(A, fd["Xty"][idx])
            P[fd["fo_rows"]] = (fd["Xfo"][:, idx] @ w + fd["ym"]).reshape(fd["n_fo"], G)
        s = float(pear_rows(P, D).mean())
        if s > best[0]: best = (s, a)
    return best


# ---- 1. redundancy between columns (pooled over the first fold's training rows)
R = np.corrcoef(folds[0]["Xtr"].T)
pairs = sorted(((abs(R[i, j]), cols[i], cols[j]) for i in range(C) for j in range(i + 1, C)), reverse=True)
rank = int(np.linalg.matrix_rank(folds[0]["Xtr"], tol=1e-6 * np.sqrt(folds[0]["Xtr"].shape[0])))

# ---- 2. forward selection by feature (a feature brings all its columns)
features = list(dict.fromkeys(feat_of))
chosen, curve = [], []
while len(chosen) < len(features):
    cand = []
    for f in features:
        if f in chosen: continue
        idx = [i for i, g in enumerate(feat_of) if g in chosen or g == f]
        s, a = cv_score(idx)
        cand.append((s, a, f))
    s, a, f = max(cand)
    chosen.append(f)
    ncols = sum(1 for g in feat_of if g in chosen)
    curve.append({"n_features": len(chosen), "n_columns": ncols, "added": f, "cv_pearson_delta": s, "alpha": a})
    print(f"{len(chosen):2d} features / {ncols:2d} columns  +{f:45s} CV {s:.4f} (alpha {a:g})", flush=True)

best_set = json.loads(best)
full_best = cv_score([i for i, g in enumerate(feat_of) if g in best_set])
single = sorted(((cv_score([i for i, g in enumerate(feat_of) if g == f])[0], f) for f in features), reverse=True)

# ---- 3. Lasso path on the whole pool (fitted on all training rows of fold 0's view; which columns survive)
from sklearn.linear_model import Lasso  # noqa: E402
fd = folds[0]
lasso = []
for lam in (0.0001, 0.0003, 0.001, 0.003, 0.01):
    m = Lasso(alpha=lam, max_iter=20000).fit(fd["Xtr"], fd["y"])
    keep = [cols[i] for i in np.flatnonzero(np.abs(m.coef_) > 1e-12)]
    lasso.append({"lambda": lam, "n_columns_kept": len(keep), "kept": keep})

out = {"run": run.name, "pool_features": pool, "columns": cols, "matrix_rank": rank,
       "most_correlated_column_pairs": [{"abs_r": round(r, 4), "a": a, "b": b} for r, a, b in pairs[:15]],
       "n_pairs_abs_r_over_0.9": sum(1 for r, _, _ in pairs if r > 0.9),
       "n_pairs_abs_r_over_0.7": sum(1 for r, _, _ in pairs if r > 0.7),
       "single_feature_cv": [{"feature": f, "cv_pearson_delta": s} for s, f in single],
       "forward_selection": curve,
       "run_best_model": {"features": best_set, "n_features": len(best_set), "cv_pearson_delta": full_best[0], "alpha": full_best[1]},
       "lasso_path": lasso}
dst = (Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()) / f"compact_model_curve_{run.name}.json"
dst.write_text(json.dumps(out, indent=1))
print(json.dumps({k: out[k] for k in ("matrix_rank", "n_pairs_abs_r_over_0.9", "n_pairs_abs_r_over_0.7", "run_best_model")}, indent=1))
print("most correlated pairs:"); [print(f"  {r:.3f}  {a}  ~  {b}") for r, a, b in pairs[:10]]
print("single features:"); [print(f"  {s:.4f}  {f}") for s, f in single]
print("lasso:"); [print(f"  lambda {l['lambda']:g}: {l['n_columns_kept']} columns kept") for l in lasso]
print("written", dst)
