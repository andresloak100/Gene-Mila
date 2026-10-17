import numpy as np
from genemila.features.api import Feature, register


@register
class MeanTargetPromoterGC(Feature):
    name = "mean_target_promoter_gc_e295"
    version = 1
    description = "Mean gc_promoter value across the target genes of perturbation p."
    rationale = ("CRISPRa efficiency depends on promoter accessibility and GC content; "
                 "target promoter GC may modulate the strength of downstream responses.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1))

        if ann is None:
            return out

        genes_map = ann.get("genes") if isinstance(ann, dict) else None
        columns = ann.get("columns") if isinstance(ann, dict) else None
        if not genes_map or not columns:
            return out

        try:
            gc_idx = columns.index("gc_promoter")
        except (ValueError, AttributeError):
            return out

        cache = ctx.cache
        key = "__mtpgc_e295__"
        if key not in cache:
            vals = {}
            for g, row in genes_map.items():
                try:
                    v = row[gc_idx]
                    if v is None:
                        continue
                    fv = float(v)
                    if np.isfinite(fv):
                        vals[g] = fv
                except (TypeError, IndexError, ValueError):
                    continue
            cache[key] = vals
        vals = cache[key]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            acc = []
            for g in tg:
                v = vals.get(g)
                if v is not None:
                    acc.append(v)
            if acc:
                out[i, :, 0] = float(np.mean(acc))
        return out
