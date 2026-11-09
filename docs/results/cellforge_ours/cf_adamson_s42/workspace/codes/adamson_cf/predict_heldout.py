#!/usr/bin/env python
"""Predict held-out perturbation mean expression profiles.

This is the prediction companion to ``result.py``.  It uses exactly the model,
preprocessing, hyperparameters and number of epochs defined in ``result.py``
and trains on every perturbation group in the supplied training file (no
out-of-distribution perturbation holdout and no validation split).

Outputs an ``npz`` file with:
  * ``perts`` -- the held-out perturbation keys, as a string array, in the
    order read from the JSON list.
  * ``means`` -- a float32 array of shape (n_perts, n_genes) giving the
    predicted mean expression for every gene in the training file, in the
    file's gene order and on the file's normalisation scale (counts per 10k,
    log1p).

Only the two input files are read.  The model is trained on the CPU (the
reference implementation in ``result.py``) which is always acceptable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional, Sequence

import numpy as np

import result as res


def _read_heldout(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"--heldout must point to a JSON list, got {type(data).__name__}")
    return [str(x) for x in data]


def _full_baseline(adata, control_mask: Optional[np.ndarray]) -> np.ndarray:
    """Mean log-normalised expression per original gene, control cells only.

    The model in ``result.py`` is trained on the selected highly-variable genes
    only.  For the full-gene output we predict the model response on the
    selected genes and return every other gene at its control mean (a predicted
    change of zero), matching the file's gene order and scale.
    """
    x = adata.X
    if res._is_sparse(x):
        if control_mask is None:
            full = np.asarray(x.mean(axis=0)).ravel().astype(np.float32)
        else:
            full = np.asarray(x[control_mask, :].mean(axis=0)).ravel().astype(np.float32)
    else:
        arr = np.asarray(x, dtype=np.float32)
        if control_mask is None:
            full = arr.mean(axis=0).astype(np.float32)
        else:
            full = arr[control_mask].mean(axis=0).astype(np.float32)
    return full


def _device() -> str:
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train the result.py model on all training perturbations and "
        "predict held-out perturbation mean profiles."
    )
    parser.add_argument("--data", required=True, help="Path to the training .h5ad file.")
    parser.add_argument("--heldout", required=True, help="Path to a JSON list of held-out perturbation keys.")
    parser.add_argument("--out", required=True, help="Output path for the .npz predictions.")
    parser.add_argument("--epochs", type=int, default=res.Config().epochs,
                        help="Number of training epochs (default: result.py Config epochs).")
    parser.add_argument("--seed", type=int, default=res.Config().seed,
                        help="Random seed (default: result.py Config seed).")
    args = parser.parse_args(argv)

    device_name = _device()
    if device_name == "mps":
        # The reference training loop hardcodes CPU; importing it keeps the
        # model exactly as defined.  CPU remains correct and is always allowed.
        res.log.info("MPS detected; result.py's reference loop will run on CPU.")

    if not os.path.exists(args.data):
        res.log.error("Training data not found: %s", args.data)
        return 2
    if not os.path.exists(args.heldout):
        res.log.error("Held-out perturbation file not found: %s", args.heldout)
        return 2

    heldout_keys = _read_heldout(args.heldout)
    if len(heldout_keys) == 0:
        res.log.error("--heldout contains no perturbation keys")
        return 2

    cfg = res.Config(seed=args.seed, epochs=args.epochs)

    adata = res._anndata.read_h5ad(args.data)
    orig_names = [str(n) for n in adata.var_names]
    name_to_orig_idx = {name: i for i, name in enumerate(orig_names)}

    # Exactly the preprocessing defined in result.py.
    pre = res.Preprocessor(cfg)
    x_train = pre.fit(adata)

    train_labels = res._labels_for(adata.obs, pre.perturb_column)
    train_groups = res.build_group_data(x_train, train_labels, pre.baseline)

    if train_groups.targets.shape[0] == 0:
        res.log.error("No training groups available")
        return 2

    res.log.info(
        "Training on %d groups (%d perturbed) for %d epochs",
        train_groups.targets.shape[0],
        sum(1 for lab in train_groups.labels if lab != "control"),
        cfg.epochs,
    )

    # Model exactly as result.py defines it.
    res._set_seed(cfg.seed)
    model = res.PerturbationResponseModel(n_genes=pre.baseline.shape[0], cfg=cfg)
    history = res.train_model(model, train_groups, None, cfg)
    res.log.info("Training finished after %s epochs", int(history.get("epochs_run", cfg.epochs)))

    # Predictions for the held-out keys (one hashed token per key).
    heldout_data = res.PerturbationData(
        baseline=pre.baseline.copy(),
        labels=heldout_keys,
        targets=np.zeros((len(heldout_keys), pre.baseline.shape[0]), dtype=np.float32),
        n_cells=np.zeros(len(heldout_keys), dtype=int),
    )
    selected_preds = res.predict_groups(model, heldout_data, cfg)  # [n_perts, n_selected]

    # Expand to every gene in the training file, in file order.  Selected genes
    # carry the model prediction; all other genes are held at their control
    # mean (predicted change of zero) on the same log1p scale.
    control_mask = pre._control_mask(adata.obs)
    full_baseline = _full_baseline(adata, control_mask)
    means = np.tile(full_baseline[None, :], (len(heldout_keys), 1)).astype(np.float32)

    missing = 0
    for j, name in enumerate(pre.selected_gene_names):
        orig_idx = name_to_orig_idx.get(name)
        if orig_idx is None:
            missing += 1
            continue
        means[:, orig_idx] = selected_preds[:, j]
    if missing:
        res.log.warning("%d selected gene names were not found in the training var_names", missing)

    if not np.all(np.isfinite(means)):
        res.log.warning("Non-finite values present in prediction means")

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    np.savez(
        args.out,
        perts=np.asarray(heldout_keys, dtype=str),
        means=means.astype(np.float32),
    )
    res.log.info("Wrote %d x %d predictions to %s", means.shape[0], means.shape[1], args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
