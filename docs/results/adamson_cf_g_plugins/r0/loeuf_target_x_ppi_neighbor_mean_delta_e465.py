import numpy as np
from genemila.features.api import Feature, register

@register
class LoeufTargetXPpiNeighborMeanDelta(Feature):
    name = "loeuf_target_x_ppi_neighbor_mean_delta_e465"
    version = 1
    description = "Product of (1 - LOEUF_target) and ppi_neighbor_mean_delta_e286 for each (p,g)."
    rationale = ("The influence of PPI neighbor mean delta on gene response depends on the "
                 "target's loss-of-function intolerance: essential targets may propagate "
                 "perturbations through protein interactions more strongly.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Base ppi neighbor mean delta feature
        ppi = ctx.feature("ppi_neighbor_mean_delta_e286", perts)
        if ppi.ndim == 3:
            ppi = ppi[:, :, 0]
        else:
            ppi = ppi.reshape(n_perts, n_genes)

        # Load LOEUF values
        constraint = ctx.knowledge("gene_constraint")
        loeuf = np.full(n_genes, np.nan, dtype=float)
        if constraint is not None:
            cols = constraint.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            genes_map = constraint.get("genes", {})
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is not None and len(vals) > idx and vals[idx] is not None:
                        try:
                            loeuf[gi] = float(vals[idx])
                        except (TypeError, ValueError):
                            pass

        # Default for missing LOEUF: assume non-intolerant (1 - LOEUF = 0)
        intol = np.where(np.isfinite(loeuf), 1.0 - loeuf, 0.0)
        # Clamp to [0,1] for safety
        intol = np.clip(intol, 0.0, 1.0)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                # No measured target -> factor 0
                continue
            # Average intolerance over targets (usually one)
            t_intol = float(np.mean(intol[t_idx]))
            out[i, :, 0] = t_intol * ppi[i, :]

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
