import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneConstraintInteractionE54(Feature):
    name = "target_gene_constraint_interaction_e54"
    version = 1
    description = ("Product of standardized target-gene and response-gene LoF constraint "
                   "(LOEUF, or pLI fallback), missing imputed to median.")
    rationale = ("Coordinated loss-of-function intolerance between target and response gene "
                 "may indicate shared essential pathways, amplifying perturbation response.")
    inputs = ["gene_constraint", "targets"]
    params = {"constraint_metric": "LOEUF"}
    dim = 1

    def _get_constraint(self, ctx, params):
        cache = ctx.cache
        key = "_e54_constraint_values"
        if key in cache:
            return cache[key]

        metric = str(params.get("constraint_metric", "LOEUF")).strip()
        metric_l = metric.lower()

        kc = ctx.knowledge("gene_constraint")
        vals = np.full(ctx.n_genes, np.nan, dtype=float)

        if kc is not None:
            columns = kc.get("columns", []) or []
            genes_tbl = kc.get("genes", {}) or {}

            # locate the desired column index
            col_idx = None
            candidates_lo = ["oe_lof_upper", "loeuf"]
            candidates_pli = ["pli"]
            if metric_l in ("loeuf", "oe_lof_upper"):
                cand = candidates_lo
            elif metric_l in ("pli",):
                cand = candidates_pli
            else:
                cand = [metric_l] + candidates_lo + candidates_pli

            lower_cols = [str(c).lower() for c in columns]
            for c in cand:
                if c in lower_cols:
                    col_idx = lower_cols.index(c)
                    break

            if col_idx is not None:
                for g, colvals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = colvals[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv

            # fallback to pLI where LOEUF missing, if we used LOEUF
            if metric_l in ("loeuf", "oe_lof_upper") and "pli" in lower_cols:
                pli_idx = lower_cols.index("pli")
                for g, colvals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or np.isfinite(vals[gi]):
                        continue
                    try:
                        v = colvals[pli_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
            std = float(np.std(vals[finite]))
            vals = np.where(finite, vals, med)
            if not np.isfinite(std) or std < 1e-12:
                std = 1.0
            z = (vals - float(np.mean(vals))) / std
        else:
            z = np.zeros(ctx.n_genes, dtype=float)

        cache[key] = z
        return z

    def compute(self, ctx, perts, params):
        z = self._get_constraint(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # average standardized constraint over target genes (usually one)
            tz = float(np.mean(z[tgt_idx]))
            out[i, :, 0] = tz * z

        out[~np.isfinite(out)] = 0.0
        return out
