import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneControlDistSimE266(Feature):
    name = "target_gene_control_dist_sim_e266"
    version = 1
    description = ("Negative log Jensen-Shannon divergence between control expression "
                   "distributions of the perturbation target and gene g.")
    rationale = ("Genes with similar control expression distributions may be co-regulated "
                 "or share regulatory mechanisms, so perturbing one affects the other.")
    inputs = ["control_cells"]
    params = {"epsilon": 0.001, "n_bins": 32}
    dim = 1

    def compute(self, ctx, perts, params):
        eps = float(params.get("epsilon", 0.001))
        n_bins = int(params.get("n_bins", 32))

        X = np.asarray(ctx.control_cells, dtype=float)
        n_cells, n_genes = X.shape

        # Precompute per-gene histograms over a shared global grid.
        gmin = float(X.min())
        gmax = float(X.max())
        if not np.isfinite(gmin) or not np.isfinite(gmax) or gmax <= gmin:
            gmin, gmax = 0.0, 1.0
        span = gmax - gmin
        edges = gmin + span * np.linspace(0.0, 1.0, n_bins + 1)

        # histograms: (n_genes, n_bins), normalised to probability mass
        hist = np.empty((n_genes, n_bins), dtype=float)
        for j in range(n_genes):
            h, _ = np.histogram(X[:, j], bins=edges)
            s = h.sum()
            if s > 0:
                hist[j] = h / s
            else:
                hist[j] = 1.0 / n_bins
        # smooth to avoid zeros
        hist = hist + 1e-12
        hist = hist / hist.sum(axis=1, keepdims=True)

        # Precompute entropy term per gene for JSD speed
        log_hist = np.log(hist)

        # Cache target histograms per perturbation
        cache = ctx.cache
        if "e266_target_hists" not in cache:
            cache["e266_target_hists"] = {}

        tcache = cache["e266_target_hists"]

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                # no measured target: zero similarity
                out[i, :, 0] = 0.0
                continue

            # average target histogram over target genes
            if p in tcache:
                t_hist = tcache[p]
            else:
                t_hist = hist[t_idx].mean(axis=0)
                t_hist = t_hist + 1e-12
                t_hist = t_hist / t_hist.sum()
                tcache[p] = t_hist

            # JSD between t_hist (1, n_bins) and hist (n_genes, n_bins)
            m = 0.5 * (t_hist[None, :] + hist)  # (n_genes, n_bins)
            log_m = np.log(m)

            # KL(t || m) for each gene
            kl_t = np.sum(t_hist[None, :] * (np.log(t_hist)[None, :] - log_m), axis=1)
            # KL(gene || m)
            kl_g = np.sum(hist * (log_hist - log_m), axis=1)

            jsd = 0.5 * (kl_t + kl_g)
            jsd = np.clip(jsd, 0.0, None)

            sim = -np.log(jsd + eps)
            out[i, :, 0] = sim

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
