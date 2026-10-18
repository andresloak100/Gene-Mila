import numpy as np
from genemila.features.api import Feature, register

@register
class TargetGeneAaNInteraction(Feature):
    name = "target_gene_aa_n_interaction_e250"
    version = 1
    description = "Product of target gene's aa_N and gene g's aa_N from gene_annotation."
    rationale = ("Shared asparagine content may reflect common interaction interfaces or "
                 "post-translational modification sites, so the product of target and "
                 "response-gene asparagine fractions may predict co-regulation.")
    inputs = ["gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        aa_n = np.zeros(n_genes, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                idx = cols.index("aa_N")
            except ValueError:
                idx = None
            if idx is not None:
                genes_map = ann.get("genes", {})
                for g, gi in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    if idx < len(vals):
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                aa_n[gi] = fv

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_val = aa_n[t_idx[0]]
            if t_val == 0.0:
                continue
            out[i, :, 0] = t_val * aa_n

        out[~np.isfinite(out)] = 0.0
        return out
