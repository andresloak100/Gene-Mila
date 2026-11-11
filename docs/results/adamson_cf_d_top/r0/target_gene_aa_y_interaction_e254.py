import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAAYInteraction(Feature):
    name = "target_gene_aa_y_interaction_e254"
    version = 1
    description = "Product of target gene's aa_Y and gene g's aa_Y from gene_annotation."
    rationale = ("Tyrosine phosphorylation is a key signaling mechanism; shared tyrosine "
                 "content between the perturbed target and a response gene may indicate "
                 "shared phosphorylation-dependent regulation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        aa_y = np.full(n_genes, np.nan, dtype=float)

        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            if "aa_Y" in cols:
                j = cols.index("aa_Y")
                for g, vals in genes_tbl.items():
                    idx = ctx.gene_index.get(g)
                    if idx is not None and vals is not None and j < len(vals):
                        v = vals[j]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                aa_y[idx] = fv

        # Replace missing with 0 so products are finite
        aa_y_filled = np.where(np.isfinite(aa_y), aa_y, 0.0)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # target aa_Y (mean if multiple targets)
            tvals = [aa_y_filled[t] for t in tidx if np.isfinite(aa_y[t])]
            if not tvals:
                # target has no aa_Y annotation -> all zeros
                continue
            t_aa_y = float(np.mean(tvals))
            out[i, :, 0] = t_aa_y * aa_y_filled

        out = np.where(np.isfinite(out), out, 0.0)
        return out
