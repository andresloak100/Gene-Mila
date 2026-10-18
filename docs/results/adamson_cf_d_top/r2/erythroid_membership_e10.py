import numpy as np
from genemila.features.api import Feature, register


@register
class ErythroidMembershipE10(Feature):
    name = "erythroid_membership_e10"
    version = 1
    description = "Binary indicator: gene g belongs to any curated erythroid/hemoglobin gene set."
    rationale = ("Erythroid-specific genes are co-regulated by master transcription factors "
                 "(GATA1, NFE2) and may show coordinated responses to perturbations affecting "
                 "these regulators.")
    inputs = ["gene_sets"]
    params = {"set_keywords": ["erythro", "hemoglobin", "globin",
                               "oxygen transport", "carbon dioxide transport"]}
    dim = 1

    def compute(self, ctx, perts, params):
        keywords = params.get("set_keywords", self.params["set_keywords"])
        keywords = [str(k).lower() for k in keywords]

        n_genes = ctx.n_genes
        membership = np.zeros(n_genes, dtype=float)

        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            # gene_sets may be nested under a "sets" key or be the mapping itself
            sets = gs.get("sets", gs)
            if not isinstance(sets, dict):
                sets = {}
        else:
            sets = {}

        for set_name, genes in sets.items():
            if not isinstance(set_name, str):
                continue
            lname = set_name.lower()
            if not any(kw in lname for kw in keywords):
                continue
            if not isinstance(genes, (list, tuple)):
                continue
            for g in genes:
                idx = ctx.gene_index.get(g)
                if idx is not None:
                    membership[idx] = 1.0

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = membership[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
