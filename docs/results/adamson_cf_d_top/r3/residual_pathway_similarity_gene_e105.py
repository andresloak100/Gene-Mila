import numpy as np
from genemila.features.api import Feature, register


@register
class ResidualPathwaySimilarityGeneE105(Feature):
    name = "residual_pathway_similarity_gene_e105"
    version = 1
    description = (
        "For each gene g, fraction of gene sets containing g that also contain "
        "at least one residual-hub gene (GATA1, NFE2, ATF4, ATF6, globins)."
    )
    rationale = (
        "Residual evidence shows enrichment of GATA1/NFE2/ATF4/ATF6 and globin "
        "pathways; genes sharing curated gene sets with these hubs may share "
        "regulatory responses and show coordinated expression changes."
    )
    inputs = ["gene_sets"]
    params = {
        "hub_genes": ["GATA1", "NFE2", "ATF4", "ATF6",
                      "HBA1", "HBA2", "HBB", "HBG1", "HBG2"]
    }
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # Resolve per-gene similarity vector (cached; independent of p).
        cache_key = "_e105_similarity_vector"
        sim = ctx.cache.get(cache_key)
        if sim is None:
            sim = np.zeros(n_genes, dtype=float)
            try:
                gs = ctx.knowledge("gene_sets")
            except Exception:
                gs = None

            if isinstance(gs, dict):
                hub_genes = set(params.get("hub_genes", []) or [])
                # Only keep hubs that are measured genes.
                hub_idx = set()
                for h in hub_genes:
                    gi = ctx.gene_index.get(h)
                    if gi is not None:
                        hub_idx.add(gi)

                if hub_idx:
                    total_sets = np.zeros(n_genes, dtype=np.int64)
                    hub_sets = np.zeros(n_genes, dtype=np.int64)

                    for _, members in gs.items():
                        if not isinstance(members, (list, tuple, set)):
                            continue
                        idxs = []
                        for m in members:
                            gi = ctx.gene_index.get(m)
                            if gi is not None:
                                idxs.append(gi)
                        if not idxs:
                            continue
                        arr = np.asarray(idxs, dtype=np.int64)
                        total_sets[arr] += 1
                        if hub_idx.intersection(idxs):
                            hub_sets[arr] += 1

                    mask = total_sets > 0
                    sim[mask] = hub_sets[mask] / total_sets[mask]

            sim = np.nan_to_num(sim, nan=0.0, posinf=0.0, neginf=0.0)
            ctx.cache[cache_key] = sim

        # Same gene-level score for every perturbation.
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = sim[None, :]
        return out
