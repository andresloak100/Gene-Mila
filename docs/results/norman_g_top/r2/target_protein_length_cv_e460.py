import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthCV(Feature):
    name = "target_protein_length_cv_e460"
    version = 1
    description = "Coefficient of variation of protein length across the perturbation's target genes (0 for singles)."
    rationale = "Heterogeneity in target protein sizes may reflect diverse regulatory functions, affecting response complexity."
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        anno = ctx.knowledge("protein_annotation")
        cols = anno.get("columns", []) if anno else []
        genes_tbl = anno.get("genes", {}) if anno else {}
        try:
            plen_idx = cols.index("protein_length")
        except (ValueError, AttributeError):
            plen_idx = 0

        cache = {}

        def get_plen(gene):
            if gene in cache:
                return cache[gene]
            val = None
            row = genes_tbl.get(gene)
            if row is not None:
                try:
                    v = row[plen_idx]
                    if v is not None:
                        fv = float(v)
                        if np.isfinite(fv):
                            val = fv
                except (TypeError, ValueError, IndexError):
                    val = None
            cache[gene] = val
            return val

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if len(targets) < 2:
                out[i, :, 0] = 0.0
                continue
            vals = [get_plen(g) for g in targets]
            vals = [v for v in vals if v is not None]
            if len(vals) < 2:
                out[i, :, 0] = 0.0
                continue
            arr = np.asarray(vals, dtype=float)
            mean = arr.mean()
            if mean > 0:
                cv = arr.std() / mean
            else:
                cv = 0.0
            if not np.isfinite(cv):
                cv = 0.0
            out[i, :, 0] = cv

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
