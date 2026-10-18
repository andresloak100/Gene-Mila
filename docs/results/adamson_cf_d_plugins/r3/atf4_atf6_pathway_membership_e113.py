import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class Atf4Atf6PathwayMembershipE113(Feature):
    name = "atf4_atf6_pathway_membership_e113"
    version = 1
    description = "Binary feature: 1 if gene g belongs to any gene set whose name contains 'ATF4' or 'ATF6', else 0."
    rationale = ("ATF4/ATF6 are master regulators of the integrated stress response and unfolded "
                 "protein response, driving large transcriptional changes.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_genes = ctx.n_genes
        vec = np.zeros(n_genes, dtype=float)

        gs = ctx.knowledge("gene_sets")
        if gs:
            cache = ctx.cache
            key = "atf4_atf6_membership_vec_e113"
            cached = cache.get(key)
            if cached is not None and cached.shape[0] == n_genes:
                vec = cached.copy()
            else:
                gene_index = ctx.gene_index
                for set_name, members in gs.items():
                    if not isinstance(set_name, str):
                        continue
                    if ("ATF4" in set_name) or ("ATF6" in set_name):
                        if not members:
                            continue
                        for g in members:
                            idx = gene_index.get(g)
                            if idx is not None:
                                vec[idx] = 1.0
                cache[key] = vec.copy()

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        return out
