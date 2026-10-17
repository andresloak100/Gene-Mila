import numpy as np
from genemila.features.api import Feature, register


@register
class StaticFeatureRandomProjectionE390(Feature):
    name = "static_feature_random_projection_e390"
    version = 1
    description = (
        "Random projection of static gene/target annotations (gene annotation, "
        "protein annotation, network distances) for each (p,g) pair."
    )
    rationale = (
        "A low-dimensional random projection of static, label-free features can "
        "capture latent structure shared between target and gene without using "
        "any response labels, avoiding leakage."
    )
    inputs = ["knowledge", "target_genes", "gene_index"]
    params = {"n_components": 10}
    dim = 10

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _to_float(v):
        if v is None:
            return 0.0
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        if not np.isfinite(f):
            return 0.0
        return f

    def _build_static_matrices(self, ctx):
        """Return (gene_matrix, target_matrix, ppi_matrix) cached in ctx.cache."""
        cache = ctx.cache
        key = "_e390_static"
        if key in cache:
            return cache[key]

        genes = ctx.genes
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # ---- gene_annotation ----
        ga = ctx.knowledge("gene_annotation")
        ga_cols = []
        ga_genes = {}
        if isinstance(ga, dict):
            cols = ga.get("columns") or []
            ga_cols = list(cols)
            ga_genes = ga.get("genes") or {}

        # ---- protein_annotation ----
        pa = ctx.knowledge("protein_annotation")
        pa_cols = []
        pa_genes = {}
        if isinstance(pa, dict):
            pa_cols = list(pa.get("columns") or [])
            pa_genes = pa.get("genes") or {}

        n_ga = len(ga_cols)
        n_pa = len(pa_cols)
        gene_mat = np.zeros((n_genes, n_ga + n_pa), dtype=np.float64)

        for i, g in enumerate(genes):
            row = ga_genes.get(g)
            if isinstance(row, (list, tuple)):
                for j in range(min(n_ga, len(row))):
                    gene_mat[i, j] = self._to_float(row[j])
            prow = pa_genes.get(g)
            if isinstance(prow, (list, tuple)):
                for j in range(min(n_pa, len(prow))):
                    gene_mat[i, n_ga + j] = self._to_float(prow[j])

        # ---- ppi adjacency for network distance features ----
        ppi = ctx.knowledge("ppi_network")
        # Build sparse-ish adjacency as dict of sets restricted to measured genes
        adj = {}
        if isinstance(ppi, list):
            for edge in ppi:
                if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                if a in gene_index and b in gene_index:
                    ia, ib = gene_index[a], gene_index[b]
                    adj.setdefault(ia, set()).add(ib)
                    adj.setdefault(ib, set()).add(ia)

        # ---- prior_network adjacency ----
        prior = ctx.knowledge("prior_network")
        padj = {}
        if isinstance(prior, list):
            for edge in prior:
                if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                if a in gene_index and b in gene_index:
                    ia, ib = gene_index[a], gene_index[b]
                    padj.setdefault(ia, set()).add(ib)
                    padj.setdefault(ib, set()).add(ia)

        cache[key] = (gene_mat, adj, padj)
        return cache[key]

    @staticmethod
    def _bfs_dist(adj, src, n_genes, max_hops=3):
        """Distances from src up to max_hops; unreachable -> max_hops+1."""
        dist = np.full(n_genes, float(max_hops + 1), dtype=np.float64)
        if src is None:
            return dist
        dist[src] = 0.0
        frontier = [src]
        for hop in range(1, max_hops + 1):
            nxt = []
            for u in frontier:
                for v in adj.get(u, ()):
                    if dist[v] == float(max_hops + 1):
                        dist[v] = float(hop)
                        nxt.append(v)
            if not nxt:
                break
            frontier = nxt
        return dist

    def _projection_matrix(self, n_in, n_comp, seed=390):
        rng = np.random.RandomState(seed)
        return rng.normal(0.0, 1.0 / np.sqrt(max(n_in, 1)), size=(n_in, n_comp))

    # ------------------------------------------------------------------ compute
    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", self.params["n_components"]))
        n_comp = max(1, n_comp)
        n_genes = ctx.n_genes
        n_perts = len(perts)

        gene_mat, adj, padj = self._build_static_matrices(ctx)
        n_static = gene_mat.shape[1]

        # Feature vector per (p,g): [gene_static(g), target_static(t), net dists]
        # net dists: ppi dist, prior dist  (2 dims)
        n_in = 2 * n_static + 2
        proj = self._projection_matrix(n_in, n_comp)

        out = np.zeros((n_perts, n_genes, n_comp), dtype=np.float64)

        # Precompute per-target static vectors and network distances
        target_cache = {}
        for p in perts:
            if p in target_cache:
                continue
            tgenes = ctx.target_genes(p)
            tidx = None
            tvec = np.zeros(n_static, dtype=np.float64)
            if tgenes:
                tg = tgenes[0]
                if tg in ctx.gene_index:
                    tidx = ctx.gene_index[tg]
                    tvec = gene_mat[tidx]
                else:
                    # target not measured: try any gene annotation entry
                    pass
            ppi_d = self._bfs_dist(adj, tidx, n_genes, max_hops=3)
            prior_d = self._bfs_dist(padj, tidx, n_genes, max_hops=3)
            target_cache[p] = (tvec, ppi_d, prior_d)

        for i, p in enumerate(perts):
            tvec, ppi_d, prior_d = target_cache[p]
            # Build (n_genes, n_in) matrix
            X = np.empty((n_genes, n_in), dtype=np.float64)
            X[:, :n_static] = gene_mat
            X[:, n_static:2 * n_static] = tvec[None, :]
            X[:, 2 * n_static] = ppi_d
            X[:, 2 * n_static + 1] = prior_d
            # Standardise columns to zero mean/unit std (safe)
            mu = X.mean(axis=0)
            sd = X.std(axis=0)
            sd[sd < 1e-8] = 1.0
            X = (X - mu) / sd
            out[i] = X @ proj

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
