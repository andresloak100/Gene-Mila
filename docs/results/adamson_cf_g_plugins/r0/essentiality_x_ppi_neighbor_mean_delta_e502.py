import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityXPPINeighborMeanDelta(Feature):
    name = "essentiality_x_ppi_neighbor_mean_delta_e502"
    version = 1
    description = (
        "For each (p,g): (1 - LOEUF_target) * ppi_neighbor_mean_delta_e286, "
        "i.e. the PPI-neighbour mean delta scaled by target essentiality."
    )
    rationale = (
        "Essential targets are network hubs; their perturbation likely propagates "
        "more strongly through PPI neighbours, so scaling the neighbour mean delta "
        "by (1 - LOEUF) of the target should sharpen the signal."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Base PPI-neighbour mean delta feature (leave-one-out handled internally).
        ppi = ctx.feature(
            "ppi_neighbor_mean_delta_e286",
            perts,
            params=None,
        )
        ppi = np.asarray(ppi, dtype=float)
        if ppi.ndim == 3:
            ppi = ppi[:, :, 0]
        elif ppi.ndim == 1:
            ppi = ppi.reshape(n_perts, n_genes)

        # Load LOEUF from gene_constraint prior knowledge.
        constraint = ctx.knowledge("gene_constraint")
        loeuf = np.full(n_genes, np.nan, dtype=float)
        if constraint is not None:
            genes_map = constraint.get("genes", {}) or {}
            columns = constraint.get("columns", []) or []
            try:
                loeuf_idx = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, name in enumerate(ctx.genes):
                    vals = genes_map.get(name)
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
                        loeuf[g] = fv

        # Default LOEUF for genes without constraint data: treat as non-essential
        # (1 - LOEUF = 0), so no spurious scaling.
        loeuf_filled = np.where(np.isfinite(loeuf), loeuf, 1.0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                scale = 0.0
            else:
                # Average essentiality signal over measured targets.
                vals = loeuf_filled[tgt_idx]
                loeuf_t = float(np.mean(vals))
                scale = 1.0 - loeuf_t
                if not np.isfinite(scale):
                    scale = 0.0
            row = ppi[i]
            if not np.all(np.isfinite(row)):
                row = np.nan_to_num(row, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = scale * row

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
