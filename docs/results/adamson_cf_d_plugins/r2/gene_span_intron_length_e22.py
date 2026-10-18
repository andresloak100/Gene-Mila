import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class GeneSpanIntronLengthE22(Feature):
    name = "gene_span_intron_length_e22"
    version = 1
    description = "Gene span (kb) and intron length (kb) per gene from gene_annotation."
    rationale = (
        "Residual magnitude negatively correlates with gene span and intron length "
        "(rho ~ -0.30, -0.29); large genes with long introns may have smaller "
        "unexplained residuals due to transcriptional kinetics or chromatin context."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 2

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 2), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        cols = ann.get("columns", [])
        try:
            i_span = cols.index("gene_span_kb")
            i_intron = cols.index("intron_length_kb")
        except ValueError:
            return out

        genes_tbl = ann.get("genes", {}) or {}

        span = np.full(n_genes, np.nan, dtype=float)
        intron = np.full(n_genes, np.nan, dtype=float)

        for gi, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            try:
                v_span = vals[i_span]
                v_intron = vals[i_intron]
            except (IndexError, TypeError):
                continue
            if v_span is not None:
                try:
                    span[gi] = float(v_span)
                except (TypeError, ValueError):
                    pass
            if v_intron is not None:
                try:
                    intron[gi] = float(v_intron)
                except (TypeError, ValueError):
                    pass

        # Fill missing values with column means (finite fallback)
        for arr in (span, intron):
            finite = np.isfinite(arr)
            if finite.any():
                arr[~finite] = arr[finite].mean()
            else:
                arr[:] = 0.0

        out[:, :, 0] = span[None, :]
        out[:, :, 1] = intron[None, :]
        return out
