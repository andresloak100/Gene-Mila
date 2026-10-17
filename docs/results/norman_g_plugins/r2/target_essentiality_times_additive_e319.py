import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityTimesAdditiveE319(Feature):
    name = "target_essentiality_times_additive_e319"
    version = 1
    description = ("Mean essentiality score of p's target genes (inverted LOEUF or pLI from "
                   "gnomAD LoF constraint) multiplied by additive_response.")
    rationale = ("Perturbations of highly constrained (essential) genes cause stronger expression "
                 "changes; scaling the additive baseline by target essentiality captures this "
                 "amplification.")
    inputs = ["gene_constraint", "additive_response"]
    params = {"metric": "loeuf"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("metric", "loeuf")
        n_genes = ctx.n_genes

        # Build per-gene essentiality vector once (cached).
        cache_key = ("essentiality_vec", metric)
        if cache_key in ctx.cache:
            ess = ctx.cache[cache_key]
        else:
            ess = np.full(n_genes, np.nan, dtype=float)
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                columns = kc.get("columns", [])
                genes_tbl = kc.get("genes", {}) or {}
                # Resolve column index for the requested metric.
                col_idx = None
                if metric in columns:
                    col_idx = columns.index(metric)
                else:
                    # Fallbacks
                    for cand in ("loeuf", "oe_lof_upper", "pLI", "pli"):
                        if cand in columns:
                            col_idx = columns.index(cand)
                            break
                use_loeuf = (col_idx is not None and
                             columns[col_idx] in ("loeuf", "oe_lof_upper"))
                if col_idx is not None:
                    for g, vals in genes_tbl.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None or vals is None:
                            continue
                        try:
                            v = vals[col_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            v = float(v)
                        except (TypeError, ValueError):
                            continue
                        if not np.isfinite(v):
                            continue
                        if use_loeuf:
                            # Invert LOEUF: low LOEUF = high essentiality.
                            ess[gi] = 1.0 - v
                        else:
                            # pLI: high = essential.
                            ess[gi] = v
            # Store; NaN entries mean unknown -> we will treat as neutral (0 contribution).
            ctx.cache[cache_key] = ess

        # additive_response feature (dim 1 per gene).
        add = ctx.feature("additive_response", perts, None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if tidx:
                vals = ess[np.asarray(tidx, dtype=int)]
                known = vals[np.isfinite(vals)]
                if known.size > 0:
                    mean_ess = float(known.mean())
                else:
                    mean_ess = 0.0
            else:
                mean_ess = 0.0
            out[i, :, 0] = mean_ess * add[i]

        out[~np.isfinite(out)] = 0.0
        return out
