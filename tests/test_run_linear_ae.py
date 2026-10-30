"""tools/baselines_dl/run_linear_ae.py: the Ahlmann-Eltze linear baseline on synthetic matrices."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "baselines_dl"))

import run_linear_ae  # noqa: E402


def _screen(n_genes=60, n_perts=30, k=3, seed=0):
    """Responses that follow the model exactly: Y = b + G W G[target]^T, with targets among the genes."""
    rng = np.random.default_rng(seed)
    genes = [f"g{i}" for i in range(n_genes)]
    G = np.linalg.qr(rng.normal(size=(n_genes, k)))[0]
    W = rng.normal(size=(k, k))
    b = rng.normal(size=n_genes)
    keys = genes[:n_perts]
    Y = np.stack([b + G @ W @ G[i] for i in range(n_perts)])
    return genes, keys, Y


def test_recovers_an_exactly_linear_screen():
    genes, keys, Y = _screen()
    train, held = keys[:24], keys[24:]
    pred, info = run_linear_ae.fit_predict(Y[:24], train, genes, held, k=3, lam=1e-8)
    assert info["heldout_fallback"] == [] and info["train_used"] == 24
    for i, p in enumerate(held):
        assert np.corrcoef(pred[i] - Y[:24].mean(0), Y[24 + i] - Y[:24].mean(0))[0, 1] > 0.99


def test_targets_outside_the_genes_fall_back_to_the_mean():
    genes, keys, Y = _screen()
    train = keys[:20] + ["NOTAGENE"]
    Ytr = np.vstack([Y[:20], Y[20]])
    pred, info = run_linear_ae.fit_predict(Ytr, train, genes, ["g25", "MISSING", "g26+g27"])
    assert info["train_without_embedding"] == ["NOTAGENE"]
    assert info["heldout_fallback"] == ["MISSING"]
    assert np.allclose(pred[1], Ytr.mean(0))
    assert pred.shape == (3, len(genes)) and np.all(np.isfinite(pred))
