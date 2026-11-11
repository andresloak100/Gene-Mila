import numpy as np
from genemila.features.api import Feature, register


@register
class CoexpressionTransferE9(Feature):
    name = "coexpression_transfer_e9"
    version = 1
    description = (
        "Correlation-weighted average of training delta responses across genes: "
        "for gene g, sum_h C[g,h]*delta[p,h] / sum_h |C[g,h]|, using control-cell "
        "gene correlation C, with thresholding of weak correlations."
    )
    rationale = (
        "Co-expressed genes often share regulatory programs and respond similarly to "
        "perturbations; transferring responses across correlated genes borrows strength "
        "from co-regulated genes and captures shared perturbation responses."
    )
    inputs = ["train_delta", "gene_corr"]
    params = {"threshold": 0.1}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("threshold", 0.1))
        n_genes = ctx.n_genes

        # Build the correlation weight matrix once (cached).
        key = ("coexp_transfer_e9", threshold, n_genes)
        cache = ctx.cache
        if key not in cache:
            corr = np.asarray(ctx.gene_corr, dtype=np.float64)
            # Threshold: zero out weak correlations (keep diagonal for stability).
            w = np.where(np.abs(corr) >= threshold, corr, 0.0)
            # Normaliser: sum of |weights| per gene g (row).
            denom = np.abs(w).sum(axis=1)
            # Avoid division by zero; fall back to identity-like normalisation.
            denom = np.where(denom > 0.0, denom, 1.0)
            cache[key] = (w, denom)
        w, denom = cache[key]

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            d = np.asarray(d, dtype=np.float64)
            if d.shape[0] == 0:
                continue
            mean_delta = d.mean(axis=0)  # (n_genes,)
            # Weighted transfer: out[g] = sum_h w[g,h]*mean_delta[h] / denom[g]
            out[i, :, 0] = (w @ mean_delta) / denom

        # Ensure finite values.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
