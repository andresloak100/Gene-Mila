import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterGCSimilarity(Feature):
    name = "target_promoter_gc_similarity_e551"
    version = 1
    description = "Mean absolute difference in promoter GC content between gene g and each target of perturbation p."
    rationale = ("Promoter GC content is associated with gene regulation; genes with similar promoter "
                 "properties may respond similarly to perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann or "genes" not in ann:
            return out

        genes_tbl = ann["genes"]
        columns = ann.get("columns", [])
        if "gc_promoter" not in columns:
            return out
        gc_idx = columns.index("gc_promoter")

        # Map gene symbol -> gc_promoter value (None if missing/null)
        gc_vals = {}
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
                gc_vals[sym] = fv

        # Precompute per-gene gc_promoter array aligned to ctx.genes
        gene_gc = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, gname in enumerate(ctx.genes):
            if gname in gc_vals:
                gene_gc[gi] = gc_vals[gname]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            tvals = [gc_vals[t] for t in targets if t in gc_vals]
            if not tvals:
                continue
            tvals = np.asarray(tvals, dtype=float)
            # Mean over targets of abs(gene_gc - t)
            diff = np.abs(gene_gc[:, None] - tvals[None, :])  # (n_genes, n_targets)
            mean_diff = np.nanmean(diff, axis=1)
            mean_diff = np.where(np.isfinite(mean_diff), mean_diff, 0.0)
            out[i, :, 0] = mean_diff

        return out
