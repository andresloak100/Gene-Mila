import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGcCdsTimesAdditiveResponse(Feature):
    name = "target_gc_cds_times_additive_response_e435"
    version = 1
    description = ("Product of the mean GC content of coding sequences (gc_cds) of p's "
                   "target genes and additive_response.")
    rationale = ("GC content affects mRNA stability and translation efficiency, potentially "
                 "modulating the magnitude of CRISPRa-induced expression changes.")
    inputs = ["control_cells", "gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Load gene_annotation once and locate the gc_cds column.
        ann = ctx.knowledge("gene_annotation")
        gc_by_gene = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            if "gc_cds" in cols:
                gc_idx = cols.index("gc_cds")
                for sym, vals in genes_ann.items():
                    if vals is None:
                        continue
                    v = vals[gc_idx]
                    if v is None:
                        continue
                    try:
                        gc_by_gene[sym] = float(v)
                    except (TypeError, ValueError):
                        continue

        # Additive response feature (n_perts, n_genes, 1).
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        add_flat = add[:, :, 0] if add.shape[2] == 1 else add[:, :, 0]

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            gcs = [gc_by_gene[g] for g in tgenes if g in gc_by_gene]
            if not gcs:
                continue
            mean_gc = float(np.mean(gcs))
            out[i, :, 0] = mean_gc * add_flat[i, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
