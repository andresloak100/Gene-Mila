import numpy as np
from genemila.features.api import Feature, register

@register
class TargetAaKFraction(Feature):
    name = "target_aa_k_fraction_e234"
    version = 1
    description = "Fraction of lysine residues in the protein of the targeted gene p."
    rationale = ("Lysine-rich proteins are often involved in chromatin regulation, "
                 "so perturbing them may cause larger expression changes.")
    inputs = ["control_cells", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        aa_k = {}
        if isinstance(ann, dict):
            genes_tbl = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                k_idx = cols.index("aa_K")
            except (ValueError, AttributeError):
                k_idx = None
            if k_idx is not None and isinstance(genes_tbl, dict):
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[k_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    aa_k[sym] = float(v)

        for i, p in enumerate(perts):
            val = 0.0
            tgenes = ctx.target_genes(p)
            if tgenes:
                vals = [aa_k[g] for g in tgenes if g in aa_k]
                if vals:
                    val = float(np.mean(vals))
            out[i, :, 0] = val

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
