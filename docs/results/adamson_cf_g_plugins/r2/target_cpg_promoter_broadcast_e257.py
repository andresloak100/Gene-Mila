import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpGPromoterBroadcast(Feature):
    name = "target_cpg_promoter_broadcast_e257"
    version = 1
    description = "CpG observed/expected ratio of the target gene's promoter, broadcast to all genes."
    rationale = ("Promoter CpG density is linked to chromatin state and transcriptional regulation; "
                 "targets with CpG-rich promoters may yield larger or more pervasive responses.")
    inputs = ["knowledge"]
    params = {"source": "gene_annotation"}
    dim = 1

    def compute(self, ctx, perts, params):
        source = params.get("source", "gene_annotation")
        ann = ctx.knowledge(source)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        col_idx = None
        genes_map = {}
        if isinstance(ann, dict):
            cols = ann.get("columns", []) or []
            try:
                col_idx = list(cols).index("cpg_oe_promoter")
            except ValueError:
                col_idx = None
            genes_map = ann.get("genes", {}) or {}

        # Cache per-gene value extraction
        cache = ctx.cache
        key = ("cpg_oe_promoter_values", source)
        if key not in cache:
            vals = {}
            if col_idx is not None:
                for g, row in genes_map.items():
                    try:
                        v = row[col_idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            fv = None
                        if fv is not None and np.isfinite(fv):
                            vals[g] = fv
            cache[key] = vals
        vals = cache[key]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            v = 0.0
            for t in tg:
                if t in vals:
                    v = vals[t]
                    break
            out[i, :, 0] = v

        out[~np.isfinite(out)] = 0.0
        return out
