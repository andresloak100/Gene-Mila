import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNuclearFractionTimesAdditiveR(Feature):
    name = "target_nuclear_fraction_times_additive_r_e148"
    version = 1
    description = ("Mean nuclear-localization flag of the perturbation's target genes "
                   "multiplied by the additive_response feature.")
    rationale = ("Nuclear proteins, especially transcription factors, may have broader "
                 "regulatory impacts; interacting the target nuclear fraction with the "
                 "additive response can modulate response magnitude.")
    inputs = ["protein_annotation", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # additive_response feature values (n_perts, n_genes, 1)
        try:
            add = ctx.feature("additive_response", perts)
        except Exception:
            add = None
        if add is not None:
            add = np.asarray(add, dtype=float)
            if add.ndim == 2:
                add = add[:, :, None]

        pa = ctx.knowledge("protein_annotation")
        nucleus_col = None
        gene_vals = {}
        if pa is not None:
            cols = pa.get("columns", [])
            if "nucleus" in cols:
                nucleus_col = cols.index("nucleus")
            genes_tbl = pa.get("genes", {}) or {}
            for g, vals in genes_tbl.items():
                if nucleus_col is not None and vals is not None and len(vals) > nucleus_col:
                    v = vals[nucleus_col]
                    gene_vals[g] = 0.0 if v is None else float(v)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if tgenes:
                vals = [gene_vals.get(g, 0.0) for g in tgenes]
                nuc_frac = float(np.mean(vals)) if vals else 0.0
            else:
                nuc_frac = 0.0
            if add is not None:
                out[i, :, 0] = nuc_frac * add[i, :, 0]
            else:
                out[i, :, 0] = 0.0

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
