import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpGIslandOverlap(Feature):
    name = "target_cpg_island_overlap_e125_e139"
    version = 1
    description = "Mean CpG-island-overlap score (cpg_oe_promoter) of the target genes of each perturbation."
    rationale = "Genes whose promoters overlap CpG islands may be more responsive to CRISPRa; encode a graded score per target."
    inputs = ["gene_annotation", "target_genes"]
    params = {"default": 0.0}
    dim = 1

    def _cpg_scores(self, ctx, params):
        cache = ctx.cache
        key = ("cpg_scores", float(params.get("default", 0.0)))
        if key in cache:
            return cache[key]
        default = float(params.get("default", 0.0))
        scores = np.full(ctx.n_genes, default, dtype=np.float64)
        has = np.zeros(ctx.n_genes, dtype=bool)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            ci = None
            for cand in ("cpg_oe_promoter", "cpg_island_overlap", "cpg_oe"):
                if cand in cols:
                    ci = cols.index(cand)
                    break
            if ci is not None:
                for g, idx in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        scores[idx] = fv
                        has[idx] = True
        cache[key] = (scores, has)
        return scores, has

    def compute(self, ctx, perts, params):
        scores, has = self._cpg_scores(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            idxs = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if not idxs:
                continue
            vals = scores[idxs]
            out[i, :, 0] = float(np.mean(vals))
        return out
