import numpy as np
from genemila.features.api import Feature, register


@register
class TargetExpressionVarianceTimesAdditiveE596(Feature):
    name = "target_expression_variance_times_additiv_e596"
    version = 1
    description = ("Mean variance of expression across tissues/cell lines for p's target genes, "
                   "multiplied by additive_response.")
    rationale = ("Targets with high expression variance across tissues may be more responsive to "
                 "perturbation due to regulatory plasticity; scaling the additive baseline by this "
                 "plasticity captures target-dependent responsiveness.")
    inputs = ["control_cells", "gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def _variance_scores(self, ctx):
        cached = ctx.cache.get("_tev596_scores")
        if cached is not None:
            return cached

        n_genes = ctx.n_genes

        # Prefer a prior knowledge expression-variance table if present; otherwise
        # derive a per-gene variance proxy from control cells (variance across the
        # measured cell population), which is always available.
        scores = None
        for name in ("gtex", "ccle", "expression_variance", "tissue_expression"):
            try:
                kn = ctx.knowledge(name)
            except Exception:
                kn = None
            if kn is None:
                continue
            genes = kn.get("genes") if isinstance(kn, dict) else None
            if not isinstance(genes, dict) or len(genes) == 0:
                continue
            vals = np.full(n_genes, np.nan, dtype=float)
            for g, v in genes.items():
                idx = ctx.gene_index.get(g)
                if idx is None:
                    continue
                try:
                    arr = np.asarray(v, dtype=float).ravel()
                except Exception:
                    continue
                if arr.size == 0:
                    continue
                arr = arr[np.isfinite(arr)]
                if arr.size == 0:
                    continue
                vals[idx] = float(np.var(arr))
            if np.isfinite(vals).any():
                scores = vals
                break

        if scores is None:
            # Fallback: control-cell expression variance per gene.
            cm = np.asarray(ctx.control_cells, dtype=float)
            if cm.ndim == 2 and cm.shape[1] == n_genes and cm.shape[0] > 1:
                scores = np.var(cm, axis=0)
            else:
                scores = np.zeros(n_genes, dtype=float)

        # Fill missing entries with the mean of observed values.
        finite = np.isfinite(scores)
        if finite.any():
            fill = float(np.mean(scores[finite]))
        else:
            fill = 0.0
        scores = np.where(finite, scores, fill)
        scores = np.maximum(scores, 0.0)

        ctx.cache["_tev596_scores"] = scores
        return scores

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        scores = self._variance_scores(ctx)

        # Additive baseline prediction.
        try:
            additive = np.asarray(
                ctx.feature("additive_response", perts), dtype=float
            )
        except Exception:
            additive = None
        if additive is None or additive.shape[0] != len(perts):
            additive = np.zeros((len(perts), n_genes, 1), dtype=float)
        if additive.ndim == 2:
            additive = additive[:, :, None]
        if additive.ndim == 1:
            additive = additive[:, None, None]
        if additive.shape[1] != n_genes:
            tmp = np.zeros((additive.shape[0], n_genes, additive.shape[2]), dtype=float)
            m = min(additive.shape[1], n_genes)
            tmp[:, :m, :] = additive[:, :m, :]
            additive = tmp

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                continue
            tv = scores[np.asarray(tgt, dtype=int)]
            mean_var = float(np.mean(tv)) if tv.size else 0.0
            out[i, :, 0] = mean_var * additive[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
