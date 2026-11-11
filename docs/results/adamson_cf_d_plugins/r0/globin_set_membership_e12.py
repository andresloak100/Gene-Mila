import numpy as np
from genemila.features.api import Feature, register


@register
class GlobinSetMembershipE12(Feature):
    name = "globin_set_membership_e12"
    version = 1
    description = ("1 if gene g is in gene_sets 'GOBP:carbon dioxide transport' "
                   "or is a globin gene symbol, else 0.")
    rationale = ("Globin genes and carbon dioxide transport members respond "
                 "coordinately to perturbations affecting oxygen/iron homeostasis, "
                 "forming a shared residual component.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    GLOBIN_SYMBOLS = ("HBA1", "HBA2", "HBB", "HBG1", "HBG2",
                      "HBD", "HBE1", "HBZ")
    SET_NAMES = ("GOBP:carbon dioxide transport",)

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vec = np.zeros(n, dtype=float)

        # Collect gene-set members from prior knowledge.
        members = set()
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            for name in self.SET_NAMES:
                genes = gs.get(name)
                if genes:
                    members.update(genes)
            # In case the bundle stores sets under an inner key.
            inner = gs.get("gene_sets")
            if isinstance(inner, dict):
                for name in self.SET_NAMES:
                    genes = inner.get(name)
                    if genes:
                        members.update(genes)

        members.update(self.GLOBIN_SYMBOLS)

        for g in members:
            idx = ctx.gene_index.get(g)
            if idx is not None:
                vec[idx] = 1.0

        out = np.zeros((len(perts), n, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        return out
