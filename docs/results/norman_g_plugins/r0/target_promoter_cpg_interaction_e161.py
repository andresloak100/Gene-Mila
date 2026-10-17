import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgInteractionE161(Feature):
    name = "target_promoter_cpg_interaction_e161"
    version = 1
    description = (
        "Average promoter GC/CpG content of perturbation targets, interacted with "
        "the target_response_similarity_to_mean_e110 feature."
    )
    rationale = (
        "CRISPRa efficiency may depend on chromatin accessibility, which correlates "
        "with promoter CpG islands; interacting this epigenetic potential with a "
        "response-similarity feature captures residual variance."
    )
    inputs = ["knowledge:gene_annotation", "feature:target_response_similarity_to_mean_e110"]
    params = {"promoter_metric": "gc_promoter"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("promoter_metric", "gc_promoter")

        ann = ctx.knowledge("gene_annotation")
        genes_ann = ann.get("genes", {}) if ann else {}
        columns = ann.get("columns", []) if ann else []
        if metric in columns:
            col_idx = columns.index(metric)
        else:
            col_idx = None

        # Compute per-perturbation average promoter metric over targets.
        n = len(perts)
        avg_metric = np.zeros(n, dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = []
            for g in tg:
                row = genes_ann.get(g)
                if row is None or col_idx is None:
                    continue
                try:
                    v = row[col_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals.append(fv)
            if vals:
                avg_metric[i] = float(np.mean(vals))
            else:
                avg_metric[i] = np.nan

        # Fill missing metrics with the mean of available ones (or 0).
        finite_mask = np.isfinite(avg_metric)
        if finite_mask.any():
            fill = float(avg_metric[finite_mask].mean())
            avg_metric[~finite_mask] = fill
        else:
            avg_metric[:] = 0.0

        # Get the companion feature.
        sim = ctx.feature("target_response_similarity_to_mean_e110", perts, None)
        sim = np.asarray(sim, dtype=float)
        if sim.ndim == 3:
            sim = sim[:, :, 0]
        elif sim.ndim == 1:
            sim = sim[:, None]
        # sim should be (n, n_genes)

        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = avg_metric[:, None] * sim

        # Ensure finite values.
        out = np.where(np.isfinite(out), out, 0.0)
        return out
