import numpy as np
from genemila.features.api import Feature, register

@register
class CdsLengthLogE80(Feature):
    name = "cds_length_log_e80"
    version = 1
    description = "Log10 of cds_length for gene g, missing imputed with median."
    rationale = ("Longer coding sequences may stabilize mRNA and buffer expression "
                 "changes after perturbation, dampening the response magnitude.")
    inputs = ["gene_annotation"]
    params = {"transform": "log10"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                cds_idx = list(columns).index("cds_length")
            except ValueError:
                cds_idx = None
            if cds_idx is not None:
                for gi, g in enumerate(ctx.genes):
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
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0:
                        vals[gi] = fv

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
        else:
            med = 1.0
        vals[~finite] = med

        logged = np.log10(vals)
        logged[~np.isfinite(logged)] = np.log10(med) if med > 0 else 0.0

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = logged[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
