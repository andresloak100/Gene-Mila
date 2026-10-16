import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenTimesPromoterCpG(Feature):
    name = "screen_times_promoter_cpg_e367"
    version = 1
    description = "Elementwise product of sign-flipped Replogle screen delta and promoter CpG o/e ratio of gene g."
    rationale = "CRISPRa efficacy may depend on promoter CpG content, modulating the external screen delta effect."
    inputs = ["replogle_delta_signed_e35", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # CpG o/e promoter per gene in bundle gene order
        cpg = np.zeros(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                cpg_idx = columns.index("cpg_oe_promoter")
            except ValueError:
                cpg_idx = None
            if cpg_idx is not None:
                for j, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is not None and len(vals) > cpg_idx:
                        v = vals[cpg_idx]
                        if v is not None and np.isfinite(v):
                            cpg[j] = float(v)

        # Reuse the signed screen delta feature
        screen = ctx.feature("replogle_delta_signed_e35", perts)
        screen = np.asarray(screen, dtype=np.float64)
        if screen.ndim == 2:
            screen = screen[:, :, None]
        if screen.shape[0] != n_perts or screen.shape[1] != n_genes:
            screen = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        out = screen * cpg[None, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
