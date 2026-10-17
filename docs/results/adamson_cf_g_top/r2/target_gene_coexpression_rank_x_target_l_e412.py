import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneCoexpressionRankXTargetLOEUF(Feature):
    name = "target_gene_coexpression_rank_x_target_l_e412"
    version = 1
    description = (
        "Product of the percentile rank of the Pearson correlation between the target "
        "gene and gene g across control cells and the target's LOEUF (gene_constraint)."
    )
    rationale = (
        "Coexpression alone was weak, but combining with essentiality (LOEUF) may reveal "
        "context-specific effects: highly coexpressed partners of an LoF-intolerant target "
        "may be more likely to respond."
    )
    inputs = ["control_cells", "gene_corr", "target_indices", "gene_constraint"]
    params = {"rank_transform": "percentile"}
    dim = 1

    def _get_loeuf(self, ctx):
        cached = ctx.cache.get("_e412_loeuf")
        if cached is not None:
            return cached
        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        try:
            gc = ctx.knowledge("gene_constraint")
        except Exception:
            gc = None
        if gc is not None:
            genes_map = gc.get("genes", {}) if isinstance(gc, dict) else {}
            cols = gc.get("columns", []) if isinstance(gc, dict) else []
            idx = None
            if isinstance(cols, list):
                for j, c in enumerate(cols):
                    if c == "oe_lof_upper":
                        idx = j
                        break
            if idx is not None:
                for sym, vals in genes_map.items():
                    gi = ctx.gene_index.get(sym)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        loeuf[gi] = v
        # Fallback: use target loeuf median if no info available
        ctx.cache["_e412_loeuf"] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        loeuf = self._get_loeuf(ctx)

        # global fallback for missing LOEUF
        finite_loeuf = loeuf[np.isfinite(loeuf)]
        if finite_loeuf.size > 0:
            global_loeuf = float(np.median(finite_loeuf))
        else:
            global_loeuf = 1.0

        corr = ctx.gene_corr
        # percentile rank transform: rank / (n_genes - 1) mapped to [0,1]
        denom = max(ctx.n_genes - 1, 1)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # no measurable target: row stays zero
                continue

            # target LOEUF: average over measured target genes, fallback to global
            tgt_loeuf_vals = [loeuf[t] for t in tgt_idx if np.isfinite(loeuf[t])]
            if tgt_loeuf_vals:
                t_loeuf = float(np.mean(tgt_loeuf_vals))
            else:
                t_loeuf = global_loeuf

            # average correlation profile across target genes
            corr_profile = corr[tgt_idx, :].mean(axis=0)
            corr_profile = np.nan_to_num(corr_profile, nan=0.0, posinf=0.0, neginf=0.0)

            # percentile rank across genes
            order = np.argsort(corr_profile, kind="mergesort")
            ranks = np.empty(ctx.n_genes, dtype=float)
            ranks[order] = np.arange(ctx.n_genes, dtype=float)
            pct = ranks / denom

            out[i, :, 0] = pct * t_loeuf

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
