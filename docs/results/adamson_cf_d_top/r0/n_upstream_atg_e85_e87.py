import numpy as np
from genemila.features.api import Feature, register

@register
class NUpstreamAtgE85E87(Feature):
    name = "n_upstream_atg_e85_e87"
    version = 1
    description = "Number of upstream ATGs in the 5' UTR of gene g from gene_annotation."
    rationale = ("Upstream ATGs repress translation initiation, reducing the protein-level "
                 "impact of perturbations and thus attenuating expression changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                idx = cols.index("n_upstream_atg")
            except ValueError:
                idx = None
            if idx is not None:
                for j, g in enumerate(ctx.genes):
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
                        vals[j] = fv

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
