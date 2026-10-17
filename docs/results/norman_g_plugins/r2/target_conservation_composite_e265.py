import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConservationCompositeE265(Feature):
    name = "target_conservation_composite_e265"
    version = 1
    description = ("Mean over perturbation targets of a composite conservation score: "
                   "z(LOEUF) - z(protein length).")
    rationale = ("Conserved targets are more predictable; LOEUF measures LoF constraint and "
                 "protein length approximates conservation, so combining them (longer proteins "
                 "penalised) gives a per-gene conservation score averaged over targets.")
    inputs = ["gene_constraint", "protein_annotation"]
    params = {}
    dim = 1

    def _gene_scores(self, ctx):
        cached = ctx.cache.get("_tcc_e265_scores")
        if cached is not None:
            return cached

        n = ctx.n_genes
        loeuf = np.full(n, np.nan, dtype=float)
        plen = np.full(n, np.nan, dtype=float)

        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            genes = gc.get("genes", {})
            if "oe_lof_upper" in cols:
                j = cols.index("oe_lof_upper")
                for g, vals in genes.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None:
                        continue
                    v = vals[j] if j < len(vals) else None
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[idx] = fv

        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            cols = pa.get("columns", [])
            genes = pa.get("genes", {})
            if "protein_length" in cols:
                j = cols.index("protein_length")
                for g, vals in genes.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None:
                        continue
                    v = vals[j] if j < len(vals) else None
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            plen[idx] = fv

        # z-score with nan-aware mean/std over genes present
        def zscore(a):
            m = np.isfinite(a)
            if not m.any():
                return np.zeros(n, dtype=float)
            mu = a[m].mean()
            sd = a[m].std()
            out = np.zeros(n, dtype=float)
            if sd > 0:
                out[m] = (a[m] - mu) / sd
            return out

        z_loeuf = zscore(loeuf)
        z_plen = zscore(plen)
        score = z_loeuf - z_plen
        ctx.cache["_tcc_e265_scores"] = score
        return score

    def compute(self, ctx, perts, params):
        score = self._gene_scores(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if idxs:
                val = float(score[idxs].mean())
            else:
                val = 0.0
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
