import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgMeanTimesAdditiveResponseE375(Feature):
    name = "target_cpg_mean_times_additive_response_e375"
    version = 1
    description = ("Product of the mean CpG island promoter score (cpg_oe_promoter) "
                   "of p's target genes and the additive_response feature.")
    rationale = ("Promoter CpG islands influence transcriptional regulation and may affect "
                 "CRISPRa efficacy, so interacting the target CpG score with the additive "
                 "response can capture context-dependent effects.")
    inputs = ["control_cells", "gene_annotation", "feature"]
    params = {}
    dim = 1

    def _cpg_column(self, ctx):
        cache = ctx.cache
        if "_cpg_col_e375" in cache:
            return cache["_cpg_col_e375"]
        ann = ctx.knowledge("gene_annotation")
        col = None
        if ann is not None:
            cols = ann.get("columns", [])
            if "cpg_oe_promoter" in cols:
                col = cols.index("cpg_oe_promoter")
        if col is None:
            cache["_cpg_col_e375"] = None
            return None
        genes_tbl = ann.get("genes", {}) or {}
        arr = np.full(ctx.n_genes, np.nan, dtype=float)
        for i, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            try:
                v = vals[col]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                arr[i] = fv
        cache["_cpg_col_e375"] = arr
        return arr

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        if n == 0:
            return out

        cpg = self._cpg_column(ctx)

        add = ctx.feature("additive_response", perts, params=None)
        if add is None:
            return out
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        elif add.ndim == 1:
            add = add[:, None, None]
        add2 = add[:, :, 0]

        # fallback mean over all genes when nothing usable
        if cpg is not None:
            finite_all = cpg[np.isfinite(cpg)]
        else:
            finite_all = np.array([], dtype=float)
        global_mean = float(finite_all.mean()) if finite_all.size > 0 else 0.0

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if cpg is not None and len(tgt) > 0:
                vals = cpg[np.asarray(tgt, dtype=int)]
                vals = vals[np.isfinite(vals)]
                score = float(vals.mean()) if vals.size > 0 else global_mean
            else:
                score = global_mean
            out[i, :, 0] = score * add2[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
