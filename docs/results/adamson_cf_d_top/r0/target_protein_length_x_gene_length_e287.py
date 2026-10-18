import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthXGeneLength(Feature):
    name = "target_protein_length_x_gene_length_e287"
    version = 1
    description = "Product of target gene's protein_length and gene g's gene_span_kb."
    rationale = "Longer proteins may mediate more interactions, amplifying effects on long genes."
    inputs = ["protein_annotation", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # ---- protein_length per gene (target side) ----
        prot_len = np.full(n_genes, np.nan, dtype=float)
        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            cols = pa.get("columns", [])
            try:
                pl_idx = cols.index("protein_length")
            except ValueError:
                pl_idx = 0
            genes_map = pa.get("genes", {}) or {}
            for g, vals in genes_map.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                v = vals[pl_idx] if pl_idx < len(vals) else None
                if v is not None:
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        prot_len[gi] = fv
        if np.all(np.isnan(prot_len)):
            prot_len_filled = np.ones(n_genes, dtype=float)
        else:
            med_pl = np.nanmedian(prot_len)
            if not np.isfinite(med_pl):
                med_pl = 1.0
            prot_len_filled = np.where(np.isnan(prot_len), med_pl, prot_len)

        # ---- gene_span_kb per gene (response side) ----
        span = np.full(n_genes, np.nan, dtype=float)
        ga = ctx.knowledge("gene_annotation")
        if ga is not None:
            cols = ga.get("columns", [])
            try:
                sp_idx = cols.index("gene_span_kb")
            except ValueError:
                sp_idx = 0
            genes_map = ga.get("genes", {}) or {}
            for g, vals in genes_map.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                v = vals[sp_idx] if sp_idx < len(vals) else None
                if v is not None:
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        span[gi] = fv
        if np.all(np.isnan(span)):
            span_filled = np.ones(n_genes, dtype=float)
        else:
            med_sp = np.nanmedian(span)
            if not np.isfinite(med_sp):
                med_sp = 1.0
            span_filled = np.where(np.isnan(span), med_sp, span)

        # ---- per perturbation: target protein length ----
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                tpl = float(np.mean(prot_len_filled[tgt_idx]))
            else:
                tpl = float(np.nanmedian(prot_len_filled))
            if not np.isfinite(tpl):
                tpl = 1.0
            out[i, :, 0] = tpl * span_filled

        out[~np.isfinite(out)] = 0.0
        return out
