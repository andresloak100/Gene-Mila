import numpy as np
from genemila.features.api import Feature, register


@register
class LofWeightedRandomProjection(Feature):
    name = "lof_weighted_random_projection_e478"
    version = 1
    description = ("Random projection of a LOEUF-weighted gene response-similarity "
                   "matrix, aggregated over a perturbation's targets.")
    rationale = ("Weighting response-similarity columns by inverse LOEUF emphasises "
                 "constrained (informative) genes; a fixed Gaussian projection yields "
                 "a robust low-dimensional summary of the target genes' similarity.")
    inputs = ["train_delta", "knowledge"]
    params = {"n_components": 10, "random_seed": 42}
    dim = 10

    def _lof_weights(self, ctx):
        if "_lof_w" in ctx.cache:
            return ctx.cache["_lof_w"]
        w = np.zeros(ctx.n_genes, dtype=np.float64)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            genes = kn.get("genes", {})
            cols = kn.get("columns", [])
            if "oe_lof_upper" in cols:
                j = cols.index("oe_lof_upper")
                for i, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v) or v <= 0:
                        continue
                    w[i] = 1.0 / v
        # normalise so scale is stable; zero stays zero
        mx = w.max()
        if mx > 0:
            w = w / mx
        ctx.cache["_lof_w"] = w
        return w

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        k = int(params.get("n_components", 10))
        seed = int(params.get("random_seed", 42))
        k = max(1, k)

        w = self._lof_weights(ctx)

        # fixed Gaussian projection matrix: (n_genes, k)
        rng = np.random.RandomState(seed)
        R = rng.standard_normal((n_genes, k)).astype(np.float64)
        R /= np.sqrt(k)

        out = np.zeros((len(perts), n_genes, k), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] < 2:
                continue
            # similarity of response vectors between genes: (n_genes, n_genes)
            X = d.astype(np.float64)
            X = X - X.mean(axis=0, keepdims=True)
            sd = X.std(axis=0)
            sd[sd <= 0] = 1.0
            X = X / sd
            S = (X.T @ X) / float(X.shape[0])

            # weight columns by inverse LOEUF
            SW = S * w[np.newaxis, :]
            # random projection -> (n_genes, k)
            P = SW @ R

            # aggregate over the perturbation's targets (order-invariant mean)
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                proj = P.mean(axis=0)
            else:
                proj = P[np.asarray(tgt, dtype=int)].mean(axis=0)
            out[i, :, :] = proj[np.newaxis, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
