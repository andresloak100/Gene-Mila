import numpy as np
from genemila.features.api import Feature, register


@register
class TargetExonCountTimesAdditiveResponse(Feature):
    name = "target_exon_count_times_additive_respons_e438"
    version = 1
    description = "Product of the mean exon count of p's target genes and additive_response."
    rationale = "Exon count relates to splicing complexity and may modulate the additive response."
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Retrieve the additive_response feature (composition).
        try:
            add = ctx.feature("additive_response", perts, params=None)
        except Exception:
            add = None

        ann = ctx.knowledge("gene_annotation")
        n_exons_map = {}
        if ann is not None and "genes" in ann and "columns" in ann:
            cols = ann["columns"]
            try:
                exon_idx = cols.index("n_exons")
            except ValueError:
                exon_idx = None
            if exon_idx is not None:
                for sym, vals in ann["genes"].items():
                    if vals is None:
                        continue
                    try:
                        v = vals[exon_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        n_exons_map[sym] = fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [n_exons_map[g] for g in targets if g in n_exons_map]
            if len(vals) > 0:
                mean_exons = float(np.mean(vals))
            else:
                mean_exons = 0.0

            if add is not None:
                base = add[i, :, 0]
            else:
                base = np.zeros(ctx.n_genes, dtype=float)

            out[i, :, 0] = mean_exons * base

        out[~np.isfinite(out)] = 0.0
        return out
