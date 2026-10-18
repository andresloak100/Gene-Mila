import numpy as np
from genemila.features.api import Feature, register


@register
class CdsLengthGeneE128E140(Feature):
    name = "cds_length_gene_e128_e140"
    version = 1
    description = "Per-gene log10 CDS length from gene_annotation, median-imputed for missing values."
    rationale = ("Longer coding sequences may indicate larger/more buffered proteins with slower "
                 "translation, reducing the magnitude of expression change upon perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                cds_idx = cols.index("cds_length")
            except ValueError:
                cds_idx = None

            if cds_idx is not None:
                for g in ctx.genes:
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[cds_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        vals[ctx.gene_index[g]] = v

        # log10 transform for positive values; treat non-positive as missing
        with np.errstate(invalid="ignore", divide="ignore"):
            logged = np.where(vals > 0, np.log10(vals), np.nan)

        finite = np.isfinite(logged)
        if finite.any():
            fill = float(np.median(logged[finite]))
        else:
            fill = 0.0
        logged = np.where(finite, logged, fill)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = logged[np.newaxis, :]
        return out
