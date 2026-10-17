import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgTimesGeneGcPromoterE115(Feature):
    name = "target_cpg_times_gene_gc_promoter_e115"
    version = 1
    description = ("Product of the mean CpG observed/expected ratio of target gene promoters "
                   "and the GC content of gene g's promoter.")
    rationale = ("CpG island status of the perturbed target may modulate chromatin state, "
                 "and its effect could scale with the GC content of the responding gene's promoter.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        cols = ann.get("columns", [])
        try:
            cpg_idx = cols.index("cpg_oe_promoter")
            gc_idx = cols.index("gc_promoter")
        except ValueError:
            return out

        genes_ann = ann.get("genes", {})

        # Per-gene gc_promoter vector aligned to ctx.genes
        gc_vec = np.full(n_genes, np.nan, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes_ann.get(g)
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
                gc_vec[j] = fv

        # Replace missing gc with column mean (or 0 if none)
        if np.any(np.isfinite(gc_vec)):
            fill = float(np.nanmean(gc_vec))
            gc_vec = np.where(np.isfinite(gc_vec), gc_vec, fill)
        else:
            gc_vec = np.zeros(n_genes, dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = []
            for tg in targets:
                tv = genes_ann.get(tg)
                if tv is None:
                    continue
                try:
                    v = tv[cpg_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals.append(fv)
            if not vals:
                continue
            mean_cpg = float(np.mean(vals))
            out[i, :, 0] = mean_cpg * gc_vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
