import numpy as np
from genemila.features.api import Feature, register


@register
class GeneTargetPLIInteraction(Feature):
    name = "gene_target_pli_interaction_e79"
    version = 1
    description = ("Interaction between gene g's LoF constraint (pLI) and the target "
                   "gene t's pLI: product of the two, with median imputation of missing values.")
    rationale = ("High pLI genes are essential and tightly regulated; perturbing another "
                 "essential (LoF-intolerant) gene may trigger larger responses in essential "
                 "genes via buffering/compensatory mechanisms.")
    inputs = ["knowledge:gene_constraint"]
    params = {"impute": "median"}
    dim = 1

    def _get_pli(self, ctx):
        """Return dict gene->pLI (0..1), using pLI, falling back to LOEUF/pRec."""
        cache_key = "e79_pli_map"
        if cache_key in ctx.cache:
            return ctx.cache[cache_key]

        kc = ctx.knowledge("gene_constraint")
        pli_map = {}
        if kc is not None:
            cols = kc.get("columns", []) if isinstance(kc, dict) else []
            genes = kc.get("genes", {}) if isinstance(kc, dict) else {}
            # locate columns
            def col_idx(*names):
                for nm in names:
                    for j, c in enumerate(cols):
                        if str(c).lower() == nm.lower():
                            return j
                return None

            i_pli = col_idx("pLI", "pli")
            i_loeuf = col_idx("oe_lof_upper", "LOEUF", "loeuf")
            i_prec = col_idx("pRec", "prec")

            for g, vals in genes.items():
                if not vals:
                    continue
                val = None
                if i_pli is not None and i_pli < len(vals) and vals[i_pli] is not None:
                    try:
                        val = float(vals[i_pli])
                    except (TypeError, ValueError):
                        val = None
                # fallback: convert LOEUF (~0..2) to a pLI-like score in [0,1]
                if val is None and i_loeuf is not None and i_loeuf < len(vals) and vals[i_loeuf] is not None:
                    try:
                        loeuf = float(vals[i_loeuf])
                        val = float(np.clip(1.0 - loeuf, 0.0, 1.0))
                    except (TypeError, ValueError):
                        val = None
                if val is None and i_prec is not None and i_prec < len(vals) and vals[i_prec] is not None:
                    try:
                        val = float(vals[i_prec])
                    except (TypeError, ValueError):
                        val = None
                if val is not None and np.isfinite(val):
                    pli_map[g] = float(np.clip(val, 0.0, 1.0))

        ctx.cache[cache_key] = pli_map
        return pli_map

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        pli_map = self._get_pli(ctx)

        # median imputation value over measured genes
        if len(pli_map) > 0:
            med = float(np.median(list(pli_map.values())))
        else:
            med = 0.0
        impute = params.get("impute", "median")
        fill = med if impute == "median" else 0.0

        # per-gene pLI vector aligned to ctx.genes
        gene_pli = np.full(ctx.n_genes, fill, dtype=float)
        for j, g in enumerate(ctx.genes):
            v = pli_map.get(g)
            if v is not None:
                gene_pli[j] = v

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                # no measured target -> use imputed target pLI
                t_pli = fill
            else:
                tvals = [gene_pli[j] for j in tgt_idx]
                t_pli = float(np.mean(tvals))
            out[i, :, 0] = gene_pli * t_pli

        out[~np.isfinite(out)] = 0.0
        return out
