import numpy as np
from genemila.features.api import Feature, register


@register
class TrainDeltaTransferSimilarityWeightedE293(Feature):
    name = "train_delta_transfer_similarity_weighted_e293"
    version = 1
    description = ("Cosine-similarity weighted average of training deltas, scaled by "
                   "the target protein's length from protein_annotation.")
    rationale = ("Longer proteins may have broader/pleiotropic effects, so scaling the "
                 "transfer-similarity prediction by target protein length can refine it.")
    inputs = ["train_delta", "control_cells", "protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Precompute control-cell based target expression profile (mean-centred).
        ctrl = np.asarray(ctx.control_cells, dtype=float)
        ctrl_mean = ctrl.mean(axis=0)
        ctrl_std = ctrl.std(axis=0)
        ctrl_std_safe = np.where(ctrl_std > 1e-8, ctrl_std, 1.0)
        ctrl_z = (ctrl - ctrl_mean) / ctrl_std_safe  # (n_cells, n_genes)

        # Protein length lookup.
        prot_len = self._protein_lengths(ctx)

        # Median protein length for missing / fallback scaling.
        valid_lens = np.array([v for v in prot_len.values() if np.isfinite(v) and v > 0],
                              dtype=float)
        median_len = float(np.median(valid_lens)) if valid_lens.size else 1.0

        for i, p in enumerate(perts):
            train_ids, deltas = ctx.train_delta(exclude=p)
            deltas = np.asarray(deltas, dtype=float)  # (n_train, n_genes)

            # Target gene expression profile of p (mean-centred z across control cells).
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                # No measured target: fall back to plain mean delta, scaled.
                base = deltas.mean(axis=0) if deltas.shape[0] > 0 else np.zeros(n_genes)
            else:
                # Use the first measured target gene as anchor.
                t = tgt_idx[0]
                t_profile = ctrl_z[:, t]  # (n_cells,)

                # For each training perturbation, compare control-cell expression of
                # the training target gene to the query target gene (cosine similarity).
                weights = np.zeros(deltas.shape[0], dtype=float)
                for j, tp in enumerate(train_ids):
                    tp_idx = ctx.target_indices(tp)
                    if len(tp_idx) == 0:
                        weights[j] = 0.0
                        continue
                    tj = tp_idx[0]
                    tj_profile = ctrl_z[:, tj]
                    denom = np.linalg.norm(t_profile) * np.linalg.norm(tj_profile)
                    if denom > 1e-12:
                        w = float(np.dot(t_profile, tj_profile) / denom)
                    else:
                        w = 0.0
                    weights[j] = max(w, 0.0)

                wsum = weights.sum()
                if wsum > 1e-12:
                    w_norm = weights / wsum
                    base = w_norm @ deltas
                else:
                    base = deltas.mean(axis=0) if deltas.shape[0] > 0 else np.zeros(n_genes)

            # Scale by target protein length (median for missing).
            scale = self._target_length(p, ctx, prot_len, median_len)
            out[i, :, 0] = base * scale

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    def _protein_lengths(self, ctx):
        cache = ctx.cache
        if "e293_prot_len" in cache:
            return cache["e293_prot_len"]

        lengths = {}
        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            cols = pa.get("columns", [])
            try:
                pl_idx = cols.index("protein_length")
            except ValueError:
                pl_idx = 0
            genes = pa.get("genes", {})
            for sym, vals in genes.items():
                if vals is None:
                    continue
                try:
                    v = vals[pl_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv) and fv > 0:
                    lengths[sym] = fv
        cache["e293_prot_len"] = lengths
        return lengths

    def _target_length(self, p, ctx, prot_len, median_len):
        tgenes = ctx.target_genes(p)
        vals = []
        for g in tgenes:
            v = prot_len.get(g)
            if v is not None and np.isfinite(v) and v > 0:
                vals.append(v)
        if vals:
            return float(np.mean(vals))
        return float(median_len)
