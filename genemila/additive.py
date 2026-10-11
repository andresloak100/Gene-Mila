"""The additive rule for perturbations of several genes, shared by the lab's additive baseline, the built-in
feature additive_response (genemila/features/builtin.py) and tools/refit_visible.py. Plain numpy, so feature code
running in an experiment process can import it without the lab."""

from __future__ import annotations

import numpy as np


def additive_delta(perts: list[str], targets: dict, train: list[str], train_delta: np.ndarray) -> np.ndarray:
    """baseline_additive's predicted change, the one rule the lab, the built-in additive_response and
    tools/refit_visible.py share: the sum over a
    perturbation's target genes (targets: perturbation -> its genes; sorted and without repeats, so the order a
    pair lists them changes nothing) of each gene's single change in `train` (the mean change in train_delta of
    the training perturbations whose one target it is) or, for a gene without a training single, the mean change of
    all training singles. A pair is Δ_A + Δ_B, a held-out single the mean single change; a perturbation without a
    listed target counts as one gene without a single. With no single in training at all, the mean training change
    stands in for the mean single change."""
    rows: dict[str, list[int]] = {}
    for i, p in enumerate(train):
        tg = targets.get(p) or []
        if len(tg) == 1:
            rows.setdefault(tg[0], []).append(i)
    single = {g: train_delta[r].mean(axis=0) for g, r in rows.items()}
    every = [i for r in rows.values() for i in r]
    fill = train_delta[every].mean(axis=0) if every else train_delta.mean(axis=0)
    out = np.zeros((len(perts), train_delta.shape[1]))
    for j, p in enumerate(perts):
        for g in sorted(set(targets.get(p) or [])) or [None]:
            out[j] += single.get(g, fill)
    return out
