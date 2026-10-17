import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesExonCountE415(Feature):
    name = "additive_times_exon_count_e415"
    version = 1
    description = "Elementwise product of additive_response and the number of exons of gene g."
    rationale = ("Exon count is a proxy for gene complexity and alternative splicing; it may "
                 "modulate how strongly a perturbation's additive effect manifests.")
    inputs = ["additive_response", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # exon counts per gene (default 0 when missing / no coding info)
        exon = np.zeros(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            if "n_exons" in cols:
                j = cols.index("n_exons")
                for g, gi in gene_index.items():
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    v = vals[j]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            exon[gi] = fv

        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=np.float64)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim != 2:
            add = add.reshape(len(perts), n_genes)

        out = add * exon[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, None]
