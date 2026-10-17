import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufSquaredTimesAdditive(Feature):
    name = "target_loeuf_squared_times_additive_e505"
    version = 1
    description = "Square of mean LOEUF of p's target genes, multiplied by additive_response."
    rationale = ("A nonlinear (squared) transform of target essentiality may better capture "
                 "threshold effects when modulating the additive response.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add.reshape(len(perts), n_genes)

        # LOEUF per gene
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            genes_tab = kn.get("genes", {})
            if idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_tab.get(g)
                    if vals is not None and idx < len(vals) and vals[idx] is not None:
                        try:
                            v = float(vals[idx])
                            if np.isfinite(v):
                                loeuf[gi] = v
                        except (TypeError, ValueError):
                            pass

        # fallback mean for missing LOEUF
        finite_mask = np.isfinite(loeuf)
        fallback = float(np.mean(loeuf[finite_mask])) if finite_mask.any() else 0.0

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                mean_loeuf = fallback
            else:
                vals = loeuf[tgt]
                vals = np.where(np.isfinite(vals), vals, fallback)
                mean_loeuf = float(np.mean(vals))
            out[i, :, 0] = (mean_loeuf ** 2) * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
