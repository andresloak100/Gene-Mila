import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthWeightedTargetSimilarity(Feature):
    name = "protein_length_weighted_target_similarit_e260"
    version = 2
    description = ("For each gene g and perturbation p, weighted average of g's similarity to each "
                   "target gene's single-gene response vector, weighted by 1/(protein_length+1).")
    rationale = ("Shorter proteins may be more directly regulated or turn over faster, so their "
                 "single-gene response profiles are more informative; weighting target similarities "
                 "by inverse protein length emphasizes these targets.")
    inputs = ["train_delta", "target_genes", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Cache protein lengths from prior knowledge.
        cache = ctx.cache
        if "_pl_len" not in cache:
            lengths = {}
            ann = ctx.knowledge("protein_annotation")
            if ann is not None:
                genes = ann.get("genes", {})
                cols = ann.get("columns", [])
                try:
                    idx = cols.index("protein_length")
                except ValueError:
                    idx = 0
                for g, vals in genes.items():
                    try:
                        v = vals[idx]
                    except Exception:
                        v = None
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv) and fv > 0:
                                lengths[g] = fv
                        except (TypeError, ValueError):
                            pass
            cache["_pl_len"] = lengths
        lengths = cache["_pl_len"]

        for i, p in enumerate(perts):
            targets = list(ctx.target_genes(p))
            if not targets:
                continue

            # Leave-one-out training deltas.
            tids, deltas = ctx.train_delta(exclude=p)
            deltas = np.asarray(deltas, dtype=float)
            if deltas.ndim != 2 or deltas.shape[0] == 0:
                continue

            # Map single-gene perturbation id -> row in deltas (only rows whose id is a gene name).
            single_map = {}
            for j, tid in enumerate(tids):
                if "+" not in tid:
                    single_map[tid] = j

            # Target delta vectors (across genes), weighted by inverse protein length.
            tgt_vecs = []
            tgt_w = []
            for t in targets:
                j = single_map.get(t)
                if j is None:
                    continue
                v = deltas[j]
                if np.all(np.isfinite(v)):
                    tgt_vecs.append(v)
                    tgt_w.append(1.0 / (lengths.get(t, 0.0) + 1.0))
            if not tgt_vecs:
                continue
            tgt_w = np.asarray(tgt_w, dtype=float)
            tw_sum = tgt_w.sum()
            if tw_sum <= 0 or not np.isfinite(tw_sum):
                continue
            tgt_w = tgt_w / tw_sum
            tgt_mat = np.stack(tgt_vecs, axis=0)  # (n_targets, n_genes)

            # Precompute standardized target vectors.
            tgt_mu = tgt_mat.mean(axis=1, keepdims=True)
            tgt_sd = tgt_mat.std(axis=1, keepdims=True)
            tgt_sd_safe = np.where(tgt_sd > 1e-12, tgt_sd, np.inf)
            tgt_z = (tgt_mat - tgt_mu) / tgt_sd_safe  # (n_targets, n_genes)

            # For each gene g that has a single perturbation, correlate its delta vector
            # (across genes) with each target vector, then take the weighted average.
            for gname, row in single_map.items():
                gidx = ctx.gene_index.get(gname)
                if gidx is None:
                    continue
                gvec = deltas[row]
                if not np.all(np.isfinite(gvec)):
                    continue
                gm = gvec.mean()
                gs = gvec.std()
                if gs <= 1e-12:
                    continue
                gz = (gvec - gm) / gs
                # Correlation with each target across genes.
                corrs = (tgt_z @ gz) / float(n_genes)
                corrs = np.where(np.isfinite(corrs), corrs, 0.0)
                val = float(np.dot(tgt_w, corrs))
                if not np.isfinite(val):
                    val = 0.0
                out[i, gidx, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
