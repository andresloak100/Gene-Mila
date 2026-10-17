import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionStaticPlusTargetRes(Feature):
    name = "random_projection_static_plus_target_res_e607"
    version = 1
    description = ("Random projection of per-gene static annotations plus target response "
                   "variance into a low-dimensional space, broadcast per gene.")
    rationale = ("Static annotations and target response variance may encode nonlinear "
                 "structure; a fixed random projection captures this without overfitting.")
    inputs = ["gene_annotation", "gene_constraint", "protein_annotation",
              "target_response_variance_e275"]
    params = {"n_components": 10, "random_seed": 42}
    dim = 10

    def _build_static(self, ctx, params):
        n = ctx.n_genes
        cols = []

        def add_block(name):
            kb = ctx.knowledge(name)
            if kb is None or "genes" not in kb:
                return
            kcols = kb.get("columns", [])
            kmap = kb["genes"]
            mat = np.full((n, len(kcols)), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                v = kmap.get(g)
                if v is None:
                    continue
                for j in range(min(len(kcols), len(v))):
                    x = v[j]
                    if x is not None:
                        try:
                            mat[i, j] = float(x)
                        except (TypeError, ValueError):
                            pass
            cols.append(mat)

        add_block("gene_annotation")
        add_block("gene_constraint")
        add_block("protein_annotation")

        if not cols:
            return np.zeros((n, 1), dtype=np.float64)
        return np.concatenate(cols, axis=1)

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("random_seed", 42))
        n = ctx.n_genes

        cache = ctx.cache
        static_key = ("rp_static", n_comp, seed)
        if static_key not in cache:
            static = self._build_static(ctx, params)
            static = np.nan_to_num(static, nan=0.0, posinf=0.0, neginf=0.0)
            mu = static.mean(axis=0, keepdims=True)
            sd = static.std(axis=0, keepdims=True)
            sd[sd < 1e-8] = 1.0
            static = (static - mu) / sd
            cache[static_key] = static
        static = cache[static_key]

        out = np.zeros((len(perts), n, n_comp), dtype=np.float64)

        for pi, p in enumerate(perts):
            # Compute target response variance WITHOUT using p's own label.
            trv_key = ("trv_excl", p)
            if trv_key not in cache:
                # Build a leave-one-out target response variance from training deltas,
                # excluding p itself, to avoid label leakage.
                try:
                    train_ids, deltas = ctx.train_delta(exclude=p)
                except TypeError:
                    train_ids, deltas = ctx.train_delta(p)
                if deltas is None or len(deltas) == 0:
                    trv_col = np.zeros((n, 1), dtype=np.float64)
                else:
                    deltas = np.asarray(deltas, dtype=np.float64)
                    var = np.var(deltas, axis=0)
                    var = np.nan_to_num(var, nan=0.0, posinf=0.0, neginf=0.0)
                    trv_col = var.reshape(n, 1)
                cache[trv_key] = trv_col
            trv_col = cache[trv_key]

            feats = np.concatenate([static, trv_col], axis=1)
            feats = np.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)

            mu = feats.mean(axis=0, keepdims=True)
            sd = feats.std(axis=0, keepdims=True)
            sd[sd < 1e-8] = 1.0
            feats = (feats - mu) / sd

            rng = np.random.RandomState(seed)
            proj = rng.randn(feats.shape[1], n_comp) / np.sqrt(feats.shape[1])
            gene_emb = feats @ proj
            gene_emb = np.nan_to_num(gene_emb, nan=0.0, posinf=0.0, neginf=0.0)
            out[pi] = gene_emb

        return out
