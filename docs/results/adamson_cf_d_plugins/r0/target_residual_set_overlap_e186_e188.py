import numpy as np
from genemila.features.api import Feature, register


@register
class TargetResidualSetOverlap(Feature):
    name = "target_residual_set_overlap_e186_e188"
    version = 1
    description = ("Jaccard similarity between the gene sets of the perturbation target "
                   "and the union of gene sets of the residual genes, broadcast to all genes.")
    rationale = ("Targets sharing pathways with residual genes are more likely to perturb "
                 "those pathways, increasing response in residual genes.")
    inputs = ["gene_sets", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        gs = ctx.knowledge("gene_sets")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        if not gs:
            return out

        # Build gene -> set of gene-set names
        gene_sets_map = {}
        for set_name, members in gs.items():
            if not isinstance(members, (list, tuple)):
                continue
            for g in members:
                if g in ctx.gene_index:
                    gene_sets_map.setdefault(g, set()).add(set_name)

        # Cache per-gene set objects
        empty = frozenset()
        gene_set_obj = {g: frozenset(s) for g, s in gene_sets_map.items()}

        # Residual genes: those with at least one gene set
        residual_genes = list(gene_set_obj.keys())
        if not residual_genes:
            return out

        # Precompute union of residual gene sets (all residual genes pooled)
        residual_union = set()
        for s in gene_set_obj.values():
            residual_union |= s
        residual_union = frozenset(residual_union)
        n_res = len(residual_union)

        if n_res == 0:
            return out

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            tgt_sets = set()
            for ti in tgt_idx:
                gname = ctx.genes[ti]
                s = gene_set_obj.get(gname)
                if s:
                    tgt_sets |= s
            if not tgt_sets:
                continue
            tgt_sets = frozenset(tgt_sets)
            inter = len(tgt_sets & residual_union)
            union = len(tgt_sets) + n_res - inter
            if union > 0:
                out[i, :, 0] = inter / union

        return out
