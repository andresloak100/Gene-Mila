import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesUtr3Length(Feature):
    name = "additive_times_utr3_length_e441"
    version = 1
    description = "Elementwise product of additive_response and utr3_length of gene g."
    rationale = ("3' UTR length influences mRNA stability and miRNA regulation, which may "
                 "modulate CRISPRa-induced expression changes.")
    inputs = ["control_cells", "train_delta", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        # additive_response: sum over p's target genes of each gene's mean training delta
        # (leave-one-out), matching the additive baseline.
        add = np.zeros((len(perts), n))
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            m = d.mean(axis=0)
            tgt = ctx.target_indices(p)
            if tgt:
                add[i, :] = m[tgt].sum(axis=0)

        # utr3_length from gene_annotation
        utr3 = np.zeros(n)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            if "utr3_length" in cols:
                j = cols.index("utr3_length")
                genes = ann.get("genes", {})
                for g, gi in ctx.gene_index.items():
                    v = genes.get(g)
                    if v is not None:
                        val = v[j]
                        if val is not None:
                            try:
                                fv = float(val)
                                if np.isfinite(fv):
                                    utr3[gi] = fv
                            except (TypeError, ValueError):
                                pass

        out = np.zeros((len(perts), n, 1))
        out[:, :, 0] = add * utr3[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
