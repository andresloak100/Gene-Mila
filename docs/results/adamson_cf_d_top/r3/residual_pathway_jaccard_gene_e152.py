import numpy as np
from genemila.features.api import Feature, register

RESIDUAL_GENES = ["HBZ", "HBG2", "HIST1H1C", "HBA1", "HBG1", "MS4A4A", "HIST1H2BK", "GAL"]

@register
class ResidualPathwayJaccardGeneE152(Feature):
    name = "residual_pathway_jaccard_gene_e152"
    version = 1
    description = "Max Jaccard similarity of gene g's gene-set memberships to residual component genes."
    rationale = "Genes functionally related to residual component genes share pathway annotations and may respond similarly."
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        gs = ctx.knowledge("gene_sets")
        if not isinstance(gs, dict):
            return out

        # Build gene -> set of set-names mapping
        gene_to_sets = {}
        for set_name, members in gs.items():
            if not isinstance(members, (list, tuple)):
                continue
            for g in members:
                if isinstance(g, str):
                    gene_to_sets.setdefault(g, set()).add(set_name)

        # Residual genes' set collections
        res_sets = []
        for rg in RESIDUAL_GENES:
            s = gene_to_sets.get(rg)
            if s:
                res_sets.append(s)
        if not res_sets:
            return out

        # Precompute for each gene its set collection
        gene_sets_list = [gene_to_sets.get(g, set()) for g in ctx.genes]

        sims = np.zeros(n_genes, dtype=float)
        for i, s in enumerate(gene_sets_list):
            if not s:
                continue
            best = 0.0
            for rs in res_sets:
                inter = len(s & rs)
                if inter == 0:
                    continue
                union = len(s | rs)
                if union > 0:
                    j = inter / union
                    if j > best:
                        best = j
            sims[i] = best

        out[:, :, 0] = sims[None, :]
        return out
