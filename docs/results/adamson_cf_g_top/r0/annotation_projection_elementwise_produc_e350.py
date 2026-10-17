import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationProjectionElementwiseProductE350(Feature):
    name = "annotation_projection_elementwise_produc_e350"
    version = 1
    description = (
        "Element-wise product of random projections of target and gene annotation "
        "vectors, summed to a single score per (p, g)."
    )
    rationale = (
        "A random projection of annotation space followed by an element-wise product "
        "can capture nonlinear interactions between target and gene annotations better "
        "than a plain dot product."
    )
    inputs = ["knowledge", "target_genes", "genes"]
    params = {"projection_dim": 50, "seed": 350}
    dim = 1

    def _build_annotation_matrix(self, ctx, annotation, columns):
        n_genes = ctx.n_genes
        mat = np.zeros((n_genes, len(columns)), dtype=np.float64)
        genes = annotation.get("genes", {}) or {}
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            row = np.zeros(len(columns), dtype=np.float64)
            for ci, v in enumerate(vals):
                if ci >= len(columns):
                    break
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    row[ci] = fv
            mat[gi] = row
        return mat

    def _get_annotation_matrix(self, ctx):
        cache = ctx.cache
        key = "e350_annotation_matrix"
        if key in cache:
            return cache[key]

        cols = []
        mats = []

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            ann_cols = ann.get("columns", []) or []
            # numeric columns only
            num_cols = []
            for c in ann_cols:
                lc = str(c).lower()
                if lc.startswith("aa_"):
                    continue
                num_cols.append(c)
            if num_cols:
                m = self._build_annotation_matrix(ctx, ann, num_cols)
                mats.append(m)
                cols.extend(["ga:" + str(c) for c in num_cols])

        cons = ctx.knowledge("gene_constraint")
        if cons is not None:
            cons_cols = cons.get("columns", []) or []
            if cons_cols:
                m = self._build_annotation_matrix(ctx, cons, cons_cols)
                mats.append(m)
                cols.extend(["gc:" + str(c) for c in cons_cols])

        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            prot_cols = prot.get("columns", []) or []
            if prot_cols:
                m = self._build_annotation_matrix(ctx, prot, prot_cols)
                mats.append(m)
                cols.extend(["pa:" + str(c) for c in prot_cols])

        if not mats:
            mat = np.zeros((ctx.n_genes, 1), dtype=np.float64)
        else:
            mat = np.concatenate(mats, axis=1)

        # standardize columns robustly
        mu = mat.mean(axis=0, keepdims=True)
        sd = mat.std(axis=0, keepdims=True)
        sd = np.where(sd < 1e-8, 1.0, sd)
        mat = (mat - mu) / sd
        mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)

        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        projection_dim = int(params.get("projection_dim", 50))
        seed = int(params.get("seed", 350))
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        ann_mat = self._get_annotation_matrix(ctx)
        in_dim = ann_mat.shape[1]

        cache = ctx.cache
        rkey = "e350_projection"
        if rkey in cache and cache[rkey].shape == (in_dim, projection_dim):
            R = cache[rkey]
        else:
            rng = np.random.RandomState(seed)
            R = rng.normal(0.0, 1.0 / np.sqrt(max(projection_dim, 1)),
                           size=(in_dim, projection_dim))
            cache[rkey] = R

        gene_proj = ann_mat @ R  # (n_genes, projection_dim)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            t_idx = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if not t_idx:
                continue
            t_proj = gene_proj[t_idx].mean(axis=0)  # (projection_dim,)
            prod = gene_proj * t_proj[np.newaxis, :]  # (n_genes, projection_dim)
            score = prod.sum(axis=1)
            out[i, :, 0] = score

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
