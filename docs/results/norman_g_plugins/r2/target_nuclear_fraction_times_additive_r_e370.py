import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNuclearFractionTimesAdditiveResponseE370(Feature):
    name = "target_nuclear_fraction_times_additive_r_e370"
    version = 1
    description = ("Fraction of p's target genes with a nucleus localization flag "
                   "(protein_annotation), multiplied by additive_response.")
    rationale = ("Nuclear proteins, especially transcription-related, may directly influence "
                 "gene expression programs, leading to stronger responses; scaling the additive "
                 "baseline by the nuclear fraction of targets captures this.")
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        # additive_response baseline (composition)
        add = ctx.feature("additive_response", perts, params)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        elif add.ndim == 1:
            add = add[:, None, None]
        if add.shape[2] != 1:
            add = add.sum(axis=2, keepdims=True)

        # protein annotation table
        pa = ctx.knowledge("protein_annotation")
        genes_tbl = {}
        nuc_col = None
        if pa is not None:
            genes_tbl = pa.get("genes", {}) or {}
            cols = pa.get("columns", []) or []
            for j, c in enumerate(cols):
                if c == "nucleus":
                    nuc_col = j
                    break

        def is_nuclear(gene):
            if nuc_col is None:
                return 0.0
            vals = genes_tbl.get(gene)
            if vals is None or nuc_col >= len(vals):
                return 0.0
            v = vals[nuc_col]
            if v is None:
                return 0.0
            try:
                return 1.0 if float(v) > 0 else 0.0
            except (TypeError, ValueError):
                return 0.0

        cache = ctx.cache
        for i, p in enumerate(perts):
            key = ("nucfrac", p)
            frac = cache.get(key)
            if frac is None:
                tg = ctx.target_genes(p)
                if not tg:
                    frac = 0.0
                else:
                    vals = [is_nuclear(g) for g in tg]
                    frac = float(np.mean(vals))
                cache[key] = frac
            out[i, :, 0] = add[i, :, 0] * frac

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
