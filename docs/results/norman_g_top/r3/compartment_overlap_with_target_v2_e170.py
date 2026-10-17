import numpy as np
from genemila.features.api import Feature, register


@register
class CompartmentOverlapWithTargetV2E170(Feature):
    name = "compartment_overlap_with_target_v2_e170"
    version = 1
    description = (
        "Jaccard similarity between the set of annotated subcellular compartments "
        "(UniProt protein_annotation flags) of gene g and the union of compartments "
        "of the perturbation's target gene(s)."
    )
    rationale = (
        "Perturbations may preferentially affect genes whose protein products reside "
        "in the same cellular compartment as the perturbed target(s), capturing spatial "
        "proximity within the cell."
    )
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    # compartment flag columns in protein_annotation (order-independent lookup)
    _COMPARTMENTS = [
        "secreted",
        "membrane",
        "endoplasmic_reticulum",
        "golgi",
        "mitochondrion",
        "nucleus",
        "cytoplasm",
        "lysosome",
        "peroxisome",
    ]

    def _build_matrix(self, ctx):
        """Return (n_genes, n_compartments) boolean matrix of compartment flags."""
        key = "_comp_matrix_e170"
        if key in ctx.cache:
            return ctx.cache[key]

        n_genes = ctx.n_genes
        n_comp = len(self._COMPARTMENTS)
        mat = np.zeros((n_genes, n_comp), dtype=bool)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            # map compartment name -> column index
            comp_col = {}
            for c in self._COMPARTMENTS:
                if c in cols:
                    comp_col[c] = cols.index(c)
            # only keep compartments actually present
            present = [c for c in self._COMPARTMENTS if c in comp_col]
            if present:
                pidx = [self._COMPARTMENTS.index(c) for c in present]
                for g, col in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    for ci, c in zip(pidx, present):
                        v = vals[comp_col[c]]
                        if v is not None:
                            try:
                                if float(v) > 0.5:
                                    mat[col, ci] = True
                            except (TypeError, ValueError):
                                pass

        ctx.cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        mat = self._build_matrix(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_indices(p)
            if not tg:
                continue
            # union of compartments over all target genes
            target_comp = mat[tg].any(axis=0)  # (n_comp,)
            t_count = int(target_comp.sum())
            if t_count == 0:
                continue

            # intersection counts per gene
            inter = (mat & target_comp[None, :]).sum(axis=1)  # (n_genes,)
            g_count = mat.sum(axis=1)  # (n_genes,)
            union = g_count + t_count - inter
            jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
            out[i, :, 0] = jac

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
