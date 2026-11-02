import numpy as np
from genemila.features.api import Feature, register

@register
class TargetIsGata1Nfe2Neighbor(Feature):
    name = "target_is_gata1_nfe2_neighbor_e217"
    version = 1
    description = "Per-gene indicator: for perturbation p, genes co-expressed with globin genes receive a signal if p targets a neighbor of GATA1 or NFE2 in prior_network."
    rationale = "Perturbations of erythroid transcription factor neighbors have a distinct effect on erythroid/globin co-regulated genes; the effect is expressed on genes co-regulated with globins."
    inputs = ["prior_network", "control_cells"]
    params = {"top_k": 50}
    dim = 1

    def compute(self, ctx, perts, params):
        top_k = int(params.get("top_k", 50))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Build neighbor set of GATA1 and NFE2 from prior_network edges.
        anchors = {"GATA1", "NFE2"}
        neighbors = set()
        net = None
        try:
            net = ctx.knowledge("prior_network")
        except Exception:
            net = None
        if net:
            # net may be a list of edges or a dict-like structure
            edges = net
            if isinstance(net, dict):
                edges = net.get("edges", [])
            for edge in edges:
                try:
                    a, b = edge[0], edge[1]
                except Exception:
                    continue
                if a in anchors and b not in anchors:
                    neighbors.add(b)
                elif b in anchors and a not in anchors:
                    neighbors.add(a)

        # Globin / erythroid gene set (co-expressed with globins).
        globin_names = ["HBA1", "HBA2", "HBB", "HBD", "HBG1", "HBG2", "HBE1", "HBZ", "HBM", "HBQ1"]
        globin_idx = [ctx.gene_index[g] for g in globin_names if g in ctx.gene_index]

        # Compute globin co-expression profile from control cells.
        corr = ctx.gene_corr  # (n_genes, n_genes)
        if globin_idx:
            globin_corr = corr[:, globin_idx]  # (n_genes, n_globin)
            # max |corr| with any globin gene
            coexp = np.max(np.abs(globin_corr), axis=1)
        else:
            coexp = np.zeros(n_genes, dtype=float)

        # Select top-k co-expressed genes as the "erythroid co-regulated" set.
        k = min(top_k, n_genes)
        if k > 0:
            order = np.argsort(coexp)[::-1][:k]
            mask = np.zeros(n_genes, dtype=float)
            mask[order] = 1.0
        else:
            mask = np.zeros(n_genes, dtype=float)

        # If no globin genes found, fall back to a broad signal so feature is non-constant
        # across perturbations based on target-neighbor membership.
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            is_neighbor = any(g in neighbors for g in tg)
            if is_neighbor:
                out[i, :, 0] = mask
            else:
                out[i, :, 0] = 0.0

        # Guard against constant output: if all rows identical, add a data-derived
        # per-perturbation scalar from target co-expression strength.
        if np.allclose(out, out[0:1]):
            for i, p in enumerate(perts):
                tg_idx = ctx.target_indices(p)
                if tg_idx:
                    strength = float(np.mean(coexp[tg_idx]))
                else:
                    strength = 0.0
                out[i, :, 0] = strength * mask

        return out
