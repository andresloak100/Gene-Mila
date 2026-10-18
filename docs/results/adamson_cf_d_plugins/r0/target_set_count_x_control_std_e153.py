import numpy as np
from genemila.features.api import Feature, register


@register
class TargetSetCountXControlStdE153(Feature):
    name = "target_set_count_x_control_std_e153"
    version = 1
    description = "Product of the number of gene sets containing the target of perturbation p and the control_std of gene g."
    rationale = "Perturbing hub-like targets with many set memberships may cause larger responses in genes with variable baseline expression."
    inputs = ["control_std", "gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        gene_sets = ctx.knowledge("gene_sets") or {}
        cache = ctx.cache

        if "set_membership_counts" not in cache:
            counts = {}
            for members in gene_sets.values():
                for g in members:
                    counts[g] = counts.get(g, 0) + 1
            cache["set_membership_counts"] = counts
        counts = cache["set_membership_counts"]

        control_std = np.asarray(ctx.control_std, dtype=float)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            c = 0
            for t in target_genes:
                c += counts.get(t, 0)
            if c != 0:
                out[i, :, 0] = float(c) * control_std

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
