import numpy as np
from genemila.features.api import Feature, register


@register
class AaIsoleucineFraction(Feature):
    name = "aa_i_fraction_e196_e197"
    version = 1
    description = "Fraction of isoleucine residues in the protein of gene g from gene_annotation."
    rationale = (
        "Isoleucine-rich proteins are often structural or membrane proteins with stable "
        "expression, leading to smaller perturbation responses."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        col = None
        vals = None
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                col = cols.index("aa_I")
            except (ValueError, AttributeError):
                col = None
            if col is not None:
                vals = ann.get("genes", {})

        if vals is not None:
            vec = np.full(n, np.nan, dtype=float)
            for i, g in enumerate(ctx.genes):
                v = vals.get(g)
                if v is None:
                    continue
                try:
                    x = v[col]
                except (IndexError, TypeError):
                    continue
                if x is None:
                    continue
                try:
                    fx = float(x)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fx):
                    vec[i] = fx
            # impute missing with mean of observed (0 if none)
            obs = np.isfinite(vec)
            if obs.any():
                fill = float(vec[obs].mean())
            else:
                fill = 0.0
            vec[~obs] = fill
        else:
            vec = np.zeros(n, dtype=float)

        out[:, :, 0] = vec[None, :]
        return out
