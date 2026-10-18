import numpy as np
from genemila.features.api import Feature, register


@register
class AAFractionChargedE175(Feature):
    name = "aa_fraction_charged_e175"
    version = 1
    description = "Sum of fractions of charged amino acids (K, R, E, D) for gene g."
    rationale = ("Charged residues may affect protein interactions and stability, "
                 "altering how perturbations propagate.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {})
            cols = ann.get("columns", [])
            idx = {c: i for i, c in enumerate(cols)}
            aa_cols = ["aa_K", "aa_R", "aa_E", "aa_D"]
            aa_idx = [idx[c] for c in aa_cols if c in idx]

            if aa_idx:
                for gi, g in enumerate(ctx.genes):
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    s = 0.0
                    ok = True
                    for j in aa_idx:
                        if j >= len(row) or row[j] is None:
                            ok = False
                            break
                        s += float(row[j])
                    if ok:
                        vals[gi] = s

        finite = np.isfinite(vals)
        fill = np.median(vals[finite]) if finite.any() else 0.0
        vals[~finite] = fill
        vals = np.nan_to_num(vals, nan=fill, posinf=fill, neginf=fill)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
