import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGcCdsXIsTarget(Feature):
    name = "target_gc_cds_x_is_target_e243"
    version = 1
    description = "Product of target gene's gc_cds and is_target indicator."
    rationale = (
        "GC content of the target coding sequence may modulate perturbation "
        "response; interacting it with the is_target indicator gives a "
        "target-specific, gene-local signal."
    )
    inputs = ["knowledge", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ka = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ka is not None:
            genes = ka.get("genes", {}) or {}
            cols = ka.get("columns", []) or []
            try:
                gc_idx = cols.index("gc_cds")
            except ValueError:
                gc_idx = None
            if gc_idx is not None:
                for sym, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[gc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc_map[sym] = fv

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            # value from the (first) target gene with a valid gc_cds
            val = None
            for tg in tgenes:
                if tg in gc_map:
                    val = gc_map[tg]
                    break
            if val is None:
                continue
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            idx = np.asarray(tgt_idx, dtype=int)
            idx = idx[(idx >= 0) & (idx < ctx.n_genes)]
            if idx.size:
                out[i, idx, 0] = val

        out[~np.isfinite(out)] = 0.0
        return out
