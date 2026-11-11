import numpy as np
from genemila.features.api import Feature, register

@register
class TargetNUpstreamAtgInteractionE85(Feature):
    name = "target_n_upstream_atg_interaction_e85"
    version = 1
    description = ("Product of the target gene's n_upstream_atg (gene_annotation) and "
                   "gene g's control_mean expression.")
    rationale = ("Perturbing genes with many upstream ATGs may alter translation "
                 "regulation globally, affecting highly expressed/translated genes.")
    inputs = ["control_mean", "n_upstream_atg"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        atg_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if "n_upstream_atg" in cols:
                idx = cols.index("n_upstream_atg")
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        atg_map[sym] = float(v)
                    except (TypeError, ValueError):
                        continue

        cmean = np.asarray(ctx.control_mean, dtype=float)
        cmean = np.nan_to_num(cmean, nan=0.0, posinf=0.0, neginf=0.0)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            val = 0.0
            for t in tg:
                if t in atg_map:
                    val += atg_map[t]
            if tg and val == 0.0 and not any(t in atg_map for t in tg):
                val = 0.0
            out[i, :, 0] = val * cmean

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
