import numpy as np
from genemila.features.api import Feature, register


@register
class GeneCorrTransferE27(Feature):
    name = "gene_corr_transfer_e27"
    version = 1
    description = (
        "Correlation-weighted average of training deltas: for each gene g, "
        "average the mean training response of its top-k most correlated "
        "control genes, weighted by their control-cell Pearson correlation."
    )
    rationale = (
        "Co-expressed genes often share regulatory programs and thus "
        "perturbation responses; transferring the response via gene_corr "
        "similarity captures co-expression structure."
    )
    inputs = ["gene_corr", "train_delta"]
    params = {"k": 50}
    dim = 1

    def compute(self, ctx, perts, params):
        k = int(params.get("k", 50))
        n_genes = ctx.n_genes
        corr = np.asarray(ctx.gene_corr, dtype=np.float64)
        # Clean correlation matrix: finite, off-diagonal.
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(corr, 0.0)

        k = max(1, min(k, n_genes - 1))

        # Precompute top-k indices and their (positive) weights per gene.
        # Use partial sort per row via argpartition for speed.
        key = "e27_topk_%d_%d" % (k, n_genes)
        cached = ctx.cache.get(key)
        if cached is None:
            idx = np.argpartition(-corr, k - 1, axis=1)[:, :k]  # (n_genes, k)
            rows = np.arange(n_genes)[:, None]
            w = corr[rows, idx]
            w = np.clip(w, 0.0, None)  # keep only positive correlations
            wsum = w.sum(axis=1, keepdims=True)
            # Fallback to uniform weights where no positive corr exists.
            uniform = np.full_like(w, 1.0 / k)
            safe = wsum[:, 0] > 1e-12
            w_norm = np.where(safe[:, None], w / np.maximum(wsum, 1e-12), uniform)
            ctx.cache[key] = (idx, w_norm)
        else:
            idx, w_norm = cached

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            d = np.asarray(d, dtype=np.float64)
            if d.size == 0:
                continue
            mean_delta = d.mean(axis=0)  # (n_genes,)
            # Gather top-k neighbours' mean responses and weighted-average.
            neighbour_vals = mean_delta[idx]  # (n_genes, k)
            out[i, :, 0] = (neighbour_vals * w_norm).sum(axis=1)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
