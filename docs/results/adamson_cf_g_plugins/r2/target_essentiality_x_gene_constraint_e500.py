import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityXGeneConstraint(Feature):
    name = "target_essentiality_x_gene_constraint_e500"
    version = 1
    description = (
        "Product of target essentiality proxy (1 - target LOEUF) and gene "
        "constraint proxy (1 - gene LOEUF) from gnomAD LoF constraint."
    )
    rationale = (
        "Essential genes and LoF-intolerant genes are both under strong selective "
        "pressure; perturbing a constrained target may disproportionately affect "
        "constrained genes via shared essential pathways."
    )
    inputs = ["knowledge", "target_indices"]
    params = {"loeuf_impute": "median"}
    dim = 1

    def _load_loeuf(self, ctx):
        cached = ctx.cache.get("e500_loeuf")
        if cached is not None:
            return cached
        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            genes_map = kn.get("genes", {}) or {}
            if idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    if idx < len(vals):
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                loeuf[gi] = fv
        ctx.cache["e500_loeuf"] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        loeuf = self._load_loeuf(ctx)
        impute = params.get("loeuf_impute", "median") if params else "median"
        finite = loeuf[np.isfinite(loeuf)]
        if finite.size > 0:
            fill = np.median(finite) if impute == "median" else float(finite.mean())
        else:
            fill = 1.0
        loeuf_f = np.where(np.isfinite(loeuf), loeuf, fill)
        # clip to sane positive range
        loeuf_f = np.clip(loeuf_f, 1e-6, None)
        gene_constraint = 1.0 - loeuf_f  # higher = more constrained

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                # no measured target: use mean target constraint as neutral value
                t_cons = float(np.mean(gene_constraint))
            else:
                t_cons = float(np.mean(gene_constraint[tidx]))
            out[i, :, 0] = t_cons * gene_constraint
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
