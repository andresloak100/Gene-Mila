import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetCytoplasm(Feature):
    name = "additive_response_x_target_cytoplasm_e543"
    version = 1
    description = "Product of additive_response and the mean cytoplasm-localization flag of the perturbation's target genes."
    rationale = "Cytoplasmic targets may act through signaling or metabolic pathways, modulating the additive response differently than nuclear targets."
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Precompute cytoplasm flag per gene
        cyto = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {})
            columns = ann.get("columns", [])
            if "cytoplasm" in columns:
                cyto_idx = columns.index("cytoplasm")
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[cyto_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        cyto[gi] = float(v)
                    except (TypeError, ValueError):
                        pass

        # Get additive_response feature
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        elif add.ndim == 1:
            add = add[:, None, None]

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                frac = 0.0
            else:
                frac = float(np.mean(cyto[tidx]))
            out[i, :, 0] = add[i, :, 0] * frac

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
