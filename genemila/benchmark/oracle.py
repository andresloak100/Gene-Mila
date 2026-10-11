"""Query-only validation (validation set 2).

Agents never see these labels. Only the controller calls the oracle, only at
the end of a run, only for a capped number of visible-validation winners, and
every query is logged. The oracle returns aggregate metrics, never labels and never a value of one
perturbation: for a bundle with pairs, a gene-grouped split or a recorded modality (evaluator.bundle_strata) the
metrics also carry pearson_delta without each perturbation's own targets and per-category means, sds and counts
(a category too small to hide its members' values reports its count only, and so do the smallest others while the
hidden members number fewer than CATEGORY_MIN_N: evaluator.hidden_categories), and `query_paired` compares two
models on the same perturbations (mean difference, paired SE, wins), pooled and per category. A run's sealed
queries go through its lab (Lab.query_only, Lab.query_paired), which records each scored model in lab.db so the
per-run cap holds in every later process; a paired query made on the lab's oracle directly is recorded too
(on_paired).

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
from . import PRIMARY_METRIC, comparable, reference
from .evaluator import bundle_strata, evaluate, metric_values, paired_summary


class QueryBudgetExceeded(RuntimeError):
    pass


class QueryOracle:
    def __init__(self, data_dir: Path, max_queries: int = 5, used: "callable | None" = None,
                 selection: str = PRIMARY_METRIC, on_paired: "callable | None" = None):
        """`used` returns how many queries the run has already made (persisted by the lab in its database),
        so the cap holds per run, across processes and re-summaries, not per process. `on_paired(out)` is called
        under the oracle's lock after every paired query, before it returns, so whoever holds the oracle persists
        the two queries it spent (the lab writes them to lab.db; see Lab.query_paired) and the cap never forgets
        them; None (a tool's own oracle) records nothing."""
        self._labels_path = Path(data_dir) / "private" / "val2.npz"
        self.max_queries = max_queries
        self.queries: list[dict] = []
        self._used = used
        self._on_paired = on_paired
        self.selection = selection  # the run's selection rule: sealed `primary` means the same as visible
        self._lock = threading.Lock()
        self._ref = False  # DE reference for comparable metrics, loaded on first query
        self._strata = False  # the bundle's extra scoring (evaluator.bundle_strata), loaded on first query
        self._spent = 0  # queries this instance made: one per query, two per paired query (two models scored)

    @property
    def used(self) -> int:
        return max(self._spent, len(self.queries), int(self._used()) if self._used is not None else 0)

    def _extras(self) -> dict:
        """evaluate()'s extras for this bundle: none for a bundle without strata (scored exactly as before)."""
        if self._strata is False:
            self._strata = bundle_strata(self._labels_path.parent.parent)
        if self._strata is None:
            return {}
        return {"targets": self._strata["target_idx"], "categories": self._strata["categories"] or None}

    @staticmethod
    def _ordered(pred: np.ndarray, pert_order: list[str], labels: LabelSet) -> np.ndarray:
        idx = {p: i for i, p in enumerate(pert_order)}
        if sorted(idx) != sorted(labels.perts):
            raise ValueError("predictions must cover exactly the query-only perturbations")
        return np.stack([pred[idx[p]] for p in labels.perts])

    @property
    def perts(self) -> list[str]:
        return LabelSet.load(self._labels_path).perts

    def query(self, experiment_id: str, pred: np.ndarray, pert_order: list[str], control_mean: np.ndarray,
              celleval_profile: str | None = None, genes: list[str] | None = None) -> dict:
        with self._lock:
            if self.used >= self.max_queries:
                raise QueryBudgetExceeded(f"query-only budget of {self.max_queries} exhausted")
            labels = LabelSet.load(self._labels_path)
            pred = self._ordered(pred, pert_order, labels)
            result = evaluate(pred, labels.means, control_mean, labels.perts, selection=self.selection,
                              **self._extras())
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
            self._spent += 1
            self.queries.append(out)
            return out

    def query_paired(self, experiment_a: str, pred_a: np.ndarray, perts_a: list[str], experiment_b: str,
                     pred_b: np.ndarray, perts_b: list[str], control_mean: np.ndarray,
                     metric: str = PRIMARY_METRIC) -> dict:
        """Compare two models on the query-only perturbations, a minus b, by one per-perturbation metric
        ("primary": the run's selection rule per perturbation): evaluator.paired_summary's mean difference,
        paired SE, wins and verdict, pooled and, for a bundle with categories, per category; and each model's
        aggregate metrics as `query` reports them (without the comparable and cell-eval metrics). Both models are
        scored on the sealed set, so the query counts as two against the cap and is refused unless two remain;
        nothing of a single perturbation leaves the oracle. A run asks through Lab.query_paired, which records both
        scorings in lab.db (on_paired)."""
        with self._lock:
            if self.used + 2 > self.max_queries:
                raise QueryBudgetExceeded(f"a paired query needs two of the query-only budget of {self.max_queries}; "
                                          f"{max(0, self.max_queries - self.used)} left")
            labels = LabelSet.load(self._labels_path)
            extras = self._extras()
            res = [evaluate(self._ordered(p, order, labels), labels.means, control_mean, labels.perts,
                            selection=self.selection, **extras)
                   for p, order in ((pred_a, perts_a), (pred_b, perts_b))]
            a, b = (metric_values(r["per_perturbation"], metric, self.selection) for r in res)
            out = {"experiments": [experiment_a, experiment_b], "metric": metric,
                   "a": {"experiment_id": experiment_a, "metrics": res[0]["metrics"]},
                   "b": {"experiment_id": experiment_b, "metrics": res[1]["metrics"]},
                   "paired": paired_summary(a, b, extras.get("categories"))}
            self._spent += 2
            self.queries.append(out)
            if self._on_paired is not None:
                self._on_paired(out)
            return out
