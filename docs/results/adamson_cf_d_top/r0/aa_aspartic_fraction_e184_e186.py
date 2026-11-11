import numpy as np
from genemila.features.api import Feature, register

@register
class AsparticAcidFraction(Feature):
    name = "aa_aspartic_fraction_e184_e186"
    version = 1
    description = "Fraction of aspartic acid (aa_D) in the protein sequence of gene g."
    rationale = ("Aspartic acid residues may stabilize protein structure, reducing "
                 "expression variability upon perturbation; genes with high aspartic "
                 "acid fraction may show smaller expression changes after perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        frac = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                aa_D_idx = columns.index("aa_D")
            except ValueError:
                aa_D_idx = None
            if aa_D_idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None:
                        continue
                    if aa_D_idx >= len(vals):
                        continue
                    v = vals[aa_D_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        frac[gi] = fv

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = frac[np.newaxis, :]
        out[~np.isfinite(out)] = 0.0
        return out
