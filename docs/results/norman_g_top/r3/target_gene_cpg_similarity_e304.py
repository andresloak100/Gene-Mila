import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneCpgSimilarityE304(Feature):
    name = "target_gene_cpg_similarity_e304"
    version = 1
    description = ("Absolute difference between cpg_oe_promoter of gene g and the mean "
                   "cpg_oe_promoter of the target gene(s) of perturbation p.")
    rationale = ("Genes with similar promoter CpG island overlap to the target gene may be "
                 "co-regulated and respond similarly to the perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def _gene_values(self, ctx):
        key = "_e304_cpg_values"
        if key in ctx.cache:
            return ctx.cache[key]
        vals = np.full(ctx.n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                idx = cols.index("cpg_oe_promoter")
            except ValueError:
                idx = None
            if idx is not None:
                for g, gi in ctx.gene_index.items():
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv
        # Fallback: fill missing with median of observed (or 0 if none)
        finite = np.isfinite(vals)
        if finite.any():
            fill = float(np.median(vals[finite]))
        else:
            fill = 0.0
        vals[~finite] = fill
        ctx.cache[key] = vals
        return vals

    def compute(self, ctx, perts, params):
        vals = self._gene_values(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if t_idx:
                tvals = vals[np.asarray(t_idx, dtype=int)]
                tmean = float(np.mean(tvals))
            else:
                tmean = float(np.mean(vals))
            out[i, :, 0] = np.abs(vals - tmean)
        out[~np.isfinite(out)] = 0.0
        return out
