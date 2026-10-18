import numpy as np
from genemila.features.api import Feature, register

@register
class GeneLengthFeaturesE12(Feature):
    name = "gene_length_features_e12"
    version = 1
    description = "Standardized gene_span_kb and intron_length_kb per gene."
    rationale = ("Longer genes or genes with longer introns may have distinct transcriptional "
                 "kinetics or chromatin environments, affecting perturbation responses.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 2

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 2))

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []

        # Locate column indices robustly
        def col_idx(name):
            try:
                return columns.index(name)
            except ValueError:
                return None

        i_span = col_idx("gene_span_kb")
        i_intron = col_idx("intron_length_kb")

        span = np.full(n_genes, np.nan)
        intron = np.full(n_genes, np.nan)

        for g, gi in ctx.gene_index.items():
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            if i_span is not None and i_span < len(vals):
                v = vals[i_span]
                if v is not None:
                    try:
                        span[gi] = float(v)
                    except (TypeError, ValueError):
                        pass
            if i_intron is not None and i_intron < len(vals):
                v = vals[i_intron]
                if v is not None:
                    try:
                        intron[gi] = float(v)
                    except (TypeError, ValueError):
                        pass

        def standardize(arr):
            a = arr.copy()
            mask = np.isfinite(a)
            if mask.sum() == 0:
                return np.zeros_like(a)
            mu = a[mask].mean()
            sd = a[mask].std()
            if not np.isfinite(sd) or sd == 0:
                a[mask] = 0.0
            else:
                a[mask] = (a[mask] - mu) / sd
            a[~mask] = 0.0
            return a

        span_z = standardize(span)
        intron_z = standardize(intron)

        out[:, :, 0] = span_z[None, :]
        out[:, :, 1] = intron_z[None, :]

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
