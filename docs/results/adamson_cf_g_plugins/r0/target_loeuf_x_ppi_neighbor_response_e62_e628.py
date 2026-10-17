import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXPpiNeighborResponse(Feature):
    name = "target_loeuf_x_ppi_neighbor_response_e62_e628"
    version = 1
    description = ("For each (p,g), product of (1 - LOEUF of perturbation target) and "
                   "target_ppi_neighbor_mean_response_e611_e605.")
    rationale = ("Combines target essentiality (LOEUF) with the network-propagated neighbor "
                 "response of the target, capturing condition-dependent essentiality effects "
                 "on network propagation.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        G = ctx.n_genes
        out = np.zeros((n, G, 1))

        # Load gene_constraint knowledge for LOEUF
        gc = ctx.knowledge("gene_constraint")
        loeuf_map = {}
        if gc is not None:
            cols = gc.get("columns", [])
            genes_tbl = gc.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    v = vals[idx]
                    if v is not None:
                        loeuf_map[sym] = float(v)

        # Get neighbor response feature (composition)
        try:
            neigh = ctx.feature("target_ppi_neighbor_mean_response_e611_e605", perts, None)
        except Exception:
            neigh = None

        if neigh is not None:
            neigh = np.asarray(neigh, dtype=float)
            if neigh.ndim == 3:
                neigh = neigh[:, :, 0]
            elif neigh.ndim != 2:
                neigh = None

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            ess = 0.0
            if tgenes:
                vals = [1.0 - loeuf_map[t] for t in tgenes if t in loeuf_map]
                if vals:
                    ess = float(np.mean(vals))
            if neigh is not None:
                out[i, :, 0] = ess * neigh[i, :]
            else:
                out[i, :, 0] = 0.0

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
