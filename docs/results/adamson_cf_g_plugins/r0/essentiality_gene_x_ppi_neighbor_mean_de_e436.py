import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityGeneXPpiNeighborMeanDeltaE436(Feature):
    name = "essentiality_gene_x_ppi_neighbor_mean_de_e436"
    version = 1
    description = (
        "For each (p,g): (1 - LOEUF_gene) * ppi_neighbor_mean_delta_e286, "
        "modulating the PPI neighbor mean delta by gene essentiality."
    )
    rationale = (
        "Essential genes may have stronger coupling to their interaction partners; "
        "the neighbor response may be more informative for essential genes."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Compute the base PPI neighbor mean delta feature (leave-one-out safe).
        base = ctx.feature("ppi_neighbor_mean_delta_e286", perts, params=None)
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        base = base[:, :, 0]

        # Load LOEUF (oe_lof_upper) from gene_constraint knowledge.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_map = kc.get("genes", {})
            columns = kc.get("columns", [])
            try:
                loeuf_idx = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for gi, gene in enumerate(ctx.genes):
                    vals = genes_map.get(gene)
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

        # Essentiality = 1 - LOEUF; missing LOEUF -> treat as non-essential (0).
        ess = np.where(np.isfinite(loeuf), 1.0 - loeuf, 0.0)
        ess = np.clip(ess, 0.0, 1.0)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        out[:, :, 0] = base * ess[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
