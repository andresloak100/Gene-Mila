import numpy as np
from genemila.features.api import Feature, register


@register
class TargetResidualSetOverlap(Feature):
    name = "target_residual_set_overlap_e214"
    version = 1
    description = (
        "For each perturbation p, Jaccard similarity between the union of gene sets "
        "containing any target gene and the union of gene sets containing any residual gene."
    )
    rationale = (
        "Targets functionally related to residual genes (shared pathway membership) may "
        "produce larger responses in those residual genes."
    )
    inputs = ["gene_sets"]
    params = {
        "residual_genes": [
            "HBZ", "HBG2", "HBA1", "HIST1H1C",
            "HIST1H2BK", "MS4A4A", "MT-ATP6", "HBG1",
        ]
    }
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        residual_genes = params.get("residual_genes", self.params["residual_genes"])
        residual_set = set(residual_genes)

        # Build gene -> set of gene-set names map from the prior knowledge (cached).
        cache = ctx.cache
        key = "e214_gene_to_sets"
        if key not in cache:
            gs = ctx.knowledge("gene_sets")
            gene_to_sets = {}
            if isinstance(gs, dict):
                for set_name, members in gs.items():
                    if not isinstance(members, (list, tuple)):
                        continue
                    for g in members:
                        if g not in gene_to_sets:
                            gene_to_sets[g] = set()
                        gene_to_sets[g].add(set_name)
            cache[key] = gene_to_sets
        gene_to_sets = cache[key]

        # Union of gene sets containing any residual gene.
        residual_sets = set()
        for g in residual_set:
            s = gene_to_sets.get(g)
            if s:
                residual_sets |= s

        n_res = len(residual_sets)

        for i, p in enumerate(perts):
            target_sets = set()
            for t in ctx.target_genes(p):
                s = gene_to_sets.get(t)
                if s:
                    target_sets |= s
            n_tar = len(target_sets)
            union = n_tar + n_res - len(target_sets & residual_sets)
            if union > 0:
                jac = len(target_sets & residual_sets) / union
            else:
                jac = 0.0
            out[i, :, 0] = jac

        return out
