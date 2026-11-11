import numpy as np
from genemila.features.api import Feature, register


@register
class ObsLofGene(Feature):
    name = "obs_lof_gene_e114_e129"
    version = 1
    description = "Number of observed loss-of-function variants for gene g from gnomAD."
    rationale = ("Genes with more observed LoF variants in the population are more tolerant to "
                 "loss of function, suggesting their expression is less sensitive to perturbation.")
    inputs = ["gene_constraint"]
    params = {"impute": 0}
    dim = 1

    def compute(self, ctx, perts, params):
        impute = float(params.get("impute", 0))
        n_genes = ctx.n_genes
        vals = np.full(n_genes, impute, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []
            try:
                idx = list(columns).index("obs_lof")
            except ValueError:
                idx = None
            if idx is not None:
                for g, col in ctx.gene_index.items():
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[col] = fv

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[np.newaxis, :]
        return np.nan_to_num(out, nan=impute, posinf=impute, neginf=impute)
