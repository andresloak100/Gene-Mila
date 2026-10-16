import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesTargetGcCdsE549(Feature):
    name = "screen_delta_times_target_gc_cds_e549"
    version = 1
    description = ("Elementwise product of replogle_delta_signed_e35 and gc_cds of the "
                   "target gene (for pairs, mean of gc_cds).")
    rationale = ("Multiplying signed Replogle screen delta by GC content of the target gene's "
                 "CDS improves prediction due to CRISPRa efficiency variation.")
    inputs = ["replogle_delta_signed_e35", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # gc_cds per gene from gene_annotation knowledge
        ann = ctx.knowledge("gene_annotation")
        gc_cds = np.zeros(n_genes, dtype=np.float64)
        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            gc_idx = None
            for j, c in enumerate(cols):
                if str(c).lower() == "gc_cds":
                    gc_idx = j
                    break
            if gc_idx is not None:
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_ann.get(gname)
                    if vals is not None:
                        v = vals[gc_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    gc_cds[gi] = fv
                            except (TypeError, ValueError):
                                pass

        # signed screen delta per perturbation (target mean)
        screen = ctx.feature("replogle_delta_signed_e35", perts, params)
        # screen shape (len(perts), n_genes, 1) or (len(perts), n_genes)
        if screen.ndim == 3:
            screen = screen[:, :, 0]
        else:
            screen = np.asarray(screen, dtype=np.float64)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            gidx = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not gidx:
                continue
            # mean gc_cds over target genes
            gc_mean = float(np.mean(gc_cds[gidx]))
            # signed screen delta of target (mean over targets) times gc_cds mean
            sd = screen[i]
            # sd is already the signed screen delta per gene g (target-mean across targets)
            out[i, :, 0] = sd * gc_mean

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
