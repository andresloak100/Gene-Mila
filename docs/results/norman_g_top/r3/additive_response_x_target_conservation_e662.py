import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveResponseXTargetConservation(Feature):
    name = "additive_response_x_target_conservation_e662"
    version = 1
    description = "Product of additive_response and mean (1 - LOEUF) over target genes."
    rationale = "Conserved (LoF-intolerant) target genes may produce more robust downstream effects."
    inputs = ["control_cells", "gene_constraint", "train_delta"]
    params = {}
    dim = 1

    def _conservation(self, ctx):
        cache = ctx.cache
        if "cons_e662" in cache:
            return cache["cons_e662"]
        cons = np.full(ctx.n_genes, np.nan, dtype=float)
        k = ctx.knowledge("gene_constraint")
        if k is not None:
            cols = k.get("columns", [])
            genes = k.get("genes", {})
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    cons[gi] = 1.0 - v
        cache["cons_e662"] = cons
        return cons

    def _additive_response(self, ctx, p, targets):
        cache = ctx.cache
        key = ("add_e662", p)
        if key in cache:
            return cache[key]
        _, d = ctx.train_delta(exclude=p)
        out = np.zeros(ctx.n_genes, dtype=float)
        if d.shape[0] > 0 and len(targets) > 0:
            tvals = d[:, targets]
            pos = tvals > 0
            denom = pos.sum(axis=0).astype(float)
            num = np.where(pos, tvals, 0.0).sum(axis=0)
            with np.errstate(invalid="ignore", divide="ignore"):
                single = np.where(denom > 0, num / np.maximum(denom, 1.0), 0.0)
            out[targets] = single
        cache[key] = out
        return out

    def compute(self, ctx, perts, params):
        cons = self._conservation(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue
            add = self._additive_response(ctx, p, targets)
            cvals = cons[targets]
            cvals = cvals[np.isfinite(cvals)]
            if cvals.size == 0:
                score = 0.0
            else:
                score = float(np.mean(cvals))
            out[i, :, 0] = add * score
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
