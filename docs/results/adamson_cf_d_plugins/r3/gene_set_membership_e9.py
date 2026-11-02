import numpy as np
from genemila.features.api import Feature, register


@register
class GeneSetMembershipE9(Feature):
    name = "gene_set_membership_e9"
    version = 1
    description = "Binary membership of each gene in selected enriched gene sets."
    rationale = ("Genes in the same functional gene set (stress/erythroid pathways) are "
                 "co-regulated and respond similarly to perturbations; membership marks them.")
    inputs = ["gene_sets"]
    params = {"sets": ["GOBP:carbon dioxide transport",
                       "REACTOME:ATF6 (ATF6-alpha) activates chaperones"]}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        membership = np.zeros(n_genes, dtype=float)

        gs = ctx.knowledge("gene_sets")
        set_names = params.get("sets", self.params["sets"])

        if isinstance(gs, dict):
            for name in set_names:
                genes = gs.get(name)
                if not genes:
                    continue
                for g in genes:
                    idx = ctx.gene_index.get(g)
                    if idx is not None:
                        membership[idx] = 1.0

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = membership[None, :]
        return out
