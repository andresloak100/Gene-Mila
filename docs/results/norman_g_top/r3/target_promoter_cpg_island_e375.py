import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGIslandE375(Feature):
    name = "target_promoter_cpg_island_e375"
    version = 1
    description = "Fraction of a perturbation's target genes whose promoter is a CpG island (cpg_oe_promoter > threshold), broadcast to all genes."
    rationale = "CpG island promoters are associated with active chromatin and may enhance CRISPRa efficacy, modulating downstream expression changes."
    inputs = ["gene_annotation", "target_genes"]
    params = {"threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("threshold", 0.6))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        cpg_col = None
        cpg_values = None
        if ann is not None:
            columns = ann.get("columns", [])
            if "cpg_oe_promoter" in columns:
                cpg_col = columns.index("cpg_oe_promoter")
                genes_ann = ann.get("genes", {})
                cpg_values = genes_ann

        # Precompute per-gene CpG island flag aligned to ctx.genes
        is_cpg = np.zeros(n_genes, dtype=float)
        if cpg_values is not None and cpg_col is not None:
            for g, col in ctx.gene_index.items():
                vals = cpg_values.get(g)
                if vals is not None and len(vals) > cpg_col:
                    v = vals[cpg_col]
                    if v is not None:
                        try:
                            if float(v) > threshold:
                                is_cpg[col] = 1.0
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            vals = []
            for tg in tgenes:
                idx = ctx.gene_index.get(tg)
                if idx is not None:
                    vals.append(is_cpg[idx])
            if vals:
                out[i, :, 0] = float(np.mean(vals))
        return out
