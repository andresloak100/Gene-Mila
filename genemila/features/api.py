"""Feature API: the ONLY interface agent-written feature code programs against.

A feature maps (perturbation p, gene g) to a small vector. The model then
predicts delta[p, g] = expression of g under p minus control expression of g,
using a single linear model shared across all (p, g) rows. The coefficient of
each feature column is therefore directly interpretable.

Contract:
    compute(ctx, perts, params) -> np.ndarray of shape (len(perts), ctx.n_genes, dim)

Leakage rule: a feature may use training labels only via
ctx.train_delta(exclude=p). For row p it MUST exclude p itself, which is what
`exclude` is for. Validation labels are not available to feature code at all.
"""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar

import numpy as np

REGISTRY: dict[str, type["Feature"]] = {}


class Feature:
    name: ClassVar[str] = ""
    version: ClassVar[int] = 1
    description: ClassVar[str] = ""
    rationale: ClassVar[str] = ""
    inputs: ClassVar[list[str]] = []        # e.g. ["control_cells", "train_delta", "gene_sets"]
    params: ClassVar[dict[str, Any]] = {}  # default parameters
    dim: ClassVar[int] = 1                  # number of output columns
    dependencies: ClassVar[list[str]] = []  # other features used via ctx.feature()

    def compute(self, ctx: "FeatureContext", perts: list[str], params: dict) -> np.ndarray:
        raise NotImplementedError

    @classmethod
    def metadata(cls) -> dict:
        return {
            "name": cls.name, "version": cls.version, "description": cls.description,
            "rationale": cls.rationale, "inputs": list(cls.inputs), "params": dict(cls.params),
            "dim": cls.dim, "dependencies": list(cls.dependencies),
        }


def register(cls: type[Feature]) -> type[Feature]:
    if not cls.name or not cls.name.isidentifier():
        raise ValueError(f"feature name {cls.name!r} must be a python identifier")
    REGISTRY[cls.name] = cls
    return cls


class FeatureContext:
    """Read-only view of the public data. Validation labels are never loaded."""

    def __init__(self, public_dir: str | Path):
        self.public_dir = Path(public_dir)
        z = np.load(self.public_dir / "public.npz", allow_pickle=False)
        self.genes: list[str] = [str(g) for g in z["genes"]]
        self.gene_index: dict[str, int] = {g: i for i, g in enumerate(self.genes)}
        self.n_genes = len(self.genes)
        self.control_cells: np.ndarray = z["control_cells"].astype(np.float64)
        self.control_mean: np.ndarray = self.control_cells.mean(axis=0)
        self.control_std: np.ndarray = self.control_cells.std(axis=0)
        self.perts: list[str] = [str(p) for p in z["perts"]]
        self.train_perts: list[str] = [str(p) for p in z["train_perts"]]
        self._train_delta = z["train_means"].astype(np.float64) - self.control_mean
        self._train_pos = {p: i for i, p in enumerate(self.train_perts)}
        self._targets: dict[str, list[str]] = json.loads((self.public_dir / "knowledge" / "targets.json").read_text())
        self._feature_cache: dict = {}
        self.cache: dict = {}  # free-form cache features may use for shared work

    # ---- perturbation metadata -------------------------------------------------
    def target_genes(self, pert: str) -> list[str]:
        return list(self._targets.get(pert, []))

    def target_indices(self, pert: str) -> list[int]:
        return [self.gene_index[g] for g in self._targets.get(pert, []) if g in self.gene_index]

    # ---- training labels (leave-one-out aware) --------------------------------
    def train_delta(self, exclude: str | None = None) -> tuple[list[str], np.ndarray]:
        """Training perturbations and their delta profiles, minus `exclude`."""
        if exclude is not None and exclude in self._train_pos:
            keep = [i for p, i in self._train_pos.items() if p != exclude]
            return [self.train_perts[i] for i in keep], self._train_delta[keep]
        return list(self.train_perts), self._train_delta

    # ---- prior knowledge ---------------------------------------------------------
    def knowledge(self, name: str) -> Any:
        """Load a prior-knowledge file (e.g. 'gene_sets', 'prior_network'). None if absent."""
        path = self.public_dir / "knowledge" / f"{name}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def available_knowledge(self) -> list[str]:
        return sorted(p.stem for p in (self.public_dir / "knowledge").glob("*.json"))

    # ---- shared helpers ------------------------------------------------------------
    @cached_property
    def gene_corr(self) -> np.ndarray:
        """Pearson correlation between genes across control cells (n_genes x n_genes)."""
        x = self.control_cells - self.control_mean
        sd = np.where(self.control_std > 0, self.control_std, 1.0)
        c = (x.T @ x) / (len(x) * np.outer(sd, sd))
        np.fill_diagonal(c, 1.0)
        return np.nan_to_num(c)

    def feature(self, name: str, perts: list[str], params: dict | None = None) -> np.ndarray:
        """Compute another registered feature (for composition)."""
        key = (name, tuple(perts), json.dumps(params or {}, sort_keys=True))
        if key not in self._feature_cache:
            cls = REGISTRY[name]
            merged = {**cls.params, **(params or {})}
            self._feature_cache[key] = cls().compute(self, perts, merged)
        return self._feature_cache[key]
