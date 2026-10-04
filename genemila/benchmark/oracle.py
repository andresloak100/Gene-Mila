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
from . import comparable, reference
from .evaluator import evaluate


class QueryBudgetExceeded(RuntimeError):
    pass


class QueryOracle:
    def __init__(self, data_dir: Path, max_queries: int = 5):
        self._labels_path = Path(data_dir) / "private" / "val2.npz"
        self.max_queries = max_queries
        self.queries: list[dict] = []
        self._lock = threading.Lock()
        self._ref = False  # DE reference for comparable metrics, loaded on first query

    @property
    def perts(self) -> list[str]:
        return LabelSet.load(self._labels_path).perts

    def query(self, experiment_id: str, pred: np.ndarray, pert_order: list[str], control_mean: np.ndarray,
              celleval_profile: str | None = None, genes: list[str] | None = None) -> dict:
        with self._lock:
            if len(self.queries) >= self.max_queries:
                raise QueryBudgetExceeded(f"query-only budget of {self.max_queries} exhausted")
            labels = LabelSet.load(self._labels_path)
            idx = {p: i for i, p in enumerate(pert_order)}
            if sorted(idx) != sorted(labels.perts):
                raise ValueError("predictions must cover exactly the query-only perturbations")
            pred = np.stack([pred[idx[p]] for p in labels.perts])
            result = evaluate(pred, labels.means, control_mean, labels.perts)
            if self._ref is False:
                self._ref = reference.load(self._labels_path.parent.parent, "val2")
            result["metrics"].update(comparable.score(pred, labels.means, labels.perts, self._ref, control_mean))
            out = {"experiment_id": experiment_id, "metrics": result["metrics"]}
            cells = self._labels_path.parent / "val2_cells.npz"
            if celleval_profile and genes is not None and cells.exists():
                from . import celleval
                if celleval.available():
                    try:
                        X, lab = celleval.load_real_cells(self._labels_path.parent.parent, "val2")
                        out["cell_eval"] = celleval.score(dict(zip(labels.perts, pred - control_mean)), X, lab,
                                                          genes, profile=celleval_profile)
                    except Exception as exc:  # report, never lose the oracle query
                        out["cell_eval_error"] = f"{type(exc).__name__}: {exc}"[:300]
            self.queries.append(out)
            return out
