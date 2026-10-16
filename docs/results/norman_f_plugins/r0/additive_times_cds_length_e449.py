import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesCdsLength(Feature):
    name = "additive_times_cds_length_e449"
    version = 1
    description = "Elementwise product of additive_response and cds_length of gene g."
    rationale = "CDS length correlates with gene function and mRNA stability; interaction with additive_response may capture response magnitude scaling."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        # additive_response feature
        add = ctx.feature("additive_response", perts)  # (n_perts, n_genes, 1)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        else:
            add = add.reshape(len(perts), n_genes)

        # cds_length per gene from gene_annotation
        cds = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_info = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                cds_idx = columns.index("cds_length")
            except ValueError:
                cds_idx = None
            if cds_idx is not None:
                for j, g in enumerate(ctx.genes):
                    vals = genes_info.get(g)
                    if vals is not None and cds_idx < len(vals):
                        v = vals[cds_idx]
                        if v is not None:
                            try:
                                cds[j] = float(v)
                            except (TypeError, ValueError):
                                cds[j] = 0.0

        out = add * cds[np.newaxis, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, np.newaxis].astype(float)
