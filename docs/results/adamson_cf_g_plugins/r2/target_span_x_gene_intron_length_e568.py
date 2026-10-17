import numpy as np
from genemila.features.api import Feature, register


@register
class TargetSpanXGeneIntronLength(Feature):
    name = "target_span_x_gene_intron_length_e568"
    version = 1
    description = "Product of target gene span (kb) and gene g's intron length (kb) from gene_annotation."
    rationale = (
        "Gene span and intron length are both associated with regulatory complexity; "
        "an interaction between target span and gene intron length may capture shared "
        "regulatory burden."
    )
    inputs = ["control_cells", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        cols = ann.get("columns", [])
        genes_tbl = ann.get("genes", {}) or {}

        try:
            span_idx = cols.index("gene_span_kb")
        except ValueError:
            span_idx = 0
        try:
            intron_idx = cols.index("intron_length_kb")
        except ValueError:
            intron_idx = None

        # Per gene-g intron length vector (kb), NaN -> 0
        intron_vec = np.zeros(n_genes, dtype=float)
        for gi, gname in enumerate(ctx.genes):
            vals = genes_tbl.get(gname)
            if vals is None:
                continue
            if intron_idx is not None and intron_idx < len(vals) and vals[intron_idx] is not None:
                try:
                    v = float(vals[intron_idx])
                    if np.isfinite(v):
                        intron_vec[gi] = v
                except (TypeError, ValueError):
                    pass

        for i, p in enumerate(perts):
            # Target gene span (kb)
            span = 0.0
            tgenes = ctx.target_genes(p)
            for tg in tgenes:
                vals = genes_tbl.get(tg)
                if vals is None:
                    continue
                if span_idx < len(vals) and vals[span_idx] is not None:
                    try:
                        v = float(vals[span_idx])
                        if np.isfinite(v):
                            span += v
                    except (TypeError, ValueError):
                        pass
            if span != 0.0:
                out[i, :, 0] = span * intron_vec

        return out
