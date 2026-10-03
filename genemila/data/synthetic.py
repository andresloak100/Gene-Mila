"""Synthetic perturbation fixture with known biology.

Control cells follow a gene-module factor model, so co-expression is real
signal. Knockouts act through a sparse regulatory network (direct + second-hop
effects), shift the knocked-out gene's module program, and induce a shared
stress response. A noisy subset of the true network and of the modules is
released as "prior knowledge", mimicking real pathway/TF databases.

Because the generating process is known, it is a fair sandbox for checking
that the laboratory can discover features that genuinely help.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .bundle import make_splits, write_bundle


def generate(
    out_dir: Path,
    n_genes: int = 300,
    n_modules: int = 10,
    n_tfs: int = 40,
    n_perts: int = 80,
    n_control: int = 1500,
    cells_per_pert: int = 80,
    seed: int = 0,
    split_seed: int = 0,
) -> Path:
    rng = np.random.default_rng(seed)
    genes = [f"G{i:04d}" for i in range(n_genes)]
    module = rng.integers(0, n_modules, size=n_genes)
    mu = rng.gamma(2.0, 0.8, size=n_genes) + 0.2

    loadings = np.zeros((n_genes, n_modules))
    loadings[np.arange(n_genes), module] = rng.normal(0.6, 0.15, size=n_genes)
    loadings += rng.normal(0, 0.05, size=loadings.shape)

    tfs = rng.choice(n_genes, size=n_tfs, replace=False)
    adj = np.zeros((n_genes, n_genes))  # adj[r, t]: regulator r -> target t
    for r in tfs:
        same = np.flatnonzero(module == module[r])
        other = np.flatnonzero(module != module[r])
        tgt = np.concatenate([
            rng.choice(same, size=min(len(same), rng.integers(4, 10)), replace=False),
            rng.choice(other, size=rng.integers(1, 4), replace=False),
        ])
        tgt = tgt[tgt != r]
        adj[r, tgt] = rng.choice([-1, 1], size=len(tgt), p=[0.3, 0.7]) * rng.uniform(0.3, 0.9, len(tgt))

    stress = rng.normal(0, 1, size=n_genes) * (rng.random(n_genes) < 0.15) * 0.4

    def sample_cells(n, shift):
        z = rng.normal(size=(n, n_modules))
        x = mu + shift + z @ loadings.T + rng.normal(0, 0.35, size=(n, n_genes))
        return np.clip(x, 0, None)

    control = sample_cells(n_control, 0.0)

    non_tf = np.setdiff1d(np.arange(n_genes), tfs)
    n_tf_perts = min(n_tfs, n_perts // 2)
    pert_targets = np.concatenate([
        rng.choice(tfs, size=n_tf_perts, replace=False),
        rng.choice(non_tf, size=n_perts - n_tf_perts, replace=False),
    ])
    pert_means, pert_ncells, targets = {}, {}, {}
    for t in pert_targets:
        kd = 0.85 * mu[t]
        delta = np.zeros(n_genes)
        delta[t] -= kd
        first = -kd * adj[t]  # loss of activation / repression of targets
        second = 0.5 * (first @ adj) / max(1.0, np.abs(first).sum() ** 0.5)
        module_shift = -0.35 * kd * loadings[:, module[t]] / loadings[:, module[t]].max()
        delta += first + second + module_shift + rng.uniform(0.3, 1.2) * stress
        name = f"{genes[t]}_KO"
        cells = sample_cells(cells_per_pert, delta)
        pert_means[name] = cells.mean(axis=0)
        pert_ncells[name] = cells_per_pert
        targets[name] = [genes[t]]

    gene_sets = {}
    for m in range(n_modules):
        members = np.flatnonzero(module == m)
        keep = members[rng.random(len(members)) < 0.8]
        noise = rng.choice(n_genes, size=max(1, len(members) // 5), replace=False)
        gene_sets[f"MODULE_{m:02d}"] = sorted(genes[i] for i in set(keep) | set(noise))
    edges = []
    for r, t in zip(*np.nonzero(adj)):
        if rng.random() < 0.6:
            edges.append([genes[r], genes[t], float(np.sign(adj[r, t]))])
    for _ in range(len(edges) // 4):
        r, t = rng.choice(tfs), rng.integers(n_genes)
        edges.append([genes[r], genes[t], float(rng.choice([-1, 1]))])

    splits = make_splits(list(pert_means), seed=split_seed)
    sub = control[rng.choice(n_control, size=min(n_control, 1000), replace=False)]
    return write_bundle(
        Path(out_dir), "synthetic", genes, sub, pert_means, pert_ncells, targets, splits,
        knowledge={
            "gene_sets.json": gene_sets,
            "prior_network.json": edges,
            "transcription_factors.json": sorted(genes[i] for i in tfs),
        },
        extra_meta={"generator": "genemila.data.synthetic", "seed": seed,
                    "description": "Synthetic knockout screen with module structure and a regulatory network."},
    )
