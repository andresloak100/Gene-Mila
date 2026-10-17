import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufWeightedTargetResponseSimilarity(Feature):
    name = "loeuf_weighted_target_response_similarit_e664"
    version = 1
    description = ("For gene g and perturbation p, weighted average of g's similarity to "
                   "training responses of p's targets, weights = 1/LOEUF (0 if missing); "
                   "pairs average over both targets.")
    rationale = ("LoF-intolerant (low LOEUF) genes may be more tightly regulated, so their "
                 "response profiles are more informative for coupling; weighting by inverse "
                 "LOEUF sharpens the target-similarity signal.")
    inputs = ["control_cells", "gene_corr", "gene_constraint"]
    params = {"weight_power": 1.0}
    dim = 1

    def _loeuf_weights(self, ctx, params):
        cache = ctx.cache
        power = float(params.get("weight_power", 1.0))
        key = ("loeuf_weights", power)
        if key in cache:
            return cache[key]
        w = np.zeros(ctx.n_genes, dtype=np.float64)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            genes_tbl = kn.get("genes", {}) or {}
            columns = kn.get("columns", []) or []
            try:
                loeuf_col = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            if loeuf_col is not None:
                for g, gi in ctx.gene_index.items():
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    try:
                        val = row[loeuf_col]
                    except (IndexError, TypeError):
                        continue
                    if val is None:
                        continue
                    try:
                        val = float(val)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(val) or val <= 0:
                        continue
                    w[gi] = 1.0 / (val ** power)
        cache[key] = w
        return w

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        w_gene = self._loeuf_weights(ctx, params)
        gc = ctx.gene_corr

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if len(targets) == 0:
                continue
            targets = list(targets)

            tw = np.array([w_gene[t] for t in targets], dtype=np.float64)
            if tw.sum() <= 0:
                tw = np.ones(len(targets), dtype=np.float64)
            tw = tw / tw.sum()

            t_idx = np.array(targets, dtype=np.int64)
            sim = gc[:, t_idx]  # (n_genes, T)
            out[i, :, 0] = sim @ tw

        out[~np.isfinite(out)] = 0.0
        return out
