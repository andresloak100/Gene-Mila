import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenDeltaTimesGcPromoterE472(Feature):
    name = "screen_delta_times_gc_promoter_e472"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and gc_promoter annotation for gene g."
    rationale = "Promoter GC content affects transcriptional regulation; interaction with screen delta may capture regulatory potential."
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n, n_genes, 1), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        gc = None
        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("gc_promoter")
            except ValueError:
                idx = None
            if idx is not None:
                gc = np.full(n_genes, np.nan, dtype=np.float64)
                for g, col in ctx.gene_index.items():
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc[col] = fv

        if gc is None:
            gc = np.zeros(n_genes, dtype=np.float64)
        else:
            gc = np.where(np.isfinite(gc), gc, 0.0)

        screen = ctx.feature("replogle_delta_signed_e35", perts)

        for i in range(n):
            row = screen[i, :, 0]
            out[i, :, 0] = row * gc

        out = np.where(np.isfinite(out), out, 0.0)
        return out
