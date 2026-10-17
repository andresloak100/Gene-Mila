import numpy as np
from genemila.features.api import Feature, register


@register
class CompartmentWeightedTargetResponseSimE231(Feature):
    name = "compartment_weighted_target_response_sim_e231"
    version = 1
    description = (
        "For each gene g and perturbation p, average Pearson correlation between g's "
        "single-gene response vector and each target's single-gene response vector, "
        "weighted by whether g and the target share a subcellular compartment."
    )
    rationale = (
        "Genes in the same subcellular compartment may respond more coherently to "
        "perturbations; weighting target-response similarity by compartment sharing "
        "adds a biologically meaningful prior."
    )
    inputs = ["train_delta", "knowledge"]
    params = {"weight_nonmatch": 0.1}
    dim = 1

    COMPARTMENT_COLS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _compartment_matrix(self, ctx):
        cached = ctx.cache.get("e231_compartments")
        if cached is not None:
            return cached

        n = ctx.n_genes
        mat = np.zeros((n, len(self.COMPARTMENT_COLS)), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}
            col_idx = {c: i for i, c in enumerate(cols)}
            present = [c for c in self.COMPARTMENT_COLS if c in col_idx]
            for g, gi in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, c in enumerate(present):
                    v = vals[col_idx[c]]
                    if v is None:
                        continue
                    try:
                        mat[gi, j] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        pass

        share = (mat @ mat.T) > 0
        ctx.cache["e231_compartments"] = share
        return share

    def compute(self, ctx, perts, params):
        w_non = float(params.get("weight_nonmatch", 0.1))
        share = self._compartment_matrix(ctx)

        # Cache single-gene response vectors from training deltas (leave-one-out safe
        # because we recompute train_delta per perturbation below).
        single_cache = {}

        def get_single_vec(pid, exclude):
            key = (pid, exclude)
            if key in single_cache:
                return single_cache[key]
            ids, deltas = ctx.train_delta(exclude=exclude)
            idx = None
            for k, pid2 in enumerate(ids):
                if pid2 == pid:
                    idx = k
                    break
            if idx is None:
                single_cache[key] = None
            else:
                single_cache[key] = deltas[idx]
            return single_cache[key]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue

            _, deltas = ctx.train_delta(exclude=p)

            # Build map from training pert id -> row for single genes.
            ids, _ = ctx.train_delta(exclude=p)
            id_to_row = {pid: k for k, pid in enumerate(ids)}

            # We need each target's single-gene response vector.
            target_vecs = []
            for t in targets:
                t_gene = ctx.genes[t]
                row = id_to_row.get(t_gene)
                if row is None:
                    target_vecs.append(None)
                else:
                    target_vecs.append(deltas[row])

            valid = [v for v in target_vecs if v is not None]
            if not valid:
                continue

            # For each gene g, correlate its own single-gene response (if available)
            # with each target's single-gene response.
            for g in range(ctx.n_genes):
                g_gene = ctx.genes[g]
                g_row = id_to_row.get(g_gene)
                if g_row is None:
                    continue
                g_vec = deltas[g_row]
                g_std = np.std(g_vec)
                if g_std <= 0 or not np.isfinite(g_std):
                    continue

                num = 0.0
                den = 0.0
                for t_idx, t_vec in zip(targets, target_vecs):
                    if t_vec is None:
                        continue
                    t_std = np.std(t_vec)
                    if t_std <= 0 or not np.isfinite(t_std):
                        continue
                    corr = np.mean((g_vec - g_vec.mean()) * (t_vec - t_vec.mean())) / (g_std * t_std)
                    if not np.isfinite(corr):
                        continue
                    w = 1.0 if share[g, t_idx] else w_non
                    num += w * corr
                    den += w

                if den > 0:
                    out[i, g, 0] = num / den

        return out
