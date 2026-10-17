import numpy as np
from genemila.features.api import Feature, register


@register
class LofResponseSimilarityInteractionE570(Feature):
    name = "lof_response_similarity_interaction_e570"
    version = 1
    description = ("Product of lof_weighted_target_response_similarity_e201 and the mean "
                   "LOEUF (oe_lof_upper) of the perturbation's target genes.")
    rationale = ("Loss-of-function intolerance of the target gene may modulate how strongly "
                 "target response similarity translates into downstream deltas; intolerant "
                 "(high LOEUF) genes may show stronger downstream effects.")
    inputs = ["control_cells", "gene_corr", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _lof_table(self, ctx, params):
        cache = ctx.cache
        key = "__lof_oe_upper_e570__"
        if key in cache:
            return cache[key]
        table = {}
        try:
            kd = ctx.knowledge("gene_constraint")
        except Exception:
            kd = None
        if kd is not None:
            cols = kd.get("columns", [])
            genes = kd.get("genes", {})
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        table[g] = fv
        cache[key] = table
        return table

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        lof = self._lof_table(ctx, params)

        # Global fallback: mean of available LOEUF values (or 0 if none).
        if lof:
            global_mean = float(np.mean(list(lof.values())))
        else:
            global_mean = 0.0

        # Composition feature.
        try:
            base = ctx.feature("lof_weighted_target_response_similarity_e201", perts, params)
        except Exception:
            base = None

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [lof[g] for g in targets if g in lof]
            if vals:
                mean_lof = float(np.mean(vals))
            else:
                mean_lof = global_mean

            if base is not None:
                b = np.asarray(base[i], dtype=float).reshape(ctx.n_genes, -1)
                # take first column if multi-dim
                col = b[:, 0] if b.shape[1] > 0 else np.zeros(ctx.n_genes)
            else:
                col = np.zeros(ctx.n_genes)

            out[i, :, 0] = mean_lof * col

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
