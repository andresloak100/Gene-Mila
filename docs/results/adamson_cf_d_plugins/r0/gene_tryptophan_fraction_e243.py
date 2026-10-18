import numpy as np
from genemila.features.api import Feature, register

@register
class GeneTryptophanFractionE243(Feature):
    name = "gene_tryptophan_fraction_e243"
    version = 1
    description = "Fraction of tryptophan residues in the protein of gene g."
    rationale = ("Tryptophan content reflects protein stability and could correlate "
                 "with expression plasticity.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vec = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                w_idx = cols.index("aa_W")
            except ValueError:
                w_idx = None
            if w_idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[w_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[gi] = fv

        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.broadcast_to(vec[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
