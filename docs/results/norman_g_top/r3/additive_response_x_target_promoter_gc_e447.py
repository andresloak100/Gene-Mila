import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetPromoterGC(Feature):
    name = "additive_response_x_target_promoter_gc_e447"
    version = 1
    description = "Product of additive_response and the mean promoter GC content of the perturbation's target genes."
    rationale = ("CRISPRa efficiency and transcriptional response may vary with promoter GC content; "
                 "high GC promoters may be more or less responsive, and interacting with the additive "
                 "baseline captures context-specific effects.")
    inputs = ["train_delta", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # Load gene annotation, get gc_promoter column index.
        ann = ctx.knowledge("gene_annotation")
        gc_prom = None
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                gc_idx = cols.index("gc_promoter")
            except ValueError:
                gc_idx = None
            genes_ann = ann.get("genes", {})
            if gc_idx is not None:
                gc_prom = {}
                for sym, vals in genes_ann.items():
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
                        gc_prom[sym] = fv

        # Fallback GC proxy: mean control expression based estimate if annotation missing.
        fallback_gc = None
        if gc_prom is None:
            # crude proxy: standardized control mean mapped to [0,1] via rank-free sigmoid
            cm = ctx.control_mean
            fallback_gc = 1.0 / (1.0 + np.exp(-cm))

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # Additive response: sum over targets of each gene's mean delta across training perts.
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)  # (n_genes,)

            tgenes = ctx.target_genes(p)
            tidx = ctx.target_indices(p)

            # Mean promoter GC across target genes.
            gc_vals = []
            if gc_prom is not None:
                for g in tgenes:
                    if g in gc_prom:
                        gc_vals.append(gc_prom[g])
            if not gc_vals and fallback_gc is not None and len(tidx) > 0:
                gc_vals = [float(fallback_gc[j]) for j in tidx]

            if gc_vals:
                gc_mean = float(np.mean(gc_vals))
            else:
                gc_mean = 0.0

            row = add * gc_mean
            row = np.where(np.isfinite(row), row, 0.0)
            out[i, :, 0] = row

        return out
