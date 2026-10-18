import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAaVInteractionE252(Feature):
    name = "target_gene_aa_v_interaction_e252"
    version = 1
    description = "Product of target gene's aa_V and gene g's aa_V from gene_annotation."
    rationale = ("Shared valine content may indicate similar hydrophobic core properties "
                 "or membrane association; valine-rich targets may elicit larger responses "
                 "in valine-rich genes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        ann = ctx.knowledge("gene_annotation")
        aa_v = np.zeros(n_genes, dtype=float)
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("aa_V")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    if idx >= len(vals):
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        aa_v[gi] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            t_vals = aa_v[tgt_idx]
            t_vals = t_vals[np.isfinite(t_vals)]
            if t_vals.size == 0:
                continue
            t_mean = float(t_vals.mean())
            out[i, :, 0] = t_mean * aa_v
        return out
