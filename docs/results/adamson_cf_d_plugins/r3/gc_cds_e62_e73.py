import numpy as np
from genemila.features.api import Feature, register


@register
class GCCdsE62E73(Feature):
    name = "gc_cds_e62_e73"
    version = 1
    description = "GC content of the coding sequence of gene g from gene_annotation."
    rationale = ("High GC content stabilizes mRNA secondary structure and reduces "
                 "degradation, buffering expression changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        vec = np.full(ctx.n_genes, np.nan, dtype=float)

        if ann is not None:
            columns = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            try:
                col_idx = columns.index("gc_cds")
            except ValueError:
                col_idx = None

            if col_idx is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None or col_idx >= len(vals):
                        continue
                    v = vals[col_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[gi] = fv

        finite_mask = np.isfinite(vec)
        if finite_mask.any():
            median = float(np.median(vec[finite_mask]))
        else:
            median = 0.0
        vec = np.where(finite_mask, vec, median)

        out[:, :, 0] = vec[None, :]
        return out
