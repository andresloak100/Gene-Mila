import numpy as np
from genemila.features.api import Feature, register


@register
class GeneSetMembershipE20(Feature):
    name = "gene_set_membership_e20"
    version = 1
    description = ("Binary indicator of whether gene g belongs to any of a selected set of "
                   "functional gene sets (e.g. globin, histone, carbon-dioxide/oxygen transport).")
    rationale = ("Perturbations may affect genes in certain functional pathways more strongly; "
                 "membership in these sets captures part of the shared residual response component.")
    inputs = ["gene_sets"]
    params = {"sets": "['GOBP:carbon dioxide transport', 'REACTOME:ATF6', 'GOBP:oxygen transport']"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Parse the requested set names (accept list or comma/bracket-separated string).
        raw = params.get("sets", self.params["sets"])
        if isinstance(raw, str):
            set_names = [s.strip().strip("'\"") for s in raw.strip("[]").split(",") if s.strip()]
        else:
            set_names = list(raw)
        if isinstance(set_names, str):
            set_names = [set_names]

        membership = np.zeros(n_genes, dtype=float)

        gs = ctx.knowledge("gene_sets")
        if gs is not None and set_names:
            # gene_sets is a dict of set_name -> list of genes.
            for name in set_names:
                genes = gs.get(name)
                if not genes:
                    continue
                for g in genes:
                    idx = ctx.gene_index.get(g)
                    if idx is not None:
                        membership[idx] = 1.0

        out[:, :, 0] = membership[np.newaxis, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
