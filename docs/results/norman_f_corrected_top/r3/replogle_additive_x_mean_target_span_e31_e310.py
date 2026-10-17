import numpy as np
from genemila.features.api import Feature, register

@register
class ReplogleAdditiveXMeanTargetSpanE31E310(Feature):
    name = "replogle_additive_x_mean_target_span_e31_e310"
    version = 1
    description = "Product of sign-corrected Replogle additive response and mean gene span (kb) of target genes."
    rationale = "Gene span relates to regulatory complexity and may modulate CRISPRa efficiency; scaling the Replogle additive response by target mean span captures this context effect."
    inputs = ["knowledge", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Get Replogle knowledge
        repl = ctx.knowledge("replogle2022_k562")
        sign = -1.0
        repl_deltas = {}
        repl_genes = []
        if repl is not None:
            sign_raw = repl.get("sign", -1.0)
            try:
                sign = float(sign_raw)
            except (TypeError, ValueError):
                sign = -1.0
            if not np.isfinite(sign):
                sign = -1.0
            repl_genes = repl.get("genes", []) or []
            perts_dict = repl.get("perts", {}) or {}
            for g, entry in perts_dict.items():
                if entry is None:
                    continue
                d = entry.get("delta") if isinstance(entry, dict) else None
                if d is None:
                    continue
                arr = np.asarray(d, dtype=float)
                if arr.size != len(repl_genes):
                    continue
                repl_deltas[g] = arr

        # Gene annotation for span
        annot = ctx.knowledge("gene_annotation")
        span_map = {}
        span_col = None
        if annot is not None:
            span_map = annot.get("genes", {}) or {}
            cols = annot.get("columns", []) or []
            for i, c in enumerate(cols):
                if c == "gene_span_kb":
                    span_col = i
                    break

        # Cache per-gene span values aligned to ctx.genes
        cache = ctx.cache
        if "span_vec_e310" not in cache:
            span_vec = np.full(ctx.n_genes, np.nan, dtype=float)
            if span_col is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = span_map.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[span_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        span_vec[gi] = fv
            cache["span_vec_e310"] = span_vec
        span_vec = cache["span_vec_e310"]

        # Precompute Replogle additive response for each target gene in ctx.genes order
        if "repl_vec_e310" not in cache:
            rvec = np.zeros(ctx.n_genes, dtype=float)
            if repl_deltas:
                for gi, g in enumerate(ctx.genes):
                    arr = repl_deltas.get(g)
                    if arr is not None:
                        val = sign * arr[gi]
                        if np.isfinite(val):
                            rvec[gi] = val
            cache["repl_vec_e310"] = rvec
        repl_vec = cache["repl_vec_e310"]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            t_idx = [ctx.gene_index[g] for g in targets if g in ctx.gene_index]
            if not t_idx:
                continue
            # Replogle additive response: sum over targets of sign-corrected delta
            repl_add = float(repl_vec[t_idx].sum())
            if not np.isfinite(repl_add) or repl_add == 0.0:
                continue
            # Mean gene span over targets
            spans = span_vec[t_idx]
            valid = np.isfinite(spans)
            if not valid.any():
                continue
            mean_span = float(spans[valid].mean())
            if not np.isfinite(mean_span):
                continue
            val = repl_add * mean_span
            if not np.isfinite(val):
                continue
            out[i, :, 0] = val

        # Final safety: replace any non-finite values with 0
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
