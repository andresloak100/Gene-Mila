import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionStaticPlusTargetVarE436(Feature):
    name = "random_projection_static_plus_target_var_e436"
    version = 1
    description = ("Random Gaussian projection of concatenated static gene/target annotations "
                   "plus target_response_variance_e275 to n_components dimensions.")
    rationale = ("A fixed low-dimensional random projection of standardized static features can "
                 "capture non-linear interactions across annotations while limiting variance.")
    inputs = ["control_cells", "gene_annotation", "protein_annotation", "gene_constraint",
              "target_response_variance_e275"]
    params = {"n_components": 10}
    dim = 10

    def _build_static_matrix(self, ctx):
        """Return (n_genes, n_static_features) matrix of static gene annotations."""
        cached = ctx.cache.get("_e436_static")
        if cached is not None:
            return cached

        n = ctx.n_genes
        gene_index = ctx.gene_index
        cols = []

        # --- gene_annotation ---
        ga = ctx.knowledge("gene_annotation")
        if ga and "genes" in ga:
            gcols = ga.get("columns", [])
            ncols = len(gcols)
            mat = np.full((n, ncols), np.nan, dtype=np.float64)
            genes = ga["genes"]
            for sym, vals in genes.items():
                gi = gene_index.get(sym)
                if gi is None:
                    continue
                for j, v in enumerate(vals):
                    if j >= ncols:
                        break
                    if v is None:
                        continue
                    try:
                        mat[gi, j] = float(v)
                    except (TypeError, ValueError):
                        pass
            cols.append(mat)

            # bidirectional indicator
            bid = ga.get("bidirectional") or {}
            bvec = np.zeros(n, dtype=np.float64)
            for sym in bid.keys():
                gi = gene_index.get(sym)
                if gi is not None:
                    bvec[gi] = 1.0
            cols.append(bvec[:, None])

            # neighbour count within 100kb
            nb = ga.get("neighbours") or {}
            nbvec = np.zeros(n, dtype=np.float64)
            for sym, lst in nb.items():
                gi = gene_index.get(sym)
                if gi is not None and lst is not None:
                    nbvec[gi] = float(len(lst))
            cols.append(nbvec[:, None])

        # --- protein_annotation ---
        pa = ctx.knowledge("protein_annotation")
        if pa and "genes" in pa:
            pcols = pa.get("columns", [])
            ncols = len(pcols)
            mat = np.full((n, ncols), np.nan, dtype=np.float64)
            for sym, vals in pa["genes"].items():
                gi = gene_index.get(sym)
                if gi is None:
                    continue
                for j, v in enumerate(vals):
                    if j >= ncols:
                        break
                    if v is None:
                        continue
                    try:
                        mat[gi, j] = float(v)
                    except (TypeError, ValueError):
                        pass
            cols.append(mat)

        # --- gene_constraint ---
        gc = ctx.knowledge("gene_constraint")
        if gc and "genes" in gc:
            ccols = gc.get("columns", [])
            ncols = len(ccols)
            mat = np.full((n, ncols), np.nan, dtype=np.float64)
            for sym, vals in gc["genes"].items():
                gi = gene_index.get(sym)
                if gi is None:
                    continue
                for j, v in enumerate(vals):
                    if j >= ncols:
                        break
                    if v is None:
                        continue
                    try:
                        mat[gi, j] = float(v)
                    except (TypeError, ValueError):
                        pass
            cols.append(mat)

        if cols:
            static = np.concatenate(cols, axis=1)
        else:
            static = np.zeros((n, 1), dtype=np.float64)

        # Standardize columns (nan-safe)
        means = np.nanmean(static, axis=0)
        stds = np.nanstd(static, axis=0)
        stds = np.where((stds > 1e-8) & np.isfinite(stds), stds, 1.0)
        means = np.where(np.isfinite(means), means, 0.0)
        static = (static - means) / stds
        static = np.nan_to_num(static, nan=0.0, posinf=0.0, neginf=0.0)

        ctx.cache["_e436_static"] = static
        return static

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 10))
        n = ctx.n_genes
        static = self._build_static_matrix(ctx)

        # target_response_variance_e275 -> per-perturbation, per-gene scalar
        try:
            trv = ctx.feature("target_response_variance_e275", perts, params=None)
        except Exception:
            trv = None

        n_static = static.shape[1]
        total_dim = n_static + 1

        # Build deterministic random projection matrix (total_dim -> n_components)
        key = ("_e436_proj", total_dim, n_components)
        proj = ctx.cache.get(key)
        if proj is None:
            rng = np.random.RandomState(436)
            proj = rng.normal(0.0, 1.0 / np.sqrt(n_components),
                              size=(total_dim, n_components)).astype(np.float64)
            ctx.cache[key] = proj

        out = np.zeros((len(perts), n, n_components), dtype=np.float64)

        for i, p in enumerate(perts):
            if trv is not None:
                tv = np.asarray(trv[i], dtype=np.float64)
                if tv.ndim == 2:
                    tv = tv[:, 0]
                elif tv.ndim == 1:
                    tv = tv
                else:
                    tv = tv.reshape(n, -1)[:, 0]
                tv = np.nan_to_num(tv, nan=0.0, posinf=0.0, neginf=0.0)
                tstd = tv.std()
                if tstd > 1e-8:
                    tv = (tv - tv.mean()) / tstd
                else:
                    tv = np.zeros_like(tv)
                tv = tv[:, None]
            else:
                tv = np.zeros((n, 1), dtype=np.float64)

            full = np.concatenate([static, tv], axis=1)  # (n, total_dim)
            out[i] = full @ proj  # (n, n_components)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
