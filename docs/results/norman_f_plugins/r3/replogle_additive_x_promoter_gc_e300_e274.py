import numpy as np
from genemila.features.api import Feature, register

@register
class ReplogleAdditiveXPromoterGC(Feature):
    name = "replogle_additive_x_promoter_gc_e300_e274"
    version = 1
    description = "Product of sign-corrected Replogle additive response and gene g's promoter GC content."
    rationale = ("CRISPRa efficiency and transcriptional response may vary with promoter GC content; "
                 "interacting the Replogle additive response with gc_promoter captures genes whose "
                 "responsiveness to activation depends on promoter composition.")
    inputs = ["replogle", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Sign-corrected Replogle additive response per perturbation.
        base = ctx.feature(
            "replogle_additive_response_signed_e104", perts
        )  # (n_perts, n_genes, 1)
        base = np.asarray(base, dtype=float).reshape(n_perts, n_genes)

        # gc_promoter per gene, aligned to ctx.genes order.
        gc = np.full(n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes") or {}
            columns = ann.get("columns") or []
            try:
                gc_idx = list(columns).index("gc_promoter")
            except ValueError:
                gc_idx = None
            if gc_idx is not None:
                for j, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
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
                        gc[j] = fv

        # Fill missing GC with the mean of the observed values (0.0 if none).
        finite_mask = np.isfinite(gc)
        if finite_mask.any():
            fill = float(np.mean(gc[finite_mask]))
        else:
            fill = 0.0
        gc = np.where(finite_mask, gc, fill)

        out = base * gc[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out.reshape(n_perts, n_genes, 1)
