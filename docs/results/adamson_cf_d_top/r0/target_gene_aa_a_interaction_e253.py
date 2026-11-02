import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAaaInteractionE253(Feature):
    name = "target_gene_aa_a_interaction_e253"
    version = 1
    description = "Product of target gene's aa_A and gene g's aa_A from gene_annotation."
    rationale = "Shared alanine content may reflect common structural motifs or stability."
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        aa_a = None
        if ann is not None:
            genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                idx = columns.index("aa_A")
            except ValueError:
                idx = None
            if idx is not None:
                aa_a = np.full(ctx.n_genes, np.nan, dtype=float)
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None or idx >= len(vals):
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        aa_a[gi] = fv

        if aa_a is None:
            return out

        gene_aa = np.where(np.isfinite(aa_a), aa_a, 0.0)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            target_vals = gene_aa[t_idx]
            target_vals = target_vals[np.isfinite(target_vals)]
            if target_vals.size == 0:
                continue
            t_aa = float(np.mean(target_vals))
            out[i, :, 0] = t_aa * gene_aa

        out[~np.isfinite(out)] = 0.0
        return out
