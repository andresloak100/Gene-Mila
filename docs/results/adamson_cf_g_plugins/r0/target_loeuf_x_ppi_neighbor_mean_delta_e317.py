import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXPpiNeighborMeanDeltaE317(Feature):
    name = "target_loeuf_x_ppi_neighbor_mean_delta_e317"
    version = 1
    description = "Product of (1 - LOEUF_target) and ppi_neighbor_mean_delta_e286."
    rationale = (
        "Essential genes (low LOEUF) are often PPI hubs; scaling the neighbor "
        "response by target essentiality captures how perturbation propagation "
        "depends on target essentiality."
    )
    inputs = ["gene_constraint", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # LOEUF lookup (oe_lof_upper) from gene_constraint
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_map = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                loeuf_idx = list(cols).index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    v = vals[loeuf_idx] if loeuf_idx < len(vals) else None
                    if v is not None:
                        try:
                            loeuf[gi] = float(v)
                        except (TypeError, ValueError):
                            pass

        # ppi_neighbor_mean_delta_e286 feature
        ppi_feat = ctx.feature(
            "ppi_neighbor_mean_delta_e286", perts, params=None
        )
        ppi_feat = np.asarray(ppi_feat, dtype=float)
        if ppi_feat.ndim == 2:
            ppi_feat = ppi_feat[:, :, None]
        if ppi_feat.shape[1] != n_genes:
            # Fallback: broadcast/trim safely
            tmp = np.zeros((n_perts, n_genes, 1), dtype=float)
            g = min(n_genes, ppi_feat.shape[1])
            tmp[:, :g, :] = ppi_feat[:, :g, :]
            ppi_feat = tmp

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            # Target LOEUF: average over targets (usually one)
            vals = []
            for gi in tgt_idx:
                v = loeuf[gi]
                if np.isfinite(v):
                    vals.append(v)
            if vals:
                loeuf_t = float(np.mean(vals))
                ess = 1.0 - loeuf_t
            else:
                # Unknown essentiality -> neutral (no scaling)
                ess = 1.0
            out[i, :, 0] = ess * ppi_feat[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
