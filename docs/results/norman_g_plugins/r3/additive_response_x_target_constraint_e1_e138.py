import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetConstraintE1E138(Feature):
    name = "additive_response_x_target_constraint_e1_e138"
    version = 1
    description = "Product of additive_response and a normalized LoF-intolerance score of the target gene(s)."
    rationale = ("The effect of the additive baseline on a gene's delta depends on how LoF-intolerant "
                 "the perturbation's target is; targets that are intolerant may produce stronger "
                 "downstream activation effects.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _constraint_scores(self, ctx):
        """Normalized LoF-intolerance score per gene (higher = more intolerant), in [0,1]."""
        cache = ctx.cache
        if "_e1_constraint" in cache:
            return cache["_e1_constraint"]
        n = ctx.n_genes
        score = np.zeros(n, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            genes = kn.get("genes", {})
            cols = kn.get("columns", [])
            # prefer LOEUF (oe_lof_upper); low LOEUF = intolerant
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
            elif "pLI" in cols:
                idx = cols.index("pLI")
            else:
                idx = None
            if idx is not None:
                vals = np.full(n, np.nan, dtype=float)
                for g, gi in ctx.gene_index.items():
                    row = genes.get(g)
                    if row is None:
                        continue
                    v = row[idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        vals[gi] = v
                # convert to intolerance
                if cols[idx] == "oe_lof_upper":
                    # low LOEUF -> intolerant
                    valid = np.isfinite(vals)
                    if valid.any():
                        lo = np.nanmin(vals[valid])
                        hi = np.nanmax(vals[valid])
                        if hi > lo:
                            score[valid] = (hi - vals[valid]) / (hi - lo)
                        else:
                            score[valid] = 0.0
                else:  # pLI: high -> intolerant
                    valid = np.isfinite(vals)
                    if valid.any():
                        lo = np.nanmin(vals[valid])
                        hi = np.nanmax(vals[valid])
                        if hi > lo:
                            score[valid] = (vals[valid] - lo) / (hi - lo)
                        else:
                            score[valid] = 0.0
        cache["_e1_constraint"] = score
        return score

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        constraint = self._constraint_scores(ctx)

        # additive_response baseline: sum over targets of each gene's mean training delta
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)  # (n_genes,)

            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                score = 0.0
            else:
                score = float(np.mean(constraint[np.asarray(tgt_idx, dtype=int)]))

            out[i, :, 0] = add * score
        return out
