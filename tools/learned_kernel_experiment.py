"""Free offline experiment on TRAINING perturbations only (public bundle; no private files).

Question: the transfer family is capped at about 0.73 with oracle weights and the lab's models sit
at about 0.60. Can a similarity between targets that is LEARNED from the training responses close
part of that gap, compared with the fixed similarities the agents' kNN features use?

Protocol: leave-one-perturbation-out over the 50 training perturbations. For the held-out p,
everything (pair model, hyper-parameters) is fitted on the other 49 only.
"""
# Provenance: written and run on the Mac (lab checkout 047595d, 2026-10-11) as genemila_scale_logs/learned_kernel_experiment.py;
# original md5 c20de8c55886dd6aae045c385c036d0c. Moved into tools/ with the repository root as an argument instead of a hard-coded path;
# nothing else changed. Its results are committed as docs/results/learned_kernel_experiment.json (to follow).

import json
from pathlib import Path

import numpy as np

import argparse

_ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]),
                 help="lab checkout holding data/adamson_cf (default: this repository)")
_ap.add_argument("--out", default=None, help="JSON results (default: next to this script)")
_args = _ap.parse_args()
REPO = Path(_args.repo).expanduser()
B = REPO / "data/adamson_cf"
pub = np.load(B / "public.npz", allow_pickle=False)
genes = [str(g) for g in pub["genes"]]; gi = {g: i for i, g in enumerate(genes)}
train = [str(p) for p in pub["train_perts"]]
C = pub["control_cells"].astype(np.float64)
ctrl_mean = C.mean(axis=0)
T = pub["train_means"].astype(np.float64) - ctrl_mean
n, G = T.shape
tg = json.load(open(B / "knowledge/targets.json"))
target = [tg[p][0] for p in train]


def pear(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


# ---------- fixed similarities between targets (all from public knowledge and control cells)
gs = json.load(open(B / "knowledge/gene_sets.json"))
memb = {t: set() for t in target}
size = {}
for s, gl in gs.items():
    size[s] = len(gl)
    for g in gl:
        if g in memb: memb[g].add(s)
idf = {s: 1.0 / np.log(2 + size[s]) for s in gs}


def gs_sim(a, b):
    A, Bm = memb[a], memb[b]
    if not A or not Bm: return 0.0
    num = sum(idf[s] ** 2 for s in A & Bm)
    den = np.sqrt(sum(idf[s] ** 2 for s in A) * sum(idf[s] ** 2 for s in Bm))
    return num / den


ppi = json.load(open(B / "knowledge/ppi_network.json"))
nb = {}
for a, b, w in ppi:
    nb.setdefault(a, {})[b] = w; nb.setdefault(b, {})[a] = w


def ppi_sim(a, b):
    A, Bn = set(nb.get(a, {})), set(nb.get(b, {}))
    direct = nb.get(a, {}).get(b, 0.0)
    jac = len(A & Bn) / len(A | Bn) if (A | Bn) else 0.0
    return direct, jac


Cz = (C - C.mean(0)) / (C.std(0) + 1e-9)
tidx = [gi[t] for t in target]
coexp = (Cz[:, tidx].T @ Cz) / C.shape[0]            # targets x genes: coexpression profile of each target
coexp_tt = coexp[:, tidx]                             # direct coexpression between targets
prof = np.corrcoef(coexp)                             # similarity of coexpression profiles
lvl = ctrl_mean[tidx]


def stem(s):
    i = len(s)
    while i > 0 and (s[i - 1].isdigit()): i -= 1
    return s[:max(i, 3)]


F_NAMES = ["gene_set", "ppi_direct", "ppi_shared_nb", "coexpr_direct", "coexpr_profile", "same_family", "level_close", "bias"]
F = np.zeros((n, n, len(F_NAMES)))
for i in range(n):
    for j in range(n):
        d, jac = ppi_sim(target[i], target[j])
        F[i, j] = [gs_sim(target[i], target[j]), d, jac, coexp_tt[i, j], prof[i, j],
                   float(stem(target[i]) == stem(target[j]) or target[i][:3] == target[j][:3]),
                   -abs(lvl[i] - lvl[j]), 1.0]


F = np.nan_to_num(F)


def transfer(i, others, w, shrink):
    """Prediction for perturbation i from the others: mean + shrink * weighted deviation."""
    m = T[others].mean(axis=0)
    w = np.maximum(w, 0)
    if w.sum() <= 0: return m
    w = w / w.sum()
    return m + shrink * (w @ (T[others] - m))


def knn_weights(sim, k, beta):
    w = np.zeros_like(sim)
    top = np.argsort(-sim)[:k]
    s = sim[top] - sim[top].max()
    w[top] = np.exp(beta * s)
    return w


def fit_pair_model(idx, lam):
    """Ridge from pair features to response correlation, on pairs inside idx only."""
    Tm = T[idx] - T[idx].mean(axis=0)
    R = np.corrcoef(Tm)
    X, y = [], []
    for a in range(len(idx)):
        for b in range(len(idx)):
            if a != b:
                X.append(F[idx[a], idx[b]]); y.append(R[a, b])
    X = np.array(X); y = np.array(y)
    mu, sd = X[:, :-1].mean(0), X[:, :-1].std(0) + 1e-9
    Xs = np.c_[(X[:, :-1] - mu) / sd, np.ones(len(X))]
    P = np.eye(Xs.shape[1]) * lam; P[-1, -1] = 0
    beta = np.linalg.solve(Xs.T @ Xs + P, Xs.T @ y)
    return beta, mu, sd


def pair_predict(model, i, others):
    beta, mu, sd = model
    X = F[i, others]
    return np.c_[(X[:, :-1] - mu) / sd, np.ones(len(others))] @ beta


GRID = [(k, b, s) for k in (3, 5, 10, 49) for b in (5.0, 15.0, 40.0) for s in (0.6, 0.8, 1.0)]
all_idx = np.arange(n)
res = {name: [] for name in ["loo_mean", "gene_set_knn", "coexpr_profile_knn", "learned_kernel"]}
coefs = []
chosen = []
for i in range(n):
    others = np.delete(all_idx, i)
    y = T[i]
    res["loo_mean"].append(pear(T[others].mean(axis=0), y))
    # fixed-similarity baselines, hyper-parameters chosen by inner leave-one-out on the others
    for name, col in (("gene_set_knn", 0), ("coexpr_profile_knn", 4)):
        best, bg = -9, None
        for (k, b, s) in GRID:
            sc = []
            for jj, j in enumerate(others):
                oo = np.delete(others, jj)
                sc.append(pear(transfer(j, oo, knn_weights(F[j, oo, col], k, b), s), T[j]))
            if np.mean(sc) > best: best, bg = np.mean(sc), (k, b, s)
        k, b, s = bg
        res[name].append(pear(transfer(i, others, knn_weights(F[i, others, col], k, b), s), y))
    # learned kernel: pair model and hyper-parameters fitted on the others only
    best, bg = -9, None
    inner_models = {}
    for lam in (1.0, 30.0):
        preds = {}
        for jj, j in enumerate(others):
            oo = np.delete(others, jj)
            preds[j] = (oo, pair_predict(fit_pair_model(oo, lam), j, oo))
        for (k, b, s) in GRID:
            sc = [pear(transfer(j, oo, knn_weights(sim, k, b), s), T[j]) for j, (oo, sim) in preds.items()]
            if np.mean(sc) > best: best, bg = np.mean(sc), (lam, k, b, s)
    lam, k, b, s = bg
    model = fit_pair_model(others, lam)
    coefs.append(model[0]); chosen.append(bg)
    res["learned_kernel"].append(pear(transfer(i, others, knn_weights(pair_predict(model, i, others), k, b), s), y))
    print(f"{train[i]:10s} mean {res['loo_mean'][-1]:.3f} gs {res['gene_set_knn'][-1]:.3f} "
          f"coexp {res['coexpr_profile_knn'][-1]:.3f} learned {res['learned_kernel'][-1]:.3f} {bg}", flush=True)

out = {k: float(np.mean(v)) for k, v in res.items()}
out["learned_minus_gene_set_per_pert_mean"] = float(np.mean(np.array(res["learned_kernel"]) - np.array(res["gene_set_knn"])))
out["learned_better_than_gene_set_in"] = int(np.sum(np.array(res["learned_kernel"]) > np.array(res["gene_set_knn"])))
out["pair_model_mean_coefficients"] = dict(zip(F_NAMES, np.mean(coefs, axis=0).round(4).tolist()))
print(json.dumps(out, indent=1))
Path(_args.out or Path(__file__).with_name("learned_kernel_experiment.json")).write_text(json.dumps({"summary": out, "per_pert": {k: v for k, v in res.items()}, "train": train}, indent=1))
