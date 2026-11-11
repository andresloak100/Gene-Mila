import numpy as np
from genemila.features.api import Feature, register


@register
class GlobinFamilyMembershipE110(Feature):
    name = "globin_family_membership_e110"
    version = 1
    description = "Binary feature: 1 if gene g is a known globin gene, else 0."
    rationale = (
        "Globin genes are co-regulated by erythroid transcription factors and may "
        "respond strongly to mitochondrial stress."
    )
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    _GLOBINS = frozenset([
        "HBZ", "HBA1", "HBA2", "HBG1", "HBG2", "HBD", "HBE1",
        "HBM", "HBQ1", "MB",
    ])

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vec = np.zeros(n_genes, dtype=float)
        for g, idx in ctx.gene_index.items():
            if g in self._GLOBINS:
                vec[idx] = 1.0
        # Broadcast the gene-level vector to every perturbation row.
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        return out
