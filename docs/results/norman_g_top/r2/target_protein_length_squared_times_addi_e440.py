import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthSquaredTimesAdditive(Feature):
    name = "target_protein_length_squared_times_addi_e440"
    version = 1
    description = "Product of the squared mean protein length of p's target genes and additive_response."
    rationale = "Protein length may have nonlinear effects on expression response; squaring captures curvature."
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # additive_response feature (n_perts, n_genes, dim)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim != 2:
            add = np.asarray(add).reshape(len(perts), n_genes)

        # protein length map
        prot = ctx.knowledge("protein_annotation")
        plen = {}
        if prot is not None:
            cols = prot.get("columns", [])
            genes_tbl = prot.get("genes", {})
            if "protein_length" in cols:
                idx = cols.index("protein_length")
                for g, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        plen[g] = v

        # cache per-pert mean protein length (order-independent over target set)
        cache = ctx.cache
        key = "_tpl_e440"
        plen_sq = cache.get(key)
        if plen_sq is None:
            plen_sq = {}
            for p in ctx.perts:
                tg = ctx.target_genes(p)
                vals = [plen[g] for g in tg if g in plen]
                if vals:
                    m = float(np.mean(vals))
                    plen_sq[p] = m * m
                else:
                    plen_sq[p] = 0.0
            cache[key] = plen_sq

        for i, p in enumerate(perts):
            out[i, :, 0] = plen_sq.get(p, 0.0) * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
