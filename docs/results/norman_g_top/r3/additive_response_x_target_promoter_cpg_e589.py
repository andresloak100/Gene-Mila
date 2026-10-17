import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetPromoterCpgE589(Feature):
    name = "additive_response_x_target_promoter_cpg_e589"
    version = 1
    description = "Product of additive_response and mean CpG-island promoter overlap of target genes."
    rationale = (
        "CpG islands mark active promoters; CRISPRa at CpG-island promoters may activate "
        "more robustly, making the additive response more reliable for such targets."
    )
    inputs = ["control_mean", "gene_annotation"]
    params = {"promoter_window": 1000}
    dim = 1

    def _cpg_scores(self, ctx, params):
        """Per-gene binary CpG-island promoter indicator, from gene_annotation if available."""
        cache = ctx.cache
        key = "cpg_promoter_indicator_e589"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        scores = np.zeros(n, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            genes_tbl = ann.get("genes", {})
            columns = ann.get("columns", [])
            # Locate a CpG-related promoter column if present.
            cpg_col = None
            for j, c in enumerate(columns):
                cl = str(c).lower()
                if "cpg" in cl:
                    cpg_col = j
                    break
            if cpg_col is not None and isinstance(genes_tbl, dict):
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[cpg_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    # cpg_oe_promoter style: >0 means CpG island present; binary flags stay as-is.
                    scores[gi] = 1.0 if fv > 0 else 0.0

        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        cpg = self._cpg_scores(ctx, params)

        # additive_response from the existing feature (composition).
        try:
            add = ctx.feature("additive_response", perts)
            add = np.asarray(add, dtype=float)
            if add.ndim == 3:
                add = add[:, :, 0]
            elif add.ndim == 1:
                add = add[:, None]
        except Exception:
            add = None

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                cpg_mean = 0.0
            else:
                cpg_mean = float(np.mean(cpg[tgt_idx]))

            if add is not None:
                base = add[i]
            else:
                # Fallback: mean control expression as a crude additive proxy.
                base = ctx.control_mean

            out[i, :, 0] = base * cpg_mean

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
