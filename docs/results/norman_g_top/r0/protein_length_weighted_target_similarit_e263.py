import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthWeightedTargetSimilarityE263(Feature):
    name = "protein_length_weighted_target_similarit_e263"
    version = 1
    description = ("For each gene g and perturbation p, max over targets t of "
                   "corr(g_response, t_response) * 1/(protein_length[t]+1).")
    rationale = ("Weighting target response similarity by inverse protein length "
                 "emphasizes targets with shorter proteins that may have faster dynamics.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load protein lengths
        plen = None
        for kname in ("protein_annotation",):
            kd = ctx.knowledge(kname)
            if kd is not None and "genes" in kd and "columns" in kd:
                cols = kd["columns"]
                if "protein_length" in cols:
                    idx = cols.index("protein_length")
                    plen = {}
                    for g, vals in kd["genes"].items():
                        try:
                            v = vals[idx]
                            if v is not None:
                                plen[g] = float(v)
                        except Exception:
                            pass
                    break

        cache = ctx.cache

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            # unique target indices
            t_idx = []
            t_w = []
            for t in tg:
                ti = ctx.gene_index.get(t)
                if ti is None:
                    continue
                pl = None
                if plen is not None:
                    pl = plen.get(t)
                if pl is None:
                    w = 1.0  # 1/(0+1) if unknown -> treat length as 0
                else:
                    if pl < 0:
                        pl = 0.0
                    w = 1.0 / (pl + 1.0)
                t_idx.append(ti)
                t_w.append(w)

            if len(t_idx) == 0:
                continue

            key = ("e263", p)
            if key in cache:
                out[i, :, 0] = cache[key]
                continue

            # Get training deltas excluding p
            pids, deltas = ctx.train_delta(exclude=p)
            if deltas.shape[0] < 2:
                row = np.zeros(n_genes, dtype=float)
                cache[key] = row
                out[i, :, 0] = row
                continue

            # Center deltas
            dmean = deltas.mean(axis=0)
            dstd = deltas.std(axis=0)
            dstd_safe = np.where(dstd > 1e-12, dstd, 1.0)
            dz = (deltas - dmean) / dstd_safe

            best = np.full(n_genes, -np.inf, dtype=float)

            for ti, w in zip(t_idx, t_w):
                tvec = dz[:, ti]
                tv_norm = np.sqrt(np.sum(tvec * tvec))
                if tv_norm < 1e-12:
                    continue
                # correlation of each gene's response vector with target's
                # corr = sum_g dz[:,g]*tvec / (||dz[:,g]|| * ||tvec||)
                num = dz.T @ tvec  # (n_genes,)
                g_norm = np.sqrt(np.sum(dz * dz, axis=0))
                g_norm_safe = np.where(g_norm > 1e-12, g_norm, 1.0)
                corr = num / (g_norm_safe * tv_norm)
                # invalid (zero-variance gene) -> 0
                corr = np.where(g_norm > 1e-12, corr, 0.0)
                weighted = corr * w
                best = np.maximum(best, weighted)

            row = np.where(np.isfinite(best), best, 0.0)
            cache[key] = row
            out[i, :, 0] = row

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
