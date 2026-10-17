import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGCContentXIsTarget(Feature):
    name = "target_gc_content_x_is_target_e284"
    version = 1
    description = "Product of target gene's GC content (from gene_annotation) and is_target indicator."
    rationale = (
        "GC content influences gene regulation and mRNA stability; the target gene's GC "
        "content may modulate the magnitude/direction of downstream changes specifically "
        "at the targeted gene, an effect not captured by a plain is_target indicator."
    )
    inputs = ["gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            # Prefer gc_cds, fall back to gc_promoter
            gc_col = None
            for cand in ("gc_cds", "gc_promoter", "gc_utr3"):
                if cand in cols:
                    gc_col = cols.index(cand)
                    break
            genes_ann = ann.get("genes", {}) or {}
            if gc_col is not None:
                for sym, vals in genes_ann.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[gc_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc_map[sym] = fv

        # Cache per-perturbation target GC values
        cache = ctx.cache
        key = "_gc284_target_gc"
        if key not in cache:
            cache[key] = {}

        for i, p in enumerate(perts):
            if p in cache[key]:
                tgc = cache[key][p]
            else:
                tgc = None
                tgenes = ctx.target_genes(p)
                vals = [gc_map[g] for g in tgenes if g in gc_map]
                if vals:
                    tgc = float(np.mean(vals))
                cache[key][p] = tgc

            if tgc is None:
                continue

            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            idx = np.asarray([j for j in t_idx if 0 <= j < n_genes], dtype=int)
            if idx.size == 0:
                continue
            out[i, idx, 0] = tgc

        out[~np.isfinite(out)] = 0.0
        return out
