import numpy as np
from genemila.features.api import Feature, register

@register
class SharedCpgPromoterE195(Feature):
    name = "shared_cpg_promoter_e195"
    version = 1
    description = "Indicator: both target and gene g have CpG islands in their promoter regions."
    rationale = ("Shared promoter CpG-island features may indicate co-regulation by methylation "
                 "or shared transcription factors; CpG island presence is a strong genomic feature.")
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {"threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("threshold", 0.6))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_map = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []
        # locate the cpg_oe_promoter column index
        cpg_col = None
        for j, c in enumerate(columns):
            if c == "cpg_oe_promoter":
                cpg_col = j
                break
        if cpg_col is None:
            return out

        # Build per-gene CpG island presence for ctx gene columns
        gene_names = ctx.genes
        presence = np.zeros(n_genes, dtype=bool)
        for i, g in enumerate(gene_names):
            vals = genes_map.get(g)
            if vals is None:
                continue
            try:
                v = vals[cpg_col]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv) and fv > threshold:
                presence[i] = True

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # target has CpG island if any of its target genes do
            t_has = any(presence[t] for t in t_idx if 0 <= t < n_genes)
            if not t_has:
                continue
            # rows where both target and gene g have CpG islands
            out[i, :, 0] = presence.astype(float)

        return out
