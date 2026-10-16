import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjectionE567(Feature):
    name = "gene_annotation_random_projection_e567"
    version = 1
    description = "Dot product of each gene's standardized annotation vector with a fixed random Gaussian matrix (n_components dims)."
    rationale = "A low-dimensional random projection of the full annotation vector captures latent functional properties that modulate perturbation response without overfitting correlated annotation features."
    inputs = ["knowledge"]
    params = {"n_components": 10}
    dim = 10

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim))

        cache = ctx.cache
        key = ("garp_e567", n_comp, n_genes)
        proj = cache.get(key)

        if proj is None:
            ann = ctx.knowledge("gene_annotation")
            genes = ctx.genes
            if ann is None:
                proj = np.zeros((n_genes, self.dim))
            else:
                genes_ann = ann.get("genes", {})
                columns = ann.get("columns", [])
                # collect feature names: numeric annotation columns
                feat_names = []
                for c in columns:
                    if isinstance(c, str) and c not in ("symbol", "chromosome", "strand"):
                        feat_names.append(c)
                if len(feat_names) == 0:
                    # fall back: infer from first entry
                    for g, vals in genes_ann.items():
                        if isinstance(vals, (list, tuple)):
                            feat_names = ["f%d" % i for i in range(len(vals))]
                        break

                n_feat = len(feat_names)
                X = np.full((n_genes, n_feat), np.nan, dtype=float)

                for gi, g in enumerate(genes):
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    if isinstance(vals, dict):
                        row = [vals.get(fn, np.nan) for fn in feat_names]
                    else:
                        row = list(vals)[:n_feat]
                    for fi, v in enumerate(row):
                        if isinstance(v, (int, float)) and np.isfinite(v):
                            X[gi, fi] = float(v)
                        elif isinstance(v, str):
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    X[gi, fi] = fv
                            except ValueError:
                                pass

                # keep columns with enough finite values and variance
                finite_counts = np.isfinite(X).sum(axis=0)
                keep = []
                for fi in range(n_feat):
                    if finite_counts[fi] < max(2, int(0.1 * n_genes)):
                        continue
                    col = X[:, fi]
                    mask = np.isfinite(col)
                    if mask.sum() < 2:
                        continue
                    if np.nanstd(col[mask]) < 1e-12:
                        continue
                    keep.append(fi)

                if len(keep) == 0:
                    proj = np.zeros((n_genes, self.dim))
                else:
                    Xk = X[:, keep]
                    # impute NaNs with column mean
                    col_means = np.nanmean(Xk, axis=0)
                    inds = np.where(~np.isfinite(Xk))
                    if len(inds[0]) > 0:
                        Xk[inds] = np.take(col_means, inds[1])
                    # standardize
                    mu = Xk.mean(axis=0)
                    sd = Xk.std(axis=0)
                    sd[sd < 1e-12] = 1.0
                    Z = (Xk - mu) / sd

                    # fixed random Gaussian matrix
                    rng = np.random.RandomState(567)
                    W = rng.randn(Z.shape[1], self.dim)
                    proj = Z.dot(W)

            cache[key] = proj

        # broadcast the same projection to every perturbation
        for i in range(len(perts)):
            out[i, :, :] = proj

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
