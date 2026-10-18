import numpy as np
from genemila.features.api import Feature, register

@register
class GeneMethionineFractionE241(Feature):
    name = "gene_methionine_fraction_e241"
    version = 1
    description = "Fraction of methionine residues in the protein of gene g from gene_annotation."
    rationale = ("Methionine content correlates with protein stability and may mark genes whose "
                 "expression is co-regulated with globin genes under stress.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        vals = np.zeros(ctx.n_genes, dtype=float)
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                idx = cols.index("aa_M")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    row = genes.get(g)
                    if row is None:
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

        out[:, :, 0] = vals[None, :]
        return out
