import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesGcCds(Feature):
    name = "additive_times_gc_cds_e418"
    version = 1
    description = "Elementwise product of additive_response and gc_cds of gene g."
    rationale = ("GC content of the coding sequence influences mRNA secondary structure, "
                 "stability and translation efficiency, which may modulate the magnitude "
                 "of the expression change produced by a perturbation.")
    inputs = ["control_mean", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # --- gc_cds per gene, aligned to ctx.genes ---
        gc = np.full(n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            try:
                col = columns.index("gc_cds")
            except ValueError:
                col = None
            if col is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is not None:
                        v = vals[col]
                        if v is not None:
                            gc[gi] = float(v)
        # replace missing values with the mean of the observed ones (fallback 0.5)
        finite = np.isfinite(gc)
        if finite.any():
            fill = float(gc[finite].mean())
        else:
            fill = 0.5
        gc = np.where(finite, gc, fill)

        # --- additive_response (use the registered feature) ---
        add = ctx.feature("additive_response", perts)  # (n_perts, n_genes, 1)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        add = np.nan_to_num(add, nan=0.0, posinf=0.0, neginf=0.0)

        out = add * gc[None, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
