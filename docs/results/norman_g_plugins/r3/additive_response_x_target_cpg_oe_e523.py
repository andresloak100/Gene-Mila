import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetCpGOe(Feature):
    name = "additive_response_x_target_cpg_oe_e523"
    version = 1
    description = "Product of additive_response and the mean promoter CpG observed/expected ratio of the perturbation's target genes."
    rationale = "High promoter CpG o/e indicates open, unmethylated chromatin, so CRISPRa targets there may be more responsive; this modulates the additive baseline."
    inputs = ["control_cells", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = np.tile(add[:, None], (1, ctx.n_genes))

        # cpg_oe_promoter per gene from gene_annotation
        ann = ctx.knowledge("gene_annotation")
        cpg = np.full(ctx.n_genes, np.nan, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            if ci is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg[gi] = fv

        # fall back to mean of known values for missing entries
        known = np.isfinite(cpg)
        fill = float(cpg[known].mean()) if known.any() else 1.0
        cpg = np.where(np.isfinite(cpg), cpg, fill)

        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                score = float(cpg[tgt].mean())
            else:
                score = fill
            out[i, :, 0] = add[i] * score

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
