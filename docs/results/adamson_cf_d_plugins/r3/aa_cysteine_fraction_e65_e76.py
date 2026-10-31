import numpy as np
from genemila.features.api import Feature, register

@register
class AACysteineFraction(Feature):
    name = "aa_cysteine_fraction_e65_e76"
    version = 1
    description = "Fraction of cysteine residues in the protein of gene g."
    rationale = ("Cysteine residues form disulfide bonds and are redox-sensitive; "
                 "proteins with more cysteines may respond more to oxidative stress "
                 "induced by perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        values = np.zeros(n_genes, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            genes_tbl = ka.get("genes", {}) or {}
            columns = ka.get("columns", []) or []
            try:
                aa_c_idx = columns.index("aa_C")
            except ValueError:
                aa_c_idx = None
            if aa_c_idx is not None:
                for g, row in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if row is None or aa_c_idx >= len(row):
                        continue
                    v = row[aa_c_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        values[gi] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = values[None, :]
        return out
