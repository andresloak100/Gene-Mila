import numpy as np
from genemila.features.api import Feature, register

@register
class TargetMisZInteractionE83(Feature):
    name = "target_mis_z_interaction_e83"
    version = 1
    description = ("Product of the target gene's missense constraint (mis_z) and "
                   "(1 - control_mean) of gene g, capturing stronger effects on "
                   "lowly expressed genes for missense-constrained targets.")
    rationale = ("Missense-constrained targets are functionally important; their "
                 "perturbation may produce broader downstream effects, especially "
                 "on lowly expressed genes that are more sensitive.")
    inputs = ["control_mean", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load gene_constraint prior knowledge.
        gc = ctx.knowledge("gene_constraint")
        mis_z_map = {}
        if gc is not None:
            cols = gc.get("columns", [])
            genes_tbl = gc.get("genes", {}) or {}
            if "mis_z" in cols:
                idx = cols.index("mis_z")
                for sym, vals in genes_tbl.items():
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
                        mis_z_map[sym] = fv

        control_mean = np.asarray(ctx.control_mean, dtype=float)
        # Low-expression weight: higher for lowly expressed genes.
        low_weight = 1.0 - control_mean
        low_weight = np.where(np.isfinite(low_weight), low_weight, 0.0)

        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            mz = 0.0
            found = False
            for tg in target_genes:
                if tg in mis_z_map:
                    mz += mis_z_map[tg]
                    found = True
            if not found:
                mz = 0.0
            out[i, :, 0] = mz * low_weight

        out = np.where(np.isfinite(out), out, 0.0)
        return out
