import numpy as np
from genemila.features.api import Feature, register


@register
class GcCdsDirectE90(Feature):
    name = "gc_cds_direct_e90"
    version = 1
    description = "Continuous feature: GC content of coding sequence for gene g, from gene_annotation."
    rationale = (
        "High GC content stabilizes mRNA and reduces transcriptional responsiveness, "
        "leading to smaller perturbation effects."
    )
    inputs = ["gene_annotation"]
    params = {"column": "gc_cds"}
    dim = 1

    def compute(self, ctx, perts, params):
        col = params.get("column", "gc_cds")
        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        genes = ctx.genes

        vals = np.zeros(n_genes, dtype=np.float64)

        if ann is not None:
            table = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                ci = columns.index(col)
            except (ValueError, AttributeError):
                ci = None

            if ci is not None:
                for j, g in enumerate(genes):
                    row = table.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[j] = fv

        out = np.broadcast_to(vals[None, :, None], (len(perts), n_genes, 1)).copy()
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
