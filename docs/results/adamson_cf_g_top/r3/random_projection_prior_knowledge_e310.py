import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionPriorKnowledge_e310(Feature):
    name = "random_projection_prior_knowledge_e310"
    version = 1
    description = ("Random Gaussian projections of a wide per-gene prior-knowledge feature "
                   "matrix (gene annotation, protein annotation, constraint, network degrees).")
    rationale = ("A low-dimensional random projection of many prior-knowledge features preserves "
                 "distances and may expose latent structure predictive of perturbation response.")
    inputs = ["knowledge", "genes"]
    params = {"n_components": 5, "seed": 42}
    dim = 5

    def _build_gene_matrix(self, ctx):
        genes = ctx.genes
        n = ctx.n_genes
        cols = []

        def add_col(vals):
            arr = np.zeros(n, dtype=np.float64)
            for i, v in enumerate(vals):
                if v is not None and np.isfinite(v):
                    arr[i] = float(v)
            cols.append(arr)

        ga = ctx.knowledge("gene_annotation")
        if ga and isinstance(ga, dict) and "genes" in ga:
            g = ga["genes"]
            ncol = len(ga.get("columns", []))
            for c in range(ncol):
                vals = []
                for sym in genes:
                    rec = g.get(sym)
                    if rec is None:
                        vals.append(np.nan)
                    else:
                        try:
                            vals.append(rec[c])
                        except Exception:
                            vals.append(np.nan)
                add_col(vals)

        pa = ctx.knowledge("protein_annotation")
        if pa and isinstance(pa, dict) and "genes" in pa:
            g = pa["genes"]
            ncol = len(pa.get("columns", []))
            for c in range(ncol):
                vals = []
                for sym in genes:
                    rec = g.get(sym)
                    if rec is None:
                        vals.append(np.nan)
                    else:
                        try:
                            vals.append(rec[c])
                        except Exception:
                            vals.append(np.nan)
                add_col(vals)

        gc = ctx.knowledge("gene_constraint")
        if gc and isinstance(gc, dict) and "genes" in gc:
            g = gc["genes"]
            ncol = len(gc.get("columns", []))
            for c in range(ncol):
                vals = []
                for sym in genes:
                    rec = g.get(sym)
                    if rec is None:
                        vals.append(np.nan)
                    else:
                        try:
                            vals.append(rec[c])
                        except Exception:
                            vals.append(np.nan)
                add_col(vals)

        # Network degrees from ppi_network and prior_network
        for kname in ("ppi_network", "prior_network"):
            net = ctx.knowledge(kname)
            deg = np.zeros(n, dtype=np.float64)
            if net:
                idx = ctx.gene_index
                for edge in net:
                    try:
                        a, b = edge[0], edge[1]
                    except Exception:
                        continue
                    if a in idx:
                        deg[idx[a]] += 1.0
                    if b in idx:
                        deg[idx[b]] += 1.0
            cols.append(deg)

        if not cols:
            return np.zeros((n, 1), dtype=np.float64)

        mat = np.stack(cols, axis=1)
        # Replace non-finite with column medians (or 0 if all nan)
        for c in range(mat.shape[1]):
            col = mat[:, c]
            finite = np.isfinite(col)
            if finite.any():
                med = np.median(col[finite])
                col[~finite] = med
            else:
                col[:] = 0.0
        # Standardize
        mean = mat.mean(axis=0)
        std = mat.std(axis=0)
        std[std < 1e-8] = 1.0
        mat = (mat - mean) / std
        return mat

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 5))
        seed = int(params.get("seed", 42))
        n = ctx.n_genes

        cache_key = ("rp_e310", n_components, seed)
        if cache_key in ctx.cache:
            proj = ctx.cache[cache_key]
        else:
            mat = self._build_gene_matrix(ctx)
            rng = np.random.RandomState(seed)
            W = rng.randn(mat.shape[1], n_components) / np.sqrt(max(mat.shape[1], 1))
            proj = mat @ W  # (n_genes, n_components)
            # Standardize projections across genes
            mu = proj.mean(axis=0)
            sd = proj.std(axis=0)
            sd[sd < 1e-8] = 1.0
            proj = (proj - mu) / sd
            proj = np.nan_to_num(proj, nan=0.0, posinf=0.0, neginf=0.0)
            ctx.cache[cache_key] = proj

        out = np.zeros((len(perts), n, n_components), dtype=np.float64)
        for i in range(len(perts)):
            out[i] = proj
        return out
