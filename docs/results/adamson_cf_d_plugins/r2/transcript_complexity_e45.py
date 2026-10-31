import numpy as np
from genemila.features.api import Feature, register


@register
class TranscriptComplexityE45(Feature):
    name = "transcript_complexity_e45"
    version = 1
    description = ("Composite gene-side feature from gene_annotation: standardized "
                   "n_transcripts, utr5_length, utr3_length, gc_utr3, gc_promoter, "
                   "cpg_oe_promoter, attached to every (pert, gene) row.")
    rationale = ("Post-transcriptional regulation via UTRs, GC content and CpG islands "
                 "affects mRNA stability/translation, modulating response magnitude.")
    inputs = ["gene_annotation"]
    params = {"columns": ["n_transcripts", "utr5_length", "utr3_length",
                          "gc_utr3", "gc_promoter", "cpg_oe_promoter"]}
    dim = 6

    def compute(self, ctx, perts, params):
        cols = params.get("columns", self.params["columns"])
        ann = ctx.knowledge("gene_annotation")

        gene_vals = np.full((ctx.n_genes, len(cols)), np.nan, dtype=float)

        if ann is not None:
            col_names = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            col_pos = {}
            for c in cols:
                if c in col_names:
                    col_pos[c] = col_names.index(c)

            for gi, g in enumerate(ctx.genes):
                row = genes_tbl.get(g)
                if row is None:
                    continue
                for j, c in enumerate(cols):
                    if c not in col_pos:
                        continue
                    try:
                        v = row[col_pos[c]]
                    except (IndexError, TypeError):
                        v = None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gene_vals[gi, j] = fv

        # Standardize each column (column-wise), using nan-aware stats.
        out_genes = np.zeros_like(gene_vals)
        for j in range(len(cols)):
            col = gene_vals[:, j]
            mask = np.isfinite(col)
            if mask.sum() >= 2:
                mu = col[mask].mean()
                sd = col[mask].std()
                if sd > 1e-12:
                    out_genes[mask, j] = (col[mask] - mu) / sd
                else:
                    out_genes[mask, j] = 0.0
            # non-finite entries remain 0

        n_perts = len(perts)
        out = np.empty((n_perts, ctx.n_genes, self.dim), dtype=float)
        out[:] = out_genes[np.newaxis, :, :]
        return out
