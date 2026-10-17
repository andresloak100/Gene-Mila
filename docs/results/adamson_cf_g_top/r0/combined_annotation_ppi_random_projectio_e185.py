import numpy as np
from genemila.features.api import Feature, register


@register
class CombinedAnnotationPPIRandomProjection(Feature):
    name = "combined_annotation_ppi_random_projectio_e185"
    version = 1
    description = ("Random projection of concatenated gene annotation vectors and PPI spectral "
                   "embedding, interacted with the perturbation target's projection.")
    rationale = ("Annotation and PPI embeddings capture complementary latent biology; a low-dim "
                 "random projection of their concatenation yields compact gene signatures whose "
                 "interaction with the target's signature predicts response.")
    inputs = ["control_cells", "gene_annotation", "ppi_network"]
    params = {"n_components": 10, "embedding_dim": 16, "seed": 0}
    dim = 10

    def _build_gene_vectors(self, ctx, params):
        cache = ctx.cache
        key = ("combined_ann_ppi_emb", params.get("embedding_dim", 16),
               params.get("seed", 0))
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        emb_dim = int(params.get("embedding_dim", 16))
        seed = int(params.get("seed", 0))

        # ---- Annotation block ----
        ann = ctx.knowledge("gene_annotation")
        ann_cols = []
        if ann is not None and isinstance(ann.get("genes"), dict):
            genes_map = ann["genes"]
            columns = ann.get("columns", [])
            # use numeric annotation columns (skip aa_* to keep it compact but include a few)
            n_cols = len(columns)
            ann_mat = np.zeros((n_genes, n_cols), dtype=np.float64)
            present = np.zeros(n_genes, dtype=bool)
            for g, col in gene_index.items():
                vals = genes_map.get(g)
                if vals is None:
                    continue
                arr = np.zeros(n_cols, dtype=np.float64)
                for j in range(min(n_cols, len(vals))):
                    v = vals[j]
                    if isinstance(v, (int, float)) and np.isfinite(v):
                        arr[j] = float(v)
                    else:
                        arr[j] = 0.0
                ann_mat[col] = arr
                present[col] = True
            # standardize columns (guard zero variance)
            mu = ann_mat.mean(axis=0)
            sd = ann_mat.std(axis=0)
            sd[sd < 1e-8] = 1.0
            ann_mat = (ann_mat - mu) / sd
            # clip extremes
            ann_mat = np.clip(ann_mat, -5.0, 5.0)
            ann_cols.append(ann_mat)

        if ann_cols:
            ann_block = np.concatenate(ann_cols, axis=1)
        else:
            ann_block = np.zeros((n_genes, 1), dtype=np.float64)

        # ---- PPI spectral embedding ----
        ppi = ctx.knowledge("ppi_network")
        adj = np.zeros((n_genes, n_genes), dtype=np.float64)
        if isinstance(ppi, list):
            for entry in ppi:
                if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                    continue
                a, b = entry[0], entry[1]
                w = 1.0
                if len(entry) >= 3:
                    try:
                        w = float(entry[2])
                    except (TypeError, ValueError):
                        w = 1.0
                ia = gene_index.get(a)
                ib = gene_index.get(b)
                if ia is None or ib is None or ia == ib:
                    continue
                adj[ia, ib] = w
                adj[ib, ia] = w

        if adj.any():
            # symmetric normalization
            deg = adj.sum(axis=1)
            deg[deg < 1e-12] = 1.0
            dinv = 1.0 / np.sqrt(deg)
            norm_adj = adj * dinv[:, None] * dinv[None, :]
            # top eigenvectors via eigh on symmetric normalized adjacency
            try:
                k = min(emb_dim, n_genes - 1)
                vals, vecs = np.linalg.eigh(norm_adj)
                # take largest magnitude eigenvalues
                order = np.argsort(-np.abs(vals))[:k]
                emb = vecs[:, order] * np.sqrt(np.abs(vals[order]) + 1e-8)[None, :]
            except np.linalg.LinAlgError:
                emb = np.zeros((n_genes, emb_dim), dtype=np.float64)
            # pad/truncate to emb_dim
            if emb.shape[1] < emb_dim:
                pad = np.zeros((n_genes, emb_dim - emb.shape[1]), dtype=np.float64)
                emb = np.concatenate([emb, pad], axis=1)
            elif emb.shape[1] > emb_dim:
                emb = emb[:, :emb_dim]
            # sign-fix for determinism: make largest-abs entry positive
            for j in range(emb.shape[1]):
                col = emb[:, j]
                if col.size:
                    idx = int(np.argmax(np.abs(col)))
                    if col[idx] < 0:
                        emb[:, j] = -col
            # standardize
            mu = emb.mean(axis=0)
            sd = emb.std(axis=0)
            sd[sd < 1e-8] = 1.0
            emb = (emb - mu) / sd
            emb = np.clip(emb, -5.0, 5.0)
        else:
            emb = np.zeros((n_genes, emb_dim), dtype=np.float64)

        # ---- Concatenate ----
        feats = np.concatenate([ann_block, emb], axis=1)

        cache[key] = feats
        return feats

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("seed", 0))

        gene_feats = self._build_gene_vectors(ctx, params)
        d = gene_feats.shape[1]

        # Random projection matrix (shared across genes) -> (d, n_comp)
        rng = np.random.RandomState(seed + 12345)
        proj = rng.normal(size=(d, n_comp)) / np.sqrt(max(d, 1))
        # gene projections: (n_genes, n_comp)
        gene_proj = gene_feats @ proj

        out = np.zeros((n, n_genes, n_comp), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                # no target measured: use mean gene projection as a weak prior
                out[i, :, :] = gene_proj
                continue
            tgt_proj = gene_proj[tgt_idx].mean(axis=0)  # (n_comp,)
            # interaction: elementwise product of gene projection and target projection
            out[i, :, :] = gene_proj * tgt_proj[None, :]

        # sanitize
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
