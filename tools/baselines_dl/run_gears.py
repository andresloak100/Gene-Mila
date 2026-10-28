#!/usr/bin/env python3
"""GEARS (Roohani et al. 2023, Nature Biotechnology) as a non-agentic deep-learning baseline on this lab's split
(docs/PLAN_DL_BASELINES.md). It reads only the export of tools/cellforge_bridge.py (control and training cells,
the bundle's genes and normalisation, the held-out list), trains GEARS on the training perturbations, and writes
predictions.npz (`perts`, `means`, `genes`) for every held-out perturbation, which tools/cellforge_bridge.py `score`
scores once through the oracle. No LLM, no paid call.

GEARS predicts a perturbation only when every target gene is in its Gene Ontology perturbation graph. A held-out
perturbation outside the graph gets the fallback prediction control mean plus the mean training change (the lab's
built-in mean_response), and the receipt lists each one, so the score says how much of it is GEARS.

    python tools/baselines_dl/run_gears.py --export ~/cellforge_adamson_export --work ~/gears_work --seed 0 \
        --out ~/gears_adamson_s0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import platform
import time
from pathlib import Path

import numpy as np


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _MaskCSR(X):
    """X as a CSR matrix that also accepts a pandas boolean mask as its row index."""
    import scipy.sparse as sp

    class MaskCSR(sp.csr_matrix):
        def __getitem__(self, key):
            if hasattr(key, "to_numpy"):
                key = key.to_numpy()
            return super().__getitem__(key)
    return MaskCSR(X)


def condition(key: str) -> str:
    """The lab's perturbation key (genes sorted, joined with '+') as GEARS's condition: 'A+ctrl' or 'A+B'."""
    if key == "control":
        return "ctrl"
    genes = key.split("+")
    return genes[0] + "+ctrl" if len(genes) == 1 else "+".join(genes)


def run(export: Path, work: Path, out: Path, seed: int, epochs: int, device: str, val_frac: float,
        hidden: int, batch: int) -> dict:
    import anndata as ad
    import scipy.sparse as sp
    import torch
    from gears import GEARS, PertData

    export, work, out = Path(export), Path(work), Path(out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    np.random.seed(seed)
    torch.manual_seed(seed)
    t0 = time.time()

    if hasattr(ad, "settings") and hasattr(ad.settings, "allow_write_nullable_strings"):
        ad.settings.allow_write_nullable_strings = True  # GEARS re-writes the AnnData; recent anndata asks first
    a = ad.read_h5ad(export / "cellforge_input.h5ad")
    heldout = json.loads((export / "heldout_perturbations.json").read_text())
    genes = a.var_names.astype(str).tolist()
    keys = a.obs["perturbation"].astype(str).to_numpy()
    a.obs["condition"] = [condition(k) for k in keys]
    a.obs["cell_type"] = "K562"
    a.var["gene_name"] = genes
    a.X = sp.csr_matrix(a.X, dtype=np.float32)  # GEARS 0.1.2 expects a sparse X (it calls .toarray())

    pd_ = PertData(str(work / "gears_data"))
    name = f"gm_{seed}"
    if (work / "gears_data" / name).exists():  # GEARS would reuse a stale processed copy of another export
        raise SystemExit(f"{work / 'gears_data' / name} exists; use a fresh --work folder per run")
    pd_.new_data_process(dataset_name=name, adata=a)
    graph = set(pd_.pert_names)
    train_conds = sorted(c for c in set(a.obs["condition"]) if c != "ctrl"
                         and all(g in graph for g in c.split("+") if g != "ctrl"))
    rng = np.random.default_rng(seed)
    order = list(rng.permutation(train_conds))
    n_val = max(1, int(round(val_frac * len(order))))
    split = {"train": sorted(order[n_val:]) + ["ctrl"], "val": sorted(order[:n_val]), "test": sorted(order[:n_val])}
    split_path = work / f"split_{name}.pkl"
    with open(split_path, "wb") as fh:
        pickle.dump(split, fh)
    pd_.prepare_split(split="custom", seed=seed, split_dict_path=str(split_path))
    pd_.get_dataloader(batch_size=batch, test_batch_size=batch)

    pd_.adata.X = _MaskCSR(pd_.adata.X)  # GEARS 0.1.2 indexes X with a pandas mask; recent scipy refuses that
    model = GEARS(pd_, device=device)
    model.model_initialize(hidden_size=hidden)
    model.train(epochs=epochs)

    X = a.X.toarray() if sp.issparse(a.X) else np.asarray(a.X)
    ctrl = X[keys == "control"].mean(0)
    train_means = np.stack([X[keys == k].mean(0) for k in sorted(set(keys) - {"control"})])
    fallback = ctrl + (train_means - ctrl).mean(0)
    means, used_fallback = [], []
    for p in heldout:
        targets = p.split("+")
        if all(g in model.pert_list for g in targets):
            pred = model.predict([targets])
            means.append(np.asarray(next(iter(pred.values())), dtype=np.float64).ravel())
        else:
            means.append(fallback.astype(np.float64))
            used_fallback.append(p)
    means = np.stack(means)
    if means.shape != (len(heldout), len(genes)):
        raise SystemExit(f"GEARS returned shape {means.shape}, expected {(len(heldout), len(genes))}")
    np.savez(out / "predictions.npz", perts=np.array(heldout), means=means, genes=np.array(genes))
    receipt = {"model": "GEARS", "gears_version": _version("cell-gears"), "torch": torch.__version__,
               "device": device, "seed": seed, "epochs": epochs, "hidden_size": hidden, "batch_size": batch,
               "val_frac": val_frac, "train_conditions": len(split["train"]) - 1, "val_conditions": len(split["val"]),
               "train_conditions_outside_graph": sorted(c for c in set(a.obs["condition"]) - {"ctrl"}
                                                        if c not in train_conds),
               "heldout": len(heldout), "heldout_fallback": used_fallback,
               "export_input_sha256": _sha(export / "cellforge_input.h5ad"),
               "predictions_sha256": _sha(out / "predictions.npz"), "seconds": round(time.time() - t0, 1),
               "machine": platform.platform()}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=1))
    return receipt


def _version(dist: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(dist)
    except Exception:
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--export", required=True, help="folder written by cellforge_bridge.py export")
    ap.add_argument("--work", required=True, help="GEARS's own data folder (downloads its gene graph here)")
    ap.add_argument("--out", required=True, help="new folder for predictions.npz and receipt.json")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--device", default="cpu", help="cpu, mps or cuda")
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--batch", type=int, default=32)
    a = ap.parse_args(argv)
    print(json.dumps(run(Path(a.export), Path(a.work), Path(a.out), a.seed, a.epochs, a.device, a.val_frac,
                         a.hidden, a.batch), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
