import numpy as np
from genemila.features.api import Feature, register

@register
class SynZDirectE119(Feature):
    name = "syn_z_direct_e119"
    version = 1
    description = "Numeric feature: syn_z value from gene_constraint for gene g."
    rationale = "Synonymous constraint may indicate translational regulation, affecting the magnitude of expression changes."
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out
        genes_tbl = kc.get("genes", {}) or {}
        cols = kc.get("columns", []) or []
        try:
            syn_idx = cols.index("syn_z")
        except ValueError:
            return out

        vals = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            row = genes_tbl.get(g)
            if row is None:
                continue
            try:
                v = row[syn_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[gi] = fv

        # Impute missing with mean of finite values (or 0)
        finite = np.isfinite(vals)
        fill = float(vals[finite].mean()) if finite.any() else 0.0
        vals = np.where(finite, vals, fill)

        out[:, :, 0] = vals[None, :]
        return out
