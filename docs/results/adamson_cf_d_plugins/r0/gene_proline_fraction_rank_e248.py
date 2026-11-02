import numpy as np
from genemila.features.api import Feature, register

@register
class GeneProlineFractionRank(Feature):
    name = "gene_proline_fraction_rank_e248"
    version = 1
    description = "Rank of gene g's proline fraction (aa_P) among all genes, scaled to [0,1]."
    rationale = ("Proline content affects protein conformational flexibility, which may "
                 "correlate with expression response variability.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        col = None
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            try:
                col = columns.index("aa_P")
            except ValueError:
                col = None

        raw = np.full(n, np.nan, dtype=float)
        if ann is not None and col is not None:
            genes_tbl = ann.get("genes", {})
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                if col < len(vals):
                    v = vals[col]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            raw[gi] = fv
        else:
            # fallback: no table -> zeros
            pass

        present = np.isfinite(raw)
        ranks = np.zeros(n, dtype=float)
        if present.any():
            vals = raw[present]
            order = np.argsort(vals, kind="mergesort")
            n_present = vals.size
            r = np.empty(n_present, dtype=float)
            # average ranks for ties
            sorted_vals = vals[order]
            i = 0
            while i < n_present:
                j = i
                while j + 1 < n_present and sorted_vals[j + 1] == sorted_vals[i]:
                    j += 1
                avg_rank = 0.5 * (i + j) + 1.0  # 1-based
                r[order[i:j + 1]] = avg_rank
                i = j + 1
            if n_present > 1:
                scaled = (r - 1.0) / (n_present - 1.0)
            else:
                scaled = np.zeros(1, dtype=float)
            ranks[present] = scaled
        # absent genes -> 0.0 (scaled rank minimum)

        out = np.broadcast_to(ranks[None, :, None], (len(perts), n, 1)).copy()
        out[~np.isfinite(out)] = 0.0
        return out
