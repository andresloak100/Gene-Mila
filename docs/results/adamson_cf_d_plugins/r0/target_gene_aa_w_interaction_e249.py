import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAaWInteractionE249(Feature):
    name = "target_gene_aa_w_interaction_e249"
    version = 1
    description = "Product of target gene's aa_W and gene g's aa_W from gene_annotation."
    rationale = ("Shared tryptophan content may indicate similar protein turnover or "
                 "interaction with the same regulatory complexes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        genes = ann.get("genes", {})
        if "aa_W" not in columns:
            return out
        w_idx = columns.index("aa_W")

        # Per-gene aa_W vector aligned to ctx.genes
        gene_aa_w = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, vals in genes.items():
            j = ctx.gene_index.get(g)
            if j is None:
                continue
            try:
                v = vals[w_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                gene_aa_w[j] = float(v)
            except (TypeError, ValueError):
                continue

        # Fill NaN with 0 (unknown tryptophan fraction)
        gene_aa_w = np.where(np.isfinite(gene_aa_w), gene_aa_w, 0.0)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # Mean aa_W of target gene(s)
            tvals = gene_aa_w[np.asarray(tidx, dtype=int)]
            t_aa_w = float(np.mean(tvals)) if tvals.size else 0.0
            out[i, :, 0] = t_aa_w * gene_aa_w

        return out
