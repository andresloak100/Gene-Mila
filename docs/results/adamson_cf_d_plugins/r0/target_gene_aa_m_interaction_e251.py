import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAaMInteraction(Feature):
    name = "target_gene_aa_m_interaction_e251"
    version = 1
    description = "Product of target gene's aa_M and gene g's aa_M from gene_annotation."
    rationale = ("Shared methionine content may indicate susceptibility to oxidative stress "
                 "and common regulation.")
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        aa_m = np.zeros(ctx.n_genes, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                col_idx = cols.index("aa_M")
            except ValueError:
                col_idx = None
            genes_dict = ann.get("genes", {})
            if col_idx is not None:
                for sym, idx in ctx.gene_index.items():
                    vals = genes_dict.get(sym)
                    if vals is None:
                        continue
                    v = vals[col_idx]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            aa_m[idx] = fv

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_vals = aa_m[t_idx]
            # target aa_M: mean over target genes (usually one)
            target_val = float(np.mean(t_vals)) if t_vals.size else 0.0
            if not np.isfinite(target_val):
                target_val = 0.0
            out[i, :, 0] = target_val * aa_m

        out[~np.isfinite(out)] = 0.0
        return out
