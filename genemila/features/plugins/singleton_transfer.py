"""Fixed-penalty external transfer for a bounded development comparison.

The correction is optional: importing this module does not change the built-in
feature set. Its reference classes can also be computed directly. Every
prediction reads labels only through train_delta(exclude=p); there is no cache.
For a training singleton, other singleton conditions with the same target are
also excluded. The correction's additive reference uses this same filtered view.
"""

import numpy as np

from genemila.features.api import Feature, register


KNOWLEDGE = "replogle2022_k562"
MIN_SHARED_GENES = 3
MIN_TRAINING_ROWS = 3


def _external_rows(ctx):
    """Align measured external values; missing/nonfinite values stay missing."""
    ext = ctx.knowledge(KNOWLEDGE) or {}
    genes = [str(g) for g in ext.get("genes") or []]
    index = {g: j for j, g in enumerate(genes)}
    measured = ext.get("measured", [True] * len(genes))
    rows = {}
    for target, rec in (ext.get("perts") or {}).items():
        if not isinstance(rec, dict):
            continue
        cells = rec.get("n_cells")
        if cells is not None:
            try:
                if int(cells) <= 0:
                    continue
            except (ValueError, TypeError, OverflowError):
                continue
        try:
            values = np.asarray(rec.get("delta", []), dtype=np.float64)
        except (ValueError, TypeError):
            continue
        if values.ndim != 1:
            continue
        row = np.full(ctx.n_genes, np.nan)
        for i, gene in enumerate(ctx.genes):
            j = index.get(gene)
            if j is not None and j < len(measured) and measured[j] and j < len(values):
                if np.isfinite(values[j]):
                    row[i] = values[j]
        rows[str(target)] = row
    return rows


def _unit(row):
    if row is None:
        return None
    finite = np.isfinite(row)
    if int(finite.sum()) < MIN_SHARED_GENES:
        return None
    z = np.zeros(len(row))
    z[finite] = row[finite] - row[finite].mean()
    norm = np.linalg.norm(z)
    return z / norm if np.isfinite(norm) and norm > 0 else None


def _pert_unit(ctx, rows, pert):
    targets = sorted(set(ctx.target_genes(pert)))
    if not targets or any(t not in rows for t in targets):
        return None
    total = rows[targets[0]].copy()
    for target in targets[1:]:
        total += rows[target]
    return _unit(total)


def _transfer(query, units, responses, mean):
    """The sole fixed KRR recipe: lambda=1, no label-dependent model choice."""
    if query is None or len(units) < MIN_TRAINING_ROWS:
        return mean.copy()
    z = np.asarray(units, dtype=np.float64)
    y = np.asarray(responses, dtype=np.float64)
    weights = np.linalg.solve(z @ z.T + np.eye(len(z)), z @ query)
    return mean + weights @ (y - mean)


def _available(ctx, pert):
    """Leave out the query and same-target replicates of a training singleton."""
    names, deltas = ctx.train_delta(exclude=pert)
    targets = ctx.target_genes(pert)
    if pert in ctx.train_perts and len(targets) == 1:
        keep = [i for i, name in enumerate(names) if ctx.target_genes(name) != targets]
        names, deltas = [names[i] for i in keep], deltas[keep]
    return names, deltas


def _singles(ctx, names, deltas):
    groups = {}
    for i, pert in enumerate(names):
        targets = ctx.target_genes(pert)
        if len(targets) == 1:
            groups.setdefault(targets[0], []).append(i)
    singles = {target: deltas[indices].mean(axis=0) for target, indices in groups.items()}
    every = [i for indices in groups.values() for i in indices]
    if every:
        mean = deltas[every].mean(axis=0)
    elif len(names):
        mean = deltas.mean(axis=0)
    else:
        mean = np.zeros(ctx.n_genes)
    return singles, mean


def _singleton_predictions(ctx, pert, names, deltas, rows):
    singles, mean = _singles(ctx, names, deltas)
    units, responses = [], []
    for target in sorted(singles):
        z = _unit(rows.get(target))
        if z is not None:
            units.append(z)
            responses.append(singles[target])
    additive = np.zeros(ctx.n_genes)
    transferred = np.zeros(ctx.n_genes)
    for target in sorted(set(ctx.target_genes(pert))) or [None]:
        baseline = singles.get(target, mean)
        additive += baseline
        if target in singles:
            transferred += baseline
        else:
            transferred += _transfer(_unit(rows.get(target)), units, responses, mean)
    return additive, transferred


def singleton_coverage(ctx, perts):
    """Count actual gate routes in each query's label-safe training view.

    Counts use the same target deduplication and exclusion as predictions. A
    zero-cell external row is absent. Missing/unusable query profiles take
    precedence over insufficient donors, matching _transfer's early return.
    An unannotated query has zero named targets and one fallback contribution.
    """
    rows = _external_rows(ctx)
    out = []
    for pert in perts:
        names, deltas = _available(ctx, pert)
        singles, _ = _singles(ctx, names, deltas)
        usable = sum(_unit(rows.get(t)) is not None for t in singles)
        targets = sorted(set(ctx.target_genes(pert)))
        known, transferred = 0, 0
        reasons = {"unknown_target": 0, "missing_external": 0,
                   "unusable_external": 0, "too_few_singletons": 0}
        for target in targets or [None]:
            if target in singles:
                known += 1
            elif target is None:
                reasons["unknown_target"] += 1
            elif target not in rows:
                reasons["missing_external"] += 1
            elif _unit(rows[target]) is None:
                reasons["unusable_external"] += 1
            elif usable < MIN_TRAINING_ROWS:
                reasons["too_few_singletons"] += 1
            else:
                transferred += 1
        out.append({"pert": pert, "n_targets": len(targets), "known_targets": known,
                    "missing_targets": max(1, len(targets)) - known,
                    "transferred_targets": transferred, "fallback_reasons": reasons,
                    "singleton_training_targets": len(singles),
                    "usable_singleton_training_targets": usable})
    return out


class OrdinaryExternalTransfer(Feature):
    """Whole-condition external KRR comparator, fitted to all training conditions."""

    name = "ordinary_external_transfer"
    description = "External kernel transfer with fixed penalty 1 over available training conditions."
    inputs = ["train_delta", "targets", KNOWLEDGE]
    dim = 1

    def compute(self, ctx, perts, params):
        rows = _external_rows(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, pert in enumerate(perts):
            names, deltas = _available(ctx, pert)
            if not names:
                continue
            mean = deltas.mean(axis=0)
            units, responses = [], []
            for j, name in enumerate(names):
                z = _pert_unit(ctx, rows, name)
                if z is not None:
                    units.append(z)
                    responses.append(deltas[j])
            out[i, :, 0] = _transfer(_pert_unit(ctx, rows, pert), units, responses, mean)
        return out


class SingletonTransferAdditive(Feature):
    """Preserve known singleton responses and transfer each missing target separately."""

    name = "singleton_transfer_additive"
    description = "Additive sum of known singleton means and fixed-penalty external transfers for missing targets."
    inputs = ["train_delta", "targets", KNOWLEDGE]
    dim = 1

    def compute(self, ctx, perts, params):
        rows = _external_rows(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, pert in enumerate(perts):
            names, deltas = _available(ctx, pert)
            out[i, :, 0] = _singleton_predictions(ctx, pert, names, deltas, rows)[1]
        return out


class DirectExternalAdditive(Feature):
    """Cheap reference: replace missing singleton responses with signed raw external rows."""

    name = "direct_external_additive"
    description = "Known singleton means plus signed external responses for missing targets, with mean-single fill."
    inputs = ["train_delta", "targets", KNOWLEDGE]
    dim = 1

    def compute(self, ctx, perts, params):
        rows = _external_rows(ctx)
        sign = (ctx.knowledge(KNOWLEDGE) or {}).get("sign", 1)
        if isinstance(sign, bool) or sign not in (-1, 1):
            raise ValueError("external screen sign must be -1 or +1")
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, pert in enumerate(perts):
            names, deltas = _available(ctx, pert)
            singles, mean = _singles(ctx, names, deltas)
            for target in sorted(set(ctx.target_genes(pert))) or [None]:
                if target in singles:
                    out[i, :, 0] += singles[target]
                else:
                    row = rows.get(target)
                    out[i, :, 0] += mean if row is None else np.where(np.isfinite(row), sign * row, mean)
        return out


@register
class SingletonTransferCorrection(Feature):
    """Optional one-column correction to the unchanged built-in additive rule."""

    name = "singleton_transfer_correction"
    description = "Singleton-transfer additive prediction minus the ordinary additive prediction, fixed penalty 1."
    inputs = ["train_delta", "targets", KNOWLEDGE]
    dim = 1

    def compute(self, ctx, perts, params):
        rows = _external_rows(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, pert in enumerate(perts):
            names, deltas = _available(ctx, pert)
            additive, transferred = _singleton_predictions(ctx, pert, names, deltas, rows)
            out[i, :, 0] = transferred - additive
        return out
