import numpy as np
from genemila.features.api import Feature, register


@register
class AaDFractionGeneE146(Feature):
    name = "aa_d_fraction_gene_e146"
    version = 1
    description = "Fraction of aspartate (aa_D) residues in gene g's protein, from gene_annotation."
    rationale = ("Aspartate-rich proteins may be less responsive to perturbations due to "
                 "structural or interaction properties (disorder, stability); aa_D provides "
                 "a direct gene-side continuous feature.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes = ann.get("genes", {}) or {}
        cols = ann.get("columns", []) or []
        try:
            aa_d_idx = cols.index("aa_D")
        except ValueError:
            return out

        vals = np.full(n, np.nan, dtype=float)
        for j, g in enumerate(ctx.genes):
            rec = genes.get(g)
            if rec is None:
                continue
            try:
                v = rec[aa_d_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[j] = fv

        finite = np.isfinite(vals)
        if finite.any():
            fill = float(vals[finite].mean())
        else:
            fill = 0.0
        vals = np.where(finite, vals, fill)

        out[:, :, 0] = vals[None, :]
        return out
