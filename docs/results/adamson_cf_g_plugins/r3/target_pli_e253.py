import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPLI(Feature):
    name = "target_pli_e253"
    version = 1
    description = "pLI (LoF intolerance) of the perturbation's target gene, median-filled."
    rationale = (
        "LoF-intolerant (high pLI) targets are often essential; their knockdown may "
        "elicit broad transcriptomic changes, so pLI can modulate response magnitude."
    )
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        data = ctx.knowledge("gene_constraint")
        pli_by_gene = {}
        all_vals = []
        if data is not None:
            cols = data.get("columns", [])
            # locate pLI column (case-insensitive)
            pli_idx = None
            for j, c in enumerate(cols):
                if str(c).lower() == "pli":
                    pli_idx = j
                    break
            if pli_idx is not None:
                genes = data.get("genes", {})
                for sym, vals in genes.items():
                    if vals is None or pli_idx >= len(vals):
                        continue
                    v = vals[pli_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        pli_by_gene[sym] = fv
                        all_vals.append(fv)

        if all_vals:
            median_val = float(np.median(np.asarray(all_vals, dtype=float)))
        else:
            median_val = 0.0

        # column vector of pLI per gene (median-filled)
        pli_vec = np.full(ctx.n_genes, median_val, dtype=float)
        for sym, fv in pli_by_gene.items():
            gi = ctx.gene_index.get(sym)
            if gi is not None:
                pli_vec[gi] = fv

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if tidx:
                # single-gene targets typical; average if multiple
                vals = pli_vec[np.asarray(tidx, dtype=int)]
                out[i, :, 0] = float(np.mean(vals))
            else:
                out[i, :, 0] = median_val

        out[~np.isfinite(out)] = 0.0
        return out
