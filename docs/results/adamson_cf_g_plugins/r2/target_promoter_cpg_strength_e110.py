import numpy as np
from genemila.features.api import Feature, register

@register
class TargetPromoterCpgStrengthE110(Feature):
    name = "target_promoter_cpg_strength_e110"
    version = 1
    description = "Promoter CpG strength (CpG O/E ratio or GC content) of the target gene broadcast to all genes."
    rationale = ("Genes with strong CpG island promoters may be more responsive to perturbations "
                 "targeting chromatin regulators or transcription factors; the target's promoter "
                 "CpG features can therefore modulate the predicted response program.")
    inputs = ["knowledge", "target_genes"]
    params = {"feature": "cpg_oe_promoter"}
    dim = 1

    def compute(self, ctx, perts, params):
        feature_name = params.get("feature", "cpg_oe_promoter")
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        if ann is None:
            return out

        genes = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []

        try:
            col_idx = columns.index(feature_name)
        except ValueError:
            col_idx = None

        # Fallback column if requested feature missing
        fallback_idx = None
        for fb in ("cpg_oe_promoter", "gc_promoter"):
            if fb in columns:
                fallback_idx = columns.index(fb)
                break

        use_idx = col_idx if col_idx is not None else fallback_idx
        if use_idx is None:
            return out

        # Precompute per-gene value lookup (gene symbol -> value)
        cache = ctx.cache
        key = ("target_promoter_cpg_strength_e110", feature_name, use_idx)
        if key not in cache:
            vals = {}
            for sym, row in genes.items():
                if row is None:
                    continue
                try:
                    v = row[use_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(v):
                    vals[sym] = v
            cache[key] = vals
        vals = cache[key]

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            collected = [vals[g] for g in tgenes if g in vals]
            if collected:
                out[i, :, 0] = float(np.mean(collected))
        return out
