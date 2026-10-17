import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTransmembraneCountInteractionE531(Feature):
    name = "target_transmembrane_count_interaction_e531"
    version = 1
    description = "Product of additive_response and the mean number of transmembrane segments across p's target genes."
    rationale = ("Perturbations targeting membrane proteins (many transmembrane segments) may produce "
                 "weaker transcriptional responses; scaling the additive baseline by this mean "
                 "modulates the predicted response accordingly.")
    inputs = ["control_cells", "protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # Build per-gene transmembrane counts from protein_annotation.
        tm_counts = None
        ann = ctx.knowledge("protein_annotation")
        if ann is not None and "genes" in ann and "columns" in ann:
            cols = ann["columns"]
            try:
                tm_idx = cols.index("n_transmembrane")
            except ValueError:
                tm_idx = None
            if tm_idx is not None:
                tm_counts = np.zeros(n_genes, dtype=float)
                ann_genes = ann["genes"]
                for g, vals in ann_genes.items():
                    j = ctx.gene_index.get(g)
                    if j is None or vals is None:
                        continue
                    v = vals[tm_idx]
                    if v is None:
                        continue
                    try:
                        tm_counts[j] = float(v)
                    except (TypeError, ValueError):
                        continue
        if tm_counts is None:
            tm_counts = np.zeros(n_genes, dtype=float)

        # Additive baseline: sum over target genes of each gene's mean control expression.
        control_mean = ctx.control_mean

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                continue
            tgt_idx = list(tgt_idx)
            add = control_mean[tgt_idx].sum()
            mean_tm = tm_counts[tgt_idx].mean()
            out[i, :, 0] = add * mean_tm

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
