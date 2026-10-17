import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLoeufRankE190(Feature):
    name = "target_loeuf_rank_e190"
    version = 1
    description = "Rank of target gene's LOEUF among all genes (lower rank = more conserved/intolerant)."
    rationale = "Conservation as measured by LoF constraint (LOEUF) reflects functional importance; a target's rank among all genes captures its relative intolerance to loss of function."
    inputs = ["knowledge", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.full((len(perts), ctx.n_genes, 1), np.nan, dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        loeuf_map = {}
        if knowledge is not None and "genes" in knowledge:
            cols = knowledge.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for sym, vals in knowledge["genes"].items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf_map[sym] = fv

        # Build per-gene LOEUF vector aligned to ctx.genes
        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            if g in loeuf_map:
                loeuf[gi] = loeuf_map[g]

        # Compute ranks over available genes; lower LOEUF -> lower rank (more intolerant)
        valid_mask = np.isfinite(loeuf)
        n_valid = int(valid_mask.sum())

        if n_valid > 0:
            valid_vals = loeuf[valid_mask]
            order = np.argsort(valid_vals, kind="mergesort")
            ranks_valid = np.empty(n_valid, dtype=float)
            # average ranks for ties
            sorted_vals = valid_vals[order]
            i = 0
            while i < n_valid:
                j = i
                while j + 1 < n_valid and sorted_vals[j + 1] == sorted_vals[i]:
                    j += 1
                avg_rank = (i + j) / 2.0
                for k in range(i, j + 1):
                    ranks_valid[order[k]] = avg_rank
                i = j + 1
            # scale to [0,1]
            if n_valid > 1:
                scaled_valid = ranks_valid / (n_valid - 1)
            else:
                scaled_valid = np.zeros(n_valid, dtype=float)
            scaled = np.full(ctx.n_genes, np.nan, dtype=float)
            scaled[valid_mask] = scaled_valid
        else:
            scaled = np.full(ctx.n_genes, np.nan, dtype=float)

        # Median fill for missing
        finite_scaled = scaled[np.isfinite(scaled)]
        if finite_scaled.size > 0:
            med = float(np.median(finite_scaled))
        else:
            med = 0.5
        scaled_filled = np.where(np.isfinite(scaled), scaled, med)

        # For each perturbation, set value at target indices and fill rest with median
        for i, p in enumerate(perts):
            out[i, :, 0] = med
            try:
                tinds = ctx.target_indices(p)
            except Exception:
                tinds = []
            for ti in tinds:
                if 0 <= ti < ctx.n_genes:
                    out[i, ti, 0] = scaled_filled[ti]

        # Ensure finite
        out = np.where(np.isfinite(out), out, med)
        return out
