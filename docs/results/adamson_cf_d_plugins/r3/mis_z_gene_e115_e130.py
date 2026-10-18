import numpy as np
from genemila.features.api import Feature, register

@register
class MisZGeneE115E130(Feature):
    name = "mis_z_gene_e115_e130"
    version = 1
    description = "Missense z-score for gene g from gnomAD constraint data."
    rationale = ("High missense z-score indicates strong purifying selection on missense "
                 "variants, implying functional importance; perturbing such genes may elicit "
                 "larger expression responses.")
    inputs = ["gene_constraint"]
    params = {"impute": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                mi = cols.index("mis_z")
            except ValueError:
                mi = None
            if mi is not None:
                for gi, g in enumerate(ctx.genes):
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[mi]
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

        mask = np.isfinite(vals)
        if mask.any():
            fill = np.median(vals[mask])
        else:
            fill = 0.0
        vals[~mask] = fill

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
