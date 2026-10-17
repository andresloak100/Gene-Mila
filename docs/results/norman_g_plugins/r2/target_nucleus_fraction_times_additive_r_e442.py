import numpy as np
from genemila.features.api import Feature, register

@register
class TargetNucleusFractionTimesAdditiveE442(Feature):
    name = "target_nucleus_fraction_times_additive_r_e442"
    version = 1
    description = "Product of the fraction of p's target genes with a nucleus localization flag and additive_response."
    rationale = "Nuclear-localized targets may be more directly regulated by CRISPRa, amplifying the additive response."
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add2 = add[:, :, 0]
        else:
            add2 = add

        # protein_annotation: nucleus flag column
        pa = ctx.knowledge("protein_annotation")
        nucleus_col = None
        if pa is not None:
            cols = pa.get("columns", [])
            try:
                nucleus_col = cols.index("nucleus")
            except (ValueError, AttributeError):
                nucleus_col = None

        # Build nucleus flag lookup: gene -> 0/1
        nuc_flag = {}
        if pa is not None and nucleus_col is not None:
            genes_tbl = pa.get("genes", {})
            for g, vals in genes_tbl.items():
                if vals is None:
                    continue
                try:
                    v = vals[nucleus_col]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    nuc_flag[g] = 1.0 if float(v) != 0.0 else 0.0
                except (TypeError, ValueError):
                    continue

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                frac = 0.0
            else:
                vals = [nuc_flag.get(g, 0.0) for g in tg]
                frac = float(np.mean(vals))
            out[i, :, 0] = frac * add2[i, :]

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
