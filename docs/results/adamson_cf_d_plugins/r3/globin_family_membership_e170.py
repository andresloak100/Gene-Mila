import numpy as np
from genemila.features.api import Feature, register

@register
class GlobinFamilyMembershipE170(Feature):
    name = "globin_family_membership_e170"
    version = 1
    description = "Binary feature: 1 if gene g is in a curated list of globin genes, else 0."
    rationale = ("Globin genes are co-regulated and may respond similarly to perturbations due to "
                 "shared chromatin or transcription factor regulation. A binary membership flag "
                 "captures shared biology for this gene family.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # Build globin gene set from prior knowledge, falling back to a manual list.
        globin_genes = set()
        try:
            gs = ctx.knowledge("gene_sets")
        except Exception:
            gs = None

        if isinstance(gs, dict):
            for key, members in gs.items():
                if not isinstance(key, str):
                    continue
                if "globin" in key.lower():
                    if isinstance(members, (list, tuple, set)):
                        for g in members:
                            if isinstance(g, str):
                                globin_genes.add(g)

        # Manual curated list (covers common globin family members).
        globin_genes.update([
            "HBZ", "HBG2", "HBG1", "HBA1", "HBA2", "HBB", "HBD", "HBE1",
            "HBM", "HBQ1", "HBF", "MB", "CYGB", "NGB", "HBBP1",
        ])

        idx = []
        for g in globin_genes:
            j = ctx.gene_index.get(g)
            if j is not None:
                idx.append(j)

        if idx:
            out[:, idx, 0] = 1.0

        return out
