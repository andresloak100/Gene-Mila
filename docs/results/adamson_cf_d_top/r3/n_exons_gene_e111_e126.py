import numpy as np
from genemila.features.api import Feature, register


@register
class NExonsGeneE111E126(Feature):
    name = "n_exons_gene_e111_e126"
    version = 1
    description = "Number of exons in gene g (from gene_annotation table, column n_exons)."
    rationale = ("Genes with more exons have longer transcription units and more splicing events, "
                 "making them more vulnerable to perturbation-induced expression changes.")
    inputs = ["gene_annotation"]
    params = {"log_transform": True, "impute": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        log_transform = params.get("log_transform", True)
        impute = params.get("impute", "median")

        ann = ctx.knowledge("gene_annotation")
        genes_ann = ann.get("genes", {}) if ann else {}
        columns = ann.get("columns", []) if ann else []

        try:
            col_idx = columns.index("n_exons")
        except ValueError:
            col_idx = None

        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        if col_idx is not None:
            for g in range(n_genes):
                sym = ctx.genes[g]
                rec = genes_ann.get(sym)
                if rec is None:
                    continue
                try:
                    v = rec[col_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals[g] = fv

        # Impute missing values
        finite_mask = np.isfinite(vals)
        if finite_mask.any():
            if impute == "median":
                fill = float(np.median(vals[finite_mask]))
            elif impute == "mean":
                fill = float(np.mean(vals[finite_mask]))
            else:
                fill = 0.0
        else:
            fill = 0.0
        vals[~finite_mask] = fill

        # Log transform if skewed
        if log_transform:
            vals = np.log1p(np.clip(vals, 0.0, None))

        # Broadcast the same per-gene value across all perturbations
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
