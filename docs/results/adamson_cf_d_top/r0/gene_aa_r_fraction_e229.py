import numpy as np
from genemila.features.api import Feature, register

@register
class GeneAARFractionE229(Feature):
    name = "gene_aa_r_fraction_e229"
    version = 1
    description = "Fraction of arginine residues (aa_R) in the protein of gene g."
    rationale = ("Arginine-rich proteins are often RNA-binding and may be under tighter "
                 "regulatory control, reducing expression variability under perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vals = np.zeros(n, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                idx = columns.index("aa_R")
            except ValueError:
                idx = None
            if idx is not None:
                for g, col in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or col is None:
                        continue
                    try:
                        v = col[idx]
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

        out = np.broadcast_to(vals[None, :, None], (len(perts), n, 1)).copy()
        return out
