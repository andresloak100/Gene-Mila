import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConstraintInteractionE91(Feature):
    name = "target_constraint_interaction_e91"
    version = 1
    description = ("Product of is_target(g, p) and a normalized LoF-intolerance score of gene g "
                   "(1 - LOEUF, or pLI fallback), for every target gene of p.")
    rationale = ("LoF-intolerant genes may be more sensitive to expression changes; targeting them "
                 "could produce larger downstream effects, so the interaction flags target genes "
                 "that are constraint-sensitive.")
    inputs = ["gene_constraint"]
    params = {"intolerance_metric": "loeuf"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("intolerance_metric", "loeuf")
        n = ctx.n_genes

        # Build per-gene intolerance vector in ctx gene column order.
        cache_key = "_tci_e91_intol_" + str(metric)
        if cache_key in ctx.cache:
            intol = ctx.cache[cache_key]
        else:
            intol = np.full(n, np.nan, dtype=float)
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                genes_tbl = kc.get("genes", {}) or {}
                columns = kc.get("columns", []) or []
                try:
                    i_loeuf = columns.index("oe_lof_upper")
                except ValueError:
                    i_loeuf = None
                try:
                    i_pli = columns.index("pLI")
                except ValueError:
                    i_pli = None

                for gi, gname in enumerate(ctx.genes):
                    vals = genes_tbl.get(gname)
                    if vals is None:
                        continue
                    loeuf = None
                    pli = None
                    if i_loeuf is not None and i_loeuf < len(vals):
                        v = vals[i_loeuf]
                        if v is not None:
                            try:
                                loeuf = float(v)
                            except (TypeError, ValueError):
                                loeuf = None
                    if i_pli is not None and i_pli < len(vals):
                        v = vals[i_pli]
                        if v is not None:
                            try:
                                pli = float(v)
                            except (TypeError, ValueError):
                                pli = None

                    if metric == "pli":
                        if pli is not None:
                            intol[gi] = pli
                        elif loeuf is not None:
                            intol[gi] = 1.0 - loeuf
                    else:  # "loeuf"
                        if loeuf is not None:
                            intol[gi] = 1.0 - loeuf
                        elif pli is not None:
                            intol[gi] = pli

            # Normalize to [0,1]; missing -> 0 (neutral, no interaction signal).
            valid = np.isfinite(intol)
            if valid.any():
                lo = np.nanmin(intol[valid])
                hi = np.nanmax(intol[valid])
                if hi > lo:
                    norm = (intol - lo) / (hi - lo)
                else:
                    norm = np.zeros(n, dtype=float)
            else:
                norm = np.zeros(n, dtype=float)
            norm = np.where(np.isfinite(norm), norm, 0.0)
            norm = np.clip(norm, 0.0, 1.0)
            intol = norm
            ctx.cache[cache_key] = intol

        out = np.zeros((len(perts), n, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            idx = np.asarray(tgt, dtype=int)
            out[i, idx, 0] = intol[idx]
        return out
