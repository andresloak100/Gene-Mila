import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNExonsXIsTarget(Feature):
    name = "target_n_exons_x_is_target_e245"
    version = 1
    description = "Product of target gene's n_exons and is_target indicator."
    rationale = "Exon count may reflect gene complexity and regulatory mechanisms; interaction with target identity."
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        n_exons_map = {}
        if ann is not None and isinstance(ann, dict):
            genes_tbl = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                ex_idx = columns.index("n_exons")
            except ValueError:
                ex_idx = None
            if ex_idx is not None:
                for sym, vals in genes_tbl.items():
                    try:
                        v = vals[ex_idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is None:
                        n_exons_map[sym] = 0.0
                    else:
                        try:
                            fv = float(v)
                            if not np.isfinite(fv):
                                fv = 0.0
                        except (TypeError, ValueError):
                            fv = 0.0
                        n_exons_map[sym] = fv

        # Precompute per-gene n_exons aligned with ctx.genes
        gene_n_exons = np.zeros(ctx.n_genes, dtype=float)
        for gi, g in enumerate(ctx.genes):
            gene_n_exons[gi] = n_exons_map.get(g, 0.0)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # value for target gene = its n_exons
            vals = gene_n_exons[np.asarray(tidx, dtype=int)]
            # if multiple targets, take mean n_exons (usually one)
            tval = float(vals.mean()) if vals.size else 0.0
            if not np.isfinite(tval):
                tval = 0.0
            out[i, np.asarray(tidx, dtype=int), 0] = tval

        return out
