import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMembraneFractionTimesAdditiveE441(Feature):
    name = "target_membrane_fraction_times_additive__e441"
    version = 1
    description = "Product of the fraction of p's target genes with membrane localization flag and additive_response."
    rationale = ("Membrane proteins may have distinct CRISPRa responses due to trafficking or stability; "
                 "the fraction of membrane targets scales the additive baseline prediction.")
    inputs = ["control_cells", "protein_annotation", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # membrane flag per gene from protein_annotation
        mem_flag = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            try:
                mi = cols.index("membrane")
            except ValueError:
                mi = None
            if mi is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    v = vals[mi]
                    if v is None:
                        continue
                    try:
                        mem_flag[gi] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        mem_flag[gi] = 0.0

        for i, p in enumerate(perts):
            # additive_response via composition
            add = ctx.feature("additive_response", [p])
            add_vec = np.asarray(add, dtype=float).reshape(n_genes)

            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) > 0:
                frac = mem_flag[tgt_idx].mean()
            else:
                frac = 0.0

            out[i, :, 0] = frac * add_vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
