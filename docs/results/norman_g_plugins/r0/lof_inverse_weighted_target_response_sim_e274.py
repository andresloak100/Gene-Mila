import numpy as np
from genemila.features.api import Feature, register


@register
class LofInverseWeightedTargetResponseSimE274(Feature):
    name = "lof_inverse_weighted_target_response_sim_e274"
    version = 1
    description = ("target_response_similarity_to_mean_e110 multiplied by a per-perturbation "
                   "weight derived from target-gene LoF constraint (1-LOEUF or pLI).")
    rationale = ("LoF-intolerant (low LOEUF / high pLI) targets may be more tightly regulated, "
                 "so their perturbation responses are more informative; weighting the "
                 "target-to-mean response similarity by target constraint may improve prediction.")
    inputs = ["gene_constraint", "target_response_similarity_to_mean_e110"]
    params = {"metric": "1-loeuf"}
    dim = 1

    def _constraint_weights(self, ctx, params):
        cache = ctx.cache
        key = ("e274_constraint", params.get("metric", "1-loeuf"))
        if key in cache:
            return cache[key]

        metric = params.get("metric", "1-loeuf")
        n = ctx.n_genes
        w = np.full(n, np.nan, dtype=float)
        have = np.zeros(n, dtype=bool)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_tab = kc.get("genes", {})
            # locate columns
            idx_loeuf = None
            idx_pli = None
            for j, c in enumerate(cols):
                cl = str(c).lower()
                if cl == "oe_lof_upper" or "loeuf" in cl:
                    idx_loeuf = j
                if cl == "pli" or cl.endswith("_pli") or cl == "p_li":
                    idx_pli = j
            if idx_loeuf is None:
                for j, c in enumerate(cols):
                    if "oe_lof" in str(c).lower():
                        idx_loeuf = j
                        break
            if idx_pli is None:
                for j, c in enumerate(cols):
                    if "pli" in str(c).lower():
                        idx_pli = j
                        break

            use_loeuf = "loeuf" in metric.lower()
            col_idx = idx_loeuf if use_loeuf else idx_pli
            if col_idx is None:
                col_idx = idx_loeuf if idx_loeuf is not None else idx_pli

            if col_idx is not None:
                for g, j in ctx.gene_index.items():
                    vals = genes_tab.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    if use_loeuf:
                        w[j] = 1.0 - fv
                    else:
                        w[j] = fv
                    have[j] = True

        # impute missing with median of observed
        if have.any():
            med = float(np.median(w[have]))
            w[~have] = med
        else:
            w[:] = 1.0

        cache[key] = w
        return w

    def compute(self, ctx, perts, params):
        base = ctx.feature("target_response_similarity_to_mean_e110", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        w_gene = self._constraint_weights(ctx, params)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                w = 1.0
            else:
                w = float(np.mean(w_gene[tgt]))
            out[i, :, 0] = base[i, :, 0] * w

        out[~np.isfinite(out)] = 0.0
        return out
