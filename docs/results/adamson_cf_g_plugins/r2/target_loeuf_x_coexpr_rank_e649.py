import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXCoexprRankE649(Feature):
    name = "target_loeuf_x_coexpr_rank_e649"
    version = 1
    description = "Product of target LOEUF and rank of Pearson correlation between target and gene."
    rationale = "LoF-intolerant (low LOEUF) targets are essential; their perturbation may dysregulate genes ranked highly coexpressed with them."
    inputs = ["control_cells", "gene_corr", "knowledge"]
    params = {}
    dim = 1

    def _loeuf_table(self, ctx):
        cache = ctx.cache
        key = "_e649_loeuf"
        if key in cache:
            return cache[key]
        loeuf = {}
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            genes = kn.get("genes", {})
            cols = kn.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is not None and len(vals) > idx:
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        loeuf = self._loeuf_table(ctx)
        corr = ctx.gene_corr
        gene_index = ctx.gene_index

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t = t_idx[0]
            t_gene = ctx.genes[t]
            lo = loeuf.get(t_gene, np.nan)
            if not np.isfinite(lo):
                # fall back to median LOEUF if target unavailable
                vals = [v for v in loeuf.values() if np.isfinite(v)]
                lo = float(np.median(vals)) if vals else 1.0
            row = corr[t]
            # rank correlations (higher corr -> higher rank)
            order = np.argsort(row, kind="mergesort")
            ranks = np.empty(n_genes, dtype=float)
            ranks[order] = np.arange(n_genes, dtype=float)
            # normalise rank to [0,1]
            if n_genes > 1:
                ranks = ranks / (n_genes - 1)
            out[i, :, 0] = lo * ranks
        return out
