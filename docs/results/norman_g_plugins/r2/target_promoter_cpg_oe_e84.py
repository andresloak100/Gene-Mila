import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgOeE84(Feature):
    name = "target_promoter_cpg_oe_e84"
    version = 1
    description = "Average cpg_oe_promoter of the perturbation's target genes (single or pair)."
    rationale = (
        "CpG-rich promoters are associated with broader chromatin accessibility and "
        "regulatory potential; CRISPRa effectiveness may depend on promoter CpG content, "
        "affecting how strongly target genes are activated and thereby downstream responses."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        columns = ann.get("columns", [])
        genes = ann.get("genes", {})
        if "cpg_oe_promoter" not in columns:
            return out
        col_idx = columns.index("cpg_oe_promoter")

        # Precompute per-gene cpg_oe_promoter value (NaN if missing/null).
        cache = ctx.cache
        key = "_cpg_oe_promoter_map"
        if key not in cache:
            val_map = {}
            for g, vals in genes.items():
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
                val_map[g] = fv
            # Fallback global mean for genes with no annotation.
            global_mean = float(np.mean(list(val_map.values()))) if val_map else 0.0
            cache[key] = (val_map, global_mean)
        val_map, global_mean = cache[key]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                out[i, :, 0] = global_mean
                continue
            vals = [val_map.get(t, global_mean) for t in targets]
            out[i, :, 0] = float(np.mean(vals))

        return out
