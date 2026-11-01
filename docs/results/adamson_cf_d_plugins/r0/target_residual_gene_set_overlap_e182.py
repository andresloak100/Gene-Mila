import numpy as np
from genemila.features.api import Feature, register

@register
class TargetResidualGeneSetOverlapE182(Feature):
    name = "target_residual_gene_set_overlap_e182"
    version = 1
    description = "Number of gene sets shared between the target gene of perturbation p and a predefined set of residual genes."
    rationale = "Shared pathway membership between a perturbed target and residual genes may explain coordinated responses."
    inputs = ["gene_sets"]
    params = {"residual_genes": ["HBZ", "HBG2", "HIST1H1C", "HBA1", "HBG1",
                                  "MS4A4A", "HIST1H2BK", "MT-ATP6"]}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        gs = ctx.knowledge("gene_sets")
        if gs is None:
            return out

        residual = list(params.get("residual_genes", []))
        residual = [g for g in residual if g]

        # Build gene -> set of set-names index
        gene_sets_map = {}
        for set_name, genes in gs.items():
            if not isinstance(genes, (list, tuple)):
                continue
            for g in genes:
                gene_sets_map.setdefault(g, set()).add(set_name)

        # Precompute union of sets over residual genes
        resid_sets = set()
        for g in residual:
            s = gene_sets_map.get(g)
            if s:
                resid_sets |= s

        # Cache per-target overlap counts
        cache = ctx.cache
        key = "_e182_overlap"
        if key not in cache:
            cache[key] = {}

        def overlap_for(target_genes):
            sets = set()
            for g in target_genes:
                s = gene_sets_map.get(g)
                if s:
                    sets |= s
            if not sets or not resid_sets:
                return 0.0
            return float(len(sets & resid_sets))

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tkey = tuple(sorted(tgenes))
            if tkey in cache[key]:
                val = cache[key][tkey]
            else:
                val = overlap_for(tgenes)
                cache[key][tkey] = val
            out[i, :, 0] = val

        return out
