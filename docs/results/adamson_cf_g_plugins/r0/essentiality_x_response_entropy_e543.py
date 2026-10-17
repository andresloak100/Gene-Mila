import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityXResponseEntropy(Feature):
    name = "essentiality_x_response_entropy_e543"
    version = 1
    description = "Product of (1 - LOEUF_target) and response_entropy_e89 for each (p,g)."
    rationale = (
        "Essential targets (low LOEUF) may induce stronger responses, but only for "
        "genes that are generally responsive across perturbations; the interaction "
        "between target essentiality and per-gene response entropy captures this synergy."
    )
    inputs = ["train_delta", "knowledge:gene_constraint"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_e543_loeuf"
        if key in cache:
            return cache[key]
        loeuf = {}
        k = ctx.knowledge("gene_constraint")
        if k is not None:
            cols = k.get("columns", [])
            genes_tbl = k.get("genes", {})
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes_tbl.items():
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
                        loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def _response_entropy(self, ctx, exclude):
        """Per-gene Shannon entropy of deltas across training perturbations,
        computed with train_delta(exclude=exclude) to avoid label leakage."""
        cache = ctx.cache
        key = ("_e543_entropy", exclude)
        if key in cache:
            return cache[key]
        _, d = ctx.train_delta(exclude=exclude)
        d = np.asarray(d, dtype=float)
        if d.ndim != 2 or d.shape[0] == 0:
            ent = np.zeros(ctx.n_genes, dtype=float)
        else:
            ent = np.zeros(d.shape[1], dtype=float)
            for j in range(d.shape[1]):
                col = d[:, j]
                col = col[np.isfinite(col)]
                if col.size == 0:
                    continue
                lo = col.min()
                hi = col.max()
                if hi <= lo:
                    continue
                nbins = int(min(20, max(3, int(np.sqrt(col.size)))))
                hist, _ = np.histogram(col, bins=nbins, range=(lo, hi))
                p = hist.astype(float)
                s = p.sum()
                if s <= 0:
                    continue
                p = p[p > 0] / s
                ent[j] = -np.sum(p * np.log(p))
        cache[key] = ent
        return ent

    def compute(self, ctx, perts, params):
        loeuf_map = self._loeuf_map(ctx)
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            ent = self._response_entropy(ctx, exclude=p)
            targets = ctx.target_genes(p)
            loeuf_vals = [loeuf_map[t] for t in targets if t in loeuf_map]
            if loeuf_vals:
                loeuf_t = float(np.mean(loeuf_vals))
            else:
                loeuf_t = 1.0
            ess = 1.0 - loeuf_t
            out[i, :, 0] = ess * ent

        out[~np.isfinite(out)] = 0.0
        return out
