import numpy as np
from genemila.features.api import Feature, register


@register
class NuclearGeneXLoeufTarget(Feature):
    name = "nuclear_gene_x_loeuf_target_e467"
    version = 1
    description = (
        "Product of a binary indicator (gene g encodes a nuclear protein) and "
        "(1 - LOEUF_target)."
    )
    rationale = (
        "Essential genes often regulate core processes; their perturbation may "
        "affect compartment-specific gene modules, here focusing on nuclear proteins."
    )
    inputs = ["protein_annotation", "gene_constraint", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- Nuclear indicator per gene ---
        nuclear = np.zeros(n_genes, dtype=float)
        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            genes_map = prot.get("genes", {})
            cols = prot.get("columns", [])
            try:
                nuc_idx = cols.index("nucleus")
            except ValueError:
                nuc_idx = None
            if nuc_idx is not None:
                for g, col_idx in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[nuc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        if float(v) > 0:
                            nuclear[col_idx] = 1.0
                    except (TypeError, ValueError):
                        continue

        # --- LOEUF per gene ---
        loeuf = np.full(n_genes, np.nan, dtype=float)
        cons = ctx.knowledge("gene_constraint")
        if cons is not None:
            genes_map = cons.get("genes", {})
            cols = cons.get("columns", [])
            try:
                lof_idx = cols.index("oe_lof_upper")
            except ValueError:
                lof_idx = None
            if lof_idx is not None:
                for g, col_idx in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[lof_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        loeuf[col_idx] = float(v)
                    except (TypeError, ValueError):
                        continue

        # Fallback LOEUF for genes without data: use median of available
        valid = np.isfinite(loeuf)
        if valid.any():
            fill = float(np.median(loeuf[valid]))
        else:
            fill = 1.0
        loeuf_filled = np.where(valid, loeuf, fill)
        # Clamp to [0,1] for a sensible (1 - LOEUF)
        loeuf_filled = np.clip(loeuf_filled, 0.0, 1.0)
        one_minus_loeuf = 1.0 - loeuf_filled

        # --- Per-perturbation target LOEUF ---
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                tl = loeuf_filled[np.asarray(tgt_idx, dtype=int)]
                # use mean if multiple targets
                loeuf_target = float(np.mean(tl))
            else:
                loeuf_target = fill
            loeuf_target = min(max(loeuf_target, 0.0), 1.0)
            factor = 1.0 - loeuf_target
            out[i, :, 0] = nuclear * factor

        return out
