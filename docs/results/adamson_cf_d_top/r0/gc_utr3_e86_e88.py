import numpy as np
from genemila.features.api import Feature, register


@register
class GCUTR3(Feature):
    name = "gc_utr3_e86_e88"
    version = 1
    description = "GC content of the 3' UTR of gene g from gene_annotation."
    rationale = ("GC-rich 3' UTRs stabilize mRNAs and increase miRNA regulation, "
                 "buffering expression changes after perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = list(columns).index("gc_utr3")
            except ValueError:
                col_idx = -1
            if col_idx >= 0:
                for g, gi in ctx.gene_index.items():
                    row = genes.get(g)
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
                        vals[gi] = fv

        # Fallback: use control mean as a neutral value where missing
        missing = ~np.isfinite(vals)
        if missing.any():
            vals[missing] = 0.0

        out = np.broadcast_to(vals[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
