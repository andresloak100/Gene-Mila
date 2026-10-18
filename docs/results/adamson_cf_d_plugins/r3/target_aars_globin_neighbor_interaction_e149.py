import numpy as np
from genemila.features.api import Feature, register

# Curated aminoacyl-tRNA synthetase gene symbols (human cytoplasmic + mitochondrial).
_AARS_GENES = {
    "AARS", "AARS2", "CARS", "CARS2", "DARS", "DARS2", "EARS2", "FARS2", "FARSA",
    "FARSB", "GARS", "HARS", "HARS2", "IARS", "IARS2", "KARS", "LARS", "LARS2",
    "MARS", "MARS2", "NARS", "NARS2", "PARS2", "QARS", "RARS", "RARS2", "SARS",
    "SARS2", "TARS", "TARS2", "VARS", "VARS2", "WARS", "WARS2", "YARS", "YARS2",
    "EPRS", "MARS1", "KARS1", "GARS1", "CARS1", "DARS1", "NARS1", "RARS1",
    "SARS1", "TARS1", "VARS1", "WARS1", "YARS1", "IARS1", "LARS1", "HARS1",
    "FARS1", "QARS1", "AARS1",
}

# GATA1 / NFE2 seed genes for the erythroid neighbour set.
_SEEDS = {"GATA1", "NFE2"}


@register
class TargetAarsGlobinNeighborInteraction(Feature):
    name = "target_aars_globin_neighbor_interaction_e149"
    version = 1
    description = (
        "Product of a binary indicator that the perturbation target is an aminoacyl-tRNA "
        "synthetase and a binary indicator that gene g is a GATA1/NFE2 prior_network neighbor."
    )
    rationale = (
        "Aminoacyl-tRNA synthetase perturbations may specifically affect erythroid genes "
        "regulated by GATA1/NFE2, an interaction captured via the prior network."
    )
    inputs = ["prior_network", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Build the set of genes that are GATA1/NFE2 prior_network neighbors.
        neighbor_mask = np.zeros(n_genes, dtype=float)
        pn = ctx.knowledge("prior_network")
        if pn:
            seed_idx = set()
            for s in _SEEDS:
                if s in ctx.gene_index:
                    seed_idx.add(ctx.gene_index[s])
            for entry in pn:
                try:
                    a, b = entry[0], entry[1]
                except (IndexError, TypeError):
                    continue
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None:
                    continue
                if ia in seed_idx:
                    neighbor_mask[ib] = 1.0
                if ib in seed_idx:
                    neighbor_mask[ia] = 1.0
            # Include the seeds themselves as part of the erythroid program.
            for i in seed_idx:
                neighbor_mask[i] = 1.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            is_aars = 1.0 if any(t in _AARS_GENES for t in tg) else 0.0
            if is_aars:
                out[i, :, 0] = neighbor_mask
        return out
