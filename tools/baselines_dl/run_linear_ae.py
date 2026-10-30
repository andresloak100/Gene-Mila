#!/usr/bin/env python3
"""The simple linear baseline of Ahlmann-Eltze, Huber and Anders (2025, Nature Methods), on this lab's split.

That paper showed that no deep model it tested beat this baseline at predicting unseen perturbations, so it is the
field's common reference point. It reads only the export of tools/cellforge_bridge.py (control and training cells,
the bundle's genes and normalisation, the held-out list), like run_gears.py, and writes predictions.npz (`perts`,
`means`, `genes`) for tools/cellforge_bridge.py `score`. No LLM, no paid call, CPU, seconds.

The model, as in the paper: Y (genes x training perturbations, mean expression per perturbation) is fitted as
Y = b + G W P^T, where b is each gene's mean over the training perturbations, G (genes x K) holds the top K principal
components of the centred Y, P holds the rows of G for each perturbation's target genes (summed for a pair), and W is
the ridge solution W = (G^T G + lam I)^-1 G^T (Y - b) P (P^T P + lam I)^-1. An unseen perturbation p is predicted as
b + G W P_p. Defaults K = 10, lam = 0.1 (the paper's). A perturbation whose target gene is not among the export's
genes has no embedding: a training one is left out of the fit, a held-out one gets b, and the receipt lists both.

    python tools/baselines_dl/run_linear_ae.py --export ~/cellforge_adamson_export --out ~/linear_ae_adamson
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fit_predict(train_means: np.ndarray, train_keys: list[str], genes: list[str], heldout: list[str],
                k: int = 10, lam: float = 0.1) -> tuple[np.ndarray, dict]:
    """train_means: training perturbations x genes. Returns held-out x genes predictions and what was left out."""
    col = {g: i for i, g in enumerate(genes)}
    Y = np.asarray(train_means, dtype=np.float64).T  # genes x perts
    b = Y.mean(1, keepdims=True)
    Yc = Y - b
    k = min(k, min(Yc.shape))
    G = np.linalg.svd(Yc, full_matrices=False)[0][:, :k]  # gene embedding

    def embed(key: str) -> np.ndarray | None:
        targets = key.split("+")
        if not all(t in col for t in targets):
            return None
        return G[[col[t] for t in targets]].sum(0)

    fit = [(i, e) for i, key in enumerate(train_keys) if (e := embed(key)) is not None]
    dropped = [train_keys[i] for i in range(len(train_keys)) if i not in {j for j, _ in fit}]
    preds, fallback = [], []
    if fit:
        P = np.stack([e for _, e in fit])  # perts x k
        Yf = Yc[:, [i for i, _ in fit]]
        W = np.linalg.solve(G.T @ G + lam * np.eye(k), G.T @ Yf @ P) @ np.linalg.inv(P.T @ P + lam * np.eye(k))
    for key in heldout:
        e = embed(key) if fit else None
        if e is None:
            preds.append(b[:, 0])
            fallback.append(key)
        else:
            preds.append(b[:, 0] + G @ W @ e)
    return np.stack(preds), {"train_used": len(fit), "train_without_embedding": dropped, "heldout_fallback": fallback,
                             "k": k, "lam": lam}


def run(export: Path, out: Path, k: int, lam: float) -> dict:
    import anndata as ad
    import scipy.sparse as sp

    export, out = Path(export), Path(out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    a = ad.read_h5ad(export / "cellforge_input.h5ad")
    heldout = json.loads((export / "heldout_perturbations.json").read_text())
    genes = a.var_names.astype(str).tolist()
    keys = a.obs["perturbation"].astype(str).to_numpy()
    X = a.X.toarray() if sp.issparse(a.X) else np.asarray(a.X)
    train_keys = sorted(set(keys) - {"control"})
    train_means = np.stack([X[keys == p].mean(0) for p in train_keys])
    means, info = fit_predict(train_means, train_keys, genes, heldout, k, lam)
    np.savez(out / "predictions.npz", perts=np.array(heldout), means=means, genes=np.array(genes))
    receipt = {"model": "linear baseline (Ahlmann-Eltze, Huber and Anders 2025)", **info,
               "train_perturbations": len(train_keys), "heldout": len(heldout),
               "export_input_sha256": _sha(export / "cellforge_input.h5ad"),
               "predictions_sha256": _sha(out / "predictions.npz"), "seconds": round(time.time() - t0, 1),
               "machine": platform.platform()}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=1))
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--export", required=True, help="folder written by cellforge_bridge.py export")
    ap.add_argument("--out", required=True, help="new folder for predictions.npz and receipt.json")
    ap.add_argument("--k", type=int, default=10, help="principal components in the gene embedding")
    ap.add_argument("--lam", type=float, default=0.1, help="ridge penalty")
    a = ap.parse_args(argv)
    print(json.dumps(run(Path(a.export), Path(a.out), a.k, a.lam), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
