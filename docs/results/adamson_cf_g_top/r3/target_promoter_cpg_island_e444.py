import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGIslandE444(Feature):
    name = "target_promoter_cpg_island_e444"
    version = 2
    description = (
        "Per-gene CpG-island promoter flag combined with target identity: "
        "for each perturbation, the row marks the gene(s) targeted by that perturbation "
        "with a value derived from whether their promoter is a CpG island. "
        "Non-target genes get 0. This produces a perturbation-specific pattern."
    )
    rationale = (
        "CpG islands at promoters affect chromatin accessibility and CRISPRi efficiency. "
        "Encoding the CpG status of the targeted gene(s) lets the model learn "
        "target-specific responses contingent on promoter CpG content."
    )
    inputs = ["knowledge"]
    params = {"threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("threshold", 0.6))
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # Build per-gene CpG-island flag from knowledge (cached).
        cache = ctx.cache
        key = ("cpg_flag", threshold)
        gene_flag = cache.get(key)
        if gene_flag is None:
            gene_flag = np.zeros(ctx.n_genes, dtype=float)
            ann = ctx.knowledge("gene_annotation")
            if ann is not None:
                genes = ann.get("genes") or {}
                cols = ann.get("columns") or []
                idx = None
                for cand in ("cpg_oe_promoter", "cpg_island_promoter",
                             "cpg_island", "promoter_cpg_island"):
                    try:
                        idx = list(cols).index(cand)
                        break
                    except ValueError:
                        continue
                if idx is not None:
                    for g, vals in genes.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None or vals is None:
                            continue
                        try:
                            v = vals[idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        # Support both boolean (0/1) and continuous OE scores.
                        if fv > 1.0 or fv < 0.0:
                            flag = 1.0 if fv > threshold else 0.0
                        else:
                            flag = 1.0 if fv >= 0.5 else 0.0
                        gene_flag[gi] = flag
            cache[key] = gene_flag

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # Encode CpG status of targets; use a small positive/negative offset
            # so perturbations targeting CpG vs non-CpG genes differ.
            vals = gene_flag[t_idx]
            if vals.size > 0 and np.any(vals > 0):
                out[i, t_idx, 0] = 1.0
            else:
                # Non-CpG targets: mark with a distinct negative value
                out[i, t_idx, 0] = -1.0

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
