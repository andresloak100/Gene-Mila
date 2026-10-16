import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterGC(Feature):
    name = "target_promoter_gc_e80_e81"
    version = 1
    description = "Mean promoter GC content of the perturbation's target gene(s)."
    rationale = ("CRISPRa efficiency may depend on promoter accessibility, which "
                 "correlates with GC content; promoter GC of the target modulates "
                 "the perturbation's effect.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out
        genes_map = ann.get("genes")
        if not genes_map:
            return out
        columns = ann.get("columns", [])
        try:
            gc_idx = columns.index("gc_promoter")
        except ValueError:
            return out

        cache = ctx.cache
        gc_by_gene = cache.get("_tp_gc_by_gene")
        if gc_by_gene is None:
            gc_by_gene = {}
            for sym, vals in genes_map.items():
                if vals is None:
                    continue
                try:
                    v = vals[gc_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    gc_by_gene[sym] = fv
            cache["_tp_gc_by_gene"] = gc_by_gene

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [gc_by_gene[g] for g in targets if g in gc_by_gene]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
        return out
