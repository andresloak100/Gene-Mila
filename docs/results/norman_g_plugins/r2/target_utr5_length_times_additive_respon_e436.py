import numpy as np
from genemila.features.api import Feature, register

@register
class TargetUtr5LengthTimesAdditiveResponse(Feature):
    name = "target_utr5_length_times_additive_respon_e436"
    version = 1
    description = "Product of the mean 5' UTR length of p's target genes and additive_response."
    rationale = ("5' UTR length influences translation initiation and may affect the efficiency "
                 "of CRISPRa-driven upregulation, modulating the additive response.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # additive_response feature: (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add.reshape(len(perts), ctx.n_genes)

        # Build per-gene utr5_length array aligned to ctx.genes
        utr5 = np.full(ctx.n_genes, np.nan)
        if ann is not None and isinstance(ann, dict):
            genes_tab = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("utr5_length")
            except ValueError:
                idx = None
            if idx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes_tab.get(g)
                    if vals is not None and idx < len(vals):
                        v = vals[idx]
                        if v is not None:
                            try:
                                utr5[col] = float(v)
                            except (TypeError, ValueError):
                                pass

        finite_mask = np.isfinite(utr5)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                mean_utr5 = 0.0
            else:
                vals = utr5[t_idx]
                vals = vals[np.isfinite(vals)]
                mean_utr5 = float(vals.mean()) if vals.size > 0 else 0.0
            out[i, :, 0] = mean_utr5 * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
