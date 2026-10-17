import numpy as np
from genemila.features.api import Feature, register

@register
class TargetUpstreamAtgTimesAdditive(Feature):
    name = "target_upstream_atg_times_additive_e612"
    version = 1
    description = "Mean n_upstream_atg of p's target genes multiplied by additive_response."
    rationale = ("Higher upstream ATG count may indicate more complex regulation and stronger "
                 "response to CRISPRa; scaling the additive baseline by mean target upstream ATG "
                 "captures this per-perturbation modulation.")
    inputs = ["control_cells", "train_delta", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Load annotation once and build per-gene n_upstream_atg vector.
        ann = ctx.knowledge("gene_annotation")
        atg_vec = np.zeros(n_genes, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            if "n_upstream_atg" in cols:
                j = cols.index("n_upstream_atg")
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    v = vals[j]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            atg_vec[gi] = fv

        for i, p in enumerate(perts):
            # Additive baseline: sum over targets of per-gene mean delta (leaving p out).
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)  # (n_genes,)
            tgt = ctx.target_indices(p)
            if len(tgt) > 0:
                additive = add[tgt].sum()
            else:
                additive = 0.0
            # Mean upstream ATG over targets.
            if len(tgt) > 0:
                mean_atg = atg_vec[tgt].mean()
            else:
                mean_atg = 0.0
            out[i, :, 0] = mean_atg * additive

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
