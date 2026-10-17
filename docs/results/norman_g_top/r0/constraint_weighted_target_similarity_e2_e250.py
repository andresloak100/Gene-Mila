import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintWeightedTargetSimilarityE2(Feature):
    name = "constraint_weighted_target_similarity_e2_e250"
    description = (
        "For each gene g and perturbation p, weight the similarity of g's single-gene "
        "response to the target's mean response by the inverse LOEUF of the target gene(s)."
    )
    rationale = (
        "LoF-intolerant genes may have more specific and stronger downstream effects; "
        "weighting target-response similarity by 1/(LOEUF+eps) emphasises constrained targets."
    )
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {"epsilon": 0.1}
    dim = 1

    def _get_loueuf(self, ctx):
        cache = ctx.cache
        if "e250_loueuf" in cache:
            return cache["e250_loueuf"]
        loueuf = {}
        try:
            kn = ctx.knowledge("gene_constraint")
        except Exception:
            kn = None
        if kn is not None:
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        loueuf[g] = fv
        cache["e250_loueuf"] = loueuf
        return loueuf

    def _get_single_response(self, ctx, exclude):
        cache = ctx.cache
        key = ("e250_single_resp", exclude)
        if key in cache:
            return cache[key]
        pert_ids, deltas = ctx.train_delta(exclude=exclude)
        single = {}
        for pid, row in zip(pert_ids, deltas):
            tg = ctx.target_genes(pid)
            if len(tg) == 1 and pid == tg[0]:
                single[pid] = row
        cache[key] = single
        return single

    def compute(self, ctx, perts, params):
        eps = float(params.get("epsilon", 0.1))
        loueuf = self._get_loueuf(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue

            # weight from inverse LOEUF, averaged over targets
            ws = []
            for t in targets:
                lo = loueuf.get(t, None)
                if lo is None:
                    ws.append(None)
                else:
                    ws.append(1.0 / (lo + eps))
            valid = [w for w in ws if w is not None]
            if valid:
                weight = float(np.mean(valid))
            else:
                weight = 1.0

            # target mean response from single-gene responses of targets
            single = self._get_single_response(ctx, p)
            resp_vecs = [single[t] for t in targets if t in single]
            if not resp_vecs:
                continue
            mean_resp = np.mean(np.stack(resp_vecs, axis=0), axis=0)

            # similarity of g's single-gene response to target mean response
            # g's single-gene response: use gene g's single perturbation response if available
            sims = np.zeros(n_genes, dtype=float)
            mean_centered = mean_resp - mean_resp.mean()
            mean_norm = np.linalg.norm(mean_centered)
            if mean_norm <= 0:
                continue
            for g_idx in range(n_genes):
                g_name = ctx.genes[g_idx]
                if g_name in single:
                    gvec = single[g_name]
                    gc = gvec - gvec.mean()
                    gn = np.linalg.norm(gc)
                    if gn > 0:
                        sims[g_idx] = float(np.dot(gc, mean_centered) / (gn * mean_norm))
            out[i, :, 0] = sims * weight

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
