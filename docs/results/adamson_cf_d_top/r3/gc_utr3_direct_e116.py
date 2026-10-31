import numpy as np
from genemila.features.api import Feature, register


@register
class GcUtr3DirectE116(Feature):
    name = "gc_utr3_direct_e116"
    version = 1
    description = "Numeric feature: gc_utr3 value from gene_annotation for gene g."
    rationale = (
        "High GC content in the 3' UTR can affect mRNA stability and translation "
        "efficiency, potentially buffering expression changes upon perturbation."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if not ka:
            return out

        genes_tbl = ka.get("genes", {}) or {}
        columns = ka.get("columns", []) or []
        try:
            col_idx = columns.index("gc_utr3")
        except ValueError:
            return out

        # Precompute per-gene value vector once.
        if "_gc_utr3_vec" not in ctx.cache:
            vec = np.full(ctx.n_genes, np.nan, dtype=float)
            for i, g in enumerate(ctx.genes):
                row = genes_tbl.get(g)
                if row is None:
                    continue
                if col_idx >= len(row):
                    continue
                v = row[col_idx]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vec[i] = fv
            ctx.cache["_gc_utr3_vec"] = vec

        vec = ctx.cache["_gc_utr3_vec"]
        # Replace missing with column mean (finite fallback 0.0).
        finite = np.isfinite(vec)
        fill = float(vec[finite].mean()) if finite.any() else 0.0
        vec_filled = np.where(finite, vec, fill)

        for i in range(len(perts)):
            out[i, :, 0] = vec_filled
        return out
