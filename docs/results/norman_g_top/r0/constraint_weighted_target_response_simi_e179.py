import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintWeightedTargetResponseSimi(Feature):
    name = "constraint_weighted_target_response_simi_e179"
    version = 1
    description = ("Correlation between gene g's single-gene response and the constraint-weighted "
                   "average target response, using LOO single-gene deltas and gnomAD constraint.")
    rationale = ("Loss-of-function-intolerant (low LOEUF / high pLI) genes are dosage-sensitive; "
                 "weighting target responses by constraint may highlight stronger, more consistent "
                 "activation effects.")
    inputs = ["train_delta", "knowledge"]
    params = {"constraint_metric": "loeuf"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "loeuf")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Build constraint weight vector over ctx genes.
        weights = self._constraint_weights(ctx, metric)

        # Memoize per-perturbation single-gene response vectors (LOO-safe is tricky:
        # single-gene response for gene t is the training delta of perturbation t itself,
        # which is NOT p unless t == p. We must exclude p from train_delta but single-gene
        # deltas for other genes are legitimately in the training set.)
        cache = ctx.cache

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # LOO training deltas (exclude p)
            pert_ids, deltas = ctx.train_delta(exclude=p)
            id_to_row = {pid: r for r, pid in enumerate(pert_ids)}

            # Weighted average target response vector
            wsum = 0.0
            acc = np.zeros(n_genes)
            for t in targets:
                row = id_to_row.get(t)
                if row is None:
                    continue
                w = weights.get(t, 0.0)
                if w <= 0.0:
                    continue
                acc += w * deltas[row]
                wsum += w
            if wsum <= 0.0:
                continue
            avg_target_resp = acc / wsum

            # For each gene g, correlation between g's single-gene response vector and avg_target_resp.
            # g's single-gene response = training delta of perturbation g (if it exists in LOO set).
            # Vectorize: build matrix of single-gene response vectors over genes that are single perts.
            single_rows = []
            single_cols = []
            for g_idx, g_name in enumerate(ctx.genes):
                row = id_to_row.get(g_name)
                if row is not None:
                    single_rows.append(row)
                    single_cols.append(g_idx)

            if not single_rows:
                continue
            single_rows = np.asarray(single_rows)
            single_cols = np.asarray(single_cols)
            resp_mat = deltas[single_rows]  # (n_single, n_genes)

            # Correlation of each resp vector with avg_target_resp
            a = resp_mat
            b = avg_target_resp
            a_mean = a.mean(axis=1, keepdims=True)
            b_mean = b.mean()
            a_c = a - a_mean
            b_c = b - b_mean
            num = a_c @ b_c
            a_var = np.einsum('ij,ij->i', a_c, a_c)
            b_var = float(b_c @ b_c)
            denom = np.sqrt(a_var * b_var)
            corr = np.zeros(a.shape[0])
            ok = denom > 0
            corr[ok] = num[ok] / denom[ok]

            out[i, single_cols, 0] = corr

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)

    def _constraint_weights(self, ctx, metric):
        cache = ctx.cache
        key = ("constraint_weights_e179", metric)
        if key in cache:
            return cache[key]

        weights = {}
        data = ctx.knowledge("gene_constraint")
        if data is not None:
            genes = data.get("genes", {})
            cols = data.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            try:
                pli_idx = cols.index("pLI")
            except ValueError:
                pli_idx = None

            for g, vals in genes.items():
                if vals is None:
                    continue
                w = 0.0
                if metric == "pli":
                    if pli_idx is not None and pli_idx < len(vals) and vals[pli_idx] is not None:
                        try:
                            w = float(vals[pli_idx])
                        except (TypeError, ValueError):
                            w = 0.0
                else:  # loeuf
                    if loeuf_idx is not None and loeuf_idx < len(vals) and vals[loeuf_idx] is not None:
                        try:
                            lo = float(vals[loeuf_idx])
                            w = 1.0 - lo
                        except (TypeError, ValueError):
                            w = 0.0
                w = max(0.0, min(1.0, w))
                weights[g] = w

        cache[key] = weights
        return weights
