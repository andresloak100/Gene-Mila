import numpy as np
from genemila.features.api import Feature, register


@register
class CpGIslandPromoterInteraction(Feature):
    name = "cpg_island_promoter_interaction_e155"
    version = 1
    description = (
        "Interaction between target gene's CpG island promoter status and gene g's "
        "CpG island promoter status."
    )
    rationale = (
        "Perturbations targeting CpG-island-promoter genes may preferentially change "
        "expression of other CpG-island-promoter genes via shared epigenetic regulation."
    )
    inputs = ["gene_annotation", "target_indices"]
    params = {"cpg_threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("cpg_threshold", 0.6))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Cache per-gene CpG island promoter binary status.
        cache = ctx.cache
        key = ("cpg_island_binary_e155", threshold)
        cpg_bin = cache.get(key)
        if cpg_bin is None:
            cpg_bin = np.zeros(n_genes, dtype=float)
            ann = ctx.knowledge("gene_annotation")
            if ann is not None:
                genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}
                cols = ann.get("columns", []) if isinstance(ann, dict) else []
                # Locate the cpg_oe_promoter column index.
                col_idx = None
                for j, c in enumerate(cols):
                    if c == "cpg_oe_promoter":
                        col_idx = j
                        break
                if col_idx is not None:
                    for gi, gname in enumerate(ctx.genes):
                        vals = genes_tbl.get(gname)
                        if vals is None:
                            continue
                        try:
                            v = vals[col_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv) and fv > threshold:
                            cpg_bin[gi] = 1.0
            cache[key] = cpg_bin

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Target CpG status: use max over targeted genes (usually single).
            tgt_status = float(np.max(cpg_bin[tgt_idx]))
            if tgt_status == 0.0:
                continue
            out[i, :, 0] = tgt_status * cpg_bin

        return out
