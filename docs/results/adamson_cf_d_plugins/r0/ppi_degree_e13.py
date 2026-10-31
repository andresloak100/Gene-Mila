import numpy as np
from genemila.features.api import Feature, register

@register
class PPIDegreeE13(Feature):
    name = "ppi_degree_e13"
    version = 1
    description = "Number of interaction partners for gene g in ppi_network."
    rationale = ("Hub genes are under tighter regulatory control and show smaller "
                 "expression changes upon perturbation; degree captures this buffering.")
    inputs = ["ppi_network"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        net = ctx.knowledge("ppi_network")
        if not net:
            return out

        degree = {}
        for entry in net:
            try:
                a, b = entry[0], entry[1]
            except (IndexError, TypeError):
                continue
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1

        col = np.zeros(ctx.n_genes, dtype=float)
        for g, idx in ctx.gene_index.items():
            d = degree.get(g)
            if d is not None:
                col[idx] = float(d)

        out[:, :, 0] = col[None, :]
        return out
