import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConservationScoreE276(Feature):
    name = "target_conservation_score_e276"
    version = 1
    description = ("Mean conservation score over a perturbation's target genes, using gnomAD "
                   "LoF intolerance (LOEUF) as a proxy; low LOEUF = conserved.")
    rationale = ("Perturbations targeting evolutionarily constrained genes may trigger more "
                 "predictable downstream responses; conservation is proxied by LoF constraint.")
    inputs = ["target_genes", "knowledge:gene_constraint"]
    params = {"proxy": "loeuf"}
    dim = 1

    def compute(self, ctx, perts, params):
        proxy = params.get("proxy", "loeuf")
        kc = ctx.knowledge("gene_constraint")
        genes_tab = {}
        flags_tab = {}
        cols = []
        if isinstance(kc, dict):
            genes_tab = kc.get("genes", {}) or {}
            flags_tab = kc.get("flags", {}) or {}
            cols = kc.get("columns", []) or []

        # Determine which column holds the proxy score.
        col_idx = None
        if proxy == "loeuf":
            for cand in ("oe_lof_upper", "loeuf", "LOEUF"):
                if cand in cols:
                    col_idx = cols.index(cand)
                    break
        elif proxy == "pli":
            for cand in ("pLI", "pli", "p_li"):
                if cand in cols:
                    col_idx = cols.index(cand)
                    break
        if col_idx is None:
            for cand in ("oe_lof_upper", "loeuf", "LOEUF", "pLI", "pli"):
                if cand in cols:
                    col_idx = cols.index(cand)
                    break

        def score_for(gene):
            vals = genes_tab.get(gene)
            if vals is None or col_idx is None:
                return None
            try:
                v = vals[col_idx]
            except (IndexError, TypeError):
                return None
            if v is None:
                return None
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(fv):
                return None
            return fv

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            scores = []
            for g in targets:
                s = score_for(g)
                if s is not None:
                    if proxy in ("loeuf", "pli"):
                        # lower LOEUF / higher pLI = more constrained; invert to a
                        # "conservation" direction where higher = more conserved.
                        if proxy == "loeuf":
                            s = -s
                    scores.append(s)
            if not scores:
                continue
            val = float(np.mean(scores))
            out[i, :, 0] = val
        return out
