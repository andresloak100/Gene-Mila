import numpy as np
from collections import deque
from genemila.features.api import Feature, register


@register
class PPIDistanceWeightedConstraint(Feature):
    name = "ppi_distance_weighted_constraint_e118"
    version = 1
    description = ("Shortest-path distance in the PPI network from gene g to the nearest "
                   "target of perturbation p, multiplied by (1 - LOEUF) of that target "
                   "(or pLI when LOEUF is unavailable).")
    rationale = ("Constrained (LoF-intolerant) targets may exert stronger downstream effects "
                 "on their interacting partners, so a constraint-weighted PPI distance "
                 "captures regulatory influence better than distance alone.")
    inputs = ["control_cells", "ppi_network", "gene_constraint"]
    params = {}
    dim = 1

    def _build_adj(self, ctx):
        cache = ctx.cache
        if "ppi_adj_e118" in cache:
            return cache["ppi_adj_e118"]
        ppi = ctx.knowledge("ppi_network")
        adj = {i: [] for i in range(ctx.n_genes)}
        if ppi:
            gi = ctx.gene_index
            for edge in ppi:
                try:
                    a, b, w = edge[0], edge[1], float(edge[2])
                except (IndexError, TypeError, ValueError):
                    continue
                ia = gi.get(a)
                ib = gi.get(b)
                if ia is None or ib is None:
                    continue
                w = max(w, 1e-6)
                dist = 1.0 / w
                adj[ia].append((ib, dist))
                adj[ib].append((ia, dist))
        cache["ppi_adj_e118"] = adj
        return adj

    def _constraint_scores(self, ctx):
        cache = ctx.cache
        if "constraint_scores_e118" in cache:
            return cache["constraint_scores_e118"]
        scores = np.full(ctx.n_genes, np.nan, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc:
            cols = gc.get("columns", [])
            genes = gc.get("genes", {})
            try:
                i_loeuf = cols.index("oe_lof_upper")
            except ValueError:
                i_loeuf = None
            try:
                i_pli = cols.index("pLI")
            except ValueError:
                i_pli = None
            for g, idx in ctx.gene_index.items():
                vals = genes.get(g)
                if not vals:
                    continue
                loeuf = None
                pli = None
                if i_loeuf is not None and i_loeuf < len(vals):
                    loeuf = vals[i_loeuf]
                if i_pli is not None and i_pli < len(vals):
                    pli = vals[i_pli]
                score = None
                if loeuf is not None:
                    try:
                        lf = float(loeuf)
                        if np.isfinite(lf):
                            score = 1.0 - lf
                    except (TypeError, ValueError):
                        score = None
                if score is None and pli is not None:
                    try:
                        pv = float(pli)
                        if np.isfinite(pv):
                            score = pv
                    except (TypeError, ValueError):
                        score = None
                if score is not None:
                    scores[idx] = score
        # Normalise available finite scores to [0, 1]; default 0.5 for missing.
        finite = np.isfinite(scores)
        if finite.any():
            mn = scores[finite].min()
            mx = scores[finite].max()
            if mx > mn:
                norm = (scores - mn) / (mx - mn)
            else:
                norm = np.full_like(scores, 0.5)
            norm[~finite] = 0.5
        else:
            norm = np.full(ctx.n_genes, 0.5)
        cache["constraint_scores_e118"] = norm
        return norm

    def _bfs(self, adj, sources):
        n = len(adj)
        dist = np.full(n, np.inf)
        dq = deque()
        for s in sources:
            if 0 <= s < n:
                dist[s] = 0.0
                dq.append(s)
        while dq:
            u = dq.popleft()
            du = dist[u]
            for v, w in adj[u]:
                nd = du + w
                if nd < dist[v]:
                    dist[v] = nd
                    dq.append(v)
        return dist

    def compute(self, ctx, perts, params):
        adj = self._build_adj(ctx)
        scores = self._constraint_scores(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue
            dist = self._bfs(adj, targets)
            # Weighted distance: distance to the nearest target weighted by that target's
            # constraint score. For each gene, use the nearest reachable target.
            # Approximate nearest target's score by taking, for each gene, the score of the
            # source that yields the minimum distance (we recompute per-source distances
            # only when there are few targets; otherwise use min over targets of score*dist).
            if len(targets) == 1:
                t = targets[0]
                w = scores[t]
                val = dist * w
            else:
                # multi-source: recover nearest target by running BFS from each target
                best = np.full(ctx.n_genes, np.inf)
                best_score = np.full(ctx.n_genes, 0.5)
                for t in targets:
                    dt = self._bfs(adj, [t])
                    w = scores[t]
                    cand = dt * w
                    mask = cand < best
                    best[mask] = cand[mask]
                    best_score[mask] = w
                val = best
            val = np.where(np.isfinite(val), val, 0.0)
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
