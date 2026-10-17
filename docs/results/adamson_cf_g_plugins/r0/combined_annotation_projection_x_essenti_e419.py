import numpy as np
from genemila.features.api import Feature, register


@register
class CombinedAnnotationProjectionXEssentiality(Feature):
    name = "combined_annotation_projection_x_essenti_e419"
    version = 1
    description = ("combined_annotation_projection_target_in_e398 multiplied by "
                   "(1 - LOEUF_target) * (1 - LOEUF_gene).")
    rationale = ("Essential genes may have more conserved functional relationships, "
                 "amplifying annotation-based similarity between target and gene.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Base annotation projection feature (already leakage-safe).
        base = ctx.feature(
            "combined_annotation_projection_target_in_e398", perts, params
        )
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        if base.shape[2] != 1:
            base = base[:, :, :1]

        # LOEUF lookup from gene_constraint knowledge.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        target_loeuf = np.full(n_perts, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_kc = kc.get("genes", {})
            cols = kc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None

            if loeuf_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_kc.get(g)
                    if vals is None:
                        continue
                    if loeuf_idx < len(vals):
                        v = vals[loeuf_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                loeuf[gi] = fv

                for i, p in enumerate(perts):
                    best = np.nan
                    for tg in ctx.target_genes(p):
                        gi = ctx.gene_index.get(tg)
                        if gi is not None and np.isfinite(loeuf[gi]):
                            if not np.isfinite(best) or loeuf[gi] < best:
                                best = loeuf[gi]
                    target_loeuf[i] = best

        # Fill missing LOEUF with median of available values.
        finite_gene = loeuf[np.isfinite(loeuf)]
        if finite_gene.size > 0:
            med_gene = float(np.median(finite_gene))
        else:
            med_gene = 1.0
        loeuf_filled = np.where(np.isfinite(loeuf), loeuf, med_gene)

        finite_t = target_loeuf[np.isfinite(target_loeuf)]
        if finite_t.size > 0:
            med_t = float(np.median(finite_t))
        else:
            med_t = med_gene
        target_loeuf_filled = np.where(np.isfinite(target_loeuf), target_loeuf, med_t)

        # (1 - LOEUF) for target and gene.
        ess_target = 1.0 - target_loeuf_filled  # (n_perts,)
        ess_gene = 1.0 - loeuf_filled           # (n_genes,)

        out = base[:, :, 0] * ess_target[:, None] * ess_gene[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, None]
