import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityXPPIInteractionE417(Feature):
    name = "target_essentiality_x_ppi_interaction_e417"
    version = 2
    description = (
        "Per-perturbation row: for each gene g, essentiality of target t "
        "(1 - LOEUF, clipped) times PPI adjacency indicator between t and g, "
        "with a fallback that spreads the signal via correlation when no PPI "
        "edges are available."
    )
    rationale = (
        "Perturbing a loss-of-function-intolerant (essential) target with many "
        "physical interactions may produce broader downstream effects; combining "
        "PPI adjacency with target LOEUF captures both connectivity and importance."
    )
    inputs = ["knowledge", "target_indices", "gene_corr"]
    params = {"ppi_threshold": 0.5, "fallback_corr": 0.3}
    dim = 1

    def compute(self, ctx, perts, params):
        thr = float(params.get("ppi_threshold", 0.5))
        fcorr = float(params.get("fallback_corr", 0.3))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        cache = ctx.cache

        # --- LOEUF lookup ---
        if "_e417_loeuf" not in cache:
            loeuf = np.full(n_genes, np.nan, dtype=float)
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                cols = gc.get("columns", []) or []
                if "oe_lof_upper" in cols:
                    idx = cols.index("oe_lof_upper")
                    genes = gc.get("genes", {}) or {}
                    for g, vals in genes.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None or vals is None:
                            continue
                        try:
                            v = vals[idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[gi] = fv
            cache["_e417_loeuf"] = loeuf

        # --- PPI adjacency ---
        if "_e417_ppi" not in cache:
            adj = {}
            ppi = ctx.knowledge("ppi_network")
            if ppi is not None:
                # ppi may be a list of triples or a dict-like structure
                entries = ppi
                if isinstance(ppi, dict):
                    entries = ppi.get("edges", ppi.get("interactions", []))
                for entry in entries:
                    try:
                        a, b, s = entry[0], entry[1], entry[2]
                    except (IndexError, TypeError):
                        continue
                    try:
                        fs = float(s)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fs) or fs <= thr:
                        continue
                    ia = ctx.gene_index.get(a)
                    ib = ctx.gene_index.get(b)
                    if ia is None or ib is None:
                        continue
                    adj.setdefault(ia, set()).add(ib)
                    adj.setdefault(ib, set()).add(ia)
            cache["_e417_ppi"] = adj

        loeuf = cache["_e417_loeuf"]
        adj = cache["_e417_ppi"]
        has_ppi = len(adj) > 0

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue

            ess_vals = []
            for ti in t_idx:
                lv = loeuf[ti]
                if np.isfinite(lv):
                    e = 1.0 - lv
                    e = min(max(e, 0.0), 1.0)
                    ess_vals.append(e)
            if not ess_vals:
                # fallback essentiality when LOEUF missing: constant baseline
                ess_val = 1.0
            else:
                ess_val = float(np.mean(ess_vals))
            if ess_val <= 0.0:
                continue

            if has_ppi:
                neigh = set()
                for ti in t_idx:
                    s = adj.get(ti)
                    if s:
                        neigh.update(s)
                if neigh:
                    cols = np.fromiter(neigh, dtype=np.int64, count=len(neigh))
                    cols = cols[(cols >= 0) & (cols < n_genes)]
                    if cols.size:
                        out[i, cols, 0] = ess_val
                        continue

            # Fallback: use correlation of target(s) with all genes
            corr_targets = [ti for ti in t_idx if 0 <= ti < n_genes]
            if not corr_targets:
                continue
            try:
                gc_mat = ctx.gene_corr
            except Exception:
                gc_mat = None
            if gc_mat is None:
                # last resort: uniform small signal on all genes
                out[i, :, 0] = ess_val * 1e-3
                continue
            sub = np.asarray(gc_mat[np.array(corr_targets, dtype=np.int64), :])
            if sub.ndim == 1:
                sub = sub[None, :]
            # max absolute correlation per gene across targets
            corr_vec = np.nanmax(np.abs(sub), axis=0)
            corr_vec = np.where(np.isfinite(corr_vec), corr_vec, 0.0)
            mask = corr_vec >= fcorr
            if not np.any(mask):
                out[i, :, 0] = ess_val * corr_vec
            else:
                out[i, :, 0] = ess_val * corr_vec * mask

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
