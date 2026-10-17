import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetGcPromoter(Feature):
    name = "additive_response_x_target_gc_promoter_e312"
    version = 1
    description = "Product of additive_response and the mean gc_promoter of the target genes of perturbation p."
    rationale = ("Promoter GC content affects transcription factor binding and chromatin accessibility; "
                 "perturbations may have stronger effects on genes with high or low GC promoters, "
                 "modulating the additive baseline prediction.")
    inputs = ["control_cells", "train_delta", "knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # Load gene_annotation gc_promoter values.
        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                gc_idx = cols.index("gc_promoter")
            except ValueError:
                gc_idx = None
            genes_tbl = ann.get("genes", {}) or {}
            if gc_idx is not None:
                for sym, vals in genes_tbl.items():
                    try:
                        v = vals[gc_idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc_map[sym] = fv

        # Additive baseline: sum over target genes of each gene's mean training delta.
        # Cache per-perturbation additive response (depends on exclude=p).
        for i, p in enumerate(perts):
            # gc_promoter mean over targets of p
            tgenes = ctx.target_genes(p)
            gc_vals = [gc_map[g] for g in tgenes if g in gc_map]
            if gc_vals:
                gc_mean = float(np.mean(gc_vals))
            else:
                gc_mean = 0.0

            # Additive response: sum of mean training deltas over target genes.
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] > 0:
                mean_delta = d.mean(axis=0)  # (n_genes,)
            else:
                mean_delta = np.zeros(ctx.n_genes, dtype=float)

            t_idx = ctx.target_indices(p)
            if t_idx:
                add = mean_delta[np.asarray(t_idx, dtype=int)].sum()
            else:
                add = 0.0

            out[i, :, 0] = add * gc_mean

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
