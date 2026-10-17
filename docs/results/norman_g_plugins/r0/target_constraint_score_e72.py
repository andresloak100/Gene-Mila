import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConstraintScoreE72(Feature):
    name = "target_constraint_score_e72"
    version = 1
    description = "Average LOEUF (or pLI) of perturbation target genes; pairs averaged over both targets."
    rationale = ("Loss-of-function intolerant genes may have broader regulatory networks, so "
                 "perturbing them could yield larger or more specific expression changes. "
                 "Constraint data is orthogonal to expression/network features.")
    inputs = ["knowledge", "target_genes"]
    params = {"metric": "loeuf"}
    dim = 1

    def _build_lookup(self, ctx, metric):
        """Return dict gene->value from gene_constraint, plus median for imputation."""
        key = ("constraint_lookup", metric)
        if key in ctx.cache:
            return ctx.cache[key]

        lookup = {}
        median = 0.0
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            columns = kc.get("columns", [])
            genes = kc.get("genes", {}) or {}
            # choose column index
            col_name = None
            if metric == "pLI" or metric == "pli":
                for c in ("pLI", "pli", "p_li"):
                    if c in columns:
                        col_name = c
                        break
            if col_name is None:
                for c in ("oe_lof_upper", "loeuf", "LOEUF"):
                    if c in columns:
                        col_name = c
                        break
            if col_name is not None:
                ci = columns.index(col_name)
                vals = []
                for g, row in genes.items():
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        lookup[g] = fv
                        vals.append(fv)
                if vals:
                    median = float(np.median(vals))
        ctx.cache[key] = (lookup, median)
        return ctx.cache[key]

    def compute(self, ctx, perts, params):
        metric = params.get("metric", "loeuf")
        lookup, median = self._build_lookup(ctx, metric)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                score = median
            else:
                vals = []
                for g in targets:
                    v = lookup.get(g, None)
                    if v is None:
                        v = median
                    vals.append(v)
                score = float(np.mean(vals))
            if not np.isfinite(score):
                score = median if np.isfinite(median) else 0.0
            # broadcast the same per-perturbation score across all genes
            out[i, :, 0] = score
        return out
