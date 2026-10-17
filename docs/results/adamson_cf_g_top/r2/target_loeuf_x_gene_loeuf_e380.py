import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneLoeuf(Feature):
    name = "target_loeuf_x_gene_loeuf_e380"
    version = 1
    description = "Product of target LOEUF and gene LOEUF from gnomAD constraint."
    rationale = ("Perturbing an essential (low LOEUF) target may disproportionately affect "
                 "dosage-sensitive (low LOEUF) genes; product captures this coupling.")
    inputs = ["knowledge", "target_indices"]
    params = {"impute_missing": "median"}
    dim = 1

    def _loeuf_map(self, ctx, params):
        cache = ctx.cache
        key = "loeuf_map_e380"
        if key in cache:
            return cache[key]

        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []
            try:
                idx = columns.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
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
                        loeuf[gi] = fv

        finite = loeuf[np.isfinite(loeuf)]
        if finite.size > 0:
            fill = float(np.median(finite))
        else:
            fill = 1.0
        loeuf = np.where(np.isfinite(loeuf), loeuf, fill)

        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        loeuf = self._loeuf_map(ctx, params)
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                t_loeuf = float(np.mean(loeuf[tgt_idx]))
            else:
                t_loeuf = 1.0
            out[i, :, 0] = t_loeuf * loeuf

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
