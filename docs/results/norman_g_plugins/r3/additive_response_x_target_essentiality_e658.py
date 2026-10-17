import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveResponseXTargetEssentiality(Feature):
    name = "additive_response_x_target_essentiality_e658"
    version = 1
    description = "Product of additive_response and mean normalized LoF-intolerance (1 - LOEUF) of target genes."
    rationale = "Essentiality of targets may modulate the strength of downstream additive responses."
    inputs = ["control_cells", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # additive_response baseline (sum over target genes of each gene's mean delta)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim != 2:
            add = np.asarray(add).reshape(len(perts), ctx.n_genes)

        # load gene_constraint
        gc = ctx.knowledge("gene_constraint")
        gene_vals = {}
        loeuf_idx = None
        if gc is not None:
            cols = gc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                gene_vals = gc.get("genes", {}) or {}

        def essentiality(gene):
            v = gene_vals.get(gene)
            if v is None:
                return None
            try:
                loeuf = v[loeuf_idx]
            except Exception:
                return None
            if loeuf is None:
                return None
            try:
                loeuf = float(loeuf)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(loeuf):
                return None
            return 1.0 - loeuf

        # compute per-perturbation mean essentiality of targets
        mean_ess = np.zeros(len(perts), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = []
            for g in targets:
                e = essentiality(g)
                if e is not None:
                    vals.append(e)
            if vals:
                mean_ess[i] = float(np.mean(vals))
            else:
                mean_ess[i] = 0.0

        out[:, :, 0] = add * mean_ess[:, None]
        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
