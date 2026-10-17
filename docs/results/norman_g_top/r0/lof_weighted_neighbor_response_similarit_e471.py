import numpy as np
from genemila.features.api import Feature, register


@register
class LofWeightedNeighborResponseSimilarity(Feature):
    name = "lof_weighted_neighbor_response_similarit_e471"
    version = 1
    description = ("Leave-one-out similarity-weighted average of training perturbation deltas "
                   "for gene g, weighting neighbor genes by their response similarity and inverse LOEUF.")
    rationale = ("LoF-intolerant genes have specific strong downstream effects; weighting neighbor "
                 "responses by inverse LOEUF emphasizes informative genes when imputing g's response.")
    inputs = ["train_delta", "knowledge"]
    params = {"similarity_metric": "pearson", "lof_weight_power": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        power = float(params.get("lof_weight_power", 1.0))
        n_genes = ctx.n_genes

        # Build inverse-LOEUF weight vector over genes (default 1.0 when missing).
        inv_lof = np.ones(n_genes, dtype=np.float64)
        try:
            kc = ctx.knowledge("gene_constraint")
        except Exception:
            kc = None
        if kc is not None:
            cols = kc.get("columns", [])
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                genes_tbl = kc.get("genes", {})
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_tbl.get(gname)
                    if vals is None:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v) or v <= 0:
                        continue
                    inv_lof[gi] = 1.0 / v
        # Normalize weights to a reasonable scale (median -> 1) for stability.
        med = np.median(inv_lof)
        if np.isfinite(med) and med > 0:
            inv_lof = inv_lof / med
        if power != 1.0:
            inv_lof = np.power(inv_lof, power)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] == 0:
                continue
            # Exclude p's own target genes from the neighbor set (columns).
            tgt_idx = set(ctx.target_indices(p))
            neighbor_mask = np.ones(n_genes, dtype=bool)
            for t in tgt_idx:
                if 0 <= t < n_genes:
                    neighbor_mask[t] = False

            # Standardize columns (genes) across training perturbations for correlation.
            mu = d.mean(axis=0, keepdims=True)
            sd = d.std(axis=0, keepdims=True)
            sd_safe = np.where(sd > 1e-8, sd, 1.0)
            Z = (d - mu) / sd_safe  # (n_train, n_genes)
            n_train = Z.shape[0]

            # For each query gene g, similarity to every neighbor gene h:
            # corr over training perturbations q. Compute once: C = Z^T Z / n_train.
            C = (Z.T @ Z) / float(n_train)  # (n_genes, n_genes)
            np.clip(C, -1.0, 1.0, out=C)

            # Positive similarities only, weighted by inverse LOEUF of neighbor h.
            W = C * inv_lof[None, :]  # (n_genes, n_genes): W[g,h]
            W = np.where(W > 0, W, 0.0)
            # Zero the diagonal (self) and non-neighbor columns.
            np.fill_diagonal(W, 0.0)
            W[:, ~neighbor_mask] = 0.0

            row_sums = W.sum(axis=1)  # (n_genes,)
            # Weighted average of deltas over training perturbations q, per gene g:
            # pred[g] = sum_h W[g,h] * (mean_q delta[q,h]) / sum_h W[g,h]
            mean_delta = d.mean(axis=0)  # (n_genes,)
            num = W @ mean_delta  # (n_genes,)
            den = row_sums
            pred = np.where(den > 1e-12, num / np.where(den > 1e-12, den, 1.0), 0.0)

            # Fall back to plain mean delta where no neighbors contribute.
            empty = den <= 1e-12
            if np.any(empty):
                pred[empty] = mean_delta[empty]

            out[i, :, 0] = pred

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
