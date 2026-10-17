import numpy as np
from genemila.features.api import Feature, register

@register
class TargetGCCDS(Feature):
    name = "target_gc_cds_e188"
    version = 1
    description = "GC content of the coding sequence of the perturbation target gene."
    rationale = "GC content influences RNA stability and translation efficiency, potentially leading to larger expression changes."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ann is not None:
            genes = ann.get("genes", {})
            for sym, vals in genes.items():
                if vals is not None and len(vals) > 8 and vals[8] is not None:
                    try:
                        gc_map[sym] = float(vals[8])
                    except (TypeError, ValueError):
                        pass
        if gc_map:
            fill = float(np.median(list(gc_map.values())))
        else:
            fill = 0.0
        target_vals = []
        for p in perts:
            tg = ctx.target_genes(p)
            v = fill
            if tg:
                v = gc_map.get(tg[0], fill)
            target_vals.append(v)
        out[:, :, 0] = np.array(target_vals, dtype=float)[:, None]
        return out
