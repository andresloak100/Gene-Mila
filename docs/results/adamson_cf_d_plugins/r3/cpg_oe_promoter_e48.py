import numpy as np
from genemila.features.api import Feature, register


@register
class CpgOePromoterE48(Feature):
    name = "cpg_oe_promoter_e48"
    version = 1
    description = "Observed/expected CpG ratio in promoter for gene g."
    rationale = ("CpG-rich promoters are more accessible and responsive to regulatory "
                 "perturbations, leading to larger expression changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        values = np.full(n_genes, np.nan, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            genes = ka.get("genes", {})
            columns = ka.get("columns", [])
            try:
                col_idx = columns.index("cpg_oe_promoter")
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
                        values[gi] = fv

        finite = np.isfinite(values)
        if finite.any():
            med = float(np.median(values[finite]))
        else:
            med = 0.0
        values[~finite] = med

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = values[None, :]
        return out
