import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityWeightedTfMotifScore(Feature):
    name = "essentiality_weighted_tf_motif_score_e386"
    version = 1
    description = ("Promoter motif score (tf_motif_score_e179) weighted by gene LoF "
                   "intolerance (1 - LOEUF).")
    rationale = ("Essential (LoF-intolerant) genes are under tighter regulatory control, so "
                 "motif-based response predictions should be more reliable for them; "
                 "weighting the motif score by (1 - LOEUF) emphasises these genes.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Base motif score from existing feature: (n_perts, n_genes, dim_base)
        base = ctx.feature("tf_motif_score_e179", perts, params)
        base = np.asarray(base, dtype=float)
        if base.ndim == 3:
            base = base[:, :, 0]
        elif base.ndim == 1:
            base = base[None, :]

        # LOEUF per gene from gene_constraint knowledge
        loeuf = np.full(n_genes, np.nan, dtype=float)
        try:
            constraint = ctx.knowledge("gene_constraint")
        except Exception:
            constraint = None

        if constraint is not None and isinstance(constraint, dict):
            genes_tbl = constraint.get("genes", {}) or {}
            cols = constraint.get("columns", []) or []
            try:
                loeuf_idx = list(cols).index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for j, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[j] = fv

        # Median imputation for missing LOEUF
        finite = np.isfinite(loeuf)
        if finite.any():
            med = float(np.median(loeuf[finite]))
        else:
            med = 1.0
        loeuf = np.where(finite, loeuf, med)

        # Clamp to [0, 1] for a stable weight
        loeuf = np.clip(loeuf, 0.0, 1.0)
        weight = 1.0 - loeuf  # (n_genes,)

        out = base * weight[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, None]
