import numpy as np
from genemila.features.api import Feature, register


@register
class NearestTssKbE117(Feature):
    name = "nearest_tss_kb_e117"
    version = 1
    description = "Distance to the nearest TSS for gene g from gene_annotation."
    rationale = ("Genes isolated from other TSS may have less regulatory interference "
                 "and more stable expression, so they show attenuated responses.")
    inputs = ["gene_annotation"]
    params = {"missing_value": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ka = ctx.knowledge("gene_annotation")
        vals = np.full(n_genes, np.nan, dtype=float)

        if ka is not None:
            genes = ka.get("genes", {}) or {}
            columns = ka.get("columns", []) or []
            try:
                col_idx = columns.index("nearest_tss_kb")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g, row in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
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
                        vals[gi] = fv

        finite_mask = np.isfinite(vals)
        if finite_mask.any():
            fill = float(np.median(vals[finite_mask]))
        else:
            fill = 0.0

        vals = np.where(finite_mask, vals, fill)
        out[:, :, 0] = vals[None, :]
        return out
