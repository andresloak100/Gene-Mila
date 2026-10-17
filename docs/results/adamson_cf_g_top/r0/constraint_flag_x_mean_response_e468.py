import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintFlagXMeanResponse(Feature):
    name = "constraint_flag_x_mean_response_e468"
    version = 1
    description = "Product of a binary indicator (gene g has any gnomAD constraint flag) and mean_response."
    rationale = ("Genes flagged as unreliable in gnomAD LoF constraint may be under unusual "
                 "selective pressures and respond differently to perturbations; interacting the "
                 "flag with the generic mean response isolates this effect.")
    inputs = ["control_cells", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # Build binary indicator of genes with any gnomAD constraint flag.
        flag = np.zeros(n_genes, dtype=np.float64)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            flags = kc.get("flags", {}) if isinstance(kc, dict) else {}
            for g, val in flags.items():
                idx = ctx.gene_index.get(g)
                if idx is None:
                    continue
                if val is None:
                    continue
                s = str(val).strip()
                if s and s.lower() != "none":
                    flag[idx] = 1.0

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mr = d.mean(axis=0)
            out[i, :, 0] = flag * mr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
