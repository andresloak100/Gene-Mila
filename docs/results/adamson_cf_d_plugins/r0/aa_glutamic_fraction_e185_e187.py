import numpy as np
from genemila.features.api import Feature, register


@register
class AAGlutamicFraction(Feature):
    name = "aa_glutamic_fraction_e185_e187"
    version = 1
    description = "Fraction of glutamic acid (aa_E) in the protein sequence of gene g."
    rationale = ("Glutamic acid residues may stabilize protein structure, reducing "
                 "expression variability upon perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            genes_tbl = ka.get("genes", {}) or {}
            columns = ka.get("columns", []) or []
            try:
                col_idx = columns.index("aa_E")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for j, g in enumerate(ctx.genes):
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    if col_idx >= len(row):
                        continue
                    v = row[col_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[j] = fv

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
