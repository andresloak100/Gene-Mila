import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufTimesControlMean(Feature):
    name = "target_loeuf_times_control_mean_e163"
    version = 1
    description = "Product of control_mean of gene g and the mean LOEUF (oe_lof_upper) of p's targets."
    rationale = ("LOEUF indicates loss-of-function intolerance; genes intolerant to LoF may have "
                 "stronger effects when activated, and this modulates the baseline expression level.")
    inputs = ["control_mean"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        control_mean = np.asarray(ctx.control_mean, dtype=float)

        # Load LOEUF (oe_lof_upper) from gene_constraint prior knowledge.
        loeuf_by_gene = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                genes_map = kc.get("genes", {})
                for sym, vals in genes_map.items():
                    if vals is None:
                        continue
                    v = vals[loeuf_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf_by_gene[sym] = fv

        # Global fallback mean LOEUF (for targets lacking a value).
        if loeuf_by_gene:
            fallback = float(np.mean(list(loeuf_by_gene.values())))
        else:
            fallback = 0.0

        out = np.zeros((len(perts), n_genes, 1))
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg:
                vals = [loeuf_by_gene.get(g, fallback) for g in tg]
                mean_loeuf = float(np.mean(vals))
            else:
                mean_loeuf = fallback
            out[i, :, 0] = control_mean * mean_loeuf

        out[~np.isfinite(out)] = 0.0
        return out
