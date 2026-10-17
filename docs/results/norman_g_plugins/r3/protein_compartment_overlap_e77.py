import numpy as np
from genemila.features.api import Feature, register

COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class ProteinCompartmentOverlapE77(Feature):
    name = "protein_compartment_overlap_e77"
    version = 1
    description = (
        "Jaccard similarity between the protein-compartment flag set of gene g "
        "and the union of compartment sets of perturbation p's target gene(s)."
    )
    rationale = (
        "Genes whose proteins localize to the same subcellular compartment as the "
        "perturbation target's protein may interact functionally and show larger "
        "expression changes."
    )
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        columns = ann["columns"]
        col_idx = {}
        for c in COMPARTMENTS:
            if c in columns:
                col_idx[c] = columns.index(c)
        if not col_idx:
            return out

        genes_ann = ann["genes"]

        # Build (n_genes, n_compartments) binary matrix in ctx.genes order.
        comp_names = list(col_idx.keys())
        n_comp = len(comp_names)
        gene_sets = np.zeros((n_genes, n_comp), dtype=bool)
        has_data = np.zeros(n_genes, dtype=bool)

        for g_idx, g in enumerate(ctx.genes):
            vals = genes_ann.get(g)
            if vals is None:
                continue
            has_data[g_idx] = True
            for k, c in enumerate(comp_names):
                v = vals[col_idx[c]]
                if v is not None:
                    try:
                        gene_sets[g_idx, k] = bool(float(v) > 0.5)
                    except (TypeError, ValueError):
                        pass

        # Precompute per-gene set sizes.
        gene_sizes = gene_sets.sum(axis=1).astype(float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            union_mask = np.zeros(n_comp, dtype=bool)
            any_target = False
            for t in targets:
                ti = ctx.gene_index.get(t)
                if ti is None or not has_data[ti]:
                    continue
                union_mask |= gene_sets[ti]
                any_target = True
            if not any_target:
                continue
            union_size = float(union_mask.sum())

            # Intersection with union for every gene: gene_sets & union_mask
            inter = (gene_sets & union_mask[None, :]).sum(axis=1).astype(float)
            union_sizes = gene_sizes + union_size - inter
            # Jaccard; define 0 when both sets empty.
            denom = np.where(union_sizes > 0, union_sizes, 1.0)
            jac = np.where(union_sizes > 0, inter / denom, 0.0)
            # Genes without annotation get 0.
            jac = np.where(has_data, jac, 0.0)
            out[i, :, 0] = jac

        return out
