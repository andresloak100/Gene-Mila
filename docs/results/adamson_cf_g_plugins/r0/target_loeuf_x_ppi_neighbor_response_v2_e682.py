import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLoeufXPpiNeighborResponseV2E682(Feature):
    name = "target_loeuf_x_ppi_neighbor_response_v2_e682"
    version = 1
    description = "Product of (1 - LOEUF of perturbation target) and the PPI-neighbor mean response of the target."
    rationale = "Essential targets (low LOEUF) with responsive PPI neighbors may drive stronger downstream effects."
    inputs = ["gene_constraint", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Get the existing neighbor-response feature (target_ppi_neighbor_mean_response_e611_e605)
        try:
            neigh = ctx.feature("target_ppi_neighbor_mean_response_e611_e605", perts, None)
        except Exception:
            neigh = None

        # Load LOEUF from gene_constraint
        constraint = ctx.knowledge("gene_constraint")
        loeuf_map = {}
        if constraint is not None and isinstance(constraint, dict):
            genes = constraint.get("genes", {})
            columns = constraint.get("columns", [])
            try:
                loeuf_idx = columns.index("oe_lof_upper")
            except (ValueError, AttributeError):
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        loeuf_map[g] = float(v)

        for i, p in enumerate(perts):
            # Determine target gene(s) for perturbation p
            tgenes = ctx.target_genes(p)
            loeuf_val = None
            for tg in tgenes:
                if tg in loeuf_map:
                    loeuf_val = loeuf_map[tg]
                    break
            if loeuf_val is None:
                factor = 1.0  # fallback: treat as fully essential-neutral
            else:
                factor = 1.0 - loeuf_val
                if not np.isfinite(factor):
                    factor = 1.0

            if neigh is not None:
                row = np.asarray(neigh[i, :, 0], dtype=float)
                row = np.where(np.isfinite(row), row, 0.0)
                out[i, :, 0] = factor * row
            else:
                out[i, :, 0] = 0.0

        out = np.where(np.isfinite(out), out, 0.0)
        return out
