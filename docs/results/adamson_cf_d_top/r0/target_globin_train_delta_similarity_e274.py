import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGlobinTrainDeltaSimilarity(Feature):
    name = "target_globin_train_delta_similarity_e274"
    version = 1
    description = (
        "For each (p,g): if gene g is a globin gene, cosine similarity between the "
        "target gene's training-delta profile and the average of globin genes' "
        "training-delta profiles; else 0."
    )
    rationale = (
        "Targets whose response profiles resemble globin genes' response profiles "
        "may share regulatory wiring, so perturbing them elicits globin-like responses."
    )
    inputs = ["train_delta"]
    params = {"globin_genes": ["HBZ", "HBG1", "HBG2", "HBA1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = params.get("globin_genes", ["HBZ", "HBG1", "HBG2", "HBA1"])

        # Map globin genes to measured columns.
        globin_idx = [
            ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index
        ]
        # Boolean mask over genes: is this gene a globin gene?
        is_globin = np.zeros(ctx.n_genes, dtype=bool)
        if globin_idx:
            is_globin[np.array(globin_idx, dtype=int)] = True

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # LEAKAGE RULE: exclude p from training deltas.
            train_ids, d = ctx.train_delta(exclude=p)
            # d shape: (n_train, n_genes)
            if d.shape[0] == 0 or not globin_idx:
                continue

            # Target gene columns (may be empty if not measured).
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_idx = np.array(t_idx, dtype=int)

            # Globin columns present.
            g_idx = np.array(globin_idx, dtype=int)

            # Target profile(s): average over target columns -> (n_train,)
            t_vec = d[:, t_idx].mean(axis=1)

            # Globin profiles: (n_train, n_globin)
            g_mat = d[:, g_idx]

            # Cosine similarity between target vector and each globin vector.
            t_norm = np.linalg.norm(t_vec)
            g_norms = np.linalg.norm(g_mat, axis=0)

            sims = np.zeros(g_mat.shape[1], dtype=float)
            valid = (t_norm > 0) & (g_norms > 0)
            if np.any(valid):
                sims[valid] = (g_mat[:, valid].T @ t_vec) / (
                    g_norms[valid] * t_norm
                )

            sim_val = float(np.mean(sims)) if sims.size > 0 else 0.0
            if not np.isfinite(sim_val):
                sim_val = 0.0

            # Only globin genes get the similarity value.
            out[i, is_globin, 0] = sim_val

        # Ensure all values are finite.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
