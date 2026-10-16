import numpy as np
from genemila.features.api import Feature, register

@register
class ReplogleAdditiveXTargetPromoterCpG_E590(Feature):
    name = "replogle_additive_x_target_promoter_cpg__e590"
    version = 1
    description = "Product of sign-corrected Replogle additive response and log(1+mean CpG promoter content of targets)."
    rationale = "Epigenetic promoter context may modulate the effect of CRISPRa perturbations, and log-normalisation compresses the CpG range."
    inputs = ["replogle2022_k562", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes_ann = ann.get("genes", {})
        cols = ann.get("columns", [])
        try:
            cpg_idx = cols.index("cpg_oe_promoter")
        except ValueError:
            return out
        cpg_map = {}
        for g, vals in genes_ann.items():
            if vals is not None and len(vals) > cpg_idx:
                v = vals[cpg_idx]
                if v is not None:
                    cpg_map[g] = float(v)
        rep = ctx.knowledge("replogle2022_k562")
        sign = -1.0
        rep_perts = {}
        if rep is not None:
            sign = float(rep.get("sign", -1.0))
            rep_perts = rep.get("perts", {}) or {}
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [cpg_map[g] for g in tg if g in cpg_map]
            if len(vals) > 0:
                mean_cpg = float(np.mean(vals))
                f = np.log1p(max(mean_cpg, 0.0))
            else:
                f = 0.0
            acc = np.zeros(n)
            for g in tg:
                row = rep_perts.get(g)
                if row is None:
                    continue
                d = row.get("delta") if isinstance(row, dict) else None
                if d is None:
                    continue
                arr = np.asarray(d, dtype=float)
                if arr.shape[0] != n:
                    continue
                acc += sign * np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = acc * f
        return out
