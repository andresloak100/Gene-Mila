import numpy as np
from genemila.features.api import Feature, register


@register
class NUpstreamAtg(Feature):
    name = "n_upstream_atg_e60_e71"
    version = 1
    description = "Number of upstream ATG codons in the 5' UTR of gene g from gene_annotation."
    rationale = ("Upstream ATGs reduce translation initiation efficiency, especially under "
                 "stress, altering protein output and downstream expression changes.")
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        values = np.full(ctx.n_genes, np.nan, dtype=float)

        if ann is not None:
            cols = ann.get("columns", [])
            genes_map = ann.get("genes", {}) or {}
            try:
                col_idx = cols.index("n_upstream_atg")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    v = vals[col_idx] if col_idx < len(vals) else None
                    if v is not None:
                        try:
                            values[gi] = float(v)
                        except (TypeError, ValueError):
                            pass

        finite = np.isfinite(values)
        if finite.any():
            fill = float(np.median(values[finite]))
        else:
            fill = 0.0
        values[~finite] = fill

        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = values[None, :]
        return out
