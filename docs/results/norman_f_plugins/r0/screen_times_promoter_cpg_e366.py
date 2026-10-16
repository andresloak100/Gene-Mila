import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenTimesPromoterCpG(Feature):
    name = "screen_times_promoter_cpg_e366"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and cpg_oe_promoter of gene g."
    rationale = "CRISPRa efficacy may depend on promoter methylation state; CpG-rich promoters may respond differently, modulating screen delta effect."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes

        # --- CpG observed/expected ratio of the promoter, per gene column ---
        cpg = np.zeros(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            if ci is not None:
                genes_map = ann.get("genes", {}) or {}
                for g, col in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    if ci < len(vals):
                        v = vals[ci]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                cpg[col] = fv

        # --- signed screen delta feature (n, n_genes, 1) ---
        sd = ctx.feature("replogle_delta_signed_e35", perts)
        sd = np.asarray(sd, dtype=np.float64)
        if sd.ndim == 2:
            sd = sd[:, :, None]

        out = sd * cpg[None, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
