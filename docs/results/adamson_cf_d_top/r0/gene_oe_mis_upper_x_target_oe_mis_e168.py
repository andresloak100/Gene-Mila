import numpy as np
from genemila.features.api import Feature, register


@register
class GeneOeMisUpperXTargetOeMisE168(Feature):
    name = "gene_oe_mis_upper_x_target_oe_mis_e168"
    version = 1
    description = ("Product of inverted gene oe_mis_upper and inverted target oe_mis_upper "
                   "(low oe_mis_upper = constrained).")
    rationale = ("Missense constraint reflects protein-level sensitivity; the interaction "
                 "captures shared proteostasis response between target and gene.")
    inputs = ["knowledge:gene_constraint", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))
        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out
        cols = kc.get("columns", [])
        try:
            ci = cols.index("oe_mis_upper")
        except ValueError:
            return out
        gdata = kc.get("genes", {})

        # gene-level inverted constraint
        gene_val = np.full(n, np.nan, dtype=float)
        for i, g in enumerate(ctx.genes):
            vals = gdata.get(g)
            if vals is None or ci >= len(vals):
                continue
            v = vals[ci]
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            gene_val[i] = 1.0 / (1.0 + v)

        # fill missing gene values with neutral 1.0
        gene_val = np.where(np.isfinite(gene_val), gene_val, 1.0)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                t_val = 1.0
            else:
                t_val = float(np.mean(gene_val[t_idx]))
            out[i, :, 0] = gene_val * t_val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
