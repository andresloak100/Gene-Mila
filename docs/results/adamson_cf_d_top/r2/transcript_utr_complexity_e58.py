import numpy as np
from genemila.features.api import Feature, register

@register
class TranscriptUtrComplexityE58(Feature):
    name = "transcript_utr_complexity_e58"
    version = 1
    description = "Per-gene transcript architecture features (n_exons, transcript_length, cds_length, gc_utr3, n_upstream_atg), standardized."
    rationale = "Transcript architecture influences mRNA half-life and translation efficiency, modulating expression response to perturbations."
    inputs = ["gene_annotation"]
    params = {}
    dim = 5

    _COLS = ["n_exons", "transcript_length", "cds_length", "gc_utr3", "n_upstream_atg"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim), dtype=float)

        raw = None
        if "matrix" not in ctx.cache:
            ann = ctx.knowledge("gene_annotation")
            cols = None
            genes_map = None
            if isinstance(ann, dict):
                cols = ann.get("columns")
                genes_map = ann.get("genes")
            mat = np.full((n_genes, self.dim), np.nan, dtype=float)
            if isinstance(cols, list) and isinstance(genes_map, dict):
                try:
                    idxs = [cols.index(c) for c in self._COLS]
                except ValueError:
                    idxs = None
                if idxs is not None:
                    for gi, g in enumerate(ctx.genes):
                        vals = genes_map.get(g)
                        if vals is None:
                            continue
                        for j, ci in enumerate(idxs):
                            try:
                                v = vals[ci]
                            except (IndexError, TypeError):
                                v = None
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                mat[gi, j] = fv
            ctx.cache["matrix"] = mat
        raw = ctx.cache["matrix"]

        # Standardize per column using finite entries; missing -> 0 after standardization.
        std_mat = np.zeros_like(raw)
        for j in range(self.dim):
            col = raw[:, j]
            finite = np.isfinite(col)
            if not np.any(finite):
                continue
            vals = col[finite]
            mu = vals.mean()
            sd = vals.std()
            if sd <= 1e-12 or not np.isfinite(sd):
                sd = 1.0
            z = np.zeros(n_genes, dtype=float)
            z[finite] = (vals - mu) / sd
            std_mat[:, j] = z

        # Same per-gene features for every perturbation row.
        out[:] = std_mat[np.newaxis, :, :]
        return out
