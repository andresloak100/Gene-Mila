import numpy as np
from genemila.features.api import Feature, register


@register
class AaCysteineFraction(Feature):
    name = "aa_cysteine_fraction_e119"
    version = 1
    description = "Fraction of cysteine residues in the protein of gene g from gene_annotation."
    rationale = ("Cysteine-rich proteins may be more sensitive to redox state, "
                 "affecting their expression response to perturbations.")
    inputs = ["gene_annotation"]
    params = {"missing_value": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        missing_value = float(params.get("missing_value", 0.0))
        n_genes = ctx.n_genes
        out = np.full((len(perts), n_genes, 1), missing_value, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            aa_c_idx = columns.index("aa_C")
        except ValueError:
            return out

        vals = np.full(n_genes, missing_value, dtype=float)
        for j, g in enumerate(ctx.genes):
            rec = genes.get(g)
            if rec is None:
                continue
            try:
                v = rec[aa_c_idx]
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

        out[:] = vals[None, :, None]
        return out
