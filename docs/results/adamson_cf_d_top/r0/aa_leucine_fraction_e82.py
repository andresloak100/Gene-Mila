import numpy as np
from genemila.features.api import Feature, register

@register
class AALeucineFractionE82(Feature):
    name = "aa_leucine_fraction_e82"
    version = 1
    description = "Fraction of leucine (aa_L) in the protein sequence of gene g."
    rationale = ("Leucine-rich proteins are more stable and dampen expression changes; "
                 "high leucine content may correlate with protein stability and buffered "
                 "expression responses after perturbation.")
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = columns.index("aa_L")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g, row in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if row is None or col_idx >= len(row):
                        continue
                    v = row[col_idx]
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

        out = np.broadcast_to(vals[None, :, None], (len(perts), n_genes, 1)).copy()
        out[~np.isfinite(out)] = med
        return out
