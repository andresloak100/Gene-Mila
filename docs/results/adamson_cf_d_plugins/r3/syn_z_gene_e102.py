import numpy as np
from genemila.features.api import Feature, register

@register
class SynZGeneE102(Feature):
    name = "syn_z_gene_e102"
    version = 1
    description = "Per-gene synonymous constraint (syn_z), z-scored across genes, imputed with 0."
    rationale = "Synonymous constraint may indicate selection for mRNA stability or translation efficiency, buffering expression changes."
    inputs = ["knowledge:gene_constraint"]
    params = {"impute": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        impute = float(params.get("impute", 0.0))
        kc = ctx.knowledge("gene_constraint")
        n = ctx.n_genes

        raw = np.full(n, np.nan, dtype=np.float64)
        if kc is not None:
            cols = kc.get("columns", [])
            genes = kc.get("genes", {})
            if "syn_z" in cols:
                j = cols.index("syn_z")
                for gi, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is not None and j < len(vals):
                        v = vals[j]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                fv = np.nan
                            if np.isfinite(fv):
                                raw[gi] = fv

        mask = np.isfinite(raw)
        filled = raw.copy()
        filled[~mask] = impute

        # z-score using only observed values for mean/std (more stable)
        if mask.sum() > 1:
            obs = raw[mask]
            mu = obs.mean()
            sd = obs.std()
            if sd > 0:
                z = (filled - mu) / sd
            else:
                z = filled - mu
        else:
            z = np.zeros(n, dtype=np.float64)

        z = np.where(np.isfinite(z), z, 0.0)
        out = np.broadcast_to(z[None, :, None], (len(perts), n, 1)).copy()
        return out
