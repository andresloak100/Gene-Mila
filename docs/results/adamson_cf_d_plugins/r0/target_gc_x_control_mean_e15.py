import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGCxControlMeanE15(Feature):
    name = "target_gc_x_control_mean_e15"
    version = 1
    description = "Product of target gene's gc_promoter (fallback gc_cds) and control_mean of gene g."
    rationale = "GC-rich promoters may amplify transcriptional responses in highly expressed genes."
    inputs = ["control_mean", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        cm = np.asarray(ctx.control_mean, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        genes_tbl = {}
        cols = []
        if isinstance(ann, dict):
            genes_tbl = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []

        # figure out indices for gc_promoter and gc_cds
        def col_idx(name):
            try:
                return cols.index(name)
            except (ValueError, AttributeError):
                return None

        i_prom = col_idx("gc_promoter")
        i_cds = col_idx("gc_cds")

        def gc_of(sym):
            vals = genes_tbl.get(sym)
            if vals is None:
                return 0.0
            if i_prom is not None and i_prom < len(vals) and vals[i_prom] is not None:
                try:
                    return float(vals[i_prom])
                except (TypeError, ValueError):
                    pass
            if i_cds is not None and i_cds < len(vals) and vals[i_cds] is not None:
                try:
                    return float(vals[i_cds])
                except (TypeError, ValueError):
                    pass
            return 0.0

        # cache gc per target gene symbol
        gc_cache = {}

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg:
                sym = tg[0]
                if sym not in gc_cache:
                    gc_cache[sym] = gc_of(sym)
                gc = gc_cache[sym]
            else:
                gc = 0.0
            out[i, :, 0] = gc * cm

        out[~np.isfinite(out)] = 0.0
        return out
