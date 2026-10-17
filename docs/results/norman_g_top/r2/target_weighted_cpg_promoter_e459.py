import numpy as np
from genemila.features.api import Feature, register


@register
class TargetWeightedCpgPromoter(Feature):
    name = "target_weighted_cpg_promoter_e459"
    version = 1
    description = ("Weighted average of cpg_oe_promoter over p's target genes, weights "
                   "proportional to |single-gene additive response|, times additive_response.")
    rationale = ("CpG island promoters mark regulatory genes; weighting by each target's "
                 "predicted contribution captures heterogeneity among pair targets.")
    inputs = ["gene_annotation", "train_delta", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load cpg_oe_promoter per gene from gene_annotation
        cpg = np.full(n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                cpg_idx = cols.index("cpg_oe_promoter")
            except ValueError:
                cpg_idx = None
            if cpg_idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cpg_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg[gi] = fv

        # Get additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.asarray(add, dtype=float)

        # Cache single-gene additive responses keyed by (exclude, gene_col)
        cache = ctx.cache.setdefault("e459_single_resp", {})

        def single_resp(exclude, gene_col):
            key = (exclude, gene_col)
            if key in cache:
                return cache[key]
            pids, deltas = ctx.train_delta(exclude=exclude)
            gname = ctx.genes[gene_col]
            val = 0.0
            found = False
            for j, pid in enumerate(pids):
                if pid == gname:
                    val = float(deltas[j, gene_col])
                    found = True
                    break
            if not found:
                # fall back to mean column response if single not present
                if deltas.shape[0] > 0:
                    val = float(deltas[:, gene_col].mean())
            cache[key] = val
            return val

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            cpg_vals = np.array([cpg[t] for t in tidx], dtype=float)
            resp = np.array([single_resp(p, t) for t in tidx], dtype=float)
            w = np.abs(resp)
            valid = np.isfinite(cpg_vals) & np.isfinite(w)
            if valid.any():
                wv = w[valid]
                cv = cpg_vals[valid]
                s = wv.sum()
                if s > 0:
                    weighted = float((wv * cv).sum() / s)
                else:
                    weighted = float(cv.mean())
            else:
                # no valid cpg values
                cv_all = cpg_vals[np.isfinite(cpg_vals)]
                if cv_all.size > 0:
                    weighted = float(cv_all.mean())
                else:
                    weighted = 0.0
            out[i, :, 0] = weighted * add[i]

        out[~np.isfinite(out)] = 0.0
        return out
