import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufInteractionTargetGene(Feature):
    name = "loeuf_interaction_target_gene_e122"
    version = 1
    description = ("Product (1 - LOEUF_target) * (1 - LOEUF_gene) using gnomAD LoF constraint, "
                   "with missing values imputed by the median LOEUF.")
    rationale = ("LOEUF measures intolerance to loss-of-function. Perturbing an intolerant gene may "
                 "cause larger expression changes, particularly in other intolerant genes; the "
                 "normalised product captures this interaction.")
    inputs = ["knowledge:gene_constraint"]
    params = {"impute": "median"}
    dim = 1

    def _load_loeuf(self, ctx):
        cached = ctx.cache.get("_loeuf_e122")
        if cached is not None:
            return cached

        n = ctx.n_genes
        raw = np.full(n, np.nan, dtype=float)
        knowledge = ctx.knowledge("gene_constraint")
        if knowledge is not None:
            genes_tbl = knowledge.get("genes", {}) or {}
            columns = knowledge.get("columns", []) or []
            try:
                loeuf_idx = list(columns).index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for i, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        raw[i] = fv

        finite = np.isfinite(raw)
        if finite.any():
            med = float(np.median(raw[finite]))
        else:
            med = 1.0
        imputed = np.where(finite, raw, med)
        # (1 - LOEUF), clipped to non-negative
        intol = np.clip(1.0 - imputed, 0.0, None)

        ctx.cache["_loeuf_e122"] = intol
        return intol

    def compute(self, ctx, perts, params):
        intol = self._load_loeuf(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if t_idx:
                t_vals = intol[np.asarray(t_idx, dtype=int)]
                t_intol = float(np.mean(t_vals))
            else:
                # fall back to median intolerance when target is unknown
                t_intol = float(np.median(intol))
            out[i, :, 0] = t_intol * intol

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
