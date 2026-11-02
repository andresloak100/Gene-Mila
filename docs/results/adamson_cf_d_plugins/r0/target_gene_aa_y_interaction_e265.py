import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAAYInteraction(Feature):
    name = "target_gene_aa_y_interaction_e265"
    version = 1
    description = "Product of target gene's tyrosine fraction (aa_Y) and gene g's tyrosine fraction."
    rationale = ("Tyrosine-rich proteins are often signaling molecules; their perturbation may "
                 "affect genes with similar phosphorylation potential.")
    inputs = ["control_cells", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load aa_Y fractions from gene_annotation
        ann = ctx.knowledge("gene_annotation")
        gene_aa_y = np.zeros(n_genes, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            try:
                y_idx = cols.index("aa_Y")
            except ValueError:
                y_idx = None
            if y_idx is not None:
                for i, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is not None and y_idx < len(vals):
                        v = vals[y_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    gene_aa_y[i] = fv
                            except (TypeError, ValueError):
                                pass

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # average aa_Y across target genes (usually one)
            t_aa_y = float(np.mean(gene_aa_y[tidx]))
            out[i, :, 0] = t_aa_y * gene_aa_y

        out[~np.isfinite(out)] = 0.0
        return out
