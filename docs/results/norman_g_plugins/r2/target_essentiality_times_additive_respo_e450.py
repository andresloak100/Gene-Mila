import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityTimesAdditiveResponse(Feature):
    name = "target_essentiality_times_additive_respo_e450"
    version = 1
    description = ("Product of additive_response and the mean essentiality score "
                   "(e.g., CERES/DepMap gene effect) of p's target genes.")
    rationale = ("Essential genes may produce stronger downstream effects when "
                 "perturbed; scaling the additive response by target essentiality "
                 "captures this sensitivity.")
    inputs = ["control_cells", "train_delta"]
    params = {"score": "ceres"}
    dim = 1

    def _essentiality_scores(self, ctx, params):
        cache = ctx.cache
        key = ("e450_ess", params.get("score", "ceres"))
        if key in cache:
            return cache[key]

        scores = np.zeros(ctx.n_genes, dtype=float)
        found = False

        # Try prior knowledge sources that might carry essentiality info.
        for name in ctx.available_knowledge():
            try:
                data = ctx.knowledge(name)
            except Exception:
                data = None
            if not isinstance(data, dict):
                continue
            low = name.lower()
            if "essent" in low or "depmap" in low or "ceres" in low or "gene_effect" in low:
                genes = data.get("genes")
                if isinstance(genes, dict):
                    cols = data.get("columns", [])
                    # Prefer a column matching the requested score name.
                    target_col = None
                    want = str(params.get("score", "ceres")).lower()
                    for j, c in enumerate(cols):
                        if want in str(c).lower():
                            target_col = j
                            break
                    if target_col is None and cols:
                        target_col = 0
                    if target_col is not None:
                        for g, vals in genes.items():
                            idx = ctx.gene_index.get(g)
                            if idx is None:
                                continue
                            try:
                                v = vals[target_col]
                            except Exception:
                                continue
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                scores[idx] = fv
                                found = True

        if not found:
            # Fallback: use gene constraint (LOEUF) as a proxy for essentiality.
            try:
                data = ctx.knowledge("gene_constraint")
            except Exception:
                data = None
            if isinstance(data, dict):
                genes = data.get("genes")
                cols = data.get("columns", [])
                if isinstance(genes, dict):
                    loeuf_col = None
                    for j, c in enumerate(cols):
                        if "oe_lof_upper" in str(c).lower() or "loeuf" in str(c).lower():
                            loeuf_col = j
                            break
                    if loeuf_col is not None:
                        for g, vals in genes.items():
                            idx = ctx.gene_index.get(g)
                            if idx is None:
                                continue
                            try:
                                v = vals[loeuf_col]
                            except Exception:
                                continue
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                # Low LOEUF = essential; invert to a positive score.
                                scores[idx] = 1.0 - fv
                                found = True

        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        ess = self._essentiality_scores(ctx, params)
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # Get additive_response feature (dim 1); fall back to additive baseline.
        try:
            add = ctx.feature("additive_response", perts)
            add = np.asarray(add, dtype=float)
            if add.ndim == 3:
                add = add[:, :, 0]
            elif add.ndim != 2:
                add = None
        except Exception:
            add = None

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                continue
            mean_ess = float(np.mean(ess[tgt_idx])) if len(tgt_idx) else 0.0
            if not np.isfinite(mean_ess):
                mean_ess = 0.0

            if add is not None and np.isfinite(add[i]).all():
                base = add[i]
            else:
                # Recompute additive baseline from training deltas.
                _, d = ctx.train_delta(exclude=p)
                base = np.zeros(ctx.n_genes, dtype=float)
                if d.shape[0] > 0:
                    for t in tgt_idx:
                        base += d[:, t]
                else:
                    base = ctx.control_mean.copy()

            vals = mean_ess * base
            vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, :, 0] = vals

        return out
