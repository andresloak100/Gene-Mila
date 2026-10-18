import numpy as np
from genemila.features.api import Feature, register


@register
class ATF4ATF6PathwayMembership(Feature):
    name = "atf4_atf6_pathway_membership_e84"
    version = 1
    description = ("Binary feature: 1 if gene g is in any gene set whose name contains "
                   "'ATF4' or 'ATF6' (or is a neighbor of ATF4 in prior_network), else 0.")
    rationale = ("ATF4/ATF6 stress response genes are coordinately regulated and show larger "
                 "perturbation responses, capturing a residual stress module.")
    inputs = ["gene_sets", "prior_network"]
    params = {"include_prior_neighbors": True, "pathway_keywords": ["ATF4", "ATF6"]}
    dim = 1

    def compute(self, ctx, perts, params):
        include_neighbors = bool(params.get("include_prior_neighbors", True))
        keywords = params.get("pathway_keywords", ["ATF4", "ATF6"])
        keywords = [str(k).upper() for k in keywords]

        member = np.zeros(ctx.n_genes, dtype=float)

        # Collect genes from gene sets whose names contain any keyword.
        gene_sets = ctx.knowledge("gene_sets")
        if isinstance(gene_sets, dict):
            for set_name, genes in gene_sets.items():
                if not isinstance(genes, (list, tuple)):
                    continue
                name_upper = str(set_name).upper()
                if any(kw in name_upper for kw in keywords):
                    for g in genes:
                        idx = ctx.gene_index.get(g)
                        if idx is not None:
                            member[idx] = 1.0

        # Optionally include prior_network neighbors of ATF4.
        if include_neighbors:
            prior = ctx.knowledge("prior_network")
            if isinstance(prior, (list, tuple)):
                for entry in prior:
                    if not isinstance(entry, (list, tuple)) or len(entry) < 3:
                        continue
                    a, b = entry[0], entry[1]
                    if a == "ATF4" or b == "ATF4":
                        other = b if a == "ATF4" else a
                        idx = ctx.gene_index.get(other)
                        if idx is not None:
                            member[idx] = 1.0
                        idx = ctx.gene_index.get("ATF4")
                        if idx is not None:
                            member[idx] = 1.0

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = member[np.newaxis, :]
        return out
