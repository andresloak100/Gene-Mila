import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNuclearFractionTimesAdditiveR(Feature):
    name = "target_nuclear_fraction_times_additive_r_e159"
    version = 1
    description = "Product of additive_response and the fraction of p's targets with a nuclear localization flag."
    rationale = "Nuclear proteins (TFs, chromatin regulators) may have stronger downstream effects; interacting with additive response may capture amplification."
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        pa = ctx.knowledge("protein_annotation")
        nuc_idx = None
        if pa is not None:
            cols = pa.get("columns", [])
            if "nucleus" in cols:
                nuc_idx = cols.index("nucleus")
            pa_genes = pa.get("genes", {}) or {}

        # additive_response feature: (n_perts, n_genes, dim)
        add = ctx.feature("additive_response", perts, None)
        if add.ndim == 2:
            add = add[:, :, None]
        add_dim = add.shape[2]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            frac = 0.0
            if tgenes:
                cnt = 0
                tot = 0
                for g in tgenes:
                    tot += 1
                    if nuc_idx is not None and g in pa_genes:
                        vals = pa_genes[g]
                        try:
                            v = vals[nuc_idx]
                        except (IndexError, TypeError):
                            v = None
                        if v is not None:
                            try:
                                if float(v) > 0:
                                    cnt += 1
                            except (TypeError, ValueError):
                                pass
                if tot > 0:
                    frac = cnt / tot
            # broadcast fraction over genes; sum over additive dims if >1
            base = add[i]
            if add_dim > 1:
                base = base.sum(axis=1)
            else:
                base = base[:, 0]
            out[i, :, 0] = frac * base

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
