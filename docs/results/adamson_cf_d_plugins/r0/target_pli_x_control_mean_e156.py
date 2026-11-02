import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPliXControlMeanE156(Feature):
    name = "target_pli_x_control_mean_e156"
    version = 1
    description = "Product of target p's pLI and gene g's control_mean."
    rationale = ("Perturbing essential (LoF-intolerant) genes may have larger effects on "
                 "highly expressed genes; interaction of target pLI with control_mean.")
    inputs = ["control_mean", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load pLI from gene_constraint
        gc = ctx.knowledge("gene_constraint")
        pli = np.zeros(n_genes, dtype=float)
        if gc is not None:
            genes_map = gc.get("genes", {})
            cols = gc.get("columns", [])
            try:
                pli_idx = list(cols).index("pLI")
            except ValueError:
                pli_idx = None
            if pli_idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is not None and len(vals) > pli_idx:
                        v = vals[pli_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    pli[gi] = fv
                            except (TypeError, ValueError):
                                pass

        cm = np.asarray(ctx.control_mean, dtype=float)
        cm = np.where(np.isfinite(cm), cm, 0.0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                p_pli = float(np.mean(pli[tgt_idx]))
            else:
                p_pli = 0.0
            if not np.isfinite(p_pli):
                p_pli = 0.0
            out[i, :, 0] = p_pli * cm

        out = np.where(np.isfinite(out), out, 0.0)
        return out
