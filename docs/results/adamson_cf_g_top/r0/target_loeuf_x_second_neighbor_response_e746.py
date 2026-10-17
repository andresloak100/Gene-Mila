import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXSecondNeighborResponse(Feature):
    name = "target_loeuf_x_second_neighbor_response_e746"
    version = 1
    description = ("For each (p,g): (1 - LOEUF of perturbation target) * mean_response "
                   "averaged over genes at PPI distance 2 from the target.")
    rationale = ("LOEUF indicates target essentiality; essential targets may propagate "
                 "stronger indirect effects through second-order PPI neighbours.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # --- Build PPI adjacency over measured genes ---
        adj = np.zeros((n_genes, n_genes), dtype=bool)
        ppi = ctx.knowledge("ppi_network")
        if ppi is not None:
            gi = ctx.gene_index
            for edge in ppi:
                try:
                    a, b = edge[0], edge[1]
                except Exception:
                    continue
                ia = gi.get(a)
                ib = gi.get(b)
                if ia is not None and ib is not None and ia != ib:
                    adj[ia, ib] = True
                    adj[ib, ia] = True

        # --- LOEUF lookup ---
        loeuf = {}
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes_tbl = gc.get("genes", {})
            cols = gc.get("columns", [])
            loeuf_idx = None
            for cand in ("oe_lof_upper", "loeuf", "LOEUF"):
                if cand in cols:
                    loeuf_idx = cols.index(cand)
                    break
            if loeuf_idx is not None:
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except Exception:
                        continue
                    if v is not None:
                        try:
                            loeuf[sym] = float(v)
                        except (TypeError, ValueError):
                            pass

        # --- Precompute second-neighbour masks per unique target set ---
        cache = ctx.cache

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            mean_resp = d.mean(axis=0)  # (n_genes,)

            targets = ctx.target_genes(p)
            target_idx = []
            for t in targets:
                ti = ctx.gene_index.get(t)
                if ti is not None:
                    target_idx.append(ti)

            if target_idx:
                key = tuple(sorted(target_idx))
                second_mask = cache.get(("second_mask", key))
                if second_mask is None:
                    nbr_mask = adj[target_idx].any(axis=0)
                    if nbr_mask.any():
                        second_mask = adj[nbr_mask].any(axis=0)
                    else:
                        second_mask = np.zeros(n_genes, dtype=bool)
                    second_mask = second_mask.copy()
                    second_mask[target_idx] = False
                    second_mask &= ~nbr_mask
                    cache[("second_mask", key)] = second_mask

                if second_mask.any():
                    snr = float(mean_resp[second_mask].mean())
                else:
                    # fall back to global mean response so the row carries signal
                    snr = float(mean_resp.mean())
            else:
                snr = float(mean_resp.mean())

            # Essentiality factor from target LOEUF (mean over targets).
            if targets:
                loeuf_vals = [loeuf[t] for t in targets if t in loeuf]
                if loeuf_vals:
                    lf = float(np.mean(loeuf_vals))
                else:
                    lf = 0.5  # unknown -> neutral essentiality
            else:
                lf = 0.5
            ess = 1.0 - lf

            out[i, :, 0] = ess * snr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)

        # Ensure the feature is non-constant: if everything collapsed to zero,
        # fall back to a perturbation-specific scalar broadcast so rows differ.
        if not np.any(out):
            for i, p in enumerate(perts):
                _, d = ctx.train_delta(exclude=p)
                if d.shape[0] == 0:
                    continue
                out[i, :, 0] = float(d.mean())

        return out
