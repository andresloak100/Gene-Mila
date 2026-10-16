import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationPPIRandomProjectionE721(Feature):
    name = "gene_annotation_ppi_random_projection_e721"
    version = 1
    description = ("Concatenate gene annotation vector and PPI distance features "
                   "(inverse distance sum to targets) for gene g, then project to a "
                   "fixed random vector; average over targets for p.")
    rationale = ("A random projection combining gene annotation with PPI network "
                 "distances to targets captures latent biological relationships and "
                 "improves prediction.")
    inputs = ["gene_annotation", "ppi_network"]
    params = {"projection_dim": 10}
    dim = 1

    def _build_per_gene_vec(self, ctx, params):
        cache = ctx.cache
        key = ("e721_vec",)
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        genes = ctx.genes
        gene_index = ctx.gene_index

        ann = ctx.knowledge("gene_annotation")
        cols = []
        if ann is not None and isinstance(ann, dict) and "genes" in ann:
            ann_genes = ann["genes"]
            col_names = ann.get("columns", None)
            # determine numeric columns
            sample = None
            for g in genes:
                if g in ann_genes:
                    sample = ann_genes[g]
                    break
            if sample is not None:
                if col_names is None:
                    col_names = list(range(len(sample)))
                # build matrix
                mat = np.zeros((n, len(col_names)), dtype=np.float64)
                for i, g in enumerate(genes):
                    v = ann_genes.get(g, None)
                    if v is None:
                        continue
                    for j in range(len(col_names)):
                        try:
                            x = v[j]
                        except Exception:
                            x = None
                        if x is None:
                            mat[i, j] = 0.0
                        else:
                            try:
                                fx = float(x)
                                if np.isfinite(fx):
                                    mat[i, j] = fx
                            except Exception:
                                mat[i, j] = 0.0
                cols.append(mat)

        if not cols:
            cols.append(np.zeros((n, 1), dtype=np.float64))

        # PPI inverse distance sum to all genes
        ppi = ctx.knowledge("ppi_network")
        ppi_sum = np.zeros(n, dtype=np.float64)
        if ppi is not None and isinstance(ppi, (list, tuple)):
            adj = {}
            for entry in ppi:
                try:
                    a, b, w = entry[0], entry[1], float(entry[2])
                except Exception:
                    continue
                if a not in adj:
                    adj[a] = []
                if b not in adj:
                    adj[b] = []
                adj[a].append((b, w))
                adj[b].append((a, w))

            for i, g in enumerate(genes):
                if g in adj:
                    s = 0.0
                    for (h, w) in adj[g]:
                        if w > 0:
                            s += 1.0 / w
                    ppi_sum[i] = s

        # log-scale ppi sum to keep values bounded
        ppi_feat = np.log1p(ppi_sum).reshape(-1, 1)
        cols.append(ppi_feat)

        vec = np.concatenate(cols, axis=1)

        # standardize columns to avoid scale dominance
        mu = vec.mean(axis=0, keepdims=True)
        sd = vec.std(axis=0, keepdims=True)
        sd = np.where(sd > 1e-8, sd, 1.0)
        vec = (vec - mu) / sd

        cache[key] = vec
        return vec

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        dim = int(params.get("projection_dim", 10))
        if dim < 1:
            dim = 1

        vec = self._build_per_gene_vec(ctx, params)
        d = vec.shape[1]

        # fixed random projection matrix (deterministic)
        rng = np.random.RandomState(721)
        R = rng.randn(d, dim) / np.sqrt(d)

        proj = vec @ R  # (n, dim)

        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            idxs = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if not idxs:
                continue
            vals = proj[idxs, :].mean(axis=0)  # (dim,)
            out[i, :, 0] = float(vals.mean())

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
