import numpy as np
from genemila.features.api import Feature, register

@register
class CdsLengthGeneE112E127(Feature):
    name = "cds_length_gene_e112_e127"
    version = 1
    description = "Length of the coding sequence (CDS) of gene g in base pairs."
    rationale = ("Longer CDS may correlate with mRNA stability and protein half-life, "
                 "dampening expression changes after perturbation.")
    inputs = ["gene_annotation"]
    params = {"log_transform": True, "impute": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        log_transform = params.get("log_transform", True)
        impute = params.get("impute", "median")

        ann = ctx.knowledge("gene_annotation")
        cols = ann.get("columns", []) if ann else []
        genes = ann.get("genes", {}) if ann else {}

        try:
            cds_idx = cols.index("cds_length")
        except ValueError:
            cds_idx = None

        n_genes = ctx.n_genes
        raw = np.full(n_genes, np.nan, dtype=float)
        if cds_idx is not None:
            for g, vals in genes.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                try:
                    v = vals[cds_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    raw[gi] = fv

        # Impute missing values
        missing = ~np.isfinite(raw)
        if missing.any():
            observed = raw[~missing]
            if observed.size > 0:
                if impute == "median":
                    fill = float(np.median(observed))
                elif impute == "mean":
                    fill = float(np.mean(observed))
                elif impute == "zero":
                    fill = 0.0
                else:
                    fill = float(np.median(observed))
            else:
                fill = 0.0
            raw[missing] = fill

        if log_transform:
            # log1p to handle zeros and keep monotonic
            vec = np.log1p(np.maximum(raw, 0.0))
        else:
            vec = raw

        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        return out
