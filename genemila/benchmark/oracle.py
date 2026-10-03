"""Query-only validation (validation set 2).

Agents never see these labels. Only the controller calls the oracle, only at
the end of a run, only for a capped number of visible-validation winners, and
every query is logged. The oracle returns aggregate metrics, never labels.

The current implementation keeps the labels in a file outside every worktree
and outside the public data copy given to experiments. To move to a truly
remote oracle (e.g. a service that holds the labels), implement the same
`query()` signature over HTTP; nothing else changes.
"""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np

from ..data.bundle import LabelSet
from .evaluator import evaluate


class QueryBudgetExceeded(RuntimeError):
    pass


class QueryOracle:
    def __init__(self, data_dir: Path, max_queries: int = 5):
        self._labels_path = Path(data_dir) / "private" / "val2.npz"
        self.max_queries = max_queries
        self.queries: list[dict] = []
        self._lock = threading.Lock()

    @property
    def perts(self) -> list[str]:
        return LabelSet.load(self._labels_path).perts

    def query(self, experiment_id: str, pred: np.ndarray, pert_order: list[str], control_mean: np.ndarray) -> dict:
        with self._lock:
            if len(self.queries) >= self.max_queries:
                raise QueryBudgetExceeded(f"query-only budget of {self.max_queries} exhausted")
            labels = LabelSet.load(self._labels_path)
            idx = {p: i for i, p in enumerate(pert_order)}
            if sorted(idx) != sorted(labels.perts):
                raise ValueError("predictions must cover exactly the query-only perturbations")
            pred = np.stack([pred[idx[p]] for p in labels.perts])
            result = evaluate(pred, labels.means, control_mean, labels.perts)
            out = {"experiment_id": experiment_id, "metrics": result["metrics"]}
            self.queries.append(out)
            return out
