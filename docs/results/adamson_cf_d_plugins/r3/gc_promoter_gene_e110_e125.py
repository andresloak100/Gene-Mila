import numpy as np
from genemila.features.api import Feature, register


@register
class GcPromoterGene(Feature):
    name = "gc_promoter_gene_e110_e125"
    version = 1
    description = "GC content of the promoter region of gene g (gene_annotation.gc_promoter)."
    rationale = ("High-GC promoters are often CpG-rich housekeeping promoters, whose genes are "
                 "broadly expressed and buffered against perturbation; promoter GC may therefore "
                 "capture gene-side susceptibility to expression change.")
    inputs = ["gene_annotation"]
    params = {"impute": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            cols = ka.get("columns", [])
            genes = ka.get("genes", {}) or {}
            try:
                ci = cols.index("gc_promoter")
            except ValueError:
                ci = None
            if ci is not None:
                for j, g in enumerate(ctx.genes):
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[j] = fv

        # Impute missing values
        impute = params.get("impute", "median") if params else "median"
        finite = np.isfinite(vals)
        if finite.any():
            if impute == "mean":
                fill = float(np.mean(vals[finite]))
            elif impute == "zero":
                fill = 0.0
            else:
                fill = float(np.median(vals[finite]))
        else:
            fill = 0.0
        vals = np.where(finite, vals, fill)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
