import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetEssentialityE448(Feature):
    name = "additive_response_x_target_essentiality_e448"
    version = 1
    description = ("Product of the additive response prediction and the mean LoF "
                   "intolerance score (1 - LOEUF) of the perturbation's target genes.")
    rationale = ("Perturbations targeting essential (LoF-intolerant) genes are expected "
                 "to produce stronger, more widespread additive responses; scaling the "
                 "additive baseline by target essentiality captures this modulation.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def _essentiality_map(self, ctx):
        cache = ctx.cache
        key = "_e448_ess"
        if key in cache:
            return cache[key]
        ess = {}
        try:
            kn = ctx.knowledge("gene_constraint")
        except Exception:
            kn = None
        if kn is not None:
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    v = vals[idx] if idx < len(vals) else None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    ess[g] = 1.0 - fv
        cache[key] = ess
        return ess

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        ess = self._essentiality_map(ctx)

        # Global fallback: mean essentiality over all genes with a score.
        if ess:
            global_mean = float(np.mean(list(ess.values())))
        else:
            global_mean = 0.0

        for i, p in enumerate(perts):
            # Additive baseline: sum over target genes of each gene's mean
            # training delta (leave-p-out to avoid leakage).
            _, d = ctx.train_delta(exclude=p)
            mean_delta = d.mean(axis=0)  # (n_genes,)

            t_idx = ctx.target_indices(p)
            additive = np.zeros(ctx.n_genes, dtype=float)
            if t_idx:
                additive = mean_delta[t_idx].sum(axis=0)

            # Mean essentiality over the perturbation's target genes.
            t_genes = ctx.target_genes(p)
            scores = [ess[g] for g in t_genes if g in ess]
            if scores:
                ess_score = float(np.mean(scores))
            else:
                ess_score = global_mean

            out[i, :, 0] = additive * ess_score

        # Guarantee finiteness.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
