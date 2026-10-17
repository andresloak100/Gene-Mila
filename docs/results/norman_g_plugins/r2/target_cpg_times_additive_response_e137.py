import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgTimesAdditiveResponseE137(Feature):
    name = "target_cpg_times_additive_response_e137"
    version = 1
    description = ("Product of the mean CpG island promoter score (cpg_oe_promoter) "
                   "of p's target genes and additive_response.")
    rationale = ("CRISPRa efficiency may depend on promoter CpG content; weighting the "
                 "additive response by target CpG status refines predictions.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def _cpg_scores(self, ctx):
        cache = ctx.cache
        key = "_e137_cpg_oe_promoter"
        if key in cache:
            return cache[key]
        scores = np.full(ctx.n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            genes = ann.get("genes", {})
            if ci is not None:
                for g, vals in genes.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None:
                        continue
                    try:
                        v = vals[ci]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        scores[idx] = fv
        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        cpg = self._cpg_scores(ctx)
        # fallback: use column mean where missing (neutral)
        finite = np.isfinite(cpg)
        fill = float(cpg[finite].mean()) if finite.any() else 0.0
        cpg_filled = np.where(finite, cpg, fill)

        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]
        add = np.nan_to_num(add, nan=0.0, posinf=0.0, neginf=0.0)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                mean_cpg = fill
            else:
                mean_cpg = float(cpg_filled[tidx].mean())
            out[i, :, 0] = mean_cpg * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
