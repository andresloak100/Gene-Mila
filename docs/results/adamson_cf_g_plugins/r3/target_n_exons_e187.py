import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNExonsE187(Feature):
    name = "target_n_exons_e187"
    version = 1
    description = "Number of exons of the perturbation target gene (median-filled)."
    rationale = (
        "Exon count is a proxy for splicing complexity; perturbing genes with many "
        "exons may disrupt alternative splicing and produce larger expression changes."
    )
    inputs = ["target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        genes_table = {}
        if isinstance(ann, dict):
            genes_table = ann.get("genes", {}) or {}

        # column index 2 = n_exons
        exon_idx = 2

        # collect values across annotation for median fill
        all_vals = []
        for sym, vals in genes_table.items():
            if vals is None:
                continue
            try:
                v = vals[exon_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                all_vals.append(fv)

        if all_vals:
            median_val = float(np.median(np.array(all_vals, dtype=float)))
        else:
            median_val = 0.0

        # per-perturbation target exon count
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            val = median_val
            if tg:
                sym = tg[0]
                vals = genes_table.get(sym)
                if vals is not None:
                    try:
                        v = vals[exon_idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                val = fv
                        except (TypeError, ValueError):
                            pass
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
