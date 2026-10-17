import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintWeightedTargetResponseSimiE234(Feature):
    name = "constraint_weighted_target_response_simi_e234"
    version = 1
    description = ("For each gene g and perturbation p, average the similarity of g's "
                   "single-gene response to each target's response, weighted by inverse LOEUF.")
    rationale = ("LoF-intolerant (low LOEUF) targets may drive stronger, more specific "
                 "downstream effects, so their response similarity should be weighted more.")
    inputs = ["train_delta", "gene_constraint"]
    params = {"epsilon": 0.1}
    dim = 1

    def _lof_weights(self, ctx, targets, eps):
        kc = ctx.knowledge("gene_constraint")
        genes_tbl = None
        cols = None
        if isinstance(kc, dict):
            genes_tbl = kc.get("genes")
            cols = kc.get("columns")
        loeuf_idx = None
        if isinstance(cols, list):
            for j, c in enumerate(cols):
                if c == "oe_lof_upper":
                    loeuf_idx = j
                    break
        raw = []
        for t in targets:
            v = None
            if genes_tbl is not None and t in genes_tbl:
                row = genes_tbl[t]
                try:
                    if loeuf_idx is not None and loeuf_idx < len(row):
                        v = row[loeuf_idx]
                except Exception:
                    v = None
            if v is None or (isinstance(v, float) and not np.isfinite(v)):
                v = 1.0
            try:
                v = float(v)
            except Exception:
                v = 1.0
            if not np.isfinite(v) or v < 0:
                v = 1.0
            raw.append(1.0 / (v + eps))
        raw = np.asarray(raw, dtype=float)
        s = raw.sum()
        if not np.isfinite(s) or s <= 0:
            raw = np.ones(len(targets), dtype=float)
            s = raw.sum()
        return raw / s

    @staticmethod
    def _corr_row(gv, mat):
        # gv: (n_genes,), mat: (T, n_genes) -> (T,) Pearson correlations
        gv_c = gv - gv.mean()
        gv_norm = np.linalg.norm(gv_c)
        if gv_norm <= 0:
            return np.zeros(mat.shape[0], dtype=float)
        mc = mat - mat.mean(axis=1, keepdims=True)
        mn = np.linalg.norm(mc, axis=1)
        mn[mn <= 0] = np.inf
        return (mc @ gv_c) / (mn * gv_norm)

    def compute(self, ctx, perts, params):
        eps = float(params.get("epsilon", 0.1)) if params else 0.1
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        cache = ctx.cache

        for i, p in enumerate(perts):
            targets = list(ctx.target_genes(p))
            if not targets:
                continue
            w = self._lof_weights(ctx, targets, eps)

            # LEAKAGE RULE: exclude p when building the training deltas.
            tids, deltas = ctx.train_delta(exclude=p)
            if tids is None or len(tids) == 0:
                continue
            deltas = np.asarray(deltas, dtype=float)
            # Map single-gene perturbation id -> row index.
            id_to_row = {}
            for k, pid in enumerate(tids):
                if "+" not in pid:
                    id_to_row[pid] = k

            # Target response vectors (exclude missing / non-finite).
            tvecs = []
            tw = []
            for t, wt in zip(targets, w):
                k = id_to_row.get(t, None)
                if k is None:
                    continue
                v = deltas[k]
                if np.all(np.isfinite(v)):
                    tvecs.append(v)
                    tw.append(wt)
            if not tvecs:
                continue
            tvecs = np.stack(tvecs, axis=0)  # (T, n_genes)
            tw = np.asarray(tw, dtype=float)
            sw = tw.sum()
            if sw <= 0:
                continue
            tw = tw / sw

            # For each gene g with a single-gene training perturbation, compute
            # its weighted average similarity to the targets.
            for g, k in id_to_row.items():
                gidx = ctx.gene_index.get(g, None)
                if gidx is None:
                    continue
                gv = deltas[k]
                if not np.all(np.isfinite(gv)):
                    continue
                sims = self._corr_row(gv, tvecs)
                val = float(np.dot(sims, tw))
                if np.isfinite(val):
                    out[i, gidx, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
