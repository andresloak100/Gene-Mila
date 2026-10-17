import numpy as np
from genemila.features.api import Feature, register


@register
class CpGPromoterScoreE81(Feature):
    name = "cpg_promoter_score_e81"
    version = 1
    description = "Gene-level CpG island promoter observed/expected ratio from gene_annotation."
    rationale = (
        "cpg_oe_promoter reflects promoter CpG content and chromatin/regulatory "
        "potential, which may modulate how strongly a gene responds to perturbation."
    )
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            if ci is not None:
                for g, row in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or row is None:
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
                        vals[gi] = fv

        # Normalize across measured genes (z-score); missing -> 0 (mean).
        out_col = np.zeros(n_genes, dtype=np.float64)
        mask = np.isfinite(vals)
        if mask.any():
            v = vals[mask]
            mu = float(v.mean())
            sd = float(v.std())
            if sd > 1e-12:
                out_col[mask] = (v - mu) / sd
            else:
                out_col[mask] = 0.0

        out = np.repeat(out_col[None, :, None], len(perts), axis=0)
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
