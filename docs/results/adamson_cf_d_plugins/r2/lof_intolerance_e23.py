import numpy as np
from genemila.features.api import Feature, register


@register
class LofIntoleranceE23(Feature):
    name = "lof_intolerance_e23"
    version = 1
    description = "Per-gene loss-of-function constraint (pLI or LOEUF) from gnomAD gene_constraint."
    rationale = ("Genes intolerant to loss-of-function may show stronger or more specific "
                 "expression responses to perturbation; gene-level constraint is an "
                 "independent property not yet used by the model.")
    inputs = ["gene_constraint"]
    params = {"constraint_metric": "pLI"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        metric = params.get("constraint_metric", "pLI")

        # Cache the per-gene vector keyed by metric (shared across perturbations).
        cache_key = ("lof_intolerance_e23", metric)
        vec = ctx.cache.get(cache_key) if isinstance(ctx.cache, dict) else None
        if vec is None:
            vec = np.zeros(n_genes, dtype=float)
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                columns = list(kc.get("columns", []))
                genes_tbl = kc.get("genes", {}) or {}

                # Resolve column name for the requested metric.
                col_idx = None
                if metric in columns:
                    col_idx = columns.index(metric)
                else:
                    # Fallbacks for common aliases.
                    aliases = {
                        "pLI": ["pLI", "pli", "p_li", "prob_lof_intolerant"],
                        "oe_lof_upper": ["oe_lof_upper", "loeuf", "LOEUF", "oe_lof"],
                    }
                    for cand in aliases.get(metric, [metric]):
                        if cand in columns:
                            col_idx = columns.index(cand)
                            break

                if col_idx is not None:
                    for g, gi in ctx.gene_index.items():
                        vals = genes_tbl.get(g)
                        if vals is None:
                            continue
                        try:
                            v = vals[col_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            vec[gi] = fv

            if isinstance(ctx.cache, dict):
                ctx.cache[cache_key] = vec

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        # Ensure finite output.
        out[~np.isfinite(out)] = 0.0
        return out
