import numpy as np
from genemila.features.api import Feature, register


@register
class AaQFractionE192E193(Feature):
    name = "aa_q_fraction_e192_e193"
    version = 1
    description = "Fraction of glutamine residues in the protein of gene g from gene_annotation amino-acid fractions."
    rationale = "Glutamine-rich proteins participate in stress responses and may show larger expression changes upon perturbation."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        genes = ann.get("genes", {})
        try:
            q_idx = columns.index("aa_Q")
        except ValueError:
            return out

        vec = np.zeros(n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            v = vals[q_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[j] = fv

        out[:, :, 0] = vec[None, :]
        return out
