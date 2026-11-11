import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAaRFractionE233(Feature):
    name = "target_aa_r_fraction_e233"
    version = 1
    description = "Fraction of arginine residues in the protein of the targeted gene p, broadcast to all genes g."
    rationale = "Arginine-rich proteins often bind RNA and may buffer transcriptional changes upon perturbation."
    inputs = ["gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        aa_r = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if "aa_R" in cols:
                idx = cols.index("aa_R")
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        aa_r[sym] = float(v)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            val = 0.0
            for tg in tgenes:
                if tg in aa_r:
                    val = aa_r[tg]
                    break
            out[i, :, 0] = val

        out[~np.isfinite(out)] = 0.0
        return out
