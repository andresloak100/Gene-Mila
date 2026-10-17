import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetGcCds(Feature):
    name = "additive_response_x_target_gc_cds_e575"
    version = 1
    description = "Product of additive_response and the mean gc_cds of the perturbation's target genes."
    rationale = ("GC content of the CDS affects translation and mRNA stability; "
                 "it may modulate CRISPRa efficiency and the downstream additive response.")
    inputs = ["control_mean", "gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # additive_response feature: (n_perts, n_genes, dim)
        add = ctx.feature("additive_response", perts, None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.nan_to_num(add, nan=0.0, posinf=0.0, neginf=0.0)

        # Load gene_annotation gc_cds per gene
        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                gc_idx = cols.index("gc_cds")
            except ValueError:
                gc_idx = None
            genes_ann = ann.get("genes", {})
            if gc_idx is not None:
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
                        gc_map[sym] = fv

        # Per-gene gc_cds vector aligned to ctx.genes
        gc_vec = np.full(n_genes, np.nan, dtype=float)
        for i, g in enumerate(ctx.genes):
            if g in gc_map:
                gc_vec[i] = gc_map[g]

        # Global fallback mean for genes lacking annotation
        finite_mask = np.isfinite(gc_vec)
        global_mean = float(np.mean(gc_vec[finite_mask])) if finite_mask.any() else 0.0

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                vals = gc_vec[tgt_idx]
                vals = vals[np.isfinite(vals)]
                mean_gc = float(np.mean(vals)) if vals.size > 0 else global_mean
            else:
                mean_gc = global_mean
            out[i, :, 0] = add[i] * mean_gc

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
