import numpy as np
from genemila.features.api import Feature, register

@register
class GeneIsHistoneE213(Feature):
    name = "gene_is_histone_e213"
    version = 1
    description = "Binary indicator: 1 if gene g's symbol starts with 'HIST' or is in a histone gene set, else 0."
    rationale = ("Histone genes are co-regulated and their expression changes are under-predicted "
                 "by current features; a binary histone-cluster membership indicator may capture this.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        is_histone = np.zeros(n_genes, dtype=float)

        # 1) symbol prefix rule
        for j, g in enumerate(ctx.genes):
            if isinstance(g, str) and g.upper().startswith("HIST"):
                is_histone[j] = 1.0

        # 2) gene set rule from prior knowledge
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            gene_index = ctx.gene_index
            for set_name, members in gs.items():
                if not isinstance(set_name, str):
                    continue
                if "histone" not in set_name.lower():
                    continue
                if not isinstance(members, (list, tuple)):
                    continue
                for sym in members:
                    j = gene_index.get(sym)
                    if j is not None:
                        is_histone[j] = 1.0

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = is_histone[None, :]
        return out
