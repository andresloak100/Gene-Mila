import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterGCGene(Feature):
    name = "promoter_gc_gene_e126_e138"
    version = 1
    description = "Promoter GC content of gene g from gene_annotation, z-scored across measured genes."
    rationale = ("Promoter GC content reflects regulatory architecture; high GC promoters "
                 "(CpG islands, housekeeping genes) may be more buffered and less responsive "
                 "to perturbations, so a negative coefficient is expected.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vals = np.full(n, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                gi = list(cols).index("gc_promoter")
            except (ValueError, TypeError):
                gi = None
            if gi is not None:
                for j, g in enumerate(ctx.genes):
                    rec = genes.get(g)
                    if rec is None:
                        continue
                    try:
                        v = rec[gi]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        vals[j] = v

        # Impute missing with mean of observed, then z-score.
        obs = np.isfinite(vals)
        if obs.any():
            m = vals[obs].mean()
        else:
            m = 0.0
        vals[~obs] = m
        sd = vals.std()
        if not np.isfinite(sd) or sd <= 0:
            z = np.zeros(n, dtype=float)
        else:
            z = (vals - vals.mean()) / sd
        z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.empty((len(perts), n, 1), dtype=float)
        out[:, :, 0] = z[None, :]
        return out
