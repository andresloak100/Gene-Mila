import numpy as np
from genemila.features.api import Feature, register


@register
class CpgOePromoterE61(Feature):
    name = "cpg_oe_promoter_e61"
    version = 1
    description = "Observed/expected CpG ratio in the promoter region of gene g from gene_annotation."
    rationale = ("CpG-rich promoters mark housekeeping genes with stable expression, "
                 "potentially reducing perturbation-induced changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if not ka:
            return out

        genes_tbl = ka.get("genes") or {}
        columns = ka.get("columns") or []
        try:
            col_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            return out

        # Build per-gene value vector aligned to ctx.genes
        vals = np.full(ctx.n_genes, np.nan, dtype=float)
        for i, g in enumerate(ctx.genes):
            row = genes_tbl.get(g)
            if row is None:
                continue
            try:
                v = row[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[i] = fv

        # Standardise across genes (z-score), impute missing with 0 (mean)
        finite = np.isfinite(vals)
        if finite.any():
            mu = vals[finite].mean()
            sd = vals[finite].std()
            z = np.where(finite, vals, mu)
            if sd > 0:
                z = (z - mu) / sd
            else:
                z = np.zeros_like(z)
        else:
            z = np.zeros(ctx.n_genes, dtype=float)

        z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)

        for i in range(len(perts)):
            out[i, :, 0] = z

        return out
