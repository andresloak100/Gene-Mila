import numpy as np
from genemila.features.api import Feature, FeatureContext, register

@register
class TargetGCpgOverlap(Feature):
    name = "target_g_cpg_overlap_e555"
    version = 1
    description = "Fraction of p's target genes sharing high/low CpG promoter status with gene g."
    rationale = ("CpG island promoters mark co-regulated genes; if a perturbation target and gene g "
                 "share CpG promoter status (both high or both low), their expression changes may be linked.")
    inputs = ["control_cells", "knowledge"]
    params = {"threshold_type": "median"}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None or "genes" not in ann:
            return out

        cols = ann.get("columns", [])
        try:
            cpg_col = cols.index("cpg_oe_promoter")
        except ValueError:
            return out

        gene_vals = ann["genes"]
        raw = np.full(n_genes, np.nan, dtype=float)
        for i, g in enumerate(ctx.genes):
            v = gene_vals.get(g)
            if v is None:
                continue
            try:
                x = v[cpg_col]
            except (IndexError, TypeError):
                continue
            if x is None:
                continue
            try:
                x = float(x)
            except (TypeError, ValueError):
                continue
            if np.isfinite(x):
                raw[i] = x

        # median over genes with finite values
        finite = raw[np.isfinite(raw)]
        if finite.size == 0:
            return out
        med = float(np.median(finite))

        # high/low status: 1 = high (>= median), 0 = low, NaN = unknown
        status = np.full(n_genes, np.nan, dtype=float)
        mask = np.isfinite(raw)
        status[mask] = (raw[mask] >= med).astype(float)

        # cache target status per perturbation id
        cache = ctx.cache
        key = "_tg_cpg_overlap_status"
        if key not in cache:
            cache[key] = {}
        tcache = cache[key]

        for i, p in enumerate(perts):
            if p in tcache:
                tstat = tcache[p]
            else:
                tidx = ctx.target_indices(p)
                tstat = status[tidx] if len(tidx) > 0 else np.array([], dtype=float)
                tstat = tstat[np.isfinite(tstat)]
                tcache[p] = tstat

            if tstat.size == 0:
                continue

            gstat = status  # (n_genes,)
            valid_g = np.isfinite(gstat)
            # fraction over targets of (target high == gene high)
            # tstat is 0/1; gstat 0/1 where valid
            match = (tstat[:, None] == gstat[None, :])  # (n_targets, n_genes)
            frac = match.sum(axis=0).astype(float)
            frac[~valid_g] = 0.0
            out[i, :, 0] = frac / float(tstat.size)

        out[~np.isfinite(out)] = 0.0
        return out
