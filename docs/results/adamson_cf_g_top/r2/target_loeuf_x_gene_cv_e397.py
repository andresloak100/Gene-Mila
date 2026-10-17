import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneCV(Feature):
    name = "target_loeuf_x_gene_cv_e397"
    version = 1
    description = ("Product of the target gene's LoF constraint (LOEUF, transformed) "
                   "and the coefficient of variation of gene g across control cells.")
    rationale = ("Essential (LoF-intolerant, low LOEUF) targets are hubs; their "
                 "perturbation may destabilize highly variable genes more, capturing "
                 "context-dependent sensitivity.")
    inputs = ["control_cells", "control_mean", "control_std", "gene_constraint"]
    params = {"loeuf_transform": "negative_log"}
    dim = 1

    def compute(self, ctx, perts, params):
        transform = params.get("loeuf_transform", "negative_log")

        # Per-gene coefficient of variation across control cells.
        mean = np.asarray(ctx.control_mean, dtype=float)
        std = np.asarray(ctx.control_std, dtype=float)
        eps = 1e-8
        cv = std / (np.abs(mean) + eps)
        cv = np.where(np.isfinite(cv), cv, 0.0)

        # LOEUF per gene from gnomAD constraint knowledge.
        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_map = kc.get("genes", {})
            cols = kc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[gi] = fv

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            target_scores = []
            for ti in tgt_idx:
                lv = loeuf[ti]
                if not np.isfinite(lv) or lv <= 0:
                    continue
                if transform == "negative_log":
                    s = -np.log(lv)
                elif transform == "inverted":
                    s = 1.0 - lv
                elif transform == "reciprocal":
                    s = 1.0 / lv
                else:
                    s = -np.log(lv)
                target_scores.append(s)
            if target_scores:
                tscore = float(np.mean(target_scores))
            else:
                tscore = 0.0
            out[i, :, 0] = tscore * cv

        out = np.where(np.isfinite(out), out, 0.0)
        return out
