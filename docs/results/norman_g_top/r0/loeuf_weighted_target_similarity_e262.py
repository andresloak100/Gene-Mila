import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufWeightedTargetResponseSimilarity(Feature):
    name = "loeuf_weighted_target_similarity_e262"
    version = 1
    description = (
        "For each gene g and perturbation p, weighted average of the Pearson "
        "correlation between g's single-gene response vector and each target "
        "gene's single-gene response vector, weighting each target by "
        "1/(LOEUF + eps) so that LoF-intolerant (low-LOEUF) targets count more."
    )
    rationale = (
        "Genes intolerant to loss-of-function (low LOEUF) are likely more "
        "sensitive/essential; their perturbation response profiles should be "
        "more informative about downstream gene responses, so their similarity "
        "to gene g should be weighted more heavily."
    )
    inputs = ["train_delta", "target_genes", "knowledge:gene_constraint"]
    params = {"eps": 0.01, "default_loeuf": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        eps = float(params.get("eps", 0.01))
        default_loeuf = float(params.get("default_loeuf", 1.0))

        n_genes = ctx.n_genes

        # ----- LOEUF lookup -------------------------------------------------
        loeuf = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[sym] = fv

        def standardize(v):
            v = np.asarray(v, dtype=float)
            v = np.where(np.isfinite(v), v, 0.0)
            mu = v.mean()
            sd = v.std()
            if sd < 1e-12:
                return None, 0.0
            return v - mu, sd

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # LEAKAGE RULE: exclude p's own label.
            train_ids, train_deltas = ctx.train_delta(exclude=p)

            # Build map: single-gene perturbation -> response vector
            gene_single = {}
            for j, pid in enumerate(train_ids):
                tg = ctx.target_genes(pid)
                if tg is not None and len(tg) == 1:
                    gi = ctx.gene_index.get(tg[0])
                    if gi is not None:
                        gene_single[gi] = train_deltas[j]

            std_cache = {}
            for gi, vec in gene_single.items():
                centered, sd = standardize(vec)
                if centered is not None:
                    std_cache[gi] = (centered, sd)

            targets = ctx.target_genes(p) or []
            target_gis = []
            weights = []
            for sym in targets:
                gi = ctx.gene_index.get(sym)
                if gi is None:
                    continue
                lv = loeuf.get(sym, default_loeuf)
                if not np.isfinite(lv):
                    lv = default_loeuf
                w = 1.0 / (max(lv, 0.0) + eps)
                target_gis.append(gi)
                weights.append(w)

            if not target_gis:
                continue

            weights = np.asarray(weights, dtype=float)
            wsum = weights.sum()
            if wsum <= 0 or not np.isfinite(wsum):
                weights = np.ones_like(weights)
                wsum = weights.sum()
            weights = weights / wsum

            col = np.zeros(n_genes, dtype=float)
            for gi, w in zip(target_gis, weights):
                if gi not in std_cache:
                    continue
                vi, sdi = std_cache[gi]
                n = vi.shape[0]
                for gj, (vj, sdj) in std_cache.items():
                    c = float(np.dot(vi, vj) / (n * sdi * sdj))
                    if np.isfinite(c):
                        col[gj] += w * c
            out[i, :, 0] = col

        out = np.where(np.isfinite(out), out, 0.0)
        return out
