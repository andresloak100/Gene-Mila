import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetMembraneSecrE559(Feature):
    name = "additive_response_x_target_membrane_secr_e559"
    version = 1
    description = ("Product of additive_response and the mean membrane or secreted "
                   "flag of the perturbation's target genes.")
    rationale = ("Membrane and secreted proteins may have different downstream effects "
                 "due to signal transduction versus intracellular regulation; the "
                 "modulation captures this interaction.")
    inputs = ["protein_annotation", "train_delta"]
    params = {"use_membrane": 1, "use_secreted": 1}
    dim = 1

    def _target_flag_means(self, ctx, params):
        cache = ctx.cache
        key = ("e559_flag_means", int(params.get("use_membrane", 1)),
               int(params.get("use_secreted", 1)))
        if key in cache:
            return cache[key]

        pa = ctx.knowledge("protein_annotation")
        cols = []
        gene_vals = {}
        if pa is not None and isinstance(pa, dict):
            columns = pa.get("columns", []) or []
            genes_tbl = pa.get("genes", {}) or {}
            use_mem = int(params.get("use_membrane", 1))
            use_sec = int(params.get("use_secreted", 1))
            idx_mem = columns.index("membrane") if "membrane" in columns else None
            idx_sec = columns.index("secreted") if "secreted" in columns else None
            for g, vals in genes_tbl.items():
                m = 0.0
                s = 0.0
                if use_mem and idx_mem is not None and idx_mem < len(vals):
                    v = vals[idx_mem]
                    m = float(v) if v is not None else 0.0
                if use_sec and idx_sec is not None and idx_sec < len(vals):
                    v = vals[idx_sec]
                    s = float(v) if v is not None else 0.0
                gene_vals[g] = max(m, s) if (m > 0 or s > 0) else 0.0

        def flag_mean(perts):
            out = np.zeros(len(perts), dtype=float)
            for i, p in enumerate(perts):
                tg = ctx.target_genes(p)
                if not tg:
                    continue
                vals = [gene_vals.get(g, 0.0) for g in tg]
                out[i] = float(np.mean(vals)) if vals else 0.0
            return out

        res = (flag_mean, gene_vals)
        cache[key] = res
        return res

    def compute(self, ctx, perts, params):
        flag_mean, _ = self._target_flag_means(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        means = flag_mean(perts)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)
            out[i, :, 0] = add * means[i]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
