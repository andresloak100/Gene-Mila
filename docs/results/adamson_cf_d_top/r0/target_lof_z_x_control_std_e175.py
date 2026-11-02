import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLofZXControlStd(Feature):
    name = "target_lof_z_x_control_std_e175"
    version = 1
    description = "Product of target gene's lof_z and gene g's control_std."
    rationale = ("LoF-intolerant targets may induce variable responses in genes "
                 "with high expression variability.")
    inputs = ["control_std", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # control_std per gene
        cstd = np.asarray(ctx.control_std, dtype=float)
        cstd = np.where(np.isfinite(cstd), cstd, 0.0)

        # Load gene_constraint table
        gc = ctx.knowledge("gene_constraint")
        lof_z_map = {}
        if gc is not None:
            cols = list(gc.get("columns", []))
            genes_tbl = gc.get("genes", {}) or {}
            if "lof_z" in cols:
                zi = cols.index("lof_z")
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[zi]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        lof_z_map[sym] = fv

        for i, p in enumerate(perts):
            # target gene(s) of perturbation p
            tg = ctx.target_genes(p)
            lof_val = 0.0
            if tg:
                # average over targets that have a value
                vals = [lof_z_map[g] for g in tg if g in lof_z_map]
                if vals:
                    lof_val = float(np.mean(vals))
            out[i, :, 0] = lof_val * cstd

        out = np.where(np.isfinite(out), out, 0.0)
        return out
