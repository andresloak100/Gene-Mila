import numpy as np
from genemila.features.api import Feature, register

@register
class GlobinFamilyMembershipE111(Feature):
    name = "globin_family_membership_e111"
    version = 1
    description = "Binary feature: 1 if gene g is a known globin gene, else 0."
    rationale = ("Globin genes are co-regulated by erythroid transcription factors and may "
                 "respond strongly to mitochondrial stress.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = {
            "HBZ", "HBA1", "HBA2", "HBG1", "HBG2",
            "HBD", "HBE1", "HBM", "HBQ1", "MB",
        }
        vec = np.zeros(ctx.n_genes, dtype=float)
        for g in globin_genes:
            j = ctx.gene_index.get(g)
            if j is not None:
                vec[j] = 1.0
        out = np.tile(vec[None, :, None], (len(perts), 1, 1))
        return out
