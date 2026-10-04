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

import copy
import hashlib
import json
import os
import tempfile
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

    _preloaded: dict[str, "FeatureContext"] = {}

    def __init__(self, public_dir: str | Path, cache_dir: str | Path | None = None):
        self.public_dir = Path(public_dir)
        self.cache_dir = Path(cache_dir) if cache_dir else None
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
        self.label_reads = 0   # how often training labels were read (tells label-dependent features apart)

    # ---- cross-validation views ---------------------------------------------------
    @property
    def train_signature(self) -> str:
        """Identifies the training set this context exposes (feature caches key on it)."""
        return hashlib.sha256("\n".join(self.train_perts).encode()).hexdigest()[:12]

    def without_train(self, exclude: list[str]) -> "FeatureContext":
        """A view whose training labels exclude `exclude` (a cross-validation fold). Feature code sees a
        smaller training set and nothing else changes; the fold's labels are unreachable through it. The view
        has its own memo caches so nothing computed from the full training set leaks in."""
        out = copy.copy(self)
        gone = set(exclude)
        keep = [i for i, p in enumerate(self.train_perts) if p not in gone]
        out.train_perts = [self.train_perts[i] for i in keep]
        out._train_delta = self._train_delta[keep]
        out._train_pos = {p: i for i, p in enumerate(out.train_perts)}
        out._feature_cache = {}
        out.cache = {}
        return out

    # ---- perturbation metadata -------------------------------------------------
    def target_genes(self, pert: str) -> list[str]:
        return list(self._targets.get(pert, []))

    def target_indices(self, pert: str) -> list[int]:
        return [self.gene_index[g] for g in self._targets.get(pert, []) if g in self.gene_index]

    # ---- training labels (leave-one-out aware) --------------------------------
    def train_delta(self, exclude: str | None = None) -> tuple[list[str], np.ndarray]:
        """Training perturbations and their delta profiles, minus `exclude`."""
        self.label_reads += 1
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
    @classmethod
    def shared(cls, public_dir: str | Path, cache_dir: str | Path | None = None) -> "FeatureContext":
        """A context loaded once per process. In the fork server it is loaded before forking, so
        each experiment starts with the data already in memory (copy-on-write)."""
        key = str(Path(public_dir).resolve())
        ctx = cls._preloaded.get(key)
        if ctx is None:
            ctx = cls._preloaded[key] = cls(public_dir, cache_dir)
        elif cache_dir and ctx.cache_dir is None:
            ctx.cache_dir = Path(cache_dir)
        return ctx

    def _disk_cached(self, name: str, compute) -> np.ndarray:
        """Shared matrices are computed once per run and reused by every experiment."""
        if self.cache_dir is None:
            return compute()
        path = self.cache_dir / f"{name}.npy"
        if path.exists():
            return np.load(path, allow_pickle=False)
        arr = compute()
        _atomic_save(path, arr)
        return arr

    @cached_property
    def gene_corr(self) -> np.ndarray:
        """Pearson correlation between genes across control cells (n_genes x n_genes)."""
        def compute():
            x = self.control_cells - self.control_mean
            sd = np.where(self.control_std > 0, self.control_std, 1.0)
            c = (x.T @ x) / (len(x) * np.outer(sd, sd))
            np.fill_diagonal(c, 1.0)
            return np.nan_to_num(c)
        return self._disk_cached("gene_corr", compute)

    def feature(self, name: str, perts: list[str], params: dict | None = None) -> np.ndarray:
        """Compute another registered feature (for composition)."""
        key = (name, tuple(perts), json.dumps(params or {}, sort_keys=True))
        if key not in self._feature_cache:
            cls = REGISTRY[name]
            merged = {**cls.params, **(params or {})}
            self._feature_cache[key] = cls().compute(self, perts, merged)
        return self._feature_cache[key]


def _atomic_save(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.npy")
    with os.fdopen(fd, "wb") as fh:
        np.save(fh, arr, allow_pickle=False)
    os.replace(tmp, path)
