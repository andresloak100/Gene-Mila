import numpy as np
from genemila.features.api import Feature, register


@register
class IntronLengthLogE33(Feature):
    name = "intron_length_log_e33"
    version = 1
    description = "Log10 of intron_length_kb (plus 1) for gene g."
    rationale = (
        "Long introns slow transcriptional elongation, imposing a kinetic barrier "
        "that dampens the magnitude of expression change after perturbation."
    )
    inputs = ["gene_annotation.intron_length_kb"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None or "genes" not in ann:
            return out

        cols = ann.get("columns", [])
        try:
            col_idx = cols.index("intron_length_kb")
        except ValueError:
            return out

        genes_ann = ann["genes"]
        for gi, gene in enumerate(ctx.genes):
            vals = genes_ann.get(gene)
            if vals is None:
                continue
            v = vals[col_idx]
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            out[:, gi, 0] = np.log10(max(v, 0.0) + 1.0)

        return out
