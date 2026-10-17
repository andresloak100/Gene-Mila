import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneLoeuf(Feature):
    name = "target_loeuf_x_gene_loeuf_e367"
    version = 1
    description = "Product of target gene's LOEUF and gene g's LOEUF (z-scored)."
    rationale = (
        "Perturbing an essential (low LOEUF) target may disproportionately affect "
        "haploinsufficient (low LOEUF) genes due to shared dosage sensitivity."
    )
    inputs = ["knowledge:gene_constraint", "target_genes"]
    params = {"normalization": "zscore"}
    dim = 1

    def _load_loeuf(self, ctx):
        cache = ctx.cache
        key = "__loeuf_vec_e367"
        if key in cache:
            return cache[key]

        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            idx = None
            for i, c in enumerate(cols):
                if str(c).lower() == "oe_lof_upper":
                    idx = i
                    break
            genes = kc.get("genes", {}) or {}
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

        finite = np.isfinite(loeuf)
        if finite.any():
            med = float(np.median(loeuf[finite]))
        else:
            med = 1.0
        loeuf = np.where(finite, loeuf, med)

        # z-score normalization
        mu = float(loeuf.mean())
        sd = float(loeuf.std())
        if not np.isfinite(sd) or sd <= 0:
            sd = 1.0
        z = (loeuf - mu) / sd

        cache[key] = z
        return z

    def compute(self, ctx, perts, params):
        z = self._load_loeuf(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if t_idx:
                t_val = float(np.mean(z[t_idx]))
            else:
                t_val = 0.0
            out[i, :, 0] = t_val * z
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
