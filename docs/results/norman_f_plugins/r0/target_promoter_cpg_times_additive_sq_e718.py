import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgTimesAdditiveSq(Feature):
    name = "target_promoter_cpg_times_additive_sq_e718"
    version = 1
    description = "Mean promoter CpG observed/expected ratio over targets times additive_response_squared."
    rationale = ("Promoter CpG content modulates epigenetic regulation; interacting it with the "
                 "squared additive response emphasizes CpG-dependent amplification of large responses.")
    inputs = ["gene_annotation", "additive_response_squared_e242"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Load gene annotation for cpg_oe_promoter
        ann = ctx.knowledge("gene_annotation") or {}
        genes_map = ann.get("genes", {}) if isinstance(ann, dict) else {}
        columns = ann.get("columns", []) if isinstance(ann, dict) else []
        cpg_idx = None
        for j, c in enumerate(columns):
            if c == "cpg_oe_promoter":
                cpg_idx = j
                break
        if cpg_idx is None:
            cpg_idx = 11  # fallback position per annotation ordering

        # Build per-gene cpg_oe vector aligned to ctx.genes
        cpg_oe = np.zeros(n_genes, dtype=np.float64)
        if isinstance(genes_map, dict) and len(genes_map) > 0:
            for gi, g in enumerate(ctx.genes):
                vals = genes_map.get(g)
                if vals is None:
                    continue
                try:
                    v = vals[cpg_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    cpg_oe[gi] = fv

        # Get additive_response_squared feature (n_perts, n_genes, 1)
        arsq = ctx.feature("additive_response_squared_e242", perts, params=None)
        arsq = np.asarray(arsq, dtype=np.float64)
        if arsq.ndim == 2:
            arsq = arsq[:, :, None]
        if arsq.shape[0] != n_perts or arsq.shape[1] != n_genes:
            # fallback: recompute from additive_response if shape mismatch
            ar = ctx.feature("additive_response", perts, params=None)
            ar = np.asarray(ar, dtype=np.float64)
            if ar.ndim == 2:
                ar = ar[:, :, None]
            arsq = ar * ar

        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg:
                idxs = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
                if idxs:
                    mean_cpg = float(np.mean(cpg_oe[idxs]))
                else:
                    mean_cpg = 0.0
            else:
                mean_cpg = 0.0
            out[i, :, 0] = mean_cpg * arsq[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
