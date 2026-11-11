import numpy as np
from genemila.features.api import Feature, register


@register
class GcUtr3GeneE103(Feature):
    name = "gc_utr3_gene_e103"
    version = 1
    description = "GC content of each gene's 3' UTR from gene_annotation.gc_utr3, z-scored per gene."
    rationale = ("GC-rich 3' UTRs may form stable secondary structures that stabilize mRNA, "
                 "buffering perturbation-induced expression changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))
        if len(perts) == 0:
            return out

        cache = ctx.cache
        key = "gc_utr3_gene_e103_z"
        vec = cache.get(key)
        if vec is None:
            ann = ctx.knowledge("gene_annotation")
            vec = np.full(n_genes, np.nan, dtype=float)
            if ann is not None:
                cols = ann.get("columns", [])
                genes_tbl = ann.get("genes", {})
                if "gc_utr3" in cols:
                    ci = cols.index("gc_utr3")
                    for j, g in enumerate(ctx.genes):
                        vals = genes_tbl.get(g)
                        if vals is None:
                            continue
                        if ci < len(vals):
                            v = vals[ci]
                            if v is not None:
                                try:
                                    fv = float(v)
                                except (TypeError, ValueError):
                                    continue
                                if np.isfinite(fv):
                                    vec[j] = fv
            finite = np.isfinite(vec)
            if finite.any():
                med = np.median(vec[finite])
                vec[~finite] = med
                sd = vec.std()
                if sd > 0 and np.isfinite(sd):
                    vec = (vec - vec.mean()) / sd
                else:
                    vec = vec - vec.mean()
            else:
                vec = np.zeros(n_genes, dtype=float)
            cache[key] = vec

        out[:, :, 0] = vec[np.newaxis, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
