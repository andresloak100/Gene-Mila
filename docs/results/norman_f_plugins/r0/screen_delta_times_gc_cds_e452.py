import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesGcCds(Feature):
    name = "screen_delta_times_gc_cds_e452"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and gc_cds of gene g."
    rationale = (
        "GC content of the coding sequence affects transcriptional/translational "
        "efficiency; interacting it with the signed screen delta captures "
        "gene-specific response modulation."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # gc_cds per gene, aligned to ctx.genes order
        gc = np.full(ctx.n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes", {})
            cols = ann.get("columns", [])
            # locate gc_cds column index robustly
            gc_idx = None
            for j, c in enumerate(cols):
                if c == "gc_cds":
                    gc_idx = j
                    break
            if gc_idx is None:
                # fallback: search for a column name containing gc_cds
                for j, c in enumerate(cols):
                    if "gc_cds" in str(c):
                        gc_idx = j
                        break
            if gc_idx is not None:
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_map.get(gname)
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
                        gc[gi] = fv

        # fill NaNs with column mean of finite values (or 0 if none)
        finite_mask = np.isfinite(gc)
        if finite_mask.any():
            fill = float(gc[finite_mask].mean())
            gc = np.where(finite_mask, gc, fill)
        else:
            gc = np.zeros(ctx.n_genes, dtype=float)

        # signed screen delta feature: (n_perts, n_genes, 1)
        sd = ctx.feature("replogle_delta_signed_e35", perts)
        sd = np.asarray(sd, dtype=float)
        if sd.ndim == 2:
            sd = sd[:, :, None]
        sd = np.nan_to_num(sd, nan=0.0, posinf=0.0, neginf=0.0)

        out[:, :, 0] = sd[:, :, 0] * gc[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
