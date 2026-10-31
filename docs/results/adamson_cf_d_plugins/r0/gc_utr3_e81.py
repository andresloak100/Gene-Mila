import numpy as np
from genemila.features.api import Feature, register

@register
class GcUtr3E81(Feature):
    name = "gc_utr3_e81"
    version = 1
    description = "GC content of the 3' UTR for gene g (imputed with median)."
    rationale = ("GC-rich 3' UTRs stabilize mRNA and reduce expression changes, "
                 "buffering perturbation responses.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vals = np.full(n, np.nan, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            genes = ka.get("genes", {}) or {}
            columns = ka.get("columns", []) or []
            try:
                idx = list(columns).index("gc_utr3")
            except ValueError:
                idx = None
            if idx is not None:
                for g, row in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = row[idx]
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

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
        else:
            med = 0.0
        vals[~finite] = med

        out = np.empty((len(perts), n, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
