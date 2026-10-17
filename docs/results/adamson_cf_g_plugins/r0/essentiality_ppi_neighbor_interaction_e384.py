import numpy as np
from genemila.features.api import Feature, register

@register
class EssentialityPpiNeighborInteractionE384(Feature):
    name = "essentiality_ppi_neighbor_interaction_e384"
    version = 1
    description = ("For each (p,g): (1 - LOEUF_g) * ppi_neighbor_mean_delta_e286, "
                   "where LOEUF_g is the gene's LoF intolerance and ppi_neighbor_mean_delta_e286 "
                   "is the mean delta of direct PPI neighbors.")
    rationale = ("Essential (LoF-intolerant) genes may respond more strongly to perturbation "
                 "of their PPI neighbors, so the product captures a synergistic effect.")
    inputs = ["gene_constraint", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Get LOEUF per gene from gene_constraint, imputing median for missing.
        loeuf = np.full(n_genes, np.nan, dtype=np.float64)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None and isinstance(kc, dict):
            genes_map = kc.get("genes") or {}
            cols = kc.get("columns") or []
            try:
                loeuf_idx = list(cols).index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv

        finite_mask = np.isfinite(loeuf)
        if finite_mask.any():
            median_loeuf = float(np.median(loeuf[finite_mask]))
        else:
            median_loeuf = 1.0
        loeuf[~finite_mask] = median_loeuf

        essentiality = 1.0 - loeuf  # (1 - LOEUF_g), shape (n_genes,)

        # Get ppi_neighbor_mean_delta_e286 feature: shape (n_perts, n_genes, 1)
        ppi = ctx.feature("ppi_neighbor_mean_delta_e286", perts)
        ppi = np.asarray(ppi, dtype=np.float64)
        if ppi.ndim == 3:
            ppi = ppi[:, :, 0]
        elif ppi.ndim == 1:
            ppi = ppi[:, None]
        # Ensure shape (n_perts, n_genes)
        if ppi.shape[0] != n_perts:
            ppi = np.tile(ppi.reshape(1, -1), (n_perts, 1))
        if ppi.shape[1] != n_genes:
            # fall back: broadcast/truncate safely
            fixed = np.zeros((n_perts, n_genes), dtype=np.float64)
            m = min(ppi.shape[1], n_genes)
            fixed[:, :m] = ppi[:, :m]
            ppi = fixed

        out = ppi * essentiality[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, None]
