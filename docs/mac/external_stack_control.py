"""Control for tools/external_loo.py: how much of external_stack's gain is the stacking, not the external screen?

Same leave-one-out, same columns, same code (imported from tools/external_loo.py); only the set of columns given
to the stack changes, and the alpha grid is widened because the tool's grid ended at the value chosen in every fold.
Training perturbations and public knowledge only; no private file, no oracle.

    .venv/bin/python ../genemila_scale_logs/external_stack_control.py        (from the lab checkout)
"""
import json, sys
from pathlib import Path
import numpy as np
REPO = Path.home() / "Documents/Mila/Gene-Mila/gene-mila"
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "tools"))
import external_loo as el  # noqa: E402

bundle = el.load_bundle(REPO / "data/adamson_cf")
ext = el.load_external(REPO / "data/adamson_cf", "replogle2022_k562", bundle["genes"])
perts, D = bundle["perts"], bundle["deltas"]; n, G = D.shape
sets_of = {}
for name, members in bundle["gene_sets"].items():
    for g in members: sets_of.setdefault(g, set()).add(name)
memb = [set().union(*(sets_of.get(t, set()) for t in bundle["targets"][p])) for p in perts]
E = np.full((n, G), np.nan); has = np.zeros(n, dtype=bool)
for i, p in enumerate(perts):
    for t in bundle["targets"][p]:
        if t in ext["rows"]: E[i], has[i] = ext["rows"][t], True; break
S = {"deltas": D, "jaccard": el._jaccard(memb), "ext_corr": el._pairwise_corr(E, has), "ext": E, "has_ext": has}
NAMES = el.STACK_COLUMNS
SUBSETS = {"stack: mean + geneset (no external)": [0, 1], "stack: + external_direct": [0, 1, 2],
           "stack: + external_knn": [0, 1, 3], "stack: all four (the tool's external_stack)": [0, 1, 2, 3]}
GRIDS = {"tool grid": el.ALPHA_GRID, "wide grid": (0.1, 1.0, 10.0, 100.0, 1000.0, 1e4, 1e5, 1e6)}
scores = {f"{s} | {g}": [] for s in SUBSETS for g in GRIDS}
alphas = {k: [] for k in scores}
base = {"mean_response": [], "geneset_knn": []}
for i in range(n):
    avail = np.ones(n, dtype=bool); avail[i] = False
    cols, _ = el._features(i, avail, S, 5)
    tc, ty = [], []
    for q in np.flatnonzero(avail):
        ia = avail.copy(); ia[q] = False
        tc.append(el._features(int(q), ia, S, 5)[0]); ty.append(D[q])
    base["mean_response"].append(float(el.pearson_delta(cols[0], D[i]))); base["geneset_knn"].append(float(el.pearson_delta(cols[1], D[i])))
    for s, idx in SUBSETS.items():
        for g, grid in GRIDS.items():
            pred, a, _ = el._stack([c[idx] for c in tc], ty, cols[idx], grid)
            scores[f"{s} | {g}"].append(float(el.pearson_delta(pred, D[i]))); alphas[f"{s} | {g}"].append(a)
ref = np.array(scores["stack: mean + geneset (no external)" + " | wide grid"])
out = {"n": n, "with_external_row": int(has.sum()), "baselines": {k: float(np.mean(v)) for k, v in base.items()}, "stacks": {}}
print(f"mean_response {np.mean(base['mean_response']):.4f}  geneset_knn {np.mean(base['geneset_knn']):.4f}")
for k, v in scores.items():
    v = np.array(v); grid = k.split(" | ")[1]
    r = np.array(scores["stack: mean + geneset (no external) | " + grid]); d = v - r
    out["stacks"][k] = {"mean": float(v.mean()), "gain_vs_no_external_stack_same_grid": float(d.mean()),
                        "se": float(d.std(ddof=1) / np.sqrt(n)), "wins": int((d > 0).sum()),
                        "alphas": {str(a): alphas[k].count(a) for a in sorted(set(alphas[k]))}, "per_pert": v.tolist()}
    print(f"{k:62s} {v.mean():.4f}  vs no-external stack {d.mean():+.4f} ± {d.std(ddof=1)/np.sqrt(n):.4f}  wins {int((d>0).sum())}/{n}  alphas {out['stacks'][k]['alphas']}")
out["perts"] = perts
Path(__file__).with_name("external_stack_control.json").write_text(json.dumps(out, indent=1))
