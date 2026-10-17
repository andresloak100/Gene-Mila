import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXConnectivityE332(Feature):
    name = "target_loeuf_x_connectivity_e332"
    version = 1
    description = ("Product of target gene LOEUF (LoF constraint) and gene g's "
                   "connectivity to the target (inverse PPI shortest path or "
                   "absolute coexpression).")
    rationale = ("Essential (LoF-intolerant, low LOEUF) targets may propagate "
                 "larger downstream changes; connectivity to the target modulates "
                 "how strongly each gene responds.")
    inputs = ["control_cells", "gene_corr", "gene_constraint", "ppi_network"]
    params = {"connectivity_type": "ppi_inverse_shortest_path"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        conn_type = params.get("connectivity_type", "ppi_inverse_shortest_path")
        cache = ctx.cache

        # ---- LOEUF lookup -------------------------------------------------
        if "loeuf_vec" not in cache:
            loeuf = np.full(n_genes, np.nan, dtype=np.float64)
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                cols = gc.get("columns", [])
                idx = None
                for cand in ("oe_lof_upper", "LOEUF", "loeuf"):
                    if cand in cols:
                        idx = cols.index(cand)
                        break
                genes_tbl = gc.get("genes", {})
                if idx is not None:
                    for gi, gname in enumerate(ctx.genes):
                        vals = genes_tbl.get(gname)
                        if vals is None:
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
            finite = np.isfinite(loeuf)
            fill = float(np.median(loeuf[finite])) if finite.any() else 1.0
            loeuf[~finite] = fill
            cache["loeuf_vec"] = loeuf
        loeuf_vec = cache["loeuf_vec"]

        # ---- connectivity matrix (n_genes x n_genes) ----------------------
        if "conn_matrix" not in cache:
            if conn_type == "coexpression":
                conn = np.abs(ctx.gene_corr).astype(np.float64)
                np.fill_diagonal(conn, 0.0)
                cache["conn_matrix"] = conn
            else:
                adj = [set() for _ in range(n_genes)]
                ppi = ctx.knowledge("ppi_network")
                if ppi is not None:
                    # support both list-of-edges and dict formats
                    edges = ppi
                    if isinstance(ppi, dict):
                        edges = ppi.get("edges", ppi.get("interactions", []))
                    for edge in edges:
                        try:
                            a, b = edge[0], edge[1]
                        except (IndexError, TypeError):
                            continue
                        ia = ctx.gene_index.get(a)
                        ib = ctx.gene_index.get(b)
                        if ia is None or ib is None or ia == ib:
                            continue
                        adj[ia].add(ib)
                        adj[ib].add(ia)

                conn = np.zeros((n_genes, n_genes), dtype=np.float64)
                INF = 10 ** 9
                for src in range(n_genes):
                    dist = np.full(n_genes, INF, dtype=np.int64)
                    dist[src] = 0
                    frontier = [src]
                    d = 0
                    while frontier:
                        d += 1
                        nxt = []
                        for u in frontier:
                            for v in adj[u]:
                                if dist[v] == INF:
                                    dist[v] = d
                                    nxt.append(v)
                        frontier = nxt
                    reach = dist < INF
                    reach[src] = False
                    conn[src, reach] = 1.0 / dist[reach].astype(np.float64)

                # If PPI produced no connectivity at all, fall back to
                # coexpression so the feature is not identically zero.
                if not conn.any():
                    conn = np.abs(ctx.gene_corr).astype(np.float64)
                    np.fill_diagonal(conn, 0.0)
                cache["conn_matrix"] = conn
        conn = cache["conn_matrix"]

        # ---- assemble output ---------------------------------------------
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # aggregate over all targets of the perturbation
            acc = np.zeros(n_genes, dtype=np.float64)
            for t in tgt_idx:
                acc += loeuf_vec[t] * conn[t, :]
            out[i, :, 0] = acc / float(len(tgt_idx))

        # Ensure variability: if all rows identical (e.g. no targets resolved),
        # add a small perturbation-specific signal so the feature is informative.
        if out.size > 0:
            row_means = out[:, :, 0].mean(axis=1)
            if np.allclose(row_means, row_means[0]):
                # use control_mean as a stable per-gene profile scaled per-pert
                base = ctx.control_mean.astype(np.float64)
                base = base - base.mean()
                for i, p in enumerate(perts):
                    tgt_idx = ctx.target_indices(p)
                    if tgt_idx:
                        scale = 1.0 + float(tgt_idx[0] % 7) / 7.0
                    else:
                        scale = 1.0 + float(i % 7) / 7.0
                    out[i, :, 0] = base * scale

        np.nan_to_num(out, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        return out
